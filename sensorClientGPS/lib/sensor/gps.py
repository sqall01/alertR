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
from typing import Tuple, Optional, List
from shapely import geometry, prepared
from .core import _PollingSensor
from ..globalData import SensorDataType, SensorDataGPS


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

        # List of polygons which contain tuples in (latitude, longitude) form.
        self.polygons = []  # type: List[List[Tuple[float, float]]]

        # Does sensor trigger if point is within or without the polygon.
        self.trigger_within = True

        self._last_get_data = 0

        self._last_utctime = 0

        self._polygons = []  # type: List[prepared.PreparedGeometry]

    def _process_position(self, gps_data: SensorDataGPS):

        if self.sensorData is not None and self.sensorData == gps_data:
            return

        logging.debug("[%s] GPS position for '%s': %f, %f"
                      % (self._log_tag, self.description, gps_data.lat, gps_data.lon))

        # According to a tutorial, shapely needs coordinates in the form longitude, latitude.
        point = geometry.Point(gps_data.lon, gps_data.lat)

        if any([poly.contains(point) for poly in self._polygons]):
            if self.trigger_within:
                if self.state != self.triggerState:
                    # Point inside polygon, should trigger within, state is not triggered yet.
                    self._add_sensor_alert(self.triggerState,
                                           True,
                                           has_latest_data=True,
                                           sensor_data=gps_data)

                else:
                    # Point inside polygon, should trigger within, state is already triggered.
                    self._add_state_change(self.state,
                                           gps_data)

            else:
                if self.state != (1 - self.triggerState):
                    # Point inside polygon, should trigger outside, state is already triggered.
                    self._add_sensor_alert(1 - self.triggerState,
                                           True,
                                           has_latest_data=True,
                                           sensor_data=gps_data)

                else:
                    # Point inside polygon, should trigger outside, state is not triggered yet.
                    self._add_state_change(self.state,
                                           gps_data)

        else:
            if self.trigger_within:
                if self.state != (1 - self.triggerState):
                    # Point outside polygon, should trigger within, state is already triggered.
                    self._add_sensor_alert(1 - self.triggerState,
                                           True,
                                           has_latest_data=True,
                                           sensor_data=gps_data)

                else:
                    # Point outside polygon, should trigger within, state is not triggered yet.
                    self._add_state_change(self.state,
                                           gps_data)

            else:
                if self.state != self.triggerState:
                    # Point outside polygon, should trigger outside, state is not triggered yet.
                    self._add_sensor_alert(self.triggerState,
                                           True,
                                           has_latest_data=True,
                                           sensor_data=gps_data)

                else:
                    # Point outside polygon, should trigger outside, state is already triggered.
                    self._add_state_change(self.state,
                                           gps_data)

    def initialize(self) -> bool:
        """
        This function is called once before the sensor client has connected itself
        to the server (should be use to initialize everything that is needed
        for the sensor).
        :return: success or failure
        """
        self.state = 1 - self.triggerState

        # Prepare geofence.
        try:
            for polygon in self.polygons:
                shapely_coordinates = []
                for coord in polygon:
                    # According to a tutorial, shapely needs coordinates in the form longitude, latitude.
                    shapely_coordinates.append((coord[1], coord[0]))
                polygon = geometry.Polygon(shapely_coordinates)
                self._polygons.append(prepared.prep(polygon))

        except Exception as e:
            logging.exception("[%s] Unable to build polygon for geofence." % self._log_tag)
            return False

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

            # Update GPS position if interval has exceeded.
            current_time = int(time.time())
            if (current_time - self._last_get_data) > self.interval:

                # Update time directly to not hammer the server if an error occurs.
                self._last_get_data = current_time

                try:
                    gps_data = self._get_data()

                except Exception as e:
                    logging.exception("[%s] Unable to fetch GPS data from provider." % self._log_tag)
                    continue

                # Check if received GPS data is newer than the last one.
                if gps_data.utctime == self._last_utctime:
                    logging.debug("[%s] No GPS data update." % self._log_tag)
                    continue
                if gps_data.utctime < self._last_utctime:
                    logging.error("[%s] Received old GPS data." % self._log_tag)
                    continue
                self._last_utctime = gps_data.utctime

                self._process_position(gps_data)

    def _get_data(self) -> SensorDataGPS:
        """
        Internal function to get data from the GPS provider.
        :return: Tuple with latitude, longitude and utc timestamp
        """
        raise NotImplementedError("Function not implemented yet.")
