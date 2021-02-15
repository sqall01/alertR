#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import urwid
from ..globalData import ManagerObjSensorAlert


# this class is an urwid object for a sensor alert
class SensorAlertUrwid:

    def __init__(self, sensorAlert: ManagerObjSensorAlert, description: str, timeShowSensorAlert: int):

        self.sensorAlert = sensorAlert
        self.description = description
        self.timeReceived = self.sensorAlert.timeReceived
        self.timeShowSensorAlert = timeShowSensorAlert

        # generate formatted string from alert levels
        alertLevelsString = ""
        first = True
        for alertLevel in self.sensorAlert.alertLevels:
            if first:
                first = False
            else:
                alertLevelsString += ", "
            alertLevelsString += str(alertLevel)

        # generate the internal urwid widgets
        stringReceivedTime = time.strftime("%D %H:%M:%S", time.localtime(self.timeReceived))
        self.textWidget = urwid.Text(stringReceivedTime + " - " + self.description + " (" + alertLevelsString + ")")

    # this function returns the final urwid widget that is used
    # to render the sensor alert
    def get(self) -> urwid.Text:
        return self.textWidget

    # this function checks if the sensor alert widget is too old
    def sensorAlertOutdated(self) -> bool:
        # check if the sensor alert is older than the configured time to
        # show the sensor alerts in the list
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.timeReceived) > self.timeShowSensorAlert:
            return True
        return False
