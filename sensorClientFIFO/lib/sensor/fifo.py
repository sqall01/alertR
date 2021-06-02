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
from typing import Optional
from .core import _PollingSensor
from ..globalData import SensorDataType


class FIFOSensor(_PollingSensor):
    """
    Class that represents one FIFO file as a sensor.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # used for logging
        self._log_tag = os.path.basename(__file__)

        self.fifoFile = None

        self.umask = None

        # Used for parallel data receiving and processing.
        self._data_queue_lock = threading.Lock()
        self._data_queue = list()
        self._data_event = threading.Event()
        self._data_event.clear()

        self._thread_read = None  # type: Optional[threading.Thread]

        # Time to wait before retrying to create a new FIFO file on failure.
        self._fifo_retry_time = 5.0

    def _check_data_type(self, data_type: int) -> int:
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
                    time.sleep(self._fifo_retry_time)
                    continue

            # Create a new FIFO file.
            try:
                old_umask = os.umask(self.umask)
                os.mkfifo(self.fifoFile)
                os.umask(old_umask)

            except Exception as e:
                logging.exception("[%s] Could not create FIFO file of sensor with id '%d'."
                                  % (self._log_tag, self.id))
                time.sleep(self._fifo_retry_time)
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
                self._data_event.wait()

            if self._exit_flag:
                return

            self._data_event.clear()

            while self._data_queue:

                data = ""
                with self._data_queue_lock:
                    data = self._data_queue.pop(0)

                # Ignore empty data.
                if data.strip() == "":
                    continue

                logging.debug("[%s] Received data from FIFO file of sensor with id '%d': %s"
                              % (self._log_tag, self.id, data))

                # Parse received data.
                try:

                    message = json.loads(data)

                    # Parse message depending on type.
                    # Type: statechange
                    if str(message["message"]).upper() == "STATECHANGE":

                        # Check if state is valid.
                        temp_input_state = message["payload"]["state"]
                        if not self._check_state(temp_input_state):
                            logging.error("[%s] Received state from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if data type is valid.
                        temp_data_type = message["payload"]["dataType"]
                        if not self._check_data_type(temp_data_type):
                            logging.error("[%s] Received data type from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Get new data.
                        temp_input_data = None
                        if self.sensorDataType == SensorDataType.INT:
                            temp_input_data = int(message["payload"]["data"])
                        elif self.sensorDataType == SensorDataType.FLOAT:
                            temp_input_data = float(message["payload"]["data"])

                        # Create state change object that is send to the server if the data could be changed
                        # or the state has changed.
                        if self.sensorData != temp_input_data or self.state != temp_input_state:
                            self._add_state_change(temp_input_state,
                                                   temp_input_data)

                        self.state = temp_input_state
                        self.sensorData = temp_input_data

                    # Type: sensoralert
                    elif str(message["message"]).upper() == "SENSORALERT":

                        # Check if state is valid.
                        temp_input_state = message["payload"]["state"]
                        if not self._check_state(temp_input_state):
                            logging.error("[%s] Received state from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if hasOptionalData field is valid.
                        temp_has_optional_data = message[
                            "payload"]["hasOptionalData"]
                        if not self._check_has_optional_data(temp_has_optional_data):
                            logging.error("[%s] Received hasOptionalData field from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if data type is valid.
                        temp_data_type = message["payload"]["dataType"]
                        if not self._check_data_type(temp_data_type):
                            logging.error("[%s] Received data type from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        temp_input_data = None
                        if self.sensorDataType == SensorDataType.INT:
                            temp_input_data = int(message["payload"]["data"])
                        elif self.sensorDataType == SensorDataType.FLOAT:
                            temp_input_data = float(message["payload"]["data"])

                        # Check if hasLatestData field is valid.
                        temp_has_latest_data = message["payload"]["hasLatestData"]
                        if not self._check_has_latest_data(temp_has_latest_data):
                            logging.error("[%s] Received hasLatestData field from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if changeState field is valid.
                        temp_change_state = message["payload"]["changeState"]
                        if not self._check_change_state(temp_change_state):
                            logging.error("[%s] Received changeState field from FIFO file of sensor with id '%d' "
                                          % (self._log_tag, self.id)
                                          + "invalid. Ignoring message.")
                            continue

                        # Check if data should be transfered with the sensor alert
                        # => if it should parse it
                        temp_optional_data = None
                        if temp_has_optional_data:

                            temp_optional_data = message["payload"]["optionalData"]

                            # check if data is of type dict
                            if not isinstance(temp_optional_data, dict):
                                logging.warning("[%s] Received optional data from FIFO file of sensor with id '%d' "
                                                % (self._log_tag, self.id)
                                                + "invalid. Ignoring message.")
                                continue

                        # Set new state.
                        if temp_change_state:
                            self.state = temp_input_state

                        # Set new data.
                        if temp_has_latest_data and self.sensorDataType != SensorDataType.NONE:
                            self.sensorData = temp_input_data

                        self._add_sensor_alert(temp_input_state,
                                               temp_change_state,
                                               temp_optional_data,
                                               temp_has_latest_data,
                                               temp_input_data)

                    # Type: invalid
                    else:
                        raise ValueError("Received invalid message type.")

                except Exception as e:
                    logging.exception("[%s] Could not parse received data from FIFO file of sensor with id '%d'."
                                      % (self._log_tag, self.id))
                    logging.error("[%s] Received data: %s" % (self._log_tag, data))
                    continue

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

        # Wake up processing thread to exit.
        self._data_event.set()

    def initialize(self) -> bool:
        self.state = 1 - self.triggerState

        if self.sensorDataType == SensorDataType.INT:
            self.sensorData = 0

        elif self.sensorDataType == SensorDataType.FLOAT:
            self.sensorData = 0.0

        return True
