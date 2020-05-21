#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from .core import BaseManagerEventHandler
from ..localObjects import Option, Node, Sensor, Manager, Alert, AlertLevel, SensorAlert, SensorDataType
from ..globalData import GlobalData
from typing import List, Any


class ManagerEventHandler(BaseManagerEventHandler):

    def __init__(self,
                 global_data: GlobalData):
        super().__init__(global_data)

    def status_update(self,
                      server_time: int,
                      options: List[Option],
                      nodes: List[Node],
                      sensors: List[Sensor],
                      managers: List[Manager],
                      alerts: List[Alert],
                      alert_levels: List[AlertLevel]) -> bool:

        result = super().status_update(server_time,
                                       options,
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
                     sensor_alert: SensorAlert) -> bool:

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
        result = super().close_connection()

        # DEVELOPERS: add your code here
        print("ManagerEventHandler: close_connection")

        return result

    def new_connection(self):
        result = super().new_connection()

        # DEVELOPERS: add your code here
        print("ManagerEventHandler: new_connection")

        return result
