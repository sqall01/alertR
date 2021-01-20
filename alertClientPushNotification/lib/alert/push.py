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
import re
from lightweightpush import LightweightPush, ErrorCodes
from .core import _Alert
from ..globalData import SensorDataType, ManagerObjSensorAlert, AlertObjProfileChange


# This class represents an alert that sends a notification to the push service
# on the configured channel.
class PushAlert(_Alert):

    def __init__(self, globalData):
        _Alert.__init__(self)

        self.fileName = os.path.basename(__file__)

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
        if sensor_alert.dataType == SensorDataType.NONE:
            data_message = "None"
        elif sensor_alert.dataType == SensorDataType.INT or sensor_alert.dataType == SensorDataType.FLOAT:
            data_message = str(sensor_alert.sensorData)
        else:
            data_message = "Unknown"

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

            logging.info("[%s] Alert '%d' sending message for triggered alert levels %s."
                         % (self.fileName, self.id, ", ".join(intersect_alert_levels)))

            error_code = self.push_service.send_msg(subject,
                                                    msg,
                                                    self.channel,
                                                    state=sensor_alert.state,
                                                    time_triggered=sensor_alert.timeReceived,
                                                    max_retries=1)

            if error_code == ErrorCodes.NO_ERROR:
                logging.info("[%s] Alert '%d' sending message successful."
                             % (self.fileName, self.id))
                break

            else:
                if error_code == ErrorCodes.AUTH_ERROR:
                    logging.error("[%s] Alert '%d' unable to authenticate at server. Please check your credentials."
                                  % (self.fileName, self.id))

                elif error_code == ErrorCodes.ILLEGAL_MSG_ERROR:
                    logging.error("[%s] Alert '%d' server replies that message is malformed."
                                  % (self.fileName, self.id))

                elif error_code == ErrorCodes.VERSION_MISSMATCH:
                    logging.error("[%s] Alert '%d' used version is no longer used. Please update your AlertR instance."
                                  % (self.fileName, self.id))

                else:
                    logging.error("[%s] Alert '%d' server responded with error '%d'."
                                  % (self.fileName, self.id, error_code))

            # Only retry sending message if we can recover from error.
            if error_code not in self.retryCodes:
                logging.error("[%s]: Alert '%d' do not retry to send message." % (self.fileName, self.id))
                break

            if ctr > self.pushRetries:
                logging.error("[%s]: Alert '%d' tried to send message for %d times. Giving up."
                              % (self.fileName, self.id, ctr))
                break
            
            logging.info("[%s] Alert '%d' retrying to send notification to channel '%s' in %d seconds."
                         % (self.fileName, self.id, self.channel, self.pushRetryTimeout))

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

    def alert_profile_change(self, profile_change: AlertObjProfileChange):
        """
        Is called when Alert Client receives a "profilechange" message which is
        sent as soon as AlertR system profile changes.
        """
        pass
