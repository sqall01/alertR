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
from lib import Sqlite, Mysql
from lib import SensorAlertExecuter, AlertLevel, RuleElement, RuleSensor, Rule
from lib import CSVBackend
from lib import SMTPAlert
from lib import ManagerUpdateExecuter
import logging
import time
import threading
import random
import xml.etree.ElementTree


# this class is a global configuration class that holds 
# values that are needed all over the server
class GlobalData:

	def __init__(self):

		# version of the used server (and protocol)
		self.version = 0.221

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
			+ "/config/config.xml"

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





# TODO
# parses the alert level rule recursively
def parseRuleRecursively(currentRoot, currentRule):
	
	if currentRoot.tag == "not":
		# TODO
		raise NotImplementedError("Not implemented yet.")

	elif (currentRoot.tag == "and"
		or currentRoot.tag == "or"):

		# parse all "sensor" tags
		for item in currentRoot.iterfind("sensor"):

			ruleSensorNew = RuleSensor()
			ruleSensorNew.username = str(item.attrib["username"])
			ruleSensorNew.remoteSensorId = int(item.attrib["remoteSensorId"])

			# create a wrapper element around the sensor element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "sensor"
			ruleElement.element = ruleSensorNew
			ruleElement.timeTriggeredFor = float(
				item.attrib["timeTriggeredFor"])

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		# parse all "and" tags
		for item in currentRoot.iterfind("and"):

			# create a new "and" rule
			ruleNew = Rule()
			ruleNew.type = "and"

			# create a wrapper element around the rule
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "rule"
			ruleElement.element = ruleNew
			ruleElement.timeTriggeredFor = float(
				item.attrib["timeTriggeredFor"])

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

			# parse rule starting from the new element
			parseRule(item, ruleNew)

		# parse all "or" tags
		for item in currentRoot.iterfind("or"):

			# create a new "or" rule
			temp = Rule()
			temp.type = "or"

			# create a wrapper element around the rule
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleEle = RuleElement()
			ruleEle.type = "rule"
			ruleEle.element = temp
			ruleElement.timeTriggeredFor = float(
				item.attrib["timeTriggeredFor"])

			# add wrapper element to the current rule
			currentRule.elements.append(ruleEle)

			# parse rule starting from the new element
			parseRule(item, temp)

		# parse all "not" tags
		for item in currentRoot.iterfind("not"):
			# TODO
			raise NotImplementedError("Not implemented yet.")


	else:
		raise ValueError("No valid tag found in rule.")




# TODO
# DEBUG
def printRule(ruleElement, tab):

	for i in range(tab):
		print "\t",
	print ("%s (triggeredFor=%.2f)"
		% (ruleElement.element.type, ruleElement.timeTriggeredFor))

	for item in ruleElement.element.elements:

		if item.type == "rule":
			printRule(item, tab+1)
		elif item.type == "sensor":

			for i in range(tab):
				print "\t",
			print ("sensor (triggeredFor=%.2f, user=%s, remoteId=%d)"
				% (item.timeTriggeredFor, item.element.username,
				item.element.remoteSensorId))
		else:
			raise ValueError("Rule has invalid type.")









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
			globalData.smtpAlert = SMTPAlert(smtpServer, smtpPort,
			smtpFromAddr, smtpToAddr)

		# configure user credentials backend
		userBackendMethod = str(
			configRoot.find("storage").find("userBackend").attrib[
			"method"]).upper()
		if userBackendMethod == "CSV":
			globalData.userBackend = CSVBackend(globalData.userBackendCsvFile)

		else:
			raise ValueError("No valid user backend method in config file.")

		# configure storage backend (check which backend is configured)
		userBackendMethod = str(
			configRoot.find("storage").find("storageBackend").attrib[
			"method"]).upper()
		if userBackendMethod == "SQLITE":
			globalData.storage = Sqlite(globalData.storageBackendSqliteFile,
				globalData.version)

		elif userBackendMethod == "MYSQL":

			backendUsername = str(configRoot.find("storage").find(
				"storageBackend").attrib["username"])
			backendPassword = str(configRoot.find("storage").find(
				"storageBackend").attrib["password"])
			backendServer = str(configRoot.find("storage").find(
				"storageBackend").attrib["server"])
			backendPort = int(configRoot.find("storage").find(
				"storageBackend").attrib["port"])
			backendDatabase = str(configRoot.find("storage").find(
				"storageBackend").attrib["database"])

			globalData.storage = Mysql(backendServer, backendPort,
				backendDatabase, backendUsername, backendPassword,
				globalData.version)

		else:
			raise ValueError("No valid storage backend method in config file.")

		# get server configurations
		globalData.serverCertFile = str(configRoot.find("general").find(
				"server").attrib["certFile"])
		globalData.serverKeyFile = str(configRoot.find("general").find(
				"server").attrib["keyFile"])
		port = int(configRoot.find("general").find("server").attrib["port"])

		if (os.path.exists(globalData.serverCertFile) is False
			or os.path.exists(globalData.serverKeyFile) is False):
			raise ValueError("Server certificate or key does not exist.")
		
		# get client configurations
		globalData.useClientCertificates = (str(
			configRoot.find("general").find("client").attrib[
			"useClientCertificates"]).upper() == "TRUE")

		if globalData.useClientCertificates is True:

			globalData.clientCAFile = str(configRoot.find("general").find(
				"client").attrib["clientCAFile"])

			if os.path.exists(globalData.clientCAFile) is False:
				raise ValueError("Client CA file does not exist.")

		# parse all alert levels
		for item in configRoot.find("alertLevels").iterfind("alertLevel"):

			alertLevel = AlertLevel()

			alertLevel.level = int(item.find("general").attrib["level"])
			alertLevel.name = str(item.find("general").attrib["name"])
			alertLevel.triggerAlways = (str(item.find("general").attrib[
				"triggerAlways"]).upper() == "TRUE")

			alertLevel.smtpActivated = (str(item.find("smtp").attrib[
				"emailAlert"]).upper() == "TRUE")

			if ((not smtpActivated)
				and alertLevel.smtpActivated):
				raise ValueError("Alert level can not have email alert"
					+ "activated when smtp is not activated.")

			alertLevel.toAddr = str(item.find("smtp").attrib["toAddr"])






			# TODO
			# read and parse rules
			alertLevel.rulesActivated = (str(item.find("rules").attrib[
				"activated"]).upper() == "TRUE")

			if alertLevel.rulesActivated:



				rulesRoot = item.find("rules")


				# TODO
				# at the moment only for one rule => more rules and id important
				firstRule = rulesRoot.find("rule")


				# get start of the rule ("or", "and" or "not")
				orRule = firstRule.find("or")
				andRule = firstRule.find("and")
				notRule = firstRule.find("not")

				# check that only that only one and/or/not tag is given in rule
				if ((orRule is None and andRule is None and notRule is None)
					or (orRule is None and not andRule is None
						and not notRule is None)
					or (not orRule is None and andRule is None
						and not notRule is None)
					or (not orRule is None and not andRule is None
						and notRule is None)
					or (not orRule is None and not andRule is None
						and not notRule is None)):
					raise ValueError("Only one or/and/not tag "
						+ "is valid as starting part of the rule.")

				# start parsing the rule
				if not orRule is None:

					ruleStart = Rule()
					ruleStart.type = "or"

					# create a wrapper element around the rule
					# to have meta information (i.e. triggered,
					# time when triggered, etc.)
					ruleElement = RuleElement()
					ruleElement.type = "rule"
					ruleElement.element = ruleStart
					ruleElement.timeTriggeredFor = float(
						orRule.attrib["timeTriggeredFor"])

					parseRuleRecursively(orRule, ruleStart)

				elif not andRule is None:

					ruleStart = Rule()
					ruleStart.type = "and"

					# create a wrapper element around the rule
					# to have meta information (i.e. triggered,
					# time when triggered, etc.)
					ruleElement = RuleElement()
					ruleElement.type = "rule"
					ruleElement.element = ruleStart
					ruleElement.timeTriggeredFor = float(
						andRule.attrib["timeTriggeredFor"])

					parseRuleRecursively(andRule, ruleStart)

				elif not notRule is None:

					ruleStart = Rule()
					ruleStart.type = "not"

					# create a wrapper element around the rule
					# to have meta information (i.e. triggered,
					# time when triggered, etc.)
					ruleElement = RuleElement()
					ruleElement.type = "rule"
					ruleElement.element = ruleStart
					ruleElement.timeTriggeredFor = float(
						notRule.attrib["timeTriggeredFor"])

					# TODO
					raise NotImplementedError("Not implemented yet.")

				else:
					raise ValueError("No valid or/and/not tag was found.")



				# TODO
				printRule(ruleElement, 0)



			# check if the alert level only exists once
			for tempAlertLevel in globalData.alertLevels:
				if tempAlertLevel.level == alertLevel.level:
					raise ValueError("Alert level must be unique.")

			globalData.alertLevels.append(alertLevel)

		# check if all alert levels for alert clients that exist in the
		# database are configured in the configuration file
		alertLevelsInDb = globalData.storage.getAllAlertsAlertLevels()
		if alertLevelsInDb == None:
			raise ValueError("Could not get alert client "
				+ "alert levels from database.")
		for alertLevelInDb in alertLevelsInDb:
			found = False
			for alertLevel in globalData.alertLevels:
				if alertLevelInDb[0] == alertLevel.level:
					found = True
					break
			if found:
				continue
			else:
				raise ValueError("An alert level for an alert client exists "
					+ "in the database that is not configured.")

		# check if all alert levels for sensors that exist in the
		# database are configured in the configuration file
		alertLevelsInDb = globalData.storage.getAllSensorsAlertLevels()
		if alertLevelsInDb == None:
			raise ValueError("Could not get sensor alert " 
				+ "levels from database.")
		for alertLevelInDb in alertLevelsInDb:
			found = False
			for alertLevel in globalData.alertLevels:
				if alertLevelInDb[0] == alertLevel.level:
					found = True
					break
			if found:
				continue
			else:
				raise ValueError("An alert level for a sensor exists "
					+ "in the database that is not configured.")

	except Exception as e:
		logging.exception("[%s]: Could not parse config." % fileName)
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