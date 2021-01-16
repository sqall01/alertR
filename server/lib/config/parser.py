#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import stat
import socket
import ssl
import time
import xml.etree.ElementTree
import logging
from ..users import CSVBackend
from ..storage import Sqlite
from ..globalData import GlobalData
from ..localObjects import AlertLevel, Profile
from ..internalSensors import NodeTimeoutSensor, SensorTimeoutSensor, ProfileChangeSensor, VersionInformerSensor, \
    AlertLevelInstrumentationErrorSensor

log_tag = os.path.basename(__file__)


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
    return os.path.abspath(os.path.dirname(__file__) + "/../../" + inputLocation)


def parse_config(global_data: GlobalData) -> bool:

    try:
        configRoot = xml.etree.ElementTree.parse(global_data.configFile).getroot()

        global_data.logdir = make_path(str(configRoot.find("general").find("log").attrib["dir"]))

        # parse chosen log level
        tempLoglevel = str(configRoot.find("general").find("log").attrib["level"])
        tempLoglevel = tempLoglevel.upper()
        if tempLoglevel == "DEBUG":
            global_data.loglevel = logging.DEBUG

        elif tempLoglevel == "INFO":
            global_data.loglevel = logging.INFO

        elif tempLoglevel == "WARNING":
            global_data.loglevel = logging.WARNING

        elif tempLoglevel == "ERROR":
            global_data.loglevel = logging.ERROR

        elif tempLoglevel == "CRITICAL":
            global_data.loglevel = logging.CRITICAL

        else:
            print("[%s]: No valid log level in config file."  % log_tag)
            return False

        # initialize logging
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%m/%d/%Y %H:%M:%S',
                            filename=global_data.logdir + "/all.log",
                            level=global_data.loglevel)

        global_data.logger = logging.getLogger("server")
        fh = logging.FileHandler(global_data.logdir + "/server.log")
        fh.setLevel(global_data.loglevel)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', '%m/%d/%Y %H:%M:%S')
        fh.setFormatter(formatter)
        global_data.logger.addHandler(fh)

    except Exception as e:
        print("[%s]: Config could not be parsed." % log_tag)
        print(e)
        return False

    if not parse_main_config(configRoot, global_data):
        global_data.logger.error("[%s]: Could not parse config." % log_tag)
        return False

    return True


def parse_main_config(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:
    if not check_config_file(configRoot, global_data):
        return False

    if not configure_update(configRoot, global_data):
        return False

    if not configure_user_backend(configRoot, global_data):
        return False

    if not configure_storage(configRoot, global_data):
        return False

    if not configure_survey(configRoot, global_data):
        return False

    if not configure_server(configRoot, global_data):
        return False

    if not configure_profiles(configRoot, global_data):
        return False

    if not configure_alert_levels(configRoot, global_data):
        return False

    if not configure_internal_sensors(configRoot, global_data):
        return False

    return True


def check_config_file(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:

    # Check file permission of config file (do not allow it to be accessible by others).
    config_stat = os.stat(global_data.configFile)
    if (config_stat.st_mode & stat.S_IROTH
       or config_stat.st_mode & stat.S_IWOTH
       or config_stat.st_mode & stat.S_IXOTH):
        global_data.logger.error("[%s]: Config file is accessible by others. " % log_tag
                                 + "Please remove file permissions for others.")
        return False

    # check if config and server version are compatible
    version = float(configRoot.attrib["version"])
    if version != global_data.version:
        global_data.logger.error("[%s]: Config version '%.3f' not compatible " % (log_tag, version)
                                 + "with server version '%.3f'." % global_data.version)
        return False

    return True


def configure_update(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:

    # parse update options
    try:
        global_data.logger.debug("[%s]: Parsing update configuration." % log_tag)
        global_data.update_url = str(configRoot.find("update").find("server").attrib["url"])

    except Exception:
        global_data.logger.exception("[%s]: Parsing update options failed." % log_tag)
        return False

    return True


def configure_user_backend(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:

    # Configure user credentials backend.
    try:
        global_data.logger.debug("[%s]: Initializing user backend." % log_tag)
        global_data.userBackend = CSVBackend(global_data, global_data.userBackendCsvFile)

    except Exception:
        global_data.logger.exception("[%s]: Configuring user backend failed." % log_tag)
        return False

    return True


def configure_storage(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:

    # Configure storage backend.
    try:
        global_data.logger.debug("[%s]: Initializing storage backend." % log_tag)
        global_data.storage = Sqlite(global_data.storageBackendSqliteFile, global_data)

    except Exception:
        global_data.logger.exception("[%s]: Configuring storage backend failed." % log_tag)
        return False

    # Add server as node to the database.
    serverUsername = global_data.storage.getUniqueID()
    if not global_data.storage.addNode(serverUsername,
                                       socket.gethostname(),
                                       "server",
                                       "server",
                                       global_data.version,
                                       global_data.rev,
                                       1):
        global_data.logger.error("[%s]: Not able to add server as node to the database." % log_tag)
        return False

    serverNodeId = global_data.storage.getNodeId(serverUsername)

    # Mark server node as connected.
    if not global_data.storage.markNodeAsConnected(serverNodeId):
        global_data.logger.error("[%s]: Not able to mark server node as connected." % log_tag)
        return False

    return True


def configure_survey(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:

    # Get survey configurations
    try:
        global_data.logger.debug("[%s]: Parsing survey configuration." % log_tag)
        global_data.survey_activated = (str(configRoot.find("general").find(
            "survey").attrib["participate"]).upper() == "TRUE")

    except Exception:
        global_data.logger.exception("[%s]: Configuring survey failed." % log_tag)
        return False

    return True


def configure_server(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:

    # Get server configurations
    try:
        global_data.logger.debug("[%s]: Parsing server configuration." % log_tag)
        global_data.serverCertFile = make_path(str(configRoot.find("general").find("server").attrib["certFile"]))
        global_data.serverKeyFile = make_path(str(configRoot.find("general").find("server").attrib["keyFile"]))
        global_data.server_port = int(configRoot.find("general").find("server").attrib["port"])

    except Exception:
        global_data.logger.exception("[%s]: Configuring server failed." % log_tag)
        return False

    if os.path.exists(global_data.serverCertFile) is False or os.path.exists(global_data.serverKeyFile) is False:
        global_data.logger.error("[%s]: Server certificate or key does not exist." % log_tag)
        return False

    # get client configurations
    try:
        global_data.useClientCertificates = (str(configRoot.find("general").find("client").attrib[
                                                     "useClientCertificates"]).upper() == "TRUE")

    except Exception:
        global_data.logger.exception("[%s]: Configuring client certificate failed." % log_tag)
        return False

    if global_data.useClientCertificates is True:
        global_data.clientCAFile = make_path(str(configRoot.find("general").find("client").attrib["clientCAFile"]))

        if os.path.exists(global_data.clientCAFile) is False:
            global_data.logger.error("[%s]: Client CA file does not exist." % log_tag)
            return False

    # Get TLS/SSL configurations.
    try:
        noSSLv2 = (str(configRoot.find("general").find("ssl").attrib["noSSLv2"]).upper() == "TRUE")
        noSSLv3 = (str(configRoot.find("general").find("ssl").attrib["noSSLv3"]).upper() == "TRUE")
        noTLSv1_0 = (str(configRoot.find("general").find("ssl").attrib["noTLSv1_0"]).upper() == "TRUE")
        noTLSv1_1 = (str(configRoot.find("general").find("ssl").attrib["noTLSv1_1"]).upper() == "TRUE")
        noTLSv1_2 = (str(configRoot.find("general").find("ssl").attrib["noTLSv1_2"]).upper() == "TRUE")

        if noSSLv2:
            global_data.sslOptions |= ssl.OP_NO_SSLv2
        if noSSLv3:
            global_data.sslOptions |= ssl.OP_NO_SSLv3
        if noTLSv1_0:
            global_data.sslOptions |= ssl.OP_NO_TLSv1
        if noTLSv1_1:
            global_data.sslOptions |= ssl.OP_NO_TLSv1_1
        if noTLSv1_2:
            global_data.sslOptions |= ssl.OP_NO_TLSv1_2

    except Exception:
        global_data.logger.exception("[%s]: Configuring TLS/SSL failed." % log_tag)
        return False

    return True


def configure_profiles(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:

    # parse all profiles
    try:
        global_data.logger.debug("[%s]: Parsing profiles configuration." % log_tag)
        for item in configRoot.find("profiles").iterfind("profile"):

            profile = Profile()

            profile.id = int(item.find("general").attrib["id"])
            profile.name = str(item.find("general").attrib["name"])

            # Check if the profile only exists once.
            for temp_profile in global_data.profiles:
                if temp_profile.id == profile.id:
                    global_data.logger.error("[%s]: Profile must be unique." % log_tag)
                    return False

            global_data.profiles.append(profile)

    except Exception:
        global_data.logger.exception("[%s]: Configuring Profiles failed." % log_tag)
        return False

    has_id_zero = False
    for profile in global_data.profiles:
        if profile.id == 1:
            has_id_zero = True
            break
    if not has_id_zero:
        global_data.logger.error("[%s]: Profile with id '1' has to exist." % log_tag)
        return False

    return True


def configure_alert_levels(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:

    # parse all alert levels
    try:
        global_data.logger.debug("[%s]: Parsing alert levels configuration." % log_tag)
        for item in configRoot.find("alertLevels").iterfind("alertLevel"):

            alertLevel = AlertLevel()

            alertLevel.level = int(item.find("general").attrib["level"])
            alertLevel.name = str(item.find("general").attrib["name"])
            alertLevel.triggerAlways = (str(item.find("general").attrib["triggerAlways"]).upper() == "TRUE")
            alertLevel.triggerAlertTriggered = (str(item.find("general").attrib[
                                                        "triggerAlertTriggered"]).upper() == "TRUE")
            alertLevel.triggerAlertNormal = (str(item.find("general").attrib["triggerAlertNormal"]).upper() == "TRUE")

            # check if instrumentation is activated
            # => parse instrumentation
            alertLevel.instrumentation_active = (str(item.find("instrumentation").attrib[
                                                         "activated"]).upper() == "TRUE")
            if alertLevel.instrumentation_active:
                alertLevel.instrumentation_cmd = str(item.find("instrumentation").attrib["cmd"])
                alertLevel.instrumentation_timeout = int(item.find("instrumentation").attrib["timeout"])

            alertLevel.profiles = list()
            for profile_xml in item.iterfind("profile"):
                alertLevel.profiles.append(int(profile_xml.text))

            # Check if the alert level only exists once.
            for tempAlertLevel in global_data.alertLevels:
                if tempAlertLevel.level == alertLevel.level:
                    global_data.logger.error("[%s]: Alert Level '%d' must be unique." % (log_tag, tempAlertLevel.level))
                    return False

            # Check instrumentation settings for sanity.
            if alertLevel.instrumentation_active is True and os.path.exists(alertLevel.instrumentation_cmd) is False:
                global_data.logger.error("[%s]: Alert Level '%d' instrumentation command '%s' does not exist."
                                         % (log_tag, alertLevel.level, alertLevel.instrumentation_cmd))
                return False

            if alertLevel.instrumentation_active is True and not os.access(alertLevel.instrumentation_cmd, os.X_OK):
                global_data.logger.error("[%s]: Alert Level '%d' instrumentation command '%s' not executable."
                                         % (log_tag, alertLevel.level, alertLevel.instrumentation_cmd))
                return False

            if alertLevel.instrumentation_active is True and alertLevel.instrumentation_timeout <= 0:
                global_data.logger.error("[%s]: Alert Level '%d' instrumentation timeout has to be greater than 0."
                                         % (log_tag, alertLevel.level))
                return False

            # Check profile settings.
            if not alertLevel.profiles:
                global_data.logger.error("[%s]: Alert Level '%d' needs at least one profile configured."
                                         % (log_tag, alertLevel.level))
                return False

            for profile in alertLevel.profiles:
                if not any(map(lambda x: x.id == profile, global_data.profiles)):
                    global_data.logger.error("[%s]: Profile '%d' configured in Alert Level '%d' does not exist."
                                             % (log_tag, profile, alertLevel.level))
                    return False

            global_data.alertLevels.append(alertLevel)

    except Exception:
        global_data.logger.exception("[%s]: Configuring Alert Levels failed." % log_tag)
        return False

    # check if all alert levels for alert clients that exist in the
    # database are configured in the configuration file
    alertLevelsInDb = global_data.storage.getAllAlertsAlertLevels()
    if alertLevelsInDb is None:
        global_data.logger.error("[%s]: Could not get alert client Alert Levels from database." % log_tag)
        return False

    for alertLevelInDb in alertLevelsInDb:
        found = False
        for alertLevel in global_data.alertLevels:
            if alertLevelInDb == alertLevel.level:
                found = True
                break
        if found:
            continue
        else:
            global_data.logger.error("[%s]: An Alert Level for an alert client exists in the database "
                                     % log_tag
                                     + "that is not configured.")
            return False

    # check if all alert levels for sensors that exist in the
    # database are configured in the configuration file
    alertLevelsInDb = global_data.storage.getAllSensorsAlertLevels()
    if alertLevelsInDb is None:
        global_data.logger.error("[%s]: Could not get sensor Alert Levels from database." % log_tag)
        return False

    for alertLevelInDb in alertLevelsInDb:
        found = False
        for alertLevel in global_data.alertLevels:
            if alertLevelInDb == alertLevel.level:
                found = True
                break
        if found:
            continue
        else:
            global_data.logger.error("[%s]: An Alert Level for a sensor exists in the database that is not configured."
                                     % log_tag)
            return False

    return True


def configure_internal_sensors(configRoot: xml.etree.ElementTree.Element, global_data: GlobalData) -> bool:

    serverUsername = global_data.storage.getUniqueID()
    if serverUsername is None:
        global_data.logger.error("[%s]: Not able to get unique id from database." % log_tag)
        return False

    serverNodeId = global_data.storage.getNodeId(serverUsername)
    if serverNodeId is None:
        global_data.logger.error("[%s]: Not able to get node id from database." % log_tag)
        return False

    # Parse internal server sensors
    try:
        global_data.logger.debug("[%s]: Parsing internal sensors configuration." % log_tag)
        internalSensorsCfg = configRoot.find("internalSensors")
        dbSensors = list()
        dbInitialStateList = list()

        # Parse sensor timeout sensor (if activated).
        item = internalSensorsCfg.find("sensorTimeout")
        if str(item.attrib["activated"]).upper() == "TRUE":

            sensor = SensorTimeoutSensor(global_data)

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

            # Check alert level setting.
            if len(set(sensor.alertLevels)) != len(sensor.alertLevels):
                global_data.logger.error("[%s]: The same Alert Level is set multiple times for the same "
                                         % log_tag
                                         + "internal Sensor.")
                return False

            for alert_level in sensor.alertLevels:
                if not any(map(lambda x: x.level == alert_level, global_data.alertLevels)):
                    global_data.logger.error("[%s]: At least one Alert Level for an internal Sensor does not exist."
                                             % log_tag)
                    return False

            global_data.internalSensors.append(sensor)

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

            sensor = NodeTimeoutSensor(global_data)

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

            # Check alert level setting.
            if len(set(sensor.alertLevels)) != len(sensor.alertLevels):
                global_data.logger.error("[%s]: The same Alert Level is set multiple times for the same "
                                         % log_tag
                                         + "internal Sensor.")
                return False

            for alert_level in sensor.alertLevels:
                if not any(map(lambda x: x.level == alert_level, global_data.alertLevels)):
                    global_data.logger.error("[%s]: At least one Alert Level for an internal Sensor does not exist."
                                             % log_tag)
                    return False

            global_data.internalSensors.append(sensor)

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
        item = internalSensorsCfg.find("profileChange")
        if str(item.attrib["activated"]).upper() == "TRUE":

            sensor = ProfileChangeSensor(global_data)

            sensor.nodeId = serverNodeId
            sensor.alertDelay = 0
            sensor.state = 0
            sensor.lastStateUpdated = int(time.time())
            sensor.description = str(item.attrib["description"])

            # Profile change sensor has always this fix internal id
            # (stored as remoteSensorId).
            sensor.remoteSensorId = 2

            sensor.alertLevels = list()
            for alertLevelXml in item.iterfind("alertLevel"):
                sensor.alertLevels.append(int(alertLevelXml.text))

            # Check alert level setting.
            if len(set(sensor.alertLevels)) != len(sensor.alertLevels):
                global_data.logger.error("[%s]: The same Alert Level is set multiple times for the same "
                                         % log_tag
                                         + "internal Sensor.")
                return False

            for alert_level in sensor.alertLevels:
                if not any(map(lambda x: x.level == alert_level, global_data.alertLevels)):
                    global_data.logger.error("[%s]: At least one Alert Level for an internal Sensor does not exist."
                                             % log_tag)
                    return False

            global_data.internalSensors.append(sensor)

            # Set initial state of the internal sensor to the state
            # of the alert system.
            option = global_data.storage.get_option_by_type("profile")
            if option is None:
                global_data.logger.error("[%s]: Unable to get 'profile' option from database." % log_tag)
                return False

            sensor.data = int(option.value)

            # Create sensor dictionary element for database interaction.
            temp = dict()
            temp["clientSensorId"] = sensor.remoteSensorId
            temp["alertDelay"] = sensor.alertDelay
            temp["alertLevels"] = sensor.alertLevels
            temp["description"] = sensor.description
            temp["state"] = 0
            temp["dataType"] = sensor.dataType
            temp["data"] = sensor.data
            dbSensors.append(temp)

            # Add tuple to db state list to set initial states of the
            # internal sensors.
            dbInitialStateList.append((sensor.remoteSensorId, sensor.state))

        # Parse version informer sensor (if activated).
        item = internalSensorsCfg.find("versionInformer")
        if str(item.attrib["activated"]).upper() == "TRUE":

            sensor = VersionInformerSensor(global_data)

            sensor.nodeId = serverNodeId
            sensor.alertDelay = 0
            sensor.lastStateUpdated = int(time.time())
            sensor.description = str(item.attrib["description"])
            sensor.repo_url = global_data.update_url
            sensor.check_interval = int(item.attrib["interval"])

            # Version informer sensor has always this fix internal id
            # (stored as remoteSensorId).
            sensor.remoteSensorId = 3

            sensor.alertLevels = list()
            for alertLevelXml in item.iterfind("alertLevel"):
                sensor.alertLevels.append(int(alertLevelXml.text))

            # Check alert level setting.
            if len(set(sensor.alertLevels)) != len(sensor.alertLevels):
                global_data.logger.error("[%s]: The same Alert Level is set multiple times for the same "
                                         % log_tag
                                         + "internal Sensor.")
                return False

            for alert_level in sensor.alertLevels:
                if not any(map(lambda x: x.level == alert_level, global_data.alertLevels)):
                    global_data.logger.error("[%s]: At least one Alert Level for an internal Sensor does not exist."
                                             % log_tag)
                    return False

            global_data.internalSensors.append(sensor)

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

        # Parse alert level instrumentation error sensor (if activated).
        item = internalSensorsCfg.find("alertLevelInstrumentationError")
        if str(item.attrib["activated"]).upper() == "TRUE":

            sensor = AlertLevelInstrumentationErrorSensor(global_data)

            sensor.nodeId = serverNodeId
            sensor.lastStateUpdated = int(time.time())
            sensor.description = str(item.attrib["description"])

            # Alert level instrumentation error sensor has always this fix internal id
            # (stored as remoteSensorId).
            sensor.remoteSensorId = 4

            sensor.alertLevels = list()
            for alertLevelXml in item.iterfind("alertLevel"):
                sensor.alertLevels.append(int(alertLevelXml.text))

            # Check alert level setting.
            if len(set(sensor.alertLevels)) != len(sensor.alertLevels):
                global_data.logger.error("[%s]: The same Alert Level is set multiple times for the same "
                                         % log_tag
                                         + "internal Sensor.")
                return False

            for alert_level in sensor.alertLevels:
                if not any(map(lambda x: x.level == alert_level, global_data.alertLevels)):
                    global_data.logger.error("[%s]: At least one Alert Level for an internal Sensor does not exist."
                                             % log_tag)
                    return False

            global_data.internalSensors.append(sensor)

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

    except Exception:
        global_data.logger.exception("[%s]: Configuring internal sensors failed." % log_tag)
        return False

    # Add internal sensors to database (updates/deletes also old
    # sensor data in the database).
    if not global_data.storage.addSensors(serverUsername, dbSensors):
        global_data.logger.error("[%s]: Not able to add internal sensors to database." % log_tag)
        return False

    # get sensor id for each activated internal sensor from the database
    for sensor in global_data.internalSensors:

        sensor.sensorId = global_data.storage.getSensorId(sensor.nodeId,
                                                          sensor.remoteSensorId)
        if sensor.sensorId is None:
            global_data.logger.error("[%s]: Not able to get sensor id for internal sensor from database." % log_tag)
            return False

    # Set initial states of the internal sensors.
    if not global_data.storage.updateSensorState(serverNodeId, dbInitialStateList):
        global_data.logger.error("[%s]: Not able set initial states for internal sensors in database." % log_tag)
        return False

    return True
