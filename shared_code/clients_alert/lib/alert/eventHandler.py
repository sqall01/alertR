#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import os
import threading
from typing import List, Any
from ..client import EventHandler
from ..alert.core import _Alert
from ..globalData import SensorObjSensorAlert, SensorObjStateChange, SensorDataType
from ..globalData import ManagerObjManager, ManagerObjNode, ManagerObjOption, ManagerObjSensorAlert, \
    ManagerObjAlertLevel, ManagerObjAlert, ManagerObjSensor
from ..globalData import GlobalData


class AlertEventHandler(EventHandler):

    def __init__(self,
                 global_data: GlobalData):
        super().__init__()

        # file name of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        # Get global configured data
        self._global_data = global_data
        self._local_alerts = self._global_data.alerts

    def _thread_alert_off(self, alert: _Alert):
        alert.alert_off()

    def status_update(self,
                      server_time: int,
                      options: List[ManagerObjOption],
                      nodes: List[ManagerObjNode],
                      sensors: List[ManagerObjSensor],
                      managers: List[ManagerObjManager],
                      alerts: List[ManagerObjAlert],
                      alert_levels: List[ManagerObjAlertLevel]) -> bool:
        return True

    def sensor_alert(self,
                     server_time: int,
                     sensor_alert: ManagerObjSensorAlert) -> bool:
        return True

    def sensor_alerts_off(self,
                          server_time: int) -> bool:

        # Stop all alerts.
        for alert in self._local_alerts:
            logging.info("[%s]: Switching Alert '%d' off." % (self._log_tag, alert.id))

            # TODO test code
            thread = threading.Thread(target=self._thread_alert_off,
                                      args=(alert, ))
            thread.daemon = True
            thread.start()

        return True

    def state_change(self,
                     server_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: SensorDataType,
                     sensor_data: Any) -> bool:
        return True

    def close_connection(self):
        pass

    def new_connection(self):
        pass
