#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import time
from typing import Optional, Union
from .core import _PollingSensor
from ..globalData.sensorObjects import SensorDataInt, SensorDataFloat, SensorOrdering, SensorErrorState


# noinspection PyAbstractClass
class _NumberSensor(_PollingSensor):
    """
    Represents the base for a numeric (int, float) sensor that is able to check thresholds.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # Used for logging.
        self._log_tag = os.path.basename(__file__)

        # This flag indicates if this sensor sends Sensor Alert events to the server
        # whenever new sensor data is available instead of Sensor Change events.
        # Since AlertR is an event driven system, this can be useful for reacting to data changes.
        self.sensorAlertForDataChange = False

        # This flag indicates if this sensor has a threshold that should be
        # checked and raise a sensor alert if it is reached.
        self.hasThreshold = False

        # The threshold that should raise a sensor alert if it is reached.
        self.threshold = None

        # Says how the threshold should be checked
        # (lower than, equal, greater than).
        self.ordering = None  # type: Optional[SensorOrdering]

        # Optional data send with every Sensor Alert.
        self._optional_data = None

        # This string is used for log messages and holds the type of the sensor.
        self._log_desc = None  # type: Optional[str]

    def _execute(self):
        while True:

            if self._exit_flag:
                return

            time.sleep(0.5)

            data = self._get_data()
            if data is None:
                continue

            self._log_debug(self._log_tag, "%s %s." % (self._log_desc, data))

            # Only check if threshold is reached if threshold check is activated.
            if self.hasThreshold:

                # Sensor is currently triggered => Check if it is "normal" again.
                if self.state == self.triggerState:
                    if self.ordering == SensorOrdering.LT:
                        if data.value >= self.threshold:
                            self._log_info(self._log_tag, "%s %s is above threshold (back to normal)."
                                           % (self._log_desc, data))

                            self._add_sensor_alert(1 - self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   data)

                    elif self.ordering == SensorOrdering.EQ:
                        if data.value != self.threshold:
                            self._log_info(self._log_tag, "%s %s is unequal to threshold (back to normal)."
                                           % (self._log_desc, data))

                            self._add_sensor_alert(1 - self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   data)

                    elif self.ordering == SensorOrdering.GT:
                        if 0 <= data.value <= self.threshold:
                            self._log_info(self._log_tag, "%s %s is below threshold (back to normal)."
                                           % (self._log_desc, data))

                            self._add_sensor_alert(1 - self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   data)

                    else:
                        self._log_error(self._log_tag, "Do not know how to check threshold. Skipping check.")
                        self._set_error_state(SensorErrorState.ProcessingError, "Unknown threshold setting.")

                # Sensor is currently not triggered => Check if it has to be triggered.
                else:
                    if self.ordering == SensorOrdering.LT:
                        if 0 <= data.value < self.threshold:
                            self._log_info(self._log_tag, "%s %s is below threshold (triggered)."
                                           % (self._log_desc, data))

                            self._add_sensor_alert(self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   data)

                    elif self.ordering == SensorOrdering.EQ:
                        if data.value == self.threshold:
                            self._log_info(self._log_tag, "%s %s is equal to threshold (triggered)."
                                           % (self._log_desc, data))

                            self._add_sensor_alert(self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   data)

                    elif self.ordering == SensorOrdering.GT:
                        if data.value > self.threshold:
                            self._log_info(self._log_tag, "%s %s is above threshold (triggered)."
                                           % (self._log_desc, data))

                            self._add_sensor_alert(self.triggerState,
                                                   True,
                                                   self._optional_data,
                                                   True,
                                                   data)

                    else:
                        self._log_error(self._log_tag, "Do not know how to check threshold. Skipping check.")
                        self._set_error_state(SensorErrorState.ProcessingError, "Unknown threshold setting.")

            if data != self.data:
                if self.sensorAlertForDataChange:
                    self._add_sensor_alert(self.state, False, has_latest_data=True, sensor_data=data)

                else:
                    self._add_state_change(self.state, data)

            # Even if the data has not changed, an error could occur in between which causes the
            # sensor to have an error state. Clear it if we received new data.
            else:
                self._clear_error_state()

    def _get_data(self) -> Optional[Union[SensorDataInt, SensorDataFloat]]:
        raise NotImplementedError("Abstract class.")

    def start(self) -> bool:
        """
        Starts the number sensor and checks if the object has necessary values set.

        :return: success or failure
        """
        if self._log_desc is None:
            self._log_critical(self._log_tag, "Variable '_log_desc' not set in object.")
            return False

        if self.hasThreshold:
            if self.ordering is None:
                self._log_critical(self._log_tag, "Variable 'ordering' not set in object.")
                return False

            if self.threshold is None:
                self._log_critical(self._log_tag, "Variable 'threshold' not set in object.")
                return False

        return super().start()
