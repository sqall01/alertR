#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import subprocess
import json
from typing import List
from .core import _Alert
from ..globalData import ManagerObjSensorAlert, ManagerObjProfile


# class that executes an command when an alert is triggered or all alerts
# are stopped
class ExecuterAlert(_Alert):

    def __init__(self):
        _Alert.__init__(self)

        # used for logging
        self._log_tag = os.path.basename(__file__)

        # Flag that indicates if command execution for corresponding received message is activated.
        self.cmd_triggered_activated = False
        self.cmd_normal_activated = False
        self.cmd_profile_change_activated = False

        # The command to execute and the arguments to pass when
        # a sensor alert with state "triggered" is received.
        self.cmd_triggered_list = list()

        # A list of indexes that have to be replaced with new data in the
        # "triggered" command list before executing.
        self.cmd_triggered_replace_list = list()

        # The command to execute and the arguments to pass when
        # a sensor alert with state "normal" is received.
        self.cmd_normal_list = list()

        # A list of indexes that have to be replaced with new data in the
        # "normal" command list before executing.
        self.cmd_normal_replace_list = list()

        # The command to execute and the arguments to pass when
        # an profile change message is received.
        self.cmd_profile_change_list = list()

        # The target system profile ids that the profile change message has to contain before the command is executed.
        self.cmd_profile_change_target_profiles = set()

        # A list of indexes that have to be replaced with new data in the
        # "profilechange" command list before executing.
        self.cmd_profile_change_replace_list = list()

    def _execute_cmd(self, execute_cmd_list: List[str]):

        self._log_debug(self._log_tag, "Executing command '%s'." % " ".join(execute_cmd_list))

        try:
            subprocess.Popen(execute_cmd_list, close_fds=True)
        except Exception as e:
            self._log_exception(self._log_tag, "Executing process failed.")
            self._log_error(self._log_tag, "Command was: %s" % " ".join(execute_cmd_list))

    def initialize(self):
        """
        Is called when Alert Client is started to initialize the Alert object.
        """

        # Find all elements that have to be replaced before executing them.
        for i in range(1, len(self.cmd_triggered_list)):
            element = self.cmd_triggered_list[i]
            if element.upper() in ["$SENSORALERT$", "$PROFILECHANGE$"]:
                self.cmd_triggered_replace_list.append(i)

        for i in range(1, len(self.cmd_normal_list)):
            element = self.cmd_normal_list[i]
            if element.upper() in ["$SENSORALERT$", "$PROFILECHANGE$"]:
                self.cmd_normal_replace_list.append(i)

        for i in range(1, len(self.cmd_profile_change_list)):
            element = self.cmd_profile_change_list[i]
            if element.upper() in ["$SENSORALERT$", "$PROFILECHANGE$"]:
                self.cmd_profile_change_replace_list.append(i)

    def alert_triggered(self, sensor_alert: ManagerObjSensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 1.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        if not self.cmd_triggered_activated:
            return

        self._log_info(self._log_tag, "Executing command for state '%d'." % sensor_alert.state)

        # Prepare command execution by replacing all placeholders.
        temp_execute = list(self.cmd_triggered_list)
        for i in self.cmd_triggered_replace_list:
            if temp_execute[i].upper() == "$SENSORALERT$":
                temp_execute[i] = json.dumps(sensor_alert.copy_to_dict())

            elif temp_execute[i].upper() == "$PROFILECHANGE$":
                temp_execute[i] = "None"

        self._execute_cmd(temp_execute)

    def alert_normal(self, sensor_alert: ManagerObjSensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 0.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        if not self.cmd_normal_activated:
            return

        self._log_info(self._log_tag, "Executing command for state '%d'." % sensor_alert.state)

        # Prepare command execution by replacing all placeholders.
        temp_execute = list(self.cmd_normal_list)
        for i in self.cmd_normal_replace_list:
            if temp_execute[i].upper() == "$SENSORALERT$":
                temp_execute[i] = json.dumps(sensor_alert.copy_to_dict())

            elif temp_execute[i].upper() == "$PROFILECHANGE$":
                temp_execute[i] = "None"

        self._execute_cmd(temp_execute)

    def alert_profile_change(self, profile: ManagerObjProfile):
        """
        Is called when Alert Client receives a "profilechange" message which is
        sent as soon as AlertR system profile changes.

        :param profile: object that contains the received "profilechange" message.
        """
        if not self.cmd_profile_change_activated:
            return

        if profile.profileId not in self.cmd_profile_change_target_profiles:
            return

        self._log_info(self._log_tag, "Executing for profile change.")

        # Prepare command execution by replacing all placeholders.
        temp_execute = list(self.cmd_profile_change_list)
        for i in self.cmd_profile_change_replace_list:
            if temp_execute[i].upper() == "$SENSORALERT$":
                temp_execute[i] = "None"

            elif temp_execute[i].upper() == "$PROFILECHANGE$":
                temp_execute[i] = json.dumps(profile.copy_to_dict())

        self._execute_cmd(temp_execute)
