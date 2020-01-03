#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import logging
import os
import xml.etree.cElementTree
import sys
from lib import GlobalData
from lib import PushAlert
from lib.localObjects import SensorAlert
from lightweightpush import ErrorCodes


# Function creates a path location for the given user input.
def makePath(inputLocation):
    # Do nothing if the given location is an absolute path.
    if inputLocation[0] == "/":
        return inputLocation
    # Replace ~ with the home directory.
    elif inputLocation[0] == "~":
        return os.environ["HOME"] + inputLocation[1:]
    # Assume we have a given relative path.
    return os.path.dirname(os.path.abspath(__file__)) + "/" + inputLocation


if __name__ == '__main__':

    fileName = os.path.basename(__file__)
    instanceLocation = os.path.dirname(os.path.abspath(__file__)) + "/"

    # generate object of the global needed data
    globalData = GlobalData()

    try:
        # parse config file
        configRoot = xml.etree.ElementTree.parse(instanceLocation + "/config/config.xml").getroot()

        # parse chosen log level
        tempLoglevel = str(configRoot.find("general").find("log").attrib["level"])
        tempLoglevel = tempLoglevel.upper()
        if tempLoglevel == "DEBUG":
            loglevel = logging.DEBUG
        elif tempLoglevel == "INFO":
            loglevel = logging.INFO
        elif tempLoglevel == "WARNING":
            loglevel = logging.WARNING
        elif tempLoglevel == "ERROR":
            loglevel = logging.ERROR
        elif tempLoglevel == "CRITICAL":
            loglevel = logging.CRITICAL
        else:
            raise ValueError("No valid log level in config file.")

        # initialize logging
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
                            datefmt='%m/%d/%Y %H:%M:%S',
                            level=loglevel)

    except Exception as e:
        print("Config could not be parsed.")
        print(e)
        sys.exit(1)

    # parse the rest of the config with initialized logging
    alerts = list()
    try:

        # Parse alertr.de account settings.
        tempConf = configRoot.find("alerts")
        alertrUsername = str(tempConf.attrib["username"])
        alertrPassword = str(tempConf.attrib["password"])

        # parse all alerts
        for item in configRoot.find("alerts").iterfind("alert"):

            alert = dict()

            # Read the push notification settings.
            alert["username"] = alertrUsername
            alert["password"] = alertrPassword
            alert["channel"] = str(item.find("push").attrib["channel"])
            alert["encSecret"] = str(item.find("push").attrib["secret"])
            alert["subject"] = str(item.find("push").attrib["subject"])
            alert["templateFile"] = makePath(str(item.find("push").attrib["templateFile"]))

            # check if the template file exists
            if not os.path.isfile(alert["templateFile"]):
                raise ValueError("Message template file '%s' does not exist." % alert["templateFile"])

            alert["id"] = int(item.find("general").attrib["id"])
            alert["description"] = str(item.find("general").attrib["description"])

            # check if the id of the alert is unique
            for registeredAlert in alerts:
                if registeredAlert["id"] == alert["id"]:
                    raise ValueError("Id of alert %d is already taken." % alert["id"])

            alerts.append(alert)

    except Exception as e:
        logging.exception("[%s]: Could not parse config." % fileName)
        sys.exit(1)

    # Sending test messages for the configured alerts.
    for alert in alerts:
        logging.info("[%s]: Sending message for alert id %d (%s)."
                     % (fileName, alert["id"], alert["description"]))

        globalData.pushRetryTimeout = 5
        globalData.pushRetries = 1

        subject = "Test message for alert with id %d" % alert["id"]
        message = "This is a test message for the alert:\n\n" \
                   + "Id: %d\nDescription: %s\n\nCheers,\nalertR" \
                   % (alert["id"], alert["description"])

        # Initialize alert object.
        alertObj = PushAlert(globalData)
        alertObj.id = alert["id"]
        alertObj.description = alert["description"]
        alertObj.username = alert["username"]
        alertObj.password = alert["password"]
        alertObj.channel = alert["channel"]
        alertObj.encSecret = alert["encSecret"]
        alertObj.templateFile = alert["templateFile"]
        alertObj.alertLevels = list()
        alertObj.subject = subject
        alertObj.initializeAlert()

        sensorAlert = SensorAlert()
        sensorAlert.state = 1
        sensorAlert.timeReceived = int(time.time())

        errorCode = alertObj._sendMessage(subject, message, sensorAlert)

        # Process response.
        if errorCode == ErrorCodes.NO_ERROR:
            logging.info("[%s]: Message successfully transmitted." % fileName)
        elif errorCode == ErrorCodes.DATABASE_ERROR:
            logging.error("[%s]: Database error on server side. Please try again later." % fileName)
        elif errorCode == ErrorCodes.AUTH_ERROR:
            logging.error("[%s]: Authentication failed. Check your credentials." % fileName)
        elif errorCode == ErrorCodes.ILLEGAL_MSG_ERROR:
            logging.error("[%s]: Illegal message was sent. "
                          % fileName
                          + "Please make sure to use the newest version. "
                          + "If you do, please open an issue on "
                          + "https://github.com/sqall01/alertR.")
        elif errorCode == ErrorCodes.GOOGLE_MSG_TOO_LARGE:
            logging.error("[%s]: Transmitted message too large. Please shorten it." % fileName)
        elif errorCode == ErrorCodes.GOOGLE_CONNECTION:
            logging.error("[%s]: Connection error on server side. Please try again later." % fileName)
        elif errorCode == ErrorCodes.GOOGLE_AUTH:
            logging.error("[%s]: Authentication error on server side. Please try again later." % fileName)
        elif errorCode == ErrorCodes.VERSION_MISSMATCH:
            logging.error("[%s]: Version mismatch. Please update your client." % fileName)
        elif errorCode == ErrorCodes.NO_NOTIFICATION_PERMISSION:
            logging.error("[%s]: No permission to use notification channel. Please update channel configuration."
                          % fileName)
        elif errorCode == ErrorCodes.CLIENT_CONNECTION_ERROR:
            logging.error("[%s]: Client has problems connecting to service. Do you have an Internet connection?."
                          % fileName)
        else:
            logging.error("[%s]: The following error code occurred: %d."
                          % (fileName, errorCode)
                          + "Please make sure to use the newest version. "
                          + "If you do, please open an issue on "
                          + "https://github.com/sqall01/alertR.")
