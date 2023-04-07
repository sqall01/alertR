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
import os
from datetime import datetime
from typing import Optional, Dict, Any, cast

from .core import _DataCollector, WeatherData
from ...globalData.sensorObjects import SensorErrorState


class OpenMeteoDataCollector(_DataCollector):

    def __init__(self, interval: int):
        super(OpenMeteoDataCollector, self).__init__()

        self._log_tag = os.path.basename(__file__)

        self.updateLock = threading.Lock()

        self.host = "https://api.open-meteo.com"

        # Interval in seconds in which the data is fetched.
        self.interval = interval

        # Dict with tuples in the form (lon, lat) as key.
        self.locations = dict()

        # Dictionary that holds the data that is collected in the form:
        # collectedData[<lon>][<lat>]["temp"/"humidity"]
        self.collectedData = dict()

        self._exit_event = threading.Event()
        self._exit_event.clear()

        self._fail_ctr = 0

    def _get_data(self,
                  country: Optional[str] = None,
                  city: Optional[str] = None,
                  lon: Optional[str] = None,
                  lat: Optional[str] = None) -> Optional[Dict[str, Any]]:

        try:
            url = self.host \
                  + "/v1/forecast" \
                  + "?latitude=%s" % lat \
                  + "&longitude=%s" % lon \
                  + "&hourly=relativehumidity_2m" \
                  + "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max" \
                  + "&current_weather=true" \
                  + "&forecast_days=3" \
                  + "&timezone=auto"
            r = requests.get(url, verify=True, timeout=60.0)

            # Extract data.
            if r.status_code == 200:
                return cast(dict, r.json())
            else:
                logging.error("[%s]: Received response code %d from OpenMeteo."
                              % (self._log_tag, r.status_code))

        except Exception as e:
            logging.exception("[%s]: Could not get weather data for %s in %s."
                              % (self._log_tag, city, country))

        return None

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

        logging.info("[%s]: Starting OpenMeteo data collector thread." % self._log_tag)

        # Tolerate failed updates for at least 12 hours.
        max_tolerated_fails = int(43200 / self.interval) + 1

        self._fail_ctr = 0
        while True:

            for location_tuple in self.locations.keys():

                lon = location_tuple[0]
                lat = location_tuple[1]
                country = self.locations[location_tuple]["country"]
                city = self.locations[location_tuple]["city"]

                logging.debug("[%s]: Getting weather data from OpenMeteo for %s in %s."
                              % (self._log_tag, city, country))

                json_data = self._get_data(country=country, city=city, lon=lon, lat=lat)

                try:
                    if json_data:

                        humidity = WeatherData(int(json_data["hourly"]["relativehumidity_2m"][datetime.now().hour]))
                        temp = WeatherData(float(json_data["current_weather"]["temperature"]))
                        forecast_day0_temp_high = WeatherData(float(json_data["daily"]["temperature_2m_max"][0]))
                        forecast_day0_temp_low = WeatherData(float(json_data["daily"]["temperature_2m_min"][0]))
                        forecast_day0_rain = WeatherData(int(json_data["daily"]["precipitation_probability_max"][0]))
                        forecast_day1_temp_high = WeatherData(float(json_data["daily"]["temperature_2m_max"][1]))
                        forecast_day1_temp_low = WeatherData(float(json_data["daily"]["temperature_2m_min"][1]))
                        forecast_day1_rain = WeatherData(int(json_data["daily"]["precipitation_probability_max"][1]))
                        forecast_day2_temp_high = WeatherData(float(json_data["daily"]["temperature_2m_max"][2]))
                        forecast_day2_temp_low = WeatherData(float(json_data["daily"]["temperature_2m_min"][2]))
                        forecast_day2_rain = WeatherData(int(json_data["daily"]["precipitation_probability_max"][2]))

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
                    self._fail_ctr += 1
                    logging.exception("[%s]: Could not get weather data for %s in %s."
                                      % (self._log_tag, city, country))
                    if json_data is not None:
                        logging.error("[%s]: Received data from server: %s"
                                      % (self._log_tag, json_data))

                    if self._fail_ctr >= max_tolerated_fails:
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
            if self._exit_event.wait(self.interval):
                return

    def exit(self):
        self._exit_event.set()
