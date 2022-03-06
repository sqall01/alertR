#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import select
import time
import threading
from typing import Optional
from .protocoldata import _ProtocolDataSensor
from ..globalData.sensorObjects import SensorDataType, SensorDataNone, SensorDataInt, SensorDataFloat, SensorDataGPS, \
    SensorErrorState


class FIFOSensor(_ProtocolDataSensor):
    """
    Class that represents one FIFO file as a sensor.
    """

    def __init__(self):
        super().__init__()

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

    def _create_fifo_file(self):

        # Create FIFO file.
        while True:

            # Check if FIFO file exists => remove it if it does.
            if os.path.exists(self.fifoFile):
                # noinspection PyBroadException,PyUnusedLocal
                try:
                    os.remove(self.fifoFile)

                except Exception as e:
                    self._log_exception(self._log_tag, "Could not delete FIFO file.")
                    time.sleep(self._fifo_retry_time)
                    continue

            # Create a new FIFO file.
            # noinspection PyBroadException,PyUnusedLocal
            try:
                old_umask = os.umask(self.umask)
                os.mkfifo(self.fifoFile)
                os.umask(old_umask)

            except Exception as e:
                self._log_exception(self._log_tag, "Could not create FIFO file.")
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

                # noinspection PyUnusedLocal
                data = ""
                with self._data_queue_lock:
                    data = self._data_queue.pop(0)

                # Ignore empty data.
                if data.strip() == "":
                    continue

                self._log_debug(self._log_tag, "Received data from FIFO file: %s" % data)
                if not self._process_protocol_data(data):
                    self._log_error(self._log_tag, "Not able to parse data from FIFO file.")
                    self._log_error(self._log_tag, "Data: %s" % data)

                    self._set_error_state(SensorErrorState.ProcessingError, "Received illegal data.")

    def _thread_read_fifo(self):
        """
        This function runs in a thread and simply reads the data from the FIFO file
        and places them in a queue for processing.
        """

        self._create_fifo_file()

        fifo = None
        while True:
            if self._exit_flag:
                return

            # Try to close FIFO file before re-opening it.
            if fifo:
                # noinspection PyBroadException,PyUnusedLocal
                try:
                    fifo.close()
                except Exception as e:
                    pass

            fifo = open(self.fifoFile, "r")

            while True:
                if self._exit_flag:
                    return

                # Read FIFO for data.
                # noinspection PyUnusedLocal
                data = ""
                try:
                    # Wait for fifo to be readable or has an exception.
                    select.select([fifo], [], [fifo])

                    data = fifo.read()
                    if not data:  # If no data is coming back, writer has closed FIFO and we have to create a new one.
                        break

                except Exception as e:
                    self._log_exception(self._log_tag, "Could not read data from FIFO file.")
                    self._set_error_state(SensorErrorState.ProcessingError,
                                          "Could not read data from FIFO file: %s" % str(e))
                    break

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

        if self.sensorDataType == SensorDataType.NONE:
            self.data = SensorDataNone()

        if self.sensorDataType == SensorDataType.INT:
            self.data = SensorDataInt(0, "")

        elif self.sensorDataType == SensorDataType.FLOAT:
            self.data = SensorDataFloat(0.0, "")

        elif self.sensorDataType == SensorDataType.GPS:
            self.data = SensorDataGPS(0.0, 0.0, 0)

        return True
