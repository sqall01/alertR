import os
import time
import logging
from unittest import TestCase
from typing import Optional
from lib.sensor.provider.wunderground import WundergroundDataCollector


class MockWundergroundCollector(WundergroundDataCollector):

    def __init__(self, interval: int, api_key: str):
        super(MockWundergroundCollector, self).__init__(interval, api_key)
        self.return_valid = True

    def _get_data(self,
                  country: Optional[str] = None,
                  city: Optional[str] = None,
                  lon: Optional[str] = None,
                  lat: Optional[str] = None) -> Optional[str]:

        if self.return_valid:
            input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "data",
                                      "response_wunderground.json")
            with open(input_file, 'rt') as fp:
                return fp.read()

        return None


class TestWunderground(TestCase):

    def setUp(self):
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%m/%d/%Y %H:%M:%S',
                            level=logging.INFO)

        self._collector = MockWundergroundCollector(30, "Test")
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

        raise NotImplementedError("TODO")

    def test_integration_no_data_processing(self):
        """
        Tests if no data is processed correctly.
        """

        raise NotImplementedError("TODO")
