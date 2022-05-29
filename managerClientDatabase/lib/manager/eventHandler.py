#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import logging
import time
import threading
from typing import List, Any
from .core import BaseManagerEventHandler
from ..globalData.globalData import GlobalData
from ..globalData.managerObjects import ManagerObjOption, ManagerObjNode, ManagerObjSensor, ManagerObjManager, \
    ManagerObjAlert, ManagerObjAlertLevel, ManagerObjSensorAlert, ManagerObjProfile
from ..globalData.sensorObjects import SensorErrorState


class ManagerEventHandler(BaseManagerEventHandler):

    def __init__(self,
                 global_data: GlobalData):
        super().__init__(global_data)

        # file name of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        # get global configured data
        self.global_data = global_data
        self.sensorAlertLifeSpan = self.global_data.sensorAlertLifeSpan
        self._storage = self.global_data.storage
        self.connectionTimeout = self.global_data.connectionTimeout

        self._thread_update_db_event = threading.Event()
        self._thread_update_db_event.clear()
        self._thread_update_db_queue = []
        self._thread_update_db_lock = threading.Lock()
        self._thread_update_db = threading.Thread(target=self._update_db_data, daemon=True)
        self._thread_update_db.start()

        self._thread_update_connected_db_event = threading.Event()
        self._thread_update_connected_db_event.clear()
        self._thread_update_connected_db_queue = []
        self._thread_update_connected_db_lock = threading.Lock()
        self._thread_update_connected_db = threading.Thread(target=self._update_db_connected, daemon=True)
        self._thread_update_connected_db.start()

    @staticmethod
    def _callback_delete_sensor_alert(sensor_alert: ManagerObjSensorAlert) -> bool:
        with sensor_alert.internal_data_lock:
            # Key/value set in storage class after sensor alert was stored in database.
            return "stored_db" in sensor_alert.internal_data.keys() and sensor_alert.internal_data["stored_db"]

    def _update_db_connected(self):
        """
        Internal function that updates connected flag in the database by waiting for an event to be set.
        """

        while True:
            if not self._thread_update_connected_db_queue:
                self._thread_update_connected_db_event.wait()

            while self._thread_update_connected_db_queue:
                with self._thread_update_connected_db_lock:
                    is_connected = self._thread_update_connected_db_queue.pop(0)
                if not self._storage.update_connected(is_connected):
                    logging.error("[%s]: Unable to update connected flag." % self._log_tag)

            self._thread_update_connected_db_event.clear()

    def _update_db_data(self):
        """
        Internal function that updates alarm system data in the database by waiting for an event to be set.
        """

        while True:
            if not self._thread_update_db_queue:
                self._thread_update_db_event.wait()

            while self._thread_update_db_queue:
                with self._thread_update_db_lock:
                    # Data in queue is irrelevant, it just encodes how many update requests are given.
                    self._thread_update_db_queue.pop()

                # Check if configured to not store sensor alerts
                # => delete them directly to prevent them to be stored in the database.
                if self.sensorAlertLifeSpan == 0:
                    self._system_data.delete_sensor_alerts_received_before(int(time.time()) + 1)

                sensor_alerts_copy = self._system_data.get_sensor_alerts_list()

                # Update the local server information.
                if not self._storage.update_server_information(self.msg_time,
                                                               self._system_data.get_options_list(),
                                                               self._system_data.get_profiles_list(),
                                                               self._system_data.get_nodes_list(),
                                                               self._system_data.get_sensors_list(),
                                                               self._system_data.get_alerts_list(),
                                                               self._system_data.get_managers_list(),
                                                               self._system_data.get_alert_levels_list(),
                                                               sensor_alerts_copy):

                    logging.error("[%s]: Unable to update server information." % self._log_tag)

                # Clear sensor alerts that were added to the database to prevent the list from getting too big.
                elif sensor_alerts_copy:
                    self._system_data.delete_sensor_alerts_with_callback(
                        ManagerEventHandler._callback_delete_sensor_alert)

            self._thread_update_db_event.clear()

    def _update_db_connected_non_blocking(self, is_connected: int):
        """
        Internal function that updates the connected flag in the database without blocking the current thread.
        """
        with self._thread_update_connected_db_lock:
            self._thread_update_connected_db_queue.append(is_connected)
        self._thread_update_connected_db_event.set()

    def _update_db_data_non_blocking(self):
        """
        Internal function that updates alarm system data in the database without blocking the current thread.
        """
        with self._thread_update_db_lock:
            # Data in queue is irrelevant, it just encodes how many update requests are given.
            self._thread_update_db_queue.append(True)
        self._thread_update_db_event.set()

    def status_update(self,
                      msg_time: int,
                      options: List[ManagerObjOption],
                      profiles: List[ManagerObjProfile],
                      nodes: List[ManagerObjNode],
                      sensors: List[ManagerObjSensor],
                      managers: List[ManagerObjManager],
                      alerts: List[ManagerObjAlert],
                      alert_levels: List[ManagerObjAlertLevel]) -> bool:

        result = super().status_update(msg_time,
                                       options,
                                       profiles,
                                       nodes,
                                       sensors,
                                       managers,
                                       alerts,
                                       alert_levels)

        self._update_db_data_non_blocking()

        return result

    def sensor_alert(self,
                     msg_time: int,
                     sensor_alert: ManagerObjSensorAlert) -> bool:

        result = super().sensor_alert(msg_time,
                                      sensor_alert)

        self._update_db_data_non_blocking()

        return result

    def sensor_error_state_change(self,
                                  msg_time: int,
                                  sensor_id: int,
                                  error_state: SensorErrorState) -> bool:

        result = super().sensor_error_state_change(msg_time,
                                                   sensor_id,
                                                   error_state)

        self._update_db_data_non_blocking()

        return result

    def state_change(self,
                     msg_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: int,
                     sensor_data: Any) -> bool:

        result = super().state_change(msg_time,
                                      sensor_id,
                                      state,
                                      data_type,
                                      sensor_data)

        self._update_db_data_non_blocking()

        return result

    def close_connection(self):
        super().close_connection()
        self._update_db_connected_non_blocking(0)
        self._update_db_data_non_blocking()

    def new_connection(self):
        super().new_connection()
        self._update_db_connected_non_blocking(1)
        self._update_db_data_non_blocking()
