#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import time
from typing import Set
from .core import _InternalSensor
from ..localObjects import SensorDataType, Node, Sensor
from ..globalData import GlobalData


# Class that represents the internal sensor that
# is responsible for sensor timeouts.
class SensorTimeoutSensor(_InternalSensor):

    def __init__(self,
                 global_data: GlobalData):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.NONE

        # file name of this file (used for logging)
        self.log_tag = os.path.basename(__file__)

        self.global_data = global_data
        self.logger = global_data.logger
        self.sensor_alert_executer = None  # Not available in global data during configuration, set in initialize()
        self.storage = None  # Not available in global data during configuration, set in initialize()

        # A set of ids of the sensors that are timed out.
        # IMPORTANT: ConnectionWatchdog holds a pointer to this object and uses it so the set is always synchronized.
        self._timeout_sensor_ids = set()  # type: Set[int]

    def get_copy_timeout_sensor_ids(self) -> Set[int]:
        """
        Returns a copy of the internal timed out node ids set.

        :return: Copy of the node ids set
        """
        return set(self._timeout_sensor_ids)

    def get_ptr_timeout_sensor_ids(self) -> Set[int]:
        """
        Returns a pointer to the internal timed out sensor ids set.

        :return: Pointer to the sensor ids set
        """
        return self._timeout_sensor_ids

    def initialize(self):
        if self.sensor_alert_executer is None:
            self.sensor_alert_executer = self.global_data.sensorAlertExecuter
        if self.storage is None:
            self.storage = self.global_data.storage

    def sensor_timed_out(self,
                         node_obj: Node,
                         sensor_obj: Sensor):
        """
        Public function that handles a sensor alert for a sensor that freshly timed out.

        :param node_obj:
        :param sensor_obj:
        """

        # If internal sensor is in state "normal", change the
        # state to "triggered" with the raised sensor alert.
        change_state = False
        if self.state == 0:

            self.state = 1
            change_state = True

            # Change sensor state in database.
            if not self.storage.updateSensorState(self.nodeId,  # nodeId
                                                  [(self.clientSensorId, self.state)],  # stateList
                                                  self.logger):  # logger
                self.logger.error("[%s]: Not able to change sensor state for internal sensor "
                                  % self.log_tag
                                  + "timeout sensor.")

        # Create message for sensor alert.
        message = "Sensor '%s' on host '%s' timed out." % (sensor_obj.description, node_obj.hostname)
        optional_data = {"message": message,
                         "description": sensor_obj.description,
                         "hostname": node_obj.hostname,
                         "username": node_obj.username,
                         "instance": node_obj.instance,
                         "nodeType": node_obj.nodeType}

        if not self.sensor_alert_executer.add_sensor_alert(self.nodeId,
                                                           self.sensorId,
                                                           1,
                                                           optional_data,
                                                           change_state,
                                                           False,
                                                           SensorDataType.NONE,
                                                           None,
                                                           self.logger):
            self.logger.error("[%s]: Not able to add sensor alert for internal sensor timeout sensor."
                              % self.log_tag)

    def sensor_back(self,
                    node_obj: Node,
                    sensor_obj: Sensor):
        """
        Public function that handles a sensor alert for a sensor that connected back.

        :param node_obj:
        :param sensor_obj:
        """

        # If internal sensor is in state "triggered" and
        # no sensor is timed out at the moment, change the
        # state to "normal" with the raised sensor alert.
        change_state = False
        if self.state == 1 and not self._timeout_sensor_ids:
            self.state = 0
            change_state = True

            # Change sensor state in database.
            if not self.storage.updateSensorState(self.nodeId,  # nodeId
                                                  [(self.clientSensorId, self.state)],  # stateList
                                                  self.logger):  # logger
                self.logger.error("[%s]: Not able to change sensor state for internal sensor timeout sensor."
                                  % self.log_tag)

        # Create message for sensor alert.
        message = "Sensor '%s' on host '%s' reconnected." % (sensor_obj.description, node_obj.hostname)
        optional_data = {"message": message,
                         "description": sensor_obj.description,
                         "hostname": node_obj.hostname,
                         "username": node_obj.username,
                         "instance": node_obj.instance,
                         "nodeType": node_obj.nodeType}

        if not self.sensor_alert_executer.add_sensor_alert(self.nodeId,
                                                           self.sensorId,
                                                           0,
                                                           optional_data,
                                                           change_state,
                                                           False,
                                                           SensorDataType.NONE,
                                                           None,
                                                           self.logger):
            self.logger.error("[%s]: Not able to add sensor alert for internal sensor timeout sensor."
                              % self.log_tag)

    def reminder(self):
        """
        Public function that handles a sensor alert as a reminder for all timed out sensors.
        """

        # Create message and sensors field for sensor alert.
        message = "%d sensor(s) still timed out:" % len(self._timeout_sensor_ids)
        sensors_field = list()
        for sensor_id in set(self._timeout_sensor_ids):

            # Get sensor object.
            sensor_obj = self.storage.getSensorById(sensor_id)

            # Since a user can be deleted during runtime, check if
            # the node/sensor still existed in the database. Since
            # the node does not exist anymore, remove the sensor
            # from the timeout list.
            if sensor_obj is None:
                self.logger.error("[%s]: Could not get sensor with id %d from database."
                                  % (self.log_tag, sensor_id))
                self._timeout_sensor_ids.remove(sensor_id)
                continue

            # Get sensor details.
            node_obj = self.storage.getNodeById(sensor_obj.nodeId)
            # Since a user can be deleted during runtime, check if
            # the node still existed in the database. Since the
            # node does not exist anymore, remove the sensor
            # from the timeout list.
            if node_obj is None:
                self.logger.error("[%s]: Could not get node with id %d from database."
                                  % (self.log_tag, sensor_obj.nodeId))
                self._timeout_sensor_ids.remove(sensor_id)
                continue

            lastStateUpdateStr = time.strftime("%D %H:%M:%S", time.localtime(sensor_obj.lastStateUpdated))
            if node_obj.hostname is None:
                self.logger.error("[%s]: Could not get hostname for node from database."
                                  % self.log_tag)
                continue

            sensor_field = {"description": sensor_obj.description,
                            "hostname": node_obj.hostname,
                            "username": node_obj.username,
                            "instance": node_obj.instance,
                            "nodeType": node_obj.nodeType,
                            "lastStateUpdated": sensor_obj.lastStateUpdated}

            message += " Host: '%s', Sensor: '%s', Last seen: %s;" \
                       % (node_obj.hostname, sensor_obj.description, lastStateUpdateStr)

            sensors_field.append(sensor_field)

        optional_data = {"message": message,
                         "sensors": sensors_field}

        if not self.sensor_alert_executer.add_sensor_alert(self.nodeId,
                                                           self.sensorId,
                                                           1,
                                                           optional_data,
                                                           False,
                                                           False,
                                                           SensorDataType.NONE,
                                                           None,
                                                           self.logger):
            self.logger.error("[%s]: Not able to add sensor alert for internal sensor timeout sensor."
                              % self.log_tag)
