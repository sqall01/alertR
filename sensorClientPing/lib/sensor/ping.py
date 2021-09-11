#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import subprocess
import time
import logging
from typing import Optional
from .core import _PollingSensor
from ..globalData import SensorDataType
from ..globalData.sensorObjects import SensorDataNone


class PingSensor(_PollingSensor):
    """
    Class that controls one ping checked host.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.NONE
        self.sensorData = SensorDataNone()

        # used for logging
        self._log_tag = os.path.basename(__file__)

        # gives the time that the process has to execute
        self.timeout = None

        # gives the interval in seconds in which the process
        # should be checked
        self.intervalToCheck = None

        # gives the command/path that should be executed
        self.execute = None

        # gives the host of the service
        self.host = None

        # Time when the process was executed.
        self._time_executed = 0

        # the process itself
        self._process = None  # type: Optional[subprocess.Popen]

    def initialize(self) -> bool:
        self._time_executed = 0
        self.state = 1 - self.triggerState
        return True

    def _execute(self):

        while True:

            if self._exit_flag:
                if self._process is not None:
                    self._process.terminate()

                    # Give process 5 seconds to terminate before killing it.
                    try:
                        self._process.wait(5.0)

                    except subprocess.TimeoutExpired:
                        self._process.kill()

                return

            if self._process is None:

                # Check if the interval in which the service should be checked is exceeded.
                utc_timestamp = int(time.time())
                if (utc_timestamp - self._time_executed) > self.intervalToCheck:

                    logging.debug("[%s] Executing process for '%s'." % (self._log_tag, self.description))

                    try:
                        # Set time before executing process in order to not hammer process creation
                        # if the process execution throws an exception.
                        self._time_executed = utc_timestamp
                        self._process = subprocess.Popen([self.execute, "-c3", str(self.host)])

                    except Exception as e:
                        logging.exception("[%s] Unable to execute process for '%s'."
                                          % (self._log_tag, self.description))

                        optional_data = {"host": self.host,
                                         "reason": "processerror",
                                         "message": "Unable to execute process"}
                        self._add_sensor_alert(self.triggerState,
                                               False,
                                               optional_data)

            # Process is still running.
            else:

                # Check if process is not finished yet.
                if self._process.poll() is None:

                    # Check if process has timed out
                    utc_timestamp = int(time.time())
                    if (utc_timestamp - self._time_executed) > self.timeout:
                        logging.error("[%s] Process for '%s' has timed out."
                                      % (self._log_tag, self.description))

                        # terminate process
                        self._process.terminate()

                        # Give the process time to terminate.
                        try:
                            self._process.wait(5.0)

                        except subprocess.TimeoutExpired:
                            logging.error("[%s] Could not terminate process for '%s'. Killing it."
                                          % (self._log_tag, self.description))

                            self._process.kill()

                        exit_code = self._process.poll()
                        new_state = self.triggerState

                        # Process state change.
                        if new_state != self.state:

                            # Check if the sensor triggers a sensor alert => send sensor alert to server.
                            if self.triggerAlert:
                                optional_data = {"message": "Timeout",
                                                 "host": self.host,
                                                 "reason": "processtimeout",
                                                 "exitCode": exit_code}
                                self._add_sensor_alert(self.triggerState,
                                                       True,
                                                       optional_data)

                            # If sensor does not trigger sensor alert => just send changed state to server.
                            else:
                                self._add_state_change(self.triggerState)

                        # Set process to None so it can be newly started in the next iteration.
                        self._process = None

                # Process has finished.
                else:
                    optional_data = {"host": self.host}

                    # Check if the process has exited with code 0 = host reachable.
                    exit_code = self._process.poll()
                    if exit_code == 0:
                        new_state = 1 - self.triggerState
                        optional_data["reason"] = "reachable"

                    # Process did not exited correctly => host not reachable.
                    else:
                        new_state = self.triggerState
                        optional_data["reason"] = "notreachable"

                    optional_data["exitCode"] = exit_code

                    # Process state change.
                    if new_state != self.state:

                        # Check if the current state is a sensor alert triggering state.
                        if new_state == self.triggerState:

                            # Check if the sensor triggers a sensor alert => send sensor alert to server.
                            if self.triggerAlert:
                                self._add_sensor_alert(self.triggerState,
                                                       True,
                                                       optional_data)

                            # If sensor does not trigger sensor alert => just send changed state to server.
                            else:
                                self._add_state_change(self.triggerState)

                        # Only possible situation left => sensor changed back from triggering state to normal state.
                        else:

                            # Check if the sensor triggers a Sensor Alert when state is back to normal
                            # => send sensor alert to server
                            if self.triggerAlertNormal:
                                self._add_sensor_alert(1 - self.triggerState,
                                                       True,
                                                       optional_data)

                            # If sensor does not trigger Sensor Alert when state is back to normal
                            # => just send changed state to server.
                            else:
                                self._add_state_change(1 - self.triggerState)

                    # Set process to none so it can be newly started in the next iteration.
                    self._process = None

            time.sleep(0.5)
