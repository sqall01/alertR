#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import os
import logging
import dbus
from .core import _Alert, SensorAlert


# this class represents an alert that sends notifications via dbus
# to the freedesktop notification system
class DbusAlert(_Alert):

    def __init__(self):
        _Alert.__init__(self)

        self.fileName = os.path.basename(__file__)

        # these values are used to check when the alert was triggered
        # the last time and if it should trigger again
        self.triggered = None
        self.triggerDelay = None

        # message notification
        self.displayTime = None

        # display a received message (if any was received)
        self.displayReceivedMessage = None

        # File location of icon to display.
        self.icon = None  # type: Optional[str]

    # this function is called once when the alert client has connected itself
    # to the server
    def initializeAlert(self):

        # set the time of the trigger
        self.triggered = 0.0

    # this function is called when this alert is triggered
    def triggerAlert(self, sensorAlert: SensorAlert):

        # only execute if the last triggered alert was more than
        # the configured trigger delay ago
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.triggered) > self.triggerDelay:

            # set the time the alert was triggered
            self.triggered = utcTimestamp

            # extract the received message if it was received and should be
            # displayed
            receivedMessage = None
            if (self.displayReceivedMessage
                and sensorAlert.hasOptionalData):

                if "message" in sensorAlert.optionalData.keys():
                    receivedMessage = sensorAlert.optionalData["message"]

            title = ("alertR (%s)" % time.strftime("%d %b %Y at %H:%M:%S", time.localtime(self.triggered)))
            appName = "alertR alertClientDbus"
            replacesId = 0  # not needed, every notification stands for its own

            # differentiate between a generic displayed notification and
            # a notification which also shows the received message
            if receivedMessage is None:

                # differentiate between a sensor alert triggered by
                # a sensor going back in normal state or in alert state
                if sensorAlert.state == 1:
                    tempMessage = "\"" + sensorAlert.description + "\" triggered."
                else:
                    tempMessage = "\"" + sensorAlert.description + "\" back to normal."

            else:

                # differentiate between a sensor alert triggered by
                # a sensor going back in normal state or in alert state
                if sensorAlert.state == 1:
                    tempMessage = ("\""
                                  + sensorAlert.description
                                  + "\" triggered.\n"
                                  + "Received message: \""
                                  + receivedMessage
                                  + "\"")
                else:
                    tempMessage = ("\""
                                  + sensorAlert.description
                                  + "\" back to normal.\n"
                                  + "Received message: \""
                                  + receivedMessage
                                  + "\"")

            # send notification via dbus to notification system
            try:
                busName = 'org.freedesktop.Notifications'
                objectPath = '/org/freedesktop/Notifications'
                sessionBus = dbus.SessionBus()
                dbusObject = sessionBus.get_object(busName, objectPath)
                interface = dbus.Interface(dbusObject, busName)
                interface.Notify(appName,
                                 replacesId,
                                 self.icon,
                                 title,
                                 tempMessage,
                                 [],
                                 [],
                                 self.displayTime)
            except Exception as e:
                logging.exception("[%s]: Could not send notification via dbus." % self.fileName)
                return

    # this function is called when the alert is stopped
    def stopAlert(self, sensorAlert: SensorAlert):
        pass
