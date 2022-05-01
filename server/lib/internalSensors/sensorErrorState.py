#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from typing import List
from .core import _InternalSensor
from ..localObjects import Option, Profile
from ..globalData.globalData import GlobalData
from ..globalData.sensorObjects import SensorDataInt, SensorDataType, SensorErrorState


class SensorErrorStateSensor(_InternalSensor):
    """
    Class that represents the internal sensor that is responsible to trigger sensor alerts if a sensor in the system
    signals an error state.
    """

    def __init__(self,
                 global_data: GlobalData):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.INT
        self.state = 0
        self.data = SensorDataInt(0, "Sensor(s)")
        self.alertDelay = 0
        self.error_state = SensorErrorState()

        # Profile change sensor has always this fix internal id.
        self.clientSensorId = 5

        # used for logging
        self._log_tag = os.path.basename(__file__)

        # Get global configured data.
        self._global_data = global_data
        self._logger = self._global_data.logger
        self._storage = None  # Not available in global data during configuration, set in initialize()
        self._sensor_alert_executer = None  # Not available in global data during configuration, set in initialize()

        # Set of sensor ids that are currently in an error state.
        self._sensor_ids_in_error = set()

    def initialize(self):
        if self._sensor_alert_executer is None:
            self._sensor_alert_executer = self._global_data.sensorAlertExecuter
        if self._storage is None:
            self._storage = self._global_data.storage

        # Create initial set of sensor ids that are currently in an error state.
        self._sensor_ids_in_error = set(self._storage.get_sensor_ids_in_error_state(self._logger))

        # Update sensor state if we have sensors in error state during initialization.
        if self._sensor_ids_in_error:
            self.state = 1
            self.data = SensorDataInt(len(self._sensor_ids_in_error), "Sensor(s)")
            self._global_data.managerUpdateExecuter.queue_state_change(self.sensorId, self.state, self.data)

    def process_error_state(self, sensor_id: int, error_state: SensorErrorState):
        """
        Triggers sensor alert for the given error state.

        :param sensor_id:
        :param error_state:
        :return:
        """


        # TODO what do we send for optional data (username and clientsensorid?)
        raise NotImplementedError("TODO not finished yet")

        if error_state.state == error_state.OK:
            self._sensor_ids_in_error.discard(sensor_id)

        else:
            self._sensor_ids_in_error.add(sensor_id)

        if self._sensor_ids_in_error:
            self.state = 1
            self.data = SensorDataInt(len(self._sensor_ids_in_error), "Sensor(s)")

        else:
            self.state = 0
            self.data = SensorDataInt(0, "Sensor(s)")


        # TODO is this necessary or does the add_sensor_alert also do this?
        if not self.storage.updateSensorData(self.nodeId,
                                             [(self.clientSensorId, self.data)],
                                             self._logger):
            self._logger.error("[%s]: Not able to change sensor data for internal sensor error state sensor."
                               % self._log_tag)
            return

        if not self._sensor_alert_executer.add_sensor_alert(self.nodeId,
                                                            self.sensorId,
                                                            1,
                                                            optional_data,
                                                            True,
                                                            True,
                                                            self.dataType,
                                                            self.data,
                                                            self._logger):
            self._logger.error("[%s]: Not able to add sensor alert for internal sensor error state sensor."
                               % self._log_tag)
