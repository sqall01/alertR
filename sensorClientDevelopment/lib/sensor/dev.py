#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from .core import _PollingSensor
from ..globalData import SensorDataType
from ..globalData.sensorObjects import _SensorData, SensorDataNone, SensorDataInt, SensorDataFloat
from typing import Optional


class DevSensor(_PollingSensor):
    """
    Class that represents one emulated sensor that can be triggered via keyboard.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # used for logging
        self._log_tag = os.path.basename(__file__)

        self.consoleInputState = 0

        # Field in which the next send data is added.
        self.nextData = None  # type: Optional[_SensorData]

    def _execute(self):
        pass

    def initialize(self) -> bool:
        self.state = self.consoleInputState

        # Initialize the data the sensor holds.
        if self.sensorDataType == SensorDataType.NONE:
            self.sensorData = SensorDataNone()
            self.nextData = SensorDataNone()

        if self.sensorDataType == SensorDataType.INT:
            self.sensorData = SensorDataInt(0, "Dev")
            self.nextData = SensorDataInt(self.sensorData.value + 1, self.sensorData.unit)

        elif self.sensorDataType == SensorDataType.FLOAT:
            self.sensorData = SensorDataFloat(0.0, "Dev")
            self.nextData = SensorDataFloat(self.sensorData.value + 0.5, self.sensorData.unit)

        return True

    def toggle_console_state(self):

        # Update the data that the sensor holds.
        if self.sensorDataType == SensorDataType.NONE:
            pass

        elif self.sensorDataType == SensorDataType.INT:
            self.sensorData = self.nextData
            # noinspection PyTypeChecker
            self.nextData = SensorDataInt(self.sensorData.value + 1, self.sensorData.unit)

        elif self.sensorDataType == SensorDataType.FLOAT:
            self.sensorData = self.nextData
            # noinspection PyTypeChecker
            self.nextData = SensorDataFloat(self.sensorData.value + 0.5, self.sensorData.unit)

        if self.consoleInputState == 0:
            self.consoleInputState = 1
        else:
            self.consoleInputState = 0

        new_state = self.consoleInputState

        if new_state == self.triggerState:
            if self.triggerAlert:
                self._add_sensor_alert(self.triggerState,
                                       True,
                                       has_latest_data=True,
                                       sensor_data=self.sensorData)

            else:
                self._add_state_change(self.triggerState,
                                       self.sensorData)

        else:
            if self.triggerAlertNormal:
                self._add_sensor_alert(1 - self.triggerState,
                                       True,
                                       has_latest_data=True,
                                       sensor_data=self.sensorData)

            else:
                self._add_state_change(1 - self.triggerState,
                                       self.sensorData)
