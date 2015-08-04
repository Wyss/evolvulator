#!usr/bin/env python
# encoding: utf-8
"""
Copyright (c) 2012 Wyss Institute at Harvard University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

http://www.opensource.org/licenses/mit-license.php
"""

"""
exp_loop.py
"""

from pprint import pformat
from collections import OrderedDict, defaultdict
from twisted.internet import reactor, task
from twisted.internet.defer import Deferred
from twisted.internet.error import TimeoutError, ConnectError, ConnectionLost
from twisted.web._newclient import ResponseFailed
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
import json
import math
import sys
import time
import inspect
import traceback
from twisted.python.log import err

class ExperimentLoop(object):
    def __init__(self, experiment_database_interface, debug=False):
        """
        url is the url to access data at
        period is the period to poll the bioreactor in seconds
        data is dictionary to store successive values in
        reactor is a reference to reactor
        """
        self._dm = None # defered reference for a measurement request
        self._dc = None # defered reference for a control request
        self.edbi = experiment_database_interface
        self._measurementDict = defaultdict(dict) # this makes sure we can write to any channel
        self._measurementHistory = defaultdict(dict) #this makes sure we can write to any channel
        self._isOn = False
        self.control_was_on = False
        self._agent = Agent(reactor)
        self._isDebug = debug
        self.setupURLs()
        self._subscribers = []  # simple push signaling paradigm
        self.control_lock = defaultdict(bool)    # make sure we can lock any channel
        # by default this will throw an Exception unless subclass
        self.updateParameters()
        self.measure_call_IDs = {}
        self.lc_IDs = {}
    # end def
    
    def setupURLs(self):
        """
        overload this method if you have multiple urls for different channels
        each list index corresponds to different channels
        """
        url = self.edbi.getURL()
        self._measurement_urls = [url + '/measurement']
        self._control_urls = [url + '/control']
    # end def
    
    def callLater(self, *args):
        reactor.callLater(*args)
    #end def

    def addSubscriber(self, item):
        """
        Add an item object which implements the emit method.
        This item will be made aware of changes to a dataset through
        updateSubscribers
        """
        print "%s addSubscriber" % self._measurement_urls[0]
        if not (item in self._subscribers):
            self._subscribers.append(item)
            item.addURI(self.edbi.jobname())
    # end def
    
    def removeSubscriber(self, item):
        print "%s removeSubscriber" % self._measurement_urls[0]
        if item in self._subscribers:
            self._subscribers.remove(item)
            item.removeURI(self.edbi.jobname())
    # end def
    
    def updateParameters(self):
        """
        periodically update the list of control parameters
        """
        print "%s updateParameters" % self._measurement_urls[0]
        edbi = self.edbi
        edbi.getParams()
        # d = reactor.callLater(edbi.parameterUpdatePeriod(), edbi.updateParams)
        d = task.deferLater(reactor, edbi.parameterUpdatePeriod(), edbi.updateParams)
        d.addCallback(self.parametersUpdated) 
    # end def
    
    def parametersUpdated(self, params):
        print "%s parametersUpdated" % self._measurement_urls[0]
        edbi = self.edbi
        edbi.paramsUpdated(params)
        onState = edbi.isSystemOn()
        if onState and not self._isOn:
            self._isOn = True
            self.start()    # check for a restart
        elif not onState:
            self._isOn = False
        self.updateParameters()
    # end def
    
    def getState(self, channel):
        self.controlRequest(channel)
    # end def
    
    def isChannelLocked(self, channel):
        return self.control_lock[channel]
    # end def
    
    def lockChannel(self, channel):
        self.control_lock[channel] = True
    # end def
    
    def unlockChannel(self, channel):
        self.control_lock[channel] = False
    # end def
    
    def startMeasuring(self, channel=0):
        print "%s startMeasuring" % self._measurement_urls[channel]
        edbi = self.edbi
        sample_period = edbi.samplePeriod(channel)
        self.lc_IDs[channel] = task.LoopingCall(self.measurementRequest, channel)
        self.lc_IDs[channel].start(sample_period)
        #callID = reactor.callLater(sample_period, self.measurementRequest, channel)
        #self.measure_call_IDs[channel] = callID
    # end def
    
    def measurement(self, channel):
        """
        get the dictionary of the latest measurement
        """
        print "%s measurement" % self._measurement_urls[channel]
        return self._measurementDict[channel]
    # end def
    
    def loadJSON(self, jsondata):
        print "%s loadJSON" % self._measurement_urls[0]
        try:
            temp_dictionary = json.loads(jsondata)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print "In: ", inspect.stack()[1][3]
            return None
        return temp_dictionary
    # end def
    
    def processMeasurement(self, channel, jsondata):
        """
        process the meaurement.  Caches the most recent measurement per channel
        no return val
        """
        print "%s processMeasurement" % self._measurement_urls[channel]
        edbi = self.edbi
        try:
            measure_d = json.loads(jsondata)
            #intentionalException = int("totally not an int")
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print "In: ", inspect.stack()[1][3]
            print traceback.extract_stack()
            print "Bad json data " + jsondata
            #sample_period = edbi.samplePeriod(channel)
            #callID = reactor.callLater(sample_period, self.measurementRequest, channel)
            #self.measure_call_IDs[channel] = callID
            #return callID
            return
        print "processing measurement"

        if edbi.checkMeasurement(channel, measure_d):
            #if self._isDebug:
                #mh = self._measurementHistory[channel]
                #for key, value in measure_d.iteritems():
                #    if key in mh:
                #        (mh[key]).append(value)
                #    else:
                #        mh[key] = [value]
                #    print mh
            # end if
            self._measurementDict[channel] = measure_d
            if edbi.isSystemOn():
                d = edbi.addMeasurement(channel, measure_d)
                d.addCallback(self.measurementRecorded, channel, measure_d)
                d.addErrback(self.measurementAddFail, channel)
                return d
            else:
                # generate our own time stamp and send it on
                ts = time.time()
                return self.measurementRecorded(ts, channel, measure_d)
        # end if
        else:
            print "Measurement data from device malformed %s" % str(self._measurement)
            #sample_period = edbi.samplePeriod(channel)
            #callID = reactor.callLater(sample_period, self.measurementRequest, channel)
            #self.measure_call_IDs[channel] = callID
            #return callID            
    # end def
    
    def measurementAddFail(self, failure, channel):
        failstr = "WARNING: measurement ADD failure on channel %d" % channel 
        print failstr
        print failure
        failure.trap(TimeoutError, ConnectError, ConnectionLost, ResponseFailed)
        # repeat request for next period
        #edbi = self.edbi
        #sample_period = edbi.samplePeriod(channel)
        #callID = reactor.callLater(sample_period, self.measurementRequest, channel)
        #self.measure_call_IDs[channel] = callID
        #return callID
    # end def
    
    def measurementRecorded(self, result_ts, channel, m_dict):
        """
        The measurement has been recorded to the database so lets read it
        to get a timestamp and update subscribers
        """
        print "%s measurementRecorded" % self._measurement_urls[channel]
        edbi = self.edbi
        print "measurement recorded", result_ts
        m_dict['TIMESTAMP'] = result_ts
        self.updateSubscribers(m_dict)
        #sample_period = edbi.samplePeriod(channel)
        #callID = reactor.callLater(sample_period, self.measurementRequest, channel)
        #self.measure_call_IDs[channel] = callID
        return result_ts
    # end def
    
    def processState(self, channel, control_data, jsondata):
        """
        process the state response.  Caches the most recent measurement per channel
        no return val
        """
        print "%s processState" % self._measurement_urls[channel]
        edbi = self.edbi
        return "state" + jsondata
    # end def
    
    def updateSubscribers(self, data):
        """
        pass a dictionary of items to update to subscribers
        by emitting the update
        """
        print "%s updateSubscribers" % self._measurement_urls[0]
        for obj in self._subscribers:
            # jobname is the path to emit on
            obj.emit(self.edbi.jobname(), data)
    # end def
    
    def controlLoop(self, channel):
        """
        this is the callback for controlling the experiment
        overload this for your own experiment
        """
        print "%s controlLoop" % self._measurement_urls[channel]
        edbi = self.edbi
        parameters = edbi.getParams()
        if edbi.isControlOn():
            pass
        self.resetControl()
    # end def
    
    def isDebug(self):
        return self._isDebug
    
    def start(self):
        """
        turns the system on and begins callbacks for the control loo[]
        """
        print "%s Started Experiment Loop" % self._measurement_urls[0]
        edbi = self.edbi
        if edbi.isSystemOn():
            self.resetControl()
    # end def
    
    def stop(self):
        """
        Will end the event on the next callback in the control loop
        """
        edbi = self.edbi
        parameters = edbi.getParams()
        self._isOn = False
        print '%s Stopped Experiment Loop' % self._measurement_urls[0]
        print "Loop control is set to: ",parameters['CONTROL_ON']
    # end def
    
    def measurementRequest(self, channel):
        """
        request the latest measurement
        """
        # print "the URL", str(self._measurement_urls[channel])
        print "%s measurementRequest" % self._measurement_urls[channel]
        self._dm = self._agent.request(
            'GET',
            str("http://"+self._measurement_urls[channel]),
            Headers({'User-Agent': ['txAutoGnarls Web Client']}),
            None)
        self._dm.addCallback(self.measurementResponse, channel)
        self._dm.addErrback(self.measurementRequestFail, channel)
        # Note: if this Deferred is returned and something goes wrong with it, it will block new calls; so don't return it
        # return self._dm
        # self.d.addBoth(self.cbShutdown)
    # end def
    
    def measurementRequestFail(self, failure, channel, *args, **kwargs):
        print "WARNING: measurement request failed on channel %d" % (channel)
        print failure
        failure.trap(TimeoutError, ConnectError, ConnectionLost, ResponseFailed)
        # repeat request for next period
        #edbi = self.edbi
        #sample_period = edbi.samplePeriod(channel)
        #reactor.callLater(sample_period, self.measurementRequest, channel)
    # end def
    
    def measurementResponse(self, response, channel):
        """
        process the response to the latest measurement request
        """
        print "%s measurementResponse" % self._measurement_urls[channel]
        if self._isDebug:
            print 'Response version:', response.version
            print 'Response code:', response.code
            print 'Response phrase:', response.phrase
            print 'Response headers:'
            print pformat(list(response.headers.getAllRawHeaders()))
        finished = Deferred()
        print "%s In measurementProtocol" % self._measurement_urls[channel]
        response.deliverBody(MeasurementProtocol(finished, self, channel))
        print "%s Finished measurementProtocol" % self._measurement_urls[channel]
        return finished
    # end def
    
    def controlRequest(self, channel, control_data):
        """
        request a change of state on the device under control
        issuing an empty getstr will just get state from the channel
        """
        print "%s controlRequest" % self._measurement_urls[channel]
        getstr = control_data['message']
        self.lockChannel(channel)
        self._dc = self._agent.request(
            'GET',
            str("http://"+self._control_urls[channel] + '?' + getstr),
            Headers({'User-Agent': ['txAutoGnarls Web Client']}),
            None)
        self._dc.addCallback(self.controlResponse, channel, control_data)
        self._dc.addErrback(self.controlRequestFail, channel, control_data)
        return self._dc
        # self.d.addBoth(self.cbShutdown)
    # end def
    
    def controlResponse(self, response, channel, control_data):
        """
        process the response to the request a change of state
        a control response always returns state
        """
        print "%s controlResponse" % self._measurement_urls[channel]
        if self._isDebug:
            print 'Response version:', response.version
            print 'Response code:', response.code
            print 'Response phrase:', response.phrase
            print 'Response headers:'
            print pformat(list(response.headers.getAllRawHeaders()))
        finished = Deferred()
        response.deliverBody(ControllerProtocol(finished, self, channel, control_data))
        return finished
    # end def
    
    def controlRequestFail(self, failure, channel, control_data, *args, **kwargs):
        print "WARNING: control request failed on channel %d" % (channel)
        print failure
        failure.trap(TimeoutError, ConnectError, ConnectionLost, ResponseFailed)
        # retry request in one second
        self.callLater(1, self.controlRequest, channel, control_data)
    # end def
    
    def resetControl(self):
        edbi = self.edbi
        sample_period = edbi.samplePeriod(0)
        control_period = edbi.controlPeriod()
        print "%s resetControl" % self._measurement_urls[0]
        # print "Control has been turned on?", edbi.isControlOn()
        if edbi.isControlOn():
            self.control_was_on = True
            # print "reconnecting to Control Loop"
            if control_period < sample_period:
                verror = "Control Period %f much less than Sample Period %f" % (control_period, sample_period)
                raise ValueError(verror)
                reactor.stop()
            self.controlLoop(0)
        elif self.control_was_on == True:
            self.control_was_on = False
            self.shutdownControl()
        if edbi.isSystemOn():
            reactor.callLater(control_period, self.resetControl)
    # end def
    
    def shutdownControl(self):
        pass
    # end def

    def cbShutdown(self,ignored):
        print "%s cbShutdown" % self._measurement_urls[channel]
        reactor.stop()
# end class

class MeasurementProtocol(Protocol):
    """
    This handle responses from measurement requests
    """
    def __init__(self, finished, parentObject, channel):
        self._finished = finished
        self._parentObject = parentObject
        self._channel = channel
        self._remaining = 1024 * 10
        self._data = ""
    # end def
    
    def connectionMade(self):
        if self._parentObject.isDebug():
            print 'Connection made'
        self._data = ""
    # end def

    def dataReceived(self, bytes):
        if self._remaining:
            display = bytes[:self._remaining]
            # print 'Some data received:'
            # print display
            self._data += display
            self._remaining -= len(display)
    # end def

    def connectionLost(self, reason):
        print "%s connectionLost" % self._parentObject._measurement_urls[0]
        if self._parentObject.isDebug():
            print 'Finished receiving body:', reason.getErrorMessage()
            print self._data
        # print 'Finished receiving body:', reason.getErrorMessage()
        self._parentObject.processMeasurement(self._channel, self._data)
        self._finished.callback(None)
    # end def
# end class

class ControllerProtocol(Protocol):
    """
    This handles responses from control requests
    """
    def __init__(self, finished, parentObject, channel, control_data):
        self._finished = finished
        self._parentObject = parentObject
        self._remaining = 1024 * 10
        self._data = ""
        self._channel = channel
        self._control_data = control_data
    # end def
    
    def connectionMade(self):
        if self._parentObject.isDebug():
            print 'Connection made'
        self._data = ""
    # end def

    def dataReceived(self, bytes):
        if self._remaining:
            display = bytes[:self._remaining]
            # print 'Some data received:'
            # print display
            self._data += display
            self._remaining -= len(display)
    # end def

    def connectionLost(self, reason):
        if self._parentObject.isDebug():
            print 'Finished receiving body:', reason.getErrorMessage()
            print self._data
        if len(self._data) < 1:
            print "message not received"
            raise Exception('ACK not sent')
        else:
            self._parentObject.processState(self._channel, self._control_data, self._data)
        self._finished.callback(None)
    # end def
# end class