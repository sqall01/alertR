#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import logging
import os
import threading
import time
import json
from events import EventSensorAlert, EventNewVersion
from events import EventStateChange, EventConnectedChange, EventSensorTimeOut
from events import EventNewOption, EventNewNode, EventNewSensor
from events import EventNewAlert, EventNewManager
from events import EventChangeOption, EventChangeNode, EventChangeSensor
from events import EventChangeAlert, EventChangeManager
from events import EventDeleteNode, EventDeleteSensor, EventDeleteAlert
from events import EventDeleteManager
from serverObjects import Option, Node, Sensor, Alert, Manager, AlertLevel
from localObjects import SensorDataType


# internal abstract class for new storage backends
class _Storage():

	# creates objects from the data in the database 
	# (should only be called during the initial connection to the database)
	#
	# no return value but raise exception if it fails
	def createObjectsFromDb(self):
		raise NotImplemented("Function not implemented yet.")


	# creates the database (should only be called if the database
	# does not exist)
	#
	# no return value but raise exception if it fails
	def createStorage(self):
		raise NotImplemented("Function not implemented yet.")


	# updates the received server information
	#
	# return True or False
	def updateServerInformation(self, options, nodes, sensors, alerts,
		managers, alertLevels):
		raise NotImplemented("Function not implemented yet.")


# class for using mysql as storage backend
class Mysql(_Storage):

	def __init__(self, host, port, database, username, password, globalData):

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# needed mysql parameters
		self.host = host
		self.port = port
		self.database = database
		self.username = username
		self.password = password

		# get global configured data
		self.globalData = globalData
		self.sensorAlertLifeSpan = self.globalData.sensorAlertLifeSpan
		self.events = self.globalData.events
		self.eventsLifeSpan = self.globalData.eventsLifeSpan
		self.version = self.globalData.version
		self.rev = self.globalData.rev
		self.options = self.globalData.options
		self.nodes = self.globalData.nodes
		self.sensors = self.globalData.sensors
		self.alerts = self.globalData.alerts
		self.managers = self.globalData.managers
		self.alertLevels = self.globalData.alertLevels

		# local copy of elements in the database (to make the update faster)
		self.optionsCopy = list()
		self.nodesCopy = list()
		self.sensorsCopy = list()
		self.alertsCopy = list()
		self.managersCopy = list()
		self.alertLevelsCopy = list()

		# mysql lock
		self.dbLock = threading.Semaphore(1)

		self.conn = None
		self.cursor = None

		# connect to the database
		self._openConnection()

		# check if version of database is the same as version of client
		self.cursor.execute("SHOW TABLES LIKE 'internals'")
		result = self.cursor.fetchall()
		if len(result) != 0:

			self.cursor.execute("SELECT type, value FROM internals")
			result = self.cursor.fetchall()

			dbVersion = 0.0
			dbRev = 0.0
			for internalTuple in result: 
				internalType = internalTuple[0]
				internalValue = internalTuple[1]

				if internalType.upper() == "VERSION":
					dbVersion = internalValue
					continue
				elif internalType.upper() == "REV":
					dbRev = internalValue
					continue

			# if version is not the same of db and client
			# => delete event tables
			if (dbVersion != self.version
				or dbRev != self.rev):
				
				self.cursor.execute("DROP TABLE IF EXISTS eventsNewVersion")
				self.cursor.execute("DROP TABLE IF EXISTS eventsSensorAlert")
				self.cursor.execute("DROP TABLE IF EXISTS eventsStateChange")
				self.cursor.execute(
					"DROP TABLE IF EXISTS eventsConnectedChange")
				self.cursor.execute("DROP TABLE IF EXISTS eventsSensorTimeOut")
				self.cursor.execute("DROP TABLE IF EXISTS eventsNewOption")
				self.cursor.execute("DROP TABLE IF EXISTS eventsNewNode")
				self.cursor.execute("DROP TABLE IF EXISTS eventsNewSensor")
				self.cursor.execute("DROP TABLE IF EXISTS eventsNewAlert")
				self.cursor.execute("DROP TABLE IF EXISTS eventsNewManager")
				self.cursor.execute("DROP TABLE IF EXISTS eventsChangeOption")
				self.cursor.execute("DROP TABLE IF EXISTS eventsChangeNode")
				self.cursor.execute("DROP TABLE IF EXISTS eventsChangeSensor")
				self.cursor.execute("DROP TABLE IF EXISTS eventsChangeAlert")
				self.cursor.execute("DROP TABLE IF EXISTS eventsChangeManager")
				self.cursor.execute("DROP TABLE IF EXISTS eventsDeleteNode")
				self.cursor.execute("DROP TABLE IF EXISTS eventsDeleteSensor")
				self.cursor.execute("DROP TABLE IF EXISTS eventsDeleteAlert")
				self.cursor.execute("DROP TABLE IF EXISTS eventsDeleteManager")
				self.cursor.execute("DROP TABLE IF EXISTS events")
				self.cursor.execute("DROP TABLE IF EXISTS internals")
				self.cursor.execute("DROP TABLE IF EXISTS options")
				self.cursor.execute("DROP TABLE IF EXISTS sensorsAlertLevels")
				self.cursor.execute(
					"DROP TABLE IF EXISTS sensorAlertsAlertLevels")
				self.cursor.execute("DROP TABLE IF EXISTS sensorAlerts")
				self.cursor.execute("DROP TABLE IF EXISTS sensorsDataInt")
				self.cursor.execute("DROP TABLE IF EXISTS sensorsDataFloat")
				self.cursor.execute("DROP TABLE IF EXISTS sensors")
				self.cursor.execute("DROP TABLE IF EXISTS alertsAlertLevels")
				self.cursor.execute("DROP TABLE IF EXISTS alerts")
				self.cursor.execute("DROP TABLE IF EXISTS managers")
				self.cursor.execute("DROP TABLE IF EXISTS alertLevels")
				self.cursor.execute("DROP TABLE IF EXISTS nodes")

				# commit all changes
				self.conn.commit()

				# close connection to the database
				self._closeConnection()

				self.createStorage()

			else:

				# commit all changes
				self.conn.commit()

				# close connection to the database
				self._closeConnection()

				self.createObjectsFromDb()

		# tables do not exist yet
		# => create them
		else:
			
			# close connection to the database
			self._closeConnection()

			self.createStorage()



	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.dbLock.acquire()


	# internal function that adds all events from the queue to the database
	#
	# return True or False
	def _addEventsToDb(self):

		# add all events to the database (if any exists)
		while len(self.events) != 0:

			event = self.events.pop()

			# insert event into the database
			if isinstance(event, EventSensorAlert):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "sensorAlert"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsSensorAlert ("
						+ "eventId, "
						+ "description, "
						+ "state) "
						+ "VALUES (%s, %s, %s)",
						(eventId, event.description, event.state))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "sensor alert event.")

					return False

			elif isinstance(event, EventNewVersion):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "newVersion"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsNewVersion ("
						+ "eventId, "
						+ "usedVersion, "
						+ "usedRev, "
						+ "newVersion, "
						+ "newRev, "
						+ "instance, "
						+ "hostname) "
						+ "VALUES (%s, %s, %s, %s, %s, %s, %s)",
						(eventId, event.usedVersion, event.usedRev,
						event.newVersion, event.newRev, event.instance,
						event.hostname))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "new version event.")

					return False

			elif isinstance(event, EventStateChange):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "stateChange"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsStateChange ("
						+ "eventId, "
						+ "hostname, "
						+ "description, "
						+ "state) "
						+ "VALUES (%s, %s, %s, %s)",
						(eventId, event.hostname, event.description,
						event.state))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "state changed event.")

					return False

			elif isinstance(event, EventConnectedChange):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "connectedChange"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsConnectedChange ("
						+ "eventId, "
						+ "hostname, "
						+ "nodeType, "
						+ "instance, "
						+ "connected) "
						+ "VALUES (%s, %s, %s, %s, %s)",
						(eventId, event.hostname, event.nodeType,
						event.instance, event.connected))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "connection changed event.")

					return False

			elif isinstance(event, EventSensorTimeOut):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "sensorTimeOut"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsSensorTimeOut ("
						+ "eventId, "
						+ "hostname, "
						+ "description, "
						+ "state) "
						+ "VALUES (%s, %s, %s, %s)",
						(eventId, event.hostname, event.description,
						event.state))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "sensor timed out event.")

					return False

			elif isinstance(event, EventNewOption):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "newOption"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsNewOption ("
						+ "eventId, "
						+ "type, "
						+ "value) "
						+ "VALUES (%s, %s, %s)",
						(eventId, event.type, event.value))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "new option event.")

					return False

			elif isinstance(event, EventNewNode):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "newNode"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsNewNode ("
						+ "eventId, "
						+ "hostname, "
						+ "nodeType, "
						+ "instance) "
						+ "VALUES (%s, %s, %s, %s)",
						(eventId, event.hostname, event.nodeType,
						event.instance))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "new node event.")

					return False

			elif isinstance(event, EventNewSensor):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "newSensor"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsNewSensor ("
						+ "eventId, "
						+ "hostname, "
						+ "description, "
						+ "state) "
						+ "VALUES (%s, %s, %s, %s)",
						(eventId, event.hostname, event.description,
						event.state))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "new sensor event.")

					return False

			elif isinstance(event, EventNewAlert):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "newAlert"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsNewAlert ("
						+ "eventId, "
						+ "hostname, "
						+ "description) "
						+ "VALUES (%s, %s, %s)",
						(eventId, event.hostname, event.description))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "new alert event.")

					return False

			elif isinstance(event, EventNewManager):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "newManager"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsNewManager ("
						+ "eventId, "
						+ "hostname, "
						+ "description) "
						+ "VALUES (%s, %s, %s)",
						(eventId, event.hostname, event.description))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "new manager event.")

					return False

			elif isinstance(event, EventChangeOption):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "changeOption"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsChangeOption ("
						+ "eventId, "
						+ "type, "
						+ "oldValue, "
						+ "newValue) "
						+ "VALUES (%s, %s, %s, %s)",
						(eventId, event.type, event.oldValue, event.newValue))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "option changed event.")

					return False

			elif isinstance(event, EventChangeNode):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "changeNode"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsChangeNode ("
						+ "eventId, "
						+ "oldHostname, "
						+ "oldNodeType, "
						+ "oldInstance, "
						+ "oldVersion, "
						+ "oldRev, "
						+ "oldUsername, "
						+ "oldPersistent, "
						+ "newHostname, "
						+ "newNodeType, "
						+ "newInstance, "
						+ "newVersion, "
						+ "newRev, "
						+ "newUsername, "
						+ "newPersistent) "
						+ "VALUES "
						+ "(%s, %s, %s, %s, %s, %s, %s, %s, %s, "
						+ "%s, %s, %s, %s, %s, %s)",
						(eventId, event.oldHostname, event.oldNodeType,
						event.oldInstance, event.oldVersion,
						event.oldRev, event.oldUsername, event.oldPersistent,
						event.newHostname, event.newNodeType,
						event.newInstance, event.newVersion, event.newRev,
						event.newUsername, event.newPersistent))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "node changed event.")

					return False

			elif isinstance(event, EventChangeSensor):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "changeSensor"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsChangeSensor ("
						+ "eventId, "
						+ "oldAlertDelay, "
						+ "oldDescription, "
						+ "oldRemoteSensorId, "
						+ "newAlertDelay, "
						+ "newDescription, "
						+ "newRemoteSensorId) "
						+ "VALUES "
						+ "(%s, %s, %s, %s, %s, %s, %s)",
						(eventId, event.oldAlertDelay, event.oldDescription,
						event.oldRemoteSensorId,
						event.newAlertDelay, event.newDescription,
						event.newRemoteSensorId))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "sensor changed event.")

					return False

			elif isinstance(event, EventChangeAlert):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "changeAlert"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsChangeAlert ("
						+ "eventId, "
						+ "oldDescription, "
						+ "oldRemoteAlertId, "
						+ "newDescription, "
						+ "newRemoteAlertId) "
						+ "VALUES "
						+ "(%s, %s, %s, %s, %s)",
						(eventId, event.oldDescription, event.oldRemoteAlertId,
						event.newDescription, event.newRemoteAlertId))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "alert changed event.")

					return False

			elif isinstance(event, EventChangeManager):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "changeManager"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsChangeManager ("
						+ "eventId, "
						+ "oldDescription, "
						+ "newDescription) "
						+ "VALUES "
						+ "(%s, %s, %s)",
						(eventId, event.oldDescription, event.newDescription))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "manager changed event.")

					return False

			elif isinstance(event, EventDeleteNode):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "deleteNode"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsDeleteNode ("
						+ "eventId, "
						+ "hostname, "
						+ "nodeType, "
						+ "instance) "
						+ "VALUES (%s, %s, %s, %s)",
						(eventId, event.hostname, event.nodeType,
						event.instance))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "node deleted event.")

					return False

			elif isinstance(event, EventDeleteSensor):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "deleteSensor"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsDeleteSensor ("
						+ "eventId, "
						+ "description) "
						+ "VALUES (%s, %s)",
						(eventId, event.description))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "sensor deleted event.")

					return False

			elif isinstance(event, EventDeleteAlert):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "deleteAlert"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsDeleteAlert ("
						+ "eventId, "
						+ "description) "
						+ "VALUES (%s, %s)",
						(eventId, event.description))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "alert deleted event.")

					return False

			elif isinstance(event, EventDeleteManager):
				try:
					self.cursor.execute("INSERT INTO events ("
						+ "timeOccurred, "
						+ "type) "
						+ "VALUES (%s, %s)",
						(event.timeOccurred, "deleteManager"))

					eventId = self.cursor.lastrowid

					self.cursor.execute("INSERT INTO eventsDeleteManager ("
						+ "eventId, "
						+ "description) "
						+ "VALUES (%s, %s)",
						(eventId, event.description))
				except Exception as e:
					logging.exception("[%s]: Not able to add "
						% self.fileName
						+ "manager deleted event.")

					return False

			else:
				logging.error("[%s]: Used event not known."
					% self.fileName)

		return True


	# Internal function that adds the data of the sensor to the database.
	# Does not catch exceptions.
	#
	# No return value.
	def _addSensorDataToDb(self, sensor):

		if sensor.dataType == SensorDataType.NONE:
			pass

		elif sensor.dataType == SensorDataType.INT:
			self.cursor.execute("INSERT INTO sensorsDataInt ("
				+ "sensorId, "
				+ "data) "
				+ "VALUES (%s, %s)",
				(sensor.sensorId, sensor.data))

		elif sensor.dataType == SensorDataType.FLOAT:
			self.cursor.execute("INSERT INTO sensorsDataFloat ("
				+ "sensorId, "
				+ "data) "
				+ "VALUES (%s, %s)",
				(sensor.sensorId, sensor.data))


	# internal function that closes the connection to the mysql server
	def _closeConnection(self):
		self.cursor.close()
		self.conn.close()
		self.cursor = None
		self.conn = None


	# internal function that connects to the mysql server
	# (needed because direct changes to the database by another program
	# are not seen if the connection to the mysql server is kept alive)
	def _openConnection(self):
		# import the needed package
		import MySQLdb

		self.conn = MySQLdb.connect(host=self.host, port=self.port,
			user=self.username,	passwd=self.password, db=self.database)

		self.cursor = self.conn.cursor()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
		self.dbLock.release()


	# internal function that removes all events from the database
	# that are too old
	#
	# return True or False
	def _removeEventsFromDb(self):

		# delete all events that are older than the configured life span 
		try:
			self.cursor.execute("SELECT id, type FROM events "
				+ "WHERE (timeOccurred + "
				+ str(self.eventsLifeSpan * 86400)
				+ ")"
				+ "<= %s",
				(int(time.time()), ))
			result = self.cursor.fetchall()
			
			for idTuple in result:
				eventId = idTuple[0]
				eventType = idTuple[1]

				if eventType.upper() == "sensorAlert".upper():
					self.cursor.execute("DELETE FROM eventsSensorAlert "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "newVersion".upper():
					self.cursor.execute("DELETE FROM eventsNewVersion "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "stateChange".upper():
					self.cursor.execute("DELETE FROM eventsStateChange "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "connectedChange".upper():
					self.cursor.execute("DELETE FROM eventsConnectedChange "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "sensorTimeOut".upper():
					self.cursor.execute("DELETE FROM eventsSensorTimeOut "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "newOption".upper():
					self.cursor.execute("DELETE FROM eventsNewOption "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "newNode".upper():
					self.cursor.execute("DELETE FROM eventsNewNode "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "newSensor".upper():
					self.cursor.execute("DELETE FROM eventsNewSensor "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "newAlert".upper():
					self.cursor.execute("DELETE FROM eventsNewAlert "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "newManager".upper():
					self.cursor.execute("DELETE FROM eventsNewManager "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "changeOption".upper():
					self.cursor.execute("DELETE FROM eventsChangeOption "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "changeNode".upper():
					self.cursor.execute("DELETE FROM eventsChangeNode "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "changeSensor".upper():
					self.cursor.execute("DELETE FROM eventsChangeSensor "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "changeAlert".upper():
					self.cursor.execute("DELETE FROM eventsChangeAlert "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "changeManager".upper():
					self.cursor.execute("DELETE FROM eventsChangeManager "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "deleteNode".upper():
					self.cursor.execute("DELETE FROM eventsDeleteNode "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "deleteSensor".upper():
					self.cursor.execute("DELETE FROM eventsDeleteSensor "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "deleteAlert".upper():
					self.cursor.execute("DELETE FROM eventsDeleteAlert "
						+ "WHERE eventId = %s",
						(eventId, ))
				elif eventType.upper() == "deleteManager".upper():
					self.cursor.execute("DELETE FROM eventsDeleteManager "
						+ "WHERE eventId = %s",
						(eventId, ))
				else:
					logging.error("[%s]: Stored event not known."
						% self.fileName)

				self.cursor.execute("DELETE FROM events "
					+ "WHERE id = %s",
					(eventId, ))
		except Exception as e:
			logging.exception("[%s]: Not able to delete old events."
				% self.fileName)

			return False

		return True



	# Internal function that removes the data of the sensor in the database.
	# Does not catch exceptions.
	#
	# No return value.
	def _removeSensorDataFromDb(self, sensor):

		self.cursor.execute("DELETE FROM sensorsDataInt "
			+ "WHERE sensorId = %s",
			(sensor.sensorId, ))

		self.cursor.execute("DELETE FROM sensorsDataFloat "
			+ "WHERE sensorId = %s",
			(sensor.sensorId, ))


	# creates objects from the data in the database 
	# (should only be called during the initial connection to the database)
	#
	# no return value but raise exception if it fails
	def createObjectsFromDb(self):

		# connect to the database
		self._openConnection()

		# get last stored server time
		self.cursor.execute("SELECT "
			+ "value "
			+ "FROM internals WHERE type = 'serverTime'")
		result = self.cursor.fetchall()
		serverTime = result[0][0]


		# create option objects from db
		self.cursor.execute("SELECT "
			+ "type, "
			+ "value "
			+ "FROM options")
		result = self.cursor.fetchall()

		for optionTuple in result:
			tempOption = Option()
			tempOption.type = optionTuple[0]
			tempOption.value = optionTuple[1]

			self.options.append(tempOption)
			self.optionsCopy.append(tempOption)


		# create node objects from db
		self.cursor.execute("SELECT * FROM nodes")
		result = self.cursor.fetchall()

		for nodeTuple in result:
			tempNode = Node()
			tempNode.nodeId = nodeTuple[0]
			tempNode.hostname = nodeTuple[1]
			tempNode.nodeType = nodeTuple[2]
			tempNode.instance = nodeTuple[3]
			tempNode.connected = nodeTuple[4]
			tempNode.version = nodeTuple[5]
			tempNode.rev = nodeTuple[6]
			tempNode.newestVersion = nodeTuple[7]
			tempNode.newestRev = nodeTuple[8]
			tempNode.username = nodeTuple[9]
			tempNode.persistent = nodeTuple[10]

			self.nodes.append(tempNode)
			self.nodesCopy.append(tempNode)

		# create sensor objects from db
		self.cursor.execute("SELECT "
			+ "id, "
			+ "nodeId, "
			+ "remoteSensorId, "
			+ "description, "
			+ "state, "
			+ "lastStateUpdated, "
			+ "alertDelay, "
			+ "dataType "
			+ "FROM sensors")
		result = self.cursor.fetchall()

		for sensorTuple in result:
			tempSensor = Sensor()
			tempSensor.sensorId = sensorTuple[0]
			tempSensor.nodeId = sensorTuple[1]
			tempSensor.remoteSensorId = sensorTuple[2]
			tempSensor.description = sensorTuple[3]
			tempSensor.state = sensorTuple[4]
			tempSensor.lastStateUpdated = sensorTuple[5]
			tempSensor.alertDelay = sensorTuple[6]
			tempSensor.dataType = sensorTuple[7]
			tempSensor.serverTime = serverTime

			self.cursor.execute("SELECT "
				+ "alertLevel "
				+ "FROM sensorsAlertLevels "
				+ "WHERE sensorId = %s", (tempSensor.sensorId, ))
			alertLevelResult = self.cursor.fetchall()
			for alertLevelTuple in alertLevelResult:
				tempSensor.alertLevels.append(alertLevelTuple[0])

			# Get sensor data from database.
			if tempSensor.dataType == SensorDataType.NONE:
				tempSensor.data = None

			elif tempSensor.dataType == SensorDataType.INT:
				self.cursor.execute("SELECT "
					+ "data "
					+ "FROM sensorsDataInt "
					+ "WHERE sensorId = %s", (tempSensor.sensorId, ))
				dataResult = self.cursor.fetchall()
				tempSensor.data = dataResult[0][0]

			elif tempSensor.dataType == SensorDataType.FLOAT:
				self.cursor.execute("SELECT "
					+ "data "
					+ "FROM sensorsDataFloat "
					+ "WHERE sensorId = %s", (tempSensor.sensorId, ))
				dataResult = self.cursor.fetchall()
				tempSensor.data = dataResult[0][0]

			self.sensors.append(tempSensor)
			self.sensorsCopy.append(tempSensor)

		# create alert objects from db
		self.cursor.execute("SELECT "
			+ "id, "
			+ "nodeId, "
			+ "remoteAlertId, "
			+ "description "
			+ "FROM alerts")
		result = self.cursor.fetchall()

		for alertTuple in result:
			tempAlert = Alert()
			tempAlert.alertId = alertTuple[0]
			tempAlert.nodeId = alertTuple[1]
			tempAlert.remoteAlertId = alertTuple[2]
			tempAlert.description = alertTuple[3]

			self.cursor.execute("SELECT "
				+ "alertLevel "
				+ "FROM alertsAlertLevels "
				+ "WHERE alertId = %s", (tempAlert.alertId, ))
			alertLevelResult = self.cursor.fetchall()
			for alertLevelTuple in alertLevelResult:
				tempAlert.alertLevels.append(alertLevelTuple[0])

			self.alerts.append(tempAlert)
			self.alertsCopy.append(tempAlert)


		# create manager objects from db
		self.cursor.execute("SELECT "
			+ "id, "
			+ "nodeId, "
			+ "description "
			+ "FROM managers")
		result = self.cursor.fetchall()

		for managerTuple in result:
			tempManager = Manager()
			tempManager.managerId = managerTuple[0]
			tempManager.nodeId = managerTuple[1]
			tempManager.description = managerTuple[2]

			self.managers.append(tempManager)
			self.managersCopy.append(tempManager)

		# create alert levels objects from db
		self.cursor.execute("SELECT "
			+ "alertLevel, "
			+ "name, "
			+ "triggerAlways "
			+ "FROM alertLevels")
		result = self.cursor.fetchall()

		for alertLevelTuple in result:
			tempAlertLevel = AlertLevel()
			tempAlertLevel.level = alertLevelTuple[0]
			tempAlertLevel.name = alertLevelTuple[1]
			tempAlertLevel.triggerAlways = (alertLevelTuple[2] == 1)

			self.alertLevels.append(tempAlertLevel)
			self.alertLevelsCopy.append(tempAlertLevel)

		# close connection to the database
		self._closeConnection()


	# creates the database (should only be called if the database
	# does not exist)
	#
	# no return value but raise exception if it fails
	def createStorage(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to MySQL server." 
				% self.fileName)

			self._releaseLock()

			# remember to pass the exception
			raise

		# create internals table (used internally by the client)
		# if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'internals'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE internals ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "type VARCHAR(255) NOT NULL UNIQUE, "
				+ "value DOUBLE NOT NULL)")

			# insert server time field
			self.cursor.execute("INSERT INTO internals ("
				+ "type, "
				+ "value) VALUES (%s, %s)",
				("serverTime", 0.0))

			# insert version field
			self.cursor.execute("INSERT INTO internals ("
				+ "type, "
				+ "value) VALUES (%s, %s)",
				("version", self.version))

			# insert rev field
			self.cursor.execute("INSERT INTO internals ("
				+ "type, "
				+ "value) VALUES (%s, %s)",
				("rev", self.rev))

		# create options table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'options'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE options ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "type VARCHAR(255) NOT NULL UNIQUE, "
				+ "value DOUBLE NOT NULL)")

		# create nodes table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'nodes'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE nodes ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "hostname VARCHAR(255) NOT NULL, "
				+ "nodeType VARCHAR(255) NOT NULL, "
				+ "instance VARCHAR(255) NOT NULL, "
				+ "connected INTEGER NOT NULL, "
				+ "version DOUBLE NOT NULL, "
				+ "rev INTEGER NOT NULL, "
				+ "newestVersion DOUBLE NOT NULL, "
				+ "newestRev INTEGER NOT NULL, "
				+ "username VARCHAR(255) NOT NULL, "
				+ "persistent INTEGER NOT NULL)")

		# create sensors table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'sensors'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE sensors ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "nodeId INTEGER NOT NULL, "
				+ "remoteSensorId INTEGER NOT NULL, "
				+ "description VARCHAR(255) NOT NULL, "
				+ "state INTEGER NOT NULL, "
				+ "lastStateUpdated INTEGER NOT NULL, "
				+ "alertDelay INTEGER NOT NULL, "
				+ "dataType INTEGER NOT NULL, "
				+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create sensorAlerts table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'sensorAlerts'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE sensorAlerts ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "sensorId INTEGER NOT NULL, "
				+ "state INTEGER NOT NULL, "
				+ "description TEXT NOT NULL,"
				+ "timeReceived INTEGER NOT NULL, "
				+ "dataJson TEXT NOT NULL)")

		# Create sensorsDataInt table if it does not exist.
		self.cursor.execute("SHOW TABLES LIKE 'sensorsDataInt'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE sensorsDataInt ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "sensorId INTEGER NOT NULL UNIQUE, "
				+ "data INTEGER NOT NULL, "
				+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# Create sensorsDataFloat table if it does not exist.
		self.cursor.execute("SHOW TABLES LIKE 'sensorsDataFloat'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE sensorsDataFloat ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "sensorId INTEGER NOT NULL UNIQUE, "
				+ "data REAL NOT NULL, "
				+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create sensorAlertsAlertLevels table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'sensorAlertsAlertLevels'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE sensorAlertsAlertLevels ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "sensorAlertId INTEGER NOT NULL, "
				+ "alertLevel INTEGER NOT NULL, "
				+ "FOREIGN KEY(sensorAlertId) REFERENCES sensorAlerts(id))")

		# create sensorsAlertLevels table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'sensorsAlertLevels'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE sensorsAlertLevels ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "sensorId INTEGER NOT NULL, "
				+ "alertLevel INTEGER NOT NULL, "
				+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create alerts table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'alerts'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE alerts ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "nodeId INTEGER NOT NULL, "
				+ "remoteAlertId INTEGER NOT NULL, "
				+ "description VARCHAR(255) NOT NULL, "
				+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create alertsAlertLevels table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'alertsAlertLevels'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE alertsAlertLevels ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "alertId INTEGER NOT NULL, "
				+ "alertLevel INTEGER NOT NULL, "
				+ "FOREIGN KEY(alertId) REFERENCES alerts(id))")

		# create managers table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'managers'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE managers ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "nodeId INTEGER NOT NULL, "
				+ "description VARCHAR(255) NOT NULL, "
				+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create alert levels table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'alertLevels'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE alertLevels ("
				+ "alertLevel INTEGER PRIMARY KEY, "
				+ "name VARCHAR(255) NOT NULL, "
				+ "triggerAlways INTEGER NOT NULL)")

		# create events table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'events'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE events ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "timeOccurred INTEGER NOT NULL, "
				+ "type VARCHAR(255) NOT NULL)")

		# create eventsSensorAlert table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsSensorAlert'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsSensorAlert ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "description TEXT NOT NULL, "
				+ "state INTEGER NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsStateChange table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsStateChange'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsStateChange ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "hostname TEXT NOT NULL, "
				+ "description TEXT NOT NULL, "
				+ "state INTEGER NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsConnectedChange table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsConnectedChange'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsConnectedChange ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "hostname TEXT NOT NULL, "
				+ "nodeType TEXT NOT NULL, "
				+ "instance TEXT NOT NULL, "
				+ "connected INTEGER NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsSensorTimeOut table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsSensorTimeOut'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsSensorTimeOut ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "hostname TEXT NOT NULL, "
				+ "description TEXT NOT NULL, "
				+ "state INTEGER NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewVersion table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsNewVersion'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsNewVersion ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "usedVersion DOUBLE NOT NULL, "
				+ "usedRev INTEGER NOT NULL, "
				+ "newVersion DOUBLE NOT NULL, "
				+ "newRev INTEGER NOT NULL, "
				+ "instance VARCHAR(255) NOT NULL, "
				+ "hostname VARCHAR(255) NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewOption table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsNewOption'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsNewOption ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "type VARCHAR(255) NOT NULL, "
				+ "value DOUBLE NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewNode table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsNewNode'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsNewNode ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "hostname TEXT NOT NULL, "
				+ "nodeType TEXT NOT NULL, "
				+ "instance TEXT NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewSensor table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsNewSensor'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsNewSensor ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "hostname TEXT NOT NULL, "
				+ "description TEXT NOT NULL, "
				+ "state INTEGER NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewAlert table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsNewAlert'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsNewAlert ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "hostname TEXT NOT NULL, "
				+ "description TEXT NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewManager table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsNewManager'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsNewManager ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "hostname TEXT NOT NULL, "
				+ "description TEXT NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeOption table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsChangeOption'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsChangeOption ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "type VARCHAR(255) NOT NULL, "
				+ "oldValue DOUBLE NOT NULL, "
				+ "newValue DOUBLE NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeNode table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsChangeNode'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsChangeNode ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "oldHostname VARCHAR(255) NOT NULL, "
				+ "oldNodeType VARCHAR(255) NOT NULL, "
				+ "oldInstance VARCHAR(255) NOT NULL, "
				+ "oldVersion DOUBLE NOT NULL, "
				+ "oldRev INTEGER NOT NULL, "
				+ "oldUsername VARCHAR(255) NOT NULL, "
				+ "oldPersistent INTEGER NOT NULL, "
				+ "newHostname VARCHAR(255) NOT NULL, "
				+ "newNodeType VARCHAR(255) NOT NULL, "
				+ "newInstance VARCHAR(255) NOT NULL, "
				+ "newVersion DOUBLE NOT NULL, "
				+ "newRev INTEGER NOT NULL, "
				+ "newUsername VARCHAR(255) NOT NULL, "
				+ "newPersistent INTEGER NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeSensor table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsChangeSensor'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsChangeSensor ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "oldAlertDelay INTEGER NOT NULL, "
				+ "oldDescription VARCHAR(255) NOT NULL, "
				+ "oldRemoteSensorId INTEGER NOT NULL, "
				+ "newAlertDelay INTEGER NOT NULL, "
				+ "newDescription VARCHAR(255) NOT NULL, "
				+ "newRemoteSensorId INTEGER NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeAlert table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsChangeAlert'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsChangeAlert ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "oldDescription VARCHAR(255) NOT NULL, "
				+ "oldRemoteAlertId INTEGER NOT NULL, "
				+ "newDescription VARCHAR(255) NOT NULL, "
				+ "newRemoteAlertId INTEGER NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeManager table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsChangeManager'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsChangeManager ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "oldDescription VARCHAR(255) NOT NULL, "
				+ "newDescription VARCHAR(255) NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsDeleteNode table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsDeleteNode'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsDeleteNode ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "hostname TEXT NOT NULL, "
				+ "nodeType TEXT NOT NULL, "
				+ "instance TEXT NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsDeleteSensor table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsDeleteSensor'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsDeleteSensor ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "description TEXT NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsDeleteAlert table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsDeleteAlert'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsDeleteAlert ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "description TEXT NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsDeleteManager table if it does not exist
		self.cursor.execute("SHOW TABLES LIKE 'eventsDeleteManager'")
		result = self.cursor.fetchall()
		if len(result) == 0:
			self.cursor.execute("CREATE TABLE eventsDeleteManager ("
				+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
				+ "eventId INTEGER NOT NULL, "
				+ "description TEXT NOT NULL, "
				+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()


	# updates the received server information
	#
	# return True or False
	def updateServerInformation(self, serverTime, options, nodes, sensors,
		alerts, managers, alertLevels, sensorAlerts):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to MySQL server." 
				% self.fileName)

			self._releaseLock()

			return False

		# update server time
		try:
			self.cursor.execute("UPDATE internals SET "
				+ "value = %s "
				+ "WHERE type = %s",
				(serverTime, "serverTime"))

		except Exception as e:
			logging.exception("[%s]: Not able to update server time." 
				% self.fileName)

			self._releaseLock()

			return False


		# step one: delete all objects that do not exist anymore
		# (NOTE: first delete alerts, sensors and managers before
		# nodes because of the foreign key dependency; also delete
		# sensorAlerts before sensors and nodes)
		for option in list(self.optionsCopy):
			# check if options stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements
			if not option in options:
				try:
					self.cursor.execute("DELETE FROM options "
						+ "WHERE type = %s "
						+ "AND value = %s",
						(option.type, option.value))
				except Exception as e:
					logging.exception("[%s]: Not able to delete option " 
						% self.fileName
						+ "of type %s."
						% option.type)

					self._releaseLock()

					return False

				self.optionsCopy.remove(option)

		# delete all sensor alerts that are older than the configured
		# life span
		try:
			# delete all sensor alerts with the returned id
			self.cursor.execute("SELECT id FROM sensorAlerts "
				+ "WHERE (timeReceived + "
				+ str(self.sensorAlertLifeSpan * 86400)
				+ ")"
				+ "<= %s",
				(int(time.time()), ))
			result = self.cursor.fetchall()
			for idTuple in result:
				self.cursor.execute("DELETE FROM sensorAlertsAlertLevels "
					+ "WHERE sensorAlertId = %s",
					(idTuple[0], ))
				self.cursor.execute("DELETE FROM sensorAlerts "
					+ "WHERE id = %s",
					(idTuple[0], ))

		except Exception as e:
			logging.exception("[%s]: Not able to delete sensor alert " 
				% self.fileName
				+ "with id %d."
				% idTuple[0])

			self._releaseLock()

			return False

		for sensor in list(self.sensorsCopy):
			# check if sensors stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements
			if not sensor in sensors:
				try:
					self.cursor.execute("DELETE FROM sensorsAlertLevels "
						+ "WHERE sensorId = %s",
						(sensor.sensorId, ))

					# delete all sensor alerts with the returned id
					self.cursor.execute("SELECT id FROM sensorAlerts "
						+ "WHERE sensorId = %s",
						(sensor.sensorId, ))
					result = self.cursor.fetchall()
					for idTuple in result:
						self.cursor.execute("DELETE FROM "
							+ "sensorAlertsAlertLevels "
							+ "WHERE sensorAlertId = %s",
							(idTuple[0], ))
						self.cursor.execute("DELETE FROM sensorAlerts "
							+ "WHERE id = %s",
							(idTuple[0], ))

					# Delete all sensor data from database.
					self._removeSensorDataFromDb(sensor)

					self.cursor.execute("DELETE FROM sensors "
						+ "WHERE id = %s",
						(sensor.sensorId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to delete sensor " 
						% self.fileName
						+ "with id %d."
						% sensor.sensorId)

					self._releaseLock()

					return False

				self.sensorsCopy.remove(sensor)

		for alert in list(self.alertsCopy):
			# check if alerts stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements	
			if not alert in alerts:
				try:
					self.cursor.execute("DELETE FROM alertsAlertLevels "
						+ "WHERE alertId = %s",
						(alert.alertId, ))

					self.cursor.execute("DELETE FROM alerts "
						+ "WHERE id = %s",
						(alert.alertId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to delete alert " 
						% self.fileName
						+ "with id %d."
						% alert.alertId)

					self._releaseLock()

					return False

				self.alertsCopy.remove(alert)

		for manager in list(self.managersCopy):
			# check if managers stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements
			if not manager in managers:
				try:
					self.cursor.execute("DELETE FROM managers "
						+ "WHERE id = %s",
						(manager.managerId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to delete manager " 
						% self.fileName
						+ "with id %d."
						% manager.managerId)

					self._releaseLock()

					return False

				self.managersCopy.remove(manager)

		for node in list(self.nodesCopy):
			# check if nodes stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements
			if not node in nodes:
				try:
					self.cursor.execute("DELETE FROM nodes "
						+ "WHERE id = %s",
						(node.nodeId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to delete node "
						% self.fileName
						+ "with id %d." 
						% node.nodeId)

					self._releaseLock()

					return False

				self.nodesCopy.remove(node)

		for alertLevel in list(self.alertLevelsCopy):
			# check if alert levels stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements	
			if not alertLevel in alertLevels:
				try:
					self.cursor.execute("DELETE FROM alertLevels "
						+ "WHERE alertLevel = %s",
						(alertLevel.level, ))
				except Exception as e:
					logging.exception("[%s]: Not able to delete alert level " 
						% self.fileName
						+ " %d."
						% alertLevel.level)

					self._releaseLock()

					return False

				self.alertLevelsCopy.remove(alertLevel)

		# delete all events that are older than the configured life span
		if self.eventsLifeSpan > 0:
			if not self._removeEventsFromDb():

				logging.error("[%s]: Not able to remove old events."
					% self.fileName)

				self._releaseLock()

				return False


		# step two: update all existing objects
		for option in options:
			# when the option was found
			# => update it in the database
			if option in self.optionsCopy:
				try:
					self.cursor.execute("UPDATE options SET "
						+ "value = %s WHERE type = %s",
						(option.value, option.type))
				except Exception as e:
					logging.exception("[%s]: Not able to update option."
						% self.fileName)

					self._releaseLock()

					return False

		for node in nodes:
			# when the node was found
			# => update it in the database
			if node in self.nodesCopy:
				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "hostname = %s, "
						+ "nodeType = %s, "
						+ "instance = %s, "
						+ "connected = %s, "
						+ "version = %s, "
						+ "rev = %s, "
						+ "newestVersion = %s, "
						+ "newestRev = %s, "
						+ "username = %s, "
						+ "persistent = %s "
						+ "WHERE id = %s",
						(node.hostname, node.nodeType, node.instance,
						node.connected, node.version, node.rev, 
						node.newestVersion, node.newestRev, node.username,
						node.persistent, node.nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to update node."
						% self.fileName)

					self._releaseLock()

					return False

		for sensor in sensors:
			# when the sensor was found
			# => update it in the database
			if sensor in self.sensorsCopy:
				try:
					self.cursor.execute("UPDATE sensors SET "
						+ "nodeId = %s, "
						+ "remoteSensorId = %s, "
						+ "description = %s, "
						+ "state = %s ,"
						+ "lastStateUpdated = %s, "
						+ "alertDelay = %s, "
						+ "dataType = %s "
						+ "WHERE id = %s",
						(sensor.nodeId, sensor.remoteSensorId,
						sensor.description, sensor.state,
						sensor.lastStateUpdated, sensor.alertDelay,
						sensor.dataType, sensor.sensorId))

					# TODO
					# delete data and add it again is not the best way
					# (index will grow steadily)

					self.cursor.execute("DELETE FROM sensorsAlertLevels "
						+ "WHERE sensorId = %s",
						(sensor.sensorId, ))

					for sensorAlertLevel in sensor.alertLevels:
						self.cursor.execute("INSERT INTO sensorsAlertLevels ("
							+ "sensorId, "
							+ "alertLevel) "
							+ "VALUES (%s, %s)",
							(sensor.sensorId, sensorAlertLevel))

					# TODO
					# delete data and add it again is not the best way
					# (index will grow steadily)

					# Delete all sensor data from database.
					self._removeSensorDataFromDb(sensor)

					# Add sensor data to database.
					self._addSensorDataToDb(sensor)

				except Exception as e:
					logging.exception("[%s]: Not able to update sensor."
						% self.fileName)

					self._releaseLock()

					return False

		for alert in alerts:
			# when the alert was found
			# => update it in the database
			if alert in self.alertsCopy:
				try:
					self.cursor.execute("UPDATE alerts SET "
						+ "nodeId = %s, "
						+ "remoteAlertId = %s, "
						+ "description = %s "
						+ "WHERE id = %s",
						(alert.nodeId, alert.remoteAlertId, 
						alert.description, alert.alertId))

					self.cursor.execute("DELETE FROM alertsAlertLevels "
						+ "WHERE alertId = %s",
						(alert.alertId, ))

					for alertAlertLevel in alert.alertLevels:
						self.cursor.execute("INSERT INTO alertsAlertLevels ("
							+ "alertId, "
							+ "alertLevel) "
							+ "VALUES (%s, %s)",
							(alert.alertId, alertAlertLevel))

				except Exception as e:
					logging.exception("[%s]: Not able to update alert."
						% self.fileName)

					self._releaseLock()

					return False

		for manager in managers:
			# when the manager was found
			# => update it in the database
			if manager in self.managersCopy:
				try:
					self.cursor.execute("UPDATE managers SET "
						+ "nodeId = %s, "
						+ "description = %s "
						+ "WHERE id = %s",
						(manager.nodeId, manager.description,
						manager.managerId))
				except Exception as e:
					logging.exception("[%s]: Not able to update manager."
						% self.fileName)

					self._releaseLock()

					return False

		for alertLevel in alertLevels:
			# when the alert level was found
			# => update it in the database
			if alertLevel in self.alertLevelsCopy:
				try:
					self.cursor.execute("UPDATE alertLevels SET "
						+ "name = %s, "
						+ "triggerAlways = %s "
						+ "WHERE alertLevel = %s",
						(alertLevel.name, alertLevel.triggerAlways,
						alertLevel.level))
				except Exception as e:
					logging.exception("[%s]: Not able to update alert level."
						% self.fileName)

					self._releaseLock()

					return False


		# step three: add all new objects
		# (NOTE: first add nodes before alerts, sensors and managers
		# because of the foreign key dependency)
		for option in options:

			# when it does not exist in the database
			# => add it and add to local database elements
			if not option in self.optionsCopy:
				try:
					self.cursor.execute("INSERT INTO options ("
						+ "type, "
						+ "value) VALUES (%s, %s)",
						(option.type, option.value))
				except Exception as e:
					logging.exception("[%s]: Not able to add option."
						% self.fileName)

					self._releaseLock()

					return False

				self.optionsCopy.append(option)

		for node in nodes:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not node in self.nodesCopy:
				try:
					self.cursor.execute("INSERT INTO nodes ("
						+ "id, "
						+ "hostname, "
						+ "nodeType, "
						+ "instance, "
						+ "connected, "
						+ "version, "
						+ "rev, "
						+ "newestVersion, "
						+ "newestRev, "
						+ "username, "
						+ "persistent) "
						+ "VALUES "
						+ "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
						(node.nodeId, node.hostname, node.nodeType,
						node.instance, node.connected, node.version, node.rev,
						node.newestVersion, node.newestRev, node.username,
						node.persistent))
				except Exception as e:
					logging.exception("[%s]: Not able to add node."
						% self.fileName)

					self._releaseLock()

					return False

				self.nodesCopy.append(node)

		for sensor in sensors:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not sensor in self.sensorsCopy:
				try:
					self.cursor.execute("INSERT INTO sensors ("
						+ "id, "
						+ "nodeId, "
						+ "remoteSensorId, "
						+ "description, "
						+ "state, "
						+ "lastStateUpdated, "
						+ "alertDelay, "
						+ "dataType) "
						+ "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
						(sensor.sensorId, sensor.nodeId,
						sensor.remoteSensorId, sensor.description,
						sensor.state, sensor.lastStateUpdated,
						sensor.alertDelay, sensor.dataType))

					for sensorAlertLevel in sensor.alertLevels:
						self.cursor.execute("INSERT INTO sensorsAlertLevels ("
							+ "sensorId, "
							+ "alertLevel) "
							+ "VALUES (%s, %s)",
							(sensor.sensorId, sensorAlertLevel))

					# Add sensor data to database.
					self._addSensorDataToDb(sensor)

				except Exception as e:
					logging.exception("[%s]: Not able to add sensor."
						% self.fileName)

					self._releaseLock()

					return False

				self.sensorsCopy.append(sensor)

		for sensorAlert in sensorAlerts:
			# try to convert received data to json
			try:
				dataJson = json.dumps(sensorAlert.optionalData)
			except Exception as e:
				logging.exception("[%s]: Not able to convert optional data "
					% self.fileName
					+ " of sensor alert to json.")
				continue

			try:
				self.cursor.execute("INSERT INTO sensorAlerts ("
					+ "sensorId, "
					+ "state, "
					+ "description, "
					+ "timeReceived, "
					+ "dataJson) "
					+ "VALUES (%s, %s, %s, %s, %s)",
					(sensorAlert.sensorId, sensorAlert.state,
					sensorAlert.description, sensorAlert.timeReceived,
					dataJson))
				sensorAlertId = self.cursor.lastrowid

				for alertLevel in sensorAlert.alertLevels:
					self.cursor.execute("INSERT INTO sensorAlertsAlertLevels ("
						+ "sensorAlertId, "
						+ "alertLevel) "
						+ "VALUES (%s, %s)",
						(sensorAlertId, alertLevel))

			except Exception as e:
				logging.exception("[%s]: Not able to add sensor alert."
					% self.fileName)

				self._releaseLock()

				return False

		for alert in alerts:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not alert in self.alertsCopy:
				try:
					self.cursor.execute("INSERT INTO alerts ("
						+ "id, "
						+ "nodeId, "
						+ "remoteAlertId, "
						+ "description) "
						+ "VALUES (%s, %s, %s, %s)",
						(alert.alertId, alert.nodeId,
						alert.remoteAlertId, alert.description))

					for alertAlertLevel in alert.alertLevels:
						self.cursor.execute("INSERT INTO alertsAlertLevels ("
							+ "alertId, "
							+ "alertLevel) "
							+ "VALUES (%s, %s)",
							(alert.alertId, alertAlertLevel))

				except Exception as e:
					logging.exception("[%s]: Not able to add alert."
						% self.fileName)

					self._releaseLock()

					return False

				self.alertsCopy.append(alert)

		for manager in managers:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not manager in self.managersCopy:
				try:
					self.cursor.execute("INSERT INTO managers ("
						+ "id, "
						+ "nodeId, "
						+ "description) "
						+ "VALUES (%s, %s, %s)",
						(manager.managerId, manager.nodeId,
						manager.description))
				except Exception as e:
					logging.exception("[%s]: Not able to add manager."
						% self.fileName)

					self._releaseLock()

					return False

				self.managersCopy.append(manager)

		for alertLevel in alertLevels:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not alertLevel in self.alertLevelsCopy:
				try:
					self.cursor.execute("INSERT INTO alertLevels ("
						+ "alertLevel, "
						+ "name, "
						+ "triggerAlways) "
						+ "VALUES (%s, %s, %s)",
						(alertLevel.level, alertLevel.name,
						alertLevel.triggerAlways))
				except Exception as e:
					logging.exception("[%s]: Not able to add alert level."
						% self.fileName)

					self._releaseLock()

					return False

				self.alertLevelsCopy.append(alertLevel)


		# add all events to the database (if it is activated to store events)
		if self.eventsLifeSpan > 0:
			if not self._addEventsToDb():

				logging.error("[%s]: Not able to add events."
					% self.fileName)

				self._releaseLock()

				return False


		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True