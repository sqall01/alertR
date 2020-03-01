#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import sys
import os
from lib import ConnectionWatchdog, CSVWatchdog
from lib import ServerSession, ThreadedTCPServer
from lib import VersionInformerSensor
from lib import SensorAlertExecuter
from lib import ManagerUpdateExecuter
from lib import GlobalData
from lib import SurveyExecuter
from lib import parse_config
import time
import threading
import random


if __name__ == '__main__':

    # generate object of the global needed data
    globalData = GlobalData()

    fileName = os.path.basename(__file__)

    # Parse config.
    if not parse_config(globalData):
        sys.exit(1)

    globalData.logger.info("[%s]: Parsing configuration succeeded." % fileName)

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
            server = ThreadedTCPServer(globalData, ('0.0.0.0', globalData.server_port), ServerSession)
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
    if globalData.survey_activated:

        # Check if version informer sensor is used.
        uses_version_informer = False
        for internal_sensor in globalData.internalSensors:
            if type(internal_sensor) == VersionInformerSensor:
                uses_version_informer = True

        globalData.logger.info("[%s] Starting survey executer thread." % fileName)
        surveyExecuter = SurveyExecuter(uses_version_informer, globalData.update_url, globalData)
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
