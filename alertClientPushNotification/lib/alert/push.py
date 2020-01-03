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
import threading
import re
from lightweightpush import LightweightPush, ErrorCodes
from .core import _Alert, SensorAlert
from ..localObjects import SensorDataType


# This class represents an alert that sends a notification to the push service
# on the configured channel.
class PushAlert(_Alert):

    def __init__(self, globalData):
        _Alert.__init__(self)

        self.fileName = os.path.basename(__file__)

        # this flag is used to signalize if the alert is triggered or not
        self.triggered = None

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

    # Internal function that replaces the wildcards in the message
    # with the corresponding values.
    def _replaceWildcards(self, sensorAlert: SensorAlert, message: str) -> str:

        # Create a received message text.
        if sensorAlert.hasOptionalData and "message" in sensorAlert.optionalData.keys():
            receivedMessage = sensorAlert.optionalData["message"]
        else:
            receivedMessage = "None"

        sensorDescription = sensorAlert.description

        # convert state to a text
        if sensorAlert.state == 0:
            stateMessage = "Normal"
        elif sensorAlert.state == 1:
            stateMessage = "Triggered"
        else:
            stateMessage = "Undefined"

        # Convert data to a string.
        if sensorAlert.dataType == SensorDataType.NONE:
            dataMessage = "None"
        elif sensorAlert.dataType == SensorDataType.INT or sensorAlert.dataType == SensorDataType.FLOAT:
            dataMessage = str(sensorAlert.sensorData)
        else:
            dataMessage = "Unknown"

        # Replace wildcards in the message with the actual values.
        tempMsg = message.replace("$MESSAGE$", receivedMessage)
        tempMsg = tempMsg.replace("$STATE$", stateMessage)
        tempMsg = tempMsg.replace("$SENSORDESC$", sensorDescription)
        tempMsg = tempMsg.replace("$TIMERECEIVED$", time.strftime("%d %b %Y %H:%M:%S",
                                                                  time.localtime(sensorAlert.timeReceived)))
        tempMsg = tempMsg.replace("$SENSORDATA$", dataMessage)

        return tempMsg

    # Internal function that sends the message to the push server.
    def _sendMessage(self, subject: str, msg: str, sensorAlert: SensorAlert) -> int:

        # Send message to push server.
        ctr = 0
        errorCode = ErrorCodes.NO_ERROR
        while True:

            ctr += 1

            logging.info("[%s] Sending message for sensorAlert to server." % self.fileName)

            errorCode = self.push_service.send_msg(subject,
                                                   msg,
                                                   self.channel,
                                                   state=sensorAlert.state,
                                                   time_triggered=sensorAlert.timeReceived,
                                                   max_retries=1)

            if errorCode == ErrorCodes.NO_ERROR:
                logging.info("[%s] Sending message successful." % self.fileName)
                break

            else:
                if errorCode == ErrorCodes.AUTH_ERROR:
                    logging.error("[%s] Unable to authenticate at server. "
                                  % self.fileName
                                  + "Please check your credentials.")

                elif errorCode == ErrorCodes.ILLEGAL_MSG_ERROR:
                    logging.error("[%s] Server replies that message is malformed." % self.fileName)

                elif errorCode == ErrorCodes.VERSION_MISSMATCH:
                    logging.error("[%s] Used version is no longer used. Please update your AlertR instance."
                                  % self.fileName)

                else:
                    logging.error("[%s] Server responded with error '%d'."
                                  % (self.fileName, errorCode))

            # Only retry sending message if we can recover from error.
            if errorCode not in self.retryCodes:
                logging.error("[%s]: Do not retry to send message." % self.fileName)
                break

            if ctr > self.pushRetries:
                logging.error("[%s]: Tried to send message for %d times. Giving up."
                              % (self.fileName, ctr))
                break
            
            logging.info("[%s] Retrying to send notification to channel '%s' in %d seconds."
                         % (self.fileName, self.channel, self.pushRetryTimeout))

            time.sleep(self.pushRetryTimeout)

        # Return last error code (used by the testPushConfiguration.py script).
        return errorCode

    # this function is called once when the alert client has connected itself
    # to the server (should be use to initialize everything that is needed
    # for the alert)
    def initializeAlert(self):

        # set the state of the alert to "not triggered"
        self.triggered = False

        with open(self.templateFile, 'r') as fp:
            self.msgText = fp.read()

        self.push_service = LightweightPush(self.username,
            self.password, self.encSecret)

    def triggerAlert(self, sensorAlert: SensorAlert):

        tempMsg = self._replaceWildcards(sensorAlert, self.msgText)
        tempSbj = self._replaceWildcards(sensorAlert, self.subject)

        thread = threading.Thread(target=self._sendMessage,
                                  args=(tempSbj,
                                  tempMsg,
                                  sensorAlert))
        thread.start()

    def stopAlert(self, sensorAlert: SensorAlert):
        pass
