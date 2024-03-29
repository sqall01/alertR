#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import os
import re
from lightweightpush import LightweightPush, ErrorCodes
from .core import _Alert
from ..globalData import ManagerObjSensorAlert, ManagerObjProfile


# This class represents an alert that sends a notification to the push service
# on the configured channel.
class PushAlert(_Alert):

    def __init__(self, globalData):
        _Alert.__init__(self)

        self._log_tag = os.path.basename(__file__)

        self.globalData = globalData
        self.pushRetryTimeout = self.globalData.pushRetryTimeout
        self.pushRetries = self.globalData.pushRetries

        # These are the message settings.
        self._channel = None
        self.encSecret = None
        self.subject = None
        self.templateFile = None
        self.msgText = None
        self.username = None
        self.password = None
        self.push_service = None

        # Error codes to determine if we can retry to send the message or not.
        self.retryCodes = [ErrorCodes.DATABASE_ERROR,
                           ErrorCodes.GOOGLE_CONNECTION,
                           ErrorCodes.GOOGLE_UNKNOWN,
                           ErrorCodes.GOOGLE_AUTH,
                           ErrorCodes.CLIENT_CONNECTION_ERROR]

    @property
    def channel(self) -> str:
        return self._channel

    @channel.setter
    def channel(self, value: str):
        if bool(re.match(r'^[a-zA-Z0-9-_.~%]+$', value)):
            self._channel = value
        else:
            raise ValueError("Channel '%s' contains illegal characters." % value)

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

    def _send_message(self, subject: str, msg: str, sensor_alert: ManagerObjSensorAlert) -> int:
        """
        Internal function that sends the message to the push server.

        :param subject: Subject of the message.
        :param msg: Message to send.
        :param sensor_alert: sensor alert object.
        :return: error code of push service.
        """
        # Send message to push server.
        ctr = 0
        error_code = ErrorCodes.NO_ERROR
        intersect_alert_levels = [str(x) for x in set(sensor_alert.alertLevels).intersection(self.alertLevels)]
        while True:

            ctr += 1

            self._log_info(self._log_tag, "Sending message for triggered alert levels %s."
                           % ", ".join(intersect_alert_levels))

            error_code = self.push_service.send_msg(subject,
                                                    msg,
                                                    self.channel,
                                                    state=sensor_alert.state,
                                                    time_triggered=sensor_alert.timeReceived,
                                                    max_retries=1)

            if error_code == ErrorCodes.NO_ERROR:
                self._log_info(self._log_tag, "Sending message successful.")
                break

            else:
                if error_code == ErrorCodes.AUTH_ERROR:
                    self._log_error(self._log_tag, "Unable to authenticate at server. Please check your credentials.")

                elif error_code == ErrorCodes.ILLEGAL_MSG_ERROR:
                    self._log_error(self._log_tag, "Server replies that message is malformed.")

                elif error_code == ErrorCodes.VERSION_MISSMATCH:
                    self._log_error(self._log_tag, "Used version is no longer used. Please update your AlertR instance.")

                else:
                    self._log_error(self._log_tag, "Server responded with error '%d'." % error_code)

            # Only retry sending message if we can recover from error.
            if error_code not in self.retryCodes:
                self._log_error(self._log_tag, "Not retrying to re-send message.")
                break

            if ctr > self.pushRetries:
                self._log_error(self._log_tag, "Tried to send message for %d times. Giving up." % ctr)
                break
            
            self._log_info(self._log_tag, "Retrying to send notification to channel '%s' in %d seconds."
                           % (self.channel, self.pushRetryTimeout))

            time.sleep(self.pushRetryTimeout)

        # Return last error code (used by the testPushConfiguration.py script).
        return error_code

    def _process_alert(self, sensor_alert: ManagerObjSensorAlert) -> int:
        temp_msg = self._replace_wildcards(sensor_alert, self.msgText)
        temp_sbj = self._replace_wildcards(sensor_alert, self.subject)

        return self._send_message(temp_sbj, temp_msg, sensor_alert)

    def initialize(self):
        """
        Is called when Alert Client is started to initialize the Alert object.
        """
        with open(self.templateFile, 'r') as fp:
            self.msgText = fp.read()

        self.push_service = LightweightPush(self.username,
                                            self.password,
                                            self.encSecret)

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
