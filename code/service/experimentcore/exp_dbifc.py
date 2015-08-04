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
exp_dbifc.py
"""

import types
from collections import OrderedDict, defaultdict
import itertools
import operator
from twisted.enterprise import adbapi
import sqlite3
from pprint import pformat
import sys
import time
import json
import os

import inspect

class Field(object):
    _counter = itertools.count()
    def __init__(self, val=None, adv=True, note=None):
        self.order_number = Field._counter.next()
        self.name = ''
        self.val = self.typeCheck(val)
        self.advancedDisplay = adv
        self.note = note
    # end def
    def __repr__(self):
        return "Field(%r) %d" % (self.name, self.order_number)
    # end def
    def typeCheck(val):
        return val
    # end def
    def resetCounter(self):
        Field._counter = itertools.count()
    # end def
    def isAdvanced(self):
        """
        Is this parameter considered advanced?
        """
        return self.advancedDisplay
    # end def
    def note(self):
        return self.note
# end class

class IntField(Field):
    def typeFix(self, val):
        return int(val) if val else 0
    # end def
    def typeCheck(self, val):
        return isinstance(val, int)
    # end def
    def sqlType(self):
        return 'INTEGER'
    # end def
    def __repr__(self):
        return "IntField(%r) %d" % (self.name, self.order_number)
    # end def
# end class

class StringField(Field):
    def typeFix(self, val):
        return unicode(val) if val else ''
    # end def
    def typeCheck(self, val):
        return isinstance(val, str) or isinstance(val, unicode)
    # end def
    def sqlType(self):
        return 'TEXT'
    # end def
    def __repr__(self):
        return "StringField(%r) %d" % (self.name, self.order_number)
    # end def
# end class

class FloatField(Field):
    def typeFix(self, val):
        return float(val) if val else 0.0
    # end def
    def typeCheck(self, val):
        return isinstance(val, float)
    # end def
    def sqlType(self):
        return 'REAL'
    # end def
    def __repr__(self):
        return "FloatField(%r) %d" % (self.name, self.order_number)
    # end def
# end class

def show_usage():
    print "database.py <filename>"
    print "filename - is a *.db file for a database"
# end def

def createDB(dbpath=None):
    if dbpath == None:
        # homepath = os.getenv('USERPROFILE') or os.getenv('HOME')
        # mydatabase = thedatabase
        print "need a db path"
        #sys.exit(-1)
    else:
        mydatabase = dbpath

    connection = None
    try:
        connection = sqlite3.connect(mydatabase)
    except sqlite3.Error:
        print "Error"# %s:" % e.args[0]
        sys.exit(1)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print "In: ", inspect.stack()[1][3]
    finally:
        if connection:
            connection.close()
# end def

class DataBaseConnection(object):
    def __init__(self, db_path, async=False):
        self._connection = None
        self._db_path = db_path
        self._async = None
        self.setAsync(async)
    # end def

    def connection(self):
        return self._connection
    # end def

    def setAsync(self, is_async):
        self._async = is_async
        if self._connection:
            """
            close existing connection if any
            """
            self._connection.close()
        if is_async:
            print "new connection"
            # see http://twistedmatrix.com/trac/ticket/3629 for the check_same_thread business
            self._connection = adbapi.ConnectionPool('sqlite3', self._db_path, check_same_thread=False)
        else:
            self._connection = sqlite3.connect(self._db_path)
    # end def

    def close(self):
        """
        Shutdown the database connection pool or close the connection
        must do it for adapi.ConnectionPool to shutdown associated thread
        """
        self._connection.close()
    # end def

    def dbInteract(self, query, ifunction, *args):
        """
        query = False means a commit will happen
        ifunction is the interaction function
        """

        if self._async:
            # self.setAsync(True)
            conn = self._connection
            if query:
                result = conn.runInteraction(ifunction, *args)
            else:
                # this performs a commit
                result = conn.runInteraction(ifunction, *args)
            return result
        # end if
        else:
            # reconnect for non-async
            self.setAsync(False)
            conn = self._connection
            try:
                try:
                    cur = conn.cursor()
                except Exception as e:  # catch a thread error
                    print e
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    print "In: ", inspect.stack()[1][3]
                print "No exception so far"
                result = ifunction(cur, *args)
                if not query:
                    conn.commit()
                conn.close()
                self._connection = None
            except sqlite3.Error, e:
                if conn:
                    if not query:
                        conn.rollback()
                    conn.close()
                    self._connection = None
                print "Error %s:" %  e.args[0]
                sys.exit(1)
            except:
                print "Unexpected error:", sys.exc_info()[0]
                print "In: ", inspect.stack()[1][3]
            return result
    # end def

    def isAsync(self):
        return self._async
    # end def
# end class


class TableInterface(object):
    """
    Creates a database table based on fieldname order
    Additionally, it will allow for
    """
    def __init__(self):
        self._field_list = None
        self.tablename = None
        self.createAccessors()
    # end def

    def setTablename(self, tablename):
        self.tablename = tablename
    # end def

    def setConnection(self, dbconnection):
        """
        Takes a DataBaseConnection
        """
        self._dbconnection = dbconnection
    # end def

    def fields(self):
        return self._field_list
    # end def

    def createAccessors(self):
        """
        Create accessors based on the initial user provided class variables
        """
        if self._field_list == None:
            class_dict = self.__dict__.copy()
            del class_dict['_field_list']
            del class_dict['tablename']
            # print class_dict
            class_vars = class_dict.keys()

            fieldList = []
            field = None
            for field_name in class_vars:
                field = getattr(self, field_name)
                if isinstance(field, Field):
                    field.name = field_name
                    fieldList.append(field)
            if field:
                # reset the counter in case you'd like to
                # keep track of fields by index number
                field.resetCounter()
            # put all the fields in order
            fieldList.sort(key=operator.attrgetter('order_number'))

            def testTable(target):
                """
                Adds a table to a db
                """
                # create id and tstamp entries
                for field in fieldList:
                    print "A key:", field
                    print "called from", target
            # end def
            self.testTable = types.MethodType(testTable,self)

            def dropTable(target):
                exec_string = "DROP TABLE IF EXISTS %s ;" % (self.tablename)
                def dropTable(cursor):
                    cursor.execute(exec_string)
                return self._dbconnection.dbInteract(False, dropTable)
            # end def
            self.dropTable = types.MethodType(dropTable,self)

            def createTable(target):
                """
                Adds a table to a db
                """
                print "creating table: %s" % (self.tablename)
                execute_string = "CREATE TABLE %s (" % (self.tablename)
                execute_string += "ID INTEGER PRIMARY KEY,"
                execute_string += "TIMESTAMP REAL,"
                # create id and tstamp entries
                for field in fieldList:
                    execute_string += "%s %s, " % (field.name, field.sqlType())
                # end for
                execute_string = execute_string[0:-2] # drop the last comma and space
                execute_string += ");"
                # print execute_string
                def execCreateTable(cursor):
                    cursor.execute(execute_string)
                return self._dbconnection.dbInteract(False, execCreateTable)
            # end def
            self.createTable = types.MethodType(createTable,self)

            def readLastRow(target, callback=None):
                # print "reading from table: %s" % (self.tablename)
                exec_string = "SELECT * from %s WHERE ID IN (SELECT MAX(ID) FROM %s);" % (self.tablename, self.tablename)
                #exec_string = "SELECT * FROM %s;" % (tablename)
                def lastRowFetch(cursor):
                    cursor.execute(exec_string)
                    row = cursor.fetchall()
                    return row[0] if len(row) > 0 else None
                if callback:
                    # return self._dbconnection.dbInteract(True, lastRowFetch, callback=callback)
                    result = self._dbconnection.dbInteract(True, lastRowFetch)
                    # t = result.callback()
                    # return callback(t)
                    if self._dbconnection.isAsync():
                        return result.addCallback(callback)
                    else:
                        return callback(result)
                else:
                    return self._dbconnection.dbInteract(True, lastRowFetch)
            # end def
            self.readLastRow = types.MethodType(readLastRow,self)

            def addToTable(target, *args):
                """
                abstracted way to add things to the table
                values is a tuple
                """
                print "inserting into table: %s" % (self.tablename)
                if not self.typeCheckFields(*args):
                    print "TypeError adding to a table"
                    print args
                    raise TypeError("TypeError adding to a table")
                execute_string = "INSERT INTO %s(TIMESTAMP, " % (self.tablename)
                val_string = " VALUES (?, " # first question mark for timestamp
                for field in fieldList:
                    execute_string += "%s, " % (field.name)
                    val_string += "?, "
                # end for
                # drop the last comma and spaces and add parentheses
                execute_string = execute_string[0:-2]  + ') ' + val_string[0:-2] + ");"
                # print "trying to add to table"
                # print execute_string, args
                def execAdd(cursor, *vals):
                    # pack it up with a time stamp
                    ts = time.time()
                    cursor.execute(execute_string, (ts,) + vals)
                    return ts
                # pass the unpacked tuple
                return self._dbconnection.dbInteract(False, execAdd, *args)
            # end def
            self.addToTable = types.MethodType(addToTable,self)

            self._field_list = fieldList
        # end if
    #end def

    def confirmEvent(self):
        def confirmLast(cursor):
            exec_string = "UPDATE %s SET CONFIRM=1 WHERE TIMESTAMP=%d;" % (self.tablename, cursor.lastrowid)
            cursor.execute(exec_string)
        self._dbconnection.dbInteract(False, confirmLast)
    # def

    def typeCheckFields(self, *args):
        for arg, field in itertools.izip(args, self._field_list):
            if field.typeCheck(arg):
                continue
            else:
                print "Bad type", field.name, arg
                return False
        # end for
        return True
    # end def

    def typeCheckDict(self, the_dict):
        for field in self._field_list:
            if field.typeCheck(the_dict[field.name]):
                continue
            else:
                print "Bad type", field.name, the_dict[field.name]
                return False
        # end for
        return True
    # end def

    def fieldCheckDict(self, the_dict):
        for field in self._field_list:
            if not field.name in the_dict:
                return False
        # end for
        return True
    # end def

    def rowToDict(self, row):
        """
        Takes the output of a query of a row and turns it into an
        Ordered dictionary based on field_order
        """
        # print "my row ZZZZZZZZZZZZZZZZZZZZZZZZ"
        output = OrderedDict()
        output['ID'] = row[0]
        output['TIMESTAMP'] = row[1]
        i = 2
        for field in self._field_list:
            output[field.name] = row[i]
            i += 1
        #end for
        return output
    # end def

    def dictToRow(self, the_dict):
        """
        Takes dictionary corresponding to fieldnames and converts
        it to a list ordered by field.order_number
        """
        row = []
        for field in self._field_list:
            row.append(the_dict[field.name])
        #end for
        return row
    # end def

    def getDict(self):
        if self._dbconnection.isAsync():
            return self.readLastRow(callback=self.rowToDict)
        else:
            return self.rowToDict(self.readLastRow())
    # end def

    def getDefaults(self, config_file):
        """
        expects a default JSON formatted file
        return the OrderedDictionay of the fields
        """
        try:
            f = open(config_file)
        except IOError, e:
            print "IOError: No such file or directory: %s" % (e.args[0])
            sys.exit(1)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print "In: ", inspect.stack()[1][3]
        try:
            defaults = json.load(f)
        except ValueError, e:
            print "ValueError: no good JSON %s" % (e.args[0])
            sys.exit(1)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print "In: ", inspect.stack()[1][3]
        outDict = OrderedDict()
        for field in self._field_list:
            if field.name in defaults:
                outDict[field.name] = defaults[field.name]
            else:
                raise Exception("Field name [%s] missing from file" % field.name)
                sys.exit(1)
            # end else
        # end for
        return outDict
    # end def

    def loadDefaults(self, default_dict):
        """
        expects a Ordered Dictionary
        """
        self.addToTable(*default_dict.values())
# end class

class ExperimentDBIFC(object):
    def __init__(self, config_file):
        """
        Do useful work with this by:
        1) Initializing with a config file
        2) get the database path
        3) use that to create a database connection
        4) (optional) Then create tables as needed
        """
        self._config_file = config_file
        self._parameters = None # this will be set to be an ordered dict
        self._pendingState = defaultdict(dict) #this makes sure we can write to any channel
        self.setTableNames(config_file)
    # end def

    def dbPath(self):
        """
        return the database path
        """
        return self._parameters['DB_PATH']
    # end def

    def setConnection(self, dbconnection):
        self._param_table_ifc.setConnection(dbconnection)
        for dtifc in self._data_table_ifc_list:
            dtifc.setConnection(dbconnection)
        for dtifc in self._event_table_ifc_list:
            dtifc.setConnection(dbconnection)
    # end def

    def createTables(self):
        """
        create the parameter, data(s), and event tables.  Drop them first if they
        exist
        """
        self._param_table_ifc.dropTable()
        self._param_table_ifc.createTable()
        for dtifc in self._data_table_ifc_list:
            dtifc.dropTable()
            dtifc.createTable()
        for dtifc in self._event_table_ifc_list:
            dtifc.dropTable()
            dtifc.createTable()
        # initialize the parameters
        self._param_table_ifc.loadDefaults(self._parameters)
    # end def

    def setTableNames(self, config_file):
        default_params = self._param_table_ifc.getDefaults(config_file)
        jobname = default_params['jobname']
        self._param_table_ifc.setTablename(jobname+'_params')
        channel = 0
        for dtifc in self._data_table_ifc_list:
            dtifc.setTablename(jobname+'_data_'+str(channel))
            channel += 1
        # end for
        channel = 0
        for dtifc in self._event_table_ifc_list:
            dtifc.setTablename(jobname+'_event_'+str(channel))
            channel += 1
        # end for
        self._parameters = default_params
    # end def

    def getURL(self):
        """
        Assumes parameters has been set
        """
        return self._parameters['URL']
    # end def

    def jobname(self):
        """
        Every experiments gotta have a name
        """
        return self._parameters['jobname']

    def getDBPath(self):
        """
        Assumes parameters has been set
        """
        return self._parameters['DB_PATH']
    # end def

    def parameterUpdatePeriod(self):
        """
        Assumes parameters has been set
        """
        return self._parameters['PARAM_UPDATE_PERIOD']
    # end def

    def controlPeriod(self):
        return self._parameters['CONTROL_PERIOD']
    #end def

    def isSystemOn(self):
        # print "FFFFF System is, ", self._parameters['SYSTEM_ON']
        return True if self._parameters['SYSTEM_ON'] == 1 else False
     # end def

    def isControlOn(self):
        return True if self._parameters['CONTROL_ON'] == 1 else False
    # end def

    def killControl(self):
        # self._parameters['CONTROL_ON'] = 0
        # self.updateParamDict(self._parameters)
        new_params = {'CONTROL_ON': 0}
        self.updateParamDict(new_params)
        # print "Control has been turned on?", self.isControlOn()
    # end def

    def samplePeriod(self, channel):
        return self._parameters['SAMPLE_PERIOD_' + str(channel)]
    #end def

    def updateParams(self):
        return self._param_table_ifc.getDict()
    # end def

    def paramsUpdated(self, params):
        """
        the db request for the parameters has finished and we can set the
        parameter cache dictionary
        """
        self._parameters = params
    # end def

    def getParams(self):
        """
        cache the parameters and returns the updated
        """
        return self._parameters
    #end def

    def setParams(self, *args):
        """
        Parameters are only updated on change
        """
        if not self.compareParameters(*args):
            self._param_table_ifc.addToTable(*args)
    # end def

    def compareParameters(self, *args):
        """
        efficiently compare to arbitrary lists
        if self._parameters hasn't been set (AKA NONE) then we return False
        """
        params = self._parameters
        if params:
            currentvalues = params.itervalues()
            for arg in args:
                 if arg != currentvalues.next():
                    return False
            # end for
            return True
        else:
            return False
    # end def

    def checkMeasurement(self, channel, data_dict):
        dtifc = self._data_table_ifc_list[channel]
        if dtifc.fieldCheckDict(data_dict):
            if dtifc.typeCheckDict(data_dict):
                return True
        return False
    # end def

    def addMeasurement(self, channel, data_dict):
        """
        return a deferred that will ultimately return the timestamp
        data was registered at
        """
        dtifc = self._data_table_ifc_list[channel]
        return dtifc.addToTable(*dtifc.dictToRow(data_dict))
    # end def

    def getMeasurement(self, channel):
        return self._data_table_ifc_list[channel].getDict()
    #end def

    def setMeasurement(self, channel, *args):
        dtifc = self._data_table_ifc_list[channel]
        dtifc.addToTable(*args)
    #end def

    def checkState(self, channel, state_dict):
        dtifc = self._event_table_ifc_list[channel]
        if dtifc.fieldCheckDict(state_dict):
            if dtifc.typeCheckDict(state_dict):
                return True
        return False
    # end def

    def confirmState(self, channel, state_dict):
        """
        confirms that the last state change was in fact registered by the
        device
        """
        dtifc = self._event_table_ifc_list[channel]
        pending_dict = self._pendingState[channel]
        confirm = True
        for key, val in pending_dict.items():
            if val != state_dict[key]:
                confirm = False
        # end for
        if confirm:
            dtifc.confirmEvent()
        else:
            sys.exit("Unconfirmed event")
    # end def

    def addEvent(self, channel, state_dict):
        """
        return a deferred that will ultimately return the timestamp
        state was registered at
        """
        self._pendingState[channel] = state_dict
        dtifc = self._event_table_ifc_list[channel]
        return dtifc.addToTable(*dtifc.dictToRow(state_dict))
    # end def

    def getEvents(self, channel):
        return self._event_table_ifc_list[channel].getDict()
    #end def

    def setEvents(self, channel, *args):
        self._event_table_ifc_list[channel].addToTable(*args)
    #end def

    def updateParamDict(self, newdict):
        olddict = self._parameters
        fieldlist = self._param_table_ifc._field_list
        change_list = self.jsonToDict(fieldlist, newdict, olddict)
        if len(change_list) > 0:    # was at least one thing different?
            dtifc = self._param_table_ifc
            dtifc.addToTable(*dtifc.dictToRow(self._parameters))
        return change_list
    # end def

    def jsonToDict(self, fieldlist, newdict, olddict):
        change_list = []
        for field in fieldlist:
            key = field.name
            if newdict.has_key(key) and olddict.has_key(key):
                val = field.typeFix(newdict[key])
                if val != olddict[key]:
                    olddict[key] = val
                    change_list.append((key, val))
            # end if
        # end for
        return change_list
    # end def

    def jsonListifyParameters(self, advanced=False):
        thedict = self._parameters
        fieldlist = self._param_table_ifc._field_list
        return self.jsonListifyDict(thedict, fieldlist, advanced=advanced)
    # end def

    def jsonListifyDict(self, thedict, fieldlist, advanced):
        if advanced:
            return [{'key':field.name,'value':str(thedict[field.name]), 'note':field.note} for field in fieldlist]
        else:
            out_list = []
            for field in fieldlist:
                if not field.isAdvanced():
                    out_list.append({'key':field.name,'value':str(thedict[field.name]), 'note':field.note})
                # end if
            # end for
            return out_list
        # end else
    # end def
# end class

def setupExperiment(module, control_on=False, datapush=None, debug=False):
    """
    take a folder for an experiment on the PYTHON_PATH and sets up an
    experiment

    looks for *_evo.json files in the path with the _evo suffix

    control_on = True when this is called from a twisted asyncronous code
    control_on = False when called from the WSGI framework Flask
    """
    import glob
    experimentmodule = __import__(module)
    experimentpath = experimentmodule.__path__[0]

    # 1. Look for configuration files
    if os.path.exists(experimentpath) and os.path.isdir(experimentpath):
        config_files = glob.glob(os.path.join(experimentpath, '*_evo.json'))
        if len(config_files) < 1:
            sys.exit("Could not find config files in %s" % (experimentpath))

    # 2. import the experiment classes
    # create the string for the classes
    modclass_str = module[0].capitalize() + module[1:]
    dbifc_str = modclass_str + 'DBInterface'
    dbifc_d = __import__(module+'.dbifc', globals(), locals(), fromlist=[dbifc_str])
    DatabaseInterface = getattr(dbifc_d, dbifc_str)
    controlloop_str = modclass_str + 'Loop'
    controlloop_d = __import__(module+'.loop', globals(), locals(), fromlist=[controlloop_str])
    ControlLoop = getattr(controlloop_d, controlloop_str)

    # 3. create a control loop if called from a twisted otherwise don't
    out_dict = OrderedDict()   # return a list of the main things created
    for cfg_file in config_files:
        if control_on:
            exp_db_ifc = DatabaseInterface(cfg_file)
            db_path = exp_db_ifc.dbPath()
            conn = DataBaseConnection(db_path, async=True)
            exp_db_ifc.setConnection(conn)
            cL = ControlLoop(exp_db_ifc, debug)
            if datapush:
                cL.addSubscriber(datapush)
            out_dict[exp_db_ifc.jobname()] = cL
        else:
            # initializing actually creates the table in the DB
            # need to do this once only
            exp_db_ifc = DatabaseInterface(cfg_file)
            db_path = exp_db_ifc.dbPath()
            conn = DataBaseConnection(db_path, async=False)
            exp_db_ifc.setConnection(conn)
            exp_db_ifc.createTables()
            out_dict[exp_db_ifc.jobname()] = exp_db_ifc
    # end for
    return out_dict
# end def

def jsonKeyVal(mydict):
    return [{'key':key,'value':str(value)} for key, value in mydict.iteritems()]
# end def

if __name__ == "__main__":
    """
    Run some tests on this file, does not test twisted stuff
    """
    # import os
    import inspect

    class EventTableInterface(TableInterface):

        def __init__(self, tablename):
            self.valve0 = IntField()
            self.valve1 = StringField()
            self.valve2 = IntField()
            # the super init comes last!!!!
            super(EventTableInterface, self).__init__(tablename)
        # end def
    # end def

    class ParameterTableInterface(TableInterface):
        def __init__(self, tablename):
            self.volume0 = StringField()
            self.volume_min = IntField()
            # the super init comes last!!!!
            super(ParameterTableInterface, self).__init__(tablename)
        # end def
    # end def

    homepath = os.getenv('USERPROFILE') or os.getenv('HOME')
    testdb = homepath + '/mytestDB'
    if os.path.exists(testdb):
        print "deleting existing database %s" % (testdb)
        os.remove(testdb)
    # end if
    print "creating database %s" % (testdb)
    createDB(testdb)
    conn = DataBaseConnection(testdb)
    a = EventTableInterface("testEventTable")
    # a.createAccessors()
    b = ParameterTableInterface("testParameterTable")
    # b.createAccessors()
    print "###### testing A #######"
    a.testTable()
    print "fields A"
    print a.fields
    print "###### testing B #######"
    b.testTable()
    print "fields B"
    print b.fields
    print pformat(inspect.getmembers(a, predicate=inspect.ismethod))
    print pformat(inspect.getmembers(b, predicate=inspect.ismethod))
    a.setConnection(conn)
    print "######## dropping A from DB if it exists"
    a.dropTable()
    print "######## creating A in the DB"
    a.createTable()
    print "######## reading from an empty A in the DB"
    print a.readLastRow()
    print "######## adding to A in DB"
    a.addToTable(4,"something", 7)
    print "######## reading from A in the DB"
    print a.readLastRow()
    print a.rowToDict(a.readLastRow())
    b.setConnection(conn)
    print "######## dropping B from DB if it exists"
    b.dropTable()
    print "######## creating B in the DB"
    b.createTable(config_file='test.json')
    print "######## reading from default from B in the DB"
    print b.readLastRow()
    print "######## adding to B in DB"
    b.addToTable("something", 7)
    print "######## reading from B in the DB"
    print b.readLastRow()
    print b.rowToDict(b.readLastRow())
    print "######## adding to B again in DB"
    b.addToTable("pooop", 30)
    print "######## reading from B again in the DB"
    print b.readLastRow()
    print b.rowToDict(b.readLastRow())
