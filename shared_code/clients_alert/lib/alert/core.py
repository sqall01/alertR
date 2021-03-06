#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import Optional
from ..globalData import ManagerObjSensorAlert


# internal class that holds the important attributes
# for a alert to work with (this class must be inherited from the
# used alert class)
class _Alert(object):

    def __init__(self):
        self.id = None  # type: Optional[int]
        self.description = None  # type: Optional[str]
        self.alertLevels = list()

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

    def alert_off(self):
        """
        Is called when Alert Client receives a "sensoralertsoff" message which is
        sent as soon as AlertR alarm status is deactivated.
        """
        raise NotImplementedError("Function not implemented yet.")

    def initialize(self):
        """
        Is called when Alert Client is started to initialize the Alert object.
        """
        raise NotImplementedError("Function not implemented yet.")
