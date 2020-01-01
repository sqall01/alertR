#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import logging
import subprocess
import json
from .core import _Alert, SensorAlert


# class that executes an command when an alert is triggered or all alerts
# are stopped
class ExecuterAlert(_Alert):

    def __init__(self):
        _Alert.__init__(self)

        # used for logging
        self.fileName = os.path.basename(__file__)

        # the command to execute and the arguments to pass when
        # an alert is triggered
        self.triggerExecute = list()

        # A list of indexes that have to be replaced with new data in the
        # triggerExecute list before executing.
        self.triggerExecuteReplace = list()

        # the command to execute and the arguments to pass when
        # an alert is stopped
        self.stopExecute = list()

        # A list of indexes that have to be replaced with new data in the
        # stopExecute list before executing.
        self.stopExecuteReplace = list()

    # this function is called once when the alert client has connected itself
    # to the server (should be use to initialize everything that is needed
    # for the alert)
    def initializeAlert(self):

        # Find all elements that have to be replaced before executing them.
        for i in range(1, len(self.triggerExecute)):
            element = self.triggerExecute[i]
            if element.upper() == "$SENSORALERT$":
                self.triggerExecuteReplace.append(i)
        for i in range(1, len(self.stopExecute)):
            element = self.stopExecute[i]
            if element.upper() == "$SENSORALERT$":
                self.stopExecuteReplace.append(i)

    # this function is called when this alert is triggered
    def triggerAlert(self, sensorAlert: SensorAlert):

        logging.debug("[%s]: Executing process "
                      % self.fileName
                      + "'%s' with trigger arguments."
                      % self.description)

        # Prepare command execution by replacing all placeholders.
        tempExecute = list(self.triggerExecute)
        for i in self.triggerExecuteReplace:
            if tempExecute[i].upper() == "$SENSORALERT$":
                tempExecute[i] = json.dumps(sensorAlert.convertToDict())

        try:
            subprocess.Popen(tempExecute, close_fds=True)
        except Exception as e:
            logging.exception("[%s]: Executing process "
                              % self.fileName
                              + "'%s' with trigger arguments failed."
                              % self.description)

    # this function is called when the alert is stopped
    def stopAlert(self, sensorAlert: SensorAlert):

        logging.debug("[%s]: Executing process "
                      % self.fileName
                      + "'%s' with stop arguments."
                      % self.description)

        # Prepare command execution by replacing all placeholders.
        tempExecute = list(self.stopExecute)
        for i in self.stopExecuteReplace:
            if tempExecute[i].upper() == "$SENSORALERT$":
                tempExecute[i] = json.dumps(sensorAlert.convertToDict())

        try:
            subprocess.Popen(tempExecute, close_fds=True)
        except Exception as e:
            logging.exception("[%s]: Executing process "
                              % self.fileName
                              + "'%s' with stop arguments failed."
                              % self.description)
