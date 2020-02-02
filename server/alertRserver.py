#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import sys
import os
import stat
from lib import ConnectionWatchdog, CSVWatchdog
from lib import ServerSession, ThreadedTCPServer
from lib import Sqlite
from lib import AlertLevel
from lib import SensorTimeoutSensor, NodeTimeoutSensor, AlertSystemActiveSensor, VersionInformerSensor
from lib import SensorAlertExecuter
from lib import CSVBackend
from lib import ManagerUpdateExecuter
from lib import GlobalData
from lib import SurveyExecuter
from lib import parse_rule
import socket
import ssl
import logging
import time
import threading
import random
import xml.etree.ElementTree


def make_path(inputLocation: str) -> str:
    """
    Normalizes the path.

    :param inputLocation:
    :return: Normalized path.
    """
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

        globalData.logdir = make_path(str(configRoot.find("general").find("log").attrib["dir"]))

        # parse chosen log level
        tempLoglevel = str(configRoot.find("general").find("log").attrib["level"])
        tempLoglevel = tempLoglevel.upper()
        if tempLoglevel == "DEBUG":
            globalData.loglevel = logging.DEBUG

        elif tempLoglevel == "INFO":
            globalData.loglevel = logging.INFO

        elif tempLoglevel == "WARNING":
            globalData.loglevel = logging.WARNING

        elif tempLoglevel == "ERROR":
            globalData.loglevel = logging.ERROR

        elif tempLoglevel == "CRITICAL":
            globalData.loglevel = logging.CRITICAL

        else:
            raise ValueError("No valid log level in config file.")

        # initialize logging
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%m/%d/%Y %H:%M:%S',
                            filename=globalData.logdir + "/all.log",
                            level=globalData.loglevel)

        globalData.logger = logging.getLogger("server")
        fh = logging.FileHandler(globalData.logdir + "/server.log")
        fh.setLevel(globalData.loglevel)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', '%m/%d/%Y %H:%M:%S')
        fh.setFormatter(formatter)
        globalData.logger.addHandler(fh)

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

        # check if config and server version are compatible
        version = float(configRoot.attrib["version"])
        if version != globalData.version:
            raise ValueError("Config version '%.3f' not compatible with server version '%.3f'."
                             % (version, globalData.version))

        # parse update options
        globalData.logger.debug("[%s]: Parsing update configuration." % fileName)
        updateUrl = str(configRoot.find("update").find("server").attrib["url"])

        # Configure user credentials backend.
        globalData.logger.debug("[%s]: Initializing user backend." % fileName)
        globalData.userBackend = CSVBackend(globalData, globalData.userBackendCsvFile)

        # Configure storage backend.
        globalData.logger.debug("[%s]: Initializing storage backend." % fileName)
        globalData.storage = Sqlite(globalData.storageBackendSqliteFile, globalData)

        # Add server as node to the database.
        serverUsername = globalData.storage.getUniqueID()
        if not globalData.storage.addNode(serverUsername,
                                          socket.gethostname(),
                                          "server",
                                          "server",
                                          globalData.version,
                                          globalData.rev,
                                          1):
            raise ValueError("Not able to add server as node to the database.")

        serverNodeId = globalData.storage.getNodeId(serverUsername)

        # Mark server node as connected.
        if not globalData.storage.markNodeAsConnected(serverNodeId):
            raise ValueError("Not able to mark server node as connected.")

        # Get survey configurations
        globalData.logger.debug("[%s]: Parsing survey configuration." % fileName)
        surveyActivated = (str(configRoot.find("general").find("survey").attrib["participate"]).upper() == "TRUE")

        # get server configurations
        globalData.logger.debug("[%s]: Parsing server configuration." % fileName)
        globalData.serverCertFile = make_path(str(configRoot.find("general").find("server").attrib["certFile"]))
        globalData.serverKeyFile = make_path(str(configRoot.find("general").find("server").attrib["keyFile"]))
        port = int(configRoot.find("general").find("server").attrib["port"])

        if os.path.exists(globalData.serverCertFile) is False or os.path.exists(globalData.serverKeyFile) is False:
            raise ValueError("Server certificate or key does not exist.")

        # get client configurations
        globalData.useClientCertificates = (str(configRoot.find("general").find("client").attrib[
                                            "useClientCertificates"]).upper() == "TRUE")

        if globalData.useClientCertificates is True:
            globalData.clientCAFile = make_path(str(configRoot.find("general").find("client").attrib["clientCAFile"]))

            if os.path.exists(globalData.clientCAFile) is False:
                raise ValueError("Client CA file does not exist.")

        # Get TLS/SSL configurations.
        noSSLv2 = (str(configRoot.find("general").find("ssl").attrib["noSSLv2"]).upper() == "TRUE")
        noSSLv3 = (str(configRoot.find("general").find("ssl").attrib["noSSLv3"]).upper() == "TRUE")
        noTLSv1_0 = (str(configRoot.find("general").find("ssl").attrib["noTLSv1_0"]).upper() == "TRUE")
        noTLSv1_1 = (str(configRoot.find("general").find("ssl").attrib["noTLSv1_1"]).upper() == "TRUE")
        noTLSv1_2 = (str(configRoot.find("general").find("ssl").attrib["noTLSv1_2"]).upper() == "TRUE")

        if noSSLv2:
            globalData.sslOptions |= ssl.OP_NO_SSLv2
        if noSSLv3:
            globalData.sslOptions |= ssl.OP_NO_SSLv3
        if noTLSv1_0:
            globalData.sslOptions |= ssl.OP_NO_TLSv1
        if noTLSv1_1:
            globalData.sslOptions |= ssl.OP_NO_TLSv1_1
        if noTLSv1_2:
            globalData.sslOptions |= ssl.OP_NO_TLSv1_2

        # parse all alert levels
        globalData.logger.debug("[%s]: Parsing alert levels configuration." % fileName)
        for item in configRoot.find("alertLevels").iterfind("alertLevel"):

            alertLevel = AlertLevel()

            alertLevel.level = int(item.find("general").attrib["level"])
            alertLevel.name = str(item.find("general").attrib["name"])
            alertLevel.triggerAlways = (str(item.find("general").attrib["triggerAlways"]).upper() == "TRUE")
            alertLevel.triggerAlertTriggered = (str(item.find("general").attrib[
                                                "triggerAlertTriggered"]).upper() == "TRUE")
            alertLevel.triggerAlertNormal = (str(item.find("general").attrib["triggerAlertNormal"]).upper() == "TRUE")

            # check if rules are activated
            # => parse rules
            alertLevel.rulesActivated = (str(item.find("rules").attrib["activated"]).upper() == "TRUE")
            if alertLevel.rulesActivated:
                parse_rule(alertLevel,
                           globalData,
                           item,
                           fileName)

            # check if the alert level only exists once
            for tempAlertLevel in globalData.alertLevels:
                if tempAlertLevel.level == alertLevel.level:
                    raise ValueError("Alert level must be unique.")

            globalData.alertLevels.append(alertLevel)

        # check if all alert levels for alert clients that exist in the
        # database are configured in the configuration file
        alertLevelsInDb = globalData.storage.getAllAlertsAlertLevels()
        if alertLevelsInDb is None:
            raise ValueError("Could not get alert client alert levels from database.")
        for alertLevelInDb in alertLevelsInDb:
            found = False
            for alertLevel in globalData.alertLevels:
                if alertLevelInDb == alertLevel.level:
                    found = True
                    break
            if found:
                continue
            else:
                raise ValueError("An alert level for an alert client exists in the database that is not configured.")

        # check if all alert levels for sensors that exist in the
        # database are configured in the configuration file
        alertLevelsInDb = globalData.storage.getAllSensorsAlertLevels()
        if alertLevelsInDb is None:
            raise ValueError("Could not get sensor alert levels from database.")
        for alertLevelInDb in alertLevelsInDb:
            found = False
            for alertLevel in globalData.alertLevels:
                if alertLevelInDb == alertLevel.level:
                    found = True
                    break
            if found:
                continue
            else:
                raise ValueError("An alert level for a sensor exists in the database that is not configured.")

        # Parse internal server sensors
        globalData.logger.debug("[%s]: Parsing internal sensors configuration." % fileName)
        internalSensorsCfg = configRoot.find("internalSensors")
        dbSensors = list()
        dbInitialStateList = list()

        # Parse sensor timeout sensor (if activated).
        item = internalSensorsCfg.find("sensorTimeout")
        if str(item.attrib["activated"]).upper() == "TRUE":

            sensor = SensorTimeoutSensor(globalData)

            sensor.nodeId = serverNodeId
            sensor.alertDelay = 0
            sensor.state = 0
            sensor.lastStateUpdated = int(time.time())
            sensor.description = str(item.attrib["description"])

            # Sensor timeout sensor has always this fix internal id
            # (stored as remoteSensorId).
            sensor.remoteSensorId = 0

            sensor.alertLevels = list()
            for alertLevelXml in item.iterfind("alertLevel"):
                sensor.alertLevels.append(int(alertLevelXml.text))

            globalData.internalSensors.append(sensor)

            # Create sensor dictionary element for database interaction.
            temp = dict()
            temp["clientSensorId"] = sensor.remoteSensorId
            temp["alertDelay"] = sensor.alertDelay
            temp["alertLevels"] = sensor.alertLevels
            temp["description"] = sensor.description
            temp["state"] = 0
            temp["dataType"] = sensor.dataType
            dbSensors.append(temp)

            # Add tuple to db state list to set initial states of the
            # internal sensors.
            dbInitialStateList.append((sensor.remoteSensorId, 0))

        # Parse node timeout sensor (if activated).
        item = internalSensorsCfg.find("nodeTimeout")
        if str(item.attrib["activated"]).upper() == "TRUE":

            sensor = NodeTimeoutSensor(globalData)

            sensor.nodeId = serverNodeId
            sensor.alertDelay = 0
            sensor.state = 0
            sensor.lastStateUpdated = int(time.time())
            sensor.description = str(item.attrib["description"])

            # Node timeout sensor has always this fix internal id
            # (stored as remoteSensorId).
            sensor.remoteSensorId = 1

            sensor.alertLevels = list()
            for alertLevelXml in item.iterfind("alertLevel"):
                sensor.alertLevels.append(int(alertLevelXml.text))

            globalData.internalSensors.append(sensor)

            # Create sensor dictionary element for database interaction.
            temp = dict()
            temp["clientSensorId"] = sensor.remoteSensorId
            temp["alertDelay"] = sensor.alertDelay
            temp["alertLevels"] = sensor.alertLevels
            temp["description"] = sensor.description
            temp["state"] = 0
            temp["dataType"] = sensor.dataType
            dbSensors.append(temp)

            # Add tuple to db state list to set initial states of the
            # internal sensors.
            dbInitialStateList.append((sensor.remoteSensorId, 0))

        # Parse alert system active sensor (if activated).
        item = internalSensorsCfg.find("alertSystemActive")
        if str(item.attrib["activated"]).upper() == "TRUE":

            sensor = AlertSystemActiveSensor(globalData)

            sensor.nodeId = serverNodeId
            sensor.alertDelay = 0
            sensor.lastStateUpdated = int(time.time())
            sensor.description = str(item.attrib["description"])

            # Alert system active sensor has always this fix internal id
            # (stored as remoteSensorId).
            sensor.remoteSensorId = 2

            sensor.alertLevels = list()
            for alertLevelXml in item.iterfind("alertLevel"):
                sensor.alertLevels.append(int(alertLevelXml.text))

            globalData.internalSensors.append(sensor)

            # Create sensor dictionary element for database interaction.
            temp = dict()
            temp["clientSensorId"] = sensor.remoteSensorId
            temp["alertDelay"] = sensor.alertDelay
            temp["alertLevels"] = sensor.alertLevels
            temp["description"] = sensor.description
            temp["state"] = 0
            temp["dataType"] = sensor.dataType
            dbSensors.append(temp)

            # Set initial state of the internal sensor to the state
            # of the alert system.
            if globalData.storage.isAlertSystemActive():
                sensor.state = 1
            else:
                sensor.state = 0

            # Add tuple to db state list to set initial states of the
            # internal sensors.
            dbInitialStateList.append((sensor.remoteSensorId, sensor.state))

        # Parse version informer sensor (if activated).
        item = internalSensorsCfg.find("versionInformer")
        if str(item.attrib["activated"]).upper() == "TRUE":

            sensor = VersionInformerSensor(globalData)

            sensor.nodeId = serverNodeId
            sensor.alertDelay = 0
            sensor.state = 0
            sensor.lastStateUpdated = int(time.time())
            sensor.description = str(item.attrib["description"])
            sensor.repo_url = updateUrl
            sensor.check_interval = int(item.attrib["interval"])

            # Version informer sensor has always this fix internal id
            # (stored as remoteSensorId).
            sensor.remoteSensorId = 3

            sensor.alertLevels = list()
            for alertLevelXml in item.iterfind("alertLevel"):
                sensor.alertLevels.append(int(alertLevelXml.text))

            globalData.internalSensors.append(sensor)

            # Create sensor dictionary element for database interaction.
            temp = dict()
            temp["clientSensorId"] = sensor.remoteSensorId
            temp["alertDelay"] = sensor.alertDelay
            temp["alertLevels"] = sensor.alertLevels
            temp["description"] = sensor.description
            temp["state"] = 0
            temp["dataType"] = sensor.dataType
            dbSensors.append(temp)

            # Add tuple to db state list to set initial states of the
            # internal sensors.
            dbInitialStateList.append((sensor.remoteSensorId, 0))

        # Add internal sensors to database (updates/deletes also old
        # sensor data in the database).
        if not globalData.storage.addSensors(serverUsername, dbSensors):
            raise ValueError("Not able to add internal sensors to database.")

        # get sensor id for each activated internal sensor from the database
        for sensor in globalData.internalSensors:

            sensor.sensorId = globalData.storage.getSensorId(sensor.nodeId,
                                                             sensor.remoteSensorId)
            if sensor.sensorId is None:
                raise ValueError("Not able to get sensor id for internal sensor from database.")

        # Set initial states of the internal sensors.
        globalData.storage.updateSensorState(serverNodeId, dbInitialStateList)

    except Exception as e:
        globalData.logger.exception("[%s]: Could not parse config." % fileName)
        sys.exit(1)

    globalData.logger.debug("[%s]: Parsing configuration succeeded." % fileName)

    random.seed()

    # start the thread that handles all sensor alerts
    globalData.logger.info("[%s] Starting sensor alert manage thread." % fileName)
    globalData.sensorAlertExecuter = SensorAlertExecuter(globalData)
    # set thread to daemon
    # => threads terminates when main thread terminates
    globalData.sensorAlertExecuter.daemon = True
    globalData.sensorAlertExecuter.start()

    globalData.logger.info("[%s] Starting manager client manage thread." % fileName)
    # start the thread that handles the manager updates
    globalData.managerUpdateExecuter = ManagerUpdateExecuter(globalData)
    # set thread to daemon
    # => threads terminates when main thread terminates
    globalData.managerUpdateExecuter.daemon = True
    globalData.managerUpdateExecuter.start()

    # start server process
    while True:
        try:
            server = ThreadedTCPServer(globalData, ('0.0.0.0', port), ServerSession)
            break

        except Exception as e:
            globalData.logger.exception("[%s]: Starting server failed. Try again in 5 seconds." % fileName)
            time.sleep(5)

    globalData.logger.info("[%s] Starting server thread." % fileName)
    serverThread = threading.Thread(target=server.serve_forever)
    # set thread to daemon
    # => threads terminates when main thread terminates
    serverThread.daemon = True
    serverThread.start()

    # start a watchdog thread that controls all server sessions
    globalData.logger.info("[%s] Starting connection watchdog thread." % fileName)
    globalData.connectionWatchdog = ConnectionWatchdog(globalData,
                                                       globalData.connectionTimeout)
    # set thread to daemon
    # => threads terminates when main thread terminates
    globalData.connectionWatchdog.daemon = True
    globalData.connectionWatchdog.start()

    # Start a watchdog thread that checks all configuration files.
    globalData.logger.info("[%s] Starting config watchdog thread." % fileName)
    globalData.configWatchdog = CSVWatchdog(globalData,
                                            globalData.configCheckInterval)
    # set thread to daemon
    # => threads terminates when main thread terminates
    globalData.configWatchdog.daemon = True
    globalData.configWatchdog.start()

    # only start survey executer if user wants to participate
    if surveyActivated:

        # Check if version informer sensor is used.
        uses_version_informer = False
        for internal_sensor in globalData.internalSensors:
            if type(internal_sensor) == VersionInformerSensor:
                uses_version_informer = True

        globalData.logger.info("[%s] Starting survey executer thread." % fileName)
        surveyExecuter = SurveyExecuter(uses_version_informer, updateUrl, globalData)
        # set thread to daemon
        # => threads terminates when main thread terminates
        surveyExecuter.daemon = True
        surveyExecuter.start()

    # Finalize internal sensors
    # (do it last in order to resolve problems with objects not available during configuration).
    globalData.logger.info("[%s] Initializing internal sensors." % fileName)
    for internal_sensor in globalData.internalSensors:
        internal_sensor.initialize()

    globalData.logger.info("[%s] Server started." % fileName)

    # Wait until the connection watchdog is initialized.
    while not globalData.connectionWatchdog.isInitialized():
        time.sleep(0.5)

    # handle requests in an infinity loop
    while True:
        server.handle_request()
