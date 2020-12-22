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
from ..localObjects import SensorAlert, StateChange, SensorDataType
from typing import Optional


# Class that controls one executed command.
class ExecuterSensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        # NOTE: Can be changed if "parseOutput" is set to true in the
        # configuration file.
        self.sensorDataType = SensorDataType.NONE

        # used for logging
        self.fileName = os.path.basename(__file__)

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
        self.timeExecute = None

        # the process itself
        self.process = None

        # Used to force a state change to be sent to the server.
        self.shouldForceSendState = False
        self.stateChange = None

        # Used to force a sensor alert to be sent to the server.
        self.shouldForceSendAlert = False
        self.sensorAlert = None

    def _checkDataType(self, dataType: int) -> bool:
        if not isinstance(dataType, int):
            return False
        if dataType != self.sensorDataType:
            return False
        return True

    def _checkChangeState(self, changeState: bool) -> bool:
        if not isinstance(changeState, bool):
            return False
        return True

    def _checkHasLatestData(self, hasLatestData: bool) -> bool:
        if not isinstance(hasLatestData, bool):
            return False
        return True

    def _checkHasOptionalData(self, hasOptionalData: bool) -> bool:
        if not isinstance(hasOptionalData, bool):
            return False
        return True

    def _checkState(self, state) -> bool:
        if not isinstance(state, int):
            return False
        if state != 0 and state != 1:
            return False
        return True

    def _parseOutput(self, data: str) -> bool:

        # Parse output data
        try:

            logging.debug("[%s] Received output from sensor with id '%d': %s"
                          % (self.fileName, self.id, data))

            message = json.loads(data)

            # Parse message depending on type.
            # Type: statechange
            if str(message["message"]).upper() == "STATECHANGE":

                # Check if state is valid.
                tempInputState = message["payload"]["state"]
                if not self._checkState(tempInputState):
                    logging.error("[%s]: Received state "
                                  % self.fileName
                                  + "from output of sensor with id '%d' "
                                  % self.id
                                  + "invalid. Ignoring output.")
                    return False

                # Check if data type is valid.
                tempDataType = message["payload"]["dataType"]
                if not self._checkDataType(tempDataType):
                    logging.error("[%s]: Received data type "
                                  % self.fileName
                                  + "from output of sensor with id '%d' "
                                  % self.id
                                  + "invalid. Ignoring output.")
                    return False

                # Set new data.
                if self.sensorDataType == SensorDataType.NONE:
                    self.sensorData = None
                elif self.sensorDataType == SensorDataType.INT:
                    self.sensorData = int(message["payload"]["data"])
                elif self.sensorDataType == SensorDataType.FLOAT:
                    self.sensorData = float(message["payload"]["data"])

                # Force state change sending if the data could be changed
                # or the state has changed.
                if (self.sensorDataType != SensorDataType.NONE
                    or self.state != tempInputState):

                    # Create state change object that is
                    # send to the server.
                    self.stateChange = StateChange()
                    self.stateChange.clientSensorId = self.id
                    if tempInputState == self.triggerState:
                        self.stateChange.state = 1
                    else:
                        self.stateChange.state = 0
                    self.stateChange.dataType = tempDataType
                    self.stateChange.sensorData = self.sensorData
                    self.shouldForceSendState = True

                # Set state.
                self.state = tempInputState

            # Type: sensoralert
            elif str(message["message"]).upper() == "SENSORALERT":

                # Check if state is valid.
                tempInputState = message["payload"]["state"]
                if not self._checkState(tempInputState):
                    logging.error("[%s]: Received state "
                                  % self.fileName
                                  + "from output of sensor with id '%d' "
                                  % self.id
                                  + "invalid. Ignoring output.")
                    return False

                # Check if hasOptionalData field is valid.
                tempHasOptionalData = message["payload"]["hasOptionalData"]
                if not self._checkHasOptionalData(tempHasOptionalData):
                    logging.error("[%s]: Received hasOptionalData field "
                                  % self.fileName
                                  + "from output of sensor with id '%d' "
                                  % self.id
                                  + "invalid. Ignoring output.")
                    return False

                # Check if data type is valid.
                tempDataType = message["payload"]["dataType"]
                if not self._checkDataType(tempDataType):
                    logging.error("[%s]: Received data type "
                                  % self.fileName
                                  + "from output of sensor with id '%d' "
                                  % self.id
                                  + "invalid. Ignoring output.")
                    return False

                tempSensorData = None
                if self.sensorDataType == SensorDataType.INT:
                    tempSensorData = int(message["payload"]["data"])
                elif self.sensorDataType == SensorDataType.FLOAT:
                    tempSensorData = float(message["payload"]["data"])

                # Check if hasLatestData field is valid.
                tempHasLatestData = message["payload"]["hasLatestData"]
                if not self._checkHasLatestData(tempHasLatestData):
                    logging.error("[%s]: Received hasLatestData field "
                                  % self.fileName
                                  + "from output of sensor with id '%d' "
                                  % self.id
                                  + "invalid. Ignoring output.")
                    return False

                # Check if changeState field is valid.
                tempChangeState = message["payload"]["changeState"]
                if not self._checkChangeState(tempChangeState):
                    logging.error("[%s]: Received changeState field "
                                  % self.fileName
                                  + "from output of sensor with id '%d' "
                                  % self.id
                                  + "invalid. Ignoring output.")
                    return False

                # Check if data should be transfered with the sensor alert
                # => if it should parse it
                tempOptionalData = None
                if tempHasOptionalData:

                    tempOptionalData = message["payload"]["optionalData"]

                    # check if data is of type dict
                    if not isinstance(tempOptionalData, dict):
                        logging.warning("[%s]: Received optional data "
                                        % self.fileName
                                        + "from output of sensor with id '%d' "
                                        % self.id
                                        + "invalid. Ignoring output.")
                        return False

                # Set optional data.
                self.hasOptionalData = tempHasOptionalData
                self.optionalData = tempOptionalData

                # Set new data.
                if tempHasLatestData:
                    self.sensorData = tempSensorData

                # Set state.
                if tempChangeState:
                    self.state = tempInputState

                # Create sensor alert object that is send to the server.
                self.sensorAlert = SensorAlert()
                self.sensorAlert.clientSensorId = self.id
                if tempInputState == self.triggerState:
                    self.sensorAlert.state = 1
                else:
                    self.sensorAlert.state = 0
                self.sensorAlert.hasOptionalData = tempHasOptionalData
                self.sensorAlert.optionalData = tempOptionalData
                self.sensorAlert.changeState = tempChangeState
                self.sensorAlert.hasLatestData = tempHasLatestData
                self.sensorAlert.dataType = tempDataType
                self.sensorAlert.sensorData = tempSensorData
                self.shouldForceSendAlert = True

            # Type: invalid
            else:
                raise ValueError("Received invalid message type.")

        except Exception as e:
            logging.exception("[%s]: Could not parse received data from "
                              % self.fileName
                              + "output of sensor with id '%d'."
                              % self.id)
            return False

        return True

    def initializeSensor(self):
        self.changeState = True
        self.hasLatestData = False
        self.timeExecute = 0.0
        self.state = 1 - self.triggerState

        # If the sensor parses the output it handles the state changes itself.
        if self.parseOutput:
            self.handlesStateMsgs = True

        if self.sensorDataType == SensorDataType.INT:
            self.sensorData = 0
        elif self.sensorDataType == SensorDataType.FLOAT:
            self.sensorData = 0.0

        return True

    def getState(self) -> int:
        return self.state

    def updateState(self):

        self.hasOptionalData = False
        self.optionalData = None

        # check if a process is executed
        # => if none no process is executed
        if self.process is None:

            # check if the interval in which the service should be checked
            # is exceeded
            utcTimestamp = int(time.time())
            if (utcTimestamp - self.timeExecute) > self.intervalToCheck:

                logging.debug("[%s]: Executing process '%s'."
                              % (self.fileName, self.description))

                self.process = subprocess.Popen(self.execute,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

                self.timeExecute = utcTimestamp

        # => process is still running
        else:

            # check if process is not finished yet
            if self.process.poll() is None:

                # check if process has timed out
                utcTimestamp = int(time.time())
                if (utcTimestamp - self.timeExecute) > self.timeout:

                    self.state = self.triggerState
                    self.hasOptionalData = True
                    self.optionalData = {"message": "Timeout"}

                    logging.error("[%s]: Process "
                                  % self.fileName
                                  + "'%s' has timed out."
                                  % self.description)

                    # terminate process
                    self.process.terminate()

                    # give the process one second to terminate
                    time.sleep(1)

                    # check if the process has terminated
                    # => if not kill it
                    exitCode = self.process.poll()
                    if exitCode != -15:
                        try:
                            logging.error("[%s]: Could not "
                                          % self.fileName
                                          + "terminate '%s'. Killing it."
                                          % self.description)

                            self.process.kill()
                        except:
                            pass
                    self.optionalData["exitCode"] = exitCode

                    # set process to none so it can be newly started
                    # in the next state update
                    self.process = None

            # process has finished
            else:

                # Distinguish if we should parse the output or not.
                if self.parseOutput:

                    # Parse output.
                    output, err = self.process.communicate()
                    output = output.decode("ascii")
                    err = err.decode("ascii")
                    if not self._parseOutput(output):

                        logging.error("[%s] Not able to parse output "
                                      % self.fileName
                                      + "of sensor with id '%d'."
                                      % self.id)
                        logging.error("[%s] Sensor with id '%d' stdout: %s"
                                      % (self.fileName, self.id, output))
                        logging.error("[%s] Sensor with id '%d' stderr: %s"
                                      % (self.fileName, self.id, err))

                        self.state = self.triggerState

                        # Generate sensor alert object.
                        self.sensorAlert = SensorAlert()
                        self.sensorAlert.clientSensorId = self.id
                        self.sensorAlert.state = 1
                        self.sensorAlert.hasOptionalData = True
                        self.sensorAlert.optionalData = {"message": "Illegal output"}
                        self.sensorAlert.changeState = True
                        self.sensorAlert.hasLatestData = False
                        self.sensorAlert.dataType = self.sensorDataType
                        if self.sensorDataType == SensorDataType.NONE:
                            self.sensorAlert.sensorData = None
                        elif self.sensorDataType == SensorDataType.INT:
                            self.sensorAlert.sensorData = 0
                        elif self.sensorDataType == SensorDataType.FLOAT:
                            self.sensorAlert.sensorData = 0.0
                        self.shouldForceSendAlert = True

                else:
                    self.hasOptionalData = True
                    self.optionalData = dict()

                    # check if the process has exited with code 0
                    # => everything works fine
                    exitCode = self.process.poll()
                    if exitCode == 0:
                        self.state = 1 - self.triggerState
                    # process did not exited correctly
                    # => something is wrong with the service
                    else:
                        output, err = self.process.communicate()
                        output = output.decode("ascii")
                        err = err.decode("ascii")
                        logging.error("[%s] Sensor with id '%d' stdout: %s"
                                      % (self.fileName, self.id, output))
                        logging.error("[%s] Sensor with id '%d' stderr: %s"
                                      % (self.fileName, self.id, err))

                        self.state = self.triggerState
                    self.optionalData["exitCode"] = exitCode

                # set process to none so it can be newly started
                # in the next state update
                self.process = None

    def forceSendAlert(self) -> Optional[SensorAlert]:
        returnValue = None
        if self.shouldForceSendAlert:
            returnValue = self.sensorAlert
            self.sensorAlert = None
            self.shouldForceSendAlert = False
        return returnValue

    def forceSendState(self) -> Optional[StateChange]:
        returnValue = None
        if self.shouldForceSendState:
            returnValue = self.stateChange
            self.stateChange = None
            self.shouldForceSendState = False
        return returnValue
