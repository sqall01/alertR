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
from ..globalData.sensorObjects import SensorDataFloat, SensorDataType, SensorErrorState


class ForecastTempPollingSensor(_NumberSensor):
    """
    Class that controls one forecast temperature sensor.
    """

    def __init__(self):
        _NumberSensor.__init__(self)

        self._unit = "°C"

        # Used for logging.
        self._log_tag = os.path.basename(__file__)

        # Set sensor to hold float data.
        self.sensorDataType = SensorDataType.FLOAT
        self.data = SensorDataFloat(-1000.0, self._unit)

        # Instance of data collector thread.
        self.dataCollector = None  # type: Optional[_DataCollector]

        self.country = None
        self.city = None
        self.lon = None
        self.lat = None
        self.day = None
        self.kind = None

        # This sensor type string is used for log messages.
        self._log_desc = "Temperature forecast"

    def _get_data(self) -> Optional[SensorDataFloat]:
        data = None
        # noinspection PyBroadException
        try:
            if self.kind == "HIGH":
                provider_data = self.dataCollector.getForecastTemperatureHigh(self.country,
                                                                              self.city,
                                                                              self.lon,
                                                                              self.lat,
                                                                              self.day)
                if provider_data.data is None:
                    self._set_error_state(provider_data.error.state, provider_data.error.msg)
                else:
                    data = SensorDataFloat(provider_data.data,
                                           self._unit)

            else:
                provider_data = self.dataCollector.getForecastTemperatureLow(self.country,
                                                                             self.city,
                                                                             self.lon,
                                                                             self.lat,
                                                                             self.day)
                if provider_data.data is None:
                    self._set_error_state(provider_data.error.state, provider_data.error.msg)
                else:
                    data = SensorDataFloat(provider_data.data,
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
                               "type": "forecasttemp",
                               "kind": self.kind,
                               "day": self.day}

        return True
