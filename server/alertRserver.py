#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import sys
import os
from lib import ServerSession, ConnectionWatchdog, ThreadedTCPServer
from lib import Sqlite, Mysql, Postgresql
from lib import SensorAlertExecuter, AlertLevel
from lib import CSVBackend
from lib import SMTPAlert
from lib import ManagerUpdateExecuter
import logging
import time
import threading
import random
import ConfigParser


# this class is a global configuration class that holds 
# values that are needed all over the server
class GlobalData:

	def __init__(self):

		# version of the used server (and protocol)
		self.version = 0.2

		# list of all sessions that are handled by the server
		self.serverSessions = list()

		# instance of the storage backend
		self.storage = None

		# instance of the user credential backend
		self.userBackend = None

		# instance of the thread that handles sensor alerts
		self.sensorAlertExecuter = None

		# instance of the thread that handles manager updates
		self.managerUpdateExecuter = None

		# this is the time in seconds when the client times out
		self.connectionTimeout = 60

		# this is the interval in seconds in which the managers
		# are sent updates of the clients (at least)
		self.managerUpdateInterval = 60.0

		# path to the configuration file of the client
		self.configFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/config/config.conf"

		# path to the csv user credentials file (if csv is used as backend)
		self.userBackendCsvFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/config/users.csv"

		# path to the sqlite database file (if sqlite is used as backend)
		self.storageBackendSqliteFile = os.path.dirname(os.path.abspath(
			__file__)) + "/config/database.db"

		# location of the certifiacte file
		self.serverCertFile = None

		# location of the key file
		self.serverKeyFile = None

		# do clients authenticate themselves via certificates
		self.useClientCertificates = None

		# path to CA that is used to authenticate clients
		self.clientCAFile = None

		# instance of the email alerting object
		self.smtpAlert = None

		# a list of all alert leves that are configured on this server
		self.alertLevels = list()

		# time the server is waiting on receives until a time out occurs
		self.serverReceiveTimeout = 20.0

		# list and lock of/for the asynchronous option executer
		self.asyncOptionExecutersLock = threading.BoundedSemaphore(1)
		self.asyncOptionExecuters = list()


if __name__ == '__main__':

	# generate object of the global needed data
	globalData = GlobalData()

	fileName = os.path.basename(__file__)

	# parse config file
	try:
		config = ConfigParser.RawConfigParser(allow_no_value=False)

		# get config file
		config.read([globalData.configFile])

		logfile = config.get("general", "logfile")

		# parse chosen log level
		tempLoglevel = config.get("general", "loglevel")
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

		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
			datefmt='%m/%d/%Y %H:%M:%S', filename=logfile, 
			level=loglevel)

		# configure smtp alert if activated
		smtpActivated = config.getboolean("smtp", "smtpActivated")
		if smtpActivated is True:
			smtpServer = config.get("smtp", "server")
			smtpPort = config.getint("smtp", "serverPort")
			smtpFromAddr = config.get("smtp", "fromAddr")
			smtpToAddr = config.get("smtp", "toAddr")
			globalData.smtpAlert = SMTPAlert(smtpServer, smtpPort,
			smtpFromAddr, smtpToAddr)

		# configure user credentials backend
		userBackendMethod = config.get("userBackend", "method")
		if userBackendMethod.upper() == "CSV":
			globalData.userBackend = CSVBackend(globalData.userBackendCsvFile)
		else:
			raise ValueError("No valid user backend method in config file.")

		# configure storage backend (check which backend is configured)
		userBackendMethod = config.get("storage", "method")
		if userBackendMethod.upper() == "SQLITE":
			globalData.storage = Sqlite(globalData.storageBackendSqliteFile,
				globalData.version)
		elif userBackendMethod.upper() == "MYSQL":

			backendUsername = config.get("storage", "username")
			backendPassword = config.get("storage", "password")
			backendServer = config.get("storage", "server")
			backendPort = config.getint("storage", "port")
			backendDatabase = config.get("storage", "database")

			globalData.storage = Mysql(backendServer, backendPort,
				backendDatabase, backendUsername, backendPassword,
				globalData.version)
		elif userBackendMethod.upper() == "POSTGRESQL":

			backendUsername = config.get("storage", "username")
			backendPassword = config.get("storage", "password")
			backendServer = config.get("storage", "server")
			backendPort = config.getint("storage", "port")
			backendDatabase = config.get("storage", "database")

			globalData.storage = Postgresql(backendServer, backendPort,
				backendDatabase, backendUsername, backendPassword,
				globalData.version)

		else:
			raise ValueError("No valid storage backend method in config file.")

		# get server configurations
		globalData.serverCertFile = config.get("server", "certificateFile")
		globalData.serverKeyFile = config.get("server", "keyFile")
		if (os.path.exists(globalData.serverCertFile) is False
			or os.path.exists(globalData.serverKeyFile) is False):
			raise ValueError("Server certificate or key does not exist.")
		port = config.getint("server", "port")
		globalData.useClientCertificates = config.getboolean("server",
			"useClientCertificates")
		if globalData.useClientCertificates is True:
			globalData.clientCAFile = config.get("server", "clientCAFile")
			if os.path.exists(globalData.clientCAFile) is False:
				raise ValueError("Client CA does not exist.")

		# parse all alert levels
		for section in config.sections():
			if section.find("alertLevel") != -1:

				alertLevel = AlertLevel()
				alertLevel.level = config.getint(section, "level")
				alertLevel.smtpActivated = config.getboolean(section,
					"emailAlert")
				if ((not smtpActivated)
					and alertLevel.smtpActivated):
					raise ValueError("Alert level can not have email alert"
						+ "activated when smtp is not activated.")
				alertLevel.toAddr = config.get(section, "toAddr")

				# check if the alert level only exists once
				for tempAlertLevel in globalData.alertLevels:
					if tempAlertLevel.level == alertLevel.level:
						raise ValueError("Alert level must be unique.")

				globalData.alertLevels.append(alertLevel)

		# check if all alert levels that exist in the database are configured
		# in the configuration file
		alertLevelsInDb = globalData.storage.getAllAlertLevels()
		if alertLevelsInDb == None:
			raise ValueError("Could not get alert levels from database.")
		for alertLevelInDb in alertLevelsInDb:
			found = False
			for alertLevel in globalData.alertLevels:
				if alertLevelInDb[0] == alertLevel.level:
					found = True
					break
			if found:
				continue
			else:
				raise ValueError("Alert level is in database that is not "
					+ "configured.")

	except Exception as e:
		print "Config could not be parsed."
		print e
		sys.exit(1)

	random.seed()

	# start the thread that handles all sensor alerts
	globalData.sensorAlertExecuter = SensorAlertExecuter(globalData)
	# set thread to daemon
	# => threads terminates when main thread terminates	
	globalData.sensorAlertExecuter.daemon = True
	globalData.sensorAlertExecuter.start()

	# start the thread that handles the manager updates
	globalData.managerUpdateExecuter = ManagerUpdateExecuter(globalData)
	# set thread to daemon
	# => threads terminates when main thread terminates	
	globalData.managerUpdateExecuter.daemon = True
	globalData.managerUpdateExecuter.start()

	# start server process
	while 1:
		try:
			server = ThreadedTCPServer(globalData, ('0.0.0.0', port),
				ServerSession)
			break
		except Exception as e:
			logging.exception("[%s]: Starting server failed. " % fileName
			+ "Try again in 5 seconds.")
			time.sleep(5)

	serverThread = threading.Thread(target=server.serve_forever)
	# set thread to daemon
	# => threads terminates when main thread terminates	
	serverThread.daemon =True
	serverThread.start()

	# start a watchdog thread that controls all server sessions
	watchdog = ConnectionWatchdog(globalData, globalData.connectionTimeout)
	# set thread to daemon
	# => threads terminates when main thread terminates	
	watchdog.daemon = True
	watchdog.start()

	logging.info("[%s] server started." % fileName)

	# handle requests in an infinity loop
	while True:
		server.handle_request()