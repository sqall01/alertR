#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import time
from typing import Tuple, Optional, List, Dict, Any
from shapely import geometry, prepared
from .core import _PollingSensor
from ..globalData.sensorObjects import SensorDataGPS, SensorDataType, SensorErrorState


class _GPSSensor(_PollingSensor):
    """
    Represents a sensor that controls one GPS device.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to hold GPS data.
        self.sensorDataType = SensorDataType.GPS

        # Initialize sensor with bogus GPS data to allow connection to server or otherwise invalid data is sent to
        # server and connection is terminated. While a GPS position (0.0, 0.0) at 1/1/1970 is technically valid,
        # we consider it as bogus since the sensor is build to track current and not historical positions.
        self.data = SensorDataGPS(0.0, 0.0, 0)

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

        self._old_gps_data_ctr = 0
        self._old_gps_data_threshold = 10

        self._polygons = []  # type: List[prepared.PreparedGeometry]

    def _process_position(self, gps_data: SensorDataGPS):

        # Do not process GPS positions that is equal to the last position.
        if self.data == gps_data:
            return

        self._log_debug(self._log_tag, "GPS position: %f, %f" % (gps_data.lat, gps_data.lon))

        # According to a tutorial, shapely needs coordinates in the form longitude, latitude.
        point = geometry.Point(gps_data.lon, gps_data.lat)

        if any([poly.contains(point) for poly in self._polygons]):
            if self.trigger_within:
                if self.state != self.triggerState:
                    # Point inside polygon, should trigger within, state is not triggered yet.
                    self._add_sensor_alert(self.triggerState,
                                           True,
                                           optional_data=self._get_optional_data(),
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
                                           optional_data=self._get_optional_data(),
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
                                           optional_data=self._get_optional_data(),
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
                                           optional_data=self._get_optional_data(),
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
            self._log_exception(self._log_tag, "Unable to build polygon for geofence.")
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
                    self._log_exception(self._log_tag, "Unable to fetch GPS data from provider: %s" % str(e))
                    self._set_error_state(SensorErrorState.ProcessingError,
                                          "Unable to fetch GPS data from provider: %s" % str(e))

                    continue

                # Check if received GPS data is newer than the last one.
                if gps_data.utctime == self._last_utctime:
                    self._log_debug(self._log_tag, "No GPS data update.")
                    self._clear_error_state()
                    continue
                if gps_data.utctime < self._last_utctime:
                    self._log_error(self._log_tag, "Received old GPS data.")

                    # Set an error state if we receive old GPS data too often in a row.
                    self._old_gps_data_ctr += 1
                    if self._old_gps_data_ctr > self._old_gps_data_threshold:
                        self._set_error_state(SensorErrorState.ValueError,
                                              "Received old GPS data for %d times." % self._old_gps_data_ctr)
                    continue
                self._last_utctime = gps_data.utctime
                self._old_gps_data_ctr = 0

                self._process_position(gps_data)

    def _get_data(self) -> SensorDataGPS:
        """
        Internal function to get data from the GPS provider.
        Throws exception in error cases.
        :return: Tuple with latitude, longitude and utc timestamp
        """
        raise NotImplementedError("Function not implemented yet.")

    def _get_optional_data(self) -> Optional[Dict[str, Any]]:
        """
        Internal function to get optional data used for a sensor alert.
        :return: None for no optional data or dict for optional data.
        """
        raise NotImplementedError("Function not implemented yet.")
