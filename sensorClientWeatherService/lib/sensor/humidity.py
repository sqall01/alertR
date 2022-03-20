#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from typing import Optional
from .number import _NumberSensor
# noinspection PyProtectedMember
from .provider.core import _DataCollector
from ..globalData.sensorObjects import SensorDataInt, SensorDataType, SensorErrorState


class HumidityPollingSensor(_NumberSensor):
    """
    Class that controls one humidity sensor.
    """

    def __init__(self):
        _NumberSensor.__init__(self)

        self._unit = "%"

        # Used for logging.
        self._log_tag = os.path.basename(__file__)

        # Set sensor to hold float data.
        self.sensorDataType = SensorDataType.INT
        self.data = SensorDataInt(-1000, self._unit)

        # Instance of data collector thread.
        self.dataCollector = None  # type: Optional[_DataCollector]

        self.country = None
        self.city = None
        self.lon = None
        self.lat = None

        # This sensor type string is used for log messages.
        self._log_desc = "Humidity"

    def _get_data(self) -> Optional[SensorDataInt]:
        data = None
        # noinspection PyBroadException
        try:
            provider_data = self.dataCollector.getHumidity(self.country, self.city, self.lon, self.lat)
            if provider_data.data is None:
                self._set_error_state(provider_data.error.state, provider_data.error.msg)
            else:
                data = SensorDataInt(provider_data.data,
                                     self._unit)

        except Exception as e:
            self._log_exception(self._log_tag, "Unable to get data from provider.")
            self._set_error_state(SensorErrorState.ProcessingError,
                                  "Unable to get data from provider: " + str(e))

        return data

    def initialize(self) -> bool:
        self.state = 1 - self.triggerState

        self._optional_data = {"country": self.country,
                               "city": self.city,
                               "lon": self.lon,
                               "lat": self.lat,
                               "type": "humidity"}

        return True
