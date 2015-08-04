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
loop.py for evolvulator
"""
import math
import copy

if __name__ == '__main__':
    # to enable tests to run on this file see the bottom
    import sys
    import os.path
    root_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.append(root_dir)
    # print sys.path

from experimentcore.exp_loop import ExperimentLoop
from experimentcore.exp_dbifc import ExperimentDBIFC


class EvolvulatorLoop(ExperimentLoop):
    def __init__(self, experiment_database_interface, debug=False):
        """
        url is the url to access data at
        period is the period to poll the bioreactor in seconds
        data is dictionary to store successive values in
        """
        super(EvolvulatorLoop, self).__init__(experiment_database_interface, debug=debug)
        self.startMeasuring(channel=0)
        self.od_average = []
        self.is_valve_open = False
        self.LoopCount = 0
        #self.od_average = 0.0 <== this is a relic for a false floating point average of OD measurements.  
        #Can be used to reduce variation seen from measurement to measurement.  This is not a very accurate way of accomplishing this.
        #See new floating average in controlLoop below.
    # end def
    
    def controlLoop(self, channel):
        """
        this is the callback for controlling the experiment
        overload this for your own experiment
        """
        print "%s EvolvulatorLoop:controlLoop" % self._measurement_urls[channel]
        edbi = self.edbi
        params = edbi.getParams()
        baseline_values = (params['PHOTODIODE1_MIN'], params['PHOTODIODE1_MAX'])
        converstion_constants = (params['OD_CONSTANT_0'], params['OD_CONSTANT_1'], params['OD_CONSTANT_2'])
        md = self.measurement(channel)
        od_max = params['OD_TARGET']*(1.0+params['OD_DELTA'])
        od_min = params['OD_TARGET']-(params['OD_TARGET']*params['OD_DELTA'])
        if 'PHOTODIODE1' in md:
            value1 = md['PHOTODIODE1']
        else:
            print "WARNING: current measurement corrupt ", md
            return
        if not self.isChannelLocked(channel):
            od = convertValueToOD(value1, baseline_values, converstion_constants)
            print "OD for ", params["jobname"], "is thought to be ", od
            #Below is the new 15 point list floating point average, which will be more accurate.
            self.od_average.append(od)
            if len(self.od_average) < 15:
                od_avg = float('nan')
            if len(self.od_average) == 16:
                self.od_average.pop(0)
                # Below is the Valve open control loop to determine when to turn the Valve on and then when to turn it off.
                if self.is_valve_open == True:
                    print "Checking for OD decrease."
                    od_avg = sum(self.od_average[12:15])/3
                    print "averaged OD are: ", self.od_average[12:15]
                    print "Decreacing OD is thought to be ", od_avg
                    if od_avg <= od_min:
                        print "Target OD minimum has been reached.  Valve has been turned off!!!!"
                        self.od_average = []
                        #print "OD list as been reset"
                        control_data = {'message': 'LOAD0=OFF'} 
                        self.controlRequest(0, control_data)
                        self.LoopCount = 0
                    else:
                        print "Valve is left on"
                        self.LoopCount = self.LoopCount + 1
                        if self.LoopCount >= 400:
                            print "Unable to dilute culture.  Shutting down control loop. Resetting Loop Counter."
                            self.LoopCount = 0
                            # control_data = {'message': 'LOAD0=OFF'} 
                            # self.controlRequest(0, control_data)
                            # Need to shut down valve!!!
                            edbi.killControl()
                            # this if statement will determine if the valve has been left on for too long indicating that the
                            # media reservoir has likely been emptied.  In order to prevent the valve from burning out, this 
                            # will trigger the valve to shut off and shut down the controlLoop thereby ending the experiment.
                            # the length of time considered to be too long can be adjusted by changing the "if self.LoopCount = x" statement
                            # above.  This variable counts the total number of times the controlLoop has been executed while
                            # valve is on, the frequency of which is determined by the CONTROL_PERIOD parameter.
                        else:
                            print "Control loop still active. We are at an active valve loop count of ", self.LoopCount
                elif self.is_valve_open == False:
                    od_avg = sum(self.od_average)/len(self.od_average)
                    print "the last 15 OD points are: ", self.od_average
                    if od_avg > od_max:
                        print "Valve turned on!!"
                        control_data = {'message': 'LOAD0=ON'}
                        self.controlRequest(channel, control_data)
                    else:
                        print "od_max od_average", od_max, self.od_average
        else:
            print "channel is locked"
    # end def
    
    def processState(self, channel, control_data, jsondata):
        """
        process the state response.  Caches the most recent measurement per channel
        no return val
        """
        print "%s EvolvulatorLoop:processState" % self._measurement_urls[channel]
        edbi = self.edbi
        params = edbi.getParams()
        is_control_on = edbi.isControlOn()
        state = self.loadJSON(jsondata)
        message = control_data['message']
        if not state:
            print "WARNING: invalid response will try again later bad JSON"
            # repeat the request after a delay of one second
            if is_control_on:
                self.callLater(1, self.controlRequest, channel, control_data)
            return
        if state['LOAD0'] == 'ON' and message == 'LOAD0=ON':  # we successfully opened the valve
            self.is_valve_open = True
            edbi.setEvents(0, 1, 0)
            self.unlockChannel(0) 
        elif state['LOAD0'] == 'OFF' and message ==  'LOAD0=OFF': # we successfully closed the valve
            self.is_valve_open = False
            self.unlockChannel(0)   # no further control requests will happen until this is called
            edbi.setEvents(0, 0, 0)
        else:
            # strings not formatted correctly
            print "WARNING: invalid response will try again later bad string"
            # repeat the request after a delay of one second
            if is_control_on:
                self.callLater(1, self.controlRequest, channel, control_data)
    # end def

    def shutdownControl(self):
        self.closeValve()
    # end def

    def closeValve(self):
        """
        send a request to close a valve and record the changed volume
        """
        control_data = {'message': 'LOAD0=OFF'}
        self.controlRequest(0, control_data)
    # end def
    
    def measurementRecorded(self, result_ts, channel, m_dict):
        """
        Wrapper function to return the nano drop OD instead of sensor reading.
        This wraps the ExperimentLoop classes measurementRecorded method
        This value will appear in the strip chart
        """
        print "%s EvolvulatorLoop:measurementRecorded" % self._measurement_urls[channel]
        edbi = self.edbi
        params = edbi.getParams()
        mdc = copy.copy(m_dict)
        value = mdc["PHOTODIODE1"]
        baseline_values = (params['PHOTODIODE1_MIN'], params['PHOTODIODE1_MAX'])
        converstion_constants = (params['OD_CONSTANT_0'], params['OD_CONSTANT_1'], params['OD_CONSTANT_2'])
        print 'Evolvulator', params['jobname'], 'sensor reading = ', value, 'sensor(min, max) = ', baseline_values, 'calibrated sensor reading = ', float(value-baseline_values[0]), 'Conv_constants = ', converstion_constants 
        mdc["PHOTODIODE1"] = convertValueToOD( value, baseline_values, converstion_constants)
                                
        return ExperimentLoop.measurementRecorded(self, result_ts, channel, mdc)
    # end def
# end class

# begin helper functions

def convertValueToOD(value, baseline_values, converstion_constants):
    """
    Convert values read from A to D to nanoDrop OD
    baseline_value is the calibrated (min, max) reading from the sensor
    when the LED is off and on with an empty bottle in place
    
    -log10( current_value - offset / calibrated_value )
    """
    evo_od = -math.log10(float(value-baseline_values[0])/(baseline_values[1]-baseline_values[0]))
    nano_drop_od = converstion_constants[0]*(evo_od**2)+converstion_constants[1]*(evo_od)+converstion_constants[2]
    return nano_drop_od
# end def

if __name__ == '__main__':
    params = {}
    params['TANK_DIA'] = 400.
    params['EXIT_DIA'] = 3.
    params['FLOWCONSTANT'] = 0.135
    params['HEIGHT_OFFSET'] = 120.0
    params['OD_TARGET'] = 0.85
    params['OD_DELTA'] = 0.05
    params["VOLUME_START"] =  20000.0
    params['VOLUME_TARGET'] = 1000.0
    params['PHOTODIODE1_MIN'] = 8
    params['PHOTODIODE1_MAX'] = 900
    params['OD_CONSTANT_0'] = 1.0
    params['OD_CONSTANT_1'] = 1.0
    params['OD_CONSTANT_2'] = 1.0
    od_max = params['OD_TARGET']*(1.0+params['OD_DELTA'])
    print "Max OD is: ", od_max
    od = convertValueToOD(params['PHOTODIODE1_MIN'] + 1, \
                                (params['PHOTODIODE1_MIN'], \
                                params['PHOTODIODE1_MAX']))
    print "OD is: ", od