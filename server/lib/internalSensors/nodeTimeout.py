#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import json
import os
from typing import Set
from .core import _InternalSensor
from ..localObjects import SensorDataType, Node
from ..globalData import GlobalData


# Class that represents the internal sensor that
# is responsible for node timeouts.
class NodeTimeoutSensor(_InternalSensor):

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

        # An internal set of ids of the nodes that are timed out.
        # IMPORTANT: ConnectionWatchdog holds a pointer to this object and uses it so the set is always synchronized.
        self._timeout_node_ids = set()  # type: Set[int]

    def get_copy_timeout_node_ids(self) -> Set[int]:
        """
        Returns a copy of the internal timed out node ids set.

        :return: Copy of the node ids set
        """
        return set(self._timeout_node_ids)

    def get_ptr_timeout_node_ids(self) -> Set[int]:
        """
        Returns a pointer to the internal timed out node ids set.

        :return: Pointer to the node ids set
        """
        return self._timeout_node_ids

    def initialize(self):
        if self.sensor_alert_executer is None:
            self.sensor_alert_executer = self.global_data.sensorAlertExecuter
        if self.storage is None:
            self.storage = self.global_data.storage

    def node_timed_out(self,
                       node_obj: Node):
        """
        Public function that handles a sensor alert for a node that freshly timed out.

        :param node_obj:
        """

        # If internal sensor is in state "normal", change the
        # state to "triggered" with the raised sensor alert.
        change_state = False
        if self.state == 0:

            self.state = 1
            change_state = True

            # Change sensor state in database.
            if not self.storage.updateSensorState(self.nodeId,  # nodeId
                                                  [(self.remoteSensorId, self.state)],  # stateList
                                                  self.logger):  # logger

                self.logger.error("[%s]: Not able to change sensor state for internal node timeout sensor."
                                  % self.log_tag)

        # Create message for sensor alert.
        message = "Node '%s' with username '%s' on host '%s' timed out." \
                  % (str(node_obj.instance), str(node_obj.username), str(node_obj.hostname))
        data_json = json.dumps({"message": message,
                                "hostname": node_obj.hostname,
                                "username": node_obj.username,
                                "instance": node_obj.instance,
                                "nodeType": node_obj.nodeType})

        if not self.sensor_alert_executer.add_sensor_alert(self.nodeId,
                                                           self.sensorId,
                                                           1,
                                                           data_json,
                                                           change_state,
                                                           False,
                                                           SensorDataType.NONE,
                                                           None,
                                                           self.logger):
            self.logger.error("[%s]: Not able to add sensor alert for internal node timeout sensor."
                              % self.log_tag)

    def node_back(self,
                  node_obj: Node):
        """
        Public function that handles a sensor alert for a node that connected back.

        :param node_obj:
        """

        # If internal sensor is in state "triggered" and there is no
        # timed out node left, change the state to "normal" with the raised sensor alert.
        change_state = False
        if self.state == 1 and not self._timeout_node_ids:
            self.state = 0
            change_state = True

            # Change sensor state in database.
            if not self.storage.updateSensorState(self.nodeId,  # nodeId
                                                  [(self.remoteSensorId, self.state)],  # stateList
                                                  self.logger):  # logger
                self.logger.error("[%s]: Not able to change sensor state for internal node timeout sensor."
                                  % self.log_tag)

        # Create message for sensor alert.
        message = "Node '%s' with username '%s' on host '%s' reconnected." \
                  % (str(node_obj.instance), str(node_obj.username), str(node_obj.hostname))
        data_json = json.dumps({"message": message,
                                "hostname": node_obj.hostname,
                                "username": node_obj.username,
                                "instance": node_obj.instance,
                                "nodeType": node_obj.nodeType})

        if not self.sensor_alert_executer.add_sensor_alert(self.nodeId,
                                                           self.sensorId,
                                                           0,
                                                           data_json,
                                                           change_state,
                                                           False,
                                                           SensorDataType.NONE,
                                                           None,
                                                           self.logger):
            self.logger.error("[%s]: Not able to add sensor alert for internal node timeout sensor."
                              % self.log_tag)

    def reminder(self):
        """
        Public function that handles a sensor alert as a reminder for all timed out nodes.
        """

        # Create message and nodes field for sensor alert.
        message = "%d node(s) still timed out:" % len(self._timeout_node_ids)
        nodes_field = list()
        for nodeId in set(self._timeout_node_ids):

            node_obj = self.storage.getNodeById(nodeId)
            # Since a user can be deleted during runtime, check if
            # the node still existed in the database. Since the
            # node does not exist anymore, remove the node
            # from the timeout list.
            if node_obj is None:
                self.logger.error("[%s]: Could not get node with id %d from database."
                                  % (self.log_tag, nodeId))
                continue

            node_field = {"hostname": node_obj.hostname,
                          "username": node_obj.username,
                          "instance": node_obj.instance,
                          "nodeType": node_obj.nodeType}

            message += " Node: '%s, Username: '%s', Hostname: '%s';" \
                       % (str(node_obj.instance), str(node_obj.username), str(node_obj.hostname))

            nodes_field.append(node_field)

        data_json = json.dumps({"message": message,
                                "nodes": nodes_field})

        if not self.sensor_alert_executer.add_sensor_alert(self.nodeId,
                                                           self.sensorId,
                                                           1,
                                                           data_json,
                                                           False,
                                                           False,
                                                           SensorDataType.NONE,
                                                           None,
                                                           self.logger):
            self.logger.error("[%s]: Not able to add sensor alert for internal node timeout sensor."
                              % self.log_tag)
