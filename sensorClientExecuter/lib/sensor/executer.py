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
import json
from typing import Optional
from .core import _PollingSensor
from ..globalData import SensorDataType
from ..globalData.sensorObjects import SensorDataInt, SensorDataFloat, SensorDataGPS, SensorDataNone


class ExecuterSensor(_PollingSensor):
    """
    Class that represents one executed command as a sensor.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

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

    def _check_data_type(self, data_type: int) -> bool:
        if not isinstance(data_type, int):
            return False
        if data_type != self.sensorDataType:
            return False
        return True

    def _check_change_state(self, change_state: bool) -> bool:
        if not isinstance(change_state, bool):
            return False
        return True

    def _check_has_latest_data(self, has_latest_data: bool) -> bool:
        if not isinstance(has_latest_data, bool):
            return False
        return True

    def _check_has_optional_data(self, has_optional_data: bool) -> bool:
        if not isinstance(has_optional_data, bool):
            return False
        return True

    def _check_state(self, state) -> bool:
        if not isinstance(state, int):
            return False
        if state != 0 and state != 1:
            return False
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

                        self._process = subprocess.Popen(self.execute,
                                                         stdout=subprocess.PIPE,
                                                         stderr=subprocess.PIPE)

                    except Exception as e:
                        self._log_exception(self._log_tag, "Unable to execute process.")

                        self._add_sensor_alert(self.triggerState,
                                               False,
                                               {"message": "Unable to execute process"},
                                               False,
                                               self.data)

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

                        exit_code = self._process.poll()

                        optional_data = {"message": "Timeout",
                                         "exitCode": exit_code}
                        self._add_sensor_alert(self.triggerState,
                                               False,
                                               optional_data,
                                               False,
                                               self.data)

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
                        if not self._handle_output(output):

                            self._log_error(self._log_tag, "Not able to parse output of sensor script.")
                            self._log_error(self._log_tag, "Stdout: %s" % output)
                            self._log_error(self._log_tag, "Stderr: %s" % err)

                            self._add_sensor_alert(self.triggerState,
                                                   False,
                                                   {"message": "Illegal output"},
                                                   False,
                                                   self.data)

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

                    # Set process to none so it can be newly started in the next iteration.
                    self._process.stdout.close()
                    self._process.stderr.close()
                    self._process = None

            time.sleep(0.5)

    def _handle_output(self, data: str) -> bool:

        # Parse output data.
        try:

            self._log_debug(self._log_tag, "Received data from output of sensor script: %s" % data)

            message = json.loads(data)

            # Parse message depending on type.
            # Type: statechange
            if str(message["message"]).upper() == "STATECHANGE":

                # Check if state is valid.
                temp_input_state = message["payload"]["state"]
                if not self._check_state(temp_input_state):
                    self._log_error(self._log_tag,
                                    "Received state from output of sensor script invalid. Ignoring output.")
                    return False

                # Check if data type is valid.
                temp_data_type = message["payload"]["dataType"]
                if not self._check_data_type(temp_data_type):
                    self._log_error(self._log_tag,
                                    "Received data type from output of sensor script invalid. Ignoring output.")
                    return False

                # Get new data.
                sensor_data_class = SensorDataType.get_sensor_data_class(temp_data_type)
                if not sensor_data_class.verify_dict(message["payload"]["data"]):
                    self._log_error(self._log_tag,
                                    "Received data from output of sensor script invalid. Ignoring output.")
                    return False
                temp_input_data = sensor_data_class.copy_from_dict(message["payload"]["data"])

                # Create state change object that is send to the server if the data could be changed
                # or the state has changed.
                if self.data != temp_input_data or self.state != temp_input_state:
                    self._add_state_change(temp_input_state,
                                           temp_input_data)

            # Type: sensoralert
            elif str(message["message"]).upper() == "SENSORALERT":

                # Check if state is valid.
                temp_input_state = message["payload"]["state"]
                if not self._check_state(temp_input_state):
                    self._log_error(self._log_tag,
                                    "Received state from output of sensor script invalid. Ignoring output.")
                    return False

                # Check if hasOptionalData field is valid.
                temp_has_optional_data = message["payload"]["hasOptionalData"]
                if not self._check_has_optional_data(temp_has_optional_data):
                    self._log_error(self._log_tag,
                                    "Received hasOptionalData field from output of sensor script invalid. "
                                    + "Ignoring output.")
                    return False

                # Check if data type is valid.
                temp_data_type = message["payload"]["dataType"]
                if not self._check_data_type(temp_data_type):
                    self._log_error(self._log_tag,
                                    "Received data type from output of sensor script invalid. Ignoring output.")
                    return False

                # Get new data.
                sensor_data_class = SensorDataType.get_sensor_data_class(temp_data_type)
                if not sensor_data_class.verify_dict(message["payload"]["data"]):
                    self._log_error(self._log_tag,
                                    "Received data from output of sensor script invalid. Ignoring output.")
                    return False
                temp_input_data = sensor_data_class.copy_from_dict(message["payload"]["data"])

                # Check if hasLatestData field is valid.
                temp_has_latest_data = message["payload"]["hasLatestData"]
                if not self._check_has_latest_data(temp_has_latest_data):
                    self._log_error(self._log_tag,
                                    "Received hasLatestData field from output of sensor script invalid. "
                                    + "Ignoring output.")
                    return False

                # Check if changeState field is valid.
                temp_change_state = message["payload"]["changeState"]
                if not self._check_change_state(temp_change_state):
                    self._log_error(self._log_tag,
                                    "Received changeState field from output of sensor script invalid. Ignoring output.")
                    return False

                # Check if data should be transfered with the sensor alert
                # => if it should parse it
                temp_optional_data = None
                if temp_has_optional_data:

                    temp_optional_data = message["payload"]["optionalData"]

                    # check if data is of type dict
                    if not isinstance(temp_optional_data, dict):
                        self._log_error(self._log_tag,
                                        "Received optional data from output of sensor script invalid. Ignoring output.")
                        return False

                self._add_sensor_alert(temp_input_state,
                                       temp_change_state,
                                       temp_optional_data,
                                       temp_has_latest_data,
                                       temp_input_data)

            # Type: invalid
            else:
                raise ValueError("Received invalid message type.")

        except Exception as e:
            self._log_exception(self._log_tag, "Could not parse received data from output of sensor script.")
            return False

        return True

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
