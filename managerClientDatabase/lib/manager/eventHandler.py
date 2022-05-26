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
        self._thread_update_db = threading.Thread(target=self._update_db_data, daemon=True)
        self._thread_update_db.start()

    def _update_connected_non_blocking(self, is_connected: int):
        """
        Internal function that updates connected flag in the database without blocking the current thread.
        """
        thread = threading.Thread(target=self._storage.update_connected, args=(is_connected, ), daemon=True)
        thread.start()

    def _update_db_data(self):
        """
        Internal function that updates alarm system data in the database by waiting for an event to be set.
        """

        while True:
            self._thread_update_db_event.wait()
            self._thread_update_db_event.clear()

            # Check if configured to not store sensor alerts
            # => delete them directly to prevent them to be stored in the database.
            if self.sensorAlertLifeSpan == 0:
                self._system_data.delete_sensor_alerts_received_before(int(time.time()) + 1)

            # Update the local server information.
            if not self._storage.update_server_information(self.msg_time,
                                                           self._system_data.get_options_list(),
                                                           self._system_data.get_profiles_list(),
                                                           self._system_data.get_nodes_list(),
                                                           self._system_data.get_sensors_list(),
                                                           self._system_data.get_alerts_list(),
                                                           self._system_data.get_managers_list(),
                                                           self._system_data.get_alert_levels_list(),
                                                           self._system_data.get_sensor_alerts_list()):

                logging.error("[%s]: Unable to update server information." % self._log_tag)

            else:
                # Clear sensor alerts list to prevent it from getting too big.
                self._system_data.delete_sensor_alerts_received_before(2147483647)  # max signed 32bit integer

    def _update_db_data_non_blocking(self):
        """
        Internal function that updates alarm system data in the database without blocking the current thread.
        """
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
        self._update_connected_non_blocking(0)
        self._update_db_data_non_blocking()

    def new_connection(self):
        super().new_connection()
        self._update_connected_non_blocking(1)
        self._update_db_data_non_blocking()
