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
from .core import _PollingSensor
from ..globalData import SensorObjSensorAlert, SensorObjStateChange, SensorDataType
from typing import Optional


# class that controls one watchdog of a challenge
class PingSensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.NONE

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
        self._time_executed = None

        # the process itself
        self._process = None  # type: Optional[subprocess.Popen]

    def initialize(self) -> bool:
        self._time_executed = 0
        self.state = 1 - self.triggerState
        self.optionalData = {"host": self.host}  # TODO
        return True

    def _execute(self):

        while True:

            if self._exit_flag:
                return

            # Check if the interval in which the service should be checked is exceeded.
            if self._process is None:

                # check if the interval in which the service should be checked
                # is exceeded
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

                        sensor_alert = SensorObjSensorAlert()
                        sensor_alert.clientSensorId = self.id
                        sensor_alert.state = 1
                        sensor_alert.hasOptionalData = True
                        sensor_alert.optionalData = {"host": self.host,
                                                     "reason": "processerror",
                                                     "message": "Unable to execute process"}
                        sensor_alert.changeState = False
                        sensor_alert.hasLatestData = False
                        sensor_alert.dataType = self.sensorDataType
                        sensor_alert.sensorData = self.sensorData

                        self._add_event(sensor_alert)

            # Process is still running.
            else:

                # Check if process is not finished yet.
                if self._process.poll() is None:

                    # Check if process has timed out
                    utc_timestamp = int(time.time())
                    if (utc_timestamp - self._time_executed) > self.timeout:
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
                                logging.error("[%s] Could not terminate process for '%s'. Killing it."
                                              % (self._log_tag, self.description))

                                self._process.kill()
                                exit_code = self._process.poll()
                            except Exception as e:
                                pass

                        old_state = self.state
                        self.state = self.triggerState

                        # Process state change.
                        if old_state != self.state:

                            # Check if the sensor triggers a sensor alert => send sensor alert to server.
                            if self.triggerAlert:
                                sensor_alert = SensorObjSensorAlert()
                                sensor_alert.clientSensorId = self.id
                                sensor_alert.state = 1
                                sensor_alert.hasOptionalData = True
                                sensor_alert.optionalData = {"message": "Timeout",
                                                             "host": self.host,
                                                             "reason": "processtimeout",
                                                             "exitCode": exit_code}
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

                        # Set process to None so it can be newly started in the next iteration.
                        self._process = None

                # Process has finished.
                else:
                    old_state = self.state
                    optional_data = {"host": self.host}

                    # Check if the process has exited with code 0 = host reachable.
                    exit_code = self._process.poll()
                    if exit_code == 0:
                        self.state = 1 - self.triggerState
                        optional_data["reason"] = "reachable"

                    # Process did not exited correctly => host not reachable.
                    else:
                        self.state = self.triggerState
                        optional_data["reason"] = "notreachable"

                    optional_data["exitCode"] = exit_code

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
                                sensor_alert.optionalData = optional_data
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
                                sensor_alert.optionalData = optional_data
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
                    self._process = None

            time.sleep(0.5)
