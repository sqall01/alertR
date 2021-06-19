#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from .base import _WeatherSensor
from ..globalData import SensorDataType
from typing import Union


# Class that controls one forecast temperature sensor.
class ForecastTempPollingSensor(_WeatherSensor):

    def __init__(self):
        _WeatherSensor.__init__(self)

        # Used for logging.
        self._log_tag = os.path.basename(__file__)

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

        # As long as errors occurring during the fetching of data are encoded as negative values,
        # we need the lowest value that we use for our threshold check.
        self._sane_lowest_value = 0

        # This sensor type string is used for log messages.
        self._sensor_type = "Temperature forecast"

    def _get_data(self) -> Union[float, int]:
        if self.kind == "HIGH":
            return self.dataCollector.getForecastTemperatureHigh(self.country, self.city, self.lon, self.lat, self.day)

        else:
            return self.dataCollector.getForecastTemperatureLow(self.country, self.city, self.lon, self.lat, self.day)

    def initialize(self) -> bool:
        self.state = 1 - self.triggerState

        self._optional_data = {"country": self.country,
                               "city": self.city,
                               "lon": self.lon,
                               "lat": self.lat,
                               "type": "forecasttemp",
                               "kind": self.kind,
                               "day": self.day}

        return True
