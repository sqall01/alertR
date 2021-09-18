#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import logging
from typing import List
from ..globalData import ManagerObjOption, ManagerObjNode, ManagerObjSensor, ManagerObjManager, ManagerObjAlert, \
    ManagerObjAlertLevel, ManagerObjSensorAlert, ManagerObjProfile
from ..client import EventHandler
from ..globalData import GlobalData
from ..globalData.sensorObjects import _SensorData


class BaseManagerEventHandler(EventHandler):

    def __init__(self,
                 global_data: GlobalData):
        super().__init__()

        # File name of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        # get global configured data
        self._global_data = global_data
        self._system_data = self._global_data.system_data

        # Keep track of the last time a message was sent by the other side.
        self.msg_time = 0.0

    def status_update(self,
                      msg_time: int,
                      options: List[ManagerObjOption],
                      profiles: List[ManagerObjProfile],
                      nodes: List[ManagerObjNode],
                      sensors: List[ManagerObjSensor],
                      managers: List[ManagerObjManager],
                      alerts: List[ManagerObjAlert],
                      alert_levels: List[ManagerObjAlertLevel]) -> bool:

        self.msg_time = msg_time

        # Update system data storage with received data.
        options_type = []
        for option in options:
            try:
                self._system_data.update_option(option)
                options_type.append(option.type)

            except ValueError:
                logging.exception("[%s]: Updating Option '%s' failed." % (self._log_tag, option.type))
                return False

        profile_ids = []
        for profile in profiles:
            try:
                self._system_data.update_profile(profile)
                profile_ids.append(profile.profileId)

            except ValueError:
                logging.exception("[%s]: Updating Profile %d failed." % (self._log_tag, profile.profileId))
                return False

        alert_levels_int = set()
        for alert_level in alert_levels:
            try:
                self._system_data.update_alert_level(alert_level)
                alert_levels_int.add(alert_level.level)

            except ValueError:
                logging.exception("[%s]: Updating Alert Level %d failed." % (self._log_tag, alert_level.level))
                return False

        nodes_int = set()
        for node in nodes:
            try:
                self._system_data.update_node(node)
                nodes_int.add(node.nodeId)

            except ValueError:
                logging.exception("[%s]: Updating Node %d failed." % (self._log_tag, node.nodeId))
                return False

        alerts_int = set()
        for alert in alerts:
            try:
                self._system_data.update_alert(alert)
                alerts_int.add(alert.alertId)

            except ValueError:
                logging.exception("[%s]: Updating Alert %d failed." % (self._log_tag, alert.alertId))
                return False

        managers_int = set()
        for manager in managers:
            try:
                self._system_data.update_manager(manager)
                managers_int.add(manager.managerId)

            except ValueError:
                logging.exception("[%s]: Updating Manager %d failed." % (self._log_tag, manager.managerId))
                return False

        sensors_int = set()
        for sensor in sensors:
            try:
                self._system_data.update_sensor(sensor)
                sensors_int.add(sensor.sensorId)

            except ValueError:
                logging.exception("[%s]: Updating Sensor %d failed." % (self._log_tag, sensor.sensorId))
                return False

        # Clean system data storage of not existing data.
        for option in self._system_data.get_options_list():
            if option.type not in options_type:
                self._system_data.delete_option_by_type(option.type)

        for profile in self._system_data.get_profiles_list():
            if profile.profileId not in profile_ids:
                self._system_data.delete_profile_by_id(profile.profileId)

        for alert_level in self._system_data.get_alert_levels_list():
            if alert_level.level not in alert_levels_int:
                self._system_data.delete_alert_level_by_level(alert_level.level)

        for node in self._system_data.get_nodes_list():
            if node.nodeId not in nodes_int:
                self._system_data.delete_node_by_id(node.nodeId)

        for alert in self._system_data.get_alerts_list():
            if alert.alertId not in alerts_int:
                self._system_data.delete_alert_by_id(alert.alertId)

        for manager in self._system_data.get_managers_list():
            if manager.managerId not in managers_int:
                self._system_data.delete_manager_by_id(manager.managerId)

        for sensor in self._system_data.get_sensors_list():
            if sensor.sensorId not in sensors_int:
                self._system_data.delete_sensor_by_id(sensor.sensorId)

        return True

    def sensor_alert(self,
                     msg_time: int,
                     sensor_alert: ManagerObjSensorAlert) -> bool:

        self.msg_time = msg_time

        try:
            self._system_data.add_sensor_alert(sensor_alert)

        except ValueError:
            logging.exception("[%s]: Adding Sensor Alert failed." % self._log_tag)
            return False

        return True

    # noinspection PyTypeChecker
    def profile_change(self,
                       msg_time: int,
                       profile: ManagerObjProfile) -> bool:
        logging.critical("[%s]: profile_change() not supported by node of type 'manager'." % self._log_tag)
        raise NotImplementedError("Not supported by node of type 'manager'.")

    def state_change(self,
                     msg_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: int,
                     sensor_data: _SensorData) -> bool:

        self.msg_time = msg_time

        try:
            self._system_data.sensor_state_change(sensor_id, state, data_type, sensor_data)

        except ValueError:
            logging.exception("[%s]: Updating Sensor %d with state change data failed." % (self._log_tag, sensor_id))
            return False

        return True

    def close_connection(self):
        pass

    def new_connection(self):
        pass
