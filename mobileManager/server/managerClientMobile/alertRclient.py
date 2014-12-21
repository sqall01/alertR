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
from lib import LocalServerSession, ThreadedUnixStreamServer
from lib import Mysql
from lib import SMTPAlert
import logging
import time
import socket
import random
import threading
import stat
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
		self.nodeType = "manager"

		# path to the configuration file that holds the parameters
		# that are registered at the server
		self.registeredFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/config/registered"

		# this flags indicates if the client is already registered or not
		self.registered = None

		# path to the configuration file of the client
		self.configFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/config/config.xml"

		# path to the unix socket which is used to communicate
		# with the web page
		self.unixSocketFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/config/localsocket"

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

		# this is a list of all alert level objects that are received
		self.alertLevels = list()

		# this variable holds the object of the server communication
		self.serverComm = None

		# instance of the storage backend
		self.storage = None


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

		# get manager settings
		globalData.description = str(
			configRoot.find("manager").find("general").attrib[
			"description"])

		# configure storage backend (check which backend is configured)
		userBackendMethod = str(
			configRoot.find("manager").find("storage").attrib[
			"method"])
		if userBackendMethod.upper() == "MYSQL":

			backendUsername = str(
			configRoot.find("manager").find("storage").attrib[
			"username"])
			backendPassword = str(
			configRoot.find("manager").find("storage").attrib[
			"password"])
			backendServer = str(
			configRoot.find("manager").find("storage").attrib[
			"server"])
			backendPort = int(
			configRoot.find("manager").find("storage").attrib[
			"port"])
			backendDatabase = str(
			configRoot.find("manager").find("storage").attrib[
			"database"])

			globalData.storage = Mysql(backendServer, backendPort,
				backendDatabase, backendUsername, backendPassword)
		else:
			raise ValueError("No valid storage backend method in config file.")

		# check if the client has already registered itself at the server
		# with the same data
		if os.path.exists(globalData.registeredFile):

			regConfigRoot = xml.etree.ElementTree.parse(
				globalData.registeredFile).getroot()

			hostname = logfile = str(regConfigRoot.find("general").find(
				"client").attrib["host"])			

			# check if the hostname
			if (hostname == socket.gethostname()):

				description = str(
					regConfigRoot.find("manager").find("general").attrib[
					"description"])

				# check if manager settings had changed since the
				# last registration at the server
				if description == globalData.description:

					# check if the registered value has changed
					# during the checks => if not set it to True
					if globalData.registered == None:
						globalData.registered = True

				else:
					globalData.registered = False

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

	# start local server process
	while 1:
		try:

			# remove unix socket file (if exists)
			try:
				os.remove(globalData.unixSocketFile)
			except OSError:
				pass

			# listen to the unix socket
			server = ThreadedUnixStreamServer(globalData,
				globalData.unixSocketFile, LocalServerSession)

			# make socket writeable by everyone
			os.chmod(globalData.unixSocketFile, stat.S_IRUSR | stat.S_IWUSR
				| stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
				| stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)

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

	# generate receiver to handle incoming data (for example status updates)
	receiver = Receiver(globalData.serverComm)
	receiver.run()