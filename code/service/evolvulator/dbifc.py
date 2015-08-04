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
dbifc.py
"""

from experimentcore.exp_dbifc import ExperimentDBIFC, TableInterface
from experimentcore.exp_dbifc import IntField, FloatField, StringField
import traceback
import sys

class DataTableInterface(TableInterface):

    def __init__(self):
        self.PHOTODIODE0 = IntField(note='10bit ADC sensor Data')
        self.PHOTODIODE1 = IntField(note='10bit ADC sensor Data')
        # the super init comes last!!!!
        super(DataTableInterface, self).__init__()
    # end def
# end def

class EventTableInterface(TableInterface):

    def __init__(self):
        self.VALVE0 = IntField(note='[int] 1 or 0 for open/close')
        self.VALVE1 = IntField(note='[int] 1 or 0 for open/close')
        # self.VOLUME = FloatField(note='[mL] Supply Reservoir Volume')
        # the super init comes last!!!!
        super(EventTableInterface, self).__init__()
    # end def
# end def

class ParameterTableInterface(TableInterface):
    def __init__(self):
        self.jobname = StringField(adv=False,
                            note='name of the specfic Evolvulator device')
        self.experiment_description = StringField(adv=False,
                            note='description of running experiment')
        self.URL = StringField(adv=True,
                            note='network locaction of the device')
        self.DB_PATH = StringField(adv=True,
                            note='database to record to')
        self.SYSTEM_ON = IntField(adv=True,
                            note='is anything being done with the experiment')
        self.CONTROL_ON = IntField(adv=True,
                            note='is the loop closed on the experiment by the user')
        self.PARAM_UPDATE_PERIOD = FloatField(adv=True,
                            note='[s] time to update parameters from GUI')
        self.CONTROL_PERIOD = FloatField(adv=True,
                            note='[s] time to execute the control loop')
        self.SAMPLE_PERIOD_0 = FloatField(adv=True,
                            note='[s] time to sample on channel 0')
        self.VOLUME_START = FloatField(adv=True,
                            note='[mL] starting volume of reservoir')
        self.VOLUME_MIN = FloatField(adv=True,
                            note='[mL] ending volume or reservoir')
        self.TANK_DIA = FloatField( adv=True,
                                note='[mm] diameter of supply reservoir')
        self.EXIT_DIA = FloatField(adv=True,
                                note='[mm] diameter of exit tube orifice')
        self.HEIGHT_OFFSET = FloatField(adv=True,
                                note='[mm] distance between exit of reservoir and exit orifice')
        self.VOLUME_TARGET = FloatField(adv=True,
                                note='[mL] volume of growth chamber')
        self.PHOTODIODE0_MIN = IntField(adv=True,
                                note='[INT] ADC min measurement (dark current reading)')
        self.PHOTODIODE0_MAX = IntField(adv=True,
                                note='[INT] Blank sensor reading. CHECK ME ON EACH EXPT!!!')
        self.PHOTODIODE1_MIN = IntField(adv=True,
                                note='[INT] ADC min measurement (dark current reading)')
        self.PHOTODIODE1_MAX = IntField(adv=False,
                                note='[INT] Blank sensor reading. CHECK ME ON EACH EXPT!!!')
        self.MEDIA_DENSITY = FloatField(adv=True,
                                note='[kg/m^3] growth media density')
        self.FLOWCONSTANT = FloatField(adv=True,
                                note='[float] calibrated flow restriction constant')
        self.OD_TARGET = FloatField(adv=False,
                                note='[float] target optical density')
        self.OD_DELTA = FloatField(adv=False,
                                note='[float] fractional allowable +/- delta')
        self.OD_CONSTANT_0 = FloatField(adv=False,
                                note='[float] 1st calibration polynomial coefficient for conversion to nanoDrop equivalent')
        self.OD_CONSTANT_1 = FloatField(adv=False,
                                note='[float] 2nd calibration polynomial coefficient for conversion to nanoDrop equivalent')
        self.OD_CONSTANT_2 = FloatField(adv=True,
                                note='[float] for conversion from OD to dilution')
        # the super init comes last!!!!
        super(ParameterTableInterface, self).__init__()
    # end def
# end def

class EvolvulatorDBInterface(ExperimentDBIFC):
    def __init__(self, config_file):
        self._param_table_ifc = ParameterTableInterface()
        self._event_table_ifc_list = [EventTableInterface()]
        self._data_table_ifc_list = [DataTableInterface()]
        self.supply_volume = None
        super(EvolvulatorDBInterface, self).__init__(config_file)
    # end def

    def getSupplyVolume(self):
        if not self.supply_volume:
            self.supply_volume = self._parameters['VOLUME_START']
        return self.supply_volume
    # end def

    def setSupplyVolume(self, volume):
        self.supply_volume = volume
    # end def
# end class