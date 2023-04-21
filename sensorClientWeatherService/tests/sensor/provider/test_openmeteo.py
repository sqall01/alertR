import datetime
import json
import os
import time
import logging
from unittest import TestCase
from typing import Optional
from lib.sensor.provider import OpenMeteoDataCollector
from lib.globalData.sensorObjects import SensorErrorState


class MockOpenMeteoCollector(OpenMeteoDataCollector):

    def __init__(self, interval: int):
        super(MockOpenMeteoCollector, self).__init__(interval)
        self.return_valid = True

    def _get_data(self,
                  country: Optional[str] = None,
                  city: Optional[str] = None,
                  lon: Optional[str] = None,
                  lat: Optional[str] = None) -> Optional[str]:

        if self.return_valid:
            input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "data",
                                      "response_openmeteo.json")
            with open(input_file, 'rt') as fp:
                return json.loads(fp.read())

        return None


class TestOpenMeteo(TestCase):

    def setUp(self):
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%m/%d/%Y %H:%M:%S',
                            level=logging.INFO)

        self._collector = MockOpenMeteoCollector(30)
        self._collector.daemon = True

        self._country = "Germany"
        self._city = "Bochum"
        self._lon = "7.2162363"
        self._lat = "51.4818445"
        self._collector.addLocation(self._country,
                                    self._city,
                                    self._lon,
                                    self._lat)

    def tearDown(self):
        self._collector.exit()

    def test_integration_valid_data_processing(self):
        """
        Tests if data is processed correctly.
        """

        # Check no value exist during initialization.
        humidity = self._collector.getHumidity(self._country,
                                               self._city,
                                               self._lon,
                                               self._lat)
        self.assertIsNone(humidity.data)
        self.assertEqual(humidity.error.state, SensorErrorState.ValueError)

        temperature = self._collector.getTemperature(self._country,
                                                     self._city,
                                                     self._lon,
                                                     self._lat)
        self.assertIsNone(temperature.data)
        self.assertEqual(temperature.error.state, SensorErrorState.ValueError)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        0)
        self.assertIsNone(rain_forecast.data)
        self.assertEqual(rain_forecast.error.state, SensorErrorState.ValueError)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        1)
        self.assertIsNone(rain_forecast.data)
        self.assertEqual(rain_forecast.error.state, SensorErrorState.ValueError)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        2)
        self.assertIsNone(rain_forecast.data)
        self.assertEqual(rain_forecast.error.state, SensorErrorState.ValueError)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      0)
        self.assertIsNone(temp_forecast_low.data)
        self.assertEqual(temp_forecast_low.error.state, SensorErrorState.ValueError)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      1)
        self.assertIsNone(temp_forecast_low.data)
        self.assertEqual(temp_forecast_low.error.state, SensorErrorState.ValueError)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      2)
        self.assertIsNone(temp_forecast_low.data)
        self.assertEqual(temp_forecast_low.error.state, SensorErrorState.ValueError)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        0)
        self.assertIsNone(temp_forecast_high.data)
        self.assertEqual(temp_forecast_high.error.state, SensorErrorState.ValueError)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        1)
        self.assertIsNone(temp_forecast_high.data)
        self.assertEqual(temp_forecast_high.error.state, SensorErrorState.ValueError)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        2)
        self.assertIsNone(temp_forecast_high.data)
        self.assertEqual(temp_forecast_high.error.state, SensorErrorState.ValueError)

        # Start data processing.
        self._collector.start()

        # Wait until the data was processed.
        time.sleep(1)

        # Check correct values are returned.
        humidity = self._collector.getHumidity(self._country,
                                               self._city,
                                               self._lon,
                                               self._lat)
        self.assertIsNone(humidity.error)
        self.assertEqual(humidity.data, 10 + datetime.datetime.now().hour)

        temperature = self._collector.getTemperature(self._country,
                                                     self._city,
                                                     self._lon,
                                                     self._lat)
        self.assertIsNone(temperature.error)
        self.assertEqual(temperature.data, 11.5)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        0)
        self.assertIsNone(rain_forecast.error)
        self.assertEqual(rain_forecast.data, 100)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        1)
        self.assertIsNone(rain_forecast.error)
        self.assertEqual(rain_forecast.data, 90)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        2)
        self.assertIsNone(rain_forecast.error)
        self.assertEqual(rain_forecast.data, 97)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      0)
        self.assertIsNone(temp_forecast_low.error)
        self.assertEqual(temp_forecast_low.data, 9.5)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      1)
        self.assertIsNone(temp_forecast_low.error)
        self.assertEqual(temp_forecast_low.data, 7.6)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      2)
        self.assertIsNone(temp_forecast_low.error)
        self.assertEqual(temp_forecast_low.data, 3.5)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        0)
        self.assertIsNone(temp_forecast_high.error)
        self.assertEqual(temp_forecast_high.data, 13.8)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        1)
        self.assertIsNone(temp_forecast_high.error)
        self.assertEqual(temp_forecast_high.data, 10.1)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        2)
        self.assertIsNone(temp_forecast_high.error)
        self.assertEqual(temp_forecast_high.data, 8.7)

    def test_integration_no_data_processing(self):
        """
        Tests if no data is processed correctly.
        """

        self._collector.return_valid = False

        # Check no value exist during initialization.
        humidity = self._collector.getHumidity(self._country,
                                               self._city,
                                               self._lon,
                                               self._lat)
        self.assertIsNone(humidity.data)
        self.assertEqual(humidity.error.state, SensorErrorState.ValueError)

        temperature = self._collector.getTemperature(self._country,
                                                     self._city,
                                                     self._lon,
                                                     self._lat)
        self.assertIsNone(temperature.data)
        self.assertEqual(temperature.error.state, SensorErrorState.ValueError)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        0)
        self.assertIsNone(rain_forecast.data)
        self.assertEqual(rain_forecast.error.state, SensorErrorState.ValueError)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        1)
        self.assertIsNone(rain_forecast.data)
        self.assertEqual(rain_forecast.error.state, SensorErrorState.ValueError)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        2)
        self.assertIsNone(rain_forecast.data)
        self.assertEqual(rain_forecast.error.state, SensorErrorState.ValueError)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      0)
        self.assertIsNone(temp_forecast_low.data)
        self.assertEqual(temp_forecast_low.error.state, SensorErrorState.ValueError)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      1)
        self.assertIsNone(temp_forecast_low.data)
        self.assertEqual(temp_forecast_low.error.state, SensorErrorState.ValueError)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      2)
        self.assertIsNone(temp_forecast_low.data)
        self.assertEqual(temp_forecast_low.error.state, SensorErrorState.ValueError)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        0)
        self.assertIsNone(temp_forecast_high.data)
        self.assertEqual(temp_forecast_high.error.state, SensorErrorState.ValueError)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        1)
        self.assertIsNone(temp_forecast_high.data)
        self.assertEqual(temp_forecast_high.error.state, SensorErrorState.ValueError)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        2)
        self.assertIsNone(temp_forecast_high.data)
        self.assertEqual(temp_forecast_high.error.state, SensorErrorState.ValueError)

        self.assertEqual(self._collector._fail_ctr, 0)

        # Start data processing.
        self._collector.start()

        # Wait until the data was processed.
        time.sleep(1)

        # Check fail counter has increased.
        self.assertEqual(self._collector._fail_ctr, 1)

        # Check no value exist due to missing data.
        humidity = self._collector.getHumidity(self._country,
                                               self._city,
                                               self._lon,
                                               self._lat)
        self.assertIsNone(humidity.data)
        self.assertEqual(humidity.error.state, SensorErrorState.ValueError)

        temperature = self._collector.getTemperature(self._country,
                                                     self._city,
                                                     self._lon,
                                                     self._lat)
        self.assertIsNone(temperature.data)
        self.assertEqual(temperature.error.state, SensorErrorState.ValueError)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        0)
        self.assertIsNone(rain_forecast.data)
        self.assertEqual(rain_forecast.error.state, SensorErrorState.ValueError)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        1)
        self.assertIsNone(rain_forecast.data)
        self.assertEqual(rain_forecast.error.state, SensorErrorState.ValueError)

        rain_forecast = self._collector.getForecastRain(self._country,
                                                        self._city,
                                                        self._lon,
                                                        self._lat,
                                                        2)
        self.assertIsNone(rain_forecast.data)
        self.assertEqual(rain_forecast.error.state, SensorErrorState.ValueError)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      0)
        self.assertIsNone(temp_forecast_low.data)
        self.assertEqual(temp_forecast_low.error.state, SensorErrorState.ValueError)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      1)
        self.assertIsNone(temp_forecast_low.data)
        self.assertEqual(temp_forecast_low.error.state, SensorErrorState.ValueError)

        temp_forecast_low = self._collector.getForecastTemperatureLow(self._country,
                                                                      self._city,
                                                                      self._lon,
                                                                      self._lat,
                                                                      2)
        self.assertIsNone(temp_forecast_low.data)
        self.assertEqual(temp_forecast_low.error.state, SensorErrorState.ValueError)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        0)
        self.assertIsNone(temp_forecast_high.data)
        self.assertEqual(temp_forecast_high.error.state, SensorErrorState.ValueError)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        1)
        self.assertIsNone(temp_forecast_high.data)
        self.assertEqual(temp_forecast_high.error.state, SensorErrorState.ValueError)

        temp_forecast_high = self._collector.getForecastTemperatureHigh(self._country,
                                                                        self._city,
                                                                        self._lon,
                                                                        self._lat,
                                                                        2)
        self.assertIsNone(temp_forecast_high.data)
        self.assertEqual(temp_forecast_high.error.state, SensorErrorState.ValueError)
