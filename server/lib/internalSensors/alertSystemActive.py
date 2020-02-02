#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from ..globalData import GlobalData
from ..localObjects import SensorDataType
from .core import _InternalSensor


# Class that represents the internal sensor that
# is responsible to trigger sensor alerts if the
# alert system changes is state from activated/deactivated
class AlertSystemActiveSensor(_InternalSensor):

    def __init__(self,
                 global_data: GlobalData):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.NONE

        # used for logging
        self.log_tag = os.path.basename(__file__)

        # Get global configured data.
        self.global_data = global_data
        self.logger = self.global_data.logger
        self.storage = None  # Not available in global data during configuration, set in initialize()
        self.sensor_alert_executer = None  # Not available in global data during configuration, set in initialize()

    def initialize(self):
        if self.sensor_alert_executer is None:
            self.sensor_alert_executer = self.global_data.sensorAlertExecuter
        if self.storage is None:
            self.storage = self.global_data.storage

    def set_state(self,
                  state: int):
        """
        Sets state of sensor, changes it in storage, creates a sensor alert for the change, and wakes up sensor
        alert processing.

        :param state: state of sensor (0 or 1)
        """
        # Set state regardless if we are already in this state. Therefore, we create a sensor alert for each
        # alert system status change message.
        self.state = state

        if not self.storage.updateSensorState(self.nodeId,  # nodeId
                                              [(self.remoteSensorId, state)],  # stateList
                                              None):  # logger

            self.logger.error("[%s]: Not able to change sensor state for internal alert system active sensor."
                              % self.log_tag)

        if self.storage.addSensorAlert(self.nodeId,  # nodeId
                                       self.sensorId,  # sensorId
                                       state,  # state
                                       "",  # dataJson
                                       True,  # changeState
                                       False,  # hasLatestData
                                       SensorDataType.NONE,  # sensorData
                                       None):  # logger
            self.sensor_alert_executer.sensorAlertEvent.set()

        else:
            self.logger.error("[%s]: Not able to add sensor alert for internal alert system active sensor."
                              % self.log_tag)
