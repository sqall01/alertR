#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import List, Any
from ..globalData.managerObjects import ManagerObjOption, ManagerObjNode, ManagerObjSensor, ManagerObjManager, \
    ManagerObjAlert, ManagerObjAlertLevel, ManagerObjSensorAlert, ManagerObjProfile
from ..globalData.sensorObjects import SensorDataType, SensorErrorState


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

    def profile_change(self,
                       msg_time: int,
                       profile: ManagerObjProfile) -> bool:
        """
        Is called when a profile change message was received.

        :param msg_time:
        :param profile:
        :return Success or Failure
        """
        raise NotImplementedError("Abstract class.")

    def sensor_alert(self,
                     msg_time: int,
                     sensor_alert: ManagerObjSensorAlert) -> bool:
        """
        Is called when a sensor alert message was received.

        :param msg_time:
        :param sensor_alert:
        :return Success or Failure
        """
        raise NotImplementedError("Abstract class.")

    def sensor_error_state_change(self,
                                  msg_time: int,
                                  sensor_id: int,
                                  error_state: SensorErrorState) -> bool:
        """
        Is called when a sensor error state change message was received.

        :param msg_time:
        :param sensor_id:
        :param error_state:
        :return Success or Failure
        """
        raise NotImplementedError("Abstract class.")

    def state_change(self,
                     msg_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: SensorDataType,
                     sensor_data: Any) -> bool:
        """
        Is called when a state change message was received.

        :param msg_time:
        :param sensor_id:
        :param state:
        :param data_type:
        :param sensor_data:
        :return Success or Failure
        """
        raise NotImplementedError("Abstract class.")

    def status_update(self,
                      msg_time: int,
                      options: List[ManagerObjOption],
                      profiles: List[ManagerObjProfile],
                      nodes: List[ManagerObjNode],
                      sensors: List[ManagerObjSensor],
                      managers: List[ManagerObjManager],
                      alerts: List[ManagerObjAlert],
                      alert_levels: List[ManagerObjAlertLevel]) -> bool:
        """
        Is called when a status update message was received.

        :param msg_time:
        :param options:
        :param profiles:
        :param nodes:
        :param sensors:
        :param managers:
        :param alerts:
        :param alert_levels:
        :return Success or Failure
        """
        raise NotImplementedError("Abstract class.")
