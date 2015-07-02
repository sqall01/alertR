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


	# updates the received server information
	#
	# return True or False
	def updateServerInformation(self, options, nodes, sensors, alerts,
		managers, alertLevels):
		raise NotImplemented("Function not implemented yet.")


# class for using mysql as storage backend
class Mysql(_Storage):

	def __init__(self, host, port, database, username, password):

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# needed mysql parameters
		self.host = host
		self.port = port
		self.database = database
		self.username = username
		self.password = password

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

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()


	# updates the received server information
	#
	# return True or False
	def updateServerInformation(self, options, nodes, sensors, alerts,
		managers, alertLevels):

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
		# nodes because of the foreign key dependency)
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

		for sensor in list(self.sensors):
			# check if sensors stored in the database do
			# not exist anymore in the received data
			# => delete from database and from local database elements
			if not sensor in sensors:
				try:
					self.cursor.execute("DELETE FROM sensorsAlertLevels "
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

		# commit all changes
		self.conn.commit()

		# close connection to the database
		self._closeConnection()

		self._releaseLock()

		return True