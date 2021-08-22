#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import time
import logging
from typing import Tuple, Optional
from .core import _PollingSensor
from ..globalData import SensorDataType


class _GPSSensor(_PollingSensor):
    """
    Represents a sensor that controls one GPS device.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.GPS

        # used for logging
        self._log_tag = os.path.basename(__file__)

        # Interval in which GPS data is fetched.
        self.interval = None  # type: Optional[int]

        self._last_get_data = 0

    def initialize(self) -> bool:
        """
        This function is called once before the sensor client has connected itself
        to the server (should be use to initialize everything that is needed
        for the sensor).
        :return: success or failure
        """
        self.state = 1 - self.triggerState

        return True

    def _execute(self):
        """
        This function runs as a thread and never returns (should only return if the exit flag is set).
        This function should contain the complete sensor logic for everything that needs to be monitored.
        :return:
        """

        while True:

            time.sleep(0.5)

            if self._exit_flag:
                return

            current_time = int(time.time())
            if (current_time - self._last_get_data) > self.interval:
                try:
                    lat, lon, utctime = self._get_data()

                except Exception as e:
                    lo

            print("Sensor: executing sensor logic")

    def _get_data(self) -> Tuple[float, float, int]:
        raise NotImplementedError("Function not implemented yet.")


'''
Tool to get GPS coordinates on map and draw polygons: https://umap.openstreetmap.fr/en/map/new
'''