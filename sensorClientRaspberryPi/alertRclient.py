#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import sys
import os
from lib import ServerCommunication, ConnectionWatchdog
from lib import SMTPAlert
from lib import RaspberryPiGPIOPollingSensor, RaspberryPiGPIOInterruptSensor, \
	SensorExecuter
import logging
import time
import ConfigParser
import socket


# this class is a global configuration class that holds 
# values that are needed all over the client
class GlobalData:

	def __init__(self):

		# version of the used client (and protocol)
		self.version = 0.1

		# interval in which a ping should be send when 
		# no data was received/send
		self.pingInterval = 30

		# type of this node/client
		self.nodeType = "sensor"

		# path to the configuration file that holds the parameters
		# that are registered at the server
		self.registeredFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/config/registered"

		# this flags indicates if the client is already registered or not
		self.registered = None

		# path to the configuration file of the client
		self.configFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/config/config.conf"

		# instance of the email alerting object
		self.smtpAlert = None

		# list of all sensors that are managed by this client
		self.sensors = list()


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

		# get server certificate file and check if it does exist
		serverCertificate = os.path.abspath(
			config.get("general", "serverCertificate"))
		if os.path.exists(serverCertificate) is False:
			raise ValueError("Server certificate does not exist.")

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

		# parse all sensors
		for section in config.sections():
			if section.find("sensor") != -1:


				sensorType = config.get(section, "type")
				sensorType = sensorType.upper()

				if sensorType == "POLLING":
					sensor = RaspberryPiGPIOPollingSensor()
					sensor.id = config.getint(section, "id")
					sensor.description = config.get(section, "description")
					sensor.gpioPin = config.getint(section, "gpioPin")
					sensor.alertDelay = config.getint(section, "alertDelay")
					sensor.alertLevel = config.getint(section, "alertLevel")
					sensor.triggerAlert = config.getboolean(section,
						"triggerAlert")
					sensor.triggerAlways = config.getboolean(section,
						"triggerAlways")
					sensor.triggerState = config.getint(section,
						"triggerState")
				elif sensorType == "INTERRUPT":
					sensor = RaspberryPiGPIOInterruptSensor()
					sensor.id = config.getint(section, "id")
					sensor.description = config.get(section, "description")
					sensor.gpioPin = config.getint(section, "gpioPin")
					sensor.alertDelay = config.getint(section, "alertDelay")
					sensor.alertLevel = config.getint(section, "alertLevel")
					sensor.triggerAlert = config.getboolean(section,
						"triggerAlert")
					sensor.triggerAlways = config.getboolean(section,
						"triggerAlways")
					sensor.triggerState = 1
					sensor.delayBetweenTriggers = config.getint(section,
						"delayBetweenTriggers")
					sensor.timeSensorTriggered = config.getint(section,
						"timeSensorTriggered")
					sensor.edge = config.getint(section, "edge")

					# check if the edge detection is correct
					if (sensor.edge != 0 and sensor.edge != 1):
						raise ValueError("Value of edge detection not valid.")
				else:
					raise ValueError("Type of sensor '%s' not valid."
						% section)

				# check if description is empty
				if len(sensor.description) == 0:
					raise ValueError("Description of sensor '%s' is empty."
						% section)

				# check if the id of the sensor is unique
				for registeredSensor in globalData.sensors:
					if registeredSensor.id == sensor.id:
						raise ValueError("Id of sensor '%s'" % section
						+ "is already taken.")				

				globalData.sensors.append(sensor)

		# check if the client has already registered itself at the server
		# with the same data
		if os.path.exists(globalData.registeredFile):

			# parse registered values
			registeredConfig = ConfigParser.RawConfigParser(
				allow_no_value=False)
			registeredConfig.read([globalData.registeredFile])

			hostname = registeredConfig.get("general", "hostname")
			sensorCount = registeredConfig.getint("general", "sensorcount")

			# check if the hostname or sensor count has changed
			if (hostname == socket.gethostname()
				and sensorCount == len(globalData.sensors)):

				# check all sensors if their data has changed since the
				# last registration at the server
				for section in registeredConfig.sections():
					if section.find("sensor") != -1:			

						# get values from the file that are registered at
						# the server
						tempId = registeredConfig.getint(section, "id")
						tempAlertDelay = registeredConfig.getint(section,
							"alertDelay")
						tempDescription = registeredConfig.get(section,
							"description")
						tempAlertLevel = registeredConfig.getint(section,
							"alertLevel")
						tempTriggerAlways = registeredConfig.getboolean(
							section, "triggerAlways")

						# find sensor with the same id parsed from the
						# regular config file
						tempSensor = None
						for sensor in globalData.sensors:
							if sensor.id == tempId:
								tempSensor = sensor
								break
						if tempSensor == None:
							globalData.registered = False
							break

						# check if the sensor data has changed since
						# the last registration
						if (tempAlertDelay != tempSensor.alertDelay
							or tempDescription != tempSensor.description
							or tempAlertLevel != tempSensor.alertLevel
							or tempTriggerAlways != tempSensor.triggerAlways):
							globalData.registered = False
							break

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

	# check if sensors were found => if not exit
	if globalData.sensors == list():
		logging.critical("[%s]: No sensors configured. " % fileName)
		sys.exit(1)

	# generate object for the communication to the server and connect to it
	serverComm = ServerCommunication(server, serverPort,
		serverCertificate, username, password, globalData)
	connectionRetries = 1
	while 1:
		# check if 5 unsuccessful attempts are made to connect
		# to the server and if smtp alert is activated
		# => send eMail alert		
		if (globalData.smtpAlert is not None
			and (connectionRetries % 5) == 0):
			globalData.smtpAlert.sendCommunicationAlert(connectionRetries)

		if serverComm.initializeCommunication() is True:
			# if smtp alert is activated
			# => send email that communication problems are solved
			if not globalData.smtpAlert is None:
				globalData.smtpAlert.sendCommunicationAlertClear()
			
			connectionRetries = 1
			break
		connectionRetries += 1

		logging.critical("[%s]: Connecting to server failed. " % fileName
			+ "Try again in 5 seconds.")
		time.sleep(5)

	# when connected => generate watchdog object to monitor the 
	# server connection
	watchdog = ConnectionWatchdog(serverComm, globalData.pingInterval,
		globalData.smtpAlert)
	# set thread to daemon
	# => threads terminates when main thread terminates	
	watchdog.daemon = True
	watchdog.start()

	# set up sensor executer and execute it
	# (note: we will not return from the executer unless the client
	# is terminated)
	sensorExecuter = SensorExecuter(serverComm, globalData)
	sensorExecuter.execute()