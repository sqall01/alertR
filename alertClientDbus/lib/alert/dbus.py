#!/usr/bin/env python3

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
from typing import Optional
from .core import _Alert
from ..globalData import ManagerObjSensorAlert, ManagerObjProfile


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

    def _process_alert(self, sensor_alert: ManagerObjSensorAlert):

        # only execute if the last triggered alert was more than
        # the configured trigger delay ago
        utc_timestamp = int(time.time())
        if (utc_timestamp - self.triggered) > self.triggerDelay:

            # set the time the alert was triggered
            self.triggered = utc_timestamp

            intersect_alert_levels = [str(x) for x in set(sensor_alert.alertLevels).intersection(self.alertLevels)]
            logging.info("[%s] Alert '%d' triggered for alert levels %s."
                         % (self.fileName, self.id, ", ".join(intersect_alert_levels)))

            # extract the received message if it was received and should be
            # displayed
            received_message = None
            if self.displayReceivedMessage and sensor_alert.hasOptionalData:

                if "message" in sensor_alert.optionalData.keys():
                    received_message = sensor_alert.optionalData["message"]

            title = ("AlertR (%s)" % time.strftime("%d %b %Y at %H:%M:%S", time.localtime(self.triggered)))
            app_name = "AlertR alertClientDbus"
            replacesId = 0  # not needed, every notification stands for its own

            # differentiate between a generic displayed notification and
            # a notification which also shows the received message
            if received_message is None:

                # differentiate between a sensor alert triggered by
                # a sensor going back in normal state or in alert state
                if sensor_alert.state == 1:
                    temp_message = "\"" + sensor_alert.description + "\" triggered."
                else:
                    temp_message = "\"" + sensor_alert.description + "\" back to normal."

            else:

                # differentiate between a sensor alert triggered by
                # a sensor going back in normal state or in alert state
                if sensor_alert.state == 1:
                    temp_message = ("\""
                                    + sensor_alert.description
                                    + "\" triggered.\n"
                                    + "Received message: \""
                                    + received_message
                                    + "\"")
                else:
                    temp_message = ("\""
                                    + sensor_alert.description
                                    + "\" back to normal.\n"
                                    + "Received message: \""
                                    + received_message
                                    + "\"")

            # send notification via dbus to notification system
            try:
                bus_name = 'org.freedesktop.Notifications'
                object_path = '/org/freedesktop/Notifications'
                session_bus = dbus.SessionBus()
                dbus_object = session_bus.get_object(bus_name, object_path)
                interface = dbus.Interface(dbus_object, bus_name)
                interface.Notify(app_name,
                                 replacesId,
                                 self.icon,
                                 title,
                                 temp_message,
                                 [],
                                 [],
                                 self.displayTime)
            except Exception as e:
                logging.exception("[%s]: Alert '%d' could not send notification via dbus." % (self.fileName, self.id))
                return

    def initialize(self):
        """
        Is called when Alert Client is started to initialize the Alert object.
        """

        # set the time of the trigger
        self.triggered = 0.0

    # this function is called when this alert is triggered
    def alert_triggered(self, sensor_alert: ManagerObjSensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 1.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        self._process_alert(sensor_alert)

    def alert_normal(self, sensor_alert: ManagerObjSensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 0.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        self._process_alert(sensor_alert)

    def alert_profile_change(self, profile: ManagerObjProfile):
        """
        Is called when Alert Client receives a "profilechange" message which is
        sent as soon as AlertR system profile changes.

        :param profile: object that contains the received "profilechange" message.
        """
        pass
