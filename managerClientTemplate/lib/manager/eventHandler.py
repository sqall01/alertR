#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import List, Any
from .core import BaseManagerEventHandler
from ..globalData import ManagerObjOption, ManagerObjNode, ManagerObjSensor, ManagerObjManager, ManagerObjAlert, \
    ManagerObjAlertLevel, ManagerObjSensorAlert, ManagerObjProfile, SensorDataType
from ..globalData import GlobalData


class ManagerEventHandler(BaseManagerEventHandler):

    def __init__(self,
                 global_data: GlobalData):
        super().__init__(global_data)

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

        # DEVELOPERS: add your code here
        print("ManagerEventHandler: status_update")

        return result

    def sensor_alert(self,
                     server_time: int,
                     sensor_alert: ManagerObjSensorAlert) -> bool:

        result = super().sensor_alert(server_time,
                                      sensor_alert)

        # DEVELOPERS: add your code here
        print("ManagerEventHandler: sensor_alert")

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

        # DEVELOPERS: add your code here
        print("ManagerEventHandler: state_change")

        return result

    def close_connection(self):
        super().close_connection()

        # DEVELOPERS: add your code here
        print("ManagerEventHandler: close_connection")

    def new_connection(self):
        super().new_connection()

        # DEVELOPERS: add your code here
        print("ManagerEventHandler: new_connection")
