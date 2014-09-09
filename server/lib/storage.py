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


# internal abstract class for new storage backends
class _Storage():

	# creates the database (should only be called if the database
	# does not exist)
	#
	# no return value but raise exception if it fails
	def createStorage(self):
		raise NotImplemented("Function not implemented yet.")


	# adds a node if it does not exist or changes the registration
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType):
		raise NotImplemented("Function not implemented yet.")


	# adds the data that is given by the node for the sensor to the database
	#
	# return True or False
	def addSensor(self, username, remoteSensorId, alertDelay, description):
		raise NotImplemented("Function not implemented yet.")


	# adds the data that is given by the node for the alert to the database
	#
	# return True or False
	def addAlert(self, username, remoteAlertId, description):
		raise NotImplemented("Function not implemented yet.")


	# adds the alert levels that are given by the node for the alert
	# client to the database
	#
	# return True or False
	def addAlertLevels(self, username, alertLevels):
		raise NotImplemented("Function not implemented yet.")


	# adds the data that is given by the node for the manager to the database
	#
	# return True or False
	def addManager(self, username, description):
		raise NotImplemented("Function not implemented yet.")


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, remoteSensorId, state):
		raise NotImplemented("Function not implemented yet.")


	# checks if the given data of the node and the data in the database
	# are the same
	#
	# return True or False
	def checkNode(self, username, hostname, nodeType):
		raise NotImplemented("Function not implemented yet.")


	# checks if the given data of the sensor and the data in the database
	# are the same
	#
	# return True or False
	def checkSensor(self, username, remoteSensorId, alertDelay, description):
		raise NotImplemented("Function not implemented yet.")


	# checks if the given data of the alert and the data in the database
	# are the same
	#
	# return True or False
	def checkAlert(self, username, remoteAlertId, description):
		raise NotImplemented("Function not implemented yet.")


	# checks if the given alert levels of the alert client and the alert
	# levels in the database are the same
	#
	# return True or False
	def checkAlertLevels(self, username, alertLevels):
		raise NotImplemented("Function not implemented yet.")


	# checks if the given data of the manager and the data in the database
	# are the same
	#
	# return True or False
	def checkManager(self, username, description):
		raise NotImplemented("Function not implemented yet.")


	# checks if the given sensor count of the node does match
	# the count in the database
	#
	# return True or False
	def checkSensorCount(username, sensorCount):
		raise NotImplemented("Function not implemented yet.")


	# checks if the given alert count of the node does match
	# the count in the database
	#
	# return True or False
	def checkAlertCount(self, username, alertCount):
		raise NotImplemented("Function not implemented yet.")


	# checks if the given alert level count of the node does match
	# the count in the database
	#
	# return True or False
	def checkAlertLevelCount(self, username, alertLevelCount):
		raise NotImplemented("Function not implemented yet.")


	# gets the id of the node by a given username
	# (usernames are unique to each node)
	#
	# return nodeId or None
	def getNodeId(self, username):
		raise NotImplemented("Function not implemented yet.")


	# gets the count of the sensors of a node in the database
	# return count of sensors in database
	def getSensorCount(self, nodeId):
		raise NotImplemented("Function not implemented yet.")


	# gets the sensor id of a sensor when the id of a node is given
	# and the remote sensor id that is used by the node internally
	#
	# return sensorId or None
	def getSensorId(self, nodeId, remoteSensorId):
		raise NotImplemented("Function not implemented yet.")


	# gets all sensor alerts in the database
	#
	# return a list of tuples (sensorAlertId, sensorId, timeReceived,
	# alertDelay, alertLevel, state, triggerAlways)
	# or None
	def getSensorAlerts(self):
		raise NotImplemented("Function not implemented yet.")


	# gets all details of a sensor alert that are for example used
	# to generate a notification
	#
	# return tuple of (hostname, description, timeReceived)
	# or None
	def getSensorAlertDetails(self, sensorAlertId):
		raise NotImplemented("Function not implemented yet.")


	# gets all alert levels from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllAlertLevels(self):
		raise NotImplemented("Function not implemented yet.")


	# gets all nodes from the database that are connected to the server
	#
	# return list of tuples of (nodeId)
	# or None
	def getAllConnectedNodeIds(self):
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
	# remoteSensorId, description, state, lastStateUpdated, alertDelay,
	# alertLevel, triggerAlways)
	# or None
	def getSensorInformation(self, sensorId):
		raise NotImplemented("Function not implemented yet.")


	# gets the hostname of a node from the database when its id is given
	#
	# return hostname or None
	def getNodeHostnameById(self, nodeId):
		raise NotImplemented("Function not implemented yet.")


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = optionCount
	# list[1] = list(tuples of (type, value))
	# list[2] = nodeCount
	# list[3] = list(tuples of (nodeId, hostname, nodeType, connected))
	# list[4] = sensorCount
	# list[5] = list(tuples of (nodeId, sensorId, alertDelay,
	# alertLevel, description, lastStateUpdated, state))
	# list[6] = managerCount
	# list[7] = list(tuples of (nodeId, managerId, description))
	# list[8] = alertCount
	# list[9] = list(tuples of (nodeId, alertId, description))
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

	def __init__(self, storagePath, version):

		# import the needed package
		import sqlite3

		# version of server
		self.version = version

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


	# internal function that checks if the username is known
	def _usernameInDb(self, username):

		# check if the username does exist => if not node is not known
		self.cursor.execute("SELECT id FROM nodes WHERE username = ? ",
			[username])
		result = self.cursor.fetchall()

		# return if username was found or not
		if len(result) == 0:
			return False
		else:
			return True


	# internal function that gets the id of a node when a username is given
	def _getNodeId(self, username):

		# check if the username does exist
		if self._usernameInDb(username):
			# get id of username
			self.cursor.execute("SELECT id FROM nodes WHERE username = ? ",
				[username])
			result = self.cursor.fetchall()

			return result[0][0]
		else:
			raise ValueError("Node id was not found.")


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.dbLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
		self.dbLock.release()


	# creates the database (should only be called if the database
	# does not exist)
	#
	# no return value but raise exception if it fails
	def createStorage(self):

		self._acquireLock()

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

		# insert version of server
		self.cursor.execute("INSERT INTO options ("
			+ "type, "
			+ "value) VALUES (?, ?)", ("version", self.version))

		# create nodes table
		self.cursor.execute("CREATE TABLE nodes ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "hostname TEXT NOT NULL, "
			+ "username TEXT NOT NULL UNIQUE, "
			+ "nodeType TEXT NOT NULL, "
			+ "connected INTEGER NOT NULL)")

		# create sensors table
		self.cursor.execute("CREATE TABLE sensors ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteSensorId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "lastStateUpdated INTEGER NOT NULL, "
			+ "alertDelay INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "triggerAlways INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create sensorAlerts table
		self.cursor.execute("CREATE TABLE sensorAlerts ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "sensorId INTEGER NOT NULL, "
			+ "timeReceived INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id), "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create alerts table
		self.cursor.execute("CREATE TABLE alerts ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteAlertId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create alertLevels table
		self.cursor.execute("CREATE TABLE alertLevels ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create managers table
		self.cursor.execute("CREATE TABLE managers ("
			+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")		

		# commit all changes
		self.conn.commit()

		self._releaseLock()


	# adds a node if it does not exist or changes the registration
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType):

		self._acquireLock()
		
		# check if node with the same username already exists
		# => only update information
		if self._usernameInDb(username):
			try:
				self.cursor.execute("UPDATE nodes SET "
					+ "hostname = ?, "
					+ "nodeType = ?, "
					+ "connected = 1 WHERE username = ?", (hostname, nodeType,
					username))
			except Exception as e:
				logging.exception("[%s]: Not able to add node."
					% self.fileName)

				self._releaseLock()

				return False

			# get the id of the node
			try:
				nodeId = self._getNodeId(username)
			except Exception as e:
				logging.exception("[%s]: Not able to add node." 
					% self.fileName)

				self._releaseLock()

				return False

			# remove old sensors data from database
			# (complete node will be newly added)
			# if type is sensor
			if nodeType == "sensor":
				try:
					self.cursor.execute("DELETE FROM sensors "
						+ "WHERE nodeId = ?", (nodeId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to add node." 
						% self.fileName)

					self._releaseLock()

					return False

			# remove old manager data from database
			# (complete node will be newly added)
			# if type is manager
			elif nodeType == "manager":
				try:
					self.cursor.execute("DELETE FROM managers "
						+ "WHERE nodeId = ?", (nodeId, ) )
				except Exception as e:
					logging.exception("[%s]: Not able to add node." 
						% self.fileName)

					self._releaseLock()

					return False

			# remove old alerts data from database
			# (complete node will be newly added)
			# if type is alert
			elif nodeType == "alert":
				try:
					self.cursor.execute("DELETE FROM alerts "
						+ "WHERE nodeId = ?", (nodeId, ))
					self.cursor.execute("DELETE FROM alertLevels "
						+ "WHERE nodeId = ?", (nodeId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to add node." 
						% self.fileName)

					self._releaseLock()

					return False	

		# if node does not exist => add it
		else:
			try:
				self.cursor.execute("INSERT INTO nodes ("
					+ "hostname, "
					+ "username, "
					+ "nodeType, "
					+ "connected) VALUES (?, ?, ?, ?)",
					(hostname, username, nodeType, 1))
			except Exception as e:
				logging.exception("[%s]: Not able to add node."
					% self.fileName)

				self._releaseLock()

				return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# adds the data that is given by the node for the sensor to the database
	#
	# return True or False
	def addSensor(self, username, remoteSensorId, alertDelay, alertLevel,
		description, triggerAlways):

		self._acquireLock()	
		
		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to add sensor." % self.fileName)

			self._releaseLock()

			return False

		# check if trigger always has a valid value
		if (triggerAlways != 0 
			and triggerAlways != 1):
			logging.error("[%s]: triggerAlways not valid." % self.fileName)

			self._releaseLock()

			return False

		# add sensor to database
		try:
			self.cursor.execute("INSERT INTO sensors ("
				+ "nodeId, "
				+ "remoteSensorId, "
				+ "description, "
				+ "state, "
				+ "lastStateUpdated, "
				+ "alertDelay, "
				+ "alertLevel, "
				+ "triggerAlways) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
				(nodeId, remoteSensorId, description, 0, 0, alertDelay,
				alertLevel, triggerAlways))
		except Exception as e:
			logging.exception("[%s]: Not able to add sensor." % self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# adds the data that is given by the node for the alert to the database
	#
	# return True or False
	def addAlert(self, username, remoteAlertId, description):

		self._acquireLock()	
		
		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to add alert." % self.fileName)

			self._releaseLock()

			return False

		# add alert to database
		try:
			self.cursor.execute("INSERT INTO alerts ("
				+ "nodeId, "
				+ "remoteAlertId, "
				+ "description) VALUES (?, ?, ?)", (nodeId,
				remoteAlertId, description))
		except Exception as e:
			logging.exception("[%s]: Not able to add alert." % self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# adds the alert levels that are given by the node for the alert
	# client to the database
	#
	# return True or False
	def addAlertLevels(self, username, alertLevels):

		self._acquireLock()	
		
		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to add alert levels."
				% self.fileName)

			self._releaseLock()

			return False

		# add alert levels to database
		try:
			for alertLevel in alertLevels:
				self.cursor.execute("INSERT INTO alertLevels ("
					+ "nodeId, "
					+ "alertLevel) VALUES (?, ?)", (nodeId, alertLevel))
		except Exception as e:
			logging.exception("[%s]: Not able to add alert levels."
				% self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True


	# adds the data that is given by the node for the manager to the database
	#
	# return True or False
	def addManager(self, username, description):

		self._acquireLock()	
		
		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to add manager." % self.fileName)

			self._releaseLock()

			return False

		# add manager to database
		try:
			self.cursor.execute("INSERT INTO managers ("
				+ "nodeId, "
				+ "description) VALUES (?, ?)", (nodeId, description))
		except Exception as e:
			logging.exception("[%s]: Not able to add manager." % self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		self._releaseLock()

		return True		


	# checks if the given data of the node and the data in the database
	# are the same
	#
	# return True or False
	def checkNode(self, username, hostname, nodeType):

		self._acquireLock()

		# check if the username does exist
		if self._usernameInDb(username):
			# get hostname and nodeType of username
			self.cursor.execute("SELECT hostname, nodeType FROM nodes "
				+ "WHERE username = ? ", (username, ))
			result = self.cursor.fetchall()

			if (result[0][0] == hostname
				and result[0][1] == nodeType):

				self._releaseLock()

				return True

		self._releaseLock()

		return False


	# checks if the given data of the sensor and the data in the database
	# are the same
	#
	# return True or False
	def checkSensor(self, username, remoteSensorId, alertDelay, alertLevel,
		description, triggerAlways):

		self._acquireLock()

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check sensor.")

			self._releaseLock()

			return False

		self.cursor.execute("SELECT alertDelay, "
			+ "alertLevel, "
			+ "description, "
			+ "triggerAlways "
			+ "FROM sensors "
			+ "WHERE nodeId = ? "
			+ "AND remoteSensorId = ?", (nodeId, remoteSensorId))

		result = self.cursor.fetchall()

		# check if the sensor was found
		if len(result) == 0:
			logging.error("[%s]: Sensor was not found." % self.fileName)

			self._releaseLock()

			return False

		# check if the sensor was found multiple times
		elif len(result) > 1:
			logging.error("[%s]: Sensor was found multiple times."
				% self.fileName)

			self._releaseLock()

			return False

		if (result[0][0] == alertDelay
			and result[0][1] == alertLevel
			and result[0][2] == description
			and result[0][3] == triggerAlways):

			self._releaseLock()

			return True

		logging.error("[%s]: Sensor configuration does not match."
				% self.fileName)

		self._releaseLock()

		return False


	# checks if the given data of the alert and the data in the database
	# are the same
	#
	# return True or False
	def checkAlert(self, username, remoteAlertId, description):

		self._acquireLock()

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert.")

			self._releaseLock()

			return False

		self.cursor.execute("SELECT description "
			+ "FROM alerts "
			+ "WHERE nodeId = ? "
			+ "AND remoteAlertId = ?", (nodeId, remoteAlertId))

		result = self.cursor.fetchall()

		# check if the alert was found
		if len(result) == 0:
			logging.error("[%s]: Alert was not found." % self.fileName)

			self._releaseLock()

			return False

		# check if the alert was found multiple times
		elif len(result) > 1:
			logging.error("[%s]: Alert was found multiple times."
				% self.fileName)

			self._releaseLock()

			return False

		if result[0][0] == description:

			self._releaseLock()

			return True

		logging.error("[%s]: Alert configuration does not match."
				% self.fileName)

		self._releaseLock()

		return False


	# checks if the given alert levels of the alert client and the alert
	# levels in the database are the same
	#
	# return True or False
	def checkAlertLevels(self, username, alertLevels):

		self._acquireLock()

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert.")

			self._releaseLock()

			return False

		self.cursor.execute("SELECT alertLevel "
			+ "FROM alertLevels "
			+ "WHERE nodeId = ? ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the alert levels were found
		if len(result) == 0:
			logging.error("[%s]: Alert levels were not found." % self.fileName)

			self._releaseLock()

			return False

		# only check of all stored alert levels are in the list of
		# the received alert levels (because the count of the alert levels
		# are checked before => they all match if this check succeeds)
		for alertLevelTuple in result:
			if not alertLevelTuple[0] in alertLevels:

				logging.error("[%s]: Alert level configuration does not match."
					% self.fileName)

				self._releaseLock()

				return False

		self._releaseLock()

		return True


	# checks if the given data of the manager and the data in the database
	# are the same
	#
	# return True or False
	def checkManager(self, username, description):

		self._acquireLock()

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check manager.")

			self._releaseLock()

			return False

		self.cursor.execute("SELECT description "
			+ "FROM managers "
			+ "WHERE nodeId = ?", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the manager was found
		if len(result) == 0:
			logging.error("[%s]: Manager was not found." % self.fileName)

			self._releaseLock()

			return False

		# check if the manager was found multiple times
		elif len(result) > 1:
			logging.error("[%s]: Manager was found multiple times."
				% self.fileName)

			self._releaseLock()

			return False

		if (result[0][0] == description):

			self._releaseLock()

			return True

		logging.error("[%s]: Manager configuration does not match."
				% self.fileName)

		self._releaseLock()

		return False


	# checks if the given sensor count of the node does match
	# the count in the database
	#
	# return True or False
	def checkSensorCount(self, username, sensorCount):

		self._acquireLock()

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check sensor count.")

			self._releaseLock()

			return False		

		# get all sensors on this nodes
		self.cursor.execute("SELECT id FROM sensors "
			+ "WHERE nodeId = ?", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the count does match the received count
		if len(result) != sensorCount:
			logging.error("[%s]: Sensor count does not match with database."
				% self.fileName)

			self._releaseLock()

			return False

		self._releaseLock()

		return True


	# checks if the given alert count of the node does match
	# the count in the database
	#
	# return True or False
	def checkAlertCount(self, username, alertCount):

		self._acquireLock()

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert count.")

			self._releaseLock()

			return False		

		# get all alerts on this nodes
		self.cursor.execute("SELECT id FROM alerts "
			+ "WHERE nodeId = ?", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the count does match the received count
		if len(result) != alertCount:
			logging.error("[%s]: Alert count does not match with database."
				% self.fileName)

			self._releaseLock()

			return False

		self._releaseLock()

		return True


	# checks if the given alert level count of the node does match
	# the count in the database
	#
	# return True or False
	def checkAlertLevelCount(self, username, alertLevelCount):

		self._acquireLock()

		# get the id of the node
		try:
			nodeId = self._getNodeId(username)
		except Exception as e:
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert level count.")

			self._releaseLock()

			return False		

		# get all alert levels on this nodes
		self.cursor.execute("SELECT id FROM alertLevels "
			+ "WHERE nodeId = ?", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the count does match the received count
		if len(result) != alertLevelCount:
			logging.error("[%s]: Alert level count " % self.fileName
				+ "does not match with database.")

			self._releaseLock()

			return False

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
	# return count of sensors in database
	def getSensorCount(self, nodeId):

		self._acquireLock()

		# get all sensors on this nodes
		self.cursor.execute("SELECT id FROM sensors "
			+ "WHERE nodeId = ?", (nodeId, ))

		result = self.cursor.fetchall()
		sensorCount = len(result)

		self._releaseLock()

		return sensorCount


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

			# get sensorId from database
			self.cursor.execute("SELECT id FROM sensors "
				+ "WHERE nodeId = ? "
				+ "AND remoteSensorId = ?", (nodeId, remoteSensorId))
			result = self.cursor.fetchall()

			if len(result) != 1:
				logging.error("[%s]: Sensor does not exist in database."
					% self.fileName)

				self._releaseLock()

				return None

			sensorId = result[0][0]

		except Exception as e:
			logging.exception("[%s]: Not able to get sensorId from database."
				% self.fileName)

			self._releaseLock()

			return None

		self._releaseLock()

		return sensorId


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, remoteSensorId, state):

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
			self.cursor.execute("UPDATE sensors SET "
				+ "state = ?, "
				+ "lastStateUpdated = ? "
				+ "WHERE nodeId = ? "
				+ "AND remoteSensorId = ?",
				(state, int(time.time()), nodeId, remoteSensorId))

			# add sensor alert to database
			self.cursor.execute("INSERT INTO sensorAlerts ("
				+ "nodeId, "
				+ "sensorId, "
				+ "timeReceived) VALUES (?, ?, ?)",
				(nodeId, sensorId, int(time.time())))

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
	# return a list of tuples (sensorAlertId, sensorId, timeReceived,
	# alertDelay, alertLevel, state, triggerAlways)
	# or None
	def getSensorAlerts(self):

		self._acquireLock()

		try:
			
			self.cursor.execute("SELECT sensorAlerts.id, "
				+ "sensors.id, "
				+ "sensorAlerts.timeReceived, "
				+ "sensors.alertDelay, "
				+ "sensors.alertLevel, "
				+ "sensors.state, "
				+ "sensors.triggerAlways "
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

		# return a list of tuples (sensorAlertId, sensorId, timeReceived,
		# alertDelay, alertLevel, state, triggerAlways)
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


	# gets all details of a sensor alert that are for example used
	# to generate a notification
	#
	# return tuple of (hostname, description, timeReceived)
	# or None
	def getSensorAlertDetails(self, sensorAlertId):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT nodeId, sensorId, timeReceived "
				+ "FROM sensorAlerts "
				+ "WHERE id = ?", (sensorAlertId, ))
			result = self.cursor.fetchall()
			nodeId = result[0][0]
			sensorId = result[0][1]
			timeReceived = result[0][2]

			self.cursor.execute("SELECT description "
				+ "FROM sensors "
				+ "WHERE id = ?", (sensorId, ))
			result = self.cursor.fetchall()
			description = result[0][0]

			self.cursor.execute("SELECT hostname "
				+ "FROM nodes "
				+ "WHERE id = ?", (nodeId, ))
			result = self.cursor.fetchall()
			hostname = result[0][0]

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "sensor alert details.")

			self._releaseLock()

			# return None if action failed
			return None

		self._releaseLock()

		# return tuple of (hostname, description, timeReceived)
		returnTuple = (hostname, description, timeReceived)
		return returnTuple


	# gets all alert levels from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllAlertLevels(self):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels.")

			self._releaseLock()

			# return None if action failed
			return None

		self._releaseLock()

		# return list of tuples of (alertLevel)
		return result


	# gets all nodes from the database that are connected to the server
	#
	# return list of tuples of (nodeId)
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
				+ "all node ids.")

			self._releaseLock()

			# return None if action failed
			return None

		self._releaseLock()

		# return list of tuples of (nodeId)
		return result


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
	# remoteSensorId, description, state, lastStateUpdated, alertDelay,
	# alertLevel, triggerAlways)
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
				+ "alertDelay, "
				+ "alertLevel, "
				+ "triggerAlways "
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
		# remoteSensorId, description, state, lastStateUpdated, alertDelay,
		# alertLevel, triggerAlways)
		return result[0]


	# gets the hostname of a node from the database when its id is given
	#
	# return hostname or None
	def getNodeHostnameById(self, nodeId):

		self._acquireLock()

		try:
			self.cursor.execute("SELECT hostname FROM nodes "
				+ "WHERE id = ?", (nodeId, ))

			result = self.cursor.fetchall()
			hostname = result[0][0]
		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "hostname for node from database.")

			self._releaseLock()

			return None

		self._releaseLock()

		return hostname


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = optionCount
	# list[1] = list(tuples of (type, value))
	# list[2] = nodeCount
	# list[3] = list(tuples of (nodeId, hostname, nodeType, connected))
	# list[4] = sensorCount
	# list[5] = list(tuples of (nodeId, sensorId, alertDelay,
	# alertLevel, description, lastStateUpdated, state))
	# list[6] = managerCount
	# list[7] = list(tuples of (nodeId, managerId, description))
	# list[8] = alertCount
	# list[9] = list(tuples of (nodeId, alertId, description))
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
			optionCount = len(optionsInformation)

			# get all nodes information
			self.cursor.execute("SELECT id, "
				+ "hostname, "
				+ "nodeType, "
				+ "connected "
				+ "FROM nodes")
			result = self.cursor.fetchall()
			nodesInformation = result
			nodeCount = len(nodesInformation)

			# get all sensors information
			self.cursor.execute("SELECT nodeId, "
				+ "id, "
				+ "alertDelay, "
				+ "alertLevel, "
				+ "description, "
				+ "lastStateUpdated, "
				+ "state "
				+ "FROM sensors")
			result = self.cursor.fetchall()
			sensorsInformation = result
			sensorCount = len(sensorsInformation)

			# get all managers information
			self.cursor.execute("SELECT nodeId, "
				+ "id, "
				+ "description "
				+ "FROM managers")
			result = self.cursor.fetchall()
			managersInformation = result
			managerCount = len(managersInformation)			

			# get all alerts information
			self.cursor.execute("SELECT nodeId, "
				+ "id, "
				+ "description "
				+ "FROM alerts")
			result = self.cursor.fetchall()
			alertsInformation = result
			alertCount = len(alertsInformation)

			# generate a list with all nodes information
			alertSystemInformation = list()
			alertSystemInformation.append(optionCount)
			alertSystemInformation.append(optionsInformation)
			alertSystemInformation.append(nodeCount)
			alertSystemInformation.append(nodesInformation)
			alertSystemInformation.append(sensorCount)
			alertSystemInformation.append(sensorsInformation)
			alertSystemInformation.append(managerCount)
			alertSystemInformation.append(managersInformation)
			alertSystemInformation.append(alertCount)
			alertSystemInformation.append(alertsInformation)

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all nodes information from database.")

			self._releaseLock()

			return None

		self._releaseLock()

		# return a list of
		# list[0] = optionCount
		# list[1] = list(tuples of (type, value))
		# list[2] = nodeCount
		# list[3] = list(tuples of (nodeId, hostname, nodeType, connected))
		# list[4] = sensorCount
		# list[5] = list(tuples of (nodeId, sensorId, alertDelay,
		# alertLevel, description, lastStateUpdated, state))
		# list[6] = managerCount
		# list[7] = list(tuples of (nodeId, managerId, description))
		# list[8] = alertCount
		# list[9] = list(tuples of (nodeId, alertId, description))		
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

	def __init__(self, host, port, database, username, password, version):

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# version of server
		self.version = version

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
		self.cursor.execute("SHOW TABLES LIKE 'options'")
		optionsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'nodes'")
		nodesResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'sensors'")
		sensorsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'sensorAlerts'")
		sensorAlertsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'alerts'")
		alertsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'alertLevels'")
		alertLevelsResult = self.cursor.fetchall()
		self.cursor.execute("SHOW TABLES LIKE 'managers'")
		managersResult = self.cursor.fetchall()

		# close connection to the database
		self._closeConnection()

		if (len(optionsResult) == 0
			or len(nodesResult) == 0
			or len(sensorsResult) == 0
			or len(sensorAlertsResult) == 0
			or len(alertsResult) == 0
			or len(alertLevelsResult) == 0
			or len(managersResult) == 0):
			self.createStorage()


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


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.dbLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
		self.dbLock.release()


	# creates the database (should only be called if the database
	# does not exist)
	#
	# no return value but raise exception if it fails
	def createStorage(self):

		self._acquireLock()

		# connect to the database
		self._openConnection()

		# create options table
		self.cursor.execute("CREATE TABLE options ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "type VARCHAR(255) NOT NULL UNIQUE, "
			+ "value FLOAT NOT NULL)")

		# insert option to activate/deactivate alert system
		# (0 = deactivated, 1 = activated)
		self.cursor.execute("INSERT INTO options ("
			+ "type, "
			+ "value) VALUES (%s, %s)", ("alertSystemActive", 0))

		# insert version of server
		self.cursor.execute("INSERT INTO options ("
			+ "type, "
			+ "value) VALUES (%s, %s)", ("version", self.version))

		# create nodes table
		self.cursor.execute("CREATE TABLE nodes ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "hostname VARCHAR(255) NOT NULL, "
			+ "username VARCHAR(255) NOT NULL UNIQUE, "
			+ "nodeType VARCHAR(255) NOT NULL, "
			+ "connected INTEGER NOT NULL)")

		# create sensors table
		self.cursor.execute("CREATE TABLE sensors ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteSensorId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "lastStateUpdated INTEGER NOT NULL, "
			+ "alertDelay INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "triggerAlways INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create sensorAlerts table
		self.cursor.execute("CREATE TABLE sensorAlerts ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "sensorId INTEGER NOT NULL, "
			+ "timeReceived INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id), "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create alerts table
		self.cursor.execute("CREATE TABLE alerts ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteAlertId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create alertLevels table
		self.cursor.execute("CREATE TABLE alertLevels ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create managers table
		self.cursor.execute("CREATE TABLE managers ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")		

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()


	# adds a node if it does not exist or changes the registration
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType):

		self._acquireLock()
		
		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		# check if node with the same username already exists
		# => only update information
		if self._usernameInDb(username):
			try:
				self.cursor.execute("UPDATE nodes SET "
					+ "hostname = %s, "
					+ "nodeType = %s, "
					+ "connected = 1 WHERE username = %s", (hostname, nodeType,
					username))
			except Exception as e:
				logging.exception("[%s]: Not able to add node."
					% self.fileName)

				self._releaseLock()

				return False

			# get the id of the node
			try:
				nodeId = self._getNodeId(username)
			except Exception as e:
				logging.exception("[%s]: Not able to add node." 
					% self.fileName)

				self._releaseLock()

				return False

			# remove old sensors data from database
			# (complete node will be newly added)
			# if type is sensor
			if nodeType == "sensor":
				try:
					self.cursor.execute("DELETE FROM sensors "
						+ "WHERE nodeId = %s", (nodeId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to add node." 
						% self.fileName)

					self._releaseLock()

					return False

			# remove old manager data from database
			# (complete node will be newly added)
			# if type is manager
			elif nodeType == "manager":
				try:
					self.cursor.execute("DELETE FROM managers "
						+ "WHERE nodeId = %s", (nodeId, ) )
				except Exception as e:
					logging.exception("[%s]: Not able to add node." 
						% self.fileName)

					self._releaseLock()

					return False

			# remove old alerts data from database
			# (complete node will be newly added)
			# if type is alert
			elif nodeType == "alert":
				try:
					self.cursor.execute("DELETE FROM alerts "
						+ "WHERE nodeId = %s", (nodeId, ))
					self.cursor.execute("DELETE FROM alertLevels "
						+ "WHERE nodeId = %s", (nodeId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to add node." 
						% self.fileName)

					self._releaseLock()

					return False	

		# if node does not exist => add it
		else:
			try:
				self.cursor.execute("INSERT INTO nodes ("
					+ "hostname, "
					+ "username, "
					+ "nodeType, "
					+ "connected) VALUES (%s, %s, %s, %s)",
					(hostname, username, nodeType, 1))
			except Exception as e:
				logging.exception("[%s]: Not able to add node."
					% self.fileName)

				self._releaseLock()

				return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds the data that is given by the node for the sensor to the database
	#
	# return True or False
	def addSensor(self, username, remoteSensorId, alertDelay, alertLevel,
		description, triggerAlways):

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
			logging.exception("[%s]: Not able to add sensor." % self.fileName)

			self._releaseLock()

			return False

		# check if trigger always has a valid value
		if (triggerAlways != 0 
			and triggerAlways != 1):
			logging.error("[%s]: triggerAlways not valid." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# add sensor to database
		try:
			self.cursor.execute("INSERT INTO sensors ("
				+ "nodeId, "
				+ "remoteSensorId, "
				+ "description, "
				+ "state, "
				+ "lastStateUpdated, "
				+ "alertDelay, "
				+ "alertLevel, "
				+ "triggerAlways) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
				(nodeId, remoteSensorId, description, 0, 0, alertDelay,
				alertLevel, triggerAlways))
		except Exception as e:
			logging.exception("[%s]: Not able to add sensor." % self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds the data that is given by the node for the alert to the database
	#
	# return True or False
	def addAlert(self, username, remoteAlertId, description):

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
			logging.exception("[%s]: Not able to add alert." % self.fileName)

			self._releaseLock()

			return False

		# add alert to database
		try:
			self.cursor.execute("INSERT INTO alerts ("
				+ "nodeId, "
				+ "remoteAlertId, "
				+ "description) VALUES (%s, %s, %s)", (nodeId,
				remoteAlertId, description))
		except Exception as e:
			logging.exception("[%s]: Not able to add alert." % self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds the alert levels that are given by the node for the alert
	# client to the database
	#
	# return True or False
	def addAlertLevels(self, username, alertLevels):

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
			logging.exception("[%s]: Not able to add alert levels."
				% self.fileName)

			self._releaseLock()

			return False

		# add alert levels to database
		try:
			for alertLevel in alertLevels:
				self.cursor.execute("INSERT INTO alertLevels ("
					+ "nodeId, "
					+ "alertLevel) VALUES (%s, %s)", (nodeId, alertLevel))
		except Exception as e:
			logging.exception("[%s]: Not able to add alert levels."
				% self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds the data that is given by the node for the manager to the database
	#
	# return True or False
	def addManager(self, username, description):

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
			logging.exception("[%s]: Not able to add manager." % self.fileName)

			self._releaseLock()

			return False

		# add manager to database
		try:
			self.cursor.execute("INSERT INTO managers ("
				+ "nodeId, "
				+ "description) VALUES (%s, %s)", (nodeId, description))
		except Exception as e:
			logging.exception("[%s]: Not able to add manager." % self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True		


	# checks if the given data of the node and the data in the database
	# are the same
	#
	# return True or False
	def checkNode(self, username, hostname, nodeType):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		# check if the username does exist
		if self._usernameInDb(username):
			# get hostname and nodeType of username
			self.cursor.execute("SELECT hostname, nodeType FROM nodes "
				+ "WHERE username = %s ", (username, ))
			result = self.cursor.fetchall()

			if (result[0][0] == hostname
				and result[0][1] == nodeType):

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return True

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return False


	# checks if the given data of the sensor and the data in the database
	# are the same
	#
	# return True or False
	def checkSensor(self, username, remoteSensorId, alertDelay, alertLevel,
		description, triggerAlways):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check sensor.")

			self._releaseLock()

			return False

		self.cursor.execute("SELECT alertDelay, "
			+ "alertLevel, "
			+ "description, "
			+ "triggerAlways "
			+ "FROM sensors "
			+ "WHERE nodeId = %s "
			+ "AND remoteSensorId = %s", (nodeId, remoteSensorId))

		result = self.cursor.fetchall()

		# check if the sensor was found
		if len(result) == 0:
			logging.error("[%s]: Sensor was not found." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# check if the sensor was found multiple times
		elif len(result) > 1:
			logging.error("[%s]: Sensor was found multiple times."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		if (result[0][0] == alertDelay
			and result[0][1] == alertLevel
			and result[0][2] == description
			and result[0][3] == triggerAlways):

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return True

		logging.error("[%s]: Sensor configuration does not match."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return False


	# checks if the given data of the alert and the data in the database
	# are the same
	#
	# return True or False
	def checkAlert(self, username, remoteAlertId, description):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert.")

			self._releaseLock()

			return False

		self.cursor.execute("SELECT description "
			+ "FROM alerts "
			+ "WHERE nodeId = %s "
			+ "AND remoteAlertId = %s", (nodeId, remoteAlertId))

		result = self.cursor.fetchall()

		# check if the alert was found
		if len(result) == 0:
			logging.error("[%s]: Alert was not found." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# check if the alert was found multiple times
		elif len(result) > 1:
			logging.error("[%s]: Alert was found multiple times."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		if result[0][0] == description:

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return True

		logging.error("[%s]: Alert configuration does not match."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return False


	# checks if the given alert levels of the alert client and the alert
	# levels in the database are the same
	#
	# return True or False
	def checkAlertLevels(self, username, alertLevels):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert.")

			self._releaseLock()

			return False

		self.cursor.execute("SELECT alertLevel "
			+ "FROM alertLevels "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the alert levels were found
		if len(result) == 0:
			logging.error("[%s]: Alert levels were not found." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# only check of all stored alert levels are in the list of
		# the received alert levels (because the count of the alert levels
		# are checked before => they all match if this check succeeds)
		for alertLevelTuple in result:
			if not alertLevelTuple[0] in alertLevels:

				logging.error("[%s]: Alert level configuration does not match."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# checks if the given data of the manager and the data in the database
	# are the same
	#
	# return True or False
	def checkManager(self, username, description):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check manager.")

			self._releaseLock()

			return False

		self.cursor.execute("SELECT description "
			+ "FROM managers "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the manager was found
		if len(result) == 0:
			logging.error("[%s]: Manager was not found." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# check if the manager was found multiple times
		elif len(result) > 1:
			logging.error("[%s]: Manager was found multiple times."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		if (result[0][0] == description):

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return True

		logging.error("[%s]: Manager configuration does not match."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return False


	# checks if the given sensor count of the node does match
	# the count in the database
	#
	# return True or False
	def checkSensorCount(self, username, sensorCount):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check sensor count.")

			self._releaseLock()

			return False		

		# get all sensors on this nodes
		self.cursor.execute("SELECT id FROM sensors "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the count does match the received count
		if len(result) != sensorCount:
			logging.error("[%s]: Sensor count does not match with database."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# checks if the given alert count of the node does match
	# the count in the database
	#
	# return True or False
	def checkAlertCount(self, username, alertCount):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert count.")

			self._releaseLock()

			return False		

		# get all alerts on this nodes
		self.cursor.execute("SELECT id FROM alerts "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the count does match the received count
		if len(result) != alertCount:
			logging.error("[%s]: Alert count does not match with database."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# checks if the given alert level count of the node does match
	# the count in the database
	#
	# return True or False
	def checkAlertLevelCount(self, username, alertLevelCount):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert level count.")

			self._releaseLock()

			return False		

		# get all alert levels on this nodes
		self.cursor.execute("SELECT id FROM alertLevels "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the count does match the received count
		if len(result) != alertLevelCount:
			logging.error("[%s]: Alert level count " % self.fileName
				+ "does not match with database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

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

		# get all sensors on this nodes
		self.cursor.execute("SELECT id FROM sensors "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()
		sensorCount = len(result)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return sensorCount


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

			# get sensorId from database
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

				return None

			sensorId = result[0][0]

		except Exception as e:
			logging.exception("[%s]: Not able to get sensorId from database."
				% self.fileName)

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return sensorId


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, remoteSensorId, state):

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
			self.cursor.execute("UPDATE sensors SET "
				+ "state = %s, "
				+ "lastStateUpdated = %s "
				+ "WHERE nodeId = %s "
				+ "AND remoteSensorId = %s",
				(state, int(time.time()), nodeId, remoteSensorId))

			# add sensor alert to database
			self.cursor.execute("INSERT INTO sensorAlerts ("
				+ "nodeId, "
				+ "sensorId, "
				+ "timeReceived) VALUES (%s, %s, %s)",
				(nodeId, sensorId, int(time.time())))

		except Exception as e:
			logging.exception("[%s]: Not able to add sensor alert."
				% self.fileName)

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
	# return a list of tuples (sensorAlertId, sensorId, timeReceived,
	# alertDelay, alertLevel, state, triggerAlways)
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
				+ "sensorAlerts.timeReceived, "
				+ "sensors.alertDelay, "
				+ "sensors.alertLevel, "
				+ "sensors.state, "
				+ "sensors.triggerAlways "
				+ "FROM sensorAlerts "
				+ "INNER JOIN sensors "
				+ "ON sensorAlerts.nodeId = sensors.nodeId "
				+ "AND sensorAlerts.sensorId = sensors.id")
			result = self.cursor.fetchall()

		except Exception as e:
			logging.exception("[%s]: Not able to get sensor alerts."
				% self.fileName)			

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a list of tuples (sensorAlertId, sensorId, timeReceived,
		# alertDelay, alertLevel, state, triggerAlways)
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

			self._releaseLock()

			return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		if alertSystemActive == 1:
			return True
		elif alertSystemActive == 0:
			return False


	# gets all details of a sensor alert that are for example used
	# to generate a notification
	#
	# return tuple of (hostname, description, timeReceived)
	# or None
	def getSensorAlertDetails(self, sensorAlertId):

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
			self.cursor.execute("SELECT nodeId, sensorId, timeReceived "
				+ "FROM sensorAlerts "
				+ "WHERE id = %s", (sensorAlertId, ))
			result = self.cursor.fetchall()
			nodeId = result[0][0]
			sensorId = result[0][1]
			timeReceived = result[0][2]

			self.cursor.execute("SELECT description "
				+ "FROM sensors "
				+ "WHERE id = %s", (sensorId, ))
			result = self.cursor.fetchall()
			description = result[0][0]

			self.cursor.execute("SELECT hostname "
				+ "FROM nodes "
				+ "WHERE id = %s", (nodeId, ))
			result = self.cursor.fetchall()
			hostname = result[0][0]

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "sensor alert details.")

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return tuple of (hostname, description, timeReceived)
		returnTuple = (hostname, description, timeReceived)
		return returnTuple


	# gets all alert levels from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllAlertLevels(self):

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
				+ "FROM alertLevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels.")

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (alertLevel)
		return result


	# gets all nodes from the database that are connected to the server
	#
	# return list of tuples of (nodeId)
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
				+ "all node ids.")

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (nodeId)
		return result


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

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (sensorId, nodeId,
		# lastStateUpdated, description)
		return result


	# gets all information of a sensor by its given id
	#
	# return a tuple of (sensorId, nodeId,
	# remoteSensorId, description, state, lastStateUpdated, alertDelay,
	# alertLevel, triggerAlways)
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
				+ "alertDelay, "
				+ "alertLevel, "
				+ "triggerAlways "
				+ "FROM sensors "
				+ "WHERE id = %s", (sensorId, ))

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

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a tuple of (sensorId, nodeId,
		# remoteSensorId, description, state, lastStateUpdated, alertDelay,
		# alertLevel, triggerAlways)
		return result[0]


	# gets the hostname of a node from the database when its id is given
	#
	# return hostname or None
	def getNodeHostnameById(self, nodeId):

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
			self.cursor.execute("SELECT hostname FROM nodes "
				+ "WHERE id = %s", (nodeId, ))

			result = self.cursor.fetchall()
			hostname = result[0][0]
		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "hostname for node from database.")

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return hostname


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = optionCount
	# list[1] = list(tuples of (type, value))
	# list[2] = nodeCount
	# list[3] = list(tuples of (nodeId, hostname, nodeType, connected))
	# list[4] = sensorCount
	# list[5] = list(tuples of (nodeId, sensorId, alertDelay,
	# alertLevel, description, lastStateUpdated, state))
	# list[6] = managerCount
	# list[7] = list(tuples of (nodeId, managerId, description))
	# list[8] = alertCount
	# list[9] = list(tuples of (nodeId, alertId, description))
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
			optionCount = len(optionsInformation)

			# get all nodes information
			self.cursor.execute("SELECT id, "
				+ "hostname, "
				+ "nodeType, "
				+ "connected "
				+ "FROM nodes")
			result = self.cursor.fetchall()
			nodesInformation = result
			nodeCount = len(nodesInformation)

			# get all sensors information
			self.cursor.execute("SELECT nodeId, "
				+ "id, "
				+ "alertDelay, "
				+ "alertLevel, "
				+ "description, "
				+ "lastStateUpdated, "
				+ "state "
				+ "FROM sensors")
			result = self.cursor.fetchall()
			sensorsInformation = result
			sensorCount = len(sensorsInformation)

			# get all managers information
			self.cursor.execute("SELECT nodeId, "
				+ "id, "
				+ "description "
				+ "FROM managers")
			result = self.cursor.fetchall()
			managersInformation = result
			managerCount = len(managersInformation)			

			# get all alerts information
			self.cursor.execute("SELECT nodeId, "
				+ "id, "
				+ "description "
				+ "FROM alerts")
			result = self.cursor.fetchall()
			alertsInformation = result
			alertCount = len(alertsInformation)

			# generate a list with all nodes information
			alertSystemInformation = list()
			alertSystemInformation.append(optionCount)
			alertSystemInformation.append(optionsInformation)
			alertSystemInformation.append(nodeCount)
			alertSystemInformation.append(nodesInformation)
			alertSystemInformation.append(sensorCount)
			alertSystemInformation.append(sensorsInformation)
			alertSystemInformation.append(managerCount)
			alertSystemInformation.append(managersInformation)
			alertSystemInformation.append(alertCount)
			alertSystemInformation.append(alertsInformation)

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all nodes information from database.")

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a list of
		# list[0] = optionCount
		# list[1] = list(tuples of (type, value))
		# list[2] = nodeCount
		# list[3] = list(tuples of (nodeId, hostname, nodeType, connected))
		# list[4] = sensorCount
		# list[5] = list(tuples of (nodeId, sensorId, alertDelay,
		# alertLevel, description, lastStateUpdated, state))
		# list[6] = managerCount
		# list[7] = list(tuples of (nodeId, managerId, description))
		# list[8] = alertCount
		# list[9] = list(tuples of (nodeId, alertId, description))		
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


# class for using postgresql as storage backend
#
# NOTE: to avoid problems with postgresql, the database names
# are not written in camel case but all in lower cases
# (problems occured when a database was created in camel case, which was
# converted to lowercase by postgresql but searched in information_schema
# via camel case because of case sensitivity)
class Postgresql(_Storage):

	def __init__(self, host, port, database, username, password, version):

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# version of server
		self.version = version

		# needed postgresql parameters
		self.host = host
		self.port = port
		self.database = database
		self.username = username
		self.password = password

		# postgresql lock
		self.dbLock = threading.Semaphore(1)

		self.conn = None
		self.cursor = None

		# connect to the database
		self._openConnection()

		# check if alert system tables exist already
		# if not => create them
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("SELECT count(*) FROM information_schema.tables "
			+ "WHERE table_name = %s "
			+ "and table_catalog = %s", ["options", self.database])
		optionsResult = self.cursor.fetchall()[0][0]
		self.cursor.execute("SELECT count(*) FROM information_schema.tables "
			+ "WHERE table_name = %s "
			+ "and table_catalog = %s", ["nodes", self.database])
		nodesResult = self.cursor.fetchall()[0][0]
		self.cursor.execute("SELECT count(*) FROM information_schema.tables "
			+ "WHERE table_name = %s "
			+ "and table_catalog = %s", ["sensors", self.database])
		sensorsResult = self.cursor.fetchall()[0][0]
		self.cursor.execute("SELECT count(*) FROM information_schema.tables "
			+ "WHERE table_name = %s "
			+ "and table_catalog = %s", ["sensoralerts", self.database])
		sensorAlertsResult = self.cursor.fetchall()[0][0]
		self.cursor.execute("SELECT count(*) FROM information_schema.tables "
			+ "WHERE table_name = %s "
			+ "and table_catalog = %s", ["alerts", self.database])
		alertsResult = self.cursor.fetchall()[0][0]
		self.cursor.execute("SELECT count(*) FROM information_schema.tables "
			+ "WHERE table_name = %s "
			+ "and table_catalog = %s", ["alertlevels", self.database])
		alertLevelsResult = self.cursor.fetchall()[0][0]
		self.cursor.execute("SELECT count(*) FROM information_schema.tables "
			+ "WHERE table_name = %s "
			+ "and table_catalog = %s", ["managers", self.database])
		managersResult = self.cursor.fetchall()[0][0]

		# close connection to the database
		self._closeConnection()

		if (optionsResult == 0
			or nodesResult == 0
			or sensorsResult == 0
			or sensorAlertsResult == 0
			or alertsResult == 0
			or alertLevelsResult == 0
			or managersResult == 0):
			self.createStorage()


	# internal function that connects to the postgresql server
	# (Needed? Mysql needs a new connection for each transaction
	# to get the current state in the database, for example when some program
	# changes the database directly. Does postgresql needs this too?)
	def _openConnection(self):
		# import the needed package
		import psycopg2

		self.conn = psycopg2.connect(host=self.host, port=self.port,
			user=self.username,	password=self.password, dbname=self.database)

		self.cursor = self.conn.cursor()


	# internal function that closes the connection to the postgresql server
	def _closeConnection(self):
		self.cursor.close()
		self.conn.close()
		self.cursor = None
		self.conn = None


	# internal function that checks if the username is known
	def _usernameInDb(self, username):

		# check if the username does exist => if not node is not known
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("SELECT id FROM nodes WHERE username = %s ",
			[username])
		result = self.cursor.fetchall()

		# return if username was found or not
		if len(result) == 0:
			return False
		else:
			return True


	# internal function that gets the id of a node when a username is given
	def _getNodeId(self, username):

		# check if the username does exist
		if self._usernameInDb(username):
			# get id of username
			# (because of problems with postgresql table names are written
			# in lowercase and not in camel case)
			self.cursor.execute("SELECT id FROM nodes WHERE username = %s ",
				[username])
			result = self.cursor.fetchall()

			return result[0][0]
		else:
			raise ValueError("Node id was not found.")


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.dbLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
		self.dbLock.release()


	# creates the database (should only be called if the database
	# does not exist)
	#
	# no return value but raise exception if it fails
	def createStorage(self):

		self._acquireLock()

		# connect to the database
		self._openConnection()

		# create options table
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("CREATE TABLE options ("
			+ "id SERIAL PRIMARY KEY, "
			+ "type VARCHAR(255) NOT NULL UNIQUE, "
			+ "value REAL NOT NULL)")

		# insert option to activate/deactivate alert system
		# (0 = deactivated, 1 = activated)
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("INSERT INTO options ("
			+ "type, "
			+ "value) VALUES (%s, %s)", ("alertSystemActive", 0))

		# insert version of server
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("INSERT INTO options ("
			+ "type, "
			+ "value) VALUES (%s, %s)", ("version", self.version))

		# create nodes table
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("CREATE TABLE nodes ("
			+ "id SERIAL PRIMARY KEY, "
			+ "hostname VARCHAR(255) NOT NULL, "
			+ "username VARCHAR(255) NOT NULL UNIQUE, "
			+ "nodeType VARCHAR(255) NOT NULL, "
			+ "connected INTEGER NOT NULL)")

		# create sensors table
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("CREATE TABLE sensors ("
			+ "id SERIAL PRIMARY KEY, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteSensorId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "lastStateUpdated INTEGER NOT NULL, "
			+ "alertDelay INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "triggerAlways INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create sensorAlerts table
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("CREATE TABLE sensoralerts ("
			+ "id SERIAL PRIMARY KEY, "
			+ "nodeId INTEGER NOT NULL, "
			+ "sensorId INTEGER NOT NULL, "
			+ "timeReceived INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id), "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create alerts table
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("CREATE TABLE alerts ("
			+ "id SERIAL PRIMARY KEY, "
			+ "nodeId INTEGER NOT NULL, "
			+ "remoteAlertId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create alertLevels table
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("CREATE TABLE alertlevels ("
			+ "id SERIAL PRIMARY KEY, "
			+ "nodeId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create managers table
		# (because of problems with postgresql table names are written
		# in lowercase and not in camel case)
		self.cursor.execute("CREATE TABLE managers ("
			+ "id SERIAL PRIMARY KEY, "
			+ "nodeId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")		

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()


	# adds a node if it does not exist or changes the registration
	# values if it does exist
	#
	# return True or False
	def addNode(self, username, hostname, nodeType):

		self._acquireLock()
		
		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		# check if node with the same username already exists
		# => only update information
		if self._usernameInDb(username):
			try:
				# (because of problems with postgresql table names are written
				# in lowercase and not in camel case)
				self.cursor.execute("UPDATE nodes SET "
					+ "hostname = %s, "
					+ "nodeType = %s, "
					+ "connected = 1 WHERE username = %s", (hostname, nodeType,
					username))
			except Exception as e:
				logging.exception("[%s]: Not able to add node."
					% self.fileName)

				self._releaseLock()

				return False

			# get the id of the node
			try:
				nodeId = self._getNodeId(username)
			except Exception as e:
				logging.exception("[%s]: Not able to add node." 
					% self.fileName)

				self._releaseLock()

				return False

			# remove old sensors data from database
			# (complete node will be newly added)
			# if type is sensor
			if nodeType == "sensor":
				try:
					# (because of problems with postgresql table names are
					# written in lowercase and not in camel case)
					self.cursor.execute("DELETE FROM sensors "
						+ "WHERE nodeId = %s", (nodeId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to add node." 
						% self.fileName)

					self._releaseLock()

					return False

			# remove old manager data from database
			# (complete node will be newly added)
			# if type is manager
			elif nodeType == "manager":
				try:
					# (because of problems with postgresql table names are
					# written in lowercase and not in camel case)
					self.cursor.execute("DELETE FROM managers "
						+ "WHERE nodeId = %s", (nodeId, ) )
				except Exception as e:
					logging.exception("[%s]: Not able to add node." 
						% self.fileName)

					self._releaseLock()

					return False

			# remove old alerts data from database
			# (complete node will be newly added)
			# if type is alert
			elif nodeType == "alert":
				try:
					# (because of problems with postgresql table names are
					# written in lowercase and not in camel case)
					self.cursor.execute("DELETE FROM alerts "
						+ "WHERE nodeId = %s", (nodeId, ))
					self.cursor.execute("DELETE FROM alertlevels "
						+ "WHERE nodeId = %s", (nodeId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to add node." 
						% self.fileName)

					self._releaseLock()

					return False	

		# if node does not exist => add it
		else:
			try:
				# (because of problems with postgresql table names are
				# written in lowercase and not in camel case)
				self.cursor.execute("INSERT INTO nodes ("
					+ "hostname, "
					+ "username, "
					+ "nodeType, "
					+ "connected) VALUES (%s, %s, %s, %s)",
					(hostname, username, nodeType, 1))
			except Exception as e:
				logging.exception("[%s]: Not able to add node."
					% self.fileName)

				self._releaseLock()

				return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds the data that is given by the node for the sensor to the database
	#
	# return True or False
	def addSensor(self, username, remoteSensorId, alertDelay, alertLevel,
		description, triggerAlways):

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
			logging.exception("[%s]: Not able to add sensor." % self.fileName)

			self._releaseLock()

			return False

		# check if trigger always has a valid value
		if (triggerAlways != 0 
			and triggerAlways != 1):
			logging.error("[%s]: triggerAlways not valid." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# add sensor to database
		try:
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("INSERT INTO sensors ("
				+ "nodeId, "
				+ "remoteSensorId, "
				+ "description, "
				+ "state, "
				+ "lastStateUpdated, "
				+ "alertDelay, "
				+ "alertLevel, "
				+ "triggerAlways) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
				(nodeId, remoteSensorId, description, 0, 0, alertDelay,
				alertLevel, triggerAlways))
		except Exception as e:
			logging.exception("[%s]: Not able to add sensor." % self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds the data that is given by the node for the alert to the database
	#
	# return True or False
	def addAlert(self, username, remoteAlertId, description):

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
			logging.exception("[%s]: Not able to add alert." % self.fileName)

			self._releaseLock()

			return False

		# add alert to database
		try:
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("INSERT INTO alerts ("
				+ "nodeId, "
				+ "remoteAlertId, "
				+ "description) VALUES (%s, %s, %s)", (nodeId,
				remoteAlertId, description))
		except Exception as e:
			logging.exception("[%s]: Not able to add alert." % self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds the alert levels that are given by the node for the alert
	# client to the database
	#
	# return True or False
	def addAlertLevels(self, username, alertLevels):

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
			logging.exception("[%s]: Not able to add alert levels."
				% self.fileName)

			self._releaseLock()

			return False

		# add alert levels to database
		try:
			for alertLevel in alertLevels:
				# (because of problems with postgresql table names are
				# written in lowercase and not in camel case)
				self.cursor.execute("INSERT INTO alertlevels ("
					+ "nodeId, "
					+ "alertLevel) VALUES (%s, %s)", (nodeId, alertLevel))
		except Exception as e:
			logging.exception("[%s]: Not able to add alert levels."
				% self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# adds the data that is given by the node for the manager to the database
	#
	# return True or False
	def addManager(self, username, description):

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
			logging.exception("[%s]: Not able to add manager." % self.fileName)

			self._releaseLock()

			return False

		# add manager to database
		try:
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("INSERT INTO managers ("
				+ "nodeId, "
				+ "description) VALUES (%s, %s)", (nodeId, description))
		except Exception as e:
			logging.exception("[%s]: Not able to add manager." % self.fileName)

			self._releaseLock()

			return False

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True		


	# checks if the given data of the node and the data in the database
	# are the same
	#
	# return True or False
	def checkNode(self, username, hostname, nodeType):

		self._acquireLock()

		# connect to the database
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to database."
				% self.fileName)

			self._releaseLock()

			return False

		# check if the username does exist
		if self._usernameInDb(username):
			# get hostname and nodeType of username
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT hostname, nodeType FROM nodes "
				+ "WHERE username = %s ", (username, ))
			result = self.cursor.fetchall()

			if (result[0][0] == hostname
				and result[0][1] == nodeType):

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return True

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return False


	# checks if the given data of the sensor and the data in the database
	# are the same
	#
	# return True or False
	def checkSensor(self, username, remoteSensorId, alertDelay, alertLevel,
		description, triggerAlways):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check sensor.")

			self._releaseLock()

			return False

		# (because of problems with postgresql table names are
		# written in lowercase and not in camel case)
		self.cursor.execute("SELECT alertDelay, "
			+ "alertLevel, "
			+ "description, "
			+ "triggerAlways "
			+ "FROM sensors "
			+ "WHERE nodeId = %s "
			+ "AND remoteSensorId = %s", (nodeId, remoteSensorId))

		result = self.cursor.fetchall()

		# check if the sensor was found
		if len(result) == 0:
			logging.error("[%s]: Sensor was not found." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# check if the sensor was found multiple times
		elif len(result) > 1:
			logging.error("[%s]: Sensor was found multiple times."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		if (result[0][0] == alertDelay
			and result[0][1] == alertLevel
			and result[0][2] == description
			and result[0][3] == triggerAlways):

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return True

		logging.error("[%s]: Sensor configuration does not match."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return False


	# checks if the given data of the alert and the data in the database
	# are the same
	#
	# return True or False
	def checkAlert(self, username, remoteAlertId, description):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert.")

			self._releaseLock()

			return False

		# (because of problems with postgresql table names are
		# written in lowercase and not in camel case)
		self.cursor.execute("SELECT description "
			+ "FROM alerts "
			+ "WHERE nodeId = %s "
			+ "AND remoteAlertId = %s", (nodeId, remoteAlertId))

		result = self.cursor.fetchall()

		# check if the alert was found
		if len(result) == 0:
			logging.error("[%s]: Alert was not found." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# check if the alert was found multiple times
		elif len(result) > 1:
			logging.error("[%s]: Alert was found multiple times."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		if result[0][0] == description:

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return True

		logging.error("[%s]: Alert configuration does not match."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return False


	# checks if the given alert levels of the alert client and the alert
	# levels in the database are the same
	#
	# return True or False
	def checkAlertLevels(self, username, alertLevels):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert.")

			self._releaseLock()

			return False

		# (because of problems with postgresql table names are
		# written in lowercase and not in camel case)
		self.cursor.execute("SELECT alertLevel "
			+ "FROM alertlevels "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the alert levels were found
		if len(result) == 0:
			logging.error("[%s]: Alert levels were not found." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# only check of all stored alert levels are in the list of
		# the received alert levels (because the count of the alert levels
		# are checked before => they all match if this check succeeds)
		for alertLevelTuple in result:
			if not alertLevelTuple[0] in alertLevels:

				logging.error("[%s]: Alert level configuration does not match."
					% self.fileName)

				# close connection to the database
				self._closeConnection()

				self._releaseLock()

				return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# checks if the given data of the manager and the data in the database
	# are the same
	#
	# return True or False
	def checkManager(self, username, description):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check manager.")

			self._releaseLock()

			return False

		# (because of problems with postgresql table names are
		# written in lowercase and not in camel case)
		self.cursor.execute("SELECT description "
			+ "FROM managers "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the manager was found
		if len(result) == 0:
			logging.error("[%s]: Manager was not found." % self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# check if the manager was found multiple times
		elif len(result) > 1:
			logging.error("[%s]: Manager was found multiple times."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		if (result[0][0] == description):

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return True

		logging.error("[%s]: Manager configuration does not match."
				% self.fileName)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return False


	# checks if the given sensor count of the node does match
	# the count in the database
	#
	# return True or False
	def checkSensorCount(self, username, sensorCount):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check sensor count.")

			self._releaseLock()

			return False		

		# get all sensors on this nodes
		# (because of problems with postgresql table names are
		# written in lowercase and not in camel case)
		self.cursor.execute("SELECT id FROM sensors "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the count does match the received count
		if len(result) != sensorCount:
			logging.error("[%s]: Sensor count does not match with database."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# checks if the given alert count of the node does match
	# the count in the database
	#
	# return True or False
	def checkAlertCount(self, username, alertCount):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert count.")

			self._releaseLock()

			return False		

		# get all alerts on this nodes
		# (because of problems with postgresql table names are
		# written in lowercase and not in camel case)
		self.cursor.execute("SELECT id FROM alerts "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the count does match the received count
		if len(result) != alertCount:
			logging.error("[%s]: Alert count does not match with database."
				% self.fileName)

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True


	# checks if the given alert level count of the node does match
	# the count in the database
	#
	# return True or False
	def checkAlertLevelCount(self, username, alertLevelCount):

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
			logging.exception("[%s]: Not able to " % self.fileName
				+ "check alert level count.")

			self._releaseLock()

			return False		

		# get all alert levels on this nodes
		# (because of problems with postgresql table names are
		# written in lowercase and not in camel case)
		self.cursor.execute("SELECT id FROM alertlevels "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()

		# check if the count does match the received count
		if len(result) != alertLevelCount:
			logging.error("[%s]: Alert level count " % self.fileName
				+ "does not match with database.")

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return False

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

		# get all sensors on this nodes
		# (because of problems with postgresql table names are
		# written in lowercase and not in camel case)
		self.cursor.execute("SELECT id FROM sensors "
			+ "WHERE nodeId = %s ", (nodeId, ))

		result = self.cursor.fetchall()
		sensorCount = len(result)

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return sensorCount


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
				# (because of problems with postgresql table names are
				# written in lowercase and not in camel case)
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

				# (because of problems with postgresql table names are
				# written in lowercase and not in camel case)
				self.cursor.execute("UPDATE sensors SET "
					+ "state = %s, "
					+ "lastStateUpdated = %s "
					+ "WHERE nodeId = %s "
					+ "AND remoteSensorId = %s",
					(stateTuple[1], int(time.time()), nodeId, stateTuple[0]))
			except Exception as e:
				logging.exception("[%s]: Not able to update sensor state."
					% self.fileName)

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

			# get sensorId from database
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
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

				return None

			sensorId = result[0][0]

		except Exception as e:
			logging.exception("[%s]: Not able to get sensorId from database."
				% self.fileName)

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return sensorId


	# adds a sensor alert to the database when the id of a node is given,
	# the id of the sensor that is used internally by the node and the state
	#
	# return True or False
	def addSensorAlert(self, nodeId, remoteSensorId, state):

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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("UPDATE sensors SET "
				+ "state = %s, "
				+ "lastStateUpdated = %s "
				+ "WHERE nodeId = %s "
				+ "AND remoteSensorId = %s",
				(state, int(time.time()), nodeId, remoteSensorId))

			# add sensor alert to database
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("INSERT INTO sensoralerts ("
				+ "nodeId, "
				+ "sensorId, "
				+ "timeReceived) VALUES (%s, %s, %s)",
				(nodeId, sensorId, int(time.time())))

		except Exception as e:
			logging.exception("[%s]: Not able to add sensor alert."
				% self.fileName)

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
	# return a list of tuples (sensorAlertId, sensorId, timeReceived,
	# alertDelay, alertLevel, state, triggerAlways)
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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT sensorAlerts.id, "
				+ "sensors.id, "
				+ "sensorAlerts.timeReceived, "
				+ "sensors.alertDelay, "
				+ "sensors.alertLevel, "
				+ "sensors.state, "
				+ "sensors.triggerAlways "
				+ "FROM sensoralerts "
				+ "INNER JOIN sensors "
				+ "ON sensoralerts.nodeId = sensors.nodeId "
				+ "AND sensoralerts.sensorId = sensors.id")
			result = self.cursor.fetchall()

		except Exception as e:
			logging.exception("[%s]: Not able to get sensor alerts."
				% self.fileName)			

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a list of tuples (sensorAlertId, sensorId, timeReceived,
		# alertDelay, alertLevel, state, triggerAlways)
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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("DELETE FROM sensoralerts WHERE id = %s",
					(sensorAlertId, ))
		except Exception as e:
			logging.exception("[%s]: Not able to delete sensor alert." 
				% self.fileName)

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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT value FROM options WHERE type = %s",
				("alertSystemActive", ))
			result = self.cursor.fetchall()
			alertSystemActive = result[0][0]

		except Exception as e:
			logging.exception("[%s]: Not able to check " % self.fileName
				+ "if alert system is active.")

			self._releaseLock()

			return False

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		if alertSystemActive == 1:
			return True
		elif alertSystemActive == 0:
			return False


	# gets all details of a sensor alert that are for example used
	# to generate a notification
	#
	# return tuple of (hostname, description, timeReceived)
	# or None
	def getSensorAlertDetails(self, sensorAlertId):

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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT nodeId, sensorId, timeReceived "
				+ "FROM sensoralerts "
				+ "WHERE id = %s", (sensorAlertId, ))
			result = self.cursor.fetchall()
			nodeId = result[0][0]
			sensorId = result[0][1]
			timeReceived = result[0][2]

			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT description "
				+ "FROM sensors "
				+ "WHERE id = %s", (sensorId, ))
			result = self.cursor.fetchall()
			description = result[0][0]

			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT hostname "
				+ "FROM nodes "
				+ "WHERE id = %s", (nodeId, ))
			result = self.cursor.fetchall()
			hostname = result[0][0]

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "sensor alert details.")

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return tuple of (hostname, description, timeReceived)
		returnTuple = (hostname, description, timeReceived)
		return returnTuple


	# gets all alert levels from the database
	#
	# return list of tuples of (alertLevel)
	# or None
	def getAllAlertLevels(self):

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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT alertLevel "
				+ "FROM alertlevels")
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all alert levels.")

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (alertLevel)
		return result


	# gets all nodes from the database that are connected to the server
	#
	# return list of tuples of (nodeId)
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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT id "
				+ "FROM nodes "
				+ "WHERE connected = %s", (1, ))
			result = self.cursor.fetchall()

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all node ids.")

			self._releaseLock()

			# return None if action failed
			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (nodeId)
		return result


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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = %s WHERE id = %s", (0, nodeId))			
		except Exception as e:

			logging.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as not connected." % nodeId)

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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("UPDATE nodes SET "
				+ "connected = %s WHERE id = %s", (1, nodeId))			
		except Exception as e:

			logging.exception("[%s]: Not able to mark " % self.fileName
				+ "node '%d' as connected." % nodeId)

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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
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

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return list of tuples of (sensorId, nodeId,
		# lastStateUpdated, description)
		return result


	# gets all information of a sensor by its given id
	#
	# return a tuple of (sensorId, nodeId,
	# remoteSensorId, description, state, lastStateUpdated, alertDelay,
	# alertLevel, triggerAlways)
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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT id, "
				+ "nodeId, "
				+ "remoteSensorId, "
				+ "description, "
				+ "state, "
				+ "lastStateUpdated, "
				+ "alertDelay, "
				+ "alertLevel, "
				+ "triggerAlways "
				+ "FROM sensors "
				+ "WHERE id = %s", (sensorId, ))

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

			# close connection to the database
			self._closeConnection()

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a tuple of (sensorId, nodeId,
		# remoteSensorId, description, state, lastStateUpdated, alertDelay,
		# alertLevel, triggerAlways)
		return result[0]


	# gets the hostname of a node from the database when its id is given
	#
	# return hostname or None
	def getNodeHostnameById(self, nodeId):

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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT hostname FROM nodes "
				+ "WHERE id = %s", (nodeId, ))

			result = self.cursor.fetchall()
			hostname = result[0][0]
		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "hostname for node from database.")

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return hostname


	# gets all information that the server has at the current moment
	#
	# return a list of
	# list[0] = optionCount
	# list[1] = list(tuples of (type, value))
	# list[2] = nodeCount
	# list[3] = list(tuples of (nodeId, hostname, nodeType, connected))
	# list[4] = sensorCount
	# list[5] = list(tuples of (nodeId, sensorId, alertDelay,
	# alertLevel, description, lastStateUpdated, state))
	# list[6] = managerCount
	# list[7] = list(tuples of (nodeId, managerId, description))
	# list[8] = alertCount
	# list[9] = list(tuples of (nodeId, alertId, description))
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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT type, "
				+ "value "
				+ "FROM options")
			result = self.cursor.fetchall()
			optionsInformation = result
			optionCount = len(optionsInformation)

			# get all nodes information
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT id, "
				+ "hostname, "
				+ "nodeType, "
				+ "connected "
				+ "FROM nodes")
			result = self.cursor.fetchall()
			nodesInformation = result
			nodeCount = len(nodesInformation)

			# get all sensors information
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT nodeId, "
				+ "id, "
				+ "alertDelay, "
				+ "alertLevel, "
				+ "description, "
				+ "lastStateUpdated, "
				+ "state "
				+ "FROM sensors")
			result = self.cursor.fetchall()
			sensorsInformation = result
			sensorCount = len(sensorsInformation)

			# get all managers information
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT nodeId, "
				+ "id, "
				+ "description "
				+ "FROM managers")
			result = self.cursor.fetchall()
			managersInformation = result
			managerCount = len(managersInformation)			

			# get all alerts information
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("SELECT nodeId, "
				+ "id, "
				+ "description "
				+ "FROM alerts")
			result = self.cursor.fetchall()
			alertsInformation = result
			alertCount = len(alertsInformation)

			# generate a list with all nodes information
			alertSystemInformation = list()
			alertSystemInformation.append(optionCount)
			alertSystemInformation.append(optionsInformation)
			alertSystemInformation.append(nodeCount)
			alertSystemInformation.append(nodesInformation)
			alertSystemInformation.append(sensorCount)
			alertSystemInformation.append(sensorsInformation)
			alertSystemInformation.append(managerCount)
			alertSystemInformation.append(managersInformation)
			alertSystemInformation.append(alertCount)
			alertSystemInformation.append(alertsInformation)

		except Exception as e:

			logging.exception("[%s]: Not able to get " % self.fileName
				+ "all nodes information from database.")

			self._releaseLock()

			return None

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		# return a list of
		# list[0] = optionCount
		# list[1] = list(tuples of (type, value))
		# list[2] = nodeCount
		# list[3] = list(tuples of (nodeId, hostname, nodeType, connected))
		# list[4] = sensorCount
		# list[5] = list(tuples of (nodeId, sensorId, alertDelay,
		# alertLevel, description, lastStateUpdated, state))
		# list[6] = managerCount
		# list[7] = list(tuples of (nodeId, managerId, description))
		# list[8] = alertCount
		# list[9] = list(tuples of (nodeId, alertId, description))		
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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
			self.cursor.execute("UPDATE options SET "
				+ "value = %s "
				+ "WHERE type = %s", (optionValue, optionType))

		except Exception as e:

			logging.exception("[%s]: Not able to update " % self.fileName
				+ "option in database.")

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
			# (because of problems with postgresql table names are
			# written in lowercase and not in camel case)
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