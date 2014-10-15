#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import sys
import os
from lib import ServerCommunication, ConnectionWatchdog, Receiver
from lib import SMTPAlert
from lib import ScreenUpdater
from lib import Console
import logging
import time
import ConfigParser
import socket
import random


# this class is a global configuration class that holds 
# values that are needed all over the client
class GlobalData:

	def __init__(self):

		# version of the used client (and protocol)
		self.version = 0.2

		# interval in which a ping should be send when 
		# no data was received/send		
		self.pingInterval = 30

		# type of this node/client
		self.nodeType = "manager"

		# path to the configuration file that holds the parameters
		# that are registered at the server
		self.registeredFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/config/registered"

		# this flags indicates if the client is already registered or not
		self.registered = None

		# path to the configuration file of the client
		self.configFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/config/config.conf"

		# this flags indicate if email alerts via smtp are active
		self.smtpAlert = None

		# this holds the description of this client
		self.description = None

		# this is a list of all option objects that are received
		self.options = list()

		# this is a list of all node objects that are received
		self.nodes = list()

		# this is a list of all sensor objects that are received
		self.sensors = list()

		# this is a list of all manager objects that are received
		self.managers = list()

		# this is a list of all alert objects that are received
		self.alerts = list()

		# this is a list of all sensor alert objects that are received
		self.sensorAlerts = list()

		# this is the instance of the screen updateter object that is
		# responsible of updating the screen
		self.screenUpdater = None

		# this variable holds the object of the server communication
		self.serverComm = None

		# this is the time in seconds when the screen should be locked
		# (if it was unlocked by the user)
		self.unlockedScreenTimeout = 20

		# this is an instance of the console object that handles
		# the screen
		self.console = None

		# this is a list of pins that allow the user to unlock the screen
		# of the manager
		self.pins = list()


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
		server = config.get("general", "server")
		serverPort = config.getint("general", "serverPort")
		globalData.description = config.get("general", "description")

		# get server certificate file and check if it does exist
		serverCAFile = os.path.abspath(
			config.get("general", "serverCAFile"))
		if os.path.exists(serverCAFile) is False:
			raise ValueError("Server CA does not exist.")

		# get client certificate and keyfile (if required)
		certificateRequired = config.getboolean("general",
			"certificateRequired")
		if certificateRequired is True:
			clientCertFile = os.path.abspath(config.get("general",
				"certificateFile"))
			clientKeyFile = os.path.abspath(config.get("general",
				"keyFile"))
			if (os.path.exists(clientCertFile) is False
				or os.path.exists(clientKeyFile) is False):
				raise ValueError("Client certificate or key does not exist.")
		else:
			clientCertFile = None
			clientKeyFile = None

		# get user credentials
		username = config.get("general", "username")
		password = config.get("general", "password")

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

		# parse smtp options if activated
		smtpActivated = config.getboolean("smtp", "smtpActivated")
		if smtpActivated is True:
			smtpServer = config.get("smtp", "server")
			smtpPort = config.getint("smtp", "serverPort")
			smtpFromAddr = config.get("smtp", "fromAddr")
			smtpToAddr = config.get("smtp", "toAddr")

		# parse pins
		tempPins = config.get("keypad", "pins")
		globalData.pins = tempPins.strip().replace(" ", "").split(",")
		# remove empty pins
		for pin in globalData.pins:
			if pin == "":
				globalData.pins.remove(pin)

		# check if the client has already registered itself at the server
		# with the same data
		if os.path.exists(globalData.registeredFile):

			# parse registered values
			registeredConfig = ConfigParser.RawConfigParser(
				allow_no_value=False)
			registeredConfig.read([globalData.registeredFile])

			hostname = registeredConfig.get("general", "hostname")
			description = registeredConfig.get("general", "description")

			# check if the hostname
			if (hostname == socket.gethostname()
				and globalData.description == description):

				# check if the registered value has changed
				# during the checks => if not set it to True
				if globalData.registered == None:
					globalData.registered = True

			else:
				globalData.registered = False

		else:
			globalData.registered = False


	except Exception as e:
		print "Config could not be parsed."
		print e
		sys.exit(1)

	random.seed()

	# check if smtp is activated => generate object to send eMail alerts
	if smtpActivated is True:
		globalData.smtpAlert = SMTPAlert(smtpServer, smtpPort,
			smtpFromAddr, smtpToAddr)
	else:
		globalData.smtpAlert = None

	# initialize logging
	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
		datefmt='%m/%d/%Y %H:%M:%S', filename=logfile, 
		level=loglevel)

	# generate a screen updater thread (that generates the GUI)
	globalData.screenUpdater = ScreenUpdater(globalData)
	# set thread to daemon
	# => threads terminates when main thread terminates	
	globalData.screenUpdater.daemon = True
	globalData.screenUpdater.start()

	# generate object for the communication to the server and connect to it
	globalData.serverComm = ServerCommunication(server, serverPort,
		serverCAFile, username, password, clientCertFile, clientKeyFile,
		globalData)
	connectionRetries = 1
	while 1:
		# check if 5 unsuccessful attempts are made to connect
		# to the server and if smtp alert is activated
		# => send eMail alert		
		if (globalData.smtpAlert is not None
			and (connectionRetries % 5) == 0):
			globalData.smtpAlert.sendCommunicationAlert(connectionRetries)

		if globalData.serverComm.initializeCommunication() is True:
			# if smtp alert is activated
			# => send email that communication problems are solved
			if not globalData.smtpAlert is None:
				globalData.smtpAlert.sendCommunicationAlertClear()

			connectionRetries = 1
			break
		connectionRetries += 1

		logging.critical("[%s]: Connecting to server failed. " % fileName
			+ "Try again in 5 seconds.")
		print "Connecting to server failed. Try again in 5 seconds."
		time.sleep(5)

	# when connected => generate watchdog object to monitor the 
	# server connection
	watchdog = ConnectionWatchdog(globalData.serverComm,
		globalData.pingInterval, globalData.smtpAlert)
	# set thread to daemon
	# => threads terminates when main thread terminates	
	watchdog.daemon = True
	watchdog.start()

	# generate receiver to handle incoming data (for example status updates)
	receiver = Receiver(globalData.serverComm)
	# set thread to daemon
	# => threads terminates when main thread terminates	
	receiver.daemon = True
	receiver.start()

	# generate the console object and start it
	# (does not return unless it is exited)
	globalData.console = Console(globalData)
	globalData.console.startConsole()