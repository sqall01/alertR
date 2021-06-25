#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import re
import os
import logging
import time
from typing import Optional, Union
from .number import _NumberSensor
from ..globalData import SensorDataType


class RaspberryPiDS18b20Sensor(_NumberSensor):
    """
    Represents one DS18b20 sensor connected to the Raspberry Pi.
    """

    def __init__(self):
        _NumberSensor.__init__(self)

        # Used for logging.
        self.fileName = os.path.basename(__file__)

        # Set sensor to hold float data.
        self.sensorDataType = SensorDataType.FLOAT

        # The file of the sensor that should be parsed.
        self._sensor_file = None

        # The name of the sensor that should be parsed.
        self.sensorName = None

        # The interval in seconds in which an update of the current held data
        # should be sent to the server.
        self.interval = None

        # The time the last update of the data was sent to the server.
        self._last_update = None

        self._last_temperature_update = 0.0

    def _get_data(self) -> Optional[Union[float, int]]:
        """
        Internal function that reads the data of the DS18b20 sensor.

        :return: temperature value or None
        """

        utc_timestamp = int(time.time())
        if (utc_timestamp - self._last_temperature_update) > self.interval:
            self._last_temperature_update = utc_timestamp

            try:
                with open(self._sensor_file, 'r') as fp:

                    # File content looks like this:
                    # 2d 00 4b 46 ff ff 04 10 b3 : crc=b3 YES
                    # 2d 00 4b 46 ff ff 04 10 b3 t=22500
                    fp.readline()
                    line = fp.readline()

                    reMatch = re.match("([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line)
                    if reMatch:
                        return float(reMatch.group(2)) / 1000

                    else:
                        logging.error("[%s]: Could not parse sensor file." % self.fileName)

            except Exception as e:
                logging.exception("[%s]: Could not read sensor file." % self.fileName)

            return None

        else:
            return self.sensorData

    def initialize(self) -> bool:
        self.state = 1 - self.triggerState

        self._sensor_file = "/sys/bus/w1/devices/" \
                            + self.sensorName \
                            + "/w1_slave"

        # First time the temperature is updated is done in a blocking way.
        utc_timestamp = int(time.time())
        self.sensorData = self._get_data()
        self._last_temperature_update = utc_timestamp

        if self.sensorData is None:
            return False

        self._last_update = utc_timestamp
        self._optional_data = {"sensorName": self.sensorName}

        return True
