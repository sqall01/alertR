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
from ..globalData import ManagerObjOption, ManagerObjNode, ManagerObjSensor, ManagerObjManager, \
    ManagerObjAlert, ManagerObjAlertLevel, ManagerObjSensorAlert, ManagerObjProfile
from ..globalData import SensorDataType
from ..globalData import GlobalData


class ManagerEventHandler(BaseManagerEventHandler):

    def __init__(self,
                 global_data: GlobalData):
        super().__init__(global_data)

        # file name of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # get global configured data
        self.global_data = global_data
        self.sensorAlertLifeSpan = self.global_data.sensorAlertLifeSpan
        self.storage = self.global_data.storage
        self.connectionTimeout = self.global_data.connectionTimeout

    def _update_db_data(self):
        """
        Internal function that updates alarm system data in the database.
        """

        # Check if configured to not store sensor alerts
        # => delete them directly to prevent them to be stored in the database.
        if self.sensorAlertLifeSpan == 0:
            self._system_data.delete_sensor_alerts_received_before(int(time.time()) + 1)

        # Update the local server information.
        if not self.storage.update_server_information(self.msg_time,
                                                      self._system_data.get_options_list(),
                                                      self._system_data.get_profiles_list(),
                                                      self._system_data.get_nodes_list(),
                                                      self._system_data.get_sensors_list(),
                                                      self._system_data.get_alerts_list(),
                                                      self._system_data.get_managers_list(),
                                                      self._system_data.get_alert_levels_list(),
                                                      self._system_data.get_sensor_alerts_list()):

            logging.error("[%s]: Unable to update server information." % self.fileName)

        else:
            # Clear sensor alerts list to prevent it from getting too big.
            self._system_data.delete_sensor_alerts_received_before(2147483647)  # max signed 32bit integer

    def _update_db_data_non_blocking(self):
        """
        Internal function that updates alarm system data in the database without blocking the current thread.
        """
        thread = threading.Thread(target=self._update_db_data, daemon=True)
        thread.start()

    def status_update(self,
                      server_time: int,
                      options: List[ManagerObjOption],
                      profiles: List[ManagerObjProfile],
                      nodes: List[ManagerObjNode],
                      sensors: List[ManagerObjSensor],
                      managers: List[ManagerObjManager],
                      alerts: List[ManagerObjAlert],
                      alert_levels: List[ManagerObjAlertLevel]) -> bool:

        result = super().status_update(server_time,
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
                     server_time: int,
                     sensor_alert: ManagerObjSensorAlert) -> bool:

        result = super().sensor_alert(server_time,
                                      sensor_alert)

        self._update_db_data_non_blocking()

        return result

    def state_change(self,
                     server_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: SensorDataType,
                     sensor_data: Any) -> bool:

        result = super().state_change(server_time,
                                      sensor_id,
                                      state,
                                      data_type,
                                      sensor_data)

        self._update_db_data_non_blocking()

        return result

    def close_connection(self):
        super().close_connection()
        self._update_db_data_non_blocking()

    def new_connection(self):
        super().new_connection()
        self._update_db_data_non_blocking()
