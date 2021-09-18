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
from ..globalData import ManagerObjOption, ManagerObjNode, ManagerObjSensor, ManagerObjManager, ManagerObjAlert, \
    ManagerObjAlertLevel, ManagerObjSensorAlert, ManagerObjProfile
from ..globalData import GlobalData
from ..globalData.sensorObjects import _SensorData


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

    # is called when a status update event was received from the server
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

        self.screen_updater.update_status()

        return result

    # is called when a sensor alert event was received from the server
    def sensor_alert(self, server_time: int, sensor_alert: ManagerObjSensorAlert) -> bool:

        result = super().sensor_alert(server_time,
                                      sensor_alert)

        self.screen_updater.update_sensor_alerts()

        return result

    # is called when a state change event was received from the server
    def state_change(self,
                     server_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: int,
                     sensor_data: _SensorData) -> bool:

        result = super().state_change(server_time,
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
