#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import logging
import time

from .core import _PollingSensor
from ..globalData import SensorOrdering
from typing import Optional, Union


class _WeatherSensor(_PollingSensor):
    """
    Represents the base for a weather sensor that is able to check thresholds.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # Used for logging.
        self._log_tag = os.path.basename(__file__)

        # This flag indicates if this sensor has a threshold that should be
        # checked and raise a sensor alert if it is reached.
        self.hasThreshold = False

        # The threshold that should raise a sensor alert if it is reached.
        self.threshold = None

        # Says how the threshold should be checked
        # (lower than, equal, greater than).
        self.ordering = None

        # As long as errors occurring during the fetching of data are encoded as negative values,
        # we need the lowest value that we use for our threshold check.
        self._sane_lowest_value = None  # type: Optional[Union[float, int]]

        # Optional data send with every Sensor Alert.
        self._optional_data = None

        # This sensor type string is used for log messages.
        self._sensor_type = "Placeholder"

    def _execute(self):
        while True:

            if self._exit_flag:
                return

            time.sleep(0.5)

            data = self._get_data()
            if data != self.sensorData:
                self._add_state_change(self.state, data)

            # Only check if threshold is reached if threshold check is activated.
            if self.hasThreshold:

                # Sensor is currently triggered => Check if it is "normal" again.
                if self.state == self.triggerState:
                    if self.ordering == SensorOrdering.LT:
                        if self.sensorData >= self.threshold and self.sensorData >= self._sane_lowest_value:
                            logging.info("[%s] %s %.1f of sensor '%s' is above threshold (back to normal)."
                                         % (self._log_tag, self._sensor_type, float(self.sensorData), self.description))

                            self._add_sensor_alert(1 - self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   self.sensorData)

                    elif self.ordering == SensorOrdering.EQ:
                        if self.sensorData != self.threshold and self.sensorData >= self._sane_lowest_value:
                            logging.info("[%s] %s %.1f of sensor '%s' is unequal to threshold (back to normal)."
                                         % (self._log_tag, self._sensor_type, float(self.sensorData), self.description))

                            self._add_sensor_alert(1 - self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   self.sensorData)

                    elif self.ordering == SensorOrdering.GT:
                        if 0 <= self.sensorData <= self.threshold:
                            logging.info("[%s] %s %.1f of sensor '%s' is below threshold (back to normal)."
                                         % (self._log_tag, self._sensor_type, float(self.sensorData), self.description))

                            self._add_sensor_alert(1 - self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   self.sensorData)

                    else:
                        logging.error("[%s] Do not know how to check threshold. Skipping check."
                                      % self._log_tag)

                # Sensor is currently not triggered => Check if it has to be triggered.
                else:
                    if self.ordering == SensorOrdering.LT:
                        if 0 <= self.sensorData < self.threshold:
                            logging.info("[%s] %s %.1f of sensor '%s' is below threshold (triggered)."
                                         % (self._log_tag, self._sensor_type, float(self.sensorData), self.description))

                            self._add_sensor_alert(self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   self.sensorData)

                    elif self.ordering == SensorOrdering.EQ:
                        if self.sensorData == self.threshold and self.sensorData >= self._sane_lowest_value:
                            logging.info("[%s] %s %.1f of sensor '%s' is equal to threshold (triggered)."
                                         % (self._log_tag, self._sensor_type, float(self.sensorData), self.description))

                            self._add_sensor_alert(self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   self.sensorData)

                    elif self.ordering == SensorOrdering.GT:
                        if self.sensorData > self.threshold and self.sensorData >= self._sane_lowest_value:
                            logging.info("[%s] %s %.1f of sensor '%s' is above threshold (triggered)."
                                         % (self._log_tag, self._sensor_type, float(self.sensorData), self.description))

                            self._add_sensor_alert(self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   self.sensorData)

                    else:
                        logging.error("[%s] Do not know how to check threshold. Skipping check."
                                      % self._log_tag)

    def _get_data(self) -> Union[float, int]:
        raise NotImplementedError("Function not implemented yet.")
