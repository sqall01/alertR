#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from ..globalData import GlobalData
import threading
import os


class DataCollector(threading.Thread):
    def __init__(self, globalData: GlobalData):
        threading.Thread.__init__(self)
        self.fileName = os.path.basename(__file__)
        self.globalData = globalData

    def addLocation(self, country: str, city: str, lon: str, lat: str):
        raise NotImplementedError("Not yet implemented.")

    def getForecastTemperatureLow(self, country: str, city: str, lon: str, lat: str, day: int) -> float:
        raise NotImplementedError("Not yet implemented.")

    def getForecastTemperatureHigh(self, country: str, city: str, lon: str, lat: str, day: int) -> float:
        raise NotImplementedError("Not yet implemented.")

    def getForecastRain(self, country: str, city: str, lon: str, lat: str, day: int) -> int:
        raise NotImplementedError("Not yet implemented.")

    def getTemperature(self, country: str, city: str, lon: str, lat: str) -> float:
        raise NotImplementedError("Not yet implemented.")

    def getHumidity(self, country: str, city: str, lon: str, lat: str) -> int:
        raise NotImplementedError("Not yet implemented.")

    def run(self):
        raise NotImplementedError("Not yet implemented.")
