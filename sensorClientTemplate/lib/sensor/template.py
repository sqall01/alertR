#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import time
from .core import _PollingSensor
from ..globalData import SensorDataType
from ..globalData.sensorObjects import SensorDataNone


# Class that controls one template sensor.
class TemplateSensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.NONE
        self.data = SensorDataNone()

        # used for logging
        self._log_tag = os.path.basename(__file__)

    def initialize(self) -> bool:
        """
        This function is called once before the sensor client has connected itself
        to the server (should be use to initialize everything that is needed
        for the sensor).
        :return: success or failure
        """
        self.state = 1 - self.triggerState

        print("Sensor: initialize")

        # PLACE YOUR CODE HERE

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

            print("Sensor: executing sensor logic")

            # PLACE YOUR CODE HERE

            # Use self._add_state_change() to initiate a state change message to the server
            # (e.g., if the sensor data has changed). See function definition for detailed information.

            # Use self._add_sensor_alert() to initiate a sensor alert message to the server.
            # See function definition for detailed information.
