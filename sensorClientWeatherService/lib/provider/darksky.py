from core import DataCollector
import threading
import logging
import requests
import time


class DarkskyDataCollector(DataCollector):

    def __init__(self, globalData):
        super(DarkskyDataCollector, self).__init__(globalData)

        self.updateLock = threading.Semaphore(1)

        self.host = "https://api.darksky.net"

        # Api key of wunderground.
        self.apiKey = None

        # Interval in seconds in which the data is fetched.
        self.interval = None

        # Dict with tuples in the form (lon, lat) as key.
        self.locations = dict()

        # Dictionary that holds the data that is collected in the form:
        # collectedData[<lon>][<lat>]["temp"/"humidity"]
        self.collectedData = dict()

        # Number of failed updates we tolerate before we change
        # the data to signal the problem.
        self.maxToleratedFails = None

    def addLocation(self, country, city, lon, lat):

        # Check if location is already registered.
        for location in self.locations.keys():
            if location[0] == lon and location[1] == lat:
                return

        # check if location is already in locations list
        self.locations[(lon, lat)] = dict()
        self.locations[(lon, lat)]["country"] = country.lower()
        self.locations[(lon, lat)]["city"] = city.lower()

        # Add locations to data collection.
        if not lon in self.collectedData.keys():
            self.collectedData[lon] = dict()
        if not lat in self.collectedData[lon].keys():
            self.collectedData[lon][lat] = dict()
            self.collectedData[lon][lat]["temp"] = float(-1000)
            self.collectedData[lon][lat]["humidity"] = -1000
            self.collectedData[lon][lat]["forecast"] = list()
            for i in range(3):
                self.collectedData[lon][lat]["forecast"].append(dict())
                self.collectedData[lon][lat]["forecast"][i]["tempHigh"] = float(-1000)
                self.collectedData[lon][lat]["forecast"][i]["tempLow"] = float(-1000)
                self.collectedData[lon][lat]["forecast"][i]["rain"] = -1000

    def getForecastTemperatureLow(self, country, city, lon, lat, day):

        # Sanity check day.
        if day < 0 and day > 2:
            return float(-1001)

        with self.updateLock:
            return self.collectedData[lon][lat]["forecast"][day]["tempLow"]

    def getForecastTemperatureHigh(self, country, city, lon, lat, day):

        # Sanity check day.
        if day < 0 and day > 2:
            return float(-1001)

        with self.updateLock:
            return self.collectedData[lon][lat]["forecast"][day]["tempHigh"]

    def getForecastRain(self, country, city, lon, lat, day):

        # Sanity check day.
        if day < 0 and day > 2:
            return float(-1001)

        with self.updateLock:
            return self.collectedData[lon][lat]["forecast"][day]["rain"]

    def getTemperature(self, country, city, lon, lat):
        with self.updateLock:
            return self.collectedData[lon][lat]["temp"]

    def getHumidity(self, country, city, lon, lat):
        with self.updateLock:
            return self.collectedData[lon][lat]["humidity"]

    def run(self):

        logging.info("[%s]: Starting DarkSky data collector thread."
            % self.fileName)

        # Tolerate failed updates for at least 12 hours.
        self.maxToleratedFails = int(43200 / self.interval) + 1

        failCtr = 0
        while True:

            for locationTuple in self.locations.keys():

                lon = locationTuple[0]
                lat = locationTuple[1]
                country = self.locations[locationTuple]["country"]
                city = self.locations[locationTuple]["city"]

                logging.debug("[%s]: Getting weather data from "
                    % self.fileName
                    + "Darksky for %s in %s."
                    % (city, country))

                r = None
                try:
                    url = self.host + "/forecast/" + self.apiKey + "/" + lat + "," + lon + "?units=si"
                    r = requests.get(url, verify=True)

                    # Extract data.
                    if r.status_code == 200:
                        jsonData =  r.json()

                        humidity = int(float(jsonData["currently"]["humidity"]) * 100)
                        temp = float(jsonData["currently"]["temperature"])
                        forecastDay0TempHigh = float(jsonData["daily"]["data"][0]["temperatureMax"])
                        forecastDay0TempLow = float(jsonData["daily"]["data"][0]["temperatureMin"])
                        forecastDay0Rain = int(float(jsonData["daily"]["data"][0]["precipProbability"]) * 100)
                        forecastDay1TempHigh = float(jsonData["daily"]["data"][1]["temperatureMax"])
                        forecastDay1TempLow = float(jsonData["daily"]["data"][1]["temperatureMin"])
                        forecastDay1Rain = int(float(jsonData["daily"]["data"][1]["precipProbability"]) * 100)
                        forecastDay2TempHigh = float(jsonData["daily"]["data"][2]["temperatureMax"])
                        forecastDay2TempLow = float(jsonData["daily"]["data"][2]["temperatureMin"])
                        forecastDay2Rain = int(float(jsonData["daily"]["data"][2]["precipProbability"]) * 100)

                        with self.updateLock:
                            self.collectedData[lon][lat]["humidity"]  = humidity
                            self.collectedData[lon][lat]["temp"]  = temp
                            self.collectedData[lon][lat]["forecast"][0]["tempHigh"] = forecastDay0TempHigh
                            self.collectedData[lon][lat]["forecast"][0]["tempLow"] = forecastDay0TempLow
                            self.collectedData[lon][lat]["forecast"][0]["rain"] = forecastDay0Rain
                            self.collectedData[lon][lat]["forecast"][1]["tempHigh"] = forecastDay1TempHigh
                            self.collectedData[lon][lat]["forecast"][1]["tempLow"] = forecastDay1TempLow
                            self.collectedData[lon][lat]["forecast"][1]["rain"] = forecastDay1Rain
                            self.collectedData[lon][lat]["forecast"][2]["tempHigh"] = forecastDay2TempHigh
                            self.collectedData[lon][lat]["forecast"][2]["tempLow"] = forecastDay2TempLow
                            self.collectedData[lon][lat]["forecast"][2]["rain"] = forecastDay2Rain

                        # Reset fail count.
                        failCtr = 0

                        logging.info("[%s]: Received new humidity data "
                            % self.fileName
                            + "from DarkSky: %d%% for %s in %s."
                            % (humidity, city, country))

                        logging.info("[%s]: Received new temperature data "
                            % self.fileName
                            + "from DarkSky: %.1f degrees Celsius "
                            % temp
                            + "for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                            % self.fileName
                            + "from DarkSky for day 0: min %.1f max %.1f "
                            % (forecastDay0TempLow, forecastDay0TempHigh)
                            + "degrees Celsius for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                            % self.fileName
                            + "from DarkSky for day 0: %d%% "
                            % forecastDay0Rain
                            + "chance of rain for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                            % self.fileName
                            + "from DarkSky for day 1: min %.1f max %.1f "
                            % (forecastDay1TempLow, forecastDay1TempHigh)
                            + "degrees Celsius for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                            % self.fileName
                            + "from DarkSky for day 1: %d%% "
                            % forecastDay1Rain
                            + "chance of rain for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                            % self.fileName
                            + "from DarkSky for day 2: min %.1f max %.1f "
                            % (forecastDay2TempLow, forecastDay2TempHigh)
                            + "degrees Celsius for %s in %s."
                            % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                            % self.fileName
                            + "from DarkSky for day 2: %d%% "
                            % forecastDay2Rain
                            + "chance of rain for %s in %s."
                            % (city, country))

                    else:
                        failCtr += 1
                        logging.error("[%s]: Received response code %d "
                            % (self.fileName, r.status_code)
                            + "from DarkSky.")

                        if failCtr >= self.maxToleratedFails:
                            with self.updateLock:
                                self.collectedData[lon][lat]["humidity"]  = -998
                                self.collectedData[lon][lat]["temp"]  = -998
                                self.collectedData[lon][lat]["forecast"][0]["tempHigh"] = float(-998)
                                self.collectedData[lon][lat]["forecast"][0]["tempLow"] = float(-998)
                                self.collectedData[lon][lat]["forecast"][0]["rain"] = -998
                                self.collectedData[lon][lat]["forecast"][1]["tempHigh"] = float(-998)
                                self.collectedData[lon][lat]["forecast"][1]["tempLow"] = float(-998)
                                self.collectedData[lon][lat]["forecast"][1]["rain"] = -998
                                self.collectedData[lon][lat]["forecast"][2]["tempHigh"] = float(-998)
                                self.collectedData[lon][lat]["forecast"][2]["tempLow"] = float(-998)
                                self.collectedData[lon][lat]["forecast"][2]["rain"] = -998

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
                        with self.updateLock:
                            self.collectedData[lon][lat]["humidity"] = -999
                            self.collectedData[lon][lat]["temp"] = float(-999)
                            self.collectedData[lon][lat]["forecast"][0]["tempHigh"] = float(-999)
                            self.collectedData[lon][lat]["forecast"][0]["tempLow"] = float(-999)
                            self.collectedData[lon][lat]["forecast"][0]["rain"] = -999
                            self.collectedData[lon][lat]["forecast"][1]["tempHigh"] = float(-999)
                            self.collectedData[lon][lat]["forecast"][1]["tempLow"] = float(-999)
                            self.collectedData[lon][lat]["forecast"][1]["rain"] = -999
                            self.collectedData[lon][lat]["forecast"][2]["tempHigh"] = float(-999)
                            self.collectedData[lon][lat]["forecast"][2]["tempLow"] = float(-999)
                            self.collectedData[lon][lat]["forecast"][2]["rain"] = -999

            # Sleep until next update cycle.
            time.sleep(self.interval)
