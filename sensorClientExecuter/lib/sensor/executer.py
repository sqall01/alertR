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
import json
from .core import _PollingSensor
from ..globalData import SensorObjSensorAlert, SensorObjStateChange, SensorDataType


# Class that controls one executed command.
class ExecuterSensor(_PollingSensor):

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

        # time when the process was executed
        self._time_execute = 0

        # the process itself
        self._process = None

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

            if self._process is None:

                # Check if the interval in which the service should be checked is exceeded.
                utc_timestamp = int(time.time())
                if (utc_timestamp - self._time_execute) > self.intervalToCheck:

                    logging.debug("[%s] Executing process for '%s'." % (self._log_tag, self.description))

                    try:
                        # Set time before executing process in order to not hammer process creation
                        # if the process execution throws an exception.
                        self._time_execute = utc_timestamp

                        self._process = subprocess.Popen(self.execute,
                                                         stdout=subprocess.PIPE,
                                                         stderr=subprocess.PIPE)

                    except Exception as e:
                        logging.exception("[%s] Unable to execute process for '%s'."
                                          % (self._log_tag, self.description))

                        sensor_alert = SensorObjSensorAlert()
                        sensor_alert.clientSensorId = self.id
                        sensor_alert.state = 1
                        sensor_alert.hasOptionalData = True
                        sensor_alert.optionalData = {"message": "Unable to execute process"}
                        sensor_alert.changeState = False
                        sensor_alert.hasLatestData = False
                        sensor_alert.dataType = self.sensorDataType

                        if self.sensorDataType == SensorDataType.NONE:
                            sensor_alert.sensorData = None
                        elif self.sensorDataType == SensorDataType.INT:
                            sensor_alert.sensorData = 0
                        elif self.sensorDataType == SensorDataType.FLOAT:
                            sensor_alert.sensorData = 0.0

                        self._add_event(sensor_alert)

            # Process is still running.
            else:

                # Check if process is not finished yet.
                if self._process.poll() is None:

                    # Check if process has timed out
                    utc_timestamp = int(time.time())
                    if (utc_timestamp - self._time_execute) > self.timeout:
                        logging.error("[%s] Process '%s' has timed out."
                                      % (self._log_tag, self.description))

                        # terminate process
                        self._process.terminate()

                        # give the process one second to terminate
                        time.sleep(1)

                        # check if the process has terminated
                        # => if not kill it
                        exit_code = self._process.poll()
                        if exit_code != -15:
                            try:
                                logging.error("[%s] Could not terminate '%s'. Killing it."
                                              % (self._log_tag, self.description))

                                self._process.kill()

                            except Exception as e:
                                pass

                        sensor_alert = SensorObjSensorAlert()
                        sensor_alert.clientSensorId = self.id
                        sensor_alert.state = 1
                        sensor_alert.hasOptionalData = True
                        sensor_alert.optionalData = {"message": "Timeout",
                                                     "exitCode": exit_code}
                        sensor_alert.changeState = False
                        sensor_alert.hasLatestData = False
                        sensor_alert.dataType = self.sensorDataType

                        if self.sensorDataType == SensorDataType.NONE:
                            sensor_alert.sensorData = None
                        elif self.sensorDataType == SensorDataType.INT:
                            sensor_alert.sensorData = 0
                        elif self.sensorDataType == SensorDataType.FLOAT:
                            sensor_alert.sensorData = 0.0

                        self._add_event(sensor_alert)

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

                            logging.error("[%s] Not able to parse output of sensor with id '%d'."
                                          % (self._log_tag, self.id))
                            logging.error("[%s] Sensor with id '%d' stdout: %s"
                                          % (self._log_tag, self.id, output))
                            logging.error("[%s] Sensor with id '%d' stderr: %s"
                                          % (self._log_tag, self.id, err))

                            sensor_alert = SensorObjSensorAlert()
                            sensor_alert.clientSensorId = self.id
                            sensor_alert.state = 1
                            sensor_alert.hasOptionalData = True
                            sensor_alert.optionalData = {"message": "Illegal output"}
                            sensor_alert.changeState = False
                            sensor_alert.hasLatestData = False
                            sensor_alert.dataType = self.sensorDataType

                            if self.sensorDataType == SensorDataType.NONE:
                                sensor_alert.sensorData = None
                            elif self.sensorDataType == SensorDataType.INT:
                                sensor_alert.sensorData = 0
                            elif self.sensorDataType == SensorDataType.FLOAT:
                                sensor_alert.sensorData = 0.0

                            self._add_event(sensor_alert)

                    else:
                        old_state = self.state

                        # Check if the process has exited with code 0 => everything works fine
                        exit_code = self._process.poll()
                        if exit_code == 0:
                            self.state = 1 - self.triggerState

                        # process did not exited correctly => something is wrong with the service
                        else:
                            output, err = self._process.communicate()
                            output = output.decode("ascii")
                            err = err.decode("ascii")
                            logging.error("[%s] Sensor with id '%d' stdout: %s"
                                          % (self._log_tag, self.id, output))
                            logging.error("[%s] Sensor with id '%d' stderr: %s"
                                          % (self._log_tag, self.id, err))

                            self.state = self.triggerState

                        # Process state change.
                        if old_state != self.state:

                            # Check if the current state is a sensor alert triggering state.
                            if self.state == self.triggerState:

                                # Check if the sensor triggers a sensor alert => send sensor alert to server.
                                if self.triggerAlert:
                                    sensor_alert = SensorObjSensorAlert()
                                    sensor_alert.clientSensorId = self.id
                                    sensor_alert.state = 1
                                    sensor_alert.hasOptionalData = True
                                    sensor_alert.optionalData = {"exitCode": exit_code}
                                    sensor_alert.changeState = True
                                    sensor_alert.hasLatestData = False
                                    sensor_alert.dataType = self.sensorDataType
                                    sensor_alert.sensorData = self.sensorData
                                    self._add_event(sensor_alert)

                                # If sensor does not trigger sensor alert => just send changed state to server.
                                else:
                                    state_change = SensorObjStateChange()
                                    state_change.clientSensorId = self.id
                                    state_change.state = 1
                                    state_change.dataType = self.sensorDataType
                                    state_change.sensorData = self.sensorData
                                    self._add_event(state_change)

                            # Only possible situation left => sensor changed back from triggering state to normal state.
                            else:

                                # Check if the sensor triggers a Sensor Alert when state is back to normal
                                # => send sensor alert to server
                                if self.triggerAlertNormal:
                                    sensor_alert = SensorObjSensorAlert()
                                    sensor_alert.clientSensorId = self.id
                                    sensor_alert.state = 0
                                    sensor_alert.hasOptionalData = True
                                    sensor_alert.optionalData = {"exitCode": exit_code}
                                    sensor_alert.changeState = True
                                    sensor_alert.hasLatestData = False
                                    sensor_alert.dataType = self.sensorDataType
                                    sensor_alert.sensorData = self.sensorData
                                    self._add_event(sensor_alert)

                                # If sensor does not trigger Sensor Alert when state is back to normal
                                # => just send changed state to server.
                                else:
                                    state_change = SensorObjStateChange()
                                    state_change.clientSensorId = self.id
                                    state_change.state = 0
                                    state_change.dataType = self.sensorDataType
                                    state_change.sensorData = self.sensorData
                                    self._add_event(state_change)

                    # Set process to none so it can be newly started in the next iteration.
                    self._process.stdout.close()
                    self._process.stderr.close()
                    self._process = None

            time.sleep(0.5)

    def _handle_output(self, data: str) -> bool:

        # Parse output data.
        try:

            logging.debug("[%s] Received output from sensor with id '%d': %s"
                          % (self._log_tag, self.id, data))

            message = json.loads(data)

            # Parse message depending on type.
            # Type: statechange
            if str(message["message"]).upper() == "STATECHANGE":

                # Check if state is valid.
                temp_input_state = message["payload"]["state"]
                if not self._check_state(temp_input_state):
                    logging.error("[%s] Received state from output of sensor with id '%d' invalid. Ignoring output."
                                  % (self._log_tag, self.id))
                    return False

                # Check if data type is valid.
                temp_data_type = message["payload"]["dataType"]
                if not self._check_data_type(temp_data_type):
                    logging.error("[%s] Received data type from output of sensor with id '%d' "
                                  % (self._log_tag, self.id)
                                  + "invalid. Ignoring output.")
                    return False

                # Get new data.
                temp_input_data = None
                if self.sensorDataType == SensorDataType.INT:
                    temp_input_data = int(message["payload"]["data"])
                elif self.sensorDataType == SensorDataType.FLOAT:
                    temp_input_data = float(message["payload"]["data"])

                # Create state change object that is send to the server if the data could be changed
                # or the state has changed.
                if self.sensorData != temp_input_data or self.state != temp_input_state:

                    state_change = SensorObjStateChange()
                    state_change.clientSensorId = self.id
                    if temp_input_state == self.triggerState:
                        state_change.state = 1
                    else:
                        state_change.state = 0
                    state_change.dataType = self.sensorDataType
                    state_change.sensorData = temp_input_data
                    self._add_event(state_change)

                self.state = temp_input_state
                self.sensorData = temp_input_data

            # Type: sensoralert
            elif str(message["message"]).upper() == "SENSORALERT":

                # Check if state is valid.
                temp_input_state = message["payload"]["state"]
                if not self._check_state(temp_input_state):
                    logging.error("[%s] Received state from output of sensor with id '%d' invalid. Ignoring output."
                                  % (self._log_tag, self.id))
                    return False

                # Check if hasOptionalData field is valid.
                temp_has_optional_data = message["payload"]["hasOptionalData"]
                if not self._check_has_optional_data(temp_has_optional_data):
                    logging.error("[%s] Received hasOptionalData field from output of sensor with id '%d' "
                                  % (self._log_tag, self.id)
                                  + "invalid. Ignoring output.")
                    return False

                # Check if data type is valid.
                temp_data_type = message["payload"]["dataType"]
                if not self._check_data_type(temp_data_type):
                    logging.error("[%s] Received data type from output of sensor with id '%d' "
                                  % (self._log_tag, self.id)
                                  + "invalid. Ignoring output.")
                    return False

                temp_input_data = None
                if self.sensorDataType == SensorDataType.INT:
                    temp_input_data = int(message["payload"]["data"])
                elif self.sensorDataType == SensorDataType.FLOAT:
                    temp_input_data = float(message["payload"]["data"])

                # Check if hasLatestData field is valid.
                temp_has_latest_data = message["payload"]["hasLatestData"]
                if not self._check_has_latest_data(temp_has_latest_data):
                    logging.error("[%s] Received hasLatestData field from output of sensor with id '%d' "
                                  % (self._log_tag, self.id)
                                  + "invalid. Ignoring output.")
                    return False

                # Check if changeState field is valid.
                temp_change_state = message["payload"]["changeState"]
                if not self._check_change_state(temp_change_state):
                    logging.error("[%s] Received changeState field from output of sensor with id '%d' "
                                  % (self._log_tag, self.id)
                                  + "invalid. Ignoring output.")
                    return False

                # Check if data should be transfered with the sensor alert
                # => if it should parse it
                temp_optional_data = None
                if temp_has_optional_data:

                    temp_optional_data = message["payload"]["optionalData"]

                    # check if data is of type dict
                    if not isinstance(temp_optional_data, dict):
                        logging.warning("[%s] Received optional data from output of sensor with id '%d' "
                                        % (self._log_tag, self.id)
                                        + "invalid. Ignoring output.")
                        return False

                # Set new state.
                if temp_change_state:
                    self.state = temp_input_state

                # Set new data.
                if temp_has_latest_data and self.sensorDataType != SensorDataType.NONE:
                    self.sensorData = temp_input_data

                sensor_alert = SensorObjSensorAlert()
                sensor_alert.clientSensorId = self.id
                if temp_input_state == self.triggerState:
                    sensor_alert.state = 1
                else:
                    sensor_alert.state = 0
                sensor_alert.hasOptionalData = temp_has_optional_data
                sensor_alert.optionalData = temp_optional_data
                sensor_alert.changeState = temp_change_state
                sensor_alert.hasLatestData = temp_has_latest_data
                sensor_alert.dataType = self.sensorDataType
                sensor_alert.sensorData = temp_input_data
                self._add_event(sensor_alert)

            # Type: invalid
            else:
                raise ValueError("Received invalid message type.")

        except Exception as e:
            logging.exception("[%s] Could not parse received data from output of sensor with id '%d'."
                              % (self._log_tag, self.id))
            return False

        return True

    def initialize(self):
        self._time_execute = 0
        self.state = 1 - self.triggerState

        if self.sensorDataType == SensorDataType.INT:
            self.sensorData = 0

        elif self.sensorDataType == SensorDataType.FLOAT:
            self.sensorData = 0.0

        return True
