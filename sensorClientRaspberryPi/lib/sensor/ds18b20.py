#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import re
import os
import logging
import time
from .core import _PollingSensor
from ..localObjects import SensorDataType, SensorAlert, StateChange, Ordering
from typing import Optional


# Class that reads one DS18b20 sensor connected to the Raspberry Pi.
class RaspberryPiDS18b20Sensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # Used for logging.
        self.fileName = os.path.basename(__file__)

        # Set sensor to hold float data.
        self.sensorDataType = SensorDataType.FLOAT

        # The file of the sensor that should be parsed.
        self.sensorFile = None

        # The name of the sensor that should be parsed.
        self.sensorName = None

        # The interval in seconds in which an update of the current held data
        # should be sent to the server.
        self.interval = None

        # The time the last update of the data was sent to the server.
        self.lastUpdate = None

        # This flag indicates if this sensor has a threshold that should be
        # checked and raise a sensor alert if it is reached.
        self.hasThreshold = None

        # The threshold that should raise a sensor alert if it is reached.
        self.threshold = None

        # Says how the threshold should be checked
        # (lower than, equal, greater than).
        self.ordering = None

        # To keep the traffic on the bus low, only allow temperature refreshes
        # every 60 seconds.
        self.refreshInterval = 60
        self.lastTemperatureUpdate = 0.0

        # Locks temperature value in order to be thread safe.
        self.updateLock = threading.Semaphore(1)

        # Internal sensor data value only accessed when locked.
        self._sensorData = None

    # Internal function that reads the data of the sensor.
    def _updateData(self):

        try:
            with open(self.sensorFile, 'r') as fp:

                # File content looks like this:
                # 2d 00 4b 46 ff ff 04 10 b3 : crc=b3 YES
                # 2d 00 4b 46 ff ff 04 10 b3 t=22500
                fp.readline()
                line = fp.readline()

                reMatch = re.match("([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line)
                if reMatch:

                    temp = float(reMatch.group(2)) / 1000
                    self.updateLock.acquire()
                    self._sensorData = temp
                    self.updateLock.release()

                else:
                    logging.error("[%s]: Could not parse sensor file." % self.fileName)

        except Exception as e:
            logging.exception("[%s]: Could not read sensor file." % self.fileName)

    def initializeSensor(self) -> bool:
        self.hasLatestData = True
        self.changeState = True

        self.state = 1 - self.triggerState

        self.sensorFile = "/sys/bus/w1/devices/" \
                          + self.sensorName \
                          + "/w1_slave"

        # First time the temperature is updated is done in a blocking way.
        utcTimestamp = int(time.time())
        self._updateData()
        self.lastTemperatureUpdate = utcTimestamp
        self.updateLock.acquire()
        self.sensorData = self._sensorData
        self.updateLock.release()

        if not self.sensorData:
            return False

        self.lastUpdate = utcTimestamp

        self.hasOptionalData = True
        self.optionalData = {"sensorName": self.sensorName}

        return True

    def getState(self) -> int:
        return self.state

    def updateState(self):

        # Restrict the times the temperature is actually read from the sensor
        # to keep the traffic on the bus relatively low.
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.lastTemperatureUpdate) > self.interval:
            self.lastTemperatureUpdate = utcTimestamp

            # Update temperature in a non-blocking way
            # (this means also, that the current temperature value will
            # not be the updated one, but one of the next rounds will have it)
            thread = threading.Thread(target=self._updateData)
            thread.daemon = True
            thread.start()

        self.updateLock.acquire()
        self.sensorData = self._sensorData
        self.updateLock.release()

        logging.debug("[%s]: Current temperature of sensor '%s': %.3f."
                      % (self.fileName, self.description, self.sensorData))

        # Only check if threshold is reached if it is activated.
        if self.hasThreshold:

            # Sensor is currently triggered.
            # Check if it is "normal" again.
            if self.state == self.triggerState:
                if self.ordering == Ordering.LT:
                    if self.sensorData >= self.threshold:
                        self.state = 1 - self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is above threshold (back to normal).")

                elif self.ordering == Ordering.EQ:
                    if self.sensorData != self.threshold:
                        self.state = 1 - self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is unequal to threshold (back to normal).")

                elif self.ordering == Ordering.GT:
                    if self.sensorData <= self.threshold:
                        self.state = 1 - self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is below threshold (back to normal).")

                else:
                    logging.error("[%s]: Do not know how to check threshold. Skipping check." % self.fileName)

            # Sensor is currently not triggered.
            # Check if it has to be triggered.
            else:
                if self.ordering == Ordering.LT:
                    if self.sensorData < self.threshold:
                        self.state = self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is below threshold (triggered).")

                elif self.ordering == Ordering.EQ:
                    if self.sensorData == self.threshold:
                        self.state = self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is equal to threshold (triggered).")

                elif self.ordering == Ordering.GT:
                    if self.sensorData > self.threshold:
                        self.state = self.triggerState
                        logging.info("[%s]: Temperature %.3f of sensor '%s' "
                                     % (self.fileName, self.sensorData, self.description)
                                     + "is above threshold (triggered).")

                else:
                    logging.error("[%s]: Do not know how to check threshold. Skipping check." % self.fileName)

    def forceSendAlert(self) -> Optional[SensorAlert]:
        return None

    def forceSendState(self) -> Optional[StateChange]:
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.lastUpdate) > self.interval:
            self.lastUpdate = utcTimestamp

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
