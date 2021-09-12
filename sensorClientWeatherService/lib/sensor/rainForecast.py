#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import os
from typing import Optional
from .number import _NumberSensor
from ..globalData import SensorDataType
from ..globalData.sensorObjects import SensorDataInt


class ForecastRainPollingSensor(_NumberSensor):
    """
    Class that controls one forecast rain sensor.
    """

    def __init__(self):
        _NumberSensor.__init__(self)

        self._unit = "%"

        # Used for logging.
        self._log_tag = os.path.basename(__file__)

        # Set sensor to hold float data.
        self.sensorDataType = SensorDataType.INT
        self.sensorData = SensorDataInt(-1000, self._unit)

        # Instance of data collector thread.
        self.dataCollector = None

        self.country = None
        self.city = None
        self.lon = None
        self.lat = None
        self.day = None

        # As long as errors occurring during the fetching of data are encoded as negative values,
        # we need the lowest value that we use for our threshold check.
        self._sane_lowest_value = 0

        # This sensor type string is used for log messages.
        self._log_desc = "Chance of rain"

    def _get_data(self) -> Optional[SensorDataInt]:
        data = None
        try:
            data = SensorDataInt(self.dataCollector.getForecastRain(self.country,
                                                                    self.city,
                                                                    self.lon,
                                                                    self.lat,
                                                                    self.day),
                                 self._unit)

        except Exception as e:
            logging.exception("[%s] Unable to rain forecast data from provider." % self._log_tag)

        return data

    def initialize(self) -> bool:
        self.state = 1 - self.triggerState

        self._optional_data = {"country": self.country,
                               "city": self.city,
                               "lon": self.lon,
                               "lat": self.lat,
                               "type": "forecastrain",
                               "day": self.day}

        return True
