#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import os
from typing import List, Any
from ..client import EventHandler
from ..globalData import ManagerObjManager, ManagerObjNode, ManagerObjOption, ManagerObjSensorAlert, \
    ManagerObjAlertLevel, ManagerObjAlert, ManagerObjSensor, ManagerObjProfile
from ..globalData import SensorDataType


class SensorEventHandler(EventHandler):

    def __init__(self):
        super().__init__()

        # file name of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

    # noinspection PyTypeChecker
    def status_update(self,
                      msg_time: int,
                      options: List[ManagerObjOption],
                      profiles: List[ManagerObjProfile],
                      nodes: List[ManagerObjNode],
                      sensors: List[ManagerObjSensor],
                      managers: List[ManagerObjManager],
                      alerts: List[ManagerObjAlert],
                      alert_levels: List[ManagerObjAlertLevel]) -> bool:
        logging.critical("[%s]: status_update() not supported by node of type 'sensor'." % self._log_tag)
        raise NotImplementedError("Not supported by node of type 'sensor'.")

    # noinspection PyTypeChecker
    def sensor_alert(self,
                     msg_time: int,
                     sensor_alert: ManagerObjSensorAlert) -> bool:
        logging.critical("[%s]: sensor_alert() not supported by node of type 'sensor'." % self._log_tag)
        raise NotImplementedError("Not supported by node of type 'sensor'.")

    # noinspection PyTypeChecker
    def profile_change(self,
                       msg_time: int,
                       profile: ManagerObjProfile) -> bool:
        logging.critical("[%s]: profile_change() not supported by node of type 'sensor'." % self._log_tag)
        raise NotImplementedError("Not supported by node of type 'sensor'.")

    # noinspection PyTypeChecker
    def state_change(self,
                     msg_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: SensorDataType,
                     sensor_data: Any) -> bool:
        logging.critical("[%s]: state_change() not supported by node of type 'sensor'." % self._log_tag)
        raise NotImplementedError("Not supported by node of type 'sensor'.")

    def close_connection(self):
        pass

    def new_connection(self):
        pass
