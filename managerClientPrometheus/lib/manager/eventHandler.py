#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import List, Any
from .core import BaseManagerEventHandler
from .prometheus import Prometheus
from ..globalData.globalData import GlobalData
from ..globalData.managerObjects import ManagerObjOption, ManagerObjNode, ManagerObjSensor, ManagerObjManager, ManagerObjAlert, \
    ManagerObjAlertLevel, ManagerObjSensorAlert, ManagerObjProfile
from ..globalData.sensorObjects import SensorErrorState, SensorDataType


class ManagerEventHandler(BaseManagerEventHandler):

    def __init__(self,
                 global_data: GlobalData,
                 prometheus: Prometheus):
        super().__init__(global_data)
        self._prometheus = prometheus

    def close_connection(self):
        super().close_connection()

    def new_connection(self):
        super().new_connection()

    def sensor_alert(self,
                     msg_time: int,
                     sensor_alert: ManagerObjSensorAlert) -> bool:

        result = super().sensor_alert(msg_time,
                                      sensor_alert)

        sensor = self._system_data.get_sensor_by_id(sensor_alert.sensorId)
        if sensor.dataType == SensorDataType.INT or sensor.dataType == SensorDataType.FLOAT:
            self._prometheus.update_data(sensor)

        return result

    def sensor_error_state_change(self,
                                  msg_time: int,
                                  sensor_id: int,
                                  error_state: SensorErrorState) -> bool:

        result = super().sensor_error_state_change(msg_time,
                                                   sensor_id,
                                                   error_state)

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

        sensor = self._system_data.get_sensor_by_id(sensor_id)
        if sensor.dataType == SensorDataType.INT or sensor.dataType == SensorDataType.FLOAT:
            self._prometheus.update_data(sensor)

        return result

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

        for sensor in self._system_data.get_sensors_list():
            if sensor.dataType == SensorDataType.INT or sensor.dataType == SensorDataType.FLOAT:
                self._prometheus.update_data(sensor)

        return result
