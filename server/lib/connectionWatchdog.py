#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import threading
import time
import logging
import os
import json
from localObjects import SensorTimeoutSensor, NodeTimeoutSensor


# This class checks handles all timeouts of nodes, sensors, and so on.
class ConnectionWatchdog(threading.Thread):

	def __init__(self, globalData, connectionTimeout):
		threading.Thread.__init__(self)

		# get global configured data
		self.globalData = globalData
		self.serverSessions = self.globalData.serverSessions
		self.storage = self.globalData.storage
		self.smtpAlert = self.globalData.smtpAlert
		self.managerUpdateExecuter = self.globalData.managerUpdateExecuter
		self.sensorAlertExecuter = self.globalData.sensorAlertExecuter

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# Get value for the configured timeout of a session.
		self.connectionTimeout = connectionTimeout
		self.timeoutReminderTime = self.globalData.timeoutReminderTime

		# set exit flag as false
		self.exitFlag = False

		# The node id of this server instance in the database.
		self.serverNodeId = None

		# Set up needed data structures for sensor timeouts.
		self.timeoutSensorIds = set()
		self.sensorTimeoutSensor = None
		self.lastSensorTimeoutReminder = 0.0

		# Set up needed data structures for node timeouts.
		self.timeoutNodeIds = set()
		self.nodeTimeoutSensor = None
		self.lastNodeTimeoutReminder = 0.0
		self.nodeTimeoutLock = threading.BoundedSemaphore(1)

		# Get activated internal sensors.
		for internalSensor in self.globalData.internalSensors:
			if isinstance(internalSensor, SensorTimeoutSensor):
				# Use set of sensor timeout sensor if it is activated.
				self.timeoutSensorIds = internalSensor.timeoutSensorIds
				self.sensorTimeoutSensor = internalSensor
			elif isinstance(internalSensor, NodeTimeoutSensor):
				# Use set of node timeout sensor if it is activated.
				self.timeoutNodeIds = internalSensor._timeoutNodeIds
				self.nodeTimeoutSensor = internalSensor


	# Internal function that acquires the node timeout sensor lock.
	def _acquireNodeTimeoutLock(self):
		logging.debug("[%s]: Acquire node timeout sensor lock."
			% self.fileName)
		self.nodeTimeoutLock.acquire()


	# Internal function that releases the node timeout sensor lock.
	def _releaseNodeTimeoutLock(self):
		logging.debug("[%s]: Release node timeout sensor lock."
			% self.fileName)
		self.nodeTimeoutLock.release()


	# Internal function that processes new occurred node timeouts
	# and raises alarm.
	def _processNewNodeTimeouts(self):

		# Check all server sessions if the connection timed out.
		for serverSession in self.serverSessions:

			# Check if client communication object exists.
			if serverSession.clientComm == None:
				continue

			# Check if the time of the data last received lies
			# too far in the past => kill connection.
			if ((time.time() - serverSession.clientComm.lastRecv)
				>= self.connectionTimeout):

				logging.error("[%s]: Connection to " % self.fileName
					+ "client timed out. Closing connection (%s:%d)."
					% (serverSession.clientAddress,
					serverSession.clientPort))

				serverSession.closeConnection()

				nodeId = serverSession.clientComm.nodeId
				if (nodeId is None
					or nodeId in self.timeoutNodeIds):
					continue

				self.addNodeTimeout(nodeId)


	# Internal function that processes old occurred node timeouts
	# and raises alarm when they are no longer timed out.
	def _processOldNodeTimeouts(self):

		# Check all server sessions if a timed out connection reconnected.
		for serverSession in self.serverSessions:

			# Check if client communication object exists.
			if serverSession.clientComm == None:
				continue

			nodeId = serverSession.clientComm.nodeId
			if (nodeId is None
				or not nodeId in self.timeoutNodeIds):
				continue

			self.removeNodeTimeout(nodeId)


	# Internal function that processes new occurred sensor timeouts
	# and raises alarm.
	def _processNewSensorTimeouts(self, sensorsTimeoutList):

		processSensorAlerts = False

		# Needed to check if a sensor timeout has occurred when there was
		# no timeout before.
		wasEmpty = True
		if self.timeoutSensorIds:
			wasEmpty = False

		# Generate an alert for every timed out sensor
		# (logging + internal "sensor timeout" sensor).
		for sensorTuple in sensorsTimeoutList:
			sensorId = sensorTuple[0]
			nodeId = sensorTuple[1]
			hostname = self.storage.getNodeHostnameById(nodeId)
			lastStateUpdated = sensorTuple[2]
			description = sensorTuple[3]
			if hostname is None:
				logging.error("[%s]: Could not " % self.fileName
					+ "get hostname for node from database.")
				self.timeoutSensorIds.add(sensorId)
				continue

			logging.critical("[%s]: Sensor " % self.fileName
					+ "with description '%s' from host '%s' timed out. "
					% (description, hostname)
					+ "Last state received at %s"
					% time.strftime("%D %H:%M:%S",
					time.localtime(lastStateUpdated)))

			# Check if sensor time out occurred for the first time
			# and internal sensor is activated.
			# => Trigger a sensor alert.
			if (not sensorId in self.timeoutSensorIds
				and not self.sensorTimeoutSensor is None):

					# If internal sensor is in state "normal", change the
					# state to "triggered" with the raised sensor alert.
					changeState = False
					if self.sensorTimeoutSensor.state == 0:

						self.sensorTimeoutSensor.state = 1
						changeState = True

					# Create message for sensor alert.
					message = "Sensor '%s' on host '%s' timed out." \
						% (description, hostname)
					dataJson = json.dumps({"message": message})

					# Add sensor alert to database for processing.
					if self.storage.addSensorAlert(
						self.sensorTimeoutSensor.nodeId,
						self.sensorTimeoutSensor.remoteSensorId,
						1,
						changeState,
						dataJson):

						processSensorAlerts = True

					else:
						logging.error("[%s]: Not able to add sensor alert "
							% self.fileName
							+ "for internal sensor timeout sensor.")

			self.timeoutSensorIds.add(sensorId)

		# Wake up sensor alert executer to process sensor alerts.
		if processSensorAlerts:
			self.sensorAlertExecuter.sensorAlertEvent.set()

		# Start sensor timeout reminder timer when the sensor timeout list
		# was empty before.
		if wasEmpty and self.timeoutSensorIds:
			self.lastSensorTimeoutReminder = time.time()


	# Internal function that processes old occurred sensor timeouts
	# and raises alarm when they are no longer timed out.
	def _processOldSensorTimeouts(self, sensorsTimeoutList):

		processSensorAlerts = False

		# check if a timed out sensor has reconnected and
		# updated its state and generate a notification
		for sensorId in set(self.timeoutSensorIds):

			# Skip if an old timed out sensor is still timed out.
			found = False
			for sensorTimeoutTuple in sensorsTimeoutList:
				timedOutSensorId = sensorTimeoutTuple[0]
				if sensorId == timedOutSensorId:
					found = True
					break
			if found:
				continue

			# Sensor is no longer timed out.
			self.timeoutSensorIds.remove(sensorId)

			# Get a tuple of (sensorId, nodeId,
			# remoteSensorId, description, state,
			# lastStateUpdated, alertDelay) for timed out sensor.
			sensorTuple = self.storage.getSensorInformation(
				sensorId)

			# Check if the sensor could be found in the database.
			if sensorTuple is None:
				logging.error("[%s]: Could not get " % self.fileName
					+ "sensor with id %d from database."
					% sensorId)
				continue

			nodeId = sensorTuple[1]
			hostname = self.storage.getNodeHostnameById(nodeId)
			description = sensorTuple[3]
			lastStateUpdated = sensorTuple[5]

			logging.critical("[%s]: Sensor " % self.fileName
				+ "with description '%s' from host '%s' has "
				% (description, hostname)
				+ "reconnected. Last state received at %s"
				% time.strftime("%D %H:%M:%S",
				time.localtime(lastStateUpdated)))

			# Check if internal sensor is activated.
			# => Trigger a sensor alert.
			if not self.sensorTimeoutSensor is None:

				# If internal sensor is in state "triggered" and
				# no sensor is timed out at the moment, change the
				# state to "normal" with the raised sensor alert.
				changeState = False
				if (self.sensorTimeoutSensor.state == 1
					and not self.timeoutSensorIds):

					self.sensorTimeoutSensor.state = 0
					changeState = True

				# Create message for sensor alert.
				message = "Sensor '%s' on host '%s' reconnected." \
					% (description, hostname)
				dataJson = json.dumps({"message": message})

				if self.storage.addSensorAlert(
					self.sensorTimeoutSensor.nodeId,
					self.sensorTimeoutSensor.remoteSensorId,
					0,
					changeState,
					dataJson):

					processSensorAlerts = True

				else:
					logging.error("[%s]: Not able to add sensor alert "
						% self.fileName
						+ "for internal sensor timeout sensor.")

		# Wake up sensor alert executer to process sensor alerts.
		if processSensorAlerts:
			self.sensorAlertExecuter.sensorAlertEvent.set()

		# Reset sensor timeout reminder timer when the sensor timeout list
		# is empty.
		if not self.timeoutSensorIds:
			self.lastSensorTimeoutReminder = 0.0


	# Internal function that checks if a reminder
	# of a timeout has to be raised.
	def _processTimeoutReminder(self):

		processSensorAlerts = False

		# Reset timeout reminder if necessary.
		if (not self.timeoutSensorIds
			and self.lastSensorTimeoutReminder != 0.0):
			self.lastSensorTimeoutReminder = 0.0

		# When sensors are still timed out check if a reminder
		# has to be raised.
		elif self.timeoutSensorIds:

			# Check if a sensor timeout reminder has to be raised.
			if ((time.time() - self.lastSensorTimeoutReminder)
				>= self.timeoutReminderTime):

				self.lastSensorTimeoutReminder = time.time()

				# Raise sensor alert for internal sensor timeout sensor.
				if not self.sensorTimeoutSensor is None:

					# Create message for sensor alert.
					message = "%d sensor(s) still timed out:" \
						% len(self.timeoutSensorIds)
					for sensorId in self.timeoutSensorIds:

						# Get a tuple of (sensorId, nodeId,
						# remoteSensorId, description, state,
						# lastStateUpdated, alertDelay) for timed out sensor.
						sensorTuple = self.storage.getSensorInformation(
							sensorId)

						# Check if the sensor could be found in the database.
						if sensorTuple is None:
							logging.error("[%s]: Could not get "
								% self.fileName
								+ "sensor with id %d from database."
								% sensorId)
							continue

						# Get sensor details.
						nodeId = sensorTuple[1]
						hostname = self.storage.getNodeHostnameById(nodeId)
						description = sensorTuple[3]
						lastStateUpdated = sensorTuple[5]
						lastStateUpdateStr = time.strftime("%D %H:%M:%S",
							time.localtime(lastStateUpdated))
						if hostname is None:
							logging.error("[%s]: Could not " % self.fileName
								+ "get hostname for node from database.")
							continue

						message += " Host: '%s', " \
							% hostname \
							+ "Sensor: '%s', " \
							% description \
							+ "Last seen: %s;" \
							% lastStateUpdateStr

					dataJson = json.dumps({"message": message})

					# Add sensor alert to database for processing.
					if self.storage.addSensorAlert(
						self.sensorTimeoutSensor.nodeId,
						self.sensorTimeoutSensor.remoteSensorId,
						1,
						False,
						dataJson):

						processSensorAlerts = True

					else:
						logging.error("[%s]: Not able to add sensor alert "
							% self.fileName
							+ "for internal sensor timeout sensor.")

		# Reset timeout reminder if necessary.
		if (not self.timeoutNodeIds
			and self.lastNodeTimeoutReminder != 0.0):
			self.lastNodeTimeoutReminder = 0.0

		# When nodes are still timed out check if a reminder
		# has to be raised.
		elif self.timeoutNodeIds:

			# Check if a node timeout reminder has to be raised.
			if ((time.time() - self.lastNodeTimeoutReminder)
				>= self.timeoutReminderTime):

				self.lastNodeTimeoutReminder = time.time()

				# Raise sensor alert for internal node timeout sensor.
				if not self.nodeTimeoutSensor is None:

					# Create message for sensor alert.
					message = "%d node(s) still timed out:" \
						% len(self.timeoutNodeIds)
					for nodeId in self.timeoutNodeIds:

						nodeTuple = self.storage.getNodeById(nodeId)
						if nodeTuple is None:
							logging.error("[%s]: Could not " % self.fileName
								+ "get node with id %d from database."
								% nodeId)
							continue
						instance = nodeTuple[4]
						username = nodeTuple[2]
						hostname = nodeTuple[1]

						message += " Node: '%s, " \
							% str(instance) \
							+ "Username: '%s', " \
							% str(username) \
							+ "Hostname: '%s';" \
							% str(hostname)

					dataJson = json.dumps({"message": message})

					# Add sensor alert to database for processing.
					if self.storage.addSensorAlert(
						self.nodeTimeoutSensor.nodeId,
						self.nodeTimeoutSensor.remoteSensorId,
						1,
						False,
						dataJson):

						processSensorAlerts = True

					else:
						logging.error("[%s]: Not able to add sensor alert "
							% self.fileName
							+ "for internal node timeout sensor.")

		# Wake up sensor alert executer to process sensor alerts.
		if processSensorAlerts:
			self.sensorAlertExecuter.sensorAlertEvent.set()


	# Internal function that synchronizes actual connected nodes and
	# as connected marked nodes in the database (can happen if
	# for example the server was restarted).
	def _syncDbAndConnections(self):

		sendManagerUpdates = False

		# Get all node ids from database that are connected.
		# Returns a list of nodeIds.
		nodeIds = self.storage.getAllConnectedNodeIds()
		if nodeIds == None:
			logging.error("[%s]: Could not get node " % self.fileName
				+ "ids from database.")
		else:

			# Check if node marked as connected got a connection
			# to the server.
			for nodeId in nodeIds:
				found = False

				# Skip node id of this server instance.
				if nodeId == self.serverNodeId:
					continue

				# Skip node ids that have a active connection
				# to this server.
				for serverSession in self.serverSessions:

					# Check if client communication object exists.
					if serverSession.clientComm == None:
						continue

					if serverSession.clientComm.nodeId == nodeId:
						found = True
						break
				if found:
					continue

				# If no server session was found with the node id
				# => node is not connected to the server.
				logging.debug("[%s]: Marking node " % self.fileName
					+ "'%d' as not connected." % nodeId)

				if not self.storage.markNodeAsNotConnected(nodeId):
					logging.error("[%s]: Could not " % self.fileName
						+ "mark node as not connected in database.")

				sendManagerUpdates = True

		# Wake up manager update executer and force to send an update to
		# all managers.
		if sendManagerUpdates:
			self.managerUpdateExecuter.forceStatusUpdate = True
			self.managerUpdateExecuter.managerUpdateEvent.set()


	# Public function that sets a node as "timed out" by its id.
	def addNodeTimeout(self, nodeId):

		self._acquireNodeTimeoutLock()

		processSensorAlerts = False

		# Needed to check if a node timeout has occurred when there was
		# no timeout before.
		wasEmpty = True
		if self.timeoutNodeIds:
			wasEmpty = False

		# Only process node timeout if we do not already know about it.
		if not nodeId in self.timeoutNodeIds:

			nodeTuple = self.storage.getNodeById(nodeId)
			if nodeTuple is None:
				logging.error("[%s]: Could not " % self.fileName
					+ "get node with id %d from database."
					% nodeId)
				logging.error("[%s]: Node with id %d "
					% (self.fileName, nodeId)
					+ "timed out (not able to determine persistence).")

				self._releaseNodeTimeoutLock()
				return

			# Check if client is not persistent and therefore
			# allowed to timeout or disconnect.
			# => Ignore timeout/disconnect.
			persistent = nodeTuple[8]
			if persistent == 0:

				self._releaseNodeTimeoutLock()
				return

			instance = nodeTuple[4]
			username = nodeTuple[2]
			hostname = nodeTuple[1]

			self.timeoutNodeIds.add(nodeId)

			logging.error("[%s]: Node '%s' with username '%s' on host '%s' "
				% (self.fileName, instance, username, hostname)
				+ "timed out.")

			if not self.nodeTimeoutSensor is None:

				# If internal sensor is in state "normal", change the
				# state to "triggered" with the raised sensor alert.
				changeState = False
				if self.nodeTimeoutSensor.state == 0:

					self.nodeTimeoutSensor.state = 1
					changeState = True

				# Create message for sensor alert.
				message = "Node '%s' with username '%s' on host '%s' " \
					% (str(instance), str(username), str(hostname)) \
					+ "timed out."
				dataJson = json.dumps({"message": message})

				# Add sensor alert to database for processing.
				if self.storage.addSensorAlert(
					self.nodeTimeoutSensor.nodeId,
					self.nodeTimeoutSensor.remoteSensorId,
					1,
					changeState,
					dataJson):

					processSensorAlerts = True

				else:
					logging.error("[%s]: Not able to add sensor alert "
						% self.fileName
						+ "for internal node timeout sensor.")

		# Wake up sensor alert executer to process sensor alerts.
		if processSensorAlerts:
			self.sensorAlertExecuter.sensorAlertEvent.set()

		# Start node timeout reminder timer when the sensor timeout list
		# was empty before.
		if wasEmpty and self.timeoutNodeIds:
			self.lastNodeTimeoutReminder = time.time()

		self._releaseNodeTimeoutLock()


	# Public function that clears a node from "timed out" by its id.
	def removeNodeTimeout(self, nodeId):

		self._acquireNodeTimeoutLock()

		processSensorAlerts = False

		# Only process node timeout if we know about it.
		if nodeId in self.timeoutNodeIds:

			self.timeoutNodeIds.remove(nodeId)

			nodeTuple = self.storage.getNodeById(nodeId)
			if nodeTuple is None:
				logging.error("[%s]: Could not " % self.fileName
					+ "get node with id %d from database."
					% nodeId)
				logging.error("[%s]: Node with id %d "
					% (self.fileName, nodeId)
					+ "reconnected.")

				self._releaseNodeTimeoutLock()
				return

			instance = nodeTuple[4]
			username = nodeTuple[2]
			hostname = nodeTuple[1]

			logging.error("[%s]: Node '%s' with username '%s' on host '%s' "
				% (self.fileName, instance, username, hostname)
				+ "reconnected.")

			if not self.nodeTimeoutSensor is None:

				# If internal sensor is in state "triggered", change the
				# state to "normal" with the raised sensor alert.
				changeState = False
				if self.nodeTimeoutSensor.state == 1:

					self.nodeTimeoutSensor.state = 0
					changeState = True

				# Create message for sensor alert.
				message = "Node '%s' with username '%s' on host '%s' " \
					% (str(instance), str(username), str(hostname)) \
					+ "reconnected."
				dataJson = json.dumps({"message": message})

				# Add sensor alert to database for processing.
				if self.storage.addSensorAlert(
					self.nodeTimeoutSensor.nodeId,
					self.nodeTimeoutSensor.remoteSensorId,
					0,
					changeState,
					dataJson):

					processSensorAlerts = True

				else:
					logging.error("[%s]: Not able to add sensor alert "
						% self.fileName
						+ "for internal node timeout sensor.")

		else:
			logging.error("[%s]: Node with id %d "
				% (self.fileName, nodeId)
				+ "reconnected. Did not know about its timeout.")

		# Wake up sensor alert executer to process sensor alerts.
		if processSensorAlerts:
			self.sensorAlertExecuter.sensorAlertEvent.set()

		# Reset node timeout reminder timer when the sensor timeout list
		# is empty.
		if not self.timeoutNodeIds:
			self.lastNodeTimeoutReminder = 0.0

		self._releaseNodeTimeoutLock()


	def run(self):

		uniqueID = self.storage.getUniqueID()
		self.serverNodeId = self.storage.getNodeId(uniqueID)

		while 1:
			# wait 5 seconds before checking time of last received data
			for i in range(5):
				if self.exitFlag:
					logging.info("[%s]: Exiting ConnectionWatchdog."
						% self.fileName)
					return
				time.sleep(1)

			# Data needed to update internal timeout sensors.
			updateStateList = list()

			# Synchronize view on connected nodes (actual connected nodes
			# and database)
			self._syncDbAndConnections()

			# Check all server sessions if the connection timed out.
			self._processNewNodeTimeouts()

			# Process nodes that timed out but reconnected.
			self._processOldNodeTimeouts()

			# Create update tuple for internal node timeout sensor.
			if not self.nodeTimeoutSensor is None:
				updateTuple = (self.nodeTimeoutSensor.remoteSensorId,
					self.nodeTimeoutSensor.state)
				updateStateList.append(updateTuple)

			# Get all sensors that have timed out.
			# Data: list of tuples of (sensorId, nodeId,
			# lastStateUpdated, description)
			sensorsTimeoutList = self.storage.getSensorsUpdatedOlderThan(
				int(time.time()) - (2 * self.connectionTimeout))

			# Process occurred sensor time outs (and if they newly occurred).
			self._processNewSensorTimeouts(sensorsTimeoutList)

			# Process sensors that timed out but reconnected.
			self._processOldSensorTimeouts(sensorsTimeoutList)

			# Create update tuple for internal sensor timeout sensor.
			if not self.sensorTimeoutSensor is None:
				updateTuple = (self.sensorTimeoutSensor.remoteSensorId,
					self.sensorTimeoutSensor.state)
				updateStateList.append(updateTuple)

			# Update state of internal timeout sensors in order to avoid
			# timeouts of these sensor.
			if updateStateList:

				logging.debug("[%s]: Update sensor state "
					% self.fileName
					+ "for internal timeout sensors.")

				if not self.storage.updateSensorState(self.serverNodeId,
					updateStateList):

					logging.error("[%s]: Not able to update sensor state "
						% self.fileName
						+ "for internal timeout sensors.")

			# Process reminder of timeouts.
			self._processTimeoutReminder()


	# sets the exit flag to shut down the thread
	def exit(self):
		self.exitFlag = True
		return