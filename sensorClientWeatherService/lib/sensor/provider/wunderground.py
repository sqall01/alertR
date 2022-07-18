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
import json
import os
from typing import Optional

from .core import _DataCollector, WeatherData
from ...globalData.sensorObjects import SensorErrorState


class WundergroundDataCollector(_DataCollector):

    def __init__(self, interval: int, api_key: str):
        super(WundergroundDataCollector, self).__init__()

        self._log_tag = os.path.basename(__file__)

        self.updateLock = threading.Lock()

        self.host = "http://api.wunderground.com"

        # Api key of wunderground.
        self.apiKey = api_key

        # Interval in seconds in which the data is fetched.
        self.interval = interval

        # List of tuples in the form [(country, city), ...]
        self.locations = list()

        # Dictionary that holds the data that is collected in the form:
        # collectedData[<country>][<city>]["temp"/"humidity"]
        self.collectedData = dict()

        self._exit_event = threading.Event()
        self._exit_event.clear()

        self._fail_ctr = 0

    def _get_data(self,
                  country: Optional[str] = None,
                  city: Optional[str] = None,
                  lon: Optional[str] = None,
                  lat: Optional[str] = None) -> Optional[str]:
        try:
            url = self.host \
                  + "/api/" \
                  + self.apiKey \
                  + "/geolookup/conditions/forecast/q/" \
                  + country \
                  + "/" \
                  + city \
                  + "json"
            r = requests.get(url, verify=True, timeout=20.0)

            # Extract data.
            if r.status_code == 200:
                return r.text
            else:
                logging.error("[%s]: Received response code %d from Wunderground."
                              % (self._log_tag, r.status_code))

        except Exception as e:
            logging.exception("[%s]: Could not get weather data for %s in %s."
                              % (self._log_tag, city, country))

        return None

    def addLocation(self, country: str, city: str, lon: str, lat: str):
        temp_country = country.lower()
        temp_city = city.lower()

        # Check if location is already registered.
        for location in self.locations:
            if location[0] == temp_country and location[1] == temp_city:
                return

        # check if location is already in locations list
        self.locations.append((temp_country, temp_city))

        error_data = WeatherData(None,
                                 SensorErrorState(SensorErrorState.ValueError,
                                                  "No data available yet."))
        # Add locations to data collection.
        if temp_country not in self.collectedData.keys():
            self.collectedData[temp_country] = dict()
        if temp_city not in self.collectedData[temp_country].keys():
            self.collectedData[temp_country][temp_city] = dict()
            self.collectedData[temp_country][temp_city]["temp"] = error_data
            self.collectedData[temp_country][temp_city]["humidity"] = error_data
            self.collectedData[temp_country][temp_city]["forecast"] = list()
            for i in range(3):
                self.collectedData[temp_country][temp_city]["forecast"].append(dict())
                self.collectedData[temp_country][temp_city]["forecast"][i]["tempHigh"] = error_data
                self.collectedData[temp_country][temp_city]["forecast"][i]["tempLow"] = error_data
                self.collectedData[temp_country][temp_city]["forecast"][i]["rain"] = error_data

    def getForecastTemperatureLow(self, country: str, city: str, lon: str, lat: str, day: int) -> WeatherData:
        temp_country = country.lower()
        temp_city = city.lower()

        # Sanity check day.
        if 0 > day > 2:
            return WeatherData(None, SensorErrorState(SensorErrorState.ValueError, "Day can only be set to 0, 1 or 2."))

        with self.updateLock:
            return self.collectedData[temp_country][temp_city]["forecast"][day]["tempLow"]

    def getForecastTemperatureHigh(self, country: str, city: str, lon: str, lat: str, day: int) -> WeatherData:
        temp_country = country.lower()
        temp_city = city.lower()

        # Sanity check day.
        if 0 > day > 2:
            return WeatherData(None, SensorErrorState(SensorErrorState.ValueError, "Day can only be set to 0, 1 or 2."))

        with self.updateLock:
            return self.collectedData[temp_country][temp_city]["forecast"][day]["tempHigh"]

    def getForecastRain(self, country: str, city: str, lon: str, lat: str, day: int) -> WeatherData:
        temp_country = country.lower()
        temp_city = city.lower()

        # Sanity check day.
        if 0 > day > 2:
            return WeatherData(None, SensorErrorState(SensorErrorState.ValueError, "Day can only be set to 0, 1 or 2."))

        with self.updateLock:
            return self.collectedData[temp_country][temp_city]["forecast"][day]["rain"]

    def getTemperature(self, country: str, city: str, lon: str, lat: str) -> WeatherData:
        temp_country = country.lower()
        temp_city = city.lower()

        with self.updateLock:
            return self.collectedData[temp_country][temp_city]["temp"]

    def getHumidity(self, country: str, city: str, lon: str, lat: str) -> WeatherData:
        temp_country = country.lower()
        temp_city = city.lower()

        with self.updateLock:
            return self.collectedData[temp_country][temp_city]["humidity"]

    def run(self):

        logging.info("[%s]: Starting Wunderground data collector thread." % self._log_tag)

        # Tolerate failed updates for at least 12 hours.
        max_tolerated_fails = int(43200 / self.interval) + 1

        self._fail_ctr = 0
        while True:

            for location_tuple in self.locations:

                country = location_tuple[0]
                city = location_tuple[1]

                logging.debug("[%s]: Getting weather data from Wunderground for %s in %s."
                              % (self._log_tag, city, country))

                data = self._get_data(country=country, city=city)

                try:
                    # Extract data.
                    if data:
                        json_data = json.loads(data)

                        humidity = WeatherData(int(json_data["current_observation"][
                                                       "relative_humidity"].replace("%", "")))
                        temp = WeatherData(float(json_data["current_observation"]["temp_c"]))
                        forecast_day0_temp_high = WeatherData(float(json_data["forecast"]["simpleforecast"][
                                                     "forecastday"][0]["high"]["celsius"]))
                        forecast_day0_temp_low = WeatherData(float(json_data["forecast"]["simpleforecast"][
                                                    "forecastday"][0]["low"]["celsius"]))
                        forecast_day0_rain = WeatherData(int(json_data["forecast"][
                                               "simpleforecast"]["forecastday"][0]["pop"]))
                        forecast_day1_temp_high = WeatherData(float(json_data["forecast"]["simpleforecast"][
                                                     "forecastday"][1]["high"]["celsius"]))
                        forecast_day1_temp_low = WeatherData(float(json_data["forecast"]["simpleforecast"][
                                                    "forecastday"][1]["low"]["celsius"]))
                        forecast_day1_rain = WeatherData(int(json_data["forecast"]["simpleforecast"][
                                               "forecastday"][1]["pop"]))
                        forecast_day2_temp_high = WeatherData(float(json_data["forecast"]["simpleforecast"][
                                                     "forecastday"][2]["high"]["celsius"]))
                        forecast_day2_temp_low = WeatherData(float(json_data["forecast"]["simpleforecast"][
                                                    "forecastday"][2]["low"]["celsius"]))
                        forecast_day2_rain = WeatherData(int(json_data["forecast"]["simpleforecast"][
                                               "forecastday"][2]["pop"]))

                        with self.updateLock:
                            self.collectedData[country][city]["humidity"] = humidity
                            self.collectedData[country][city]["temp"] = temp
                            self.collectedData[country][city]["forecast"][0]["tempHigh"] = forecast_day0_temp_high
                            self.collectedData[country][city]["forecast"][0]["tempLow"] = forecast_day0_temp_low
                            self.collectedData[country][city]["forecast"][0]["rain"] = forecast_day0_rain
                            self.collectedData[country][city]["forecast"][1]["tempHigh"] = forecast_day1_temp_high
                            self.collectedData[country][city]["forecast"][1]["tempLow"] = forecast_day1_temp_low
                            self.collectedData[country][city]["forecast"][1]["rain"] = forecast_day1_rain
                            self.collectedData[country][city]["forecast"][2]["tempHigh"] = forecast_day2_temp_high
                            self.collectedData[country][city]["forecast"][2]["tempLow"] = forecast_day2_temp_low
                            self.collectedData[country][city]["forecast"][2]["rain"] = forecast_day2_rain

                        # Reset fail count.
                        self._fail_ctr = 0

                        logging.info("[%s]: Received new humidity data "
                                     % self._log_tag
                                     + "%d%% for %s in %s."
                                     % (humidity.data, city, country))

                        logging.info("[%s]: Received new temperature data "
                                     % self._log_tag
                                     + "%.1f degrees Celsius "
                                     % temp.data
                                     + "for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                                     % self._log_tag
                                     + "for day 0: min %.1f max %.1f "
                                     % (forecast_day0_temp_low.data, forecast_day0_temp_high.data)
                                     + "degrees Celsius for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                                     % self._log_tag
                                     + "for day 0: %d%% "
                                     % forecast_day0_rain.data
                                     + "chance of rain for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                                     % self._log_tag
                                     + "for day 1: min %.1f max %.1f "
                                     % (forecast_day1_temp_low.data, forecast_day1_temp_high.data)
                                     + "degrees Celsius for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                                     % self._log_tag
                                     + "for day 1: %d%% "
                                     % forecast_day1_rain.data
                                     + "chance of rain for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new temperature forecast "
                                     % self._log_tag
                                     + "for day 2: min %.1f max %.1f "
                                     % (forecast_day2_temp_low.data, forecast_day2_temp_high.data)
                                     + "degrees Celsius for %s in %s."
                                     % (city, country))

                        logging.info("[%s]: Received new rain forecast "
                                     % self._log_tag
                                     + "for day 2: %d%% "
                                     % forecast_day2_rain.data
                                     + "chance of rain for %s in %s."
                                     % (city, country))

                    else:
                        self._fail_ctr += 1

                        if self._fail_ctr >= max_tolerated_fails:
                            with self.updateLock:
                                error_data = WeatherData(None,
                                                         SensorErrorState(SensorErrorState.ConnectionError,
                                                                          "Not able to collect data."))
                                self.collectedData[country][city]["humidity"] = error_data
                                self.collectedData[country][city]["temp"] = error_data
                                self.collectedData[country][city]["forecast"][0]["tempHigh"] = error_data
                                self.collectedData[country][city]["forecast"][0]["tempLow"] = error_data
                                self.collectedData[country][city]["forecast"][0]["rain"] = error_data
                                self.collectedData[country][city]["forecast"][1]["tempHigh"] = error_data
                                self.collectedData[country][city]["forecast"][1]["tempLow"] = error_data
                                self.collectedData[country][city]["forecast"][1]["rain"] = error_data
                                self.collectedData[country][city]["forecast"][2]["tempHigh"] = error_data
                                self.collectedData[country][city]["forecast"][2]["tempLow"] = error_data
                                self.collectedData[country][city]["forecast"][2]["rain"] = error_data

                except Exception as e:
                    self._fail_ctr += 1
                    logging.exception("[%s]: Could not get weather data for %s in %s."
                                      % (self._log_tag, city, country))
                    if data is not None:
                        logging.error("[%s]: Received data from server: %s"
                                      % (self._log_tag, data))

                    if self._fail_ctr >= max_tolerated_fails:
                        with self.updateLock:
                            error_data = WeatherData(None,
                                                     SensorErrorState(SensorErrorState.ProcessingError,
                                                                      "Not able to parse data: %s" % str(e)))
                            self.collectedData[country][city]["humidity"] = error_data
                            self.collectedData[country][city]["temp"] = error_data
                            self.collectedData[country][city]["forecast"][0]["tempHigh"] = error_data
                            self.collectedData[country][city]["forecast"][0]["tempLow"] = error_data
                            self.collectedData[country][city]["forecast"][0]["rain"] = error_data
                            self.collectedData[country][city]["forecast"][1]["tempHigh"] = error_data
                            self.collectedData[country][city]["forecast"][1]["tempLow"] = error_data
                            self.collectedData[country][city]["forecast"][1]["rain"] = error_data
                            self.collectedData[country][city]["forecast"][2]["tempHigh"] = error_data
                            self.collectedData[country][city]["forecast"][2]["tempLow"] = error_data
                            self.collectedData[country][city]["forecast"][2]["rain"] = error_data

            # Sleep until next update cycle.
            if self._exit_event.wait(self.interval):
                return

    def exit(self):
        self._exit_event.set()
