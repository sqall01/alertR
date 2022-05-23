#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import os
from typing import List, Tuple, Optional
from ..server import AsynchronousSender
from ..globalData.globalData import GlobalData
from ..globalData.sensorObjects import SensorErrorState
from ..internalSensors.sensorErrorState import SensorErrorStateSensor


class ErrorStateExecuter(threading.Thread):
    """
    This class is handles sensor error state processing
    """

    def __init__(self,
                 global_data: GlobalData):
        threading.Thread.__init__(self)

        # get global configured data
        self._global_data = global_data
        self._logger = self._global_data.logger
        self._storage = self._global_data.storage
        self._server_sessions = self._global_data.serverSessions

        # file nme of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        # Create an event that is used to wake this thread up and react on options.
        self._error_state_event = threading.Event()
        self._error_state_event.clear()

        self._exit_flag = False

        self._error_state_queue = list()  # type: List[Tuple[int, int, SensorErrorState]]
        self._error_state_queue_lock = threading.Lock()

        # Set of sensor ids that are currently in an error state.
        self._sensor_ids_in_error = set()

        # Get instance of the internal sensor error state sensor (if exists).
        self._internal_sensor = None  # type: Optional[SensorErrorStateSensor]
        for internal_sensor in self._global_data.internalSensors:
            if isinstance(internal_sensor, SensorErrorStateSensor):
                self._internal_sensor = internal_sensor

    def _process_error_state_changes(self):
        """
        Internal function that processes error state events in queue. If queue is empty, nothing happens.

        :return:
        """

        while self._error_state_queue:
            with self._error_state_queue_lock:
                node_id, client_sensor_id, error_state = self._error_state_queue.pop(0)

            self._logger.info("[%s]: Processing error state for node id %d with client sensor id %d: %s"
                              % (self._log_tag, node_id, client_sensor_id, str(error_state)))

            # Update error state in database.
            if not self._storage.update_sensor_error_state(node_id,
                                                           client_sensor_id,
                                                           error_state,
                                                           self._logger):
                self._logger.error("[%s]: Unable to update error state for node id %d with client sensor id %d."
                                   % (self._log_tag, node_id, client_sensor_id))
                continue

            sensor_id = self._storage.getSensorId(node_id, client_sensor_id, self._logger)
            if sensor_id is None:
                self._logger.error("[%s]: Sensor for node id %d with client sensor id %d does not exist."
                                   % (self._log_tag, node_id, client_sensor_id))
                return

            # Update local set of sensors in error state.
            if error_state.state == SensorErrorState.OK:
                self._sensor_ids_in_error.discard(sensor_id)
            else:
                self._sensor_ids_in_error.add(sensor_id)

            self._send_sensor_error_state_change(node_id,
                                                 client_sensor_id,
                                                 error_state)

            self._update_sensor_error_state_sensor(node_id,
                                                   client_sensor_id,
                                                   error_state)

    def _process_sensor_error_states(self):
        """
        Internal function that handles missed sensor error state events
        to recover the correct state in the system correct.

        :return:
        """
        curr_sensor_ids = set(self._storage.get_sensor_ids_in_error_state(self._logger))

        missed_events = self._sensor_ids_in_error ^ curr_sensor_ids  # missed ok events and error events

        for sensor_id in missed_events:
            error_state = self._storage.get_sensor_error_state(sensor_id, self._logger)

            if error_state is None:
                self._logger.error("[%s]: Unable to get error state for sensor id %d."
                                   % (self._log_tag, sensor_id))
                continue

            self._send_sensor_error_state_change_by_sensor_id(sensor_id, error_state)

            self._update_sensor_error_state_sensor_by_sensor_id(sensor_id, error_state)

        self._sensor_ids_in_error = curr_sensor_ids

    def _send_sensor_error_state_change(self,
                                        node_id: int,
                                        client_sensor_id: int,
                                        error_state: SensorErrorState):

        sensor_id = self._storage.getSensorId(node_id, client_sensor_id, self._logger)
        if sensor_id is None:
            self._logger.error("[%s]: Sensor for node id %d with client sensor id %d does not exist."
                               % (self._log_tag, node_id, client_sensor_id))
            return

        self._send_sensor_error_state_change_by_sensor_id(sensor_id, error_state)

    def _send_sensor_error_state_change_by_sensor_id(self,
                                                     sensor_id: int,
                                                     error_state: SensorErrorState):
        for server_session in self._server_sessions:
            # Ignore sessions which do not exist yet and that are not managers.
            if server_session.clientComm is None:
                continue
            if server_session.clientComm.nodeType != "manager":
                continue
            if not server_session.clientComm.clientInitialized:
                continue

            # Sending sensor error state change to manager client via a thread to not block this one
            sender = AsynchronousSender(self._global_data, server_session.clientComm)
            # set thread to daemon
            # => threads terminates when main thread terminates
            sender.daemon = True
            sender.send_sensor_error_state_change = True
            sender.sensor_id = sensor_id
            sender.error_state = error_state
            self._logger.debug("[%s]: Sending error state change for sensor id %d "
                               % (self._log_tag, sensor_id)
                               + "to manager client (%s:%d)."
                               % (server_session.clientComm.clientAddress, server_session.clientComm.clientPort))
            sender.start()

    def _update_sensor_error_state_sensor(self,
                                          node_id: int,
                                          client_sensor_id: int,
                                          error_state: SensorErrorState):
        """
        Internal function that triggers the internal sensor for sensor error states.
        :param node_id:
        :param client_sensor_id:
        :param error_state:
        """
        if self._internal_sensor is not None:
            sensor_id = self._storage.getSensorId(node_id, client_sensor_id, self._logger)
            if sensor_id is None:
                self._logger.error("[%s]: Sensor for node id %d with client sensor id %d does not exist."
                                   % (self._log_tag, node_id, client_sensor_id))
                return

            node = self._storage.getNodeById(node_id, self._logger)
            if node is None:
                self._logger.error("[%s]: Node id %d does not exist."
                                   % (self._log_tag, node_id))
                return

            self._internal_sensor.process_error_state(node.username, client_sensor_id, sensor_id, error_state)

    def _update_sensor_error_state_sensor_by_sensor_id(self,
                                                       sensor_id: int,
                                                       error_state: SensorErrorState):
        """
        Internal function that triggers the internal sensor for sensor error states.
        :param sensor_id:
        :param error_state:
        """
        if self._internal_sensor is not None:
            sensor = self._storage.getSensorById(sensor_id, self._logger)
            if sensor is None:
                self._logger.error("[%s]: Sensor id %d does not exist."
                                   % (self._log_tag, sensor_id))
                return

            node = self._storage.getNodeById(sensor.nodeId, self._logger)
            if node is None:
                self._logger.error("[%s]: Node id %d does not exist."
                                   % (self._log_tag, sensor.nodeId))
                return

            self._internal_sensor.process_error_state(node.username, sensor.clientSensorId, sensor_id, error_state)

    def add_error_state(self,
                        node_id: int,
                        client_sensor_id: int,
                        error_state: SensorErrorState):
        """
        Adds received error state change for processing.

        :param node_id:
        :param client_sensor_id:
        :param error_state:
        """

        with self._error_state_queue_lock:
            self._error_state_queue.append((node_id, client_sensor_id, error_state))

        self._error_state_event.set()

    def exit(self):
        """
        sets the exit flag to shut down the thread
        """
        self._exit_flag = True
        self._error_state_event.set()

    def run(self):
        """
        This function starts the endless loop of the error state executer thread.

        This object has to handle two main events:

        1) A sensor is connected to the server and sends an error state change event which has to be handled.
        2) The server could miss an error state change event (e.g., sensor is in an error state and sensor client was
        restarted and hence no error state change was sent, sensor client lost connection to server and resolves error
        state change and message never got through to the server) and thus has to recover the
        correct state for the system.
        """

        # Create initial set of sensor ids that are currently in an error state.
        self._sensor_ids_in_error = set(self._storage.get_sensor_ids_in_error_state(self._logger))

        while True:
            # Wait until a new object has to be processed if we do not have anything in the queue.
            # We do not need a timeout in the wait event since every event that could change the sensor error state
            # sets the event to start the processing.
            if not self._error_state_queue:
                self._error_state_event.wait()

            if self._exit_flag:
                return

            # Process error state change events in queue. If no event is in queue, function does nothing.
            self._process_error_state_changes()

            # Process sensor error states to make sure that the system has the correct state and we did not
            # miss any sensor error state events.
            self._process_sensor_error_states()

            self._error_state_event.clear()

    def start_processing_round(self):
        """
        Wakes up the processing thread to run a processing round (and fix possible wrong error states in the system
        due to missed error state changed messages).
        """
        self._error_state_event.set()
