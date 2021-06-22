#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from .number import _NumberSensor
from ..globalData import SensorDataType
from typing import Union


# Class that controls one temperature sensor.
class TempPollingSensor(_NumberSensor):

    def __init__(self):
        _NumberSensor.__init__(self)

        # Used for logging.
        self._log_tag = os.path.basename(__file__)

        # Set sensor to hold float data.
        self.sensorDataType = SensorDataType.FLOAT

        # Instance of data collector thread.
        self.dataCollector = None

        self.country = None
        self.city = None
        self.lon = None
        self.lat = None

        # As long as errors occurring during the fetching of data are encoded as negative values,
        # we need the lowest value that we use for our threshold check.
        self._sane_lowest_value = -273.0

        # This sensor type string is used for log messages.
        self._log_desc = "Temperature"

    def _get_data(self) -> Union[float, int]:
        return self.dataCollector.getTemperature(self.country, self.city, self.lon, self.lat)

    def initialize(self) -> bool:
        self.state = 1 - self.triggerState

        self._optional_data = {"country": self.country,
                               "city": self.city,
                               "lon": self.lon,
                               "lat": self.lat,
                               "type": "temperature"}

        return True
