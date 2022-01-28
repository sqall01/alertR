#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
from typing import Optional
from ..globalData import ManagerObjSensorAlert, ManagerObjProfile


# internal class that holds the important attributes
# for a alert to work with (this class must be inherited from the
# used alert class)
class _Alert(object):

    def __init__(self):
        self.id = None  # type: Optional[int]
        self.description = None  # type: Optional[str]
        self.alertLevels = list()

    def _log_debug(self, log_tag: str, msg: str):
        """
        Internal function to log debug messages.
        """
        logging.debug("[%s] [Alert %d] %s" % (log_tag, self.id, msg))

    def _log_info(self, log_tag: str, msg: str):
        """
        Internal function to log info messages.
        """
        logging.info("[%s] [Alert %d] %s" % (log_tag, self.id, msg))

    def _log_warning(self, log_tag: str, msg: str):
        """
        Internal function to log warning messages.
        """
        logging.warning("[%s] [Alert %d] %s" % (log_tag, self.id, msg))

    def _log_error(self, log_tag: str, msg: str):
        """
        Internal function to log error messages.
        """
        logging.error("[%s] [Alert %d] %s" % (log_tag, self.id, msg))

    def _log_critical(self, log_tag: str, msg: str):
        """
        Internal function to log critical messages.
        """
        logging.critical("[%s] [Alert %d] %s" % (log_tag, self.id, msg))

    def _log_exception(self, log_tag: str, msg: str):
        """
        Internal function to log exception messages.
        """
        logging.exception("[%s] [Alert %d] %s" % (log_tag, self.id, msg))

    def alert_triggered(self, sensor_alert: ManagerObjSensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 1.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        raise NotImplementedError("Function not implemented yet.")

    def alert_normal(self, sensor_alert: ManagerObjSensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 0.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        raise NotImplementedError("Function not implemented yet.")

    def alert_profile_change(self, profile: ManagerObjProfile):
        """
        Is called when Alert Client receives a "profilechange" message which is
        sent as soon as AlertR system profile changes.

        :param profile: object that contains the received "profilechange" message.
        """
        raise NotImplementedError("Function not implemented yet.")

    def initialize(self):
        """
        Is called when Alert Client is started to initialize the Alert object.
        """
        raise NotImplementedError("Function not implemented yet.")
