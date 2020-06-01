#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import os
from ..globalData import GlobalData


# this class handles the screen updates
class ScreenUpdater:

    def __init__(self, global_data: GlobalData):

        # get global configured data
        self.global_data = global_data
        self.console = self.global_data.console

        # file nme of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

    def update_connection_fail(self):
        """
        Updates screen with a failed connection.
        """
        # if reference to console object does not exist
        # => get it from global data or if it does not exist return
        if self.console is None:
            if self.global_data.console is not None:
                self.console = self.global_data.console
            else:
                return

        logging.debug("[%s]: Updating screen for connection failure." % self._log_tag)

        if not self.console.updateScreen("connectionfail"):
            logging.error("[%s]: Updating screen failed." % self._log_tag)

    def update_sensor_alerts(self):
        """
        Updates sensor alerts.
        """
        # if reference to console object does not exist
        # => get it from global data or if it does not exist return
        if self.console is None:
            if self.global_data.console is not None:
                self.console = self.global_data.console
            else:
                return

        logging.info("[%s]: Updating screen with sensor alert." % self._log_tag)

        if not self.console.updateScreen("sensoralert"):
            logging.error("[%s]: Updating screen with sensor alert failed." % self._log_tag)

    def update_status(self):
        """
        Updates screen elements.
        """
        # if reference to console object does not exist
        # => get it from global data or if it does not exist return
        if self.console is None:
            if self.global_data.console is not None:
                self.console = self.global_data.console
            else:
                return

        logging.debug("[%s]: Updating screen." % self._log_tag)

        if not self.console.updateScreen("status"):
            logging.error("[%s]: Updating screen failed." % self._log_tag)
