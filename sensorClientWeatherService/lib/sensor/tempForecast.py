#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import logging
from .core import _PollingSensor
from ..localObjects import SensorDataType, Ordering, SensorAlert, StateChange
from typing import Optional


# Class that controls one forecast temperature sensor.
class ForecastTempPollingSensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # Used for logging.
        self.fileName = os.path.basename(__file__)

        # Set sensor to hold float data.
        self.sensorDataType = SensorDataType.FLOAT

        self._forceSendState = False

        # Instance of data collector thread.
        self.dataCollector = None

        self.country = None
        self.city = None
        self.lon = None
        self.lat = None
        self.day = None
        self.kind = None

        # This flag indicates if this sensor has a threshold that should be
        # checked and raise a sensor alert if it is reached.
        self.hasThreshold = False

        # The threshold that should raise a sensor alert if it is reached.
        self.threshold = None

        # Says how the threshold should be checked
        # (lower than, equal, greater than).
        self.ordering = None

    def initializeSensor(self):
        self.hasLatestData = False
        self.changeState = False
        self.state = 1 - self.triggerState

        # Update data directly for the first time.
        self.updateState()

        self.hasOptionalData = True
        self.optionalData = {"country": self.country,
                             "city": self.city,
                             "lon": self.lon,
                             "lat": self.lat,
                             "type": "forecasttemp",
                             "kind": self.kind,
                             "day": self.day}

        return True

    def getState(self):
        return self.state

    def updateState(self):
        if self.kind == "HIGH":
            temp = self.dataCollector.getForecastTemperatureHigh(
                self.country, self.city, self.lon, self.lat, self.day)
        else:
            temp = self.dataCollector.getForecastTemperatureLow(
                self.country, self.city, self.lon, self.lat, self.day)
        if temp != self.sensorData:
            self.sensorData = temp
            self._forceSendState = True

        # Only check if threshold is reached if it is activated.
        if self.hasThreshold:

            # Sensor is currently triggered.
            # Check if it is "normal" again.
            if self.state == self.triggerState:
                if self.ordering == Ordering.LT:
                    if self.sensorData >= self.threshold and self.sensorData >= -273.0:
                        self.state = 1 - self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is above threshold (back to normal).")

                elif self.ordering == Ordering.EQ:
                    if self.sensorData != self.threshold and self.sensorData >= -273.0:
                        self.state = 1 - self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is unequal to threshold (back to normal).")

                elif self.ordering == Ordering.GT:
                    if -273.0 <= self.sensorData <= self.threshold:
                        self.state = 1 - self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is below threshold (back to normal).")

                else:
                    logging.error("[%s]: Do not know how to check threshold. "
                                  % self.fileName
                                  + "Skipping check.")

            # Sensor is currently not triggered.
            # Check if it has to be triggered.
            else:
                if self.ordering == Ordering.LT:
                    if -273.0 <= self.sensorData < self.threshold:
                        self.state = self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is below threshold (triggered).")

                elif self.ordering == Ordering.EQ:
                    if self.sensorData == self.threshold and self.sensorData >= -273.0:
                        self.state = self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is equal to threshold (triggered).")

                elif self.ordering == Ordering.GT:
                    if self.sensorData > self.threshold and self.sensorData >= -273.0:
                        self.state = self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is above threshold (triggered).")

                else:
                    logging.error("[%s]: Do not know how to check threshold. "
                                  % self.fileName
                                  + "Skipping check.")

    def forceSendAlert(self) -> Optional[SensorAlert]:
        return None

    def forceSendState(self) -> Optional[StateChange]:
        if self._forceSendState:
            self._forceSendState = False

            stateChange = StateChange()
            stateChange.clientSensorId = self.id
            if self.state == self.triggerState:
                stateChange.state = 1
            else:
                stateChange.state = 0
            stateChange.dataType = self.sensorDataType
            stateChange.sensorData = self.sensorData

            return stateChange
        return None
