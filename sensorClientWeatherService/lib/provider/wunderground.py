from core import DataCollector
import threading
import logging
import requests
import json
import time


# Class that collects data from Wunderground.
class WundergroundDataCollector(DataCollector):

    def __init__(self, globalData):
        super(WundergroundDataCollector, self).__init__(globalData)

        self.updateLock = threading.Semaphore(1)

        self.host = "http://api.wunderground.com"

        # Api key of wunderground.
        self.apiKey = None

        # Interval in seconds in which the data is fetched.
        self.interval = None

        # List of tuples in the form [(country, city), ...]
        self.locations = list()

        # Dictionary that holds the data that is collected in the form:
        # collectedData[<country>][<city>]["temp"/"humidity"]
        self.collectedData = dict()

        # Number of failed updates we tolerate before we change
        # the data to signal the problem.
        self.maxToleratedFails = None

    def addLocation(self, country, city, lon, lat):
        tempCountry = country.lower()
        tempCity = city.lower()

        # Check if location is already registered.
        for location in self.locations:
            if (location[0] == tempCountry
                and location[1] == tempCity):
                return

        # check if location is already in locations list
        self.locations.append( (tempCountry, tempCity) )

        # Add locations to data collection.
        if not tempCountry in self.collectedData.keys():
            self.collectedData[tempCountry] = dict()
        if not tempCity in self.collectedData[tempCountry].keys():
            self.collectedData[tempCountry][tempCity] = dict()
            self.collectedData[tempCountry][tempCity]["temp"] = float(-1000)
            self.collectedData[tempCountry][tempCity]["humidity"] = -1000
            self.collectedData[tempCountry][tempCity]["forecast"] = list()
            for i in range(3):
                self.collectedData[tempCountry][tempCity][
                    "forecast"].append(dict())
                self.collectedData[tempCountry][tempCity][
                    "forecast"][i]["tempHigh"] = float(-1000)
                self.collectedData[tempCountry][tempCity][
                    "forecast"][i]["tempLow"] = float(-1000)
                self.collectedData[tempCountry][tempCity][
                    "forecast"][i]["rain"] = -1000

    def getForecastTemperatureLow(self, country, city, lon, lat, day):
        tempCountry = country.lower()
        tempCity = city.lower()

        # Sanity check day.
        if day < 0 and day > 2:
            return float(-1001)

        self.updateLock.acquire()
        temp = self.collectedData[tempCountry][tempCity][
            "forecast"][day]["tempLow"]
        self.updateLock.release()
        return temp

    def getForecastTemperatureHigh(self, country, city, lon, lat, day):
        tempCountry = country.lower()
        tempCity = city.lower()

        # Sanity check day.
        if day < 0 and day > 2:
            return float(-1001)

        self.updateLock.acquire()
        temp = self.collectedData[tempCountry][tempCity][
            "forecast"][day]["tempHigh"]
        self.updateLock.release()
        return temp

    def getForecastRain(self, country, city, lon, lat, day):
        tempCountry = country.lower()
        tempCity = city.lower()

        # Sanity check day.
        if day < 0 and day > 2:
            return float(-1001)

        self.updateLock.acquire()
        temp = self.collectedData[tempCountry][tempCity][
            "forecast"][day]["rain"]
        self.updateLock.release()
        return temp

    def getTemperature(self, country, city, lon, lat):
        tempCountry = country.lower()
        tempCity = city.lower()

        self.updateLock.acquire()
        temp = self.collectedData[tempCountry][tempCity]["temp"]
        self.updateLock.release()
        return temp

    def getHumidity(self, country, city, lon, lat):
        tempCountry = country.lower()
        tempCity = city.lower()

        self.updateLock.acquire()
        humidity = self.collectedData[tempCountry][tempCity]["humidity"]
        self.updateLock.release()
        return humidity

    def run(self):

        logging.info("[%s]: Starting Wunderground data collector thread."
            % self.fileName)

        # Tolerate failed updates for at least 12 hours.
        self.maxToleratedFails = int(43200 / self.interval) + 1

        failCtr = 0
        while True:

            for locationTuple in self.locations:

                country = locationTuple[0]
                city = locationTuple[1]

                logging.debug("[%s]: Getting weather data from "
                    % self.fileName
                    + "Wunderground for %s in %s."
                    % (city, country))

                r = None
                try:
                    # Get weather data from Wunderground
                    url = self.host + "/api/" + self.apiKey + "/geolookup/conditions/forecast/q/" \
                          + country + "/" + city + "json"
                    r = requests.get(url)

                    # Extract data.
                    if r.status_code == 200:
                        jsonData =  r.json()

                        humidity = int(jsonData["current_observation"][
                            "relative_humidity"].replace("%", ""))
                        temp = float(jsonData["current_observation"]["temp_c"])
                        forecastDay0TempHigh = float(
                            jsonData["forecast"]["simpleforecast"][
                            "forecastday"][0]["high"]["celsius"])
                        forecastDay0TempLow = float(
                            jsonData["forecast"]["simpleforecast"][
                            "forecastday"][0]["low"]["celsius"])
                        forecastDay0Rain = int(jsonData["forecast"][
                            "simpleforecast"]["forecastday"][0]["pop"])
                        forecastDay1TempHigh = float(
                            jsonData["forecast"]["simpleforecast"][
                            "forecastday"][1]["high"]["celsius"])
                        forecastDay1TempLow = float(
                            jsonData["forecast"]["simpleforecast"][
                            "forecastday"][1]["low"]["celsius"])
                        forecastDay1Rain = int(
                            jsonData["forecast"]["simpleforecast"][
                            "forecastday"][1]["pop"])
                        forecastDay2TempHigh = float(
                            jsonData["forecast"]["simpleforecast"][
                            "forecastday"][2]["high"]["celsius"])
                        forecastDay2TempLow = float(
                            jsonData["forecast"]["simpleforecast"][
                            "forecastday"][2]["low"]["celsius"])
                        forecastDay2Rain = int(
                            jsonData["forecast"]["simpleforecast"][
                            "forecastday"][2]["pop"])

                        self.updateLock.acquire()
                        self.collectedData[country][city]["humidity"] \
                            = humidity
                        self.collectedData[country][city]["temp"] \
                            = temp
                        self.collectedData[country][city][
                            "forecast"][0]["tempHigh"] = forecastDay0TempHigh
                        self.collectedData[country][city][
                            "forecast"][0]["tempLow"] = forecastDay0TempLow
                        self.collectedData[country][city][
                            "forecast"][0]["rain"] = forecastDay0Rain
                        self.collectedData[country][city][
                            "forecast"][1]["tempHigh"] = forecastDay1TempHigh
                        self.collectedData[country][city][
                            "forecast"][1]["tempLow"] = forecastDay1TempLow
                        self.collectedData[country][city][
                            "forecast"][1]["rain"] = forecastDay1Rain
                        self.collectedData[country][city][
                            "forecast"][2]["tempHigh"] = forecastDay2TempHigh
                        self.collectedData[country][city][
                            "forecast"][2]["tempLow"] = forecastDay2TempLow
                        self.collectedData[country][city][
                            "forecast"][2]["rain"] = forecastDay2Rain
                        self.updateLock.release()

                        # Reset fail count.
                        failCtr = 0

                        logging.info("[%s]: Received new humidity data "
                            % self.fileName
                            + "from Wunderground: %d%% for %s in %s."
                            % (humidity, city, country))

                        logging.info("[%s]: Received new temperature data "
                            % self.fileName
                            + "from Wunderground: %.1f degrees Celsius "
                            % temp
                            + "for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                            % self.fileName
                            + "from Wunderground for day 0: min %.1f max %.1f "
                            % (forecastDay0TempLow, forecastDay0TempHigh)
                            + "degrees Celsius for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                            % self.fileName
                            + "from Wunderground for day 0: %d%% "
                            % forecastDay0Rain
                            + "chance of rain for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                            % self.fileName
                            + "from Wunderground for day 1: min %.1f max %.1f "
                            % (forecastDay1TempLow, forecastDay1TempHigh)
                            + "degrees Celsius for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                            % self.fileName
                            + "from Wunderground for day 1: %d%% "
                            % forecastDay1Rain
                            + "chance of rain for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                            % self.fileName
                            + "from Wunderground for day 2: min %.1f max %.1f "
                            % (forecastDay2TempLow, forecastDay2TempHigh)
                            + "degrees Celsius for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                            % self.fileName
                            + "from Wunderground for day 2: %d%% "
                            % forecastDay2Rain
                            + "chance of rain for %s in %s."
                            % (city, country))

                    else:
                        failCtr += 1
                        logging.error("[%s]: Received response code %d "
                            % (self.fileName, r.status_code)
                            + "from Wunderground.")

                        if failCtr >= self.maxToleratedFails:
                            self.updateLock.acquire()
                            self.collectedData[country][city]["humidity"] \
                                = -998
                            self.collectedData[country][city]["temp"] \
                                = -998
                            self.collectedData[country][city][
                                "forecast"][0]["tempHigh"] = float(-998)
                            self.collectedData[country][city][
                                "forecast"][0]["tempLow"] = float(-998)
                            self.collectedData[country][city][
                                "forecast"][0]["rain"] = -998
                            self.collectedData[country][city][
                                "forecast"][1]["tempHigh"] = float(-998)
                            self.collectedData[country][city][
                                "forecast"][1]["tempLow"] = float(-998)
                            self.collectedData[country][city][
                                "forecast"][1]["rain"] = -998
                            self.collectedData[country][city][
                                "forecast"][2]["tempHigh"] = float(-998)
                            self.collectedData[country][city][
                                "forecast"][2]["tempLow"] = float(-998)
                            self.collectedData[country][city][
                                "forecast"][2]["rain"] = -998
                            self.updateLock.release()

                except Exception as e:
                    failCtr += 1
                    logging.exception("[%s]: Could not get weather data "
                        % self.fileName
                        + "for %s in %s."
                        % (city, country))
                    if r is not None:
                        logging.error("[%s]: Received data from server: '%s'."
							% (self.fileName, r.text))

                    if failCtr >= self.maxToleratedFails:
                        self.updateLock.acquire()
                        self.collectedData[country][city]["humidity"] \
                            = -999
                        self.collectedData[country][city]["temp"] \
                            = float(-999)
                        self.collectedData[country][city][
                            "forecast"][0]["tempHigh"] = float(-999)
                        self.collectedData[country][city][
                            "forecast"][0]["tempLow"] = float(-999)
                        self.collectedData[country][city][
                            "forecast"][0]["rain"] = -999
                        self.collectedData[country][city][
                            "forecast"][1]["tempHigh"] = float(-999)
                        self.collectedData[country][city][
                            "forecast"][1]["tempLow"] = float(-999)
                        self.collectedData[country][city][
                            "forecast"][1]["rain"] = -999
                        self.collectedData[country][city][
                            "forecast"][2]["tempHigh"] = float(-999)
                        self.collectedData[country][city][
                            "forecast"][2]["tempLow"] = float(-999)
                        self.collectedData[country][city][
                            "forecast"][2]["rain"] = -999
                        self.updateLock.release()

            # Sleep until next update cycle.
            time.sleep(self.interval)
