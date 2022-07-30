#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from prometheus_client import metrics, start_http_server, Gauge
from typing import Dict, cast
from ..globalData.globalData import GlobalData
from ..globalData.managerObjects import ManagerObjSensor
from ..globalData.sensorObjects import SensorDataType, SensorDataInt, SensorDataFloat


class Prometheus:
    def __init__(self,
                 port: int,
                 global_data: GlobalData):
        self._global_data = global_data
        self._system_data = self._global_data.system_data
        self._metrics = dict()  # type: Dict[int, metrics]

        start_http_server(port)

    def update_data(self, sensor: ManagerObjSensor):

        if sensor.sensorId not in self._metrics.keys():
            node = self._system_data.get_node_by_id(sensor.nodeId)
            name = "alertr_sensor_" + node.username + "_" + str(sensor.clientSensorId)
            gauge = Gauge(name, sensor.description)
            self._metrics[sensor.sensorId] = gauge

        else:
            gauge = self._metrics[sensor.sensorId]

        if sensor.dataType == SensorDataType.INT:
            data = cast(SensorDataInt, sensor.data)

        elif sensor.dataType == SensorDataType.FLOAT:
            data = cast(SensorDataFloat, sensor.data)

        else:
            raise TypeError("Illegal data type.")

        gauge.set(data.value)
