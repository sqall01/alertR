#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import os
import smtplib
from ..globalData import ManagerObjSensorAlert, ManagerObjProfile
from .core import _Alert


# this class represents an alert that sends a notification via mail
# to the configured address 
class MailAlert(_Alert):

    def __init__(self):
        _Alert.__init__(self)

        self._log_tag = os.path.basename(__file__)

        # these are the mail settings
        self.host = None
        self.port = None
        self.fromAddr = None
        self.toAddr = None
        self.subject = None
        self.templateFile = None

        # Body text for send mails.
        self.body_text = None

    def _replace_wildcards(self, sensor_alert: ManagerObjSensorAlert, message: str) -> str:
        """
        Internal function that replaces the wildcards in the message with the corresponding values.

        :param sensor_alert: sensor alert object.
        :param message: message template.
        :return: Generated message.
        """
        # Create a received message text.
        if sensor_alert.hasOptionalData and "message" in sensor_alert.optionalData.keys():
            received_message = sensor_alert.optionalData["message"]
        else:
            received_message = "None"

        sensor_description = sensor_alert.description

        # convert state to a text
        if sensor_alert.state == 0:
            state_message = "Normal"
        elif sensor_alert.state == 1:
            state_message = "Triggered"
        else:
            state_message = "Undefined"

        # Convert data to a string.
        data_message = str(sensor_alert.data)

        # Replace wildcards in the message with the actual values.
        temp_msg = message.replace("$MESSAGE$", received_message)
        temp_msg = temp_msg.replace("$STATE$", state_message)
        temp_msg = temp_msg.replace("$SENSORDESC$", sensor_description)
        temp_msg = temp_msg.replace("$TIMERECEIVED$", time.strftime("%d %b %Y %H:%M:%S",
                                                                    time.localtime(sensor_alert.timeReceived)))
        temp_msg = temp_msg.replace("$SENSORDATA$", data_message)

        return temp_msg

    def _process_alert(self, sensor_alert: ManagerObjSensorAlert):

        # replace wildcards with the actual values
        temp_msg = self._replace_wildcards(sensor_alert, self.body_text)
        temp_sbj = self._replace_wildcards(sensor_alert, self.subject)

        email_header = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" % (self.fromAddr, self.toAddr, temp_sbj)

        intersect_alert_levels = [str(x) for x in set(sensor_alert.alertLevels).intersection(self.alertLevels)]
        try:
            self._log_info(self._log_tag, "Sending mail for triggered alert levels %s."
                           % ", ".join(intersect_alert_levels))
            smtp_server = smtplib.SMTP(self.host, self.port)
            smtp_server.sendmail(self.fromAddr, self.toAddr, email_header + temp_msg)
            smtp_server.quit()

        except Exception as e:
            self._log_exception(self._log_tag, "Unable to send mail.")

    def initialize(self):
        """
        Is called when Alert Client is started to initialize the Alert object.
        """
        with open(self.templateFile, 'r') as fp:
            self.body_text = fp.read()

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
