#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import threading
from typing import Union, Optional
from ...globalData import GlobalData
from ...globalData.sensorObjects import SensorErrorState


class WeatherData:
    """
    Class holds either data from the weather provider or an error state.
    """
    def __init__(self, data: Union[None, int, float], error: Optional[SensorErrorState] = None):
        if data is None and error is None:
            raise ValueError("Only 'data' or 'error' can be None.")

        if data is not None and error is not None:
            raise ValueError("Only 'data' or 'error' can be set.")

        self._data = data
        self._error = error

    @property
    def data(self) -> Union[None, int, float]:
        return self._data

    @property
    def error(self) -> Optional[SensorErrorState]:
        return self._error


class _DataCollector(threading.Thread):
    def __init__(self, global_data: GlobalData):
        threading.Thread.__init__(self)
        self._log_tag = os.path.basename(__file__)
        self.globalData = global_data

    def addLocation(self, country: str, city: str, lon: str, lat: str):
        raise NotImplementedError("Abstract class.")

    def getForecastTemperatureLow(self, country: str, city: str, lon: str, lat: str, day: int) -> WeatherData:
        raise NotImplementedError("Abstract class.")

    def getForecastTemperatureHigh(self, country: str, city: str, lon: str, lat: str, day: int) -> WeatherData:
        raise NotImplementedError("Abstract class.")

    def getForecastRain(self, country: str, city: str, lon: str, lat: str, day: int) -> WeatherData:
        raise NotImplementedError("Abstract class.")

    def getTemperature(self, country: str, city: str, lon: str, lat: str) -> WeatherData:
        raise NotImplementedError("Abstract class.")

    def getHumidity(self, country: str, city: str, lon: str, lat: str) -> WeatherData:
        raise NotImplementedError("Abstract class.")

    def run(self):
        raise NotImplementedError("Abstract class.")
