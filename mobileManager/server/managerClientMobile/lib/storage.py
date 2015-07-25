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
from events import EventSensorAlert, EventNewVersion, EventStateChange, \
	EventConnectedChange, EventSensorTimeOut, \
	EventNewOption, EventNewNode, EventNewSensor, EventNewAlert, \
	EventNewManager, EventChangeOption, EventChangeNode, EventChangeSensor, \
	EventChangeAlert, EventChangeManager, \
	EventDeleteNode, EventDeleteSensor, EventDeleteAlert, EventDeleteManager


# internal abstract class for new storage backends
class _Storage():

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

		# local copy of elements in the database (to make the update faster)
		self.options = list()
		self.nodes = list()
		self.sensors = list()
		self.alerts = list()
		self.managers = list()
		self.alertLevels = list()

		# mysql lock
		self.dbLock = threading.Semaphore(1)

		self.conn = None
		self.cursor = None

		# connect to the database
		self._openConnection()

		# delete all tables from the database to clear old data
		self.cursor.execute("DROP TABLE IF EXISTS internals")
		self.cursor.execute("DROP TABLE IF EXISTS options")
		self.cursor.execute("DROP TABLE IF EXISTS sensorsAlertLevels")
		self.cursor.execute("DROP TABLE IF EXISTS sensorAlerts")
		self.cursor.execute("DROP TABLE IF EXISTS sensors")
		self.cursor.execute("DROP TABLE IF EXISTS alertsAlertLevels")
		self.cursor.execute("DROP TABLE IF EXISTS alerts")
		self.cursor.execute("DROP TABLE IF EXISTS managers")
		self.cursor.execute("DROP TABLE IF EXISTS alertLevels")
		self.cursor.execute("DROP TABLE IF EXISTS nodes")
		self.cursor.execute("DROP TABLE IF EXISTS eventsNewVersion")
		self.cursor.execute("DROP TABLE IF EXISTS eventsSensorAlert")
		self.cursor.execute("DROP TABLE IF EXISTS eventsStateChange")
		self.cursor.execute("DROP TABLE IF EXISTS eventsConnectedChange")
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

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

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
		try:
			self._openConnection()
		except Exception as e:
			logging.exception("[%s]: Not able to connect to MySQL server." 
				% self.fileName)

			self._releaseLock()

			# remember to pass the exception
			raise

		# create internals table (used internally by the client)
		self.cursor.execute("CREATE TABLE internals ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "type VARCHAR(255) NOT NULL UNIQUE, "
			+ "value DOUBLE NOT NULL)")

		# insert server time field
		self.cursor.execute("INSERT INTO internals ("
			+ "type, "
			+ "value) VALUES (%s, %s)",
			("serverTime", 0.0))

		# create options table
		self.cursor.execute("CREATE TABLE options ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "type VARCHAR(255) NOT NULL UNIQUE, "
			+ "value DOUBLE NOT NULL)")

		# create nodes table
		self.cursor.execute("CREATE TABLE nodes ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "hostname VARCHAR(255) NOT NULL, "
			+ "nodeType VARCHAR(255) NOT NULL, "
			+ "instance VARCHAR(255) NOT NULL, "
			+ "connected INTEGER NOT NULL, "
			+ "version DOUBLE NOT NULL, "
			+ "rev INTEGER NOT NULL, "
			+ "newestVersion DOUBLE NOT NULL, "
			+ "newestRev INTEGER NOT NULL)")

		# create sensors table
		self.cursor.execute("CREATE TABLE sensors ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
			+ "description VARCHAR(255) NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "lastStateUpdated INTEGER NOT NULL, "
			+ "alertDelay INTEGER NOT NULL, "
			+ "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

		# create sensorAlerts table
		self.cursor.execute("CREATE TABLE sensorAlerts ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "sensorId INTEGER NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "description TEXT NOT NULL,"
			+ "timeReceived INTEGER NOT NULL, "
			+ "dataJson TEXT NOT NULL)")

		# create sensorsAlertLevels table
		self.cursor.execute("CREATE TABLE sensorsAlertLevels ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "sensorId INTEGER NOT NULL, "
			+ "alertLevel INTEGER NOT NULL, "
			+ "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

		# create alerts table
		self.cursor.execute("CREATE TABLE alerts ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "nodeId INTEGER NOT NULL, "
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

		# create alert levels table
		self.cursor.execute("CREATE TABLE alertLevels ("
			+ "alertLevel INTEGER PRIMARY KEY, "
			+ "name VARCHAR(255) NOT NULL, "
			+ "triggerAlways INTEGER NOT NULL, "
			+ "smtpActivated INTEGER NOT NULL, "
			+ "toAddr VARCHAR(255) NOT NULL)")

		# create events table
		self.cursor.execute("CREATE TABLE events ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "timeOccurred INTEGER NOT NULL, "
			+ "type VARCHAR(255) NOT NULL)")

		# create eventsSensorAlert table
		self.cursor.execute("CREATE TABLE eventsSensorAlert ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsStateChange table
		self.cursor.execute("CREATE TABLE eventsStateChange ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "hostname TEXT NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsConnectedChange table
		self.cursor.execute("CREATE TABLE eventsConnectedChange ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "hostname TEXT NOT NULL, "
			+ "nodeType TEXT NOT NULL, "
			+ "instance TEXT NOT NULL, "
			+ "connected INTEGER NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsSensorTimeOut table
		self.cursor.execute("CREATE TABLE eventsSensorTimeOut ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "hostname TEXT NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsSensorAlert table
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

		# create eventsNewOption table
		self.cursor.execute("CREATE TABLE eventsNewOption ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "type VARCHAR(255) NOT NULL, "
			+ "value DOUBLE NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewNode table
		self.cursor.execute("CREATE TABLE eventsNewNode ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "hostname TEXT NOT NULL, "
			+ "nodeType TEXT NOT NULL, "
			+ "instance TEXT NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewSensor table
		self.cursor.execute("CREATE TABLE eventsNewSensor ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "hostname TEXT NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "state INTEGER NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewAlert table
		self.cursor.execute("CREATE TABLE eventsNewAlert ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "hostname TEXT NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsNewManager table
		self.cursor.execute("CREATE TABLE eventsNewManager ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "hostname TEXT NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeOption table
		self.cursor.execute("CREATE TABLE eventsChangeOption ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "type VARCHAR(255) NOT NULL, "
			+ "oldValue DOUBLE NOT NULL, "
			+ "newValue DOUBLE NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeNode table
		self.cursor.execute("CREATE TABLE eventsChangeNode ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "oldHostname VARCHAR(255) NOT NULL, "
			+ "oldNodeType VARCHAR(255) NOT NULL, "
			+ "oldInstance VARCHAR(255) NOT NULL, "
			+ "oldVersion DOUBLE NOT NULL, "
			+ "oldRev INTEGER NOT NULL, "
			+ "newHostname VARCHAR(255) NOT NULL, "
			+ "newNodeType VARCHAR(255) NOT NULL, "
			+ "newInstance VARCHAR(255) NOT NULL, "
			+ "newVersion DOUBLE NOT NULL, "
			+ "newRev INTEGER NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeSensor table
		self.cursor.execute("CREATE TABLE eventsChangeSensor ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "oldAlertDelay INTEGER NOT NULL, "
			+ "oldDescription VARCHAR(255) NOT NULL, "
			+ "newAlertDelay INTEGER NOT NULL, "
			+ "newDescription VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeAlert table
		self.cursor.execute("CREATE TABLE eventsChangeAlert ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "oldDescription VARCHAR(255) NOT NULL, "
			+ "newDescription VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsChangeManager table
		self.cursor.execute("CREATE TABLE eventsChangeManager ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "oldDescription VARCHAR(255) NOT NULL, "
			+ "newDescription VARCHAR(255) NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsDeleteNode table
		self.cursor.execute("CREATE TABLE eventsDeleteNode ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "hostname TEXT NOT NULL, "
			+ "nodeType TEXT NOT NULL, "
			+ "instance TEXT NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsDeleteSensor table
		self.cursor.execute("CREATE TABLE eventsDeleteSensor ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsDeleteAlert table
		self.cursor.execute("CREATE TABLE eventsDeleteAlert ("
			+ "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
			+ "eventId INTEGER NOT NULL, "
			+ "description TEXT NOT NULL, "
			+ "FOREIGN KEY(eventId) REFERENCES events(id))")

		# create eventsDeleteManager table
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
	def updateServerInformation(self, options, nodes, sensors, alerts,
		managers, alertLevels, sensorAlerts):

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
		if sensors:
			try:
				self.cursor.execute("UPDATE internals SET "
					+ "value = %s "
					+ "WHERE type = %s",
					(sensors[0].serverTime, "serverTime"))

			except Exception as e:
				logging.exception("[%s]: Not able to update server time." 
					% self.fileName)

				self._releaseLock()

				return False


		# step one: delete all objects that do not exist anymore
		# (NOTE: first delete alerts, sensors and managers before
		# nodes because of the foreign key dependency; also delete
		# sensorAlerts before sensors and nodes)
		for option in list(self.options):
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
					logging.exception("[%s]: Not able to delete option." 
						% self.fileName)

					self._releaseLock()

					return False

				self.options.remove(option)

		# delete all sensor alerts that are older than the configured
		# life span
		try:
			self.cursor.execute("DELETE FROM sensorAlerts "
				+ "WHERE (timeReceived + "
				+ str(self.sensorAlertLifeSpan * 86400)
				+ ")"
				+ "<= %s",
				(int(time.time()), ))
		except Exception as e:
			logging.exception("[%s]: Not able to delete sensor alert." 
				% self.fileName)

			self._releaseLock()

			return False

		for sensor in list(self.sensors):
			# check if sensors stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements
			if not sensor in sensors:
				try:
					self.cursor.execute("DELETE FROM sensorsAlertLevels "
						+ "WHERE sensorId = %s",
						(sensor.sensorId, ))

					self.cursor.execute("DELETE FROM sensorAlerts "
						+ "WHERE sensorId = %s",
						(sensor.sensorId, ))

					self.cursor.execute("DELETE FROM sensors "
						+ "WHERE id = %s",
						(sensor.sensorId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to delete sensor." 
						% self.fileName)

					self._releaseLock()

					return False

				self.sensors.remove(sensor)

		for alert in list(self.alerts):
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
					logging.exception("[%s]: Not able to delete alert." 
						% self.fileName)

					self._releaseLock()

					return False

				self.alerts.remove(alert)

		for manager in list(self.managers):
			# check if managers stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements
			if not manager in managers:
				try:
					self.cursor.execute("DELETE FROM managers "
						+ "WHERE id = %s",
						(manager.managerId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to delete manager." 
						% self.fileName)

					self._releaseLock()

					return False

				self.managers.remove(manager)

		for node in list(self.nodes):
			# check if nodes stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements
			if not node in nodes:
				try:
					self.cursor.execute("DELETE FROM nodes "
						+ "WHERE id = %s",
						(node.nodeId, ))
				except Exception as e:
					logging.exception("[%s]: Not able to delete node." 
						% self.fileName)

					self._releaseLock()

					return False

				self.nodes.remove(node)

		for alertLevel in list(self.alertLevels):
			# check if alert levels stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements	
			if not alertLevel in alertLevels:
				try:
					self.cursor.execute("DELETE FROM alertLevels "
						+ "WHERE alertLevel = %s",
						(alertLevel.level, ))
				except Exception as e:
					logging.exception("[%s]: Not able to delete alert level." 
						% self.fileName)

					self._releaseLock()

					return False

				self.alertLevels.remove(alertLevel)

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

			self._releaseLock()

			return False


		# step two: update all existing objects
		for option in options:
			# when the option was found
			# => update it in the database
			if option in self.options:
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
			if node in self.nodes:
				try:
					self.cursor.execute("UPDATE nodes SET "
						+ "hostname = %s, "
						+ "nodeType = %s, "
						+ "instance = %s, "
						+ "connected = %s, "
						+ "version = %s, "
						+ "rev = %s, "
						+ "newestVersion = %s, "
						+ "newestRev = %s "
						+ "WHERE id = %s",
						(node.hostname, node.nodeType, node.instance,
						node.connected, node.version, node.rev, 
						node.newestVersion, node.newestRev, node.nodeId))
				except Exception as e:
					logging.exception("[%s]: Not able to update node."
						% self.fileName)

					self._releaseLock()

					return False

		for sensor in sensors:
			# when the sensor was found
			# => update it in the database
			if sensor in self.sensors:
				try:
					self.cursor.execute("UPDATE sensors SET "
						+ "nodeId = %s, "
						+ "description = %s, "
						+ "state = %s ,"
						+ "lastStateUpdated = %s ,"
						+ "alertDelay = %s "
						+ "WHERE id = %s",
						(sensor.nodeId, sensor.description, sensor.state,
						sensor.lastStateUpdated, sensor.alertDelay,
						sensor.sensorId))

					self.cursor.execute("DELETE FROM sensorsAlertLevels "
						+ "WHERE sensorId = %s",
						(sensor.sensorId, ))

					for sensorAlertLevel in sensor.alertLevels:
						self.cursor.execute("INSERT INTO sensorsAlertLevels ("
							+ "sensorId, "
							+ "alertLevel) "
							+ "VALUES (%s, %s)",
							(sensor.sensorId, sensorAlertLevel))

				except Exception as e:
					logging.exception("[%s]: Not able to update sensor."
						% self.fileName)

					self._releaseLock()

					return False

		for alert in alerts:
			# when the alert was found
			# => update it in the database
			if alert in self.alerts:
				try:
					self.cursor.execute("UPDATE alerts SET "
						+ "nodeId = %s, "
						+ "description = %s "
						+ "WHERE id = %s",
						(alert.nodeId, alert.description, alert.alertId))

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
			if manager in self.managers:
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
			if alertLevel in self.alertLevels:
				try:
					self.cursor.execute("UPDATE alertLevels SET "
						+ "name = %s, "
						+ "triggerAlways = %s, "
						+ "smtpActivated = %s, "
						+ "toAddr = %s "
						+ "WHERE alertLevel = %s",
						(alertLevel.name, alertLevel.triggerAlways,
						alertLevel.smtpActivated, alertLevel.toAddr,
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
			if not option in self.options:
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

				self.options.append(option)

		for node in nodes:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not node in self.nodes:
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
						+ "newestRev) "
						+ "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
						(node.nodeId, node.hostname, node.nodeType,
						node.instance, node.connected, node.version, node.rev,
						node.newestVersion, node.newestRev))
				except Exception as e:
					logging.exception("[%s]: Not able to add node."
						% self.fileName)

					self._releaseLock()

					return False

				self.nodes.append(node)

		for sensor in sensors:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not sensor in self.sensors:
				try:
					self.cursor.execute("INSERT INTO sensors ("
						+ "id, "
						+ "nodeId, "
						+ "description, "
						+ "state, "
						+ "lastStateUpdated, "
						+ "alertDelay) "
						+ "VALUES (%s, %s, %s, %s, %s, %s)",
						(sensor.sensorId, sensor.nodeId, sensor.description,
						sensor.state, sensor.lastStateUpdated,
						sensor.alertDelay))

					for sensorAlertLevel in sensor.alertLevels:
						self.cursor.execute("INSERT INTO sensorsAlertLevels ("
							+ "sensorId, "
							+ "alertLevel) "
							+ "VALUES (%s, %s)",
							(sensor.sensorId, sensorAlertLevel))

				except Exception as e:
					logging.exception("[%s]: Not able to add sensor."
						% self.fileName)

					self._releaseLock()

					return False

				self.sensors.append(sensor)

		for sensorAlert in sensorAlerts:
			# try to convert received data to json
			try:
				dataJson = json.dumps(sensorAlert.data)
			except Exception as e:
				logging.exception("[%s]: Not able to convert data "
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

			except Exception as e:
				logging.exception("[%s]: Not able to add sensor alert."
					% self.fileName)

				self._releaseLock()

				return False

		for alert in alerts:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not alert in self.alerts:
				try:
					self.cursor.execute("INSERT INTO alerts ("
						+ "id, "
						+ "nodeId, "
						+ "description) "
						+ "VALUES (%s, %s, %s)",
						(alert.alertId, alert.nodeId, alert.description))

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

				self.alerts.append(alert)

		for manager in managers:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not manager in self.managers:
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

				self.managers.append(manager)

		for alertLevel in alertLevels:
			# when it does not exist in the database
			# => add it and add to local database elements
			if not alertLevel in self.alertLevels:
				try:
					self.cursor.execute("INSERT INTO alertLevels ("
						+ "alertLevel, "
						+ "name, "
						+ "triggerAlways, "
						+ "smtpActivated, "
						+ "toAddr) "
						+ "VALUES (%s, %s, %s, %s, %s)",
						(alertLevel.level, alertLevel.name,
						alertLevel.triggerAlways, alertLevel.smtpActivated,
						alertLevel.toAddr))
				except Exception as e:
					logging.exception("[%s]: Not able to add alert level."
						% self.fileName)

					self._releaseLock()

					return False

				self.alertLevels.append(alertLevel)

		# add all events to the database (if any exists and it is activated
		# to store events)
		while (len(self.events) != 0
			and self.eventsLifeSpan > 0):

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
						+ "newHostname, "
						+ "newNodeType, "
						+ "newInstance, "
						+ "newVersion, "
						+ "newRev) "
						+ "VALUES "
						+ "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
						(eventId, event.oldHostname, event.oldNodeType,
						event.oldInstance, event.oldVersion,
						event.oldRev, event.newHostname,
						event.newNodeType, event.newInstance,
						event.newVersion, event.newRev))
				except Exception as e:
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
						+ "newAlertDelay, "
						+ "newDescription) "
						+ "VALUES "
						+ "(%s, %s, %s, %s, %s)",
						(eventId, event.oldAlertDelay, event.oldDescription,
						event.newAlertDelay, event.newDescription))
				except Exception as e:
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
						+ "newDescription) "
						+ "VALUES "
						+ "(%s, %s, %s)",
						(eventId, event.oldDescription, event.newDescription))
				except Exception as e:
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

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
					logging.exception("[%s]: Not able to add event."
						% self.fileName)

					self._releaseLock()

					return False

			else:
				logging.error("[%s]: Used event not known."
					% self.fileName)

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True