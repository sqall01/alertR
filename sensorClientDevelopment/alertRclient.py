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
from lib import SensorDataType, DevSensor, SensorExecuter, SensorEventHandler
from lib import GlobalData
import logging
import time
import random
import xml.etree.ElementTree


# Function creates a path location for the given user input.
def make_path(input_location: str) -> str:
    # Do nothing if the given location is an absolute path.
    if input_location[0] == "/":
        return input_location
    # Replace ~ with the home directory.
    elif input_location[0] == "~":
        pos = -1
        for i in range(1, len(input_location)):
            if input_location[i] == "/":
                continue
            pos = i
            break
        if pos == -1:
            return os.environ["HOME"]
        return os.path.join(os.environ["HOME"], input_location[pos:])
    # Assume we have a given relative path.
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), input_location)


if __name__ == '__main__':

    # generate object of the global needed data
    globalData = GlobalData()

    fileName = os.path.basename(__file__)

    # parse config file, get logfile configurations
    # and initialize logging
    try:
        configRoot = xml.etree.ElementTree.parse(globalData.configFile).getroot()

        logfile = make_path(str(configRoot.find("general").find("log").attrib["file"]))

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
        serverCAFile = os.path.abspath(make_path(str(configRoot.find("general").find("server").attrib["caFile"])))
        if os.path.exists(serverCAFile) is False:
            raise ValueError("Server CA does not exist.")

        # get client certificate and keyfile (if required)
        certificateRequired = (str(configRoot.find("general").find(
                               "client").attrib["certificateRequired"]).upper() == "TRUE")

        if certificateRequired is True:
            clientCertFile = os.path.abspath(
                             make_path(str(configRoot.find("general").find("client").attrib["certFile"])))
            clientKeyFile = os.path.abspath(
                            make_path(str(configRoot.find("general").find("client").attrib["keyFile"])))
            if (os.path.exists(clientCertFile) is False
                    or os.path.exists(clientKeyFile) is False):
                raise ValueError("Client certificate or key does not exist.")

            key_stat = os.stat(clientKeyFile)
            if (key_stat.st_mode & stat.S_IROTH
                    or key_stat.st_mode & stat.S_IWOTH
                    or key_stat.st_mode & stat.S_IXOTH):
                raise ValueError("Client key is accessible by others. Please remove file permissions for others.")

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

        # parse all sensors
        for item in configRoot.find("sensors").iterfind("sensor"):

            sensor = DevSensor()

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

            # Development sensor specific options.
            sensor.sensorDataType = int(item.find("dev").attrib["dataType"])
            if (sensor.sensorDataType != SensorDataType.NONE
                and sensor.sensorDataType != SensorDataType.INT
                and sensor.sensorDataType != SensorDataType.FLOAT):
                raise ValueError("Illegal data type for sensor %d."% sensor.id)

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

    # Initialize sensors before starting worker threads.
    logging.info("[%s] Initializing sensors." % fileName)
    for sensor in globalData.sensors:
        if not sensor.initialize():
            logging.critical("[%s]: Not able to initialize sensor." % fileName)
            sys.exit(1)

    # Starting sensors before starting worker threads.
    logging.info("[%s] Starting sensors." % fileName)
    for sensor in globalData.sensors:
        if not sensor.start():
            logging.critical("[%s]: Not able to start sensor." % fileName)
            sys.exit(1)

    # generate object for the communication to the server and connect to it
    globalData.serverComm = ServerCommunication(server,
                                                serverPort,
                                                serverCAFile,
                                                username,
                                                password,
                                                clientCertFile,
                                                clientKeyFile,
                                                SensorEventHandler(),
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

    # set up sensor executer and execute it
    executer = SensorExecuter(globalData)
    # set thread to daemon
    # => threads terminates when main thread terminates
    executer.daemon = True
    executer.start()

    # set up sensor executer and execute it
    receiver = Receiver(globalData.serverComm)
    # set thread to daemon
    # => threads terminates when main thread terminates
    receiver.daemon = True
    receiver.start()

    # Wait until thread is initialized.
    while not executer.is_initialized:
        time.sleep(0.1)

    logging.info("[%s]: Client started." % fileName)

    # read keyboard input and toggle the sensors accordingly
    while True:

        print("--------")
        for sensor in globalData.sensors:
            dataString = ""
            if sensor.sensorDataType == SensorDataType.NONE:
                dataString = "Current Data: NONE"

            elif sensor.sensorDataType == SensorDataType.INT:
                dataString = "Current Data: (INT) %d" % sensor.sensorData
                dataString += " -> Next Data: %d" % sensor.nextData

            elif sensor.sensorDataType == SensorDataType.FLOAT:
                dataString = "Current Data: (FLOAT) %.3f" % sensor.sensorData
                dataString += " -> Next Data: %.3f" % sensor.nextData

            if sensor.consoleInputState == sensor.triggerState:
                print("Sensor Id: %d - Triggered (%s)" % (sensor.id, dataString))

            else:
                print("Sensor Id: %d - Not Triggered (%s)" % (sensor.id, dataString))

        try:
            localSensorId = int(input("Please enter sensor ID to toggle: "))
        except KeyboardInterrupt:
            break
        except:
            continue

        found = False
        for sensor in globalData.sensors:
            if sensor.id == localSensorId:
                found = True

                sensor.toggle_console_state()
                break
        if not found:
            print("Sensor with local ID '%d' does not exist." % localSensorId)
