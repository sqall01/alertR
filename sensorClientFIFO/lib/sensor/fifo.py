#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import time
import logging
import json
import threading
from .core import _PollingSensor
from ..globalData import SensorObjSensorAlert, SensorObjStateChange, SensorDataType
from typing import Optional


class SensorFIFO(_PollingSensor):
    """
    Class that represents one FIFO file as a sensor.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # used for logging
        self._log_tag = os.path.basename(__file__)

        self.fifoFile = None

        self.umask = None

        # Used to force a state change to be sent to the server.
        self._state_changes_lock = threading.Lock()
        self._state_changes = None

        # Used to force a sensor alert to be sent to the server.
        self._sensor_alerts_lock = threading.Lock()
        self._sensor_alerts = list()

        # Used for parallel data receiving and processing.
        self._data_queue_lock = threading.Lock()
        self._data_queue = list()
        self._data_event = threading.Event()
        self._data_event.clear()

        self._thread_read = None  # type: Optional[threading.Thread]

    def _checkDataType(self, dataType: int) -> int:
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

    def _checkState(self, state):
        if not isinstance(state, int):
            return False
        if state != 0 and state != 1:
            return False
        return True

    def _create_fifo_file(self):

        # Create FIFO file.
        while True:

            # Check if FIFO file exists => remove it if it does.
            if os.path.exists(self.fifoFile):
                try:
                    os.remove(self.fifoFile)

                except Exception as e:
                    logging.exception("[%s] Could not delete FIFO file of sensor with id '%d'."
                                      % (self._log_tag, self.id))
                    time.sleep(5)
                    continue

            # Create a new FIFO file.
            try:
                old_umask = os.umask(self.umask)
                os.mkfifo(self.fifoFile)
                os.umask(old_umask)

            except Exception as e:
                logging.exception("[%s] Could not create FIFO file of sensor with id '%d'."
                                  % (self._log_tag, self.id))
                time.sleep(5)
                continue
            break

    def _execute(self):
        """
        This function runs in a thread and processes data read by the FIFO reader thread.
        """

        # Start FIFO reading thread.
        self._thread_read = threading.Thread(target=self._thread_read_fifo)
        self._thread_read.daemon = True
        self._thread_read.start()

        while True:

            # If we still have data in the queue, wait a short time before starting a new processing round.
            # This is done to not lock up data queue for the fifo reading thread if it gets a lot of messages to read.
            if self._data_queue:
                time.sleep(0.5)

            # Wait until new data has to be processed if we do not have anything in the queue.
            else:
                self._data_event.wait(5.0)

            if self._exit_flag:
                return

            while self._data_queue:

                data = ""
                with self._data_queue_lock:
                    data = self._data_queue.pop(0)

                # Ignore empty data.
                if data.strip() == "":
                    continue

                logging.debug("[%s] Received data '%s' from FIFO file of sensor with id '%d'."
                              % (self._log_tag, data, self.id))

                # Parse received data.
                try:

                    message = json.loads(data)

                    # Parse message depending on type.
                    # Type: statechange
                    if str(message["message"]).upper() == "STATECHANGE":

                        # Check if state is valid.
                        tempInputState = message["payload"]["state"]
                        if not self._checkState(tempInputState):
                            logging.error("[%s] Received state from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if data type is valid.
                        tempDataType = message["payload"]["dataType"]
                        if not self._checkDataType(tempDataType):
                            logging.error("[%s] Received data type from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Set new data.
                        if self.sensorDataType == SensorDataType.NONE:
                            self.sensorData = None
                        elif self.sensorDataType == SensorDataType.INT:
                            self.sensorData = int(message["payload"]["data"])
                        elif self.sensorDataType == SensorDataType.FLOAT:
                            self.sensorData = float(message["payload"]["data"])

                        # Force state change sending if the data could be changed
                        # or the state has changed.
                        if self.sensorDataType != SensorDataType.NONE or self.state != tempInputState:

                            # Create state change object that is
                            # send to the server.
                            temp_state_change = SensorObjStateChange()
                            temp_state_change.clientSensorId = self.id
                            if tempInputState == self.triggerState:
                                temp_state_change.state = 1
                            else:
                                temp_state_change.state = 0
                            temp_state_change.dataType = tempDataType
                            temp_state_change.sensorData = self.sensorData
                            with self._state_changes_lock:
                                self._state_changes.append(temp_state_change)

                        # Set state.
                        self.state = tempInputState

                    # Type: sensoralert
                    elif str(message["message"]).upper() == "SENSORALERT":

                        # Check if state is valid.
                        tempInputState = message["payload"]["state"]
                        if not self._checkState(tempInputState):
                            logging.error("[%s] Received state from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if hasOptionalData field is valid.
                        tempHasOptionalData = message[
                            "payload"]["hasOptionalData"]
                        if not self._checkHasOptionalData(tempHasOptionalData):
                            logging.error("[%s] Received hasOptionalData field from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if data type is valid.
                        tempDataType = message["payload"]["dataType"]
                        if not self._checkDataType(tempDataType):
                            logging.error("[%s] Received data type from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        tempSensorData = None
                        if self.sensorDataType == SensorDataType.INT:
                            tempSensorData = int(message["payload"]["data"])
                        elif self.sensorDataType == SensorDataType.FLOAT:
                            tempSensorData = float(message["payload"]["data"])

                        # Check if hasLatestData field is valid.
                        tempHasLatestData = message[
                            "payload"]["hasLatestData"]
                        if not self._checkHasLatestData(tempHasLatestData):
                            logging.error("[%s] Received hasLatestData field from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if changeState field is valid.
                        tempChangeState = message[
                            "payload"]["changeState"]
                        if not self._checkChangeState(tempChangeState):
                            logging.error("[%s] Received changeState field from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if data should be transfered with the sensor alert
                        # => if it should parse it
                        tempOptionalData = None
                        if tempHasOptionalData:

                            tempOptionalData = message["payload"]["optionalData"]

                            # check if data is of type dict
                            if not isinstance(tempOptionalData, dict):
                                logging.warning("[%s] Received optional data from FIFO file of sensor with id '%d' "
                                                % (self._log_tag, self.id)
                                                + "invalid. Ignoring message.")
                                continue

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
                        temp_sensor_alert = SensorObjSensorAlert()
                        temp_sensor_alert.clientSensorId = self.id
                        if tempInputState == self.triggerState:
                            temp_sensor_alert.state = 1
                        else:
                            temp_sensor_alert.state = 0
                        temp_sensor_alert.hasOptionalData = tempHasOptionalData
                        temp_sensor_alert.optionalData = tempOptionalData
                        temp_sensor_alert.changeState = tempChangeState
                        temp_sensor_alert.hasLatestData = tempHasLatestData
                        temp_sensor_alert.dataType = tempDataType
                        temp_sensor_alert.sensorData = tempSensorData

                        with self._sensor_alerts_lock:
                            self._sensor_alerts.append(temp_sensor_alert)

                    # Type: invalid
                    else:
                        raise ValueError("Received invalid message type.")

                except Exception as e:
                    logging.exception("[%s] Could not parse received data from FIFO file of sensor with id '%d'."
                                      % (self._log_tag, self.id))
                    logging.error("[%s] Received data: %s" % (self._log_tag, data))
                    continue

            self._data_event.clear()

    def _thread_read_fifo(self):
        """
        This function runs in a thread and simply reads the data from the FIFO file
        and places them in a queue for processing.
        """
        self._create_fifo_file()

        while True:

            if self._exit_flag:
                return

            # Read FIFO for data.
            data = ""
            try:
                fifo = open(self.fifoFile, "r")
                data = fifo.read()
                fifo.close()

            except Exception as e:
                logging.exception("[%s] Could not read data from FIFO file of sensor with id '%d'."
                                  % (self._log_tag, self.id))

                # Create a new FIFO file.
                self._create_fifo_file()
                continue

            with self._data_queue_lock:
                for line in data.strip().split("\n"):
                    self._data_queue.append(line)

            # Wake up processing thread.
            self._data_event.set()

    def exit(self):
        super().exit()

        # Wake up processing thread to speed up exit.
        self._data_event.set()

    def initialize(self) -> bool:

        # TODO
        self.changeState = True
        self.hasLatestData = False
        self.state = 1 - self.triggerState

        # Set initial sensor data
        if self.sensorDataType == SensorDataType.INT:
            self.sensorData = 0
        elif self.sensorDataType == SensorDataType.FLOAT:
            self.sensorData = 0.0

        return True
