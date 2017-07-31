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
from lib import RaspberryPiGPIOAlert
from lib import GlobalData
import logging
import time
import socket
import random
import RPi.GPIO as GPIO
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
		configRoot = xml.etree.ElementTree.parse(
			globalData.configFile).getroot()

		logfile = makePath(
			str(configRoot.find("general").find("log").attrib["file"]))

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
		serverCAFile = os.path.abspath(makePath(
			str(configRoot.find("general").find("server").attrib["caFile"])))
		if os.path.exists(serverCAFile) is False:
			raise ValueError("Server CA does not exist.")

		# get client certificate and keyfile (if required)
		certificateRequired = (str(
			configRoot.find("general").find("client").attrib[
			"certificateRequired"]).upper()	== "TRUE")

		if certificateRequired is True:
			clientCertFile = os.path.abspath(makePath(str(
			configRoot.find("general").find("client").attrib["certFile"])))
			clientKeyFile = os.path.abspath(makePath(str(
			configRoot.find("general").find("client").attrib["keyFile"])))
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

		# Get connection settings.
		temp = (str(
			configRoot.find("general").find("connection").attrib[
			"persistent"]).upper()	== "TRUE")
		if temp:
			globalData.persistent = 1
		else:
			globalData.persistent = 0

		# parse smtp options if activated
		smtpActivated = (str(
			configRoot.find("smtp").find("general").attrib[
			"activated"]).upper()	== "TRUE")
		if smtpActivated is True:
			smtpServer = str(
				configRoot.find("smtp").find("server").attrib["host"])
			smtpPort = int(
				configRoot.find("smtp").find("server").attrib["port"])
			smtpFromAddr = str(
				configRoot.find("smtp").find("general").attrib["fromAddr"])
			smtpToAddr = str(
				configRoot.find("smtp").find("general").attrib["toAddr"])

		# parse all alerts
		for item in configRoot.find("alerts").iterfind("alert"):

			alert = RaspberryPiGPIOAlert()

			# get gpio pin settings
			alert.gpioPin = int(item.find("gpio").attrib["gpioPin"])
			if int(item.find("gpio").attrib["gpioPinStateNormal"]) == 1:
				alert.gpioPinStateNormal = GPIO.HIGH
			else:
				alert.gpioPinStateNormal = GPIO.LOW
			if int(item.find("gpio").attrib["gpioPinStateTriggered"]) == 1:
				alert.gpioPinStateTriggered = GPIO.HIGH
			else:
				alert.gpioPinStateTriggered = GPIO.LOW

			# these options are needed by the server to
			# differentiate between the registered alerts
			alert.id = int(item.find("general").attrib["id"])
			alert.description = str(item.find("general").attrib["description"])

			alert.alertLevels = list()
			for alertLevelXml in item.iterfind("alertLevel"):
				alert.alertLevels.append(int(alertLevelXml.text))

			# check if description is empty
			if len(alert.description) == 0:
				raise ValueError("Description of alert %d is empty."
					% alert.id)

			# check if the id of the alert is unique
			for registeredAlert in globalData.alerts:
				if registeredAlert.id == alert.id:
					raise ValueError("Id of alert %d"
						% alert.id + "is already taken.")

			globalData.alerts.append(alert)

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

	# generate object for the communication to the server and connect to it
	globalData.serverComm = ServerCommunication(server, serverPort,
		serverCAFile, username, password, clientCertFile, clientKeyFile,
		globalData)
	connectionRetries = 1
	logging.info("[%s] Connecting to server." % fileName)
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
	logging.info("[%s] Starting watchdog thread." % fileName)
	watchdog = ConnectionWatchdog(globalData.serverComm,
		globalData.pingInterval, globalData.smtpAlert)
	# set thread to daemon
	# => threads terminates when main thread terminates
	watchdog.daemon = True
	watchdog.start()

	# initialize all alerts
	logging.info("[%s] Initializing alerts." % fileName)
	for alert in globalData.alerts:
		alert.initializeAlert()

	logging.info("[%s] Client started." % fileName)

	# generate receiver to handle incoming data (for example status updates)
	receiver = Receiver(globalData.serverComm)
	receiver.run()