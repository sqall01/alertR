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
from lib import CtfWatchdogSensor, SensorExecuter
import logging
import time
import socket
import random
import xml.etree.ElementTree


# this class is a global configuration class that holds 
# values that are needed all over the client
class GlobalData:

	def __init__(self):

		# version of the used client (and protocol)
		self.version = 0.22

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
			+ "/config/config.xml"

		# instance of the email alerting object
		self.smtpAlert = None

		# this variable holds the object of the server communication
		self.serverComm = None

		# list of all sensors that are managed by this client
		self.sensors = list()


if __name__ == '__main__':

	# generate object of the global needed data
	globalData = GlobalData()

	fileName = os.path.basename(__file__)

	# parse config file, get logfile configurations
	# and initialize logging
	try:
		configRoot = xml.etree.ElementTree.parse(
			globalData.configFile).getroot()

		logfile = str(configRoot.find("general").find("log").attrib["file"])

		# parse chosen log level
		tempLoglevel = str(
			configRoot.find("general").find("log").attrib["level"])
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
			datefmt='%m/%d/%Y %H:%M:%S', filename=logfile, 
			level=loglevel)

	except Exception as e:
		print "Config could not be parsed."
		print e
		sys.exit(1)

	# parse the rest of the config with initialized logging
	try:

		# check if config and client version are compatible
		version = float(configRoot.attrib["version"])
		if version != globalData.version:
			raise ValueError("Config version '%.3f' not "
				% version
				+ "compatible with client version '%.3f'."
				% globalData.version)

		# parse server configurations
		server = str(configRoot.find("general").find("server").attrib["host"])
		serverPort = int(
			configRoot.find("general").find("server").attrib["port"])

		# get server certificate file and check if it does exist
		serverCAFile = os.path.abspath(
			str(configRoot.find("general").find("server").attrib["caFile"]))
		if os.path.exists(serverCAFile) is False:
			raise ValueError("Server CA does not exist.")

		# get client certificate and keyfile (if required)
		certificateRequired = (str(
			configRoot.find("general").find("client").attrib[
			"certificateRequired"]).upper()	== "TRUE")

		if certificateRequired is True:
			clientCertFile = os.path.abspath(str(
			configRoot.find("general").find("client").attrib["certFile"]))
			clientKeyFile = os.path.abspath(str(
			configRoot.find("general").find("client").attrib["keyFile"]))
			if (os.path.exists(clientCertFile) is False
				or os.path.exists(clientKeyFile) is False):
				raise ValueError("Client certificate or key does not exist.")
		else:
			clientCertFile = None
			clientKeyFile = None
		
		# get user credentials
		username = str(
			configRoot.find("general").find("credentials").attrib["username"])
		password = str(
			configRoot.find("general").find("credentials").attrib["password"])

		# parse smtp options if activated
		smtpActivated = (str(
			configRoot.find("smtp").find("general").attrib[
			"activated"]).upper() == "TRUE")
		if smtpActivated is True:
			smtpServer = str(
				configRoot.find("smtp").find("server").attrib["host"])
			smtpPort = int(
				configRoot.find("smtp").find("server").attrib["port"])
			smtpFromAddr = str(
				configRoot.find("smtp").find("general").attrib["fromAddr"])
			smtpToAddr = str(
				configRoot.find("smtp").find("general").attrib["toAddr"])

		# parse all sensors
		for item in configRoot.find("sensors").iterfind("sensor"):

			sensor = CtfWatchdogSensor()

			# these options are needed by the server to
			# differentiate between the registered sensors
			sensor.id = int(item.find("general").attrib["id"])
			sensor.description = str(item.find("general").attrib[
				"description"])
			sensor.alertDelay = int(item.find("general").attrib["alertDelay"])
			sensor.triggerAlert = (str(item.find("general").attrib[
				"triggerAlert"]).upper() == "TRUE")
			sensor.triggerState = int(item.find("general").attrib[
				"triggerState"])

			sensor.alertLevels = list()
			for alertLevelXml in item.iterfind("alertLevel"):
				sensor.alertLevels.append(int(alertLevelXml.text))

			# ctf specific options
			sensor.timeout = int(item.find("ctf").attrib[
				"timeout"])
			sensor.intervalToCheck = int(item.find("ctf").attrib[
				"intervalToCheck"])
			sensor.host = str(item.find("ctf").attrib[
				"host"])
			sensor.port = int(item.find("ctf").attrib[
				"port"])
			sensor.execute = str(item.find("ctf").attrib[
				"execute"])

			# check if description is empty
			if len(sensor.description) == 0:
				raise ValueError("Description of sensor '%s' is empty."
					% section)

			# check if the id of the sensor is unique
			for registeredSensor in globalData.sensors:
				if registeredSensor.id == sensor.id:
					raise ValueError("Id of sensor '%s'"
						% section + "is already taken.")				

			globalData.sensors.append(sensor)

		# check if the client has already registered itself at the server
		# with the same data
		if os.path.exists(globalData.registeredFile):

			regConfigRoot = xml.etree.ElementTree.parse(
				globalData.registeredFile).getroot()

			hostname = logfile = str(regConfigRoot.find("general").find(
				"client").attrib["host"])			

			# check if the hostname
			if (hostname == socket.gethostname()):

				# check all sensors if their data has changed since the
				# last registration at the server
				sensorCount = 0
				for item in regConfigRoot.find("sensors").iterfind("sensor"):
					sensorCount += 1

					# get values from the file that are registered at
					# the server
					tempId = int(item.find("general").attrib["id"])
					tempDescription = str(item.find("general").attrib[
						"description"])
					tempAlertDelay = int(item.find("general").attrib[
						"alertDelay"])

					tempAlertLevels = list()
					for alertLevelXml in item.iterfind("alertLevel"):
						tempAlertLevels.append(int(alertLevelXml.text))

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

					# check if the alert levels of the sensors
					# have changed
					for alertLevel in tempSensor.alertLevels:
						if not alertLevel in tempAlertLevels:
							globalData.registered = False
							break
					for tempAlertLevel in tempAlertLevels:
						if not tempAlertLevel in tempSensor.alertLevels:
							globalData.registered = False
							break
					if globalData.registered is False:
						break

					# check if the sensor data has changed since
					# the last registration
					if (tempAlertDelay != tempSensor.alertDelay
						or tempDescription != tempSensor.description):
						globalData.registered = False
						break

				# check if the count of the sensors has changed
				if sensorCount != len(globalData.sensors):
					globalData.registered = False

				# check if the registered value has changed
				# during the checks => if not set it to True
				if globalData.registered == None:
					globalData.registered = True

			else:
				globalData.registered = False

		else:
			globalData.registered = False

	except Exception as e:
		logging.exception("[%s]: Could not parse config." % fileName)
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

	# check if sensors were found => if not exit
	if globalData.sensors == list():
		logging.critical("[%s]: No sensors configured. " % fileName)
		sys.exit(1)

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
		time.sleep(5)

	# when connected => generate watchdog object to monitor the 
	# server connection
	watchdog = ConnectionWatchdog(globalData.serverComm,
		globalData.pingInterval, globalData.smtpAlert)
	# set thread to daemon
	# => threads terminates when main thread terminates	
	watchdog.daemon = True
	watchdog.start()

	# set up sensor executer and execute it
	# (note: we will not return from the executer unless the client
	# is terminated)
	sensorExecuter = SensorExecuter(globalData.serverComm, globalData)
	sensorExecuter.execute()