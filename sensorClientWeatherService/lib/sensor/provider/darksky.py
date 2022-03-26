#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import logging
import requests
import time
from typing import Optional

from .core import _DataCollector, WeatherData
from ...globalData import GlobalData
from ...globalData.sensorObjects import SensorErrorState


class DarkskyDataCollector(_DataCollector):

    def __init__(self, global_data: GlobalData):
        super(DarkskyDataCollector, self).__init__(global_data)

        self.updateLock = threading.Semaphore(1)

        self.host = "https://api.darksky.net"

        # Api key of darksky.
        self.apiKey = None  # type: Optional[str]

        # Interval in seconds in which the data is fetched.
        self.interval = None  # type: Optional[int]

        # Dict with tuples in the form (lon, lat) as key.
        self.locations = dict()

        # Dictionary that holds the data that is collected in the form:
        # collectedData[<lon>][<lat>]["temp"/"humidity"]
        self.collectedData = dict()

    def addLocation(self, country: str, city: str, lon: str, lat: str):

        # Check if location is already registered.
        for location in self.locations.keys():
            if location[0] == lon and location[1] == lat:
                return

        # check if location is already in locations list
        self.locations[(lon, lat)] = dict()
        self.locations[(lon, lat)]["country"] = country.lower()
        self.locations[(lon, lat)]["city"] = city.lower()

        error_data = WeatherData(None,
                                 SensorErrorState(SensorErrorState.ValueError,
                                                  "No data available yet."))
        # Add locations to data collection.
        if lon not in self.collectedData.keys():
            self.collectedData[lon] = dict()
        if lat not in self.collectedData[lon].keys():
            self.collectedData[lon][lat] = dict()
            self.collectedData[lon][lat]["temp"] = error_data
            self.collectedData[lon][lat]["humidity"] = error_data
            self.collectedData[lon][lat]["forecast"] = list()
            for i in range(3):
                self.collectedData[lon][lat]["forecast"].append(dict())
                self.collectedData[lon][lat]["forecast"][i]["tempHigh"] = error_data
                self.collectedData[lon][lat]["forecast"][i]["tempLow"] = error_data
                self.collectedData[lon][lat]["forecast"][i]["rain"] = error_data

    def getForecastTemperatureLow(self, country: str, city: str, lon: str, lat: str, day: int) -> WeatherData:

        # Sanity check day.
        if 0 > day > 2:
            return WeatherData(None, SensorErrorState(SensorErrorState.ValueError, "Day can only be set to 0, 1 or 2."))

        with self.updateLock:
            return self.collectedData[lon][lat]["forecast"][day]["tempLow"]

    def getForecastTemperatureHigh(self, country: str, city: str, lon: str, lat: str, day: int) -> WeatherData:

        # Sanity check day.
        if 0 > day > 2:
            return WeatherData(None, SensorErrorState(SensorErrorState.ValueError, "Day can only be set to 0, 1 or 2."))

        with self.updateLock:
            return self.collectedData[lon][lat]["forecast"][day]["tempHigh"]

    def getForecastRain(self, country: str, city: str, lon: str, lat: str, day: int) -> WeatherData:

        # Sanity check day.
        if 0 > day > 2:
            return WeatherData(None, SensorErrorState(SensorErrorState.ValueError, "Day can only be set to 0, 1 or 2."))

        with self.updateLock:
            return self.collectedData[lon][lat]["forecast"][day]["rain"]

    def getTemperature(self, country: str, city: str, lon: str, lat: str) -> WeatherData:
        with self.updateLock:
            return self.collectedData[lon][lat]["temp"]

    def getHumidity(self, country: str, city: str, lon: str, lat: str) -> WeatherData:
        with self.updateLock:
            return self.collectedData[lon][lat]["humidity"]

    def run(self):

        logging.info("[%s]: Starting DarkSky data collector thread." % self._log_tag)

        # Tolerate failed updates for at least 12 hours.
        max_tolerated_fails = int(43200 / self.interval) + 1

        fail_ctr = 0
        while True:

            for locationTuple in self.locations.keys():

                lon = locationTuple[0]
                lat = locationTuple[1]
                country = self.locations[locationTuple]["country"]
                city = self.locations[locationTuple]["city"]

                logging.debug("[%s]: Getting weather data from Darksky for %s in %s."
                              % (self._log_tag, city, country))

                r = None
                try:
                    url = self.host + "/forecast/" + self.apiKey + "/" + lat + "," + lon + "?units=si"
                    r = requests.get(url, verify=True, timeout=20.0)

                    # Extract data.
                    if r.status_code == 200:
                        json_data = r.json()

                        humidity = WeatherData(int(float(json_data["currently"]["humidity"]) * 100))
                        temp = WeatherData(float(json_data["currently"]["temperature"]))
                        forecast_day0_temp_high = WeatherData(float(json_data["daily"]["data"][0]["temperatureMax"]))
                        forecast_day0_temp_low = WeatherData(float(json_data["daily"]["data"][0]["temperatureMin"]))
                        forecast_day0_rain = WeatherData(int(float(
                            json_data["daily"]["data"][0]["precipProbability"]) * 100))
                        forecast_day1_temp_high = WeatherData(float(json_data["daily"]["data"][1]["temperatureMax"]))
                        forecast_day1_temp_low = WeatherData(float(json_data["daily"]["data"][1]["temperatureMin"]))
                        forecast_day1_rain = WeatherData(int(float(
                            json_data["daily"]["data"][1]["precipProbability"]) * 100))
                        forecast_day2_temp_high = WeatherData(float(json_data["daily"]["data"][2]["temperatureMax"]))
                        forecast_day2_temp_low = WeatherData(float(json_data["daily"]["data"][2]["temperatureMin"]))
                        forecast_day2_rain = WeatherData(int(float(
                            json_data["daily"]["data"][2]["precipProbability"]) * 100))

                        with self.updateLock:
                            self.collectedData[lon][lat]["humidity"] = humidity
                            self.collectedData[lon][lat]["temp"] = temp
                            self.collectedData[lon][lat]["forecast"][0]["tempHigh"] = forecast_day0_temp_high
                            self.collectedData[lon][lat]["forecast"][0]["tempLow"] = forecast_day0_temp_low
                            self.collectedData[lon][lat]["forecast"][0]["rain"] = forecast_day0_rain
                            self.collectedData[lon][lat]["forecast"][1]["tempHigh"] = forecast_day1_temp_high
                            self.collectedData[lon][lat]["forecast"][1]["tempLow"] = forecast_day1_temp_low
                            self.collectedData[lon][lat]["forecast"][1]["rain"] = forecast_day1_rain
                            self.collectedData[lon][lat]["forecast"][2]["tempHigh"] = forecast_day2_temp_high
                            self.collectedData[lon][lat]["forecast"][2]["tempLow"] = forecast_day2_temp_low
                            self.collectedData[lon][lat]["forecast"][2]["rain"] = forecast_day2_rain

                        # Reset fail count.
                        fail_ctr = 0

                        logging.info("[%s]: Received new humidity data "
                                     % self._log_tag
                                     + "from DarkSky: %d%% for %s in %s."
                                     % (humidity.data, city, country))

                        logging.info("[%s]: Received new temperature data "
                                     % self._log_tag
                                     + "from DarkSky: %.1f degrees Celsius "
                                     % temp.data
                                     + "for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                                     % self._log_tag
                                     + "from DarkSky for day 0: min %.1f max %.1f "
                                     % (forecast_day0_temp_low.data, forecast_day0_temp_high.data)
                                     + "degrees Celsius for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                                     % self._log_tag
                                     + "from DarkSky for day 0: %d%% "
                                     % forecast_day0_rain.data
                                     + "chance of rain for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                                     % self._log_tag
                                     + "from DarkSky for day 1: min %.1f max %.1f "
                                     % (forecast_day1_temp_low.data, forecast_day1_temp_high.data)
                                     + "degrees Celsius for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                                     % self._log_tag
                                     + "from DarkSky for day 1: %d%% "
                                     % forecast_day1_rain.data
                                     + "chance of rain for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                                     % self._log_tag
                                     + "from DarkSky for day 2: min %.1f max %.1f "
                                     % (forecast_day2_temp_low.data, forecast_day2_temp_high.data)
                                     + "degrees Celsius for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                                     % self._log_tag
                                     + "from DarkSky for day 2: %d%% "
                                     % forecast_day2_rain.data
                                     + "chance of rain for %s in %s."
                                     % (city, country))

                    else:
                        fail_ctr += 1
                        logging.error("[%s]: Received response code %d from DarkSky."
                                      % (self._log_tag, r.status_code))

                        if fail_ctr >= max_tolerated_fails:
                            with self.updateLock:
                                error_data = WeatherData(None,
                                                         SensorErrorState(SensorErrorState.ConnectionError,
                                                                          "Not able to collect data."))
                                self.collectedData[lon][lat]["humidity"] = error_data
                                self.collectedData[lon][lat]["temp"] = error_data
                                self.collectedData[lon][lat]["forecast"][0]["tempHigh"] = error_data
                                self.collectedData[lon][lat]["forecast"][0]["tempLow"] = error_data
                                self.collectedData[lon][lat]["forecast"][0]["rain"] = error_data
                                self.collectedData[lon][lat]["forecast"][1]["tempHigh"] = error_data
                                self.collectedData[lon][lat]["forecast"][1]["tempLow"] = error_data
                                self.collectedData[lon][lat]["forecast"][1]["rain"] = error_data
                                self.collectedData[lon][lat]["forecast"][2]["tempHigh"] = error_data
                                self.collectedData[lon][lat]["forecast"][2]["tempLow"] = error_data
                                self.collectedData[lon][lat]["forecast"][2]["rain"] = error_data

                except Exception as e:
                    fail_ctr += 1
                    logging.exception("[%s]: Could not get weather data for %s in %s."
                                      % (self._log_tag, city, country))
                    if r is not None:
                        logging.error("[%s]: Received data from server: '%s'."
                                      % (self._log_tag, r.text))

                    if fail_ctr >= max_tolerated_fails:
                        with self.updateLock:
                            error_data = WeatherData(None,
                                                     SensorErrorState(SensorErrorState.ProcessingError,
                                                                      "Not able to parse data: %s" % str(e)))
                            self.collectedData[lon][lat]["humidity"] = error_data
                            self.collectedData[lon][lat]["temp"] = error_data
                            self.collectedData[lon][lat]["forecast"][0]["tempHigh"] = error_data
                            self.collectedData[lon][lat]["forecast"][0]["tempLow"] = error_data
                            self.collectedData[lon][lat]["forecast"][0]["rain"] = error_data
                            self.collectedData[lon][lat]["forecast"][1]["tempHigh"] = error_data
                            self.collectedData[lon][lat]["forecast"][1]["tempLow"] = error_data
                            self.collectedData[lon][lat]["forecast"][1]["rain"] = error_data
                            self.collectedData[lon][lat]["forecast"][2]["tempHigh"] = error_data
                            self.collectedData[lon][lat]["forecast"][2]["tempLow"] = error_data
                            self.collectedData[lon][lat]["forecast"][2]["rain"] = error_data

            # Sleep until next update cycle.
            time.sleep(self.interval)
