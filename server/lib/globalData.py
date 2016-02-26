#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import os
import threading


# this class is a global configuration class that holds 
# values that are needed all over the client
class GlobalData:

	def __init__(self):

		# version of the used server (and protocol)
		self.version = 0.301

		# revision of the used server
		self.rev = 0

		# name of this server
		self.name = "alertR Server"

		# the instance of this server
		self.instance = "server"

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

		# This is the time a "persistent" client does not count as 
		# timed out if it disconnects from the server.
		self.gracePeriodTimeout = 20

		# The time a reminder of timed out sensors is raised.
		self.timeoutReminderTime = 1800.0

		# this is the interval in seconds in which the managers
		# are sent updates of the clients (at least)
		self.managerUpdateInterval = 60.0

		# path to the configuration file of the client
		self.configFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/../config/config.xml"

		# path to the csv user credentials file (if csv is used as backend)
		self.userBackendCsvFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/../config/users.csv"

		# path to the sqlite database file (if sqlite is used as backend)
		self.storageBackendSqliteFile = os.path.dirname(os.path.abspath(
			__file__)) + "/../config/database.db"

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

		# List of the server's internal sensors.
		self.internalSensors = list()

		# Instance of the connection watchdog object.
		self.connectionWatchdog = None