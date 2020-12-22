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
from lib import ServerCommunication, ConnectionWatchdog
from lib import SMTPAlert
from lib import TempPollingSensor, HumidityPollingSensor, ForecastTempPollingSensor, ForecastRainPollingSensor
from lib import SensorExecuter
from lib import WundergroundDataCollector, DarkskyDataCollector
from lib import GlobalData
from lib import Ordering
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

        # Set connection settings.
        globalData.persistent = 1 # Consider sensor client always persistent

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

        # Parse data collector settings.
        tempConf = configRoot.find("sensors")
        provider = str(tempConf.attrib["provider"]).upper()
        # Create sensor data collector thread.
        if provider == "WUNDERGROUND":
            sensorDataCollector = WundergroundDataCollector(globalData)
            sensorDataCollector.apiKey = str(tempConf.attrib["apiKey"])
            sensorDataCollector.interval = int(tempConf.attrib["interval"])
        elif provider == "DARKSKY":
            sensorDataCollector = DarkskyDataCollector(globalData)
            sensorDataCollector.apiKey = str(tempConf.attrib["apiKey"])
            sensorDataCollector.interval = int(tempConf.attrib["interval"])
        else:
            raise ValueError("Provider '%s' unknown." % provider)

        # parse all sensors
        for item in configRoot.find("sensors").iterfind("sensor"):

            sensorType = str(item.find("weather").attrib["type"]).upper()

            if sensorType == "temperature".upper():

                sensor = TempPollingSensor()

                # these options are needed by the server to
                # differentiate between the registered sensors
                sensor.id = int(item.find("general").attrib["id"])
                sensor.description = str(item.find("general").attrib["description"])
                sensor.alertDelay = int(item.find("general").attrib["alertDelay"])
                sensor.triggerAlert = (str(item.find("general").attrib["triggerAlert"]).upper() == "TRUE")
                sensor.triggerAlertNormal = (str(item.find("general").attrib["triggerAlertNormal"]).upper() == "TRUE")
                sensor.triggerState = 1

                sensor.alertLevels = list()
                for alertLevelXml in item.iterfind("alertLevel"):
                    sensor.alertLevels.append(int(alertLevelXml.text))

                # Temperature specific settings.
                sensor.country = str(item.find("weather").attrib["country"])
                sensor.city = str(item.find("weather").attrib["city"])
                sensor.lon = str(item.find("weather").attrib["lon"])
                sensor.lat = str(item.find("weather").attrib["lat"])
                sensor.hasThreshold = (str(item.find("weather").attrib["hasThreshold"]).upper() == "TRUE")
                sensor.threshold = float(item.find("weather").attrib["threshold"])
                orderingStr = str(item.find("weather").attrib["ordering"]).upper()
                if orderingStr == "LT":
                    sensor.ordering = Ordering.LT
                elif orderingStr == "EQ":
                    sensor.ordering = Ordering.EQ
                elif orderingStr == "GT":
                    sensor.ordering = Ordering.GT
                else:
                    raise ValueError("Type of ordering '%s' not valid." % orderingStr)

                # Register location in data collector.
                sensorDataCollector.addLocation(sensor.country, sensor.city, sensor.lon, sensor.lat)
                sensor.dataCollector = sensorDataCollector

            elif sensorType == "humidity".upper():

                sensor = HumidityPollingSensor()

                # these options are needed by the server to
                # differentiate between the registered sensors
                sensor.id = int(item.find("general").attrib["id"])
                sensor.description = str(item.find("general").attrib["description"])
                sensor.alertDelay = int(item.find("general").attrib["alertDelay"])
                sensor.triggerAlert = (str(item.find("general").attrib["triggerAlert"]).upper() == "TRUE")
                sensor.triggerAlertNormal = (str(item.find("general").attrib["triggerAlertNormal"]).upper() == "TRUE")
                sensor.triggerState = 1

                sensor.alertLevels = list()
                for alertLevelXml in item.iterfind("alertLevel"):
                    sensor.alertLevels.append(int(alertLevelXml.text))

                # Temperature specific settings
                sensor.country = str(item.find("weather").attrib["country"])
                sensor.city = str(item.find("weather").attrib["city"])
                sensor.lon = str(item.find("weather").attrib["lon"])
                sensor.lat = str(item.find("weather").attrib["lat"])
                sensor.hasThreshold = (str(item.find("weather").attrib["hasThreshold"]).upper() == "TRUE")
                sensor.threshold = int(item.find("weather").attrib["threshold"])
                orderingStr = str(item.find("weather").attrib["ordering"]).upper()
                if orderingStr == "LT":
                    sensor.ordering = Ordering.LT
                elif orderingStr == "EQ":
                    sensor.ordering = Ordering.EQ
                elif orderingStr == "GT":
                    sensor.ordering = Ordering.GT
                else:
                    raise ValueError("Type of ordering '%s' not valid." % orderingStr)

                # Register location in data collector.
                sensorDataCollector.addLocation(sensor.country, sensor.city, sensor.lon, sensor.lat)
                sensor.dataCollector = sensorDataCollector

            elif sensorType == "forecasttemp".upper():

                sensor = ForecastTempPollingSensor()

                # these options are needed by the server to
                # differentiate between the registered sensors
                sensor.id = int(item.find("general").attrib["id"])
                sensor.description = str(item.find("general").attrib["description"])
                sensor.alertDelay = int(item.find("general").attrib["alertDelay"])
                sensor.triggerAlert = (str(item.find("general").attrib["triggerAlert"]).upper() == "TRUE")
                sensor.triggerAlertNormal = (str(item.find("general").attrib["triggerAlertNormal"]).upper() == "TRUE")
                sensor.triggerState = 1

                sensor.alertLevels = list()
                for alertLevelXml in item.iterfind("alertLevel"):
                    sensor.alertLevels.append(int(alertLevelXml.text))

                # Temperature specific settings
                sensor.country = str(item.find("weather").attrib["country"])
                sensor.city = str(item.find("weather").attrib["city"])
                sensor.lon = str(item.find("weather").attrib["lon"])
                sensor.lat = str(item.find("weather").attrib["lat"])
                sensor.hasThreshold = (str(item.find("weather").attrib["hasThreshold"]).upper() == "TRUE")
                sensor.threshold = float(item.find("weather").attrib["threshold"])
                orderingStr = str(item.find("weather").attrib["ordering"]).upper()
                if orderingStr == "LT":
                    sensor.ordering = Ordering.LT
                elif orderingStr == "EQ":
                    sensor.ordering = Ordering.EQ
                elif orderingStr == "GT":
                    sensor.ordering = Ordering.GT
                else:
                    raise ValueError("Type of ordering '%s' not valid." % orderingStr)

                sensor.kind = str(item.find("weather").attrib["kind"]).upper()
                sensor.day = int(item.find("weather").attrib["day"])

                # Sanity check of kind option.
                if (sensor.kind != "high".upper()
                    and sensor.kind != "low".upper()):
                    raise ValueError("Kind of sensor '%s' not valid." % sensor.kind)

                # Sanity check of day option.
                if sensor.day < 0 and sensor.day > 2:
                    raise ValueError("Day of sensor '%d' not valid." % sensor.day)

                # Register location in data collector.
                sensorDataCollector.addLocation(sensor.country, sensor.city, sensor.lon, sensor.lat)
                sensor.dataCollector = sensorDataCollector

            elif sensorType == "forecastrain".upper():

                sensor = ForecastRainPollingSensor()

                # these options are needed by the server to
                # differentiate between the registered sensors
                sensor.id = int(item.find("general").attrib["id"])
                sensor.description = str(item.find("general").attrib["description"])
                sensor.alertDelay = int(item.find("general").attrib["alertDelay"])
                sensor.triggerAlert = (str(item.find("general").attrib["triggerAlert"]).upper() == "TRUE")
                sensor.triggerAlertNormal = (str(item.find("general").attrib["triggerAlertNormal"]).upper() == "TRUE")
                sensor.triggerState = 1

                sensor.alertLevels = list()
                for alertLevelXml in item.iterfind("alertLevel"):
                    sensor.alertLevels.append(int(alertLevelXml.text))

                # Temperature specific settings
                sensor.country = str(item.find("weather").attrib["country"])
                sensor.city = str(item.find("weather").attrib["city"])
                sensor.lon = str(item.find("weather").attrib["lon"])
                sensor.lat = str(item.find("weather").attrib["lat"])
                sensor.hasThreshold = (str(item.find("weather").attrib["hasThreshold"]).upper() == "TRUE")
                sensor.threshold = int(item.find("weather").attrib["threshold"])
                orderingStr = str(item.find("weather").attrib["ordering"]).upper()
                if orderingStr == "LT":
                    sensor.ordering = Ordering.LT
                elif orderingStr == "EQ":
                    sensor.ordering = Ordering.EQ
                elif orderingStr == "GT":
                    sensor.ordering = Ordering.GT
                else:
                    raise ValueError("Type of ordering '%s' not valid." % orderingStr)

                sensor.day = int(item.find("weather").attrib["day"])

                # Sanity check of day option.
                if sensor.day < 0 and sensor.day > 2:
                    raise ValueError("Day of sensor '%d' not valid." % sensor.day)

                # Register location in data collector.
                sensorDataCollector.addLocation(sensor.country, sensor.city, sensor.lon, sensor.lat)
                sensor.dataCollector = sensorDataCollector

            else:
                raise ValueError("Type of sensor '%s' not valid." % sensorType)

            # check if description is empty
            if len(sensor.description) == 0:
                raise ValueError("Description of sensor %d is empty." % sensor.id)

            # check if the id of the sensor is unique
            for registeredSensor in globalData.sensors:
                if registeredSensor.id == sensor.id:
                    raise ValueError("Id of sensor %d is already taken." % sensor.id)

            if not sensor.triggerAlert and sensor.triggerAlertNormal:
                    raise ValueError("'triggerAlert' for sensor %d "
                                     % sensor.id
                                     + "has to be activated when "
                                     + "'triggerAlertNormal' is activated.")

            globalData.sensors.append(sensor)

    except Exception as e:
        logging.exception("[%s]: Could not parse config." % fileName)
        sys.exit(1)

    random.seed()

    # check if smtp is activated => generate object to send eMail alerts
    if smtpActivated is True:
        globalData.smtpAlert = SMTPAlert(smtpServer, smtpPort, smtpFromAddr, smtpToAddr)
    else:
        globalData.smtpAlert = None

    # check if sensors were found => if not exit
    if not globalData.sensors:
        logging.critical("[%s]: No sensors configured." % fileName)
        sys.exit(1)

    # Start data collector thread.
    # Set thread to daemon.
    # => Thread terminates when main thread terminates.
    logging.info("[%s] Starting data collector thread." % fileName)
    sensorDataCollector.daemon = True
    sensorDataCollector.start()

    # Initialize sensors before starting worker threads.
    logging.info("[%s] Initializing sensors." % fileName)
    for sensor in globalData.sensors:
        if not sensor.initializeSensor():
            logging.critical("[%s]: Not able to initialize sensor." % fileName)
            sys.exit(1)

    # generate object for the communication to the server and connect to it
    globalData.serverComm = ServerCommunication(server,
                                                serverPort,
                                                serverCAFile,
                                                username,
                                                password,
                                                clientCertFile,
                                                clientKeyFile,
                                                globalData)
    connectionRetries = 1
    logging.info("[%s] Connecting to server." % fileName)
    while True:
        # check if 5 unsuccessful attempts are made to connect
        # to the server and if smtp alert is activated
        # => send eMail alert
        if (globalData.smtpAlert is not None
           and (connectionRetries % 5) == 0):
            globalData.smtpAlert.sendCommunicationAlert(connectionRetries)

        if globalData.serverComm.initializeCommunication() is True:
            # if smtp alert is activated
            # => send email that communication problems are solved
            if globalData.smtpAlert is not None:
                globalData.smtpAlert.sendCommunicationAlertClear()

            connectionRetries = 1
            break
        connectionRetries += 1

        logging.critical("[%s]: Connecting to server failed. " % fileName
                         + "Try again in 5 seconds.")
        time.sleep(5)

    # when connected => generate watchdog object to monitor the
    # server connection
    logging.info("[%s] Starting watchdog thread." % fileName)
    watchdog = ConnectionWatchdog(globalData.serverComm,
                                  globalData.pingInterval,
                                  globalData.smtpAlert)
    # set thread to daemon
    # => threads terminates when main thread terminates
    watchdog.daemon = True
    watchdog.start()

    logging.info("[%s] Client started." % fileName)

    # set up sensor executer and execute it
    # (note: we will not return from the executer unless the client
    # is terminated)
    sensorExecuter = SensorExecuter(globalData)
    sensorExecuter.execute()
