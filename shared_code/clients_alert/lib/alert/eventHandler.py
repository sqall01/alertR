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
from ..globalData import ManagerObjManager, ManagerObjNode, ManagerObjOption, ManagerObjSensorAlert, \
    ManagerObjAlertLevel, ManagerObjAlert, ManagerObjSensor, ManagerObjProfile
from ..globalData import GlobalData
from ..globalData.sensorObjects import _SensorData, SensorDataType


class AlertEventHandler(EventHandler):

    def __init__(self,
                 global_data: GlobalData):
        super().__init__()

        # file name of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        # Get global configured data
        self._global_data = global_data
        self._local_alerts = self._global_data.alerts

    def _thread_profile_change(self, alert: _Alert, profile: ManagerObjProfile):
        alert.alert_profile_change(profile)

    def _thread_sensor_alert(self, alert: _Alert, sensor_alert: ManagerObjSensorAlert):
        if sensor_alert.state == 1:
            alert.alert_triggered(sensor_alert)

        elif sensor_alert.state == 0:
            alert.alert_normal(sensor_alert)

    # noinspection PyTypeChecker
    def status_update(self,
                      msg_time: int,
                      options: List[ManagerObjOption],
                      profiles: List[ManagerObjProfile],
                      nodes: List[ManagerObjNode],
                      sensors: List[ManagerObjSensor],
                      managers: List[ManagerObjManager],
                      alerts: List[ManagerObjAlert],
                      alert_levels: List[ManagerObjAlertLevel]) -> bool:
        logging.critical("[%s]: status_update() not supported by node of type 'alert'." % self._log_tag)
        raise NotImplementedError("Not supported by node of type 'alert'.")

    def sensor_alert(self,
                     msg_time: int,
                     sensor_alert: ManagerObjSensorAlert) -> bool:

        at_least_once_triggered = False
        alert_level_str = ", ".join(map(str, sensor_alert.alertLevels))
        for alert in self._local_alerts:

            # Check Alert Levels of Sensor Alert and Alert have common levels.
            intersect_alert_levels = set(sensor_alert.alertLevels).intersection(alert.alertLevels)
            if intersect_alert_levels:
                at_least_once_triggered = True

                logging.debug("[%s]: Trigger Alert '%d' with state '%s' for Alert Levels '%s'."
                              % (self._log_tag, alert.id, str(sensor_alert.state), alert_level_str))

                thread = threading.Thread(target=self._thread_sensor_alert,
                                          args=(alert, sensor_alert))
                thread.daemon = True
                thread.start()

        if not at_least_once_triggered:
            logging.info("[%s]: No Alert triggered for Alert Levels '%s'."
                         % (self._log_tag, alert_level_str))

        return True

    def profile_change(self,
                       msg_time: int,
                       profile: ManagerObjProfile) -> bool:

        # Tell system profile change to all alerts.
        for alert in self._local_alerts:
            logging.debug("[%s]: Notifying Alert '%d' about system profile change to '%d'."
                          % (self._log_tag, alert.id, profile.profileId))

            thread = threading.Thread(target=self._thread_profile_change,
                                      args=(alert, profile))
            thread.daemon = True
            thread.start()

        return True

    # noinspection PyTypeChecker
    def state_change(self,
                     msg_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: SensorDataType,
                     sensor_data: _SensorData) -> bool:
        logging.critical("[%s]: state_change() not supported by node of type 'alert'." % self._log_tag)
        raise NotImplementedError("Not supported by node of type 'alert'.")

    def close_connection(self):
        pass

    def new_connection(self):
        pass
