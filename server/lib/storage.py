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
import socket
import struct
import hashlib


# internal abstract class for new storage backends
class _Storage():

	# creates the database (should only be called if the database
	# does not exist)
	#
	# no return value but raise exception if it fails
	def createStorage(self):
		raise NotImplemented("Function not implemented yet.")


	# checks the version of the server and the version in the database
	# and clears every compatibility issue
	#
	# no return value but raise exception if it fails
	def checkVersionAndClearConflict(self):
		raise NotImplemented("Function not implemented yet.")


	# adds a node if it does not exist or changes the registered
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType, instance, version, rev,
		persistent):
		raise NotImplemented("Function not implemented yet.")


	# adds/updates the data that is given by the node for the sensors
	# to the database
	#
	# return True or False
	def addSensors(self, username, sensors):
		raise NotImplemented("Function not implemented yet.")


	# adds/updates the data that is given by the node for the alerts
	# to the database
	#
	# return True or False
	def addAlerts(self, username, alerts):
		raise NotImplemented("Function not implemented yet.")


	# adds/updates the data that is given by the node for
	# the manager to the database
	#
	# return True or False
	def addManager(self, username, manager):
		raise NotImplemented("Function not implemented yet.")


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, remoteSensorId, state, changeState,
		dataJson):
		raise NotImplemented("Function not implemented yet.")


	# gets the id of the node by a given username
	# (usernames are unique to each node)
	#
	# return nodeId or None
	def getNodeId(self, username):
		raise NotImplemented("Function not implemented yet.")


	# gets the count of the sensors of a node in the database
	#
	# return count of sensors or None
	def getSensorCount(self, nodeId):
		raise NotImplemented("Function not implemented yet.")


	# gets the sensor id of a sensor when the id of a node is given
	# and the remote sensor id that is used by the node internally
	#
	# return sensorId or None
	def getSensorId(self, nodeId, remoteSensorId):
		raise NotImplemented("Function not implemented yet.")


	# gets all data needed for the survey
	#
	# return list of tuples of (instance, version, rev)
	# or None
	def getSurveyData(self):
		raise NotImplemented("Function not implemented yet.")


	# gets the unique id from the database
	#
	# return unique id
	# or None
	def getUniqueID(self):
		raise NotImplemented("Function not implemented yet.")


	# gets the alert id of a alert when the id of a node is given
	# and the remote alert id that is used by the node internally
	#
	# return alertId or None
	def getAlertId(self, nodeId, remoteAlertId):
		raise NotImplemented("Function not implemented yet.")


	# gets all alert levels for a specific sensor given by sensorId
	#
	# return list of alertLevel
	# or None
	def getSensorAlertLevels(self, sensorId):
		raise NotImplemented("Function not implemented yet.")


	# gets all alert levels for a specific alert given by alertId
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAlertAlertLevels(self, alertId):
		raise NotImplemented("Function not implemented yet.")


	# gets all sensor alerts in the database
	#
	# return a list of tuples (sensorAlertId, sensorId, nodeId, timeReceived,
	# alertDelay, state, description, dataJson)
	# or None
	def getSensorAlerts(self):
		raise NotImplemented("Function not implemented yet.")


	# gets all alert levels for the alert clients from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllAlertsAlertLevels(self):
		raise NotImplemented("Function not implemented yet.")


	# gets all alert levels for the sensors from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllSensorsAlertLevels(self):
		raise NotImplemented("Function not implemented yet.")	


	# gets all nodes from the database that are connected to the server
	#
	# return list of nodeIds
	# or None
	def getAllConnectedNodeIds(self):
		raise NotImplemented("Function not implemented yet.")


	# Gets all nodes from the database that are registered as persistent
	# to the server.
	#
	# return list of nodeIds
	# or None
	def getAllPersistentNodeIds(self):
		raise NotImplemented("Function not implemented yet.")


	# gets the information of all sensors which last state updates
	# are older than the given time
	#
	# return list of tuples of (sensorId, nodeId,
	# lastStateUpdated, description)
	# or None
	def getSensorsUpdatedOlderThan(self, oldestTimeUpdated):
		raise NotImplemented("Function not implemented yet.")


	# gets all information of a sensor by its given id
	#
	# return a tuple of (sensorId, nodeId,
	# remoteSensorId, description, state, lastStateUpdated, alertDelay)
	# or None
	def getSensorInformation(self, sensorId):
		raise NotImplemented("Function not implemented yet.")


	# gets the node from the database when its id is given
	#
	# return a tuple of (nodeId, hostname, username, nodeType, instance,
	# connected, version, rev, persistent) or None
	def getNodeById(self, nodeId):
		raise NotImplemented("Function not implemented yet.")


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = list(tuples of (type, value))
	# list[1] = list(tuples of (nodeId, hostname, username, nodeType,
	# instance, connected, version, rev, persistent))
	# list[2] = list(tuples of (sensorId, nodeId, remoteSensorId,
	# description, state, lastStateUpdated, alertDelay))
	# list[3] = list(tuples of (managerId, nodeId, description))
	# list[4] = list(tuples of (alertId, nodeId, remoteAlertId,
	# description))
	# or None
	def getAlertSystemInformation(self):
		raise NotImplemented("Function not implemented yet.")


	# gets the state of a sensor given by id
	#
	# return sensor state or None
	def getSensorState(self, sensorId):
		raise NotImplemented("Function not implemented yet.")


	# change a option in the database
	#
	# return True or False
	def changeOption(self, optionType, optionValue):
		raise NotImplemented("Function not implemented yet.")


	# marks a node given by its id as NOT connected
	#
	# return True or False
	def markNodeAsNotConnected(self, nodeId):
		raise NotImplemented("Function not implemented yet.")


	# marks a node given by its id as connected
	#
	# return True or False
	def markNodeAsConnected(self, nodeId):
		raise NotImplemented("Function not implemented yet.")


	# deletes a sensor alert given by its sensor alert id
	#
	# return True or False
	def deleteSensorAlert(self, sensorAlertId):
		raise NotImplemented("Function not implemented yet.")


	# checks if the alert system is active or not
	#
	# return True or False
	def isAlertSystemActive(self):
		raise NotImplemented("Function not implemented yet.")


	# updates the states of the sensors of a node in the databse
	# (given in a tuple of (remoteSensorId, state))
	#
	# return True or False
	def updateSensorState(self, nodeId, stateList):
		raise NotImplemented("Function not implemented yet.")


	# closes db for usage
	#
	# no return value
	def close(self):
		raise NotImplemented("Function not implemented yet.")


# class for using sqlite as storage backend
class Sqlite(_Storage):

	def __init__(self, storagePath, globalData):

		# import the needed package
		import sqlite3

		self.globalData = globalData

		# version of server
		self.version = self.globalData.version
		self.rev = self.globalData.rev

		# unique id of this server (is also the username of this server)
		# (used for caching)
		self.uniqueID = None

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# path to the sqlite database
		self.storagePath = storagePath

		# sqlite is not thread safe => use lock
		self.dbLock = threading.Semaphore(1)

		# check if database exists
		# if not create one
		if os.path.exists(self.storagePath) == False:
			
			logging.info("[%s]: No database found. Creating '%s'."
			% (self.fileName, self.storagePath))

			self.conn = sqlite3.connect(self.storagePath,
				check_same_thread=False)
			self.cursor = self.conn.cursor()
			self.createStorage()
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
		uniqueString = socket.gethostname() \
			+ struct.pack("d", time.time()) \
			+ os.urandom(200)
		sha256 = hashlib.sha256()
		sha256.update(uniqueString)
		uniqueID = sha256.hexdigest()

		return uniqueID


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
	def _getUniqueID(self):

		# if unique id already cached => return it
		if not self.uniqueID is None:
			return self.uniqueID

		try:
			self.cursor.execute("SELECT value "
				+ "FROM internals WHERE type=?", ("uniqueID", ))
			self.uniqueID = self.cursor.fetchall()[0][0]
		except Exception as e:
			logging.exception("[%s]: Not able to get the unique id." 
				% self.fileName)

		return self.uniqueID


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.dbLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
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

		# create node entry for this server (use unique id as username)
		self.cursor.execute("INSERT INTO nodes ("
			+ "hostname, "
			+ "username, "
			+ "nodeType, "
			+ "instance, "
			+ "connected, "
			+ "version, "
			+ "rev, "
			+ "persistent) "
			+ "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
			(socket.gethostname(), uniqueID, "server", "server", 1,
			self.version, self.rev, 1))

		# create sensors table
		self.cursor.execute("CREATE TABLE sensors ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteSensorId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "lastStateUpdated INTEGER NOT NULL, "
			+ "alertDelay INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create sensorsAlertLevels table
		self.cursor.execute("CREATE TABLE sensorsAlertLevels ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "sensorId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create sensorAlerts table
		self.cursor.execute("CREATE TABLE sensorAlerts ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "sensorId INTEGER NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "timeReceived INTEGER NOT NULL, "
			+ "dataJson TEXT NOT NULL,"
			+ "changeState INTEGER NOT NULL,"
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id), "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create alerts table
		self.cursor.execute("CREATE TABLE alerts ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteAlertId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create alertsAlertLevels table
		self.cursor.execute("CREATE TABLE alertsAlertLevels ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "alertId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "FOREIGN KEY(alertId) REFERENCES alerts(id))")

		# create managers table
		self.cursor.execute("CREATE TABLE managers ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")		

		# commit all changes
		self.conn.commit()


	# checks the version of the server and the version in the database
	# and clears every compatibility issue
	#
	# no return value but raise exception if it fails
	def checkVersionAndClearConflict(self):

		self._acquireLock()

		# get version from the current database
		self.cursor.execute("SELECT value FROM internals "
			+ "WHERE type = ?",
			("version", ))
		result = self.cursor.fetchall()

		# if the versions are not compatible
		# => delete old database schema
		if float(result[0][0]) != self.version:

			logging.info("[%s]: Server version "
				% self.fileName
				+ "'%.3f' not compatible "
				% self.version
				+ "with database version '%.3f'. "
				% float(result[0][0])
				+ "Updating database.")

			# get old uniqueId to keep it
			uniqueID = self._getUniqueID()
			if uniqueID is None:
				uniqueID = self._generateUniqueId()

			# delete all tables from the database to clear the old version
			self.cursor.execute("DROP TABLE IF EXISTS internals")
			self.cursor.execute("DROP TABLE IF EXISTS options")
			self.cursor.execute("DROP TABLE IF EXISTS sensorAlerts")
			self.cursor.execute("DROP TABLE IF EXISTS sensorsAlertLevels")
			self.cursor.execute("DROP TABLE IF EXISTS sensors")
			self.cursor.execute("DROP TABLE IF EXISTS alertsAlertLevels")
			self.cursor.execute("DROP TABLE IF EXISTS alerts")
			self.cursor.execute("DROP TABLE IF EXISTS managers")
			self.cursor.execute("DROP TABLE IF EXISTS nodes")

			# create new database
			self._createStorage(uniqueID)

			# commit all changes
			self.conn.commit()

		self._releaseLock()


	# creates the database (should only be called if the database
	# does not exist)
	#
	# no return value but raise exception if it fails
	def createStorage(self):

		self._acquireLock()

		uniqueID = self._generateUniqueId()

		self._createStorage(uniqueID)

		self._releaseLock()


	# adds a node if it does not exist or changes the registered
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType, instance, version, rev,
		persistent):

		self._acquireLock()

		# check if a node with the same username already exists
		# => if not add node
		if not self._usernameInDb(username):

			logging.info("[%s]: Node with username '%s' does not exist "
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
				logging.exception("[%s]: Not able to add node."
					% self.fileName)

				self._releaseLock()

				return False

		# if a node with this username exists
		# => check if everything is the same
		else:

			logging.info("[%s]: Node with username '%s' already exists "
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
				logging.exception("[%s]: Not able to get node information."
					% self.fileName)

				self._releaseLock()

				return False

			# change hostname if it had changed
			if dbHostname != hostname:

				logging.info("[%s]: Hostname of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbHostname, hostname))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "hostname = ? "
						+ "WHERE id = ?",
						(hostname, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update hostname of node.")

					self._releaseLock()

					return False

			# change instance if it had changed
			if dbInstance != instance:

				logging.info("[%s]: Instance of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbInstance, instance))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "instance = ? "
						+ "WHERE id = ?",
						(instance, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update instance of node.")

					self._releaseLock()

					return False

			# change version if it had changed
			if dbVersion != version:

				logging.info("[%s]: Version of node has changed "
					% self.fileName
					+ "from '%.3f' to '%.3f'. Updating database."
					% (dbVersion, version))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "version = ? "
						+ "WHERE id = ?",
						(version, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update version of node.")

					self._releaseLock()

					return False

			# change revision if it had changed
			if dbRev != rev:

				logging.info("[%s]: Revision of node has changed "
					% self.fileName
					+ "from '%d' to '%d'. Updating database."
					% (dbRev, rev))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "rev = ? "
						+ "WHERE id = ?",
						(rev, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update revision of node.")

					self._releaseLock()

					return False

			# change persistent if it had changed
			if dbPersistent != persistent:

				logging.info("[%s]: Persistent flag of node has changed "
					% self.fileName
					+ "from '%d' to '%d'. Updating database."
					% (dbPersistent, persistent))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "persistent = ? "
						+ "WHERE id = ?",
						(persistent, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update persistent flag of node.")

					self._releaseLock()

					return False

			# if node type has changed
			# => delete sensors/alerts/manager information of old node
			# and change node type
			if dbNodeType != nodeType:

				logging.info("[%s]: Type of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbNodeType, nodeType))

				# if old node had type "sensor"
				# => delete all sensors
				if dbNodeType == "sensor":

					try:
						# get all sensor ids that are connected to
						# the old sensor
						self.cursor.execute("SELECT id FROM sensors "
							+ "WHERE nodeId = ? ", (nodeId, ))
						result = self.cursor.fetchall()

						# delete all sensor alert levels and sensors of
						# this node
						for sensorIdResult in result:

							self.cursor.execute("DELETE FROM "
								+ "sensorsAlertLevels "
								+ "WHERE sensorId = ?",
								(sensorIdResult[0], ))

							self.cursor.execute("DELETE FROM sensors "
								+ "WHERE id = ?",
								(sensorIdResult[0], ))

					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "delete sensors of the node.")

						self._releaseLock()

						return False

				# if old node had type "alert"
				# => delete all alerts
				elif dbNodeType == "alert":

					try:
						# get all alert ids that are connected to
						# the old alert
						self.cursor.execute("SELECT id FROM alerts "
							+ "WHERE nodeId = ?", (nodeId, ))
						result = self.cursor.fetchall()

						# delete all alert alert levels and alerts of
						# this node
						for alertIdResult in result:

							self.cursor.execute("DELETE FROM "
								+ "alertsAlertLevels "
								+ "WHERE alertId = ?",
								(alertIdResult[0], ))

							self.cursor.execute("DELETE FROM alerts "
								+ "WHERE id = ?",
								(alertIdResult[0], ))

					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "delete alerts of the node.")

						self._releaseLock()

						return False

				# if old node had type "manager"
				# => delete all manager information
				elif dbNodeType == "manager":
					
					try:
						self.cursor.execute("DELETE FROM managers "
							+ "WHERE nodeId = ?",
							(nodeId, ))

					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "delete manager information of the node.")

						self._releaseLock()

						return False

				# node type in database not known
				else:

					logging.error("[%s]: Unknown node type " % self.fileName
						+ "when deleting old sensors/alerts/manager "
						+ "information.")

					self._releaseLock()

					return False

				# update node type
				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "nodeType = ? "
						+ "WHERE id = ?",
						(nodeType, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update type of node.")

					self._releaseLock()

					return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# adds/updates the data that is given by the node for the sensors
	# to the database
	#
	# return True or False
	def addSensors(self, username, sensors):

		self._acquireLock()	

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to get node id." % self.fileName)

			self._releaseLock()

			return False

		# add/update all sensors
		for sensor in sensors:

			# check if a sensor with the same remote id for this node
			# already exists in the database
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = ? AND remoteSensorId = ?",
				(nodeId, int(sensor["clientSensorId"])))
			result = self.cursor.fetchall()

			# if the sensor does not exist
			# => add it
			if len(result) == 0:

				logging.info("[%s]: Sensor with client id '%d' does not exist "
					% (self.fileName, int(sensor["clientSensorId"]))
					+ "in database. Adding it.")

				# add sensor to database
				try:
					self.cursor.execute("INSERT INTO sensors ("
						+ "nodeId, "
						+ "remoteSensorId, "
						+ "description, "
						+ "state, "
						+ "lastStateUpdated, "
						+ "alertDelay) VALUES (?, ?, ?, ?, ?, ?)",
						(nodeId, int(sensor["clientSensorId"]),
						str(sensor["description"]), 0, 0,
						int(sensor["alertDelay"])))
				except Exception as e:
					logging.exception("[%s]: Not able to add sensor."
						% self.fileName)

					self._releaseLock()

					return False

				# get sensorId of current added sensor
				try:
					sensorId = self._getSensorId(nodeId,
						int(sensor["clientSensorId"]))
				except Exception as e:
					logging.exception("[%s]: Not able to get sensorId." 
						% self.fileName)

					self._releaseLock()

					return False

				# add sensor alert levels to database
				try:
					for alertLevel in sensor["alertLevels"]:			
						self.cursor.execute("INSERT INTO sensorsAlertLevels ("
							+ "sensorId, "
							+ "alertLevel) VALUES (?, ?)",
							(sensorId, alertLevel))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "add sensor alert levels.")

					self._releaseLock()

					return False

			# if the sensor does already exist
			# => check if everything is the same
			else:

				logging.info("[%s]: Sensor with client id '%d' already exists "
					% (self.fileName, int(sensor["clientSensorId"]))
					+ "in database.")

				# get sensorId, description and alertDelay
				try:
					sensorId = self._getSensorId(nodeId,
						int(sensor["clientSensorId"]))

					self.cursor.execute("SELECT description, "
						+ "alertDelay "
						+ "FROM sensors "
						+ "WHERE id = ?",
						(sensorId, ))
					result = self.cursor.fetchall()
					dbDescription = result[0][0]
					dbAlertDelay = result[0][1]

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get sensor information.")

					self._releaseLock()

					return False

				# change description if it had changed
				if dbDescription != str(sensor["description"]):

					logging.info("[%s]: Description of sensor has changed "
						% self.fileName
						+ "from '%s' to '%s'. Updating database."
						% (dbDescription, str(sensor["description"])))

					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "description = ? "
							+ "WHERE id = ?",
							(str(sensor["description"]), sensorId))
					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "update description of sensor.")

						self._releaseLock()

						return False

				# change alert delay if it had changed
				if dbAlertDelay != int(sensor["alertDelay"]):

					logging.info("[%s]: Alert delay of sensor has changed "
						% self.fileName
						+ "from '%d' to '%d'. Updating database."
						% (dbAlertDelay, int(sensor["alertDelay"])))

					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "alertDelay = ? "
							+ "WHERE id = ?",
							(int(sensor["alertDelay"]), sensorId))
					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "update alert delay of sensor.")

						self._releaseLock()

						return False

				# get sensor alert levels from database
				try:
					
					self.cursor.execute("SELECT id, "
						+ "alertLevel "
						+ "FROM sensorsAlertLevels "
						+ "WHERE sensorId = ? ", (sensorId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get alert levels of the sensor.")

					self._releaseLock()

					return False

				# check if the alert levels do already
				# exist in the database
				# => add alert level if it does not
				for alertLevel in sensor["alertLevels"]:

					# check if alert level already exists
					found = False
					for dbAlertLevel in result:
						if dbAlertLevel[1] == alertLevel:
							found = True
							break
					if found:
						continue

					logging.info("[%s]: Alert level '%d' of sensor does not "
						% (self.fileName, alertLevel)
						+ "exist in database. Adding it.")

					# add sensor alert level to database
					self.cursor.execute("INSERT INTO sensorsAlertLevels ("
						+ "sensorId, "
						+ "alertLevel) VALUES (?, ?)",
						(sensorId, alertLevel))

				# get updated sensor alert levels from database
				try:
					
					self.cursor.execute("SELECT id, "
						+ "alertLevel "
						+ "FROM sensorsAlertLevels "
						+ "WHERE sensorId = ? ", (sensorId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get updated alert levels of the sensor.")

					self._releaseLock()

					return False

				# check if the alert levels from the database
				# do still exist in the sensor
				# => delete alert level if it does not
				for dbAlertLevel in result:

					# check if database alert level does exist
					found = False
					for alertLevel in sensor["alertLevels"]:
						if dbAlertLevel[1] == alertLevel:
							found = True
							break
					if found:
						continue

					logging.info("[%s]: Alert level '%d' in database does "
						% (self.fileName, dbAlertLevel[1])
						+ "not exist anymore for sensor. Deleting it.")

					self.cursor.execute("DELETE FROM sensorsAlertLevels "
						+ "WHERE id = ?",
						(dbAlertLevel[0], ))

		# get updated sensors from database
		try:
					
			self.cursor.execute("SELECT id, "
				+ "remoteSensorId "
				+ "FROM sensors "
				+ "WHERE nodeId = ? ", (nodeId, ))
			result = self.cursor.fetchall()

		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "get updated sensors from database.")

			self._releaseLock()

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

			logging.info("[%s]: Sensor with client id '%d' in database does "
				% (self.fileName, dbSensor[1])
				+ "not exist anymore for the node. Deleting it.")

			try:
				self.cursor.execute("DELETE FROM sensorsAlertLevels "
					+ "WHERE sensorId = ?",
					(dbSensor[0], ))

				self.cursor.execute("DELETE FROM sensors "
					+ "WHERE id = ?",
					(dbSensor[0], ))
			except Exception as e:
				logging.exception("[%s]: Not able to delete sensor." 
					% self.fileName)

				self._releaseLock()

				return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# adds/updates the data that is given by the node for the alerts
	# to the database
	#
	# return True or False
	def addAlerts(self, username, alerts):

		self._acquireLock()	

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to get node id." % self.fileName)

			self._releaseLock()

			return False

		# add/update all alerts
		for alert in alerts:

			# check if a alert with the same remote id for this node
			# already exists in the database
			self.cursor.execute("SELECT id FROM alerts "
				+ "WHERE nodeId = ? AND remoteAlertId = ?",
				(nodeId, int(alert["clientAlertId"])))
			result = self.cursor.fetchall()

			# if the alert does not exist
			# => add it
			if len(result) == 0:

				logging.info("[%s]: Alert with client id '%d' does not exist "
					% (self.fileName, int(alert["clientAlertId"]))
					+ "in database. Adding it.")

				# add alert to database
				try:
					self.cursor.execute("INSERT INTO alerts ("
						+ "nodeId, "
						+ "remoteAlertId, "
						+ "description) VALUES (?, ?, ?)", (nodeId,
						int(alert["clientAlertId"]),
						str(alert["description"])))
				except Exception as e:
					logging.exception("[%s]: Not able to add alert."
						% self.fileName)

					self._releaseLock()

					return False

				# get alertId of current added alert
				try:
					alertId = self._getAlertId(nodeId,
						int(alert["clientAlertId"]))
				except Exception as e:
					logging.exception("[%s]: Not able to get alertId." 
						% self.fileName)

					self._releaseLock()

					return False

				# add alert alert levels to database
				try:
					for alertLevel in alert["alertLevels"]:			
						self.cursor.execute("INSERT INTO alertsAlertLevels ("
							+ "alertId, "
							+ "alertLevel) VALUES (?, ?)",
							(alertId, alertLevel))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "add alert alert levels.")

					self._releaseLock()

					return False

			# if the alert does already exist
			# => check if everything is the same
			else:

				logging.info("[%s]: Alert with client id '%d' already exists "
					% (self.fileName, int(alert["clientAlertId"]))
					+ "in database.")

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
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get alert information.")

					self._releaseLock()

					return False

				# change description if it had changed
				if dbDescription != str(alert["description"]):

					logging.info("[%s]: Description of alert has changed "
						% self.fileName
						+ "from '%s' to '%s'. Updating database."
						% (dbDescription, str(alert["description"])))

					try:
						self.cursor.execute("UPDATE alerts SET "
							+ "description = ? "
							+ "WHERE id = ?",
							(str(alert["description"]), alertId))
					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "update description of alert.")

						self._releaseLock()

						return False

				# get alert alert levels from database
				try:
					
					self.cursor.execute("SELECT id, "
						+ "alertLevel "
						+ "FROM alertsAlertLevels "
						+ "WHERE alertId = ? ", (alertId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get alert levels of the alert.")

					self._releaseLock()

					return False

				# check if the alert levels do already
				# exist in the database
				# => add alert level if it does not
				for alertLevel in alert["alertLevels"]:

					# check if alert level already exists
					found = False
					for dbAlertLevel in result:
						if dbAlertLevel[1] == alertLevel:
							found = True
							break
					if found:
						continue

					logging.info("[%s]: Alert level '%d' of alert does not "
						% (self.fileName, alertLevel)
						+ "exist in database. Adding it.")

					# add alert alert level to database
					self.cursor.execute("INSERT INTO alertsAlertLevels ("
						+ "alertId, "
						+ "alertLevel) VALUES (?, ?)",
						(alertId, alertLevel))

				# get updated alert alert levels from database
				try:
					
					self.cursor.execute("SELECT id, "
						+ "alertLevel "
						+ "FROM alertsAlertLevels "
						+ "WHERE alertId = ? ", (alertId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get updated alert levels of the alert.")

					self._releaseLock()

					return False

				# check if the alert levels from the database
				# do still exist in the alert
				# => delete alert level if it does not
				for dbAlertLevel in result:

					# check if database alert level does exist
					found = False
					for alertLevel in alert["alertLevels"]:
						if dbAlertLevel[1] == alertLevel:
							found = True
							break
					if found:
						continue

					logging.info("[%s]: Alert level '%d' in database does "
						% (self.fileName, dbAlertLevel[1])
						+ "not exist anymore for alert. Deleting it.")

					self.cursor.execute("DELETE FROM alertsAlertLevels "
						+ "WHERE id = ?",
						(dbAlertLevel[0], ))

		# get updated alerts from database
		try:
					
			self.cursor.execute("SELECT id, "
				+ "remoteAlertId "
				+ "FROM alerts "
				+ "WHERE nodeId = ? ", (nodeId, ))
			result = self.cursor.fetchall()

		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "get updated alerts from database.")

			self._releaseLock()

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

			logging.info("[%s]: Alert with client id '%d' in database does "
				% (self.fileName, dbAlert[1])
				+ "not exist anymore for the node. Deleting it.")

			try:
				self.cursor.execute("DELETE FROM alertsAlertLevels "
					+ "WHERE alertId = ?",
					(dbAlert[0], ))

				self.cursor.execute("DELETE FROM alerts "
					+ "WHERE id = ?",
					(dbAlert[0], ))
			except Exception as e:
				logging.exception("[%s]: Not able to delete alert." 
					% self.fileName)

				self._releaseLock()

				return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# adds/updates the data that is given by the node for
	# the manager to the database
	#
	# return True or False
	def addManager(self, username, manager):

		self._acquireLock()	

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to get node id." % self.fileName)

			self._releaseLock()

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

			logging.info("[%s]: Manager does not exist "
				% self.fileName
				+ "in database. Adding it.")

			# add manager to database
			try:
				self.cursor.execute("INSERT INTO managers ("
					+ "nodeId, "
					+ "description) VALUES (?, ?)", (nodeId,
					str(manager["description"])))
			except Exception as e:
				logging.exception("[%s]: Not able to add manager."
					% self.fileName)

				self._releaseLock()

				return False

		# if the manager does already exist
		# => check if everything is the same
		else:

			logging.info("[%s]: Manager already exists "
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
				logging.exception("[%s]: Not able to " % self.fileName
					+ "get manager information.")

				self._releaseLock()

				return False

			# change description if it had changed
			if dbDescription != str(manager["description"]):

				logging.info("[%s]: Description of manager has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbDescription, str(manager["description"])))

				try:
					self.cursor.execute("UPDATE managers SET "
						+ "description = ? "
						+ "WHERE id = ?",
						(str(manager["description"]), managerId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update description of manager.")

					self._releaseLock()

					return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# gets the id of the node by a given username
	# (usernames are unique to each node)
	#
	# return nodeId or None
	def getNodeId(self, username):

		self._acquireLock()

		nodeId = None
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to get node id." 
				% self.fileName)			
	
		self._releaseLock()

		return nodeId


	# gets the count of the sensors of a node in the database
	#
	# return count of sensors or None
	def getSensorCount(self, nodeId):

		self._acquireLock()

		# get all sensors on this nodes
		sensorCount = None
		try:
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = ?", (nodeId, ))
			result = self.cursor.fetchall()
			sensorCount = len(result)
		except Exception as e:
			logging.exception("[%s]: Not able to get sensor count." 
				% self.fileName)	

		self._releaseLock()

		return sensorCount


	# gets all data needed for the survey
	#
	# return list of tuples of (instance, version, rev)
	# or None
	def getSurveyData(self):

		self._acquireLock()

		surveyData = None
		try:
			self.cursor.execute("SELECT "
				+ "instance, "
				+ "version, "
				+ "rev "
				+ "FROM nodes")
			surveyData = self.cursor.fetchall()
		except Exception as e:
			logging.exception("[%s]: Not able to get survey data." 
				% self.fileName)

		self._releaseLock()

		return surveyData

	# gets the unique id from the database
	#
	# return unique id
	# or None
	def getUniqueID(self):

		self._acquireLock()

		uniqueID = self._getUniqueID()

		self._releaseLock()

		return uniqueID


	# updates the states of the sensors of a node in the databse
	# (given in a tuple of (remoteSensorId, state))
	#
	# return True or False
	def updateSensorState(self, nodeId, stateList):
		
		self._acquireLock()

		# stateList is a list of tuples of (remoteSensorId, state)
		for stateTuple in stateList:

			try:

				# check if the sensor does exist in the database
				self.cursor.execute("SELECT id FROM sensors "
					+ "WHERE nodeId = ? "
					+ "AND remoteSensorId = ?", (nodeId, stateTuple[0]))
				result = self.cursor.fetchall()
				if len(result) != 1:
					logging.error("[%s]: Sensor does not exist in database."
						% self.fileName)

					self._releaseLock()

					return False

				self.cursor.execute("UPDATE sensors SET "
					+ "state = ?, "
					+ "lastStateUpdated = ? "
					+ "WHERE nodeId = ? "
					+ "AND remoteSensorId = ?",
					(stateTuple[1], int(time.time()), nodeId, stateTuple[0]))
			except Exception as e:
				logging.exception("[%s]: Not able to update sensor state."
					% self.fileName)

				self._releaseLock()

				return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# gets the sensor id of a sensor when the id of a node is given
	# and the remote sensor id that is used by the node internally
	#
	# return sensorId or None
	def getSensorId(self, nodeId, remoteSensorId):

		self._acquireLock()

		try:
			sensorId = self._getSensorId(nodeId, remoteSensorId)
		except Exception as e:
			logging.exception("[%s]: Not able to get sensorId from database."
				% self.fileName)

			self._releaseLock()

			return None

		self._releaseLock()

		return sensorId


	# gets the alert id of a alert when the id of a node is given
	# and the remote alert id that is used by the node internally
	#
	# return alertId or None
	def getAlertId(self, nodeId, remoteAlertId):

		self._acquireLock()

		try:
			alertId = self._getAlertId(nodeId, remoteAlertId)
		except Exception as e:
			logging.exception("[%s]: Not able to get alertId from database."
				% self.fileName)

			self._releaseLock()

			return None

		self._releaseLock()

		return alertId		


	# gets all alert levels for a specific sensor given by sensorId
	#
	# return list of alertLevel
	# or None
	def getSensorAlertLevels(self, sensorId):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM sensorsAlertLevels "
				+ "WHERE sensorId = ?", (sensorId, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "alert levels for sensor with id %d." % sensorId)

			self._releaseLock()

			# return None if action failed
			return None

		self._releaseLock()

		# return list of alertLevel
		return map(lambda x: x[0], result)


	# gets all alert levels for a specific alert given by alertId
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAlertAlertLevels(self, alertId):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertsAlertLevels "
				+ "WHERE alertId = ?", (alertId, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "alert levels for alert with id %d." % alertId)

			self._releaseLock()

			# return None if action failed
			return None

		self._releaseLock()

		# return list of tuples of (alertLevel)
		return result


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, remoteSensorId, state, changeState,
		dataJson):

		self._acquireLock()

		try:

			# check if the sensor does exist in the database
			# and get its sensorId
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = ? "
				+ "AND remoteSensorId = ?", (nodeId, remoteSensorId))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logging.error("[%s]: Sensor does not exist in database."
					% self.fileName)

				self._releaseLock()

				return False
			sensorId = result[0][0]

			# update state of sensor in the database
			# (if state is affected by sensor alert)
			if changeState:
				self.cursor.execute("UPDATE sensors SET "
					+ "state = ?, "
					+ "lastStateUpdated = ? "
					+ "WHERE nodeId = ? "
					+ "AND remoteSensorId = ?",
					(state, int(time.time()), nodeId, remoteSensorId))
			# update only the last state update value
			else:
				self.cursor.execute("UPDATE sensors SET "
					+ "lastStateUpdated = ? "
					+ "WHERE nodeId = ? "
					+ "AND remoteSensorId = ?",
					(int(time.time()), nodeId, remoteSensorId))

			# add sensor alert to database
			if changeState:
				dbChangeState = 1
			else:
				dbChangeState = 0
			self.cursor.execute("INSERT INTO sensorAlerts ("
				+ "nodeId, "
				+ "sensorId, "
				+ "state, "
				+ "timeReceived, "
				+ "dataJson, "
				+ "changeState) VALUES (?, ?, ?, ?, ?, ?)",
				(nodeId, sensorId, state, int(time.time()), dataJson,
				dbChangeState))

		except Exception as e:
			logging.exception("[%s]: Not able to add sensor alert."
				% self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# gets all sensor alerts in the database
	#
	# return a list of tuples (sensorAlertId, sensorId, nodeId, timeReceived,
	# alertDelay, state, description, dataJson, changeState)
	# or None
	def getSensorAlerts(self):

		self._acquireLock()

		try:
			
			self.cursor.execute("SELECT sensorAlerts.id, "
				+ "sensors.id, "
				+ "sensors.nodeId, "
				+ "sensorAlerts.timeReceived, "
				+ "sensors.alertDelay, "
				+ "sensorAlerts.state, "
				+ "sensors.description, "
				+ "sensorAlerts.dataJson, "
				+ "sensorAlerts.changeState "
				+ "FROM sensorAlerts "
				+ "INNER JOIN sensors "
				+ "ON sensorAlerts.nodeId == sensors.nodeId "
				+ "AND sensorAlerts.sensorId == sensors.id")
			result = self.cursor.fetchall()

		except Exception as e:
			logging.exception("[%s]: Not able to get sensor alerts."
				% self.fileName)			

			self._releaseLock()

			return None

		self._releaseLock()

		# return a list of tuples (sensorAlertId, sensorId, nodeId,
		# timeReceived, alertDelay, state, description, dataJson, changeState)
		return result


	# deletes a sensor alert given by its sensor alert id
	#
	# return True or False
	def deleteSensorAlert(self, sensorAlertId):

		self._acquireLock()

		try:
			self.cursor.execute("DELETE FROM sensorAlerts WHERE id = ?",
					(sensorAlertId, ))
		except Exception as e:
			logging.exception("[%s]: Not able to delete sensor alert." 
				% self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# checks if the alert system is active or not
	#
	# return True or False
	def isAlertSystemActive(self):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT value FROM options WHERE type = ?",
				("alertSystemActive", ))
			result = self.cursor.fetchall()
			alertSystemActive = result[0][0]

		except Exception as e:
			logging.exception("[%s]: Not able to check " % self.fileName
				+ "if alert system is active.")

			self._releaseLock()

			return False

		self._releaseLock()

		if alertSystemActive == 1:
			return True
		elif alertSystemActive == 0:
			return False


	# gets all alert levels for the alert clients from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllAlertsAlertLevels(self):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertsAlertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels for alert clients.")

			self._releaseLock()

			# return None if action failed
			return None

		self._releaseLock()

		# return list of tuples of (alertLevel)
		return result


	# gets all alert levels for the sensors from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllSensorsAlertLevels(self):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM sensorsAlertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels for sensors.")

			self._releaseLock()

			# return None if action failed
			return None

		self._releaseLock()

		# return list of tuples of (alertLevel)
		return result


	# gets all nodes from the database that are connected to the server
	#
	# return list of nodeIds
	# or None
	def getAllConnectedNodeIds(self):

		self._acquireLock()

		# get all connected node ids from database
		try:
			self.cursor.execute("SELECT id "
				+ "FROM nodes "
				+ "WHERE connected = ?", (1, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all connected node ids.")

			self._releaseLock()

			# return None if action failed
			return None

		self._releaseLock()

		# return list of nodeIds
		return map(lambda x: x[0], result)


	# Gets all nodes from the database that are registered as persistent
	# to the server.
	#
	# return list of nodeIds
	# or None
	def getAllPersistentNodeIds(self):

		self._acquireLock()

		# get all persistent node ids from database
		try:
			self.cursor.execute("SELECT id "
				+ "FROM nodes "
				+ "WHERE persistent = ?", (1, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all persistent node ids.")

			self._releaseLock()

			# return None if action failed
			return None

		self._releaseLock()

		# return list of nodeIds
		return map(lambda x: x[0], result)


	# marks a node given by its id as NOT connected
	#
	# return True or False
	def markNodeAsNotConnected(self, nodeId):

		self._acquireLock()

		try:
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = ? WHERE id = ?", (0, nodeId))			
		except Exception as e:

			logging.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as not connected." % nodeId)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# marks a node given by its id as connected
	#
	# return True or False
	def markNodeAsConnected(self, nodeId):

		self._acquireLock()

		try:
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = ? WHERE id = ?", (1, nodeId))			
		except Exception as e:

			logging.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as connected." % nodeId)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# gets the information of all sensors which last state updates
	# are older than the given time
	#
	# return list of tuples of (sensorId, nodeId,
	# lastStateUpdated, description)
	# or None
	def getSensorsUpdatedOlderThan(self, oldestTimeUpdated):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT id, "
				+ "nodeId, "
				+ "lastStateUpdated, "
				+ "description "
				+ "FROM sensors "
				+ "WHERE lastStateUpdated < ?", (oldestTimeUpdated, ))

			result = self.cursor.fetchall()
		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "nodes from database which sensors were not updated.")

			self._releaseLock()

			return None

		self._releaseLock()

		# return list of tuples of (sensorId, nodeId,
		# lastStateUpdated, description)
		return result


	# gets all information of a sensor by its given id
	#
	# return a tuple of (sensorId, nodeId,
	# remoteSensorId, description, state, lastStateUpdated, alertDelay)
	# or None
	def getSensorInformation(self, sensorId):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT id, "
				+ "nodeId, "
				+ "remoteSensorId, "
				+ "description, "
				+ "state, "
				+ "lastStateUpdated, "
				+ "alertDelay "
				+ "FROM sensors "
				+ "WHERE id = ?", (sensorId, ))

			result = self.cursor.fetchall()
		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "sensor information from sensor id.")

			self._releaseLock()

			return None

		# check if it is the only result
		if len(result) != 1:

			logging.error("[%s]: Sensor id is not unique in " % self.fileName
				+ "database.")

			self._releaseLock()

			return None

		self._releaseLock()

		# return a tuple of (sensorId, nodeId,
		# remoteSensorId, description, state, lastStateUpdated, alertDelay)
		return result[0]


	# gets the node from the database when its id is given
	#
	# return a tuple of (nodeId, hostname, username, nodeType, instance,
	# connected, version, rev, persistent) or None
	def getNodeById(self, nodeId):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT * FROM nodes "
				+ "WHERE id = ?", (nodeId, ))

			result = self.cursor.fetchall()
		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "node with id %d from database." % nodeId)

			self._releaseLock()

			return None

		self._releaseLock()

		# return a tuple of (nodeId, hostname, username, nodeType, instance,
		# connected, version, rev, persistent) or None
		return result[0]


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = list(tuples of (type, value))
	# list[1] = list(tuples of (nodeId, hostname, username, nodeType,
	# instance, connected, version, rev, persistent))
	# list[2] = list(tuples of (sensorId, nodeId, remoteSensorId,
	# description, state, lastStateUpdated, alertDelay))
	# list[3] = list(tuples of (managerId, nodeId, description))
	# list[4] = list(tuples of (alertId, nodeId, remoteAlertId,
	# description))
	# or None
	def getAlertSystemInformation(self):

		self._acquireLock()

		try:

			# get all options information
			self.cursor.execute("SELECT type, "
				+ "value "
				+ "FROM options")
			result = self.cursor.fetchall()
			optionsInformation = result

			# get all nodes information
			self.cursor.execute("SELECT * FROM nodes")
			result = self.cursor.fetchall()
			nodesInformation = result

			# get all sensors information
			self.cursor.execute("SELECT * FROM sensors")
			result = self.cursor.fetchall()
			sensorsInformation = result

			# get all managers information
			self.cursor.execute("SELECT * FROM managers")
			result = self.cursor.fetchall()
			managersInformation = result		

			# get all alerts information
			self.cursor.execute("SELECT * FROM alerts")
			result = self.cursor.fetchall()
			alertsInformation = result

			# generate a list with all nodes information
			alertSystemInformation = list()
			alertSystemInformation.append(optionsInformation)
			alertSystemInformation.append(nodesInformation)
			alertSystemInformation.append(sensorsInformation)
			alertSystemInformation.append(managersInformation)
			alertSystemInformation.append(alertsInformation)

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all nodes information from database.")

			self._releaseLock()

			return None

		self._releaseLock()

		# return a list of
		# list[0] = list(tuples of (type, value))
		# list[1] = list(tuples of (nodeId, hostname, username, nodeType,
		# instance, connected, version, rev, persistent))
		# list[2] = list(tuples of (sensorId, nodeId, remoteSensorId,
		# description, state, lastStateUpdated, alertDelay))
		# list[3] = list(tuples of (managerId, nodeId, description))
		# list[4] = list(tuples of (alertId, nodeId, remoteAlertId,
		# description))
		# or None
		return alertSystemInformation


	# change a option in the database
	#
	# return True or False
	def changeOption(self, optionType, optionValue):

		self._acquireLock()

		try:
			# check if option does exist
			self.cursor.execute("SELECT id "
				+ "FROM options "
				+ "WHERE type = ?", (optionType, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logging.error("[%s]: Option was not found." % self.fileName)
				self._releaseLock()

				return False

			# update option in database
			self.cursor.execute("UPDATE options SET "
				+ "value = ? "
				+ "WHERE type = ?", (optionValue, optionType))

		except Exception as e:

			logging.exception("[%s]: Not able to update " % self.fileName
				+ "option in database.")

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# gets the state of a sensor given by id
	#
	# return sensor state or None
	def getSensorState(self, sensorId):

		self._acquireLock()

		try:
			# get sensor state from database
			self.cursor.execute("SELECT state "
				+ "FROM sensors "
				+ "WHERE id = ?", (sensorId, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logging.error("[%s]: Sensor was not found." % self.fileName)

				self._releaseLock()

				return None

			state = result[0][0]

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "sensor state from database.")

			self._releaseLock()

			return None

		self._releaseLock()

		return state


	# closes db for usage
	#
	# no return value
	def close(self):

		self._acquireLock()

		self.cursor.close()
		self.conn.close()

		self._releaseLock()


# class for using mysql as storage backend
class Mysql(_Storage):

	def __init__(self, host, port, database, username, password, globalData):

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		self.globalData = globalData

		# version of server
		self.version = self.globalData.version
		self.rev = self.globalData.rev

		# unique id of this server (is also the username of this server)
		# (used for caching)
		self.uniqueID = None

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

		# check if alert system tables exist already
		# if not => create them
		self.cursor.execute("SHOW TABLES LIKE 'internals'")
		internalsResult = self.cursor.fetchall()		
		self.cursor.execute("SHOW TABLES LIKE 'options'")
		optionsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'nodes'")
		nodesResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'sensors'")
		sensorsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'sensorsAlertLevels'")
		sensorsAlertLevelsResult = self.cursor.fetchall()		
		self.cursor.execute("SHOW TABLES LIKE 'sensorAlerts'")
		sensorAlertsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'alerts'")
		alertsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'alertsAlertLevels'")
		alertsAlertLevelsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'managers'")
		managersResult = self.cursor.fetchall()

		# close connection to the database
		self._closeConnection()

		# if one table does not exist
		# => create all tables
		if (len(internalsResult) == 0
			or len(optionsResult) == 0
			or len(nodesResult) == 0
			or len(sensorsResult) == 0
			or len(sensorsAlertLevelsResult) == 0
			or len(sensorAlertsResult) == 0
			or len(alertsResult) == 0
			or len(alertsAlertLevelsResult) == 0
			or len(managersResult) == 0):
			self.createStorage()

		# check if the versions are compatible
		else:
			self.checkVersionAndClearConflict()


	# internal function that connects to the mysql server
	# (needed because direct changes to the database by another program
	# are not seen if the connection to the mysql server is kept alive)
	def _openConnection(self):
		# import the needed package
		import MySQLdb

		self.conn = MySQLdb.connect(host=self.host, port=self.port,
			user=self.username,	passwd=self.password, db=self.database)

		self.cursor = self.conn.cursor()


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
		uniqueString = socket.gethostname() \
			+ struct.pack("d", time.time()) \
			+ os.urandom(200)
		sha256 = hashlib.sha256()
		sha256.update(uniqueString)
		uniqueID = sha256.hexdigest()

		return uniqueID


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
	def _getUniqueID(self):

		# if unique id already cached => return it
		if not self.uniqueID is None:
			return self.uniqueID

		try:
			self.cursor.execute("SELECT value "
				+ "FROM internals WHERE type=%s", ("uniqueID", ))
			self.uniqueID = self.cursor.fetchall()[0][0]
		except Exception as e:
			logging.exception("[%s]: Not able to get the unique id." 
				% self.fileName)

		return self.uniqueID


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.dbLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
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
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create node entry for this server (use unique id as username)
		self.cursor.execute("INSERT INTO nodes ("
			+ "hostname, "
			+ "username, "
			+ "nodeType, "
			+ "instance, "
			+ "connected, "
			+ "version, "
			+ "rev, "
			+ "persistent) "
			+ "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
			(socket.gethostname(), uniqueID, "server", "server", 1,
			self.version, self.rev, 1))

		# create sensorsAlertLevels table
		self.cursor.execute("CREATE TABLE sensorsAlertLevels ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "sensorId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
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
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id), "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create alerts table
		self.cursor.execute("CREATE TABLE alerts ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteAlertId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create alertsAlertLevels table
		self.cursor.execute("CREATE TABLE alertsAlertLevels ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "alertId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "FOREIGN KEY(alertId) REFERENCES alerts(id))")

		# create managers table
		self.cursor.execute("CREATE TABLE managers ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")		

		# commit all changes
		self.conn.commit()


	# checks the version of the server and the version in the database
	# and clears every compatibility issue
	#
	# no return value but raise exception if it fails
	def checkVersionAndClearConflict(self):

		self._acquireLock()

		# connect to the database
		self._openConnection()

		# get version from the current database
		self.cursor.execute("SELECT value FROM internals "
			+ "WHERE type = %s",
			("version", ))
		result = self.cursor.fetchall()

		# if the versions are not compatible
		# => delete old database schema
		if float(result[0][0]) != self.version:

			logging.info("[%s]: Server version "
				% self.fileName
				+ "'%.3f' not compatible "
				% self.version
				+ "with database version '%.3f'. "
				% float(result[0][0])
				+ "Updating database.")

			# get old uniqueId to keep it
			uniqueID = self._getUniqueID()
			if uniqueID is None:
				uniqueID = self._generateUniqueId()

			# delete all tables from the database to clear the old version
			self.cursor.execute("DROP TABLE IF EXISTS internals")
			self.cursor.execute("DROP TABLE IF EXISTS options")
			self.cursor.execute("DROP TABLE IF EXISTS sensorAlerts")
			self.cursor.execute("DROP TABLE IF EXISTS sensorsAlertLevels")
			self.cursor.execute("DROP TABLE IF EXISTS sensors")
			self.cursor.execute("DROP TABLE IF EXISTS alertsAlertLevels")
			self.cursor.execute("DROP TABLE IF EXISTS alerts")
			self.cursor.execute("DROP TABLE IF EXISTS managers")
			self.cursor.execute("DROP TABLE IF EXISTS nodes")

			# create new database
			self._createStorage(uniqueID)

			# commit all changes
			self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()


	# creates the database (should only be called if the database
	# does not exist)
	#
	# no return value but raise exception if it fails
	def createStorage(self):

		self._acquireLock()

		# connect to the database
		self._openConnection()

		uniqueID = self._generateUniqueId()

		self._createStorage(uniqueID)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()


	# adds a node if it does not exist or changes the registered
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType, instance, version, rev,
		persistent):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		# check if a node with the same username already exists
		# => if not add node
		if not self._usernameInDb(username):

			logging.info("[%s]: Node with username '%s' does not exist "
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
				logging.exception("[%s]: Not able to add node."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

		# if a node with this username exists
		# => check if everything is the same
		else:

			logging.info("[%s]: Node with username '%s' already exists "
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
				logging.exception("[%s]: Not able to get node information."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

			# change hostname if it had changed
			if dbHostname != hostname:

				logging.info("[%s]: Hostname of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbHostname, hostname))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "hostname = %s "
						+ "WHERE id = %s",
						(hostname, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update hostname of node.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

			# change instance if it had changed
			if dbInstance != instance:

				logging.info("[%s]: Instance of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbInstance, instance))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "instance = %s "
						+ "WHERE id = %s",
						(instance, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update instance of node.")

					self._releaseLock()

					return False

			# change version if it had changed
			if dbVersion != version:

				logging.info("[%s]: Version of node has changed "
					% self.fileName
					+ "from '%.3f' to '%.3f'. Updating database."
					% (dbVersion, version))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "version = %s "
						+ "WHERE id = %s",
						(version, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update version of node.")

					self._releaseLock()

					return False

			# change revision if it had changed
			if dbRev != rev:

				logging.info("[%s]: Revision of node has changed "
					% self.fileName
					+ "from '%d' to '%d'. Updating database."
					% (dbRev, rev))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "rev = %s "
						+ "WHERE id = %s",
						(rev, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update revision of node.")

					self._releaseLock()

					return False

			# change persistent if it had changed
			if dbPersistent != persistent:

				logging.info("[%s]: Persistent flag of node has changed "
					% self.fileName
					+ "from '%d' to '%d'. Updating database."
					% (dbPersistent, persistent))

				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "persistent = %s "
						+ "WHERE id = %s",
						(persistent, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update persistent flag of node.")

					self._releaseLock()

					return False

			# if node type has changed
			# => delete sensors/alerts/manager information of old node
			# and change node type
			if dbNodeType != nodeType:

				logging.info("[%s]: Type of node has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbNodeType, nodeType))

				# if old node had type "sensor"
				# => delete all sensors
				if dbNodeType == "sensor":

					try:
						# get all sensor ids that are connected to
						# the old sensor
						self.cursor.execute("SELECT id FROM sensors "
							+ "WHERE nodeId = %s ", (nodeId, ))
						result = self.cursor.fetchall()

						# delete all sensor alert levels and sensors of
						# this node
						for sensorIdResult in result:

							self.cursor.execute("DELETE FROM "
								+ "sensorsAlertLevels "
								+ "WHERE sensorId = %s",
								(sensorIdResult[0], ))

							self.cursor.execute("DELETE FROM sensors "
								+ "WHERE id = %s",
								(sensorIdResult[0], ))

					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "delete sensors of the node.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock()

						return False

				# if old node had type "alert"
				# => delete all alerts
				elif dbNodeType == "alert":

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

					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "delete alerts of the node.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock()

						return False

				# if old node had type "manager"
				# => delete all manager information
				elif dbNodeType == "manager":
					
					try:
						self.cursor.execute("DELETE FROM managers "
							+ "WHERE nodeId = %s",
							(nodeId, ))

					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "delete manager information of the node.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock()

						return False

				# node type in database not known
				else:

					logging.error("[%s]: Unknown node type " % self.fileName
						+ "when deleting old sensors/alerts/manager "
						+ "information.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# update node type
				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "nodeType = %s "
						+ "WHERE id = %s",
						(nodeType, nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update type of node.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds/updates the data that is given by the node for the sensors
	# to the database
	#
	# return True or False
	def addSensors(self, username, sensors):

		self._acquireLock()	

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to get node id." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# add/update all sensors
		for sensor in sensors:

			# check if a sensor with the same remote id for this node
			# already exists in the database
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = %s AND remoteSensorId = %s",
				(nodeId, int(sensor["clientSensorId"])))
			result = self.cursor.fetchall()

			# if the sensor does not exist
			# => add it
			if len(result) == 0:

				logging.info("[%s]: Sensor with client id '%d' does not exist "
					% (self.fileName, int(sensor["clientSensorId"]))
					+ "in database. Adding it.")

				# add sensor to database
				try:
					self.cursor.execute("INSERT INTO sensors ("
						+ "nodeId, "
						+ "remoteSensorId, "
						+ "description, "
						+ "state, "
						+ "lastStateUpdated, "
						+ "alertDelay) VALUES (%s, %s, %s, %s, %s, %s)",
						(nodeId, int(sensor["clientSensorId"]),
						str(sensor["description"]), 0, 0,
						int(sensor["alertDelay"])))
				except Exception as e:
					logging.exception("[%s]: Not able to add sensor."
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# get sensorId of current added sensor
				try:
					sensorId = self._getSensorId(nodeId,
						int(sensor["clientSensorId"]))
				except Exception as e:
					logging.exception("[%s]: Not able to get sensorId." 
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# add sensor alert levels to database
				try:
					for alertLevel in sensor["alertLevels"]:			
						self.cursor.execute("INSERT INTO sensorsAlertLevels ("
							+ "sensorId, "
							+ "alertLevel) VALUES (%s, %s)",
							(sensorId, alertLevel))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "add sensor alert levels.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

			# if the sensor does already exist
			# => check if everything is the same
			else:

				logging.info("[%s]: Sensor with client id '%d' already exists "
					% (self.fileName, int(sensor["clientSensorId"]))
					+ "in database.")

				# get sensorId, description and alertDelay
				try:
					sensorId = self._getSensorId(nodeId,
						int(sensor["clientSensorId"]))

					self.cursor.execute("SELECT description, "
						+ "alertDelay "
						+ "FROM sensors "
						+ "WHERE id = %s",
						(sensorId, ))
					result = self.cursor.fetchall()
					dbDescription = result[0][0]
					dbAlertDelay = result[0][1]

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get sensor information.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# change description if it had changed
				if dbDescription != str(sensor["description"]):

					logging.info("[%s]: Description of sensor has changed "
						% self.fileName
						+ "from '%s' to '%s'. Updating database."
						% (dbDescription, str(sensor["description"])))

					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "description = %s "
							+ "WHERE id = %s",
							(str(sensor["description"]), sensorId))
					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "update description of sensor.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock()

						return False

				# change alert delay if it had changed
				if dbAlertDelay != int(sensor["alertDelay"]):

					logging.info("[%s]: Alert delay of sensor has changed "
						% self.fileName
						+ "from '%d' to '%d'. Updating database."
						% (dbAlertDelay, int(sensor["alertDelay"])))

					try:
						self.cursor.execute("UPDATE sensors SET "
							+ "alertDelay = %s "
							+ "WHERE id = %s",
							(int(sensor["alertDelay"]), sensorId))
					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "update alert delay of sensor.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock()

						return False

				# get sensor alert levels from database
				try:
					
					self.cursor.execute("SELECT id, "
						+ "alertLevel "
						+ "FROM sensorsAlertLevels "
						+ "WHERE sensorId = %s ", (sensorId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get alert levels of the sensor.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# check if the alert levels do already
				# exist in the database
				# => add alert level if it does not
				for alertLevel in sensor["alertLevels"]:

					# check if alert level already exists
					found = False
					for dbAlertLevel in result:
						if dbAlertLevel[1] == alertLevel:
							found = True
							break
					if found:
						continue

					logging.info("[%s]: Alert level '%d' of sensor does not "
						% (self.fileName, alertLevel)
						+ "exist in database. Adding it.")

					# add sensor alert level to database
					self.cursor.execute("INSERT INTO sensorsAlertLevels ("
						+ "sensorId, "
						+ "alertLevel) VALUES (%s, %s)",
						(sensorId, alertLevel))

				# get updated sensor alert levels from database
				try:
					
					self.cursor.execute("SELECT id, "
						+ "alertLevel "
						+ "FROM sensorsAlertLevels "
						+ "WHERE sensorId = %s ", (sensorId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get updated alert levels of the sensor.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# check if the alert levels from the database
				# do still exist in the sensor
				# => delete alert level if it does not
				for dbAlertLevel in result:

					# check if database alert level does exist
					found = False
					for alertLevel in sensor["alertLevels"]:
						if dbAlertLevel[1] == alertLevel:
							found = True
							break
					if found:
						continue

					logging.info("[%s]: Alert level '%d' in database does "
						% (self.fileName, dbAlertLevel[1])
						+ "not exist anymore for sensor. Deleting it.")

					self.cursor.execute("DELETE FROM sensorsAlertLevels "
						+ "WHERE id = %s",
						(dbAlertLevel[0], ))

		# get updated sensors from database
		try:
					
			self.cursor.execute("SELECT id, "
				+ "remoteSensorId "
				+ "FROM sensors "
				+ "WHERE nodeId = %s ", (nodeId, ))
			result = self.cursor.fetchall()

		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "get updated sensors from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

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

			logging.info("[%s]: Sensor with client id '%d' in database does "
				% (self.fileName, dbSensor[1])
				+ "not exist anymore for the node. Deleting it.")

			try:
				self.cursor.execute("DELETE FROM sensorsAlertLevels "
					+ "WHERE sensorId = %s",
					(dbSensor[0], ))

				self.cursor.execute("DELETE FROM sensors "
					+ "WHERE id = %s",
					(dbSensor[0], ))
			except Exception as e:
				logging.exception("[%s]: Not able to delete sensor." 
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds/updates the data that is given by the node for the alerts
	# to the database
	#
	# return True or False
	def addAlerts(self, username, alerts):

		self._acquireLock()	

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to get node id." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# add/update all alerts
		for alert in alerts:

			# check if a alert with the same remote id for this node
			# already exists in the database
			self.cursor.execute("SELECT id FROM alerts "
				+ "WHERE nodeId = %s AND remoteAlertId = %s",
				(nodeId, int(alert["clientAlertId"])))
			result = self.cursor.fetchall()

			# if the alert does not exist
			# => add it
			if len(result) == 0:

				logging.info("[%s]: Alert with client id '%d' does not exist "
					% (self.fileName, int(alert["clientAlertId"]))
					+ "in database. Adding it.")

				# add alert to database
				try:
					self.cursor.execute("INSERT INTO alerts ("
						+ "nodeId, "
						+ "remoteAlertId, "
						+ "description) VALUES (%s, %s, %s)", (nodeId,
						int(alert["clientAlertId"]),
						str(alert["description"])))
				except Exception as e:
					logging.exception("[%s]: Not able to add alert."
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# get alertId of current added alert
				try:
					alertId = self._getAlertId(nodeId,
						int(alert["clientAlertId"]))
				except Exception as e:
					logging.exception("[%s]: Not able to get alertId." 
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# add alert alert levels to database
				try:
					for alertLevel in alert["alertLevels"]:			
						self.cursor.execute("INSERT INTO alertsAlertLevels ("
							+ "alertId, "
							+ "alertLevel) VALUES (%s, %s)",
							(alertId, alertLevel))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "add alert alert levels.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

			# if the alert does already exist
			# => check if everything is the same
			else:

				logging.info("[%s]: Alert with client id '%d' already exists "
					% (self.fileName, int(alert["clientAlertId"]))
					+ "in database.")

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
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get alert information.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# change description if it had changed
				if dbDescription != str(alert["description"]):

					logging.info("[%s]: Description of alert has changed "
						% self.fileName
						+ "from '%s' to '%s'. Updating database."
						% (dbDescription, str(alert["description"])))

					try:
						self.cursor.execute("UPDATE alerts SET "
							+ "description = %s "
							+ "WHERE id = %s",
							(str(alert["description"]), alertId))
					except Exception as e:
						logging.exception("[%s]: Not able to " % self.fileName
							+ "update description of alert.")

						# close connection to the database
						self._closeConnection()

						self._releaseLock()

						return False

				# get alert alert levels from database
				try:
					
					self.cursor.execute("SELECT id, "
						+ "alertLevel "
						+ "FROM alertsAlertLevels "
						+ "WHERE alertId = %s ", (alertId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get alert levels of the alert.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# check if the alert levels do already
				# exist in the database
				# => add alert level if it does not
				for alertLevel in alert["alertLevels"]:

					# check if alert level already exists
					found = False
					for dbAlertLevel in result:
						if dbAlertLevel[1] == alertLevel:
							found = True
							break
					if found:
						continue

					logging.info("[%s]: Alert level '%d' of alert does not "
						% (self.fileName, alertLevel)
						+ "exist in database. Adding it.")

					# add alert alert level to database
					self.cursor.execute("INSERT INTO alertsAlertLevels ("
						+ "alertId, "
						+ "alertLevel) VALUES (%s, %s)",
						(alertId, alertLevel))

				# get updated alert alert levels from database
				try:
					
					self.cursor.execute("SELECT id, "
						+ "alertLevel "
						+ "FROM alertsAlertLevels "
						+ "WHERE alertId = %s ", (alertId, ))
					result = self.cursor.fetchall()

				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "get updated alert levels of the alert.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				# check if the alert levels from the database
				# do still exist in the alert
				# => delete alert level if it does not
				for dbAlertLevel in result:

					# check if database alert level does exist
					found = False
					for alertLevel in alert["alertLevels"]:
						if dbAlertLevel[1] == alertLevel:
							found = True
							break
					if found:
						continue

					logging.info("[%s]: Alert level '%d' in database does "
						% (self.fileName, dbAlertLevel[1])
						+ "not exist anymore for alert. Deleting it.")

					self.cursor.execute("DELETE FROM alertsAlertLevels "
						+ "WHERE id = %s",
						(dbAlertLevel[0], ))

		# get updated alerts from database
		try:
					
			self.cursor.execute("SELECT id, "
				+ "remoteAlertId "
				+ "FROM alerts "
				+ "WHERE nodeId = %s ", (nodeId, ))
			result = self.cursor.fetchall()

		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "get updated alerts from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

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

			logging.info("[%s]: Alert with client id '%d' in database does "
				% (self.fileName, dbAlert[1])
				+ "not exist anymore for the node. Deleting it.")

			try:
				self.cursor.execute("DELETE FROM alertsAlertLevels "
					+ "WHERE alertId = %s",
					(dbAlert[0], ))

				self.cursor.execute("DELETE FROM alerts "
					+ "WHERE id = %s",
					(dbAlert[0], ))
			except Exception as e:
				logging.exception("[%s]: Not able to delete alert." 
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds/updates the data that is given by the node for
	# the manager to the database
	#
	# return True or False
	def addManager(self, username, manager):

		self._acquireLock()	

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to get node id." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

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

			logging.info("[%s]: Manager does not exist "
				% self.fileName
				+ "in database. Adding it.")

			# add manager to database
			try:
				self.cursor.execute("INSERT INTO managers ("
					+ "nodeId, "
					+ "description) VALUES (%s, %s)", (nodeId,
					str(manager["description"])))
			except Exception as e:
				logging.exception("[%s]: Not able to add manager."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

		# if the manager does already exist
		# => check if everything is the same
		else:

			logging.info("[%s]: Manager already exists "
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
				logging.exception("[%s]: Not able to " % self.fileName
					+ "get manager information.")

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

			# change description if it had changed
			if dbDescription != str(manager["description"]):

				logging.info("[%s]: Description of manager has changed "
					% self.fileName
					+ "from '%s' to '%s'. Updating database."
					% (dbDescription, str(manager["description"])))

				try:
					self.cursor.execute("UPDATE managers SET "
						+ "description = %s "
						+ "WHERE id = %s",
						(str(manager["description"]), managerId))
				except Exception as e:
					logging.exception("[%s]: Not able to " % self.fileName
						+ "update description of manager.")

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# gets the id of the node by a given username
	# (usernames are unique to each node)
	#
	# return nodeId or None
	def getNodeId(self, username):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		nodeId = None
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to get node id." 
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return nodeId


	# gets the count of the sensors of a node in the database
	# return count of sensors in database
	def getSensorCount(self, nodeId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		# get all sensors on this node
		sensorCount = None
		try:
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = %s ", (nodeId, ))

			result = self.cursor.fetchall()
			sensorCount = len(result)
		except Exception as e:
			logging.exception("[%s]: Not able to get sensor count." 
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return sensorCount


	# gets all data needed for the survey
	#
	# return list of tuples of (instance, version, rev)
	# or None
	def getSurveyData(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

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
			logging.exception("[%s]: Not able to get survey data." 
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return list(surveyData)


	# gets the unique id from the database
	#
	# return unique id
	# or None
	def getUniqueID(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		uniqueID = self._getUniqueID()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return uniqueID



	# updates the states of the sensors of a node in the databse
	# (given in a tuple of (remoteSensorId, state))
	#
	# return True or False
	def updateSensorState(self, nodeId, stateList):
		
		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

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
					logging.error("[%s]: Sensor does not exist in database."
						% self.fileName)

					# close connection to the database
					self._closeConnection()

					self._releaseLock()

					return False

				self.cursor.execute("UPDATE sensors SET "
					+ "state = %s, "
					+ "lastStateUpdated = %s "
					+ "WHERE nodeId = %s "
					+ "AND remoteSensorId = %s",
					(stateTuple[1], int(time.time()), nodeId, stateTuple[0]))
			except Exception as e:
				logging.exception("[%s]: Not able to update sensor state."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# gets the sensor id of a sensor when the id of a node is given
	# and the remote sensor id that is used by the node internally
	#
	# return sensorId or None
	def getSensorId(self, nodeId, remoteSensorId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:
			sensorId = self._getSensorId(nodeId, remoteSensorId)
		except Exception as e:
			logging.exception("[%s]: Not able to get sensorId from database."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return sensorId


	# gets the alert id of a alert when the id of a node is given
	# and the remote alert id that is used by the node internally
	#
	# return alertId or None
	def getAlertId(self, nodeId, remoteAlertId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:
			alertId = self._getAlertId(nodeId, remoteAlertId)
		except Exception as e:
			logging.exception("[%s]: Not able to get alertId from database."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return alertId


	# gets all alert levels for a specific sensor given by sensorId
	#
	# return list of alertLevel
	# or None
	def getSensorAlertLevels(self, sensorId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM sensorsAlertLevels "
				+ "WHERE sensorId = %s", (sensorId, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "alert levels for sensor with id %d." % sensorId)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of alertLevel
		return map(lambda x: x[0], result)


	# gets all alert levels for a specific alert given by alertId
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAlertAlertLevels(self, alertId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertsAlertLevels "
				+ "WHERE alertId = %s", (alertId, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "alert levels for alert with id %d." % alertId)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (alertLevel)
		return list(result)


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, remoteSensorId, state, changeState,
		dataJson):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		try:

			# check if the sensor does exist in the database
			# and get its sensorId
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = %s "
				+ "AND remoteSensorId = %s", (nodeId, remoteSensorId))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logging.error("[%s]: Sensor does not exist in database."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False
			sensorId = result[0][0]

			# update state of sensor in the database
			# (if state is affected by sensor alert)
			if changeState:			
				self.cursor.execute("UPDATE sensors SET "
					+ "state = %s, "
					+ "lastStateUpdated = %s "
					+ "WHERE nodeId = %s "
					+ "AND remoteSensorId = %s",
					(state, int(time.time()), nodeId, remoteSensorId))
			# update only the last state update value
			else:
				self.cursor.execute("UPDATE sensors SET "
					+ "lastStateUpdated = %s "
					+ "WHERE nodeId = %s "
					+ "AND remoteSensorId = %s",
					(int(time.time()), nodeId, remoteSensorId))

			# add sensor alert to database
			if changeState:
				dbChangeState = 1
			else:
				dbChangeState = 0
			self.cursor.execute("INSERT INTO sensorAlerts ("
				+ "nodeId, "
				+ "sensorId, "
				+ "state, "
				+ "timeReceived, "
				+ "dataJson, "
				+ "changeState) VALUES (%s, %s, %s, %s, %s, %s)",
				(nodeId, sensorId, state, int(time.time()), dataJson,
				dbChangeState))

		except Exception as e:
			logging.exception("[%s]: Not able to add sensor alert."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# gets all sensor alerts in the database
	#
	# return a list of tuples (sensorAlertId, sensorId, nodeId, timeReceived,
	# alertDelay, state, description, dataJson, changeState)
	# or None
	def getSensorAlerts(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:
			
			self.cursor.execute("SELECT sensorAlerts.id, "
				+ "sensors.id, "
				+ "sensors.nodeId, "
				+ "sensorAlerts.timeReceived, "
				+ "sensors.alertDelay, "
				+ "sensorAlerts.state, "
				+ "sensors.description, "
				+ "sensorAlerts.dataJson, "
				+ "sensorAlerts.changeState "
				+ "FROM sensorAlerts "
				+ "INNER JOIN sensors "
				+ "ON sensorAlerts.nodeId = sensors.nodeId "
				+ "AND sensorAlerts.sensorId = sensors.id")
			result = self.cursor.fetchall()

		except Exception as e:
			logging.exception("[%s]: Not able to get sensor alerts."
				% self.fileName)			

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a list of tuples (sensorAlertId, sensorId, nodeId,
		# timeReceived, alertDelay, state, description, dataJson, changeState)
		return result


	# deletes a sensor alert given by its sensor alert id
	#
	# return True or False
	def deleteSensorAlert(self, sensorAlertId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		try:
			self.cursor.execute("DELETE FROM sensorAlerts WHERE id = %s",
					(sensorAlertId, ))
		except Exception as e:
			logging.exception("[%s]: Not able to delete sensor alert." 
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# checks if the alert system is active or not
	#
	# return True or False
	def isAlertSystemActive(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		try:
			self.cursor.execute("SELECT value FROM options WHERE type = %s",
				("alertSystemActive", ))
			result = self.cursor.fetchall()
			alertSystemActive = result[0][0]

		except Exception as e:
			logging.exception("[%s]: Not able to check " % self.fileName
				+ "if alert system is active.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		if alertSystemActive == 1:
			return True
		elif alertSystemActive == 0:
			return False


	# gets all alert levels for the alert clients from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllAlertsAlertLevels(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertsAlertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels for alert clients.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (alertLevel)
		return list(result)


	# gets all alert levels for the sensors from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllSensorsAlertLevels(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM sensorsAlertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels for sensors.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (alertLevel)
		return list(result)


	# gets all nodes from the database that are connected to the server
	#
	# return list of nodeIds
	# or None
	def getAllConnectedNodeIds(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		# get all connected node ids from database
		try:
			self.cursor.execute("SELECT id "
				+ "FROM nodes "
				+ "WHERE connected = %s", (1, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all connected node ids.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of nodeIds
		return map(lambda x: x[0], result)


	# Gets all nodes from the database that are registered as persistent
	# to the server.
	#
	# return list of nodeIds
	# or None
	def getAllPersistentNodeIds(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		# get all persistent node ids from database
		try:
			self.cursor.execute("SELECT id "
				+ "FROM nodes "
				+ "WHERE persistent = %s", (1, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all persistent node ids.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of nodeIds
		return map(lambda x: x[0], result)


	# marks a node given by its id as NOT connected
	#
	# return True or False
	def markNodeAsNotConnected(self, nodeId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		try:
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = %s WHERE id = %s", (0, nodeId))			
		except Exception as e:

			logging.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as not connected." % nodeId)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# marks a node given by its id as connected
	#
	# return True or False
	def markNodeAsConnected(self, nodeId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		try:
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = %s WHERE id = %s", (1, nodeId))			
		except Exception as e:

			logging.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as connected." % nodeId)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# gets the information of all sensors which last state updates
	# are older than the given time
	#
	# return list of tuples of (sensorId, nodeId,
	# lastStateUpdated, description)
	# or None
	def getSensorsUpdatedOlderThan(self, oldestTimeUpdated):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:
			self.cursor.execute("SELECT id, "
				+ "nodeId, "
				+ "lastStateUpdated, "
				+ "description "
				+ "FROM sensors "
				+ "WHERE lastStateUpdated < %s", (oldestTimeUpdated, ))

			result = self.cursor.fetchall()
		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "nodes from database which sensors were not updated.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (sensorId, nodeId,
		# lastStateUpdated, description)
		return list(result)


	# gets all information of a sensor by its given id
	#
	# return a tuple of (sensorId, nodeId,
	# remoteSensorId, description, state, lastStateUpdated, alertDelay)
	# or None
	def getSensorInformation(self, sensorId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:
			self.cursor.execute("SELECT id, "
				+ "nodeId, "
				+ "remoteSensorId, "
				+ "description, "
				+ "state, "
				+ "lastStateUpdated, "
				+ "alertDelay "
				+ "FROM sensors "
				+ "WHERE id = %s", (sensorId, ))

			result = self.cursor.fetchall()
		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "sensor information from sensor id.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# check if it is the only result
		if len(result) != 1:

			logging.error("[%s]: Sensor id is not unique in " % self.fileName
				+ "database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a tuple of (sensorId, nodeId,
		# remoteSensorId, description, state, lastStateUpdated, alertDelay)
		return result[0]


	# gets the node from the database when its id is given
	#
	# return a tuple of (nodeId, hostname, username, nodeType, instance,
	# connected, version, rev, persistent) or None
	def getNodeById(self, nodeId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:
			self.cursor.execute("SELECT * FROM nodes "
				+ "WHERE id = %s", (nodeId, ))

			result = self.cursor.fetchall()
		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "node with id %d from database." % nodeId)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a tuple of (nodeId, hostname, username, nodeType, instance,
		# connected, version, rev, persistent) or None
		return result[0]


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = list(tuples of (type, value))
	# list[1] = list(tuples of (nodeId, hostname, username, nodeType,
	# instance, connected, version, rev, persistent))
	# list[2] = list(tuples of (sensorId, nodeId, remoteSensorId,
	# description, state, lastStateUpdated, alertDelay))
	# list[3] = list(tuples of (managerId, nodeId, description))
	# list[4] = list(tuples of (alertId, nodeId, remoteAlertId,
	# description))
	# or None
	def getAlertSystemInformation(self):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:

			# get all options information
			self.cursor.execute("SELECT type, "
				+ "value "
				+ "FROM options")
			result = self.cursor.fetchall()
			optionsInformation = result

			# get all nodes information
			self.cursor.execute("SELECT * FROM nodes")
			result = self.cursor.fetchall()
			nodesInformation = result

			# get all sensors information
			self.cursor.execute("SELECT * FROM sensors")
			result = self.cursor.fetchall()
			sensorsInformation = result

			# get all managers information
			self.cursor.execute("SELECT * FROM managers")
			result = self.cursor.fetchall()
			managersInformation = result		

			# get all alerts information
			self.cursor.execute("SELECT * FROM alerts")
			result = self.cursor.fetchall()
			alertsInformation = result

			# generate a list with all nodes information
			alertSystemInformation = list()
			alertSystemInformation.append(optionsInformation)
			alertSystemInformation.append(nodesInformation)
			alertSystemInformation.append(sensorsInformation)
			alertSystemInformation.append(managersInformation)
			alertSystemInformation.append(alertsInformation)

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all nodes information from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a list of
		# list[0] = list(tuples of (type, value))
		# list[1] = list(tuples of (nodeId, hostname, username, nodeType,
		# instance, connected, version, rev, persistent))
		# list[2] = list(tuples of (sensorId, nodeId, remoteSensorId,
		# description, state, lastStateUpdated, alertDelay))
		# list[3] = list(tuples of (managerId, nodeId, description))
		# list[4] = list(tuples of (alertId, nodeId, remoteAlertId,
		# description))
		# or None
		return alertSystemInformation


	# change a option in the database
	#
	# return True or False
	def changeOption(self, optionType, optionValue):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		try:
			# check if option does exist
			self.cursor.execute("SELECT id "
				+ "FROM options "
				+ "WHERE type=%s", (optionType, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logging.error("[%s]: Option was not found." % self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

			# update option in database
			self.cursor.execute("UPDATE options SET "
				+ "value = %s "
				+ "WHERE type = %s", (optionValue, optionType))

		except Exception as e:

			logging.exception("[%s]: Not able to update " % self.fileName
				+ "option in database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# gets the state of a sensor given by id
	#
	# return sensor state or None
	def getSensorState(self, sensorId):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return None

		try:
			# get sensor state from database
			self.cursor.execute("SELECT state "
				+ "FROM sensors "
				+ "WHERE id=%s", (sensorId, ))
			result = self.cursor.fetchall()
			if len(result) != 1:
				logging.error("[%s]: Sensor was not found." % self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return None

			state = result[0][0]

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "sensor state from database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return state


	# closes db for usage
	#
	# no return value
	def close(self):
		pass