#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from typing import Optional, Dict, Any
from .core import _InternalSensor
from ..localObjects import AlertLevel
# noinspection PyProtectedMember
from ..storage.core import _Storage
from ..globalData.globalData import GlobalData
from ..globalData.sensorObjects import SensorDataNone, SensorDataType


# Class that represents the internal sensor that
# is responsible for alert level instrumentation errors.
class AlertLevelInstrumentationErrorSensor(_InternalSensor):

    def __init__(self,
                 global_data: GlobalData):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.NONE
        self.data = SensorDataNone()
        self.alertDelay = 0
        self.state = 0

        # file name of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        self._global_data = global_data
        self._logger = global_data.logger

        # Not available in global data during configuration, set in initialize()
        self._sensor_alert_executer = None

        # Not available in global data during configuration, set in initialize()
        self._storage = None  # type: Optional[_Storage]

    def _add_sensor_alert(self, optional_data: Dict[str, Any]):
        """
        Adds sensor alert for processing.
        :param optional_data: optional data
        """

        self._logger.debug("[%s]: Triggering sensor alert for an instrumentation error of Alert Level '%d'."
                           % (self._log_tag, optional_data["alert_level"]))

        if not self._sensor_alert_executer.add_sensor_alert(self.nodeId,
                                                            self.sensorId,
                                                            1,
                                                            optional_data,
                                                            False,
                                                            False,
                                                            self.dataType,
                                                            self.data,
                                                            self._logger):
            self._logger.error("[%s]: Not able to add sensor alert for "
                               % self._log_tag
                               + "internal alert level instrumentation error sensor.")

    def initialize(self):
        if self._sensor_alert_executer is None:
            self._sensor_alert_executer = self._global_data.sensorAlertExecuter

        if self._storage is None:
            self._storage = self._global_data.storage

    def raise_sensor_alert_execution_error(self, alert_level: AlertLevel):
        """
        Raises a sensor alert if the instrumentation produces an error while trying to execute it.
        :param alert_level:
        """
        message = "Executing instrumentation for Alert Level '%d' failed." % alert_level.level

        optional_data = {"message": message,
                         "alert_level": alert_level.level,
                         "instrumentation_cmd": alert_level.instrumentation_cmd,
                         "instrumentation_timeout": alert_level.instrumentation_timeout}

        self._add_sensor_alert(optional_data)

    def raise_sensor_alert_exit_code(self, alert_level: AlertLevel, exit_code: int):
        """
        Raises a sensor alert if the instrumentation returns an error code not equal to 0.
        :param alert_level:
        :param exit_code:
        """
        message = "Instrumentation for Alert Level '%d' exited with exit code '%d'." % (alert_level.level, exit_code)

        optional_data = {"message": message,
                         "alert_level": alert_level.level,
                         "instrumentation_cmd": alert_level.instrumentation_cmd,
                         "instrumentation_timeout": alert_level.instrumentation_timeout,
                         "exit_code": exit_code}

        self._add_sensor_alert(optional_data)

    def raise_sensor_alert_invalid_output(self, alert_level: AlertLevel):
        """
        Raises a sensor alert if the instrumentation returns invalid output.
        :param alert_level:
        """
        message = "Unable to process output from instrumentation for Alert Level '%d'." % alert_level.level

        optional_data = {"message": message,
                         "alert_level": alert_level.level,
                         "instrumentation_cmd": alert_level.instrumentation_cmd,
                         "instrumentation_timeout": alert_level.instrumentation_timeout}

        self._add_sensor_alert(optional_data)

    def raise_sensor_alert_output_empty(self, alert_level: AlertLevel):
        """
        Raises a sensor alert if the instrumentation does not produce any output.
        :param alert_level:
        """
        message = "No output for instrumentation for Alert Level '%d'." % alert_level.level

        optional_data = {"message": message,
                         "alert_level": alert_level.level,
                         "instrumentation_cmd": alert_level.instrumentation_cmd,
                         "instrumentation_timeout": alert_level.instrumentation_timeout}

        self._add_sensor_alert(optional_data)

    def raise_sensor_alert_timeout(self, alert_level: AlertLevel):
        """
        Raises a sensor alert if the instrumentation times out.
        :param alert_level:
        """
        message = "Instrumentation for Alert Level '%d' timed out." % alert_level.level

        optional_data = {"message": message,
                         "alert_level": alert_level.level,
                         "instrumentation_cmd": alert_level.instrumentation_cmd,
                         "instrumentation_timeout": alert_level.instrumentation_timeout}

        self._add_sensor_alert(optional_data)
