#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import sys
import os
import stat
from lib import ServerCommunication, ConnectionWatchdog, Receiver
from lib import SMTPAlert
from lib import KodiAlert, AlertEventHandler
from lib import GlobalData
import logging
import time
import random
import xml.etree.ElementTree


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

    # generate object of the global needed data
    globalData = GlobalData()

    fileName = os.path.basename(__file__)

    # parse config file, get logfile configurations
    # and initialize logging
    try:
        configRoot = xml.etree.ElementTree.parse(globalData.configFile).getroot()

        logfile = makePath(str(configRoot.find("general").find("log").attrib["file"]))

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
                            filename=logfile,
                            level=loglevel)

    except Exception as e:
        print("Config could not be parsed.")
        print(e)
        sys.exit(1)

    # parse the rest of the config with initialized logging
    try:

        # Check file permission of config file (do not allow it to be accessible by others).
        config_stat = os.stat(globalData.configFile)
        if (config_stat.st_mode & stat.S_IROTH
           or config_stat.st_mode & stat.S_IWOTH
           or config_stat.st_mode & stat.S_IXOTH):
            raise ValueError("Config file is accessible by others. Please remove file permissions for others.")

        # check if config and client version are compatible
        version = float(configRoot.attrib["version"])
        if version != globalData.version:
            raise ValueError("Config version '%.3f' not "
                             % version
                             + "compatible with client version '%.3f'."
                             % globalData.version)

        # parse server configurations
        server = str(configRoot.find("general").find("server").attrib["host"])
        serverPort = int(configRoot.find("general").find("server").attrib["port"])

        # get server certificate file and check if it does exist
        serverCAFile = os.path.abspath(makePath(str(configRoot.find("general").find("server").attrib["caFile"])))
        if os.path.exists(serverCAFile) is False:
            raise ValueError("Server CA does not exist.")

        # get client certificate and keyfile (if required)
        certificateRequired = (str(configRoot.find("general").find(
                               "client").attrib["certificateRequired"]).upper() == "TRUE")

        if certificateRequired is True:
            clientCertFile = os.path.abspath(
                             makePath(str(configRoot.find("general").find("client").attrib["certFile"])))
            clientKeyFile = os.path.abspath(
                            makePath(str(configRoot.find("general").find("client").attrib["keyFile"])))
            if (os.path.exists(clientCertFile) is False
               or os.path.exists(clientKeyFile) is False):
                raise ValueError("Client certificate or key does not exist.")
        else:
            clientCertFile = None
            clientKeyFile = None

        # get user credentials
        username = str(configRoot.find("general").find("credentials").attrib["username"])
        password = str(configRoot.find("general").find("credentials").attrib["password"])

        # Get connection settings.
        temp = (str(configRoot.find("general").find("connection").attrib["persistent"]).upper() == "TRUE")
        if temp:
            globalData.persistent = 1
        else:
            globalData.persistent = 0

        # parse smtp options if activated
        smtpActivated = (str(configRoot.find("smtp").find("general").attrib["activated"]).upper() == "TRUE")
        smtpServer = ""
        smtpPort = -1
        smtpFromAddr = ""
        smtpToAddr = ""
        if smtpActivated is True:
            smtpServer = str(configRoot.find("smtp").find("server").attrib["host"])
            smtpPort = int(configRoot.find("smtp").find("server").attrib["port"])
            smtpFromAddr = str(configRoot.find("smtp").find("general").attrib["fromAddr"])
            smtpToAddr = str(configRoot.find("smtp").find("general").attrib["toAddr"])

        # parse all alerts
        for item in configRoot.find("alerts").iterfind("alert"):

            alert = KodiAlert()

            # get kodi settings
            alert.host = str(item.find("kodi").attrib["host"])
            alert.port = int(item.find("kodi").attrib["port"])
            alert.displayTime = int(item.find("kodi").attrib["displayTime"])
            alert.showMessage = (str(item.find("kodi").attrib["showMessage"]).upper() == "TRUE")
            alert.pausePlayer = (str(item.find("kodi").attrib["pausePlayer"]).upper() == "TRUE")
            alert.triggerDelay = int(item.find("kodi").attrib["triggerDelay"])
            alert.displayReceivedMessage = (str(item.find("kodi").attrib["displayReceivedMessage"]).upper() == "TRUE")
            alert.icon = makePath("./config/kodi_logo.png")

            # these options are needed by the server to
            # differentiate between the registered alerts
            alert.id = int(item.find("general").attrib["id"])
            alert.description = str(item.find("general").attrib["description"])

            alert.alertLevels = list()
            for alertLevelXml in item.iterfind("alertLevel"):
                alert.alertLevels.append(int(alertLevelXml.text))

            # check if description is empty
            if len(alert.description) == 0:
                raise ValueError("Description of alert %d is empty."
                                 % alert.id)

            # check if the id of the alert is unique
            for registeredAlert in globalData.alerts:
                if registeredAlert.id == alert.id:
                    raise ValueError("Id of alert %d is already taken."
                                     % alert.id)

            globalData.alerts.append(alert)

    except Exception as e:
        logging.exception("[%s]: Could not parse config." % fileName)
        sys.exit(1)

    random.seed()

    # check if smtp is activated => generate object to send eMail alerts
    if smtpActivated is True:
        globalData.smtpAlert = SMTPAlert(smtpServer, smtpPort, smtpFromAddr, smtpToAddr)
    else:
        globalData.smtpAlert = None

    # generate object for the communication to the server and connect to it
    globalData.serverComm = ServerCommunication(server,
                                                serverPort,
                                                serverCAFile,
                                                username,
                                                password,
                                                clientCertFile,
                                                clientKeyFile,
                                                AlertEventHandler(globalData),
                                                globalData)
    connectionRetries = 1
    logging.info("[%s]: Connecting to server." % fileName)
    while True:
        # check if 5 unsuccessful attempts are made to connect
        # to the server and if smtp alert is activated
        # => send eMail alert
        if (globalData.smtpAlert is not None
                and (connectionRetries % 5) == 0):
            globalData.smtpAlert.sendCommunicationAlert(connectionRetries)

        if globalData.serverComm.initialize() is True:
            # if smtp alert is activated
            # => send email that communication problems are solved
            if globalData.smtpAlert is not None:
                globalData.smtpAlert.sendCommunicationAlertClear()

            connectionRetries = 1
            break

        connectionRetries += 1

        logging.critical("[%s]: Connecting to server failed. Try again in 5 seconds." % fileName)
        time.sleep(5)

    # when connected => generate watchdog object to monitor the
    # server connection
    logging.info("[%s]: Starting watchdog thread." % fileName)
    watchdog = ConnectionWatchdog(globalData.serverComm,
                                  globalData.pingInterval,
                                  globalData.smtpAlert)
    # set thread to daemon
    # => threads terminates when main thread terminates
    watchdog.daemon = True
    watchdog.start()

    # initialize all alerts
    logging.info("[%s] Initializing alerts." % fileName)
    for alert in globalData.alerts:
        alert.initialize()

    logging.info("[%s]: Client started." % fileName)

    # generate receiver to handle incoming data (for example status updates)
    # (note: we will not return from the receiver unless the client is terminated)
    receiver = Receiver(globalData.serverComm)
    receiver.run()
