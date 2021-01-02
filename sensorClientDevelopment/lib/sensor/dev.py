#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from .core import _PollingSensor
from ..globalData import SensorDataType, SensorObjSensorAlert, SensorObjStateChange
from typing import Optional


# class that represents one emulated sensor that can be triggered via keyboard
class SensorDev(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # used for logging
        self.fileName = os.path.basename(__file__)

        self.consoleInputState = 0

        # Field in which the next send data is added.
        self.nextData = None

    def initializeSensor(self) -> bool:
        self.changeState = True
        self.hasLatestData = True
        self.state = self.consoleInputState

        # Initialize the data the sensor holds.
        if self.sensorDataType == SensorDataType.NONE:
            self.hasLatestData = False
        elif self.sensorDataType == SensorDataType.INT:
            self.sensorData = 0
            self.nextData = self.sensorData + 1
        elif self.sensorDataType == SensorDataType.FLOAT:
            self.sensorData = 0.0
            self.nextData = self.sensorData + 0.5

        return True

    def getState(self) -> int:
        return self.state

    def updateState(self):
        self.state = self.consoleInputState

    def forceSendAlert(self) -> Optional[SensorObjSensorAlert]:
        return None

    def forceSendState(self) -> Optional[SensorObjStateChange]:
        return None

    def toggleConsoleState(self):

        # Update the data that the sensor holds.
        if self.sensorDataType == SensorDataType.NONE:
            pass
        elif self.sensorDataType == SensorDataType.INT:
            self.sensorData = self.nextData
            self.nextData += 1
        elif self.sensorDataType == SensorDataType.FLOAT:
            self.sensorData = self.nextData
            self.nextData += 0.5

        if self.consoleInputState == 0:
            self.consoleInputState = 1
        else:
            self.consoleInputState = 0
