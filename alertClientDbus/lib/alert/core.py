#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import threading
from typing import Optional
from ..localObjects import SensorAlert


# internal class that holds the important attributes
# for a alert to work with (this class must be inherited from the
# used alert class)
class _Alert(object):

    def __init__(self):
        self.id = None  # type: Optional[int]
        self.description = None  # type: Optional[str]
        self.alertLevels = list()

    def triggerAlert(self, sensorAlert: SensorAlert):
        raise NotImplementedError("Function not implemented yet.")

    def stopAlert(self, sensorAlert: SensorAlert):
        raise NotImplementedError("Function not implemented yet.")

    def initializeAlert(self):
        raise NotImplementedError("Function not implemented yet.")


# this class is used to trigger or stop an alert
# in an own thread to not block the initiating thread
class AsynchronousAlertExecuter(threading.Thread):

    def __init__(self, alert: _Alert):
        threading.Thread.__init__(self)

        self.fileName = os.path.basename(__file__)
        self.alert = alert

        # this option is used when the thread should
        # trigger an alert
        self.triggerAlert = False

        # this option is used when the thread should
        # stop an alert
        self.stopAlert = False

        # this options are used to transfer data from the received
        # sensor alert to the alert that is triggered
        self.sensorAlert = None  # type: Optional[SensorAlert]

    def run(self):

        # check if an alert should be triggered
        if self.triggerAlert:
            self.alert.triggerAlert(self.sensorAlert)

        # check if an alert should be stopped
        elif self.stopAlert:
            self.alert.stopAlert(self.sensorAlert)
