import threading
import os


class DataCollector(threading.Thread):
    def __init__(self, globalData):
        threading.Thread.__init__(self)
        self.fileName = os.path.basename(__file__)
        self.globalData = globalData

    def addLocation(self, country, city, lon, lat):
        raise NotImplementedError("Not yet implemented.")

    def getForecastTemperatureLow(self, country, city, lon, lat, day):
        raise NotImplementedError("Not yet implemented.")

    def getForecastTemperatureHigh(self, country, city, lon, lat, day):
        raise NotImplementedError("Not yet implemented.")

    def getForecastRain(self, country, city, lon, lat, day):
        raise NotImplementedError("Not yet implemented.")

    def getTemperature(self, country, city, lon, lat):
        raise NotImplementedError("Not yet implemented.")

    def getHumidity(self, country, city, lon, lat):
        raise NotImplementedError("Not yet implemented.")

    def run(self):
        raise NotImplementedError("Not yet implemented.")
