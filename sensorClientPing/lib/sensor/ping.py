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
from typing import Optional
from .core import _PollingSensor
from ..globalData.sensorObjects import SensorDataNone, SensorDataType, SensorErrorState


class PingSensor(_PollingSensor):
    """
    Class that controls one ping checked host.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.NONE
        self.data = SensorDataNone()

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

                    self._log_debug(self._log_tag, "Executing process.")

                    try:
                        # Set time before executing process in order to not hammer process creation
                        # if the process execution throws an exception.
                        self._time_executed = utc_timestamp
                        self._process = subprocess.Popen([self.execute, "-c3", str(self.host)])

                    except Exception as e:
                        self._log_exception(self._log_tag, "Unable to execute ping command.")
                        self._set_error_state(SensorErrorState.ProcessingError, "Unable to execute ping command.")

            # Process is still running.
            else:

                # Check if process is not finished yet.
                if self._process.poll() is None:

                    # Check if process has timed out
                    utc_timestamp = int(time.time())
                    if (utc_timestamp - self._time_executed) > self.timeout:
                        self._log_error(self._log_tag, "Process has timed out.")

                        # terminate process
                        self._process.terminate()

                        # Give the process time to terminate.
                        try:
                            self._process.wait(5.0)

                        except subprocess.TimeoutExpired:
                            self._log_error(self._log_tag, "Could not terminate process. Killing it.")

                            self._process.kill()

                        self._set_error_state(SensorErrorState.TimeoutError, "Ping process timed out.")

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
                        self._add_sensor_alert(new_state,
                                               True,
                                               optional_data)

                    # Set process to none so it can be newly started in the next iteration.
                    self._process = None

            time.sleep(0.5)
