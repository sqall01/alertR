#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import json
from typing import List
from ..globalData import GlobalData
from ..localObjects import SensorDataType, Option, Profile
from .core import _InternalSensor


class ProfileChangeSensor(_InternalSensor):
    """
    Class that represents the internal sensor that is responsible to trigger sensor alerts if the
    system profile changes.
    """

    def __init__(self,
                 global_data: GlobalData):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.INT
        self.state = 0

        # used for logging
        self._log_tag = os.path.basename(__file__)

        # Get global configured data.
        self._global_data = global_data
        self._logger = self._global_data.logger
        self._profiles = self._global_data.profiles  # type: List[Profile]
        self.storage = None  # Not available in global data during configuration, set in initialize()
        self._sensor_alert_executer = None  # Not available in global data during configuration, set in initialize()

    def initialize(self):
        if self._sensor_alert_executer is None:
            self._sensor_alert_executer = self._global_data.sensorAlertExecuter
        if self.storage is None:
            self.storage = self._global_data.storage

    def process_option(self,
                       option: Option):
        """
        Triggers sensor alert for given profile option.

        :param option:
        """

        # Only handle profile options.
        if option.type != "profile":
            return

        curr_profile = None
        for profile in self._profiles:
            if profile.id == int(option.value):
                curr_profile = profile
                break
        if curr_profile is None:
            self._logger.error("[%s]: Not able to find profile with id %d for internal profile change sensor."
                               % (self._log_tag, int(option.value)))
            return

        if not self.storage.updateSensorData(self.nodeId,  # nodeId
                                             [(self.remoteSensorId, curr_profile.id)],  # dataList
                                             self._logger):  # logger
            self._logger.error("[%s]: Not able to change sensor data for internal profile change sensor."
                               % self._log_tag)
            return

        self.data = curr_profile.id

        message = "Changing system profile to '%s'." % curr_profile.name

        optional_data = {"message": message,
                         "name": curr_profile.name}

        if not self._sensor_alert_executer.add_sensor_alert(self.nodeId,
                                                            self.sensorId,
                                                            1,
                                                            json.dumps(optional_data),
                                                            False,
                                                            True,
                                                            self.dataType,
                                                            self.data,
                                                            self._logger):
            self._logger.error("[%s]: Not able to add sensor alert for internal profile change sensor."
                               % self._log_tag)
