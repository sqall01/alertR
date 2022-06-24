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
from .protocoldata import _ProtocolDataSensor
from ..globalData.sensorObjects import SensorDataType, SensorDataInt, SensorDataFloat, SensorDataGPS, SensorDataNone, \
    SensorErrorState


class ExecuterSensor(_ProtocolDataSensor):
    """
    Class that represents one executed command as a sensor.
    """

    def __init__(self):
        super().__init__()

        # Set sensor to not hold any data.
        # NOTE: Can be changed if "parseOutput" is set to true in the
        # configuration file.
        self.sensorDataType = SensorDataType.NONE

        # used for logging
        self._log_tag = os.path.basename(__file__)

        # gives the time that the process has to execute
        self.timeout = None

        # gives the interval in seconds in which the process
        # should be checked
        self.intervalToCheck = None

        # the command to execute and the arguments to pass
        self.execute = list()

        # This flag indicates if we should only use the exit code to
        # determine the state of the sensor or if we should parse the output.
        self.parseOutput = None

        # Time when the process was executed.
        self._time_executed = 0

        # the process itself
        self._process = None  # type: Optional[subprocess.Popen]

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

                        self._process = subprocess.Popen(self.execute,
                                                         stdout=subprocess.PIPE,
                                                         stderr=subprocess.PIPE)

                    except Exception as e:
                        self._log_exception(self._log_tag, "Unable to execute process.")
                        self._set_error_state(SensorErrorState.ExecutionError, "Unable to execute process: %s" % str(e))

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

                        self._set_error_state(SensorErrorState.TimeoutError, "Process timed out.")

                        # Set process to None so it can be newly started in the next iteration.
                        self._process.stdout.close()
                        self._process.stderr.close()
                        self._process = None

                # Process has finished.
                else:

                    # Distinguish if we should parse the output or not.
                    if self.parseOutput:

                        # Parse output.
                        output, err = self._process.communicate()
                        output = output.decode("ascii")
                        err = err.decode("ascii")

                        self._log_debug(self._log_tag, "Received data from output of sensor script: %s" % output)
                        if not self._process_protocol_data(output):
                            self._log_error(self._log_tag, "Not able to parse output of sensor script.")
                            self._log_error(self._log_tag, "Stdout: %s" % output)
                            self._log_error(self._log_tag, "Stderr: %s" % err)

                            self._set_error_state(SensorErrorState.ProcessingError, "Illegal script output.")

                    else:
                        # Check if the process has exited with code 0 => everything works fine
                        exit_code = self._process.poll()
                        if exit_code == 0:
                            new_state = 1 - self.triggerState

                        # process did not exited correctly => something is wrong with the service
                        else:
                            output, err = self._process.communicate()
                            output = output.decode("ascii")
                            err = err.decode("ascii")
                            self._log_error(self._log_tag, "Exit code of sensor script: %d" % exit_code)
                            self._log_error(self._log_tag, "Stdout: %s" % output)
                            self._log_error(self._log_tag, "Stderr: %s" % err)

                            new_state = self.triggerState

                        # Process state change.
                        if new_state != self.state:

                            # Check if the current state is a sensor alert triggering state.
                            if new_state == self.triggerState:
                                self._add_sensor_alert(self.triggerState,
                                                       True,
                                                       {"exitCode": exit_code},
                                                       False,
                                                       self.data)

                            # Only possible situation left => sensor changed back from triggering state to normal state.
                            else:
                                self._add_sensor_alert(1 - self.triggerState,
                                                       True,
                                                       {"exitCode": exit_code},
                                                       False,
                                                       self.data)

                        # Even if the state/data has not changed, an error could occur in between which causes the
                        # sensor to have an error state. Clear it if we received a new data.
                        else:
                            self._clear_error_state()

                    # Set process to none so it can be newly started in the next iteration.
                    self._process.stdout.close()
                    self._process.stderr.close()
                    self._process = None

            time.sleep(0.5)

    def initialize(self) -> bool:
        self._time_executed = 0
        self.state = 1 - self.triggerState

        if self.sensorDataType == SensorDataType.NONE:
            self.data = SensorDataNone()

        elif self.sensorDataType == SensorDataType.INT:
            self.data = SensorDataInt(0, "")

        elif self.sensorDataType == SensorDataType.FLOAT:
            self.data = SensorDataFloat(0.0, "")

        elif self.sensorDataType == SensorDataType.GPS:
            self.data = SensorDataGPS(0.0, 0.0, 0)

        else:
            return False

        return True
