#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import List
from .screenUpdater import ScreenUpdater
from .core import BaseManagerEventHandler
from ..globalData.globalData import GlobalData
from ..globalData.managerObjects import ManagerObjOption, ManagerObjNode, ManagerObjSensor, ManagerObjManager, \
    ManagerObjAlert, ManagerObjAlertLevel, ManagerObjSensorAlert, ManagerObjProfile
# noinspection PyProtectedMember
from ..globalData.sensorObjects import _SensorData, SensorErrorState


class ManagerEventHandler(BaseManagerEventHandler):
    """
    This class handles an incoming server event (sensor alert message, status update, ...)
    """

    def __init__(self,
                 global_data: GlobalData):
        super().__init__(global_data)

        # get global configured data
        self.global_data = global_data
        self.screen_updater = self.global_data.screenUpdater  # type: ScreenUpdater

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

        self.screen_updater.update_status()

        return result

    def sensor_alert(self, msg_time: int, sensor_alert: ManagerObjSensorAlert) -> bool:

        result = super().sensor_alert(msg_time,
                                      sensor_alert)

        self.screen_updater.update_sensor_alerts()

        return result

    def sensor_error_state_change(self,
                                  msg_time: int,
                                  sensor_id: int,
                                  error_state: SensorErrorState) -> bool:

        result = super().sensor_error_state_change(msg_time,
                                                   sensor_id,
                                                   error_state)

        self.screen_updater.update_status()

        return result

    def state_change(self,
                     msg_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: int,
                     sensor_data: _SensorData) -> bool:

        result = super().state_change(msg_time,
                                      sensor_id,
                                      state,
                                      data_type,
                                      sensor_data)

        self.screen_updater.update_status()

        return result

    def close_connection(self):
        super().close_connection()

        self.screen_updater.update_connection_fail()

    def new_connection(self):
        super().new_connection()

        self.screen_updater.update_status()
