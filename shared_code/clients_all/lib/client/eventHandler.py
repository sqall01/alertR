#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import List, Any
from ..localObjects import Option, Node, Sensor, Manager, Alert, AlertLevel, SensorAlert, SensorDataType


class EventHandler:

    def __init__(self):
        pass

    def close_connection(self):
        """
        Is called when a connection was closed.
        """
        raise NotImplementedError("Abstract class.")

    def new_connection(self):
        """
        Is called when a new connection was successfully established.
        """
        raise NotImplementedError("Abstract class.")

    def sensor_alert(self,
                     server_time: int,
                     sensor_alert: SensorAlert) -> bool:
        """
        Is called when a sensor alert message was received.

        :param server_time:
        :param sensor_alert:
        """
        raise NotImplementedError("Abstract class.")

    def state_change(self,
                     server_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: SensorDataType,
                     sensor_data: Any) -> bool:
        """
        Is called when a state change message was received.

        :param server_time:
        :param sensor_id:
        :param state:
        :param data_type:
        :param sensor_data:
        """
        raise NotImplementedError("Abstract class.")

    def status_update(self,
                      server_time: int,
                      options: List[Option],
                      nodes: List[Node],
                      sensors: List[Sensor],
                      managers: List[Manager],
                      alerts: List[Alert],
                      alert_levels: List[AlertLevel]) -> bool:
        """
        Is called when a status update message was received.

        :param server_time:
        :param options:
        :param nodes:
        :param sensors:
        :param managers:
        :param alerts:
        :param alert_levels:
        """
        raise NotImplementedError("Abstract class.")
