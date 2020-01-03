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
import smtplib
from ..localObjects import SensorDataType
from .core import _Alert, SensorAlert


# this class represents an alert that sends a notification via mail
# to the configured address 
class MailAlert(_Alert):

    def __init__(self):
        _Alert.__init__(self)

        self.fileName = os.path.basename(__file__)

        # this flag is used to signalize if the alert is triggered or not
        self.triggered = None

        # these are the mail settings
        self.host = None
        self.port = None
        self.fromAddr = None
        self.toAddr = None
        self.subject = None
        self.templateFile = None

        self.bodyText = None

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

    # this function is called once when the alert client has connected itself
    # to the server (should be use to initialize everything that is needed
    # for the alert)
    def initializeAlert(self):

        # set the state of the alert to "not triggered"
        self.triggered = False

        with open(self.templateFile, 'r') as fp:
            self.bodyText = fp.read()

    def triggerAlert(self, sensorAlert: SensorAlert):

        # replace wildcards with the actual values
        tempMsg = self._replaceWildcards(sensorAlert, self.bodyText)
        tempSbj = self._replaceWildcards(sensorAlert, self.subject)

        emailHeader = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" % (self.fromAddr, self.toAddr, tempSbj)

        try:
            logging.info("[%s] Sending eMail for triggered alert." % self.fileName)
            smtpServer = smtplib.SMTP(self.host, self.port)
            smtpServer.sendmail(self.fromAddr, self.toAddr, emailHeader + tempMsg)
            smtpServer.quit()

        except Exception as e:
            logging.exception("[%s]: Unable to send eMail for triggered alert." % self.fileName)

    def stopAlert(self, sensorAlert: SensorAlert):
        pass
