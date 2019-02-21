#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import os
import threading
import time
import socket
import struct
import hashlib
import json
import importlib
from localObjects import Node, Alert, Manager, Sensor, SensorAlert, \
	SensorData, SensorDataType, Option


# internal abstract class for new storage backends
class _Storage():

	# checks the version of the server and the version in the database
	# and clears every compatibility issue
	#
	# no return value but raise exception if it fails
	def checkVersionAndClearConflict(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# adds a node if it does not exist or changes the registered
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType, instance, version, rev,
		persistent, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# adds/updates the data that is given by the node for the sensors
	# to the database
	#
	# return True or False
	def addSensors(self, username, sensors, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# adds/updates the data that is given by the node for the alerts
	# to the database
	#
	# return True or False
	def addAlerts(self, username, alerts, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# adds/updates the data that is given by the node for
	# the manager to the database
	#
	# return True or False
	def addManager(self, username, manager, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, sensorId, state, dataJson, changeState,
		hasLatestData, dataType, sensorData, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the id of the node by a given username
	# (usernames are unique to each node)
	#
	# return nodeId or None
	def getNodeId(self, username, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# Gets the ids of all nodes
	#
	# return list of nodeIds
	def getNodeIds(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the count of the sensors of a node in the database
	#
	# return count of sensors or None
	def getSensorCount(self, nodeId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the sensor id of a sensor when the id of a node is given
	# and the remote sensor id that is used by the node internally
	#
	# return sensorId or None
	def getSensorId(self, nodeId, remoteSensorId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets all data needed for the survey
	#
	# return list of tuples of (instance, version, rev)
	# or None
	def getSurveyData(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the unique id from the database
	#
	# return unique id
	# or None
	def getUniqueID(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the alert id of an alert when the id of a node is given
	# and the remote alert id that is used by the node internally
	#
	# return alertId or None
	def getAlertId(self, nodeId, remoteAlertId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets all alert levels for a specific sensor given by sensorId
	#
	# return list of alertLevel
	# or None
	def getSensorAlertLevels(self, sensorId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets all alert levels for a specific alert given by alertId
	#
	# return list of alertLevels
	# or None
	def getAlertAlertLevels(self, alertId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets all sensor alerts in the database
	#
	# return a list of sensorAlert objects
	# or None
	def getSensorAlerts(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets all alert levels for the alert clients from the database
	#
	# return list alertLevels as integer
	# or None
	def getAllAlertsAlertLevels(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets all alert levels for the sensors from the database
	#
	# return list alertLevels as integer
	# or None
	def getAllSensorsAlertLevels(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets all nodes from the database that are connected to the server
	#
	# return list of nodeIds
	# or None
	def getAllConnectedNodeIds(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# Gets all nodes from the database that are registered as persistent
	# to the server.
	#
	# return list of nodeIds
	# or None
	def getAllPersistentNodeIds(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the information of all sensors which last state updates
	# are older than the given time
	#
	# return list of sensor objects
	# or None
	def getSensorsUpdatedOlderThan(self, oldestTimeUpdated, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the alert from the database when its id is given
	#
	# return an alert object or None
	def getAlertById(self, alertId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the manager from the database when its id is given
	#
	# return a manager object or None
	def getManagerById(self, managerId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the node from the database when its id is given
	#
	# return a node object or None
	def getNodeById(self, nodeId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the sensor from the database when its id is given
	#
	# return a sensor object or None
	def getSensorById(self, sensorId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# Gets all nodes from the database.
	#
	# return a list of node objects or None
	def getNodes(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = list(option objects)
	# list[1] = list(node objects)
	# list[2] = list(sensor objects)
	# list[3] = list(manager objects)
	# list[4] = list(alert objects)
	# or None
	def getAlertSystemInformation(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# gets the state of a sensor given by id
	#
	# return sensor state or None
	def getSensorState(self, sensorId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# Gets the data of a sensor given by id.
	#
	# return a sensor data object or None
	def getSensorData(self, sensorId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# change a option in the database
	#
	# return True or False
	def changeOption(self, optionType, optionValue, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# marks a node given by its id as NOT connected
	#
	# return True or False
	def markNodeAsNotConnected(self, nodeId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# marks a node given by its id as connected
	#
	# return True or False
	def markNodeAsConnected(self, nodeId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# Deletes a sensor alert given by its sensor alert id.
	#
	# return True or False
	def deleteSensorAlert(self, sensorAlertId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# Deletes a node given by its node id.
	#
	# return True or False
	def deleteNode(self, nodeId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# checks if the alert system is active or not
	#
	# return True or False
	def isAlertSystemActive(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# updates the states of the sensors of a node in the database
	# (given in a tuple of (remoteSensorId, state))
	#
	# return True or False
	def updateSensorState(self, nodeId, stateList, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# updates the data of the sensors of a node in the database
	# (given in a tuple of (remoteSensorId, data))
	#
	# return True or False
	def updateSensorData(self, nodeId, dataList, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# Updates the time the sensor send an update given by sensorId.
	#
	# return True or False
	def updateSensorTime(self, sensorId, logger=None):
		raise NotImplemented("Function not implemented yet.")


	# closes db for usage
	#
	# no return value
	def close(self, logger=None):
		raise NotImplemented("Function not implemented yet.")


# class for using sqlite as storage backend
class Sqlite(_Storage):

	def __init__(self, storagePath, globalData):

		# import the needed package
		import sqlite3

		self.globalData = globalData
		self.logger = self.globalData.logger

		# version of server
		self.version = self.globalData.version
		self.rev = self.globalData.rev
		self.dbVersion = self.globalData.dbVersion

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# path to the sqlite database
		self.storagePath = storagePath

		# sqlite is not thread safe => use lock
		self.dbLock = threading.Semaphore(1)

		# check if database exists
		# if not create one
		if os.path.exists(self.storagePath) == False:

			self.logger.info("[%s]: No database found. Creating '%s'."
			% (self.fileName, self.storagePath))

			self.conn = sqlite3.connect(self.storagePath,
				check_same_thread=False)
			self.cursor = self.conn.cursor()
			uniqueID = self._generateUniqueId()
			self._createStorage(uniqueID)
		else:
			self.conn = sqlite3.connect(self.storagePath,
				check_same_thread=False)
			self.cursor = self.conn.cursor()

			# check if the versions are compatible
			self.checkVersionAndClearConflict()


	# internal function that checks if the username is known
	def _usernameInDb(self, username):

		# check if the username does exist => if not node is not known
		self.cursor.execute("SELECT id FROM nodes WHERE username = ? ",
			(username, ))
		result = self.cursor.fetchall()

		# return if username was found or not
		if len(result) == 0:
			return False
		else:
			return True


	# internal function that generates a unique id for this server instance
	def _generateUniqueId(self):

		# generate unique id for this installation
		utcTimestamp = int(time.time())
		uniqueString = socket.gethostname() \
			+ struct.pack("d", utcTimestamp) \
			+ os.urandom(200)
		sha256 = hashlib.sha256()
		sha256.update(uniqueString)
		uniqueID = sha256.hexdigest()

		return uniqueID


	# Internal function that converts a tuple that is fetched from the
	# database by "SELECT * FROM nodes" to an node object.
	#
	# returns a node object
	def _convertNodeTupleToObj(self, nodeTuple):
		node = Node()
		node.id = nodeTuple[0]
		node.hostname = nodeTuple[1]
		node.username = nodeTuple[2]
		node.nodeType = nodeTuple[3]
		node.instance = nodeTuple[4]
		node.connected = (nodeTuple[5] == 1)
		node.version = nodeTuple[6]
		node.rev = nodeTuple[7]
		node.persistent = (nodeTuple[8] == 1)
		return node


	# internal function that gets the id of a node when a username is given
	def _getNodeId(self, username):

		# check if the username does exist
		if self._usernameInDb(username):
			# get id of username
			self.cursor.execute("SELECT id FROM nodes WHERE username = ? ",
				(username, ))
			result = self.cursor.fetchall()

			return result[0][0]
		else:
			raise ValueError("Node id was not found.")


	# Internal function that gets the alert from the database given
	# by its id.
	#
	# return an alert object or None
	def _getAlertById(self, alertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		alert = None
		try:
			self.cursor.execute("SELECT * FROM alerts "
				+ "WHERE id = ?", (alertId, ))

			result = self.cursor.fetchall()

			if len(result) == 1:
				alert = Alert()
				alert.alertId = result[0][0]
				alert.nodeId = result[0][1]
				alert.remoteAlertId = result[0][2]
				alert.description = result[0][3]

				# Set alert levels for alert.
				alertLevels = self._getAlertAlertLevels(alert.alertId,
					logger)
				if alertLevels is None:
					logger.error("[%s]: Not able to get alert levels for "
						% self.fileName
						+ "alert with id %d."
						% alert.alertId)

					return None
				alert.alertLevels = alertLevels

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "alert with id %d." % alertId)

			return None

		return alert


	# Internal function that gets the manager from the database given
	# by its id.
	#
	# return a manager object or None
	def _getManagerById(self, managerId, logger=None):
		
		# Set logger instance to use.
		if not logger:
			logger = self.logger

		manager = None
		try:
			self.cursor.execute("SELECT * FROM managers "
				+ "WHERE id = ?", (managerId, ))

			result = self.cursor.fetchall()

			if len(result) == 1:
				manager = Manager()
				manager.managerId = result[0][0]
				manager.nodeId = result[0][1]
				manager.description = result[0][2]

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "manager with id %d." % managerId)

			return None

		return manager


	# Internal function that gets the node from the database given by its id.
	#
	# return a node object or None
	def _getNodeById(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("SELECT * FROM nodes "
				+ "WHERE id = ?", (nodeId, ))

			result = self.cursor.fetchall()
		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "node with id %d." % nodeId)

			return None

		if len(result) == 1:
			try:
				return self._convertNodeTupleToObj(result[0])
			except Exception as e:
				logger.exception("[%s]: Not able to convert " % self.fileName
					+ "node data for id %d to object." % nodeId)

		return None


	# Internal function that gets the sensor from the database given by its id.
	#
	# return a sensor object or None
	def _getSensorById(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		sensor = None
		try:
			self.cursor.execute("SELECT * FROM sensors "
				+ "WHERE id = ?", (sensorId, ))

			result = self.cursor.fetchall()

			if len(result) == 1:
				sensor = Sensor()
				sensor.sensorId = result[0][0]
				sensor.nodeId = result[0][1]
				sensor.remoteSensorId = result[0][2]
				sensor.description = result[0][3]
				sensor.state = result[0][4]
				sensor.lastStateUpdated = result[0][5]
				sensor.alertDelay = result[0][6]
				sensor.dataType = result[0][7]

				# Set alert levels for sensor.
				alertLevels = self._getSensorAlertLevels(sensor.sensorId,
					logger)
				if alertLevels is None:
					logger.error("[%s]: Not able to get alert levels for "
						% self.fileName
						+ "sensor with id %d."
						% sensor.sensorId)

					return None
				sensor.alertLevels = alertLevels

				# Extract sensor data.
				if sensor.dataType == SensorDataType.NONE:
					sensor.data = None

				elif sensor.dataType == SensorDataType.INT:
					self.cursor.execute("SELECT data "
						+ "FROM sensorsDataInt "
						+ "WHERE sensorId = ?",
						(sensor.sensorId, ))
					subResult = self.cursor.fetchall()

					if len(subResult) != 1:
						logger.error("[%s]: Sensor data for sensor with id %d "
							% (self.fileName, sensor.sensorId)
							+ "was not found.")

						return None
					sensor.data = subResult[0][0]

				elif sensor.dataType == SensorDataType.FLOAT:
					self.cursor.execute("SELECT data "
						+ "FROM sensorsDataFloat "
						+ "WHERE sensorId = ?",
						(sensor.sensorId, ))
					subResult = self.cursor.fetchall()

					if len(subResult) != 1:
						logger.error("[%s]: Sensor data for sensor with id %d "
							% (self.fileName, sensor.sensorId)
							+ "was not found.")

						return None
					sensor.data = subResult[0][0]

				else:
					logger.error("[%s]: Not able to get sensor with id %d. "
						% (self.fileName, sensor.sensorId)
						+ "Data type in database unknown.")

					return None
				
		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "sensor with id %d." % sensorId)

			return None

		return sensor


	# internal function that gets the sensor id of a sensor when the id
	# of a node is given and the remote sensor id that is used
	# by the node internally
	#
	# return sensorId or raised Exception
	def _getSensorId(self, nodeId, remoteSensorId):

		# get sensorId from database
		self.cursor.execute("SELECT id FROM sensors "
			+ "WHERE nodeId = ? "
			+ "AND remoteSensorId = ?", (nodeId, remoteSensorId))
		result = self.cursor.fetchall()

		if len(result) != 1:
			raise ValueError("Sensor does not exist in database.")

		sensorId = result[0][0]

		return sensorId


	# internal function that gets the alert id of an alert when the id
	# of a node is given and the remote alert id that is used
	# by the node internally
	#
	# return alertId or raised Exception
	def _getAlertId(self, nodeId, remoteAlertId):

		# get alertId from database
		self.cursor.execute("SELECT id FROM alerts "
			+ "WHERE nodeId = ? "
			+ "AND remoteAlertId = ?", (nodeId, remoteAlertId))
		result = self.cursor.fetchall()

		if len(result) != 1:
			raise ValueError("Alert does not exist in database.")

		alertId = result[0][0]

		return alertId


	# internal function that gets the manager id of a manager when the id
	# of a node is given
	#
	# return managerId or raised Exception
	def _getManagerId(self, nodeId):

		# get managerId from database
		self.cursor.execute("SELECT id FROM managers "
			+ "WHERE nodeId = ?", (nodeId, ))
		result = self.cursor.fetchall()

		if len(result) != 1:
			raise ValueError("Manager does not exist in database.")

		managerId = result[0][0]

		return managerId


	# internal function that gets the unique id from the database
	#
	# return unique id
	# or None
	def _getUniqueID(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		# if unique id already cached => return it
		if not self.globalData.uniqueID is None:
			return self.globalData.uniqueID

		try:
			self.cursor.execute("SELECT value "
				+ "FROM internals WHERE type=?", ("uniqueID", ))
			self.globalData.uniqueID = self.cursor.fetchall()[0][0]
		except Exception as e:
			logger.exception("[%s]: Not able to get the unique id."
				% self.fileName)

		return self.globalData.uniqueID


	# internal function that acquires the lock
	def _acquireLock(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		logger.debug("[%s]: Acquire lock." % self.fileName)
		self.dbLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		logger.debug("[%s]: Release lock." % self.fileName)
		self.dbLock.release()


	# internal function that creates the database
	# (should only be called if the database does not exist)
	#
	# no return value but raise exception if it fails
	def _createStorage(self, uniqueID):

		# create internals table
		self.cursor.execute("CREATE TABLE internals ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "type TEXT NOT NULL UNIQUE, "
			+ "value TEXT NOT NULL)")

		# insert version of server
		self.cursor.execute("INSERT INTO internals ("
			+ "type, "
			+ "value) VALUES (?, ?)", ("version", self.version))

		# insert db version of server
		self.cursor.execute("INSERT INTO internals ("
			+ "type, "
			+ "value) VALUES (?, ?)", ("dbversion", self.dbVersion))

		# insert unique id
		self.cursor.execute("INSERT INTO internals ("
			+ "type, "
			+ "value) VALUES (?, ?)", ("uniqueID", uniqueID))

		# create options table
		self.cursor.execute("CREATE TABLE options ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "type TEXT NOT NULL UNIQUE, "
			+ "value REAL NOT NULL)")

		# insert option to activate/deactivate alert system
		# (0 = deactivated, 1 = activated)
		self.cursor.execute("INSERT INTO options ("
			+ "type, "
			+ "value) VALUES (?, ?)", ("alertSystemActive", 0))

		# create nodes table
		self.cursor.execute("CREATE TABLE nodes ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "hostname TEXT NOT NULL, "
			+ "username TEXT NOT NULL UNIQUE, "
			+ "nodeType TEXT NOT NULL, "
			+ "instance TEXT NOT NULL, "
			+ "connected INTEGER NOT NULL, "
			+ "version REAL NOT NULL, "
			+ "rev INTEGER NOT NULL, "
			+ "persistent INTEGER NOT NULL)")

		# create sensors table
		self.cursor.execute("CREATE TABLE sensors ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteSensorId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "lastStateUpdated INTEGER NOT NULL, "
			+ "alertDelay INTEGER NOT NULL, "
			+ "dataType INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create sensorsAlertLevels table
		self.cursor.execute("CREATE TABLE sensorsAlertLevels ("
			+ "sensorId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "PRIMARY KEY(sensorId, alertLevel), "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# Create sensorsDataInt table.
		self.cursor.execute("CREATE TABLE sensorsDataInt ("
			+ "sensorId INTEGER NOT NULL PRIMARY KEY, "
			+ "data INTEGER NOT NULL, "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# Create sensorsDataFloat table.
		self.cursor.execute("CREATE TABLE sensorsDataFloat ("
			+ "sensorId INTEGER NOT NULL PRIMARY KEY, "
			+ "data REAL NOT NULL, "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create sensorAlerts table
		self.cursor.execute("CREATE TABLE sensorAlerts ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "sensorId INTEGER NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "timeReceived INTEGER NOT NULL, "
			+ "dataJson TEXT NOT NULL,"
			+ "changeState INTEGER NOT NULL, "
			+ "hasLatestData INTEGER NOT NULL, "
			+ "dataType INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id), "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# Create sensorAlertsDataInt table.
		self.cursor.execute("CREATE TABLE sensorAlertsDataInt ("
			+ "sensorAlertId INTEGER NOT NULL PRIMARY KEY, "
			+ "data INTEGER NOT NULL, "
			+ "FOREIGN KEY(sensorAlertId) REFERENCES sensorAlerts(id))")

		# Create sensorAlertsDataFloat table.
		self.cursor.execute("CREATE TABLE sensorAlertsDataFloat ("
			+ "sensorAlertId INTEGER NOT NULL PRIMARY KEY, "
			+ "data REAL NOT NULL, "
			+ "FOREIGN KEY(sensorAlertId) REFERENCES sensorAlerts(id))")

		# create alerts table
		self.cursor.execute("CREATE TABLE alerts ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteAlertId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create alertsAlertLevels table
		self.cursor.execute("CREATE TABLE alertsAlertLevels ("
			+ "alertId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "PRIMARY KEY(alertId, alertLevel), "
			+ "FOREIGN KEY(alertId) REFERENCES alerts(id))")

		# create managers table
		self.cursor.execute("CREATE TABLE managers ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# commit all changes
		self.conn.commit()


	# Internal function that deletes the database
	# (should only be called if parts of the database do exist)
	#
	# no return value but raise exception if it fails
	def _deleteStorage(self):

		# Delete all tables from the database to clear the old version.
		self.cursor.execute("DROP TABLE IF EXISTS internals")
		self.cursor.execute("DROP TABLE IF EXISTS options")
		self.cursor.execute("DROP TABLE IF EXISTS sensorAlertsDataInt")
		self.cursor.execute("DROP TABLE IF EXISTS sensorAlertsDataFloat")
		self.cursor.execute("DROP TABLE IF EXISTS sensorAlerts")
		self.cursor.execute("DROP TABLE IF EXISTS sensorsAlertLevels")
		self.cursor.execute("DROP TABLE IF EXISTS sensorsDataInt")
		self.cursor.execute("DROP TABLE IF EXISTS sensorsDataFloat")
		self.cursor.execute("DROP TABLE IF EXISTS sensors")
		self.cursor.execute("DROP TABLE IF EXISTS alertsAlertLevels")
		self.cursor.execute("DROP TABLE IF EXISTS alerts")
		self.cursor.execute("DROP TABLE IF EXISTS managers")
		self.cursor.execute("DROP TABLE IF EXISTS nodes")

		# commit all changes
		self.conn.commit()


	# Internal function that deletes all alert data corresponding
	# to the given node id.
	#
	# Returns true if everything worked fine.
	def _deleteAlertsForNodeId(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			# Get all alert ids that are connected to
			# the node.
			self.cursor.execute("SELECT id FROM alerts "
				+ "WHERE nodeId = ?", (nodeId, ))
			result = self.cursor.fetchall()

			# Delete all alert alert levels and alerts of
			# this node
			for alertIdResult in result:

				self.cursor.execute("DELETE FROM "
					+ "alertsAlertLevels "
					+ "WHERE alertId = ?",
					(alertIdResult[0], ))

				self.cursor.execute("DELETE FROM alerts "
					+ "WHERE id = ?",
					(alertIdResult[0], ))

			# Commit all changes.
			self.conn.commit()

		except Exception as e:
			logger.exception("[%s]: Not able to "
				% self.fileName
				+ "delete alerts for node with id %d."
				% nodeId)

			return False

		return True


	# Internal function that deletes all manager data corresponding
	# to the given node id.
	#
	# Returns true if everything worked fine.
	def _deleteManagerForNodeId(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("DELETE FROM managers "
				+ "WHERE nodeId = ?",
				(nodeId, ))

			# Commit all changes.
			self.conn.commit()

		except Exception as e:
			logger.exception("[%s]: Not able to "
				% self.fileName
				+ "delete manager for node with id %d."
				% nodeId)

			return False

		return True


	# Internal function that deletes all sensor data corresponding
	# to the given node id.
	#
	# Returns true if everything worked fine.
	def _deleteSensorsForNodeId(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			# Get all sensor ids that are connected to
			# the old sensor.
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = ? ", (nodeId, ))
			result = self.cursor.fetchall()

			# Delete all sensor alert levels, data and sensors of
			# this node.
			for sensorIdResult in result:

				# Get all sensor alert ids that are connected to
				# the this sensor.
				self.cursor.execute("SELECT id FROM sensorAlerts "
					+ "WHERE sensorId = ? ",
					(sensorIdResult[0], ))
				sensorAlertIdsresult = self.cursor.fetchall()

				# Delete all sensor alert data connected to the corresponding
				# sensor alert.
				for sensorAlertIdResult in sensorAlertIdsresult:
					sensorAlertId = sensorAlertIdResult[0]
					if not self._deleteSensorAlert(sensorAlertId, logger):
						return False

				self.cursor.execute("DELETE FROM "
					+ "sensorsAlertLevels "
					+ "WHERE sensorId = ?",
					(sensorIdResult[0], ))

				self.cursor.execute("DELETE FROM "
					+ "sensorsDataInt "
					+ "WHERE sensorId = ?",
					(sensorIdResult[0], ))

				self.cursor.execute("DELETE FROM "
					+ "sensorsDataFloat "
					+ "WHERE sensorId = ?",
					(sensorIdResult[0], ))

				self.cursor.execute("DELETE FROM sensors "
					+ "WHERE id = ?",
					(sensorIdResult[0], ))

			# Commit all changes.
			self.conn.commit()

		except Exception as e:
			logger.exception("[%s]: Not able to "
				% self.fileName
				+ "delete sensors for node with id %d."
				% nodeId)

			return False

		return True


	# Internal function thatdeletes a sensor alert given by its
	# sensor alert id.
	#
	# Returns true if everything worked fine.
	def _deleteSensorAlert(self, sensorAlertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("DELETE FROM sensorAlertsDataInt "
				+ "WHERE sensorAlertId = ?",
				(sensorAlertId, ))

			self.cursor.execute("DELETE FROM sensorAlertsDataFloat "
				+ "WHERE sensorAlertId = ?",
				(sensorAlertId, ))

			self.cursor.execute("DELETE FROM sensorAlerts "
				+ "WHERE id = ?",
				(sensorAlertId, ))
		except Exception as e:
			logger.exception("[%s]: Not able to delete "
				% self.fileName
				+ "sensor alert with id %d."
				% sensorAlertId)

			return False

		# commit all changes
		self.conn.commit()

		return True


	# Internal function that gets all alert levels for a specific
	# alert given by alertId
	#
	# return list of alertLevels
	# or None
	def _getAlertAlertLevels(self, alertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertsAlertLevels "
				+ "WHERE alertId = ?", (alertId, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "alert levels for alert with id %d." % alertId)

			# return None if action failed
			return None

		# return list of alertLevels
		return map(lambda x: x[0], result)


	# Internal function that gets all alert levels for a specific
	# sensor given by sensorId
	#
	# return list of alertLevel
	# or None
	def _getSensorAlertLevels(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM sensorsAlertLevels "
				+ "WHERE sensorId = ?", (sensorId, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "alert levels for sensor with id %d." % sensorId)

			# return None if action failed
			return None

		# return list of alertLevel
		return map(lambda x: x[0], result)


	# Internal function that inserts sensor data according to its type.
	#
	# Returns true if everything worked fine.
	def _insertSensorData(self, sensorId, dataType, data, logger=None):

		# Depending on the data type of the sensor add it to the
		# corresponding table.
		if dataType == SensorDataType.NONE:
			return True

		elif dataType == SensorDataType.INT:
			try:
				self.cursor.execute("INSERT INTO sensorsDataInt ("
					+ "sensorId, "
					+ "data) VALUES (?, ?)",
					(sensorId,
					data))
			except Exception as e:
				logger.exception("[%s]: Not able to "
					% self.fileName
					+ "add sensor's integer data.")

				return False

		elif dataType == SensorDataType.FLOAT:
			try:
				self.cursor.execute("INSERT INTO sensorsDataFloat ("
					+ "sensorId, "
					+ "data) VALUES (?, ?)",
					(sensorId,
					data))
			except Exception as e:
				logger.exception("[%s]: Not able to "
					% self.fileName
					+ "add sensor's floating point data.")

				return False

		else:
			logger.error("[%s]: Data type not known. Not able to "
				% self.fileName
				+ "add sensor.")

			return False

		return True


	# Internal function that inserts sensor alert data according to its type.
	#
	# Returns true if everything worked fine.
	def _insertSensorAlertData(self, sensorAlertId, dataType, data,
		logger=None):

		# Depending on the data type of the sensor alert add it to the
		# corresponding table.
		if dataType == SensorDataType.NONE:
			return True

		elif dataType == SensorDataType.INT:
			try:
				self.cursor.execute("INSERT INTO sensorAlertsDataInt ("
					+ "sensorAlertId, "
					+ "data) VALUES (?, ?)",
					(sensorAlertId,
					data))
			except Exception as e:
				logger.exception("[%s]: Not able to "
					% self.fileName
					+ "add sensorAlert's integer data.")

				return False

		elif dataType == SensorDataType.FLOAT:
			try:
				self.cursor.execute("INSERT INTO sensorAlertsDataFloat ("
					+ "sensorAlertId, "
					+ "data) VALUES (?, ?)",
					(sensorAlertId,
					data))
			except Exception as e:
				logger.exception("[%s]: Not able to "
					% self.fileName
					+ "add sensorAlert's floating point data.")

				return False

		else:
			logger.error("[%s]: Data type not known. Not able to "
				% self.fileName
				+ "add sensorAlert.")

			return False

		return True


	# checks the version of the server and the version in the database
	# and clears every compatibility issue
	#
	# no return value but raise exception if it fails
	def checkVersionAndClearConflict(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# get version from the current database
		self.cursor.execute("SELECT value FROM internals "
			+ "WHERE type = ?",
			("dbversion", ))
		result = self.cursor.fetchall()

		# In case the current database does not have any db version
		# set it.
		if result:
			currDbVersion = int(result[0][0])
		else:
			currDbVersion = -1

		# If the versions are not compatible
		# => update database schema.
		if currDbVersion < self.dbVersion:

			logger.info("[%s]: Needed database version "
				% self.fileName
				+ "'%d' not compatible "
				% self.dbVersion
				+ "with current database layout version '%d'. "
				% currDbVersion
				+ "Updating database.")

			# get old uniqueId to keep it
			uniqueID = self._getUniqueID()
			if uniqueID is None:
				uniqueID = self._generateUniqueId()

			self._deleteStorage()

			# create new database
			self._createStorage(uniqueID)

			# commit all changes
			self.conn.commit()

		# Raise an exception if database layout version
		# is newer than the one we need.
		elif currDbVersion > self.dbVersion:
			raise ValueError("Current database layout version ('%d') "
				% currDbVersion
				+ "newer than the one this server uses ('%d')."
				% self.dbVersion)

		self._releaseLock(logger)


	# adds a node if it does not exist or changes the registered
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType, instance, version, rev,
		persistent, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# check if a node with the same username already exists
		# => if not add node
		if not self._usernameInDb(username):

			logger.info("[%s]: Node with username '%s' does not exist "
				% (self.fileName, username)
				+ "in database. Adding it.")

			try:
				# NOTE: connection state is changed later on
				# in the registration process
				self.cursor.execute("INSERT INTO nodes ("
					+ "hostname, "
					+ "username, "
					+ "nodeType, "
					+ "instance, "
					+ "connected, "
					+ "version, "
					+ "rev, "
					+ "persistent) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
					(hostname, username, nodeType, instance, 0, version, rev,
					persistent))
			except Exception as e:
				logger.exception("[%s]: Not able to add node."
					% self.fileName)

				self._releaseLock(logger)

				return False

		# if a node with this username exists
		# => check if everything is the same
		else:

			logger.info("[%s]: Node with username '%s' already exists "
				% (self.fileName, username)
				+ "in database.")

			nodeId = self._getNodeId(username)

			# get hostname, nodeType, version, revision, persistent
			try:
				self.cursor.execute("SELECT hostname, "
					+ "nodeType, "
					+ "instance, "
					+ "version, "
					+ "rev, "
					+ "persistent "
					+ "FROM nodes WHERE id = ? ",
					(nodeId, ))
				result = self.cursor.fetchall()
				dbHostname = result[0][0]
				dbNodeType = result[0][1]
				dbInstance = result[0][2]
				dbVersion = result[0][3]
				dbRev = result[0][4]
				dbPersistent = result[0][5]

			except Exception as e:
				logger.exception("[%s]: Not able to get node information."
					% self.fileName)

				self._releaseLock(logger)

				return False

			# change hostname if it had changed
			if dbHostname != hostname:

				logger.info("[%s]: Hostname of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbHostname, hostname))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "hostname = ? "
						+ "WHERE id = ?",
						(hostname, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update hostname of node.")

					self._releaseLock(logger)

					return False

			# change instance if it had changed
			if dbInstance != instance:

				logger.info("[%s]: Instance of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbInstance, instance))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "instance = ? "
						+ "WHERE id = ?",
						(instance, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update instance of node.")

					self._releaseLock(logger)

					return False

			# change version if it had changed
			if dbVersion != version:

				logger.info("[%s]: Version of node has changed "
					% self.fileName
					+ "from '%.3f' to '%.3f'. Updating database."
					% (dbVersion, version))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "version = ? "
						+ "WHERE id = ?",
						(version, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update version of node.")

					self._releaseLock(logger)

					return False

			# change revision if it had changed
			if dbRev != rev:

				logger.info("[%s]: Revision of node has changed "
					% self.fileName
					+ "from '%d' to '%d'. Updating database."
					% (dbRev, rev))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "rev = ? "
						+ "WHERE id = ?",
						(rev, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update revision of node.")

					self._releaseLock(logger)

					return False

			# change persistent if it had changed
			if dbPersistent != persistent:

				logger.info("[%s]: Persistent flag of node has changed "
					% self.fileName
					+ "from '%d' to '%d'. Updating database."
					% (dbPersistent, persistent))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "persistent = ? "
						+ "WHERE id = ?",
						(persistent, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update persistent flag of node.")

					self._releaseLock(logger)

					return False

			# if node type has changed
			# => delete sensors/alerts/manager information of old node
			# and change node type
			if dbNodeType != nodeType:

				logger.info("[%s]: Type of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbNodeType, nodeType))

				# if old node had type "sensor"
				# => delete all sensors
				if dbNodeType == "sensor":

					if not self._deleteSensorsForNodeId(nodeId, logger):
						self._releaseLock(logger)

						return False

				# if old node had type "alert"
				# => delete all alerts
				elif dbNodeType == "alert":

					if not self._deleteAlertsForNodeId(nodeId, logger):
						self._releaseLock(logger)

						return False

				# if old node had type "manager"
				# => delete all manager information
				elif dbNodeType == "manager":

					if not self._deleteManagerForNodeId(nodeId, logger):
						self._releaseLock(logger)

						return False

				# if old node had type "server"
				# => delete all sensor information
				elif dbNodeType == "server":

					if not self._deleteSensorsForNodeId(nodeId, logger):
						self._releaseLock(logger)

						return False

				# node type in database not known
				else:

					logger.error("[%s]: Unknown node type "
						% self.fileName
						+ "when deleting old sensors/alerts/manager "
						+ "information.")

					self._releaseLock(logger)

					return False

				# update node type
				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "nodeType = ? "
						+ "WHERE id = ?",
						(nodeType, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update type of node.")

					self._releaseLock(logger)

					return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# adds/updates the data that is given by the node for the sensors
	# to the database
	#
	# return True or False
	def addSensors(self, username, sensors, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logger.exception("[%s]: Not able to get node id."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# add/update all sensors
		for sensor in sensors:

			# Extract sensor data (field does not exist
			# if data type is "none").
			if sensor["dataType"] == SensorDataType.NONE:
				sensorData = None
			else:
				sensorData = sensor["data"]

			# check if a sensor with the same remote id for this node
			# already exists in the database
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = ? AND remoteSensorId = ?",
				(nodeId, sensor["clientSensorId"]))
			result = self.cursor.fetchall()

			# if the sensor does not exist
			# => add it
			if not result:

				logger.info("[%s]: Sensor with client id '%d' does not "
					% (self.fileName, int(sensor["clientSensorId"]))
					+ "exist in database. Adding it.")

				# add sensor to database
				try:
					utcTimestamp = int(time.time())
					self.cursor.execute("INSERT INTO sensors ("
						+ "nodeId, "
						+ "remoteSensorId, "
						+ "description, "
						+ "state, "
						+ "lastStateUpdated, "
						+ "alertDelay, "
						+ "dataType) VALUES (?, ?, ?, ?, ?, ?, ?)",
						(nodeId,
						sensor["clientSensorId"],
						sensor["description"],
						sensor["state"],
						utcTimestamp,
						sensor["alertDelay"],
						sensor["dataType"]))
				except Exception as e:
					logger.exception("[%s]: Not able to add sensor."
						% self.fileName)

					self._releaseLock(logger)

					return False

				# get sensorId of current added sensor
				sensorId = self.cursor.lastrowid

				# add sensor alert levels to database
				try:
					for alertLevel in sensor["alertLevels"]:
						self.cursor.execute("INSERT INTO sensorsAlertLevels ("
							+ "sensorId, "
							+ "alertLevel) VALUES (?, ?)",
							(sensorId,
							alertLevel))
				except Exception as e:
					logger.exception("[%s]: Not able to "
						% self.fileName
						+ "add sensor's alert levels.")

					self._releaseLock(logger)

					return False

				# Depending on the data type of the sensor add it to the
				# corresponding table.
				if not self._insertSensorData(sensorId,
					sensor["dataType"], sensorData, logger):

					logger.error("[%s]: Not able to add data for newly "
						% self.fileName
						+ "added sensor.")

					self._releaseLock(logger)

					return False

			# if the sensor does already exist
			# => check if everything is the same
			else:

				logger.info("[%s]: Sensor with client id '%d' already "
					% (self.fileName, int(sensor["clientSensorId"]))
					+ "exists in database.")

				# get sensorId, description, alertDelay and dataType
				try:
					sensorId = self._getSensorId(nodeId,
						int(sensor["clientSensorId"]))

					self.cursor.execute("SELECT description, "
						+ "alertDelay, "
						+ "dataType "
						+ "FROM sensors "
						+ "WHERE id = ?",
						(sensorId, ))
					result = self.cursor.fetchall()
					dbDescription = result[0][0]
					dbAlertDelay = result[0][1]
					dbDataType = result[0][2]

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get sensor information.")

					self._releaseLock(logger)

					return False

				# change description if it had changed
				if dbDescription != str(sensor["description"]):

					logger.info("[%s]: Description of sensor has changed "
						% self.fileName
						+ "from '%s' to '%s'. Updating database."
						% (dbDescription, str(sensor["description"])))

					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "description = ? "
							+ "WHERE id = ?",
							(str(sensor["description"]), sensorId))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "update description of sensor.")

						self._releaseLock(logger)

						return False

				# change alert delay if it had changed
				if dbAlertDelay != int(sensor["alertDelay"]):

					logger.info("[%s]: Alert delay of sensor has changed "
						% self.fileName
						+ "from '%d' to '%d'. Updating database."
						% (dbAlertDelay, int(sensor["alertDelay"])))

					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "alertDelay = ? "
							+ "WHERE id = ?",
							(int(sensor["alertDelay"]), sensorId))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "update alert delay of sensor.")

						self._releaseLock(logger)

						return False

				# Change data type if it had changed (and remove
				# old data).
				if dbDataType != sensor["dataType"]:

					logger.info("[%s]: Data type of sensor has changed "
						% self.fileName
						+ "from '%d' to '%d'. Updating database."
						% (dbDataType, sensor["dataType"]))

					# Remove old data entry of sensor.
					try:
						self.cursor.execute("DELETE FROM "
							+ "sensorsDataInt "
							+ "WHERE sensorId = ?",
							(sensorId, ))

						self.cursor.execute("DELETE FROM "
							+ "sensorsDataFloat "
							+ "WHERE sensorId = ?",
							(sensorId, ))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "remove old data entry of sensor.")

						self._releaseLock(logger)

						return False

					# Update data type.
					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "dataType = ? "
							+ "WHERE id = ?",
							(int(sensor["dataType"]), sensorId))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "update data type of sensor.")

						self._releaseLock(logger)

						return False

					# Depending on the data type of the sensor add it to the
					# corresponding table.
					if not self._insertSensorData(sensorId,
						sensor["dataType"], sensorData, logger):

						logger.error("[%s]: Not able to add data for "
							% self.fileName
							+ "changed sensor.")

						self._releaseLock(logger)

						return False

				# get sensor alert levels from database
				try:

					self.cursor.execute("SELECT alertLevel "
						+ "FROM sensorsAlertLevels "
						+ "WHERE sensorId = ? ", (sensorId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get alert levels of the sensor.")

					self._releaseLock(logger)

					return False

				# check if the alert levels do already
				# exist in the database
				# => add alert level if it does not
				for alertLevel in sensor["alertLevels"]:

					# check if alert level already exists
					found = False
					for dbAlertLevel in result:
						if dbAlertLevel[0] == alertLevel:
							found = True
							break
					if found:
						continue

					logger.info("[%s]: Alert level '%d' of sensor does "
						% (self.fileName, alertLevel)
						+ "not exist in database. Adding it.")

					# add sensor alert level to database
					self.cursor.execute("INSERT INTO sensorsAlertLevels ("
						+ "sensorId, "
						+ "alertLevel) VALUES (?, ?)",
						(sensorId, alertLevel))

				# get updated sensor alert levels from database
				try:

					self.cursor.execute("SELECT alertLevel "
						+ "FROM sensorsAlertLevels "
						+ "WHERE sensorId = ? ", (sensorId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get updated alert levels of the sensor.")

					self._releaseLock(logger)

					return False

				# check if the alert levels from the database
				# do still exist in the sensor
				# => delete alert level if it does not
				for dbAlertLevel in result:

					# check if database alert level does exist
					found = False
					for alertLevel in sensor["alertLevels"]:
						if dbAlertLevel[0] == alertLevel:
							found = True
							break
					if found:
						continue

					logger.info("[%s]: Alert level '%d' in database does "
						% (self.fileName, dbAlertLevel[0])
						+ "not exist anymore for sensor. Deleting it.")

					self.cursor.execute("DELETE FROM sensorsAlertLevels "
						+ "WHERE sensorId = ? AND alertLevel = ?",
						(sensorId, dbAlertLevel[0]))

		# get updated sensors from database
		try:

			self.cursor.execute("SELECT id, "
				+ "remoteSensorId "
				+ "FROM sensors "
				+ "WHERE nodeId = ? ", (nodeId, ))
			result = self.cursor.fetchall()

		except Exception as e:
			logger.exception("[%s]: Not able to " % self.fileName
				+ "get updated sensors from database.")

			self._releaseLock(logger)

			return False

		# check if the sensors from the database
		# do still exist for the node
		# => delete sensor if it does not
		for dbSensor in result:

			found = False
			for sensor in sensors:
				if dbSensor[1] == int(sensor["clientSensorId"]):
					found = True
					break
			if found:
				continue

			logger.info("[%s]: Sensor with client id '%d' in database "
				% (self.fileName, dbSensor[1])
				+ "does not exist anymore for the node. Deleting it.")

			try:
				# Delete sensor alertLevels.
				self.cursor.execute("DELETE FROM sensorsAlertLevels "
					+ "WHERE sensorId = ?",
					(dbSensor[0], ))

				# Delete old data entries (if any exist at all).
				self.cursor.execute("DELETE FROM "
					+ "sensorsDataInt "
					+ "WHERE sensorId = ?",
					(dbSensor[0], ))
				self.cursor.execute("DELETE FROM "
					+ "sensorsDataFloat "
					+ "WHERE sensorId = ?",
					(dbSensor[0], ))

				# Finally, delete sensor.
				self.cursor.execute("DELETE FROM sensors "
					+ "WHERE id = ?",
					(dbSensor[0], ))
			except Exception as e:
				logger.exception("[%s]: Not able to delete sensor."
					% self.fileName)

				self._releaseLock(logger)

				return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# adds/updates the data that is given by the node for the alerts
	# to the database
	#
	# return True or False
	def addAlerts(self, username, alerts, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logger.exception("[%s]: Not able to get node id."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# add/update all alerts
		for alert in alerts:

			# check if an alert with the same remote id for this node
			# already exists in the database
			self.cursor.execute("SELECT id FROM alerts "
				+ "WHERE nodeId = ? AND remoteAlertId = ?",
				(nodeId, int(alert["clientAlertId"])))
			result = self.cursor.fetchall()

			# if the alert does not exist
			# => add it
			if len(result) == 0:

				logger.info("[%s]: Alert with client id '%d' does not "
					% (self.fileName, int(alert["clientAlertId"]))
					+ "exist in database. Adding it.")

				# add alert to database
				try:
					self.cursor.execute("INSERT INTO alerts ("
						+ "nodeId, "
						+ "remoteAlertId, "
						+ "description) VALUES (?, ?, ?)", (nodeId,
						int(alert["clientAlertId"]),
						str(alert["description"])))
				except Exception as e:
					logger.exception("[%s]: Not able to add alert."
						% self.fileName)

					self._releaseLock(logger)

					return False

				# get alertId of current added alert
				try:
					alertId = self._getAlertId(nodeId,
						int(alert["clientAlertId"]))
				except Exception as e:
					logger.exception("[%s]: Not able to get alertId."
						% self.fileName)

					self._releaseLock(logger)

					return False

				# add alert alert levels to database
				try:
					for alertLevel in alert["alertLevels"]:
						self.cursor.execute("INSERT INTO alertsAlertLevels ("
							+ "alertId, "
							+ "alertLevel) VALUES (?, ?)",
							(alertId, alertLevel))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "add alert alert levels.")

					self._releaseLock(logger)

					return False

			# if the alert does already exist
			# => check if everything is the same
			else:

				logger.info("[%s]: Alert with client id '%d' already "
					% (self.fileName, int(alert["clientAlertId"]))
					+ "exists in database.")

				# get alertId and description
				try:
					alertId = self._getAlertId(nodeId,
						int(alert["clientAlertId"]))

					self.cursor.execute("SELECT description "
						+ "FROM alerts "
						+ "WHERE id = ?",
						(alertId, ))
					result = self.cursor.fetchall()
					dbDescription = result[0][0]

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get alert information.")

					self._releaseLock(logger)

					return False

				# change description if it had changed
				if dbDescription != str(alert["description"]):

					logger.info("[%s]: Description of alert has changed "
						% self.fileName
						+ "from '%s' to '%s'. Updating database."
						% (dbDescription, str(alert["description"])))

					try:
						self.cursor.execute("UPDATE alerts SET "
							+ "description = ? "
							+ "WHERE id = ?",
							(str(alert["description"]), alertId))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "update description of alert.")

						self._releaseLock(logger)

						return False

				# get alert alert levels from database
				try:

					self.cursor.execute("SELECT alertLevel "
						+ "FROM alertsAlertLevels "
						+ "WHERE alertId = ? ", (alertId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get alert levels of the alert.")

					self._releaseLock(logger)

					return False

				# check if the alert levels do already
				# exist in the database
				# => add alert level if it does not
				for alertLevel in alert["alertLevels"]:

					# check if alert level already exists
					found = False
					for dbAlertLevel in result:
						if dbAlertLevel[0] == alertLevel:
							found = True
							break
					if found:
						continue

					logger.info("[%s]: Alert level '%d' of alert does "
						% (self.fileName, alertLevel)
						+ "not exist in database. Adding it.")

					# add alert alert level to database
					self.cursor.execute("INSERT INTO alertsAlertLevels ("
						+ "alertId, "
						+ "alertLevel) VALUES (?, ?)",
						(alertId, alertLevel))

				# get updated alert alert levels from database
				try:

					self.cursor.execute("SELECT alertLevel "
						+ "FROM alertsAlertLevels "
						+ "WHERE alertId = ? ", (alertId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get updated alert levels of the alert.")

					self._releaseLock(logger)

					return False

				# check if the alert levels from the database
				# do still exist in the alert
				# => delete alert level if it does not
				for dbAlertLevel in result:

					# check if database alert level does exist
					found = False
					for alertLevel in alert["alertLevels"]:
						if dbAlertLevel[0] == alertLevel:
							found = True
							break
					if found:
						continue

					logger.info("[%s]: Alert level '%d' in database does "
						% (self.fileName, dbAlertLevel[0])
						+ "not exist anymore for alert. Deleting it.")

					self.cursor.execute("DELETE FROM alertsAlertLevels "
						+ "WHERE alertId = ? AND alertLevel = ?",
						(alertId, dbAlertLevel[0]))

		# get updated alerts from database
		try:

			self.cursor.execute("SELECT id, "
				+ "remoteAlertId "
				+ "FROM alerts "
				+ "WHERE nodeId = ? ", (nodeId, ))
			result = self.cursor.fetchall()

		except Exception as e:
			logger.exception("[%s]: Not able to " % self.fileName
				+ "get updated alerts from database.")

			self._releaseLock(logger)

			return False

		# check if the alerts from the database
		# do still exist for the node
		# => delete alert if it does not
		for dbAlert in result:

			found = False
			for alert in alerts:
				if dbAlert[1] == int(alert["clientAlertId"]):
					found = True
					break
			if found:
				continue

			logger.info("[%s]: Alert with client id '%d' in database "
				% (self.fileName, dbAlert[1])
				+ "does not exist anymore for the node. Deleting it.")

			try:
				self.cursor.execute("DELETE FROM alertsAlertLevels "
					+ "WHERE alertId = ?",
					(dbAlert[0], ))

				self.cursor.execute("DELETE FROM alerts "
					+ "WHERE id = ?",
					(dbAlert[0], ))
			except Exception as e:
				logger.exception("[%s]: Not able to delete alert."
					% self.fileName)

				self._releaseLock(logger)

				return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# adds/updates the data that is given by the node for
	# the manager to the database
	#
	# return True or False
	def addManager(self, username, manager, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logger.exception("[%s]: Not able to get node id."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# check if a manager with the same node id
		# already exists in the database
		self.cursor.execute("SELECT id FROM managers "
			+ "WHERE nodeId = ?",
			(nodeId, ))
		result = self.cursor.fetchall()

		# if the manager does not exist
		# => add it
		if len(result) == 0:

			logger.info("[%s]: Manager does not exist "
				% self.fileName
				+ "in database. Adding it.")

			# add manager to database
			try:
				self.cursor.execute("INSERT INTO managers ("
					+ "nodeId, "
					+ "description) VALUES (?, ?)", (nodeId,
					str(manager["description"])))
			except Exception as e:
				logger.exception("[%s]: Not able to add manager."
					% self.fileName)

				self._releaseLock(logger)

				return False

		# if the manager does already exist
		# => check if everything is the same
		else:

			logger.info("[%s]: Manager already exists "
				% self.fileName
				+ "in database.")

			# get managerId and description
			try:
				managerId = self._getManagerId(nodeId)

				self.cursor.execute("SELECT description "
					+ "FROM managers "
					+ "WHERE id = ?",
					(managerId, ))
				result = self.cursor.fetchall()
				dbDescription = result[0][0]

			except Exception as e:
				logger.exception("[%s]: Not able to " % self.fileName
					+ "get manager information.")

				self._releaseLock(logger)

				return False

			# change description if it had changed
			if dbDescription != str(manager["description"]):

				logger.info("[%s]: Description of manager has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbDescription, str(manager["description"])))

				try:
					self.cursor.execute("UPDATE managers SET "
						+ "description = ? "
						+ "WHERE id = ?",
						(str(manager["description"]), managerId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update description of manager.")

					self._releaseLock(logger)

					return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# gets the id of the node by a given username
	# (usernames are unique to each node)
	#
	# return nodeId or None
	def getNodeId(self, username, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		nodeId = None
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logger.exception("[%s]: Not able to get node id."
				% self.fileName)

		self._releaseLock(logger)

		return nodeId


	# Gets the ids of all nodes
	#
	# return list of nodeIds
	def getNodeIds(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		nodeIds = list()
		try:
			self.cursor.execute("SELECT id FROM nodes")
			result = self.cursor.fetchall()

			# Unpack list of tuples of one integer to list of integers.
			nodeIds = map(lambda x: x[0], result)

		except Exception as e:
			logger.exception("[%s]: Not able to get node ids."
				% self.fileName)

		self._releaseLock(logger)

		return nodeIds


	# gets the count of the sensors of a node in the database
	#
	# return count of sensors or None
	def getSensorCount(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# get all sensors on this nodes
		sensorCount = None
		try:
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = ?", (nodeId, ))
			result = self.cursor.fetchall()
			sensorCount = len(result)
		except Exception as e:
			logger.exception("[%s]: Not able to get sensor count."
				% self.fileName)

		self._releaseLock(logger)

		return sensorCount


	# gets all data needed for the survey
	#
	# return list of tuples of (instance, version, rev)
	# or None
	def getSurveyData(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		surveyData = None
		try:
			self.cursor.execute("SELECT "
				+ "instance, "
				+ "version, "
				+ "rev "
				+ "FROM nodes")
			surveyData = self.cursor.fetchall()
		except Exception as e:
			logger.exception("[%s]: Not able to get survey data."
				% self.fileName)

		self._releaseLock(logger)

		return surveyData

	# gets the unique id from the database
	#
	# return unique id
	# or None
	def getUniqueID(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		uniqueID = self._getUniqueID()

		self._releaseLock(logger)

		return uniqueID


	# updates the states of the sensors of a node in the database
	# (given in a tuple of (remoteSensorId, state))
	#
	# return True or False
	def updateSensorState(self, nodeId, stateList, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# stateList is a list of tuples of (remoteSensorId, state)
		for stateTuple in stateList:

			try:

				# check if the sensor does exist in the database
				self.cursor.execute("SELECT id FROM sensors "
					+ "WHERE nodeId = ? "
					+ "AND remoteSensorId = ?", (nodeId, stateTuple[0]))
				result = self.cursor.fetchall()
				if len(result) != 1:
					logger.error("[%s]: Sensor does not exist in "
						% self.fileName
						+ "database.")

					self._releaseLock(logger)

					return False

				utcTimestamp = int(time.time())
				self.cursor.execute("UPDATE sensors SET "
					+ "state = ?, "
					+ "lastStateUpdated = ? "
					+ "WHERE nodeId = ? "
					+ "AND remoteSensorId = ?",
					(stateTuple[1], utcTimestamp, nodeId, stateTuple[0]))
			except Exception as e:
				logger.exception("[%s]: Not able to update sensor state."
					% self.fileName)

				self._releaseLock(logger)

				return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# updates the data of the sensors of a node in the database
	# (given in a tuple of (remoteSensorId, data))
	#
	# return True or False
	def updateSensorData(self, nodeId, dataList, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# dataList is a list of tuples of (remoteSensorId, data)
		for dataTuple in dataList:

			try:

				# Check if the sensor does exist in the database and get its
				# data type.
				self.cursor.execute("SELECT id, dataType FROM sensors "
					+ "WHERE nodeId = ? "
					+ "AND remoteSensorId = ?", (nodeId, dataTuple[0]))
				result = self.cursor.fetchall()
				if len(result) != 1:
					logger.error("[%s]: Sensor does not exist in "
						% self.fileName
						+ "database.")

					self._releaseLock(logger)

					return False

				sensorId = result[0][0]
				dataType = result[0][1]

				if dataType == SensorDataType.NONE:
					logger.error("[%s]: Sensor with remote id %d holds "
						% (self.fileName, dataTuple[0])
						+ "no data. Ignoring it.")

				elif dataType == SensorDataType.INT:
					self.cursor.execute("UPDATE sensorsDataInt SET "
						+ "data = ? "
						+ "WHERE sensorId = ?",
						(dataTuple[1],
						sensorId))

				elif dataType == SensorDataType.FLOAT:
					self.cursor.execute("UPDATE sensorsDataFloat SET "
						+ "data = ? "
						+ "WHERE sensorId = ?",
						(dataTuple[1],
						sensorId))

			except Exception as e:
				logger.exception("[%s]: Not able to update sensor data."
					% self.fileName)

				self._releaseLock(logger)

				return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True



	# Updates the time the sensor send an update given by sensorId.
	#
	# return True or False
	def updateSensorTime(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# Update time of sensor in the database.
		try:
			utcTimestamp = int(time.time())
			self.cursor.execute("UPDATE sensors SET "
				+ "lastStateUpdated = ? "
				+ "WHERE id = ?",
				(utcTimestamp, sensorId))

		except Exception as e:
			logger.exception("[%s]: Not able to update sensor time."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# gets the sensor id of a sensor when the id of a node is given
	# and the remote sensor id that is used by the node internally
	#
	# return sensorId or None
	def getSensorId(self, nodeId, remoteSensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			sensorId = self._getSensorId(nodeId, remoteSensorId)
		except Exception as e:
			logger.exception("[%s]: Not able to get sensorId from "
				% self.fileName
				+ "database.")

			self._releaseLock(logger)

			return None

		self._releaseLock(logger)

		return sensorId


	# gets the alert id of an alert when the id of a node is given
	# and the remote alert id that is used by the node internally
	#
	# return alertId or None
	def getAlertId(self, nodeId, remoteAlertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			alertId = self._getAlertId(nodeId, remoteAlertId)
		except Exception as e:
			logger.exception("[%s]: Not able to get alertId from "
				% self.fileName
				+ "database.")

			self._releaseLock(logger)

			return None

		self._releaseLock(logger)

		return alertId


	# gets all alert levels for a specific sensor given by sensorId
	#
	# return list of alertLevel
	# or None
	def getSensorAlertLevels(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		result = self._getSensorAlertLevels(sensorId, logger)

		self._releaseLock(logger)

		# return list of alertLevel
		return result


	# gets all alert levels for a specific alert given by alertId
	#
	# return list of alertLevels
	# or None
	def getAlertAlertLevels(self, alertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		result = self._getAlertAlertLevels(alertId, logger)

		self._releaseLock(logger)

		# return list of alertLevels
		return result


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, sensorId, state, dataJson, changeState,
		hasLatestData, dataType, sensorData, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# add sensor alert to database
		try:
			if changeState:
				dbChangeState = 1
			else:
				dbChangeState = 0
			if hasLatestData:
				dbHasLatestData = 1
			else:
				dbHasLatestData = 0
			utcTimestamp = int(time.time())
			self.cursor.execute("INSERT INTO sensorAlerts ("
				+ "nodeId, "
				+ "sensorId, "
				+ "state, "
				+ "timeReceived, "
				+ "dataJson, "
				+ "changeState, "
				+ "hasLatestData, "
				+ "dataType) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
				(nodeId, sensorId, state, utcTimestamp, dataJson,
				dbChangeState, dbHasLatestData, dataType))

			# Get sensorAlertId of current added sensor alert.
			sensorAlertId = self.cursor.lastrowid

			if not self._insertSensorAlertData(sensorAlertId,
				dataType, sensorData, logger):

				logger.error("[%s]: Not able to add data for newly "
					% self.fileName
					+ "added sensor alert.")

				self._releaseLock(logger)

				return False

		except Exception as e:
			logger.exception("[%s]: Not able to add sensor alert."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# gets all sensor alerts in the database
	#
	# return a list of sensorAlert objects
	# or None
	def getSensorAlerts(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		returnList = list()
		try:
			self.cursor.execute("SELECT "
				+ "sensorAlerts.id, "
				+ "sensors.id, "
				+ "sensors.nodeId, "
				+ "sensorAlerts.timeReceived, "
				+ "sensors.alertDelay, "
				+ "sensorAlerts.state, "
				+ "sensors.description, "
				+ "sensorAlerts.dataJson, "
				+ "sensorAlerts.changeState, "
				+ "sensorAlerts.hasLatestData, "
				+ "sensorAlerts.dataType "
				+ "FROM sensorAlerts "
				+ "INNER JOIN sensors "
				+ "ON sensorAlerts.nodeId == sensors.nodeId "
				+ "AND sensorAlerts.sensorId == sensors.id")
			result = self.cursor.fetchall()

			# Extract for each sensor alert the corresponding data.
			for resultTuple in result:

				sensorAlert = SensorAlert()
				sensorAlert.sensorAlertId = resultTuple[0]
				sensorAlert.sensorId = resultTuple[1]
				sensorAlert.nodeId = resultTuple[2]
				sensorAlert.timeReceived = resultTuple[3]
				sensorAlert.alertDelay = resultTuple[4]
				sensorAlert.state = resultTuple[5]
				sensorAlert.description = resultTuple[6]
				sensorAlert.changeState = (resultTuple[8] == 1)
				sensorAlert.hasLatestData = (resultTuple[9] == 1)
				sensorAlert.dataType = resultTuple[10]
				sensorAlert.rulesActivated = False

				# Set optional data for sensor alert.
				sensorAlert.hasOptionalData = False
				sensorAlert.optionalData = None
				dataJson = resultTuple[7]
				if dataJson != "":
					try:
						sensorAlert.optionalData = json.loads(dataJson)
						sensorAlert.hasOptionalData = True
					except Exception as e:
						self.logger.exception("[%s]: Optional data from "
							% self.fileName
							+ "database not a valid json string. "
							+ "Ignoring data.")

				# Set alert levels for sensor alert.
				alertLevels = self._getSensorAlertLevels(sensorAlert.sensorId,
					logger)
				if alertLevels is None:
					logger.error("[%s]: Not able to get alert levels for "
						% self.fileName
						+ "sensor alert with id %d."
						% sensorAlert.sensorAlertId)

					self._releaseLock(logger)

					return None

				sensorAlert.alertLevels = alertLevels

				# Extract sensor alert data.
				if sensorAlert.dataType == SensorDataType.NONE:
					sensorAlert.sensorData = None

				elif sensorAlert.dataType == SensorDataType.INT:
					self.cursor.execute("SELECT data "
						+ "FROM sensorAlertsDataInt "
						+ "WHERE sensorAlertId = ?",
						(sensorAlert.sensorAlertId, ))
					subResult = self.cursor.fetchall()

					if len(subResult) != 1:
						logger.error("[%s]: Sensor alert data was not found."
							% self.fileName)

						self._releaseLock(logger)

						return None
					sensorAlert.sensorData = subResult[0][0]

				elif sensorAlert.dataType == SensorDataType.FLOAT:
					self.cursor.execute("SELECT data "
						+ "FROM sensorAlertsDataFloat "
						+ "WHERE sensorAlertId = ?",
						(sensorAlert.sensorAlertId, ))
					subResult = self.cursor.fetchall()

					if len(subResult) != 1:
						logger.error("[%s]: Sensor alert data was not found."
							% self.fileName)

						self._releaseLock(logger)

						return None
					sensorAlert.sensorData = subResult[0][0]

				else:
					logger.error("[%s]: Not able to get sensor alerts. "
						% self.fileName
						+ "Data type in database unknown.")

					self._releaseLock(logger)

					return None

				returnList.append(sensorAlert)

		except Exception as e:
			logger.exception("[%s]: Not able to get sensor alerts."
				% self.fileName)

			self._releaseLock(logger)

			return None

		self._releaseLock(logger)

		# return a list of sensorAlert objects
		return returnList


	# Deletes a sensor alert given by its sensor alert id.
	#
	# return True or False
	def deleteSensorAlert(self, sensorAlertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		result = self._deleteSensorAlert(sensorAlertId, logger)

		self._releaseLock(logger)

		return result


	# Deletes a node given by its node id.
	#
	# return True or False
	def deleteNode(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# Get node type from database.
		nodeObj = self._getNodeById(nodeId, logger)
		if nodeObj is None:
			logger.error("[%s]: Not able to get node with id %d."
				% (self.fileName, nodeId))

			self._releaseLock(logger)

			return False

		# Delete all corresponding alert entries from database.
		if nodeObj.type == "alert":

			if not self._deleteAlertsForNodeId(nodeId, logger):
				self._releaseLock(logger)

				return False

		# Delete all corresponding manager entries from database.
		elif nodeObj.type == "manager":

			if not self._deleteManagerForNodeId(nodeId, logger):
				self._releaseLock(logger)

				return False

		# Delete all corresponding sensor entries from database.
		elif nodeObj.type == "sensor":

			if not self._deleteSensorsForNodeId(nodeId, logger):
				self._releaseLock(logger)

				return False

		# Return if we do not know how to handle the node.
		else:
			logger.exception("[%s]: Unknown node type '%s' for node "
				% (self.fileName, nodeObj.type)
				+ "with id %d."
				% nodeId)

			self._releaseLock(logger)

			return False

		# Delete node from database.
		try:
			self.cursor.execute("DELETE FROM "
				+ "nodes "
				+ "WHERE id = ?",
				(nodeId, ))

		except Exception as e:
			logger.exception("[%s]: Not able to delete node with id %d."
				% (self.fileName, nodeId))

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# checks if the alert system is active or not
	#
	# return True or False
	def isAlertSystemActive(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			self.cursor.execute("SELECT value FROM options WHERE type = ?",
				("alertSystemActive", ))
			result = self.cursor.fetchall()
			alertSystemActive = result[0][0]

		except Exception as e:
			logger.exception("[%s]: Not able to check " % self.fileName
				+ "if alert system is active.")

			self._releaseLock(logger)

			return False

		self._releaseLock(logger)

		if alertSystemActive == 1:
			return True
		elif alertSystemActive == 0:
			return False


	# gets all alert levels for the alert clients from the database
	#
	# return list alertLevels as integer
	# or None
	def getAllAlertsAlertLevels(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertsAlertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels for alert clients.")

			self._releaseLock(logger)

			# return None if action failed
			return None

		self._releaseLock(logger)

		# return list alertLevels as integer
		return map(lambda x: x[0], result)


	# gets all alert levels for the sensors from the database
	#
	# return list alertLevels as integer
	# or None
	def getAllSensorsAlertLevels(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM sensorsAlertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels for sensors.")

			self._releaseLock(logger)

			# return None if action failed
			return None

		self._releaseLock(logger)

		# return list alertLevels as integer
		return map(lambda x: x[0], result)


	# gets all nodes from the database that are connected to the server
	#
	# return list of nodeIds
	# or None
	def getAllConnectedNodeIds(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# get all connected node ids from database
		try:
			self.cursor.execute("SELECT id "
				+ "FROM nodes "
				+ "WHERE connected = ?", (1, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "all connected node ids.")

			self._releaseLock(logger)

			# return None if action failed
			return None

		self._releaseLock(logger)

		# return list of nodeIds
		return map(lambda x: x[0], result)


	# Gets all nodes from the database that are registered as persistent
	# to the server.
	#
	# return list of nodeIds
	# or None
	def getAllPersistentNodeIds(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# get all persistent node ids from database
		try:
			self.cursor.execute("SELECT id "
				+ "FROM nodes "
				+ "WHERE persistent = ?", (1, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "all persistent node ids.")

			self._releaseLock(logger)

			# return None if action failed
			return None

		self._releaseLock(logger)

		# return list of nodeIds
		return map(lambda x: x[0], result)


	# marks a node given by its id as NOT connected
	#
	# return True or False
	def markNodeAsNotConnected(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = ? WHERE id = ?", (0, nodeId))
		except Exception as e:

			logger.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as not connected." % nodeId)

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# marks a node given by its id as connected
	#
	# return True or False
	def markNodeAsConnected(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = ? WHERE id = ?", (1, nodeId))
		except Exception as e:

			logger.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as connected." % nodeId)

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# gets the information of all sensors which last state updates
	# are older than the given time
	#
	# return list of sensor objects
	# or None
	def getSensorsUpdatedOlderThan(self, oldestTimeUpdated, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		sensorList = list()
		try:
			self.cursor.execute("SELECT id "
				+ "FROM sensors "
				+ "WHERE lastStateUpdated < ?", (oldestTimeUpdated, ))

			results = self.cursor.fetchall()

			for resultTuple in results:
				sensorId = resultTuple[0]
				sensor = self._getSensorById(sensorId, logger)
				if sensor is not None:
					sensorList.append(sensor)

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "sensors from database which update was older than %d."
				% oldestTimeUpdated)

			self._releaseLock(logger)

			return None

		self._releaseLock(logger)

		# return list of sensor objects
		return sensorList


	# gets the alert from the database when its id is given
	#
	# return an alert object or None
	def getAlertById(self, alertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		result = self._getAlertById(alertId, logger)

		self._releaseLock(logger)

		# return an alert object or None
		return result


	# gets the manager from the database when its id is given
	#
	# return a manager object or None
	def getManagerById(self, managerId, logger=None):
		
		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		result = self._getManagerById(managerId, logger)

		self._releaseLock(logger)

		# return a manager object or None
		return result


	# gets the node from the database when its id is given
	#
	# return a node object or None
	def getNodeById(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		result = self._getNodeById(nodeId, logger)

		self._releaseLock(logger)

		# return a node object or None
		return result


	# gets the sensor from the database when its id is given
	#
	# return a sensor object or None
	def getSensorById(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		result = self._getSensorById(sensorId, logger)

		self._releaseLock(logger)

		# return a sensor object or None
		return result


	# Gets all nodes from the database.
	#
	# return a list of node objects or None
	def getNodes(self, logger=None):
		
		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		nodes = list()
		try:

			# Get all nodes information.
			self.cursor.execute("SELECT * FROM nodes")
			nodeTuples = self.cursor.fetchall()
			for nodeTuple in nodeTuples:
				node = self._convertNodeTupleToObj(nodeTuple)
				nodes.append(node)

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "nodes from database.")

			self._releaseLock(logger)

			return None

		self._releaseLock(logger)

		# list(node objects)
		return nodes


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = list(option objects)
	# list[1] = list(node objects)
	# list[2] = list(sensor objects)
	# list[3] = list(manager objects)
	# list[4] = list(alert objects)
	# or None
	def getAlertSystemInformation(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:

			# Get all options.
			optionList = list()
			self.cursor.execute("SELECT type, "
				+ "value "
				+ "FROM options")
			results = self.cursor.fetchall()
			for resultTuple in results:
				optionObj = Option()
				optionObj.type = resultTuple[0]
				optionObj.value = resultTuple[1]
				optionList.append(optionObj)

			# Get all nodes.
			nodeList = list()
			self.cursor.execute("SELECT * FROM nodes")
			results = self.cursor.fetchall()
			for resultTuple in results:
				nodeObj = self._convertNodeTupleToObj(resultTuple)
				nodeList.append(nodeObj)

			# Get all sensors.
			sensorList = list()
			self.cursor.execute("SELECT id FROM sensors")
			results = self.cursor.fetchall()
			for resultTuple in results:
				sensorObj = self._getSensorById(resultTuple[0], logger)
				if sensorObj is None:
					raise ValueError("Can not retrieve sensor with id %d."
						% resultTuple[0])
				sensorList.append(sensorObj)

			# Get all managers.
			managerList = list()
			self.cursor.execute("SELECT id FROM managers")
			results = self.cursor.fetchall()
			for resultTuple in results:
				managerObj = self._getManagerById(resultTuple[0], logger)
				if managerObj is None:
					raise ValueError("Can not retrieve manager with id %d."
						% resultTuple[0])
				managerList.append(managerObj)

			# Get all alerts.
			alertList = list()
			self.cursor.execute("SELECT id FROM alerts")
			results = self.cursor.fetchall()
			for resultTuple in results:
				alertObj = self._getAlertById(resultTuple[0], logger)
				if alertObj is None:
					raise ValueError("Can not retrieve alert with id %d."
						% resultTuple[0])
				alertList.append(alertObj)

			# Generate a list with system information.
			alertSystemInformation = list()
			alertSystemInformation.append(optionList)
			alertSystemInformation.append(nodeList)
			alertSystemInformation.append(sensorList)
			alertSystemInformation.append(managerList)
			alertSystemInformation.append(alertList)

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "complete system information from database.")

			self._releaseLock(logger)

			return None

		self._releaseLock(logger)

		# return a list of
		# list[0] = list(option objects)
		# list[1] = list(node objects)
		# list[2] = list(sensor objects)
		# list[3] = list(manager objects)
		# list[4] = list(alert objects)
		return alertSystemInformation


	# change a option in the database
	#
	# return True or False
	def changeOption(self, optionType, optionValue, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			# check if option does exist
			self.cursor.execute("SELECT id "
				+ "FROM options "
				+ "WHERE type = ?", (optionType, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logger.error("[%s]: Option was not found."
					% self.fileName)
				self._releaseLock(logger)

				return False

			# update option in database
			self.cursor.execute("UPDATE options SET "
				+ "value = ? "
				+ "WHERE type = ?", (optionValue, optionType))

		except Exception as e:

			logger.exception("[%s]: Not able to update "
				% self.fileName
				+ "option in database.")

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock(logger)

		return True


	# gets the state of a sensor given by id
	#
	# return sensor state or None
	def getSensorState(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			# get sensor state from database
			self.cursor.execute("SELECT state "
				+ "FROM sensors "
				+ "WHERE id = ?", (sensorId, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logger.error("[%s]: Sensor was not found."
					% self.fileName)

				self._releaseLock(logger)

				return None

			state = result[0][0]

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "sensor state from database.")

			self._releaseLock(logger)

			return None

		self._releaseLock(logger)

		return state


	# Gets the data of a sensor given by id.
	#
	# return a sensor data object or None
	def getSensorData(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		try:
			# Get data type from database.
			self.cursor.execute("SELECT dataType "
				+ "FROM sensors "
				+ "WHERE id = ?", (sensorId, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logger.error("[%s]: Sensor was not found."
					% self.fileName)

				self._releaseLock(logger)

				return None

			dataType = result[0][0]

		except Exception as e:

			logger.exception("[%s]: Not able to get "
				% self.fileName
				+ "sensor data type from database.")

			self._releaseLock(logger)

			return None

		data = SensorData()
		data.sensorId = sensorId
		data.dataType = dataType
		if dataType == SensorDataType.NONE:
			data.data = None

		elif dataType == SensorDataType.INT:
			try:
				# Get data type from database.
				self.cursor.execute("SELECT data "
					+ "FROM sensorsDataInt "
					+ "WHERE sensorId = ?", (sensorId, ))
				result = self.cursor.fetchall()
				if len(result) != 1:
					logger.error("[%s]: Sensor data was not found."
						% self.fileName)

					self._releaseLock(logger)

					return None

				data.data = result[0][0]


			except Exception as e:

				logger.exception("[%s]: Not able to get "
					% self.fileName
					+ "sensor data from database.")

				self._releaseLock(logger)

				return None

		elif dataType == SensorDataType.FLOAT:
			try:
				# Get data type from database.
				self.cursor.execute("SELECT data "
					+ "FROM sensorsDataFloat "
					+ "WHERE sensorId = ?", (sensorId, ))
				result = self.cursor.fetchall()
				if len(result) != 1:
					logger.error("[%s]: Sensor data was not found."
						% self.fileName)

					self._releaseLock(logger)

					return None

				data.data = result[0][0]

			except Exception as e:

				logger.exception("[%s]: Not able to get "
					% self.fileName
					+ "sensor data from database.")

				self._releaseLock(logger)

				return None

		self._releaseLock(logger)

		# return a sensor data object or None
		return data


	# closes db for usage
	#
	# no return value
	def close(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		self.cursor.close()
		self.conn.close()

		self._releaseLock(logger)


# class for using mysql as storage backend
class Mysql(_Storage):

	def __init__(self, host, port, database, username, password, globalData):

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# Import the needed package.
		self.MySQLdb = importlib.import_module("MySQLdb")

		self.globalData = globalData
		self.logger = self.globalData.logger
		self.storageBackendMysqlRetries = \
			self.globalData.storageBackendMysqlRetries

		# version of server
		self.version = self.globalData.version
		self.rev = self.globalData.rev
		self.dbVersion = self.globalData.dbVersion

		# needed mysql parameters
		self.host = host
		self.port = port
		self.database = database
		self.username = username
		self.password = password

		# mysql lock
		self.dbLock = threading.Semaphore(1)

		self.conn = None
		self.cursor = None

		# connect to the database
		self._openConnection()

		# Check if AlertR tables exist already
		# if not => create them.
		self.cursor.execute("SHOW TABLES LIKE 'internals'")
		internalsResult = self.cursor.fetchall()

		# close connection to the database
		self._closeConnection()

		# If table does not exist
		# => create all tables.
		if not internalsResult:

			self._openConnection()
			uniqueID = self._getUniqueID()
			self._deleteStorage()
			self._closeConnection()

			# If we already have a uniqueID, create storage with the same
			# uniqueID.
			if uniqueID is None:
				uniqueID = self._generateUniqueId()
			self._openConnection()
			self._createStorage(uniqueID)
			self._closeConnection()

		# check if the versions are compatible
		else:
			self.checkVersionAndClearConflict()


	# internal function that connects to the mysql server
	# (needed because direct changes to the database by another program
	# are not seen if the connection to the mysql server is kept alive)
	def _openConnection(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		currentTry = 0
		while True:
			try:
				self.conn = self.MySQLdb.connect(host=self.host,
					port=self.port,
					user=self.username,
					passwd=self.password,
					db=self.database)

				self.cursor = self.conn.cursor()
				break

			except Exception as e:

				# Re-throw the exception if we reached our retry limit.
				if currentTry >= self.storageBackendMysqlRetries:
					raise

				currentTry += 1
				logger.exception("[%s]: Not able to connect to the MySQL "
					% self.fileName
					+ "server. Waiting before retrying (%d/%d)."
					% (currentTry, self.storageBackendMysqlRetries))

				time.sleep(5)


	# internal function that closes the connection to the mysql server
	def _closeConnection(self):
		self.cursor.close()
		self.conn.close()
		self.cursor = None
		self.conn = None


	# internal function that checks if the username is known
	def _usernameInDb(self, username):

		# check if the username does exist => if not node is not known
		self.cursor.execute("SELECT id FROM nodes WHERE username = %s ",
			[username])
		result = self.cursor.fetchall()

		# return if username was found or not
		if len(result) == 0:
			return False
		else:
			return True


	# internal function that generates a unique id for this server instance
	def _generateUniqueId(self):

		# generate unique id for this installation
		utcTimestamp = int(time.time())
		uniqueString = socket.gethostname() \
			+ struct.pack("d", utcTimestamp) \
			+ os.urandom(200)
		sha256 = hashlib.sha256()
		sha256.update(uniqueString)
		uniqueID = sha256.hexdigest()

		return uniqueID


	# Internal function that converts a tuple that is fetched from the
	# database by "SELECT * FROM nodes" to an node object.
	#
	# returns a node object
	def _convertNodeTupleToObj(self, nodeTuple):
		node = Node()
		node.id = nodeTuple[0]
		node.hostname = nodeTuple[1]
		node.username = nodeTuple[2]
		node.nodeType = nodeTuple[3]
		node.instance = nodeTuple[4]
		node.connected = (nodeTuple[5] == 1)
		node.version = nodeTuple[6]
		node.rev = nodeTuple[7]
		node.persistent = (nodeTuple[8] == 1)
		return node


	# internal function that gets the id of a node when a username is given
	def _getNodeId(self, username):

		# check if the username does exist
		if self._usernameInDb(username):
			# get id of username
			self.cursor.execute("SELECT id FROM nodes WHERE username = %s ",
				[username])
			result = self.cursor.fetchall()

			return result[0][0]
		else:
			raise ValueError("Node id was not found.")


	# Internal function that gets the alert from the database given
	# by its id.
	#
	# return an alert object or None
	def _getAlertById(self, alertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		alert = None
		try:
			self.cursor.execute("SELECT * FROM alerts "
				+ "WHERE id = %s", (alertId, ))

			result = self.cursor.fetchall()

			if len(result) == 1:
				alert = Alert()
				alert.alertId = result[0][0]
				alert.nodeId = result[0][1]
				alert.remoteAlertId = result[0][2]
				alert.description = result[0][3]

				# Set alert levels for alert.
				alertLevels = self._getAlertAlertLevels(alert.alertId,
					logger)
				if alertLevels is None:
					logger.error("[%s]: Not able to get alert levels for "
						% self.fileName
						+ "alert with id %d."
						% alert.alertId)

					return None
				alert.alertLevels = alertLevels

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "alert with id %d." % alertId)

			return None

		return alert


	# Internal function that gets the manager from the database given
	# by its id.
	#
	# return a manager object or None
	def _getManagerById(self, managerId, logger=None):
		
		# Set logger instance to use.
		if not logger:
			logger = self.logger

		manager = None
		try:
			self.cursor.execute("SELECT * FROM managers "
				+ "WHERE id = %s", (managerId, ))

			result = self.cursor.fetchall()

			if len(result) == 1:
				manager = Manager()
				manager.managerId = result[0][0]
				manager.nodeId = result[0][1]
				manager.description = result[0][2]

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "manager with id %d." % managerId)

			return None

		return manager


	# Internal function that gets the node from the database given by its id.
	#
	# return a node object or None
	def _getNodeById(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("SELECT * FROM nodes "
				+ "WHERE id = %s", (nodeId, ))

			result = self.cursor.fetchall()
		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "node with id %d from database." % nodeId)

			return None

		if len(result) == 1:
			try:
				return self._convertNodeTupleToObj(result[0])
			except Exception as e:
				logger.exception("[%s]: Not able to convert " % self.fileName
					+ "node data for id %d to object." % nodeId)

		return None


	# Internal function that gets the sensor from the database given by its id.
	#
	# return a sensor object or None
	def _getSensorById(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		sensor = None
		try:
			self.cursor.execute("SELECT * FROM sensors "
				+ "WHERE id = %s", (sensorId, ))

			result = self.cursor.fetchall()

			if len(result) == 1:
				sensor = Sensor()
				sensor.sensorId = result[0][0]
				sensor.nodeId = result[0][1]
				sensor.remoteSensorId = result[0][2]
				sensor.description = result[0][3]
				sensor.state = result[0][4]
				sensor.lastStateUpdated = result[0][5]
				sensor.alertDelay = result[0][6]
				sensor.dataType = result[0][7]

				# Set alert levels for sensor.
				alertLevels = self._getSensorAlertLevels(sensor.sensorId,
					logger)
				if alertLevels is None:
					logger.error("[%s]: Not able to get alert levels for "
						% self.fileName
						+ "sensor with id %d."
						% sensor.sensorId)

					return None
				sensor.alertLevels = alertLevels

				# Extract sensor data.
				if sensor.dataType == SensorDataType.NONE:
					sensor.data = None

				elif sensor.dataType == SensorDataType.INT:
					self.cursor.execute("SELECT data "
						+ "FROM sensorsDataInt "
						+ "WHERE sensorId = %s",
						(sensor.sensorId, ))
					subResult = self.cursor.fetchall()

					if len(subResult) != 1:
						logger.error("[%s]: Sensor data for sensor with id %d "
							% (self.fileName, sensor.sensorId)
							+ "was not found.")

						return None
					sensor.data = subResult[0][0]

				elif sensor.dataType == SensorDataType.FLOAT:
					self.cursor.execute("SELECT data "
						+ "FROM sensorsDataFloat "
						+ "WHERE sensorId = %s",
						(sensor.sensorId, ))
					subResult = self.cursor.fetchall()

					if len(subResult) != 1:
						logger.error("[%s]: Sensor data for sensor with id %d "
							% (self.fileName, sensor.sensorId)
							+ "was not found.")

						return None
					sensor.data = subResult[0][0]

				else:
					logger.error("[%s]: Not able to get sensor with id %d. "
						% (self.fileName, sensor.sensorId)
						+ "Data type in database unknown.")

					return None
				
		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "sensor with id %d." % sensorId)

			return None

		return sensor


	# internal function that gets the sensor id of a sensor when the id
	# of a node is given and the remote sensor id that is used
	# by the node internally
	#
	# return sensorId or raised Exception
	def _getSensorId(self, nodeId, remoteSensorId):

		# get sensorId from database
		self.cursor.execute("SELECT id FROM sensors "
			+ "WHERE nodeId = %s "
			+ "AND remoteSensorId = %s", (nodeId, remoteSensorId))
		result = self.cursor.fetchall()

		if len(result) != 1:
			raise ValueError("Sensor does not exist in database.")

		sensorId = result[0][0]

		return sensorId


	# internal function that gets the alert id of an alert when the id
	# of a node is given and the remote alert id that is used
	# by the node internally
	#
	# return alertId or raised Exception
	def _getAlertId(self, nodeId, remoteAlertId):

		# get alertId from database
		self.cursor.execute("SELECT id FROM alerts "
			+ "WHERE nodeId = %s "
			+ "AND remoteAlertId = %s", (nodeId, remoteAlertId))
		result = self.cursor.fetchall()

		if len(result) != 1:
			raise ValueError("Alert does not exist in database.")

		alertId = result[0][0]

		return alertId


	# internal function that gets the manager id of a manager when the id
	# of a node is given
	#
	# return managerId or raised Exception
	def _getManagerId(self, nodeId):

		# get managerId from database
		self.cursor.execute("SELECT id FROM managers "
			+ "WHERE nodeId = %s", (nodeId, ))
		result = self.cursor.fetchall()

		if len(result) != 1:
			raise ValueError("Manager does not exist in database.")

		managerId = result[0][0]

		return managerId


	# internal function that gets the unique id from the database
	#
	# return unique id
	# or None
	def _getUniqueID(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		# if unique id already cached => return it
		if not self.globalData.uniqueID is None:
			return self.globalData.uniqueID

		try:
			self.cursor.execute("SELECT value "
				+ "FROM internals WHERE type=%s", ("uniqueID", ))
			self.globalData.uniqueID = self.cursor.fetchall()[0][0]
		except Exception as e:
			logger.exception("[%s]: Not able to get the unique id."
				% self.fileName)

		return self.globalData.uniqueID


	# internal function that acquires the lock
	def _acquireLock(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		logger.debug("[%s]: Acquire lock." % self.fileName)
		self.dbLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		logger.debug("[%s]: Release lock." % self.fileName)
		self.dbLock.release()


	# internal function that creates the database
	# (should only be called if the database does not exist)
	#
	# no return value but raise exception if it fails
	def _createStorage(self, uniqueID):

		# create internals table
		self.cursor.execute("CREATE TABLE internals ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "type VARCHAR(255) NOT NULL UNIQUE, "
			+ "value VARCHAR(255) NOT NULL)")

		# insert version of server
		self.cursor.execute("INSERT INTO internals ("
			+ "type, "
			+ "value) VALUES (%s, %s)", ("version", self.version))

		# insert db version of server
		self.cursor.execute("INSERT INTO internals ("
			+ "type, "
			+ "value) VALUES (%s, %s)", ("dbversion", self.dbVersion))

		# insert unique id
		self.cursor.execute("INSERT INTO internals ("
			+ "type, "
			+ "value) VALUES (%s, %s)", ("uniqueID", uniqueID))

		# create options table
		self.cursor.execute("CREATE TABLE options ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "type VARCHAR(255) NOT NULL UNIQUE, "
			+ "value DOUBLE NOT NULL)")

		# insert option to activate/deactivate alert system
		# (0 = deactivated, 1 = activated)
		self.cursor.execute("INSERT INTO options ("
			+ "type, "
			+ "value) VALUES (%s, %s)", ("alertSystemActive", 0))

		# create nodes table
		self.cursor.execute("CREATE TABLE nodes ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "hostname VARCHAR(255) NOT NULL, "
			+ "username VARCHAR(255) NOT NULL UNIQUE, "
			+ "nodeType VARCHAR(255) NOT NULL, "
			+ "instance VARCHAR(255) NOT NULL, "
			+ "connected INTEGER NOT NULL, "
			+ "version DOUBLE NOT NULL, "
			+ "rev INTEGER NOT NULL, "
			+ "persistent INTEGER NOT NULL)")

		# create sensors table
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

		# create sensorsAlertLevels table
		self.cursor.execute("CREATE TABLE sensorsAlertLevels ("
			+ "sensorId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "PRIMARY KEY(sensorId, alertLevel), "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# Create sensorsDataInt table.
		self.cursor.execute("CREATE TABLE sensorsDataInt ("
			+ "sensorId INTEGER NOT NULL PRIMARY KEY, "
			+ "data INTEGER NOT NULL, "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# Create sensorsDataFloat table.
		self.cursor.execute("CREATE TABLE sensorsDataFloat ("
			+ "sensorId INTEGER NOT NULL PRIMARY KEY, "
			+ "data DOUBLE NOT NULL, "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create sensorAlerts table
		self.cursor.execute("CREATE TABLE sensorAlerts ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "sensorId INTEGER NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "timeReceived INTEGER NOT NULL, "
			+ "dataJson TEXT NOT NULL,"
			+ "changeState INTEGER NOT NULL,"
			+ "hasLatestData INTEGER NOT NULL, "
			+ "dataType INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id), "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# Create sensorAlertsDataInt table.
		self.cursor.execute("CREATE TABLE sensorAlertsDataInt ("
			+ "sensorAlertId INTEGER NOT NULL PRIMARY KEY, "
			+ "data INTEGER NOT NULL, "
			+ "FOREIGN KEY(sensorAlertId) REFERENCES sensorAlerts(id))")

		# Create sensorAlertsDataFloat table.
		self.cursor.execute("CREATE TABLE sensorAlertsDataFloat ("
			+ "sensorAlertId INTEGER NOT NULL PRIMARY KEY, "
			+ "data DOUBLE NOT NULL, "
			+ "FOREIGN KEY(sensorAlertId) REFERENCES sensorAlerts(id))")

		# create alerts table
		self.cursor.execute("CREATE TABLE alerts ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteAlertId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create alertsAlertLevels table
		self.cursor.execute("CREATE TABLE alertsAlertLevels ("
			+ "alertId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "PRIMARY KEY(alertId, alertLevel), "
			+ "FOREIGN KEY(alertId) REFERENCES alerts(id))")

		# create managers table
		self.cursor.execute("CREATE TABLE managers ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# commit all changes
		self.conn.commit()


	# Internal function that deletes the database
	# (should only be called if parts of the database do exist)
	#
	# no return value but raise exception if it fails
	def _deleteStorage(self):

		# Delete all tables from the database to clear the old version.
		self.cursor.execute("DROP TABLE IF EXISTS internals")
		self.cursor.execute("DROP TABLE IF EXISTS options")
		self.cursor.execute("DROP TABLE IF EXISTS sensorAlertsDataInt")
		self.cursor.execute("DROP TABLE IF EXISTS sensorAlertsDataFloat")
		self.cursor.execute("DROP TABLE IF EXISTS sensorAlerts")
		self.cursor.execute("DROP TABLE IF EXISTS sensorsAlertLevels")
		self.cursor.execute("DROP TABLE IF EXISTS sensorsDataInt")
		self.cursor.execute("DROP TABLE IF EXISTS sensorsDataFloat")
		self.cursor.execute("DROP TABLE IF EXISTS sensors")
		self.cursor.execute("DROP TABLE IF EXISTS alertsAlertLevels")
		self.cursor.execute("DROP TABLE IF EXISTS alerts")
		self.cursor.execute("DROP TABLE IF EXISTS managers")
		self.cursor.execute("DROP TABLE IF EXISTS nodes")

		# commit all changes
		self.conn.commit()


	# Internal function that deletes all alert data corresponding
	# to the given node id.
	#
	# Returns true if everything worked fine.
	def _deleteAlertsForNodeId(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			# get all alert ids that are connected to
			# the old alert
			self.cursor.execute("SELECT id FROM alerts "
				+ "WHERE nodeId = %s", (nodeId, ))
			result = self.cursor.fetchall()

			# delete all alert alert levels and alerts of
			# this node
			for alertIdResult in result:

				self.cursor.execute("DELETE FROM "
					+ "alertsAlertLevels "
					+ "WHERE alertId = %s",
					(alertIdResult[0], ))

				self.cursor.execute("DELETE FROM alerts "
					+ "WHERE id = %s",
					(alertIdResult[0], ))

			# Commit all changes.
			self.conn.commit()

		except Exception as e:
			logger.exception("[%s]: Not able to "
				% self.fileName
				+ "delete alerts for node with id %d."
				% nodeId)

			return False

		return True


	# Internal function that deletes all manager data corresponding
	# to the given node id.
	#
	# Returns true if everything worked fine.
	def _deleteManagerForNodeId(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("DELETE FROM managers "
				+ "WHERE nodeId = %s",
				(nodeId, ))

			# Commit all changes.
			self.conn.commit()

		except Exception as e:
			logger.exception("[%s]: Not able to "
				% self.fileName
				+ "delete manager for node with id %d."
				% nodeId)

			return False

		return True


	# Internal function that deletes all sensor data corresponding
	# to the given node id.
	#
	# Returns true if everything worked fine.
	def _deleteSensorsForNodeId(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			# Get all sensor ids that are connected to
			# the old sensor.
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = %s ", (nodeId, ))
			result = self.cursor.fetchall()

			# Delete all sensor alert levels, data and sensors of
			# this node.
			for sensorIdResult in result:

				# Get all sensor alert ids that are connected to
				# the this sensor.
				self.cursor.execute("SELECT id FROM sensorAlerts "
					+ "WHERE sensorId = %s ",
					(sensorIdResult[0], ))
				sensorAlertIdsresult = self.cursor.fetchall()

				# Delete all sensor alert data connected to the corresponding
				# sensor alert.
				for sensorAlertIdResult in sensorAlertIdsresult:
					sensorAlertId = sensorAlertIdResult[0]
					if not self._deleteSensorAlert(sensorAlertId, logger):
						return False

				self.cursor.execute("DELETE FROM "
					+ "sensorsAlertLevels "
					+ "WHERE sensorId = %s",
					(sensorIdResult[0], ))

				self.cursor.execute("DELETE FROM "
					+ "sensorsDataInt "
					+ "WHERE sensorId = %s",
					(sensorIdResult[0], ))

				self.cursor.execute("DELETE FROM "
					+ "sensorsDataFloat "
					+ "WHERE sensorId = %s",
					(sensorIdResult[0], ))

				self.cursor.execute("DELETE FROM sensors "
					+ "WHERE id = %s",
					(sensorIdResult[0], ))

			# Commit all changes.
			self.conn.commit()

		except Exception as e:
			logger.exception("[%s]: Not able to "
				% self.fileName
				+ "delete sensors for node with id %d."
				% nodeId)

			return False

		return True


	# Internal function thatdeletes a sensor alert given by its
	# sensor alert id.
	#
	# Returns true if everything worked fine.
	def _deleteSensorAlert(self, sensorAlertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("DELETE FROM sensorAlertsDataInt "
				+ "WHERE sensorAlertId = %s",
				(sensorAlertId, ))

			self.cursor.execute("DELETE FROM sensorAlertsDataFloat "
				+ "WHERE sensorAlertId = %s",
				(sensorAlertId, ))

			self.cursor.execute("DELETE FROM sensorAlerts "
				+ "WHERE id = %s",
				(sensorAlertId, ))
		except Exception as e:
			logger.exception("[%s]: Not able to delete "
				% self.fileName
				+ "sensor alert with id %d."
				% sensorAlertId)

			return False

		# commit all changes
		self.conn.commit()

		return True


	# Internal function that gets all alert levels for a specific
	# alert given by alertId
	#
	# return list of alertLevels
	# or None
	def _getAlertAlertLevels(self, alertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertsAlertLevels "
				+ "WHERE alertId = %s", (alertId, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "alert levels for alert with id %d." % alertId)

			# return None if action failed
			return None

		# return list of alertLevels
		return map(lambda x: x[0], result)


	# Internal function that gets all alert levels for a specific
	# sensor given by sensorId
	#
	# return list of alertLevel
	# or None
	def _getSensorAlertLevels(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM sensorsAlertLevels "
				+ "WHERE sensorId = %s", (sensorId, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "alert levels for sensor with id %d." % sensorId)

			# return None if action failed
			return None

		# return list of alertLevel
		return map(lambda x: x[0], result)


	# Internal function that inserts sensor data according to its type.
	#
	# Returns true if everything worked fine.
	def _insertSensorData(self, sensorId, dataType, data, logger=None):

		# Depending on the data type of the sensor add it to the
		# corresponding table.
		if dataType == SensorDataType.NONE:
			return True

		elif dataType == SensorDataType.INT:
			try:
				self.cursor.execute("INSERT INTO sensorsDataInt ("
					+ "sensorId, "
					+ "data) VALUES (%s, %s)",
					(sensorId,
					data))
			except Exception as e:
				logger.exception("[%s]: Not able to "
					% self.fileName
					+ "add sensor's integer data.")

				return False

		elif dataType == SensorDataType.FLOAT:
			try:
				self.cursor.execute("INSERT INTO sensorsDataFloat ("
					+ "sensorId, "
					+ "data) VALUES (%s, %s)",
					(sensorId,
					data))
			except Exception as e:
				logger.exception("[%s]: Not able to "
					% self.fileName
					+ "add sensor's floating point data.")

				return False

		else:
			logger.error("[%s]: Data type not known. Not able to "
				% self.fileName
				+ "add sensor.")

			return False

		return True


	# Internal function that inserts sensor data according to its type.
	#
	# Returns true if everything worked fine.
	def _insertSensorAlertData(self, sensorAlertId, dataType, data,
		logger=None):

		# Depending on the data type of the sensor alert add it to the
		# corresponding table.
		if dataType == SensorDataType.NONE:
			return True

		elif dataType == SensorDataType.INT:
			try:
				self.cursor.execute("INSERT INTO sensorAlertsDataInt ("
					+ "sensorAlertId, "
					+ "data) VALUES (%s, %s)",
					(sensorAlertId,
					data))
			except Exception as e:
				logger.exception("[%s]: Not able to "
					% self.fileName
					+ "add sensorAlert's integer data.")

				return False

		elif dataType == SensorDataType.FLOAT:
			try:
				self.cursor.execute("INSERT INTO sensorAlertsDataFloat ("
					+ "sensorAlertId, "
					+ "data) VALUES (%s, %s)",
					(sensorAlertId,
					data))
			except Exception as e:
				logger.exception("[%s]: Not able to "
					% self.fileName
					+ "add sensorAlert's floating point data.")

				return False

		else:
			logger.error("[%s]: Data type not known. Not able to "
				% self.fileName
				+ "add sensorAlert.")

			return False

		return True


	# checks the version of the server and the version in the database
	# and clears every compatibility issue
	#
	# no return value but raise exception if it fails
	def checkVersionAndClearConflict(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		self._openConnection(logger)

		# get version from the current database
		self.cursor.execute("SELECT value FROM internals "
			+ "WHERE type = %s",
			("dbversion", ))
		result = self.cursor.fetchall()

		# In case the current database does not have any db version
		# set it.
		if result:
			currDbVersion = int(result[0][0])
		else:
			currDbVersion = -1

		# If the versions are not compatible
		# => update database schema.
		if currDbVersion < self.dbVersion:

			logger.info("[%s]: Needed database version "
				% self.fileName
				+ "'%d' not compatible "
				% self.dbVersion
				+ "with current database layout version '%d'. "
				% currDbVersion
				+ "Updating database.")

			# get old uniqueId to keep it
			uniqueID = self._getUniqueID()
			if uniqueID is None:
				uniqueID = self._generateUniqueId()

			self._deleteStorage()

			# create new database
			self._createStorage(uniqueID)

			# commit all changes
			self.conn.commit()

		# Raise an exception if database layout version
		# is newer than the one we need.
		elif currDbVersion > self.dbVersion:
			raise ValueError("Current database layout version ('%d') "
				% currDbVersion
				+ "newer than the one this server uses ('%d')."
				% self.dbVersion)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)


	# adds a node if it does not exist or changes the registered
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType, instance, version, rev,
		persistent, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# check if a node with the same username already exists
		# => if not add node
		if not self._usernameInDb(username):

			logger.info("[%s]: Node with username '%s' does not exist "
				% (self.fileName, username)
				+ "in database. Adding it.")

			try:
				# NOTE: connection state is changed later on
				# in the registration process
				self.cursor.execute("INSERT INTO nodes ("
					+ "hostname, "
					+ "username, "
					+ "nodeType, "
					+ "instance, "
					+ "connected, "
					+ "version, "
					+ "rev, "
					+ "persistent) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
					(hostname, username, nodeType, instance, 0, version, rev,
					persistent))
			except Exception as e:
				logger.exception("[%s]: Not able to add node."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		# if a node with this username exists
		# => check if everything is the same
		else:

			logger.info("[%s]: Node with username '%s' already exists "
				% (self.fileName, username)
				+ "in database.")

			nodeId = self._getNodeId(username)

			# get hostname, nodeType, version, revision, persistent
			try:
				self.cursor.execute("SELECT hostname, "
					+ "nodeType, "
					+ "instance, "
					+ "version, "
					+ "rev, "
					+ "persistent "
					+ "FROM nodes WHERE id = %s ",
					(nodeId, ))
				result = self.cursor.fetchall()
				dbHostname = result[0][0]
				dbNodeType = result[0][1]
				dbInstance = result[0][2]
				dbVersion = result[0][3]
				dbRev = result[0][4]
				dbPersistent = result[0][5]

			except Exception as e:
				logger.exception("[%s]: Not able to get node information."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

			# change hostname if it had changed
			if dbHostname != hostname:

				logger.info("[%s]: Hostname of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbHostname, hostname))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "hostname = %s "
						+ "WHERE id = %s",
						(hostname, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update hostname of node.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

			# change instance if it had changed
			if dbInstance != instance:

				logger.info("[%s]: Instance of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbInstance, instance))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "instance = %s "
						+ "WHERE id = %s",
						(instance, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update instance of node.")

					self._releaseLock(logger)

					return False

			# change version if it had changed
			if dbVersion != version:

				logger.info("[%s]: Version of node has changed "
					% self.fileName
					+ "from '%.3f' to '%.3f'. Updating database."
					% (dbVersion, version))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "version = %s "
						+ "WHERE id = %s",
						(version, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update version of node.")

					self._releaseLock(logger)

					return False

			# change revision if it had changed
			if dbRev != rev:

				logger.info("[%s]: Revision of node has changed "
					% self.fileName
					+ "from '%d' to '%d'. Updating database."
					% (dbRev, rev))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "rev = %s "
						+ "WHERE id = %s",
						(rev, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update revision of node.")

					self._releaseLock(logger)

					return False

			# change persistent if it had changed
			if dbPersistent != persistent:

				logger.info("[%s]: Persistent flag of node has changed "
					% self.fileName
					+ "from '%d' to '%d'. Updating database."
					% (dbPersistent, persistent))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "persistent = %s "
						+ "WHERE id = %s",
						(persistent, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update persistent flag of node.")

					self._releaseLock(logger)

					return False

			# if node type has changed
			# => delete sensors/alerts/manager information of old node
			# and change node type
			if dbNodeType != nodeType:

				logger.info("[%s]: Type of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbNodeType, nodeType))

				# if old node had type "sensor"
				# => delete all sensors
				if dbNodeType == "sensor":

					if not self._deleteAlertsForNodeId(nodeId, logger):

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

				# if old node had type "alert"
				# => delete all alerts
				elif dbNodeType == "alert":

					if not self._deleteAlertsForNodeId(nodeId, logger):

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

				# if old node had type "manager"
				# => delete all manager information
				elif dbNodeType == "manager":

					if not self._deleteManagerForNodeId(nodeId, logger):

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

				# if old node had type "server"
				# => delete all sensor information
				elif dbNodeType == "server":

					if not self._deleteAlertsForNodeId(nodeId, logger):

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

				# node type in database not known
				else:

					logger.error("[%s]: Unknown node type "
						% self.fileName
						+ "when deleting old sensors/alerts/manager "
						+ "information.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# update node type
				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "nodeType = %s "
						+ "WHERE id = %s",
						(nodeType, nodeId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update type of node.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# adds/updates the data that is given by the node for the sensors
	# to the database
	#
	# return True or False
	def addSensors(self, username, sensors, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logger.exception("[%s]: Not able to get node id."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# add/update all sensors
		for sensor in sensors:

			# Extract sensor data (field does not exist
			# if data type is "none").
			if sensor["dataType"] == SensorDataType.NONE:
				sensorData = None
			else:
				sensorData = sensor["data"]

			# check if a sensor with the same remote id for this node
			# already exists in the database
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = %s AND remoteSensorId = %s",
				(nodeId, int(sensor["clientSensorId"])))
			result = self.cursor.fetchall()

			# if the sensor does not exist
			# => add it
			if not result:

				logger.info("[%s]: Sensor with client id '%d' does not "
					% (self.fileName, sensor["clientSensorId"])
					+ "exist in database. Adding it.")

				# add sensor to database
				try:
					utcTimestamp = int(time.time())
					self.cursor.execute("INSERT INTO sensors ("
						+ "nodeId, "
						+ "remoteSensorId, "
						+ "description, "
						+ "state, "
						+ "lastStateUpdated, "
						+ "alertDelay, "
						+ "dataType) VALUES (%s, %s, %s, %s, %s, %s, %s)",
						(nodeId,
						sensor["clientSensorId"],
						sensor["description"],
						sensor["state"],
						utcTimestamp,
						sensor["alertDelay"],
						sensor["dataType"]))
				except Exception as e:
					logger.exception("[%s]: Not able to add sensor."
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# get sensorId of current added sensor
				sensorId = self.cursor.lastrowid

				# add sensor alert levels to database
				try:
					for alertLevel in sensor["alertLevels"]:
						self.cursor.execute("INSERT INTO sensorsAlertLevels ("
							+ "sensorId, "
							+ "alertLevel) VALUES (%s, %s)",
							(sensorId,
							alertLevel))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "add sensor's alert levels.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# Depending on the data type of the sensor add it to the
				# corresponding table.
				if not self._insertSensorData(sensorId,
					sensor["dataType"], sensorData, logger):

					logger.error("[%s]: Not able to add data for newly "
						% self.fileName
						+ "added sensor.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

			# if the sensor does already exist
			# => check if everything is the same
			else:

				logger.info("[%s]: Sensor with client id '%d' already "
					% (self.fileName, int(sensor["clientSensorId"]))
					+ "exists in database.")

				# get sensorId, description, alertDelay and dataType
				try:
					sensorId = self._getSensorId(nodeId,
						int(sensor["clientSensorId"]))

					self.cursor.execute("SELECT description, "
						+ "alertDelay, "
						+ "dataType "
						+ "FROM sensors "
						+ "WHERE id = %s",
						(sensorId, ))
					result = self.cursor.fetchall()
					dbDescription = result[0][0]
					dbAlertDelay = result[0][1]
					dbDataType = result[0][2]

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get sensor information.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# change description if it had changed
				if dbDescription != str(sensor["description"]):

					logger.info("[%s]: Description of sensor has changed "
						% self.fileName
						+ "from '%s' to '%s'. Updating database."
						% (dbDescription, str(sensor["description"])))

					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "description = %s "
							+ "WHERE id = %s",
							(str(sensor["description"]), sensorId))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "update description of sensor.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

				# change alert delay if it had changed
				if dbAlertDelay != int(sensor["alertDelay"]):

					logger.info("[%s]: Alert delay of sensor has changed "
						% self.fileName
						+ "from '%d' to '%d'. Updating database."
						% (dbAlertDelay, int(sensor["alertDelay"])))

					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "alertDelay = %s "
							+ "WHERE id = %s",
							(int(sensor["alertDelay"]), sensorId))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "update alert delay of sensor.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

				# Change data type if it had changed (and remove
				# old data).
				if dbDataType != sensor["dataType"]:

					logger.info("[%s]: Data type of sensor has changed "
						% self.fileName
						+ "from '%d' to '%d'. Updating database."
						% (dbDataType, sensor["dataType"]))

					# Remove old data entry of sensor.
					try:
						self.cursor.execute("DELETE FROM "
							+ "sensorsDataInt "
							+ "WHERE sensorId = %s",
							(sensorId, ))

						self.cursor.execute("DELETE FROM "
							+ "sensorsDataFloat "
							+ "WHERE sensorId = %s",
							(sensorId, ))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "remove old data entry of sensor.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

					# Update data type.
					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "dataType = %s "
							+ "WHERE id = %s",
							(int(sensor["dataType"]), sensorId))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "update data type of sensor.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

					# Depending on the data type of the sensor add it to the
					# corresponding table.
					if not self._insertSensorData(sensorId,
						sensor["dataType"], sensorData, logger):

						logger.error("[%s]: Not able to add data for "
							% self.fileName
							+ "changed sensor.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

				# get sensor alert levels from database
				try:

					self.cursor.execute("SELECT alertLevel "
						+ "FROM sensorsAlertLevels "
						+ "WHERE sensorId = %s ", (sensorId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get alert levels of the sensor.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# check if the alert levels do already
				# exist in the database
				# => add alert level if it does not
				for alertLevel in sensor["alertLevels"]:

					# check if alert level already exists
					found = False
					for dbAlertLevel in result:
						if dbAlertLevel[0] == alertLevel:
							found = True
							break
					if found:
						continue

					logger.info("[%s]: Alert level '%d' of sensor does "
						% (self.fileName, alertLevel)
						+ "not exist in database. Adding it.")

					# add sensor alert level to database
					self.cursor.execute("INSERT INTO sensorsAlertLevels ("
						+ "sensorId, "
						+ "alertLevel) VALUES (%s, %s)",
						(sensorId, alertLevel))

				# get updated sensor alert levels from database
				try:

					self.cursor.execute("SELECT alertLevel "
						+ "FROM sensorsAlertLevels "
						+ "WHERE sensorId = %s ", (sensorId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get updated alert levels of the sensor.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# check if the alert levels from the database
				# do still exist in the sensor
				# => delete alert level if it does not
				for dbAlertLevel in result:

					# check if database alert level does exist
					found = False
					for alertLevel in sensor["alertLevels"]:
						if dbAlertLevel[0] == alertLevel:
							found = True
							break
					if found:
						continue

					logger.info("[%s]: Alert level '%d' in database does "
						% (self.fileName, dbAlertLevel[0])
						+ "not exist anymore for sensor. Deleting it.")

					self.cursor.execute("DELETE FROM sensorsAlertLevels "
						+ "WHERE sensorId = %s AND alertLevel = %s",
						(sensorId, dbAlertLevel[0]))

		# get updated sensors from database
		try:

			self.cursor.execute("SELECT id, "
				+ "remoteSensorId "
				+ "FROM sensors "
				+ "WHERE nodeId = %s ", (nodeId, ))
			result = self.cursor.fetchall()

		except Exception as e:
			logger.exception("[%s]: Not able to " % self.fileName
				+ "get updated sensors from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# check if the sensors from the database
		# do still exist for the node
		# => delete sensor if it does not
		for dbSensor in result:

			found = False
			for sensor in sensors:
				if dbSensor[1] == int(sensor["clientSensorId"]):
					found = True
					break
			if found:
				continue

			logger.info("[%s]: Sensor with client id '%d' in database "
				% (self.fileName, dbSensor[1])
				+ "does not exist anymore for the node. Deleting it.")

			try:
				# Delete sensor alertLevels.
				self.cursor.execute("DELETE FROM sensorsAlertLevels "
					+ "WHERE sensorId = %s",
					(dbSensor[0], ))

				# Delete old data entries (if any exist at all).
				self.cursor.execute("DELETE FROM "
					+ "sensorsDataInt "
					+ "WHERE sensorId = %s",
					(dbSensor[0], ))
				self.cursor.execute("DELETE FROM "
					+ "sensorsDataFloat "
					+ "WHERE sensorId = %s",
					(dbSensor[0], ))

				# Finally, delete sensor.
				self.cursor.execute("DELETE FROM sensors "
					+ "WHERE id = %s",
					(dbSensor[0], ))
			except Exception as e:
				logger.exception("[%s]: Not able to delete sensor."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# adds/updates the data that is given by the node for the alerts
	# to the database
	#
	# return True or False
	def addAlerts(self, username, alerts, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logger.exception("[%s]: Not able to get node id."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# add/update all alerts
		for alert in alerts:

			# check if an alert with the same remote id for this node
			# already exists in the database
			self.cursor.execute("SELECT id FROM alerts "
				+ "WHERE nodeId = %s AND remoteAlertId = %s",
				(nodeId, int(alert["clientAlertId"])))
			result = self.cursor.fetchall()

			# if the alert does not exist
			# => add it
			if len(result) == 0:

				logger.info("[%s]: Alert with client id '%d' does not "
					% (self.fileName, int(alert["clientAlertId"]))
					+ "exist in database. Adding it.")

				# add alert to database
				try:
					self.cursor.execute("INSERT INTO alerts ("
						+ "nodeId, "
						+ "remoteAlertId, "
						+ "description) VALUES (%s, %s, %s)", (nodeId,
						int(alert["clientAlertId"]),
						str(alert["description"])))
				except Exception as e:
					logger.exception("[%s]: Not able to add alert."
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# get alertId of current added alert
				try:
					alertId = self._getAlertId(nodeId,
						int(alert["clientAlertId"]))
				except Exception as e:
					logger.exception("[%s]: Not able to get alertId."
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# add alert alert levels to database
				try:
					for alertLevel in alert["alertLevels"]:
						self.cursor.execute("INSERT INTO alertsAlertLevels ("
							+ "alertId, "
							+ "alertLevel) VALUES (%s, %s)",
							(alertId, alertLevel))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "add alert alert levels.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

			# if the alert does already exist
			# => check if everything is the same
			else:

				logger.info("[%s]: Alert with client id '%d' already "
					% (self.fileName, int(alert["clientAlertId"]))
					+ "exists in database.")

				# get alertId and description
				try:
					alertId = self._getAlertId(nodeId,
						int(alert["clientAlertId"]))

					self.cursor.execute("SELECT description "
						+ "FROM alerts "
						+ "WHERE id = %s",
						(alertId, ))
					result = self.cursor.fetchall()
					dbDescription = result[0][0]

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get alert information.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# change description if it had changed
				if dbDescription != str(alert["description"]):

					logger.info("[%s]: Description of alert has changed "
						% self.fileName
						+ "from '%s' to '%s'. Updating database."
						% (dbDescription, str(alert["description"])))

					try:
						self.cursor.execute("UPDATE alerts SET "
							+ "description = %s "
							+ "WHERE id = %s",
							(str(alert["description"]), alertId))
					except Exception as e:
						logger.exception("[%s]: Not able to "
							% self.fileName
							+ "update description of alert.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return False

				# get alert alert levels from database
				try:

					self.cursor.execute("SELECT alertLevel "
						+ "FROM alertsAlertLevels "
						+ "WHERE alertId = %s ", (alertId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logger.exception("[%s]: Not able to "
						% self.fileName
						+ "get alert levels of the alert.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# check if the alert levels do already
				# exist in the database
				# => add alert level if it does not
				for alertLevel in alert["alertLevels"]:

					# check if alert level already exists
					found = False
					for dbAlertLevel in result:
						if dbAlertLevel[0] == alertLevel:
							found = True
							break
					if found:
						continue

					logger.info("[%s]: Alert level '%d' of alert does "
						% (self.fileName, alertLevel)
						+ "not exist in database. Adding it.")

					# add alert alert level to database
					self.cursor.execute("INSERT INTO alertsAlertLevels ("
						+ "alertId, "
						+ "alertLevel) VALUES (%s, %s)",
						(alertId, alertLevel))

				# get updated alert alert levels from database
				try:

					self.cursor.execute("SELECT alertLevel "
						+ "FROM alertsAlertLevels "
						+ "WHERE alertId = %s ", (alertId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "get updated alert levels of the alert.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				# check if the alert levels from the database
				# do still exist in the alert
				# => delete alert level if it does not
				for dbAlertLevel in result:

					# check if database alert level does exist
					found = False
					for alertLevel in alert["alertLevels"]:
						if dbAlertLevel[0] == alertLevel:
							found = True
							break
					if found:
						continue

					logger.info("[%s]: Alert level '%d' in database does "
						% (self.fileName, dbAlertLevel[0])
						+ "not exist anymore for alert. Deleting it.")

					self.cursor.execute("DELETE FROM alertsAlertLevels "
						+ "WHERE alertId = %s AND alertLevel = %s",
						(alertId, dbAlertLevel[0]))

		# get updated alerts from database
		try:

			self.cursor.execute("SELECT id, "
				+ "remoteAlertId "
				+ "FROM alerts "
				+ "WHERE nodeId = %s ", (nodeId, ))
			result = self.cursor.fetchall()

		except Exception as e:
			logger.exception("[%s]: Not able to " % self.fileName
				+ "get updated alerts from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# check if the alerts from the database
		# do still exist for the node
		# => delete alert if it does not
		for dbAlert in result:

			found = False
			for alert in alerts:
				if dbAlert[1] == int(alert["clientAlertId"]):
					found = True
					break
			if found:
				continue

			logger.info("[%s]: Alert with client id '%d' in "
				% (self.fileName, dbAlert[1])
				+ "database does not exist anymore for the node. Deleting it.")

			try:
				self.cursor.execute("DELETE FROM alertsAlertLevels "
					+ "WHERE alertId = %s",
					(dbAlert[0], ))

				self.cursor.execute("DELETE FROM alerts "
					+ "WHERE id = %s",
					(dbAlert[0], ))
			except Exception as e:
				logger.exception("[%s]: Not able to delete alert."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# adds/updates the data that is given by the node for
	# the manager to the database
	#
	# return True or False
	def addManager(self, username, manager, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logger.exception("[%s]: Not able to get node id."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# check if a manager with the same node id
		# already exists in the database
		self.cursor.execute("SELECT id FROM managers "
			+ "WHERE nodeId = %s",
			(nodeId, ))
		result = self.cursor.fetchall()

		# if the manager does not exist
		# => add it
		if len(result) == 0:

			logger.info("[%s]: Manager does not exist "
				% self.fileName
				+ "in database. Adding it.")

			# add manager to database
			try:
				self.cursor.execute("INSERT INTO managers ("
					+ "nodeId, "
					+ "description) VALUES (%s, %s)", (nodeId,
					str(manager["description"])))
			except Exception as e:
				logger.exception("[%s]: Not able to add manager."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		# if the manager does already exist
		# => check if everything is the same
		else:

			logger.info("[%s]: Manager already exists "
				% self.fileName
				+ "in database.")

			# get managerId and description
			try:
				managerId = self._getManagerId(nodeId)

				self.cursor.execute("SELECT description "
					+ "FROM managers "
					+ "WHERE id = %s",
					(managerId, ))
				result = self.cursor.fetchall()
				dbDescription = result[0][0]

			except Exception as e:
				logger.exception("[%s]: Not able to " % self.fileName
					+ "get manager information.")

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

			# change description if it had changed
			if dbDescription != str(manager["description"]):

				logger.info("[%s]: Description of manager has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbDescription, str(manager["description"])))

				try:
					self.cursor.execute("UPDATE managers SET "
						+ "description = %s "
						+ "WHERE id = %s",
						(str(manager["description"]), managerId))
				except Exception as e:
					logger.exception("[%s]: Not able to " % self.fileName
						+ "update description of manager.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# gets the id of the node by a given username
	# (usernames are unique to each node)
	#
	# return nodeId or None
	def getNodeId(self, username, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		nodeId = None
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logger.exception("[%s]: Not able to get node id."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return nodeId


	# Gets the ids of all nodes
	#
	# return list of nodeIds
	def getNodeIds(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		nodeIds = list()
		try:
			self.cursor.execute("SELECT id FROM nodes")
			result = self.cursor.fetchall()

			# Unpack list of tuples of one integer to list of integers.
			nodeIds = map(lambda x: x[0], result)
		except Exception as e:
			logger.exception("[%s]: Not able to get node ids."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return nodeIds


	# gets the count of the sensors of a node in the database
	# return count of sensors in database
	def getSensorCount(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		# get all sensors on this node
		sensorCount = None
		try:
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = %s ", (nodeId, ))

			result = self.cursor.fetchall()
			sensorCount = len(result)
		except Exception as e:
			logger.exception("[%s]: Not able to get sensor count."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return sensorCount


	# gets all data needed for the survey
	#
	# return list of tuples of (instance, version, rev)
	# or None
	def getSurveyData(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		surveyData = None
		try:
			self.cursor.execute("SELECT "
				+ "instance, "
				+ "version, "
				+ "rev "
				+ "FROM nodes")
			surveyData = self.cursor.fetchall()
		except Exception as e:
			logger.exception("[%s]: Not able to get survey data."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return list(surveyData)


	# gets the unique id from the database
	#
	# return unique id
	# or None
	def getUniqueID(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		uniqueID = self._getUniqueID()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return uniqueID



	# updates the states of the sensors of a node in the database
	# (given in a tuple of (remoteSensorId, state))
	#
	# return True or False
	def updateSensorState(self, nodeId, stateList, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# stateList is a list of tuples of (remoteSensorId, state)
		for stateTuple in stateList:

			try:

				# check if the sensor does exist in the database
				self.cursor.execute("SELECT id FROM sensors "
					+ "WHERE nodeId = %s "
					+ "AND remoteSensorId = %s", (nodeId, stateTuple[0]))
				result = self.cursor.fetchall()
				if len(result) != 1:
					logger.error("[%s]: Sensor does not exist in "
						% self.fileName
						+ "database.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				utcTimestamp = int(time.time())
				self.cursor.execute("UPDATE sensors SET "
					+ "state = %s, "
					+ "lastStateUpdated = %s "
					+ "WHERE nodeId = %s "
					+ "AND remoteSensorId = %s",
					(stateTuple[1], utcTimestamp, nodeId, stateTuple[0]))
			except Exception as e:
				logger.exception("[%s]: Not able to update sensor state."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# updates the data of the sensors of a node in the database
	# (given in a tuple of (remoteSensorId, data))
	#
	# return True or False
	def updateSensorData(self, nodeId, dataList, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# dataList is a list of tuples of (remoteSensorId, data)
		for dataTuple in dataList:

			try:

				# Check if the sensor does exist in the database and get its
				# data type.
				self.cursor.execute("SELECT id, dataType FROM sensors "
					+ "WHERE nodeId = %s "
					+ "AND remoteSensorId = %s", (nodeId, dataTuple[0]))
				result = self.cursor.fetchall()
				if len(result) != 1:
					logger.error("[%s]: Sensor does not exist in "
						% self.fileName
						+ "database.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return False

				sensorId = result[0][0]
				dataType = result[0][1]

				if dataType == SensorDataType.NONE:
					logger.error("[%s]: Sensor with remote id %d holds "
						% (self.fileName, dataTuple[0])
						+ "no data. Ignoring it.")

				elif dataType == SensorDataType.INT:
					self.cursor.execute("UPDATE sensorsDataInt SET "
						+ "data = %s "
						+ "WHERE sensorId = %s",
						(dataTuple[1],
						sensorId))

				elif dataType == SensorDataType.FLOAT:
					self.cursor.execute("UPDATE sensorsDataFloat SET "
						+ "data = %s "
						+ "WHERE sensorId = %s",
						(dataTuple[1],
						sensorId))

			except Exception as e:
				logger.exception("[%s]: Not able to update sensor data."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# Updates the time the sensor send an update given by sensorId.
	#
	# return True or False
	def updateSensorTime(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# Update time of sensor in the database.
		try:
			utcTimestamp = int(time.time())
			self.cursor.execute("UPDATE sensors SET "
				+ "lastStateUpdated = %s "
				+ "WHERE id = %s",
				(utcTimestamp, sensorId))

		except Exception as e:
			logger.exception("[%s]: Not able to update sensor time."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# gets the sensor id of a sensor when the id of a node is given
	# and the remote sensor id that is used by the node internally
	#
	# return sensorId or None
	def getSensorId(self, nodeId, remoteSensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		try:
			sensorId = self._getSensorId(nodeId, remoteSensorId)
		except Exception as e:
			logger.exception("[%s]: Not able to get sensorId from "
				% self.fileName
				+ "database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return sensorId


	# gets the alert id of an alert when the id of a node is given
	# and the remote alert id that is used by the node internally
	#
	# return alertId or None
	def getAlertId(self, nodeId, remoteAlertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		try:
			alertId = self._getAlertId(nodeId, remoteAlertId)
		except Exception as e:
			logger.exception("[%s]: Not able to get alertId from "
				% self.fileName
				+ "database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return alertId


	# gets all alert levels for a specific sensor given by sensorId
	#
	# return list of alertLevel
	# or None
	def getSensorAlertLevels(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		result = self._getSensorAlertLevels(sensorId, logger)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return list of alertLevel
		return result


	# gets all alert levels for a specific alert given by alertId
	#
	# return list of alertLevels
	# or None
	def getAlertAlertLevels(self, alertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		result = self._getAlertAlertLevels(sensorId, logger)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return list of alertLevels
		return map(lambda x: x[0], result)


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, sensorId, state, dataJson, changeState,
		hasLatestData, dataType, sensorData, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# add sensor alert to database
		try:
			if changeState:
				dbChangeState = 1
			else:
				dbChangeState = 0
			if hasLatestData:
				dbHasLatestData = 1
			else:
				dbHasLatestData = 0
			utcTimestamp = int(time.time())
			self.cursor.execute("INSERT INTO sensorAlerts ("
				+ "nodeId, "
				+ "sensorId, "
				+ "state, "
				+ "timeReceived, "
				+ "dataJson, "
				+ "changeState, "
				+ "hasLatestData, "
				+ "dataType) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
				(nodeId, sensorId, state, utcTimestamp, dataJson,
				dbChangeState, dbHasLatestData, dataType))

			# Get sensorAlertId of current added sensor alert.
			sensorAlertId = self.cursor.lastrowid

			if not self._insertSensorAlertData(sensorAlertId,
				dataType, sensorData, logger):

				logger.error("[%s]: Not able to add data for newly "
					% self.fileName
					+ "added sensor alert.")

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		except Exception as e:
			logger.exception("[%s]: Not able to add sensor alert."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# gets all sensor alerts in the database
	#
	# return a list of tuples (sensorAlertId, sensorId, nodeId, timeReceived,
	# alertDelay, state, description, dataJson, changeState, hasLatestData,
	# dataType, sensorData)
	# or None
	def getSensorAlerts(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		returnList = list()
		try:
			self.cursor.execute("SELECT "
				+ "sensorAlerts.id, "
				+ "sensors.id, "
				+ "sensors.nodeId, "
				+ "sensorAlerts.timeReceived, "
				+ "sensors.alertDelay, "
				+ "sensorAlerts.state, "
				+ "sensors.description, "
				+ "sensorAlerts.dataJson, "
				+ "sensorAlerts.changeState, "
				+ "sensorAlerts.hasLatestData, "
				+ "sensorAlerts.dataType "
				+ "FROM sensorAlerts "
				+ "INNER JOIN sensors "
				+ "ON sensorAlerts.nodeId = sensors.nodeId "
				+ "AND sensorAlerts.sensorId = sensors.id")
			result = self.cursor.fetchall()

			# Extract for each sensor alert the corresponding data.
			for resultTuple in result:

				sensorAlert = SensorAlert()
				sensorAlert.sensorAlertId = resultTuple[0]
				sensorAlert.sensorId = resultTuple[1]
				sensorAlert.nodeId = resultTuple[2]
				sensorAlert.timeReceived = resultTuple[3]
				sensorAlert.alertDelay = resultTuple[4]
				sensorAlert.state = resultTuple[5]
				sensorAlert.description = resultTuple[6]
				sensorAlert.changeState = (resultTuple[8] == 1)
				sensorAlert.hasLatestData = (resultTuple[9] == 1)
				sensorAlert.dataType = resultTuple[10]
				sensorAlert.rulesActivated = False

				# Set optional data for sensor alert.
				sensorAlert.hasOptionalData = False
				sensorAlert.optionalData = None
				dataJson = resultTuple[7]
				if dataJson != "":
					try:
						sensorAlert.optionalData = json.loads(dataJson)
						sensorAlert.hasOptionalData = True
					except Exception as e:
						self.logger.exception("[%s]: Optional data from "
							% self.fileName
							+ "database not a valid json string. "
							+ "Ignoring data.")

				# Set alert levels for sensor alert.
				alertLevels = self._getSensorAlertLevels(sensorAlert.sensorId,
					logger)
				if alertLevels is None:
					logger.error("[%s]: Not able to get alert levels for "
						% self.fileName
						+ "sensor alert with id %d."
						% sensorAlert.sensorAlertId)

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return None

				sensorAlert.alertLevels = alertLevels

				# Extract sensor alert data.
				if sensorAlert.dataType == SensorDataType.NONE:
					sensorAlert.sensorData = None

				elif sensorAlert.dataType == SensorDataType.INT:
					self.cursor.execute("SELECT data "
						+ "FROM sensorAlertsDataInt "
						+ "WHERE sensorAlertId = %s",
						(sensorAlert.sensorAlertId, ))
					subResult = self.cursor.fetchall()

					if len(subResult) != 1:
						logger.error("[%s]: Sensor alert data was not found."
							% self.fileName)

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return None
					sensorAlert.sensorData = subResult[0][0]

				elif sensorAlert.dataType == SensorDataType.FLOAT:
					self.cursor.execute("SELECT data "
						+ "FROM sensorAlertsDataFloat "
						+ "WHERE sensorAlertId = %s",
						(sensorAlert.sensorAlertId, ))
					subResult = self.cursor.fetchall()

					if len(subResult) != 1:
						logger.error("[%s]: Sensor alert data was not found."
							% self.fileName)

						# close connection to the database
						self._closeConnection()

						self._releaseLock(logger)

						return None
					sensorAlert.sensorData = subResult[0][0]

				else:
					logger.exception("[%s]: Not able to get sensor alerts. "
						% self.fileName
						+ "Data type in database unknown.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return None

				returnList.append(sensorAlert)

		except Exception as e:
			logger.exception("[%s]: Not able to get sensor alerts."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return a list of sensorAlert objects
		return returnList


	# Deletes a sensor alert given by its sensor alert id.
	#
	# return True or False
	def deleteSensorAlert(self, sensorAlertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		result = self._deleteSensorAlert(sensorAlertId, logger)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return result


	# Deletes a node given by its node id.
	#
	# return True or False
	def deleteNode(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# Connect to the database.
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		# Get node type from database.
		nodeObj = self._getNodeById(nodeId, logger)
		if nodeObj is None:
			logger.error("[%s]: Not able to get node with id %d."
				% (self.fileName, nodeId))

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# Delete all corresponding alert entries from database.
		if nodeObj.type == "alert":

			if not self._deleteAlertsForNodeId(nodeId, logger):

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		# Delete all corresponding manager entries from database.
		elif nodeObj.type == "manager":

			if not self._deleteManagerForNodeId(nodeId, logger):

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		# Delete all corresponding sensor entries from database.
		elif nodeObj.type == "sensor":

			if not self._deleteSensorsForNodeId(nodeId, logger):

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

		# Return if we do not know how to handle the node.
		else:
			logger.exception("[%s]: Unknown node type '%s' for node "
				% (self.fileName, nodeObj.type)
				+ "with id %d."
				% nodeId)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# Delete node from database.
		try:
			self.cursor.execute("DELETE FROM "
				+ "nodes "
				+ "WHERE id = %s",
				(nodeId, ))

		except Exception as e:
			logger.exception("[%s]: Not able to delete node with id %d."
				% (self.fileName, nodeId))

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# checks if the alert system is active or not
	#
	# return True or False
	def isAlertSystemActive(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		try:
			self.cursor.execute("SELECT value FROM options WHERE type = %s",
				("alertSystemActive", ))
			result = self.cursor.fetchall()
			alertSystemActive = result[0][0]

		except Exception as e:
			logger.exception("[%s]: Not able to check " % self.fileName
				+ "if alert system is active.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		if alertSystemActive == 1:
			return True
		elif alertSystemActive == 0:
			return False


	# gets all alert levels for the alert clients from the database
	#
	# return list alertLevels as integer
	# or None
	def getAllAlertsAlertLevels(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertsAlertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels for alert clients.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return list alertLevels as integer
		return map(lambda x: x[0], result)


	# gets all alert levels for the sensors from the database
	#
	# return list alertLevels as integer
	# or None
	def getAllSensorsAlertLevels(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM sensorsAlertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels for sensors.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return list alertLevels as integer
		return map(lambda x: x[0], result)


	# gets all nodes from the database that are connected to the server
	#
	# return list of nodeIds
	# or None
	def getAllConnectedNodeIds(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		# get all connected node ids from database
		try:
			self.cursor.execute("SELECT id "
				+ "FROM nodes "
				+ "WHERE connected = %s", (1, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "all connected node ids.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return list of nodeIds
		return map(lambda x: x[0], result)


	# Gets all nodes from the database that are registered as persistent
	# to the server.
	#
	# return list of nodeIds
	# or None
	def getAllPersistentNodeIds(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		# get all persistent node ids from database
		try:
			self.cursor.execute("SELECT id "
				+ "FROM nodes "
				+ "WHERE persistent = %s", (1, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "all persistent node ids.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return list of nodeIds
		return map(lambda x: x[0], result)


	# marks a node given by its id as NOT connected
	#
	# return True or False
	def markNodeAsNotConnected(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		try:
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = %s WHERE id = %s", (0, nodeId))
		except Exception as e:

			logger.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as not connected." % nodeId)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# marks a node given by its id as connected
	#
	# return True or False
	def markNodeAsConnected(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		try:
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = %s WHERE id = %s", (1, nodeId))
		except Exception as e:

			logger.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as connected." % nodeId)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# gets the information of all sensors which last state updates
	# are older than the given time
	#
	# return list of sensor objects
	# or None
	def getSensorsUpdatedOlderThan(self, oldestTimeUpdated, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		sensorList = list()
		try:
			self.cursor.execute("SELECT id "
				+ "FROM sensors "
				+ "WHERE lastStateUpdated < %s", (oldestTimeUpdated, ))

			results = self.cursor.fetchall()

			for resultTuple in results:
				sensorId = resultTuple[0]
				sensor = self._getSensorById(sensorId, logger)
				if sensor is not None:
					sensorList.append(sensor)

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "sensors from database which update was older than %d."
				% oldestTimeUpdated)

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return list of sensor objects
		return sensorList


	# gets the alert from the database when its id is given
	#
	# return an alert object or None
	def getAlertById(self, alertId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		result = self._getAlertById(alertId, logger)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return an alert object or None
		return result


	# gets the manager from the database when its id is given
	#
	# return a manager object or None
	def getManagerById(self, managerId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		result = self._getManagerById(managerId, logger)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return a manager object or None
		return result


	# gets the node from the database when its id is given
	#
	# return a node object or None
	def getNodeById(self, nodeId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		result = self._getNodeById(nodeId, logger)

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return a node object or None
		return result


	# gets the sensor from the database when its id is given
	#
	# return a sensor object or None
	def getSensorById(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		result = self._getSensorById(sensorId, logger)

		self._releaseLock(logger)

		# return a sensor object or None
		return result


	# Gets all nodes from the database.
	#
	# return a list of node objects or None
	def getNodes(self, logger=None):
		
		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# Connect to the database.
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		nodes = list()
		try:

			# Get all nodes information.
			self.cursor.execute("SELECT * FROM nodes")
			nodeTuples = self.cursor.fetchall()
			for nodeTuple in nodeTuples:
				node = self._convertNodeTupleToObj(nodeTuple)
				nodes.append(node)

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "nodes from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# list(node objects)
		return nodes


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = list(option objects)
	# list[1] = list(node objects)
	# list[2] = list(sensor objects)
	# list[3] = list(manager objects)
	# list[4] = list(alert objects)
	# or None
	def getAlertSystemInformation(self, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		try:

			# Get all options.
			optionList = list()
			self.cursor.execute("SELECT type, "
				+ "value "
				+ "FROM options")
			results = self.cursor.fetchall()
			for resultTuple in results:
				optionObj = Option()
				optionObj.type = resultTuple[0]
				optionObj.value = resultTuple[1]
				optionList.append(optionObj)

			# Get all nodes.
			nodeList = list()
			self.cursor.execute("SELECT * FROM nodes")
			results = self.cursor.fetchall()
			for resultTuple in results:
				nodeObj = self._convertNodeTupleToObj(resultTuple)
				nodeList.append(nodeObj)

			# Get all sensors.
			sensorList = list()
			self.cursor.execute("SELECT id FROM sensors")
			results = self.cursor.fetchall()
			for resultTuple in results:
				sensorObj = self._getSensorById(resultTuple[0], logger)
				if sensorObj is None:
					raise ValueError("Can not retrieve sensor with id %d."
						% resultTuple[0])
				sensorList.append(sensorObj)

			# Get all managers.
			managerList = list()
			self.cursor.execute("SELECT id FROM managers")
			results = self.cursor.fetchall()
			for resultTuple in results:
				managerObj = self._getManagerById(resultTuple[0], logger)
				if managerObj is None:
					raise ValueError("Can not retrieve manager with id %d."
						% resultTuple[0])
				managerList.append(managerObj)

			# Get all alerts.
			alertList = list()
			self.cursor.execute("SELECT id FROM alerts")
			results = self.cursor.fetchall()
			for resultTuple in results:
				alertObj = self._getAlertById(resultTuple[0], logger)
				if alertObj is None:
					raise ValueError("Can not retrieve alert with id %d."
						% resultTuple[0])
				alertList.append(alertObj)

			# Generate a list with system information.
			alertSystemInformation = list()
			alertSystemInformation.append(optionList)
			alertSystemInformation.append(nodeList)
			alertSystemInformation.append(sensorList)
			alertSystemInformation.append(managerList)
			alertSystemInformation.append(alertList)

		except Exception as e:

			logger.exception("[%s]: Not able to get " % self.fileName
				+ "complete system information from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return a list of
		# list[0] = list(option objects)
		# list[1] = list(node objects)
		# list[2] = list(sensor objects)
		# list[3] = list(manager objects)
		# list[4] = list(alert objects)
		# or None
		return alertSystemInformation


	# change a option in the database
	#
	# return True or False
	def changeOption(self, optionType, optionValue, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return False

		try:
			# check if option does exist
			self.cursor.execute("SELECT id "
				+ "FROM options "
				+ "WHERE type = %s", (optionType, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logger.error("[%s]: Option was not found."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return False

			# update option in database
			self.cursor.execute("UPDATE options SET "
				+ "value = %s "
				+ "WHERE type = %s", (optionValue, optionType))

		except Exception as e:

			logger.exception("[%s]: Not able to update " % self.fileName
				+ "option in database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return True


	# gets the state of a sensor given by id
	#
	# return sensor state or None
	def getSensorState(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		try:
			# get sensor state from database
			self.cursor.execute("SELECT state "
				+ "FROM sensors "
				+ "WHERE id = %s", (sensorId, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logger.error("[%s]: Sensor was not found."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return None

			state = result[0][0]

		except Exception as e:

			logger.exception("[%s]: Not able to get "
				% self.fileName
				+ "sensor state from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		return state


	# Gets the data of a sensor given by id.
	#
	# return a sensor data object or None
	def getSensorData(self, sensorId, logger=None):

		# Set logger instance to use.
		if not logger:
			logger = self.logger

		self._acquireLock(logger)

		# connect to the database
		try:
			self._openConnection(logger)
		except Exception as e:
			logger.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock(logger)

			return None

		try:
			# Get data type from database.
			self.cursor.execute("SELECT dataType "
				+ "FROM sensors "
				+ "WHERE id = %s", (sensorId, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logger.error("[%s]: Sensor was not found."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return None

			dataType = result[0][0]

		except Exception as e:

			logger.exception("[%s]: Not able to get "
				% self.fileName
				+ "sensor data type from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock(logger)

			return None

		data = SensorData()
		data.sensorId = sensorId
		data.dataType = dataType
		if dataType == SensorDataType.NONE:
			data.data = None

		elif dataType == SensorDataType.INT:
			try:
				# Get data type from database.
				self.cursor.execute("SELECT data "
					+ "FROM sensorsDataInt "
					+ "WHERE sensorId = %s", (sensorId, ))
				result = self.cursor.fetchall()
				if len(result) != 1:
					logger.error("[%s]: Sensor data was not found."
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return None

				data.data = result[0][0]

			except Exception as e:

				logger.exception("[%s]: Not able to get "
					% self.fileName
					+ "sensor data from database.")

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return None

		elif dataType == SensorDataType.FLOAT:
			try:
				# Get data type from database.
				self.cursor.execute("SELECT data "
					+ "FROM sensorsDataFloat "
					+ "WHERE sensorId = %s", (sensorId, ))
				result = self.cursor.fetchall()
				if len(result) != 1:
					logger.error("[%s]: Sensor data was not found."
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock(logger)

					return None

				data.data = result[0][0]

			except Exception as e:

				logger.exception("[%s]: Not able to get "
					% self.fileName
					+ "sensor data from database.")

				# close connection to the database
				self._closeConnection()

				self._releaseLock(logger)

				return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock(logger)

		# return a sensor data object or None
		return data


	# closes db for usage
	#
	# no return value
	def close(self, logger=None):
		pass