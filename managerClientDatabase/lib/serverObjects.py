#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import os
import logging
import time
from localObjects import SensorDataType
from events import EventSensorAlert, EventNewVersion
from events import EventStateChange, EventConnectedChange, EventSensorTimeOut
from events import EventNewOption, EventNewNode, EventNewSensor
from events import EventNewAlert, EventNewManager
from events import EventChangeOption, EventChangeNode, EventChangeSensor
from events import EventChangeAlert, EventChangeManager
from events import EventDeleteNode, EventDeleteSensor, EventDeleteAlert
from events import EventDeleteManager


# this class represents an option of the server
class Option:

	def __init__(self):
		self.type = None
		self.value = None


# this class represents an node/client of the alert system
# which can be either a sensor, alert or manager
class Node:

	def __init__(self):
		self.nodeId = None
		self.hostname = None
		self.nodeType = None
		self.instance = None
		self.connected = None
		self.version = None
		self.rev = None
		self.username = None
		self.persistent = None

		# used by mobile manager only:
		# newest known version
		self.newestVersion = -1.0
		self.newestRev = -1

		# flag that marks this object as checked
		# (is used to verify if this object is still connected to the server)
		self.checked = False


	# This function copies all attributes of the given node to this object.
	def deepCopy(self, node):
		self.nodeId = node.nodeId
		self.hostname = node.hostname
		self.nodeType = node.nodeType
		self.instance = node.instance
		self.connected = node.connected
		self.version = node.version
		self.rev = node.rev
		self.username = node.username
		self.persistent = node.persistent


# this class represents a sensor client of the alert system
class Sensor:

	def __init__(self):
		self.nodeId = None
		self.sensorId = None
		self.remoteSensorId = None
		self.alertDelay = None
		self.alertLevels = list()
		self.description = None
		self.lastStateUpdated = None
		self.state = None
		self.dataType = None
		self.data = None

		# flag that marks this object as checked
		# (is used to verify if this object is still connected to the server)
		self.checked = False


	# This function copies all attributes of the given sensor to this object.
	def deepCopy(self, sensor):
		self.nodeId = sensor.nodeId
		self.sensorId = sensor.sensorId
		self.remoteSensorId = sensor.remoteSensorId
		self.alertDelay = sensor.alertDelay
		self.alertLevels = list(sensor.alertLevels)
		self.description = sensor.description
		self.lastStateUpdated = sensor.lastStateUpdated
		self.state = sensor.state
		self.dataType = sensor.dataType
		self.data = sensor.data


# this class represents a manager client of the alert system
class Manager:

	def __init__(self):
		self.nodeId = None
		self.managerId = None
		self.description = None

		# flag that marks this object as checked
		# (is used to verify if this object is still connected to the server)
		self.checked = False


	# This function copies all attributes of the given manager to this object.
	def deepCopy(self, manager):
		self.nodeId = manager.nodeId
		self.managerId = manager.managerId
		self.description = manager.description


# this class represents an alert client of the alert system
class Alert:

	def __init__(self):
		self.nodeId = None
		self.alertId = None
		self.remoteAlertId = None
		self.alertLevels = list()
		self.description = None

		# flag that marks this object as checked
		# (is used to verify if this object is still connected to the server)
		self.checked = False


	# This function copies all attributes of the given alert to this object.
	def deepCopy(self, alert):
		self.nodeId = alert.nodeId
		self.alertId = alert.alertId
		self.remoteAlertId = alert.remoteAlertId
		self.alertLevels = list(alert.alertLevels)
		self.description = alert.description


# this class represents a triggered sensor alert of the alert system
class SensorAlert:

	def __init__(self):

		# Are rules for this sensor alert activated (true or false)?
		self.rulesActivated = None

		# If rulesActivated = true => always set to -1.
		self.sensorId = None

		# State of the sensor alert ("triggered" = 1; "normal" = 0).
		# If rulesActivated = true => always set to 1.
		self.state = None

		# Description of the sensor that raised this sensor alert.
		self.description = None

		# Time this sensor alert was received.
		self.timeReceived = None

		# List of alert levels (Integer) that are triggered
		# by this sensor alert.
		self.alertLevels = list()

		# The optional data of the sensor alert (if it has any).
		# If rulesActivated = true => always set to false.
		self.hasOptionalData = None
		self.optionalData = None

		# Does this sensor alert change the state of the sensor?
		self.changeState = None

		# Does this sensor alert hold the latest data of the sensor?
		self.hasLatestData = None

		# The sensor data type and data that is connected to this sensor alert.
		self.dataType = None
		self.sensorData = None


# this class represents an alert level that is configured on the server
class AlertLevel:

	def __init__(self):
		self.level = None
		self.name = None
		self.triggerAlways = None
		self.rulesActivated = None

		# flag that marks this object as checked
		# (is used to verify if this object is still connected to the server)
		self.checked = False


# this class handles an incoming server event (sensor alert message,
# status update, ...)
class ServerEventHandler:

	def __init__(self, globalData):

		# file name of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# get global configured data
		self.globalData = globalData
		self.sensorAlertLifeSpan = self.globalData.sensorAlertLifeSpan
		self.eventsLifeSpan = self.globalData.eventsLifeSpan
		self.storage = self.globalData.storage
		self.options = self.globalData.options
		self.nodes = self.globalData.nodes
		self.sensors = self.globalData.sensors
		self.managers = self.globalData.managers
		self.alerts = self.globalData.alerts
		self.alertLevels = self.globalData.alertLevels
		self.sensorAlerts = self.globalData.sensorAlerts
		self.versionInformer = self.globalData.versionInformer
		self.events = self.globalData.events
		self.connectionTimeout = self.globalData.connectionTimeout

		# keep track of the server time
		self.serverTime = 0.0


	# internal function that checks if all options are checked
	def _checkAllOptionsAreChecked(self):
		for option in self.options:
			if option.checked is False:
				return False
		return True


	# internal function that removes all nodes that are not checked
	def _removeNotCheckedNodes(self):

		timeReceived = int(time.time())

		for node in self.nodes:
			if node.checked is False:

				# create delete node event
				tempEvent = EventDeleteNode(timeReceived)
				tempEvent.hostname = node.hostname
				tempEvent.nodeType = node.nodeType
				tempEvent.instance = node.instance
				self.events.append(tempEvent)

				# remove node from list of nodes
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.nodes.remove(node)

		for sensor in self.sensors:
			if sensor.checked is False:

				# create delete sensor event
				tempEvent = EventDeleteSensor(timeReceived)
				tempEvent.description = sensor.description
				self.events.append(tempEvent)

				# remove sensor from list of sensors
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.sensors.remove(sensor)

		for manager in self.managers:
			if manager.checked is False:

				# create delete manager event
				tempEvent = EventDeleteManager(timeReceived)
				tempEvent.description = manager.description
				self.events.append(tempEvent)

				# remove manager from list of managers
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.managers.remove(manager)

		for alert in self.alerts:
			if alert.checked is False:

				# create delete alert event
				tempEvent = EventDeleteAlert(timeReceived)
				tempEvent.description = alert.description
				self.events.append(tempEvent)

				# remove alert from list of alerts
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.alerts.remove(alert)

		for alertLevel in self.alertLevels:
			if alertLevel.checked is False:

				# remove alert level from list of alert levels
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.alertLevels.remove(alertLevel)


	# internal function that marks all nodes as not checked
	def _markAlertSystemObjectsAsNotChecked(self):
		for option in self.options:
			option.checked = False

		for node in self.nodes:
			node.checked = False

		for sensor in self.sensors:
			sensor.checked = False		

		for manager in self.managers:
			manager.checked = False

		for alert in self.alerts:
			alert.checked = False

		for alertLevel in self.alertLevels:
			alertLevel.checked = False


	# is called when a status update event was received from the server
	def receivedStatusUpdate(self, serverTime, options, nodes, sensors,
		managers, alerts, alertLevels):

		self.serverTime = serverTime
		timeReceived = int(time.time())

		# mark all nodes as not checked
		self._markAlertSystemObjectsAsNotChecked()

		# process received options
		for recvOption in options:

			# search option in list of known options
			# => if not known add it
			found = False
			for option in self.options:
				# ignore options that are already checked
				if option.checked:

					# check if the type is unique
					if option.type == recvOption.type:
						logging.error("[%s]: Received optionType "
							% self.fileName
							+ "'%s' is not unique." % recvOption.type)

						return False

					continue

				# when found => mark option as checked and update information
				if option.type == recvOption.type:
					option.checked = True

					# only change value when it has changed
					if option.value != recvOption.value:

						# create change option event
						tempEvent = EventChangeOption(timeReceived)
						tempEvent.type = option.type
						tempEvent.oldValue = option.value
						tempEvent.newValue = recvOption.value
						self.events.append(tempEvent)

						option.value = recvOption.value

					found = True
					break
			# when not found => add option to list
			if not found:
				recvOption.checked = True
				self.options.append(recvOption)

				# create new option event
				tempEvent = EventNewOption(timeReceived)
				tempEvent.type = recvOption.type
				tempEvent.value = recvOption.value
				self.events.append(tempEvent)

		# check if all options are checked
		# => if not, one was removed on the server
		if not self._checkAllOptionsAreChecked():
			logging.exception("[%s]: Options are inconsistent."
				% self.fileName)

			return False

		# process received nodes
		for recvNode in nodes:

			# search node in list of known nodes
			# => if not known add it
			found = False
			for node in self.nodes:
				# ignore nodes that are already checked
				if node.checked:

					# check if the nodeId is unique
					if node.nodeId == recvNode.nodeId:
						logging.error("[%s]: Received nodeId " % self.fileName
							+ "'%d' is not unique." % recvNode.nodeId)

						return False

					continue

				# when found => mark node as checked and update information
				if node.nodeId == recvNode.nodeId:
					node.checked = True

					# create change node event (only add it if an information
					# has changed)
					changed = False
					tempEvent = EventChangeNode(timeReceived)

					# only update information if they have changed
					tempEvent.oldHostname = node.hostname
					tempEvent.newHostname = recvNode.hostname
					if node.hostname != recvNode.hostname:
						changed = True

					tempEvent.oldNodeType = node.nodeType
					tempEvent.newNodeType = recvNode.nodeType
					if node.nodeType != recvNode.nodeType:
						changed = True

					tempEvent.oldInstance = node.instance
					tempEvent.newInstance = recvNode.instance
					if node.instance != recvNode.instance:
						changed = True

					tempEvent.oldVersion = node.version
					tempEvent.newVersion = recvNode.version
					if node.version != recvNode.version:
						changed = True

					tempEvent.oldRev = node.rev
					tempEvent.newRev = recvNode.rev
					if node.rev != recvNode.rev:
						changed = True

					tempEvent.oldUsername = node.username
					tempEvent.newUsername = recvNode.username
					if node.username != recvNode.username:
						changed = True

					tempEvent.oldPersistent = node.persistent
					tempEvent.newPersistent = recvNode.persistent
					if node.persistent != recvNode.persistent:
						changed = True

					# add event to event queue if an information has changed
					if changed:
						self.events.append(tempEvent)

					# only change connected value when it has changed
					if node.connected != recvNode.connected:
						
						# create connected change event
						tempEvent = EventConnectedChange(timeReceived)
						tempEvent.hostname = node.hostname
						tempEvent.nodeType = node.nodeType
						tempEvent.instance = node.instance
						tempEvent.connected = recvNode.connected
						self.events.append(tempEvent)

					node.deepCopy(recvNode)
					found = True
					break
			# when not found => add node to list
			if not found:
				recvNode.checked = True
				self.nodes.append(recvNode)

				# create new node event
				tempEvent = EventNewNode(timeReceived)
				tempEvent.hostname = recvNode.hostname
				tempEvent.nodeType = recvNode.nodeType
				tempEvent.instance = recvNode.instance
				self.events.append(tempEvent)

		# process received sensors
		for recvSensor in sensors:

			# search sensor in list of known sensors
			# => if not known add it
			found = False
			for sensor in self.sensors:

				# ignore sensors that are already checked
				if sensor.checked:

					# check if the sensorId is unique
					if sensor.sensorId == recvSensor.sensorId:
						logging.error("[%s]: Received sensorId "
							% self.fileName
							+ "'%d' is not unique." % recvSensor.sensorId)

						return False

					continue

				# when found => mark sensor as checked and update information
				if sensor.sensorId == recvSensor.sensorId:
					sensor.checked = True
					tempLastStateUpdated = sensor.lastStateUpdated
					tempState = sensor.state

					# create change sensor event (only add it if an information
					# has changed)
					changed = False
					tempEvent = EventChangeSensor(timeReceived)

					# only update information if they have changed
					tempEvent.oldAlertDelay = sensor.alertDelay
					tempEvent.newAlertDelay = recvSensor.alertDelay
					if sensor.alertDelay != recvSensor.alertDelay:
						changed = True

					tempEvent.oldDescription = sensor.description
					tempEvent.newDescription = recvSensor.description
					if sensor.description != recvSensor.description:
						changed = True

					tempEvent.oldRemoteSensorId = sensor.remoteSensorId
					tempEvent.newRemoteSensorId = recvSensor.remoteSensorId
					if sensor.remoteSensorId != recvSensor.remoteSensorId:
						changed = True

					# add event to event queue if an information has changed
					if changed:
						self.events.append(tempEvent)

					sensor.deepCopy(recvSensor)

					# Revert change to the state if the old state was newer.
					if sensor.lastStateUpdated < tempLastStateUpdated:
						sensor.lastStateUpdated = tempLastStateUpdated
						sensor.state = tempState

					found = True
					break

			# when not found => add sensor to list
			if not found:
				recvSensor.checked = True
				self.sensors.append(recvSensor)

				# create new sensor event
				foundNode = None
				for node in self.nodes:
					if node.nodeId == recvSensor.nodeId:
						foundNode = node
						break
				if foundNode is None:
					logging.error("[%s]: Could not find node with id "
						% self.fileName
						+ "'%d' for sensor with id '%d'."
						% (recvSensor.nodeId, recvSensor.sensorId))

					return False
				tempEvent = EventNewSensor(timeReceived)
				tempEvent.hostname = foundNode.hostname
				tempEvent.description = recvSensor.description
				tempEvent.state = recvSensor.state
				self.events.append(tempEvent)

		# process received managers
		for recvManager in managers:

			# search manager in list of known managers
			# => if not known add it
			found = False
			for manager in self.managers:
				# ignore managers that are already checked
				if manager.checked:

					# check if the managerId is unique
					if manager.managerId == recvManager.managerId:
						logging.error("[%s]: Received managerId "
							% self.fileName
							+ "'%d' is not unique." % recvManager.managerId)

						return False

					continue

				# when found => mark manager as checked and update information
				if manager.managerId == recvManager.managerId:
					manager.checked = True

					# create change manager event
					# (only add it if an information has changed)
					changed = False
					tempEvent = EventChangeManager(timeReceived)

					# only update information if they have changed
					tempEvent.oldDescription = manager.description
					tempEvent.newDescription = recvManager.description
					if manager.description != recvManager.description:
						changed = True

					# add event to event queue if an information has changed
					if changed:
						self.events.append(tempEvent)

					manager.deepCopy(recvManager)
					found = True
					break
			# when not found => add manager to list
			if not found:
				recvManager.checked = True
				self.managers.append(recvManager)

				# create new manager event
				foundNode = None
				for node in self.nodes:
					if node.nodeId == recvManager.nodeId:
						foundNode = node
						break
				if foundNode is None:
					logging.error("[%s]: Could not find node with id "
						% self.fileName
						+ "'%d' for manager with id '%d'."
						% (recvManager.nodeId, recvManager.managerId))

					return False
				tempEvent = EventNewManager(timeReceived)
				tempEvent.hostname = foundNode.hostname
				tempEvent.description = recvManager.description
				self.events.append(tempEvent)

		# process received alerts
		for recvAlert in alerts:

			# search alert in list of known alerts
			# => if not known add it
			found = False
			for alert in self.alerts:
				# ignore alerts that are already checked
				if alert.checked:

					# check if the alertId is unique
					if alert.alertId == recvAlert.alertId:
						logging.error("[%s]: Received alertId " % self.fileName
							+ "'%d' is not unique." % recvAlert.alertId)

						return False

					continue

				# when found => mark alert as checked and update information
				if alert.alertId == recvAlert.alertId:
					alert.checked = True

					# create change alert event (only add it if an information
					# has changed)
					changed = False
					tempEvent = EventChangeAlert(timeReceived)

					# only update information if they have changed
					tempEvent.oldDescription = alert.description
					tempEvent.newDescription = recvAlert.description
					if alert.description != recvAlert.description:
						changed = True

					tempEvent.oldRemoteAlertId = alert.remoteAlertId
					tempEvent.newRemoteAlertId = recvAlert.remoteAlertId
					if alert.remoteAlertId != recvAlert.remoteAlertId:
						changed = True

					# add event to event queue if an information has changed
					if changed:
						self.events.append(tempEvent)

					alert.deepCopy(recvAlert)
					found = True
					break

			# when not found => add alert to list
			if not found:
				recvAlert.checked = True
				self.alerts.append(recvAlert)

				# create new alert event
				foundNode = None
				for node in self.nodes:
					if node.nodeId == recvAlert.nodeId:
						foundNode = node
						break
				if foundNode is None:
					logging.error("[%s]: Could not find node with id "
						% self.fileName
						+ "'%d' for alert with id '%d'."
						% (recvAlert.nodeId, recvAlert.alertId))

					return False
				tempEvent = EventNewAlert(timeReceived)
				tempEvent.hostname = foundNode.hostname
				tempEvent.description = recvAlert.description
				self.events.append(tempEvent)

		# process received alertLevels
		for recvAlertLevel in alertLevels:

			# search alertLevel in list of known alertLevels
			# => if not known add it
			found = False
			for alertLevel in self.alertLevels:
				# ignore alertLevels that are already checked
				if alertLevel.checked:

					# check if the level is unique
					if alertLevel.level == recvAlertLevel.level:
						logging.error("[%s]: Received alertLevel "
							% self.fileName
							+ "'%d' is not unique." % recvAlertLevel.level)

						return False

					continue

				# when found => mark alertLevel as checked
				# and update information
				if alertLevel.level == recvAlertLevel.level:
					alertLevel.checked = True
					alertLevel.name = recvAlertLevel.name
					alertLevel.triggerAlways = recvAlertLevel.triggerAlways
					alertLevel.rulesActivated = recvAlertLevel.rulesActivated

					found = True
					break

			# when not found => add alertLevel to list
			if not found:
				recvAlertLevel.checked = True
				self.alertLevels.append(recvAlertLevel)

		# remove all nodes that are not checked
		self._removeNotCheckedNodes()

		return True


	# is called when a sensor alert event was received from the server
	def receivedSensorAlert(self, serverTime, sensorAlert):

		self.serverTime = serverTime
		timeReceived = int(time.time())
		self.sensorAlerts.append(sensorAlert)

		# when events are activated
		# => create events
		if self.eventsLifeSpan != 0:

			# create sensor alert event
			tempEvent = EventSensorAlert(timeReceived)
			tempEvent.description = sensorAlert.description
			tempEvent.state = sensorAlert.state
			tempEvent.dataType = sensorAlert.dataType
			tempEvent.sensorData = sensorAlert.sensorData

			tempEvent.alertLevels = list(sensorAlert.alertLevels)
			self.events.append(tempEvent)

			# When rules are not activated and change state flag is set.
			# => Create state change event.
			if not sensorAlert.rulesActivated and sensorAlert.changeState:
				tempStateEvent = EventStateChange(timeReceived)
				tempStateEvent.state = sensorAlert.state

				# Only store data for this state change event if the sensor
				# alert carries the latest data of the sensor.
				if sensorAlert.hasLatestData:
					tempStateEvent.dataType = sensorAlert.dataType
					tempStateEvent.data = sensorAlert.sensorData
				else:
					tempStateEvent.dataType = SensorDataType.NONE

				triggeredSensor = None
				for sensor in self.sensors:
					if sensor.sensorId == sensorAlert.sensorId:
						tempStateEvent.description = sensor.description
						triggeredSensor = sensor
						break
				if not triggeredSensor is None:
					for node in self.nodes:
						if node.nodeId == sensor.nodeId:
							tempStateEvent.hostname = node.hostname
							self.events.append(tempStateEvent)
							break
					if tempStateEvent.hostname is None:
						logging.error("[%s]: Unable to find corresponding " 
							% self.fileName
							+ "node to sensor for state change event.")
				else:
					logging.error("[%s]: Unable to find corresponding " 
						% self.fileName
						+ "sensor to sensor alert for state change event.")

		# If rules are not activated (and therefore the sensor alert was
		# only triggered by one distinct sensor).
		# => Update information in sensor which triggered the sensor alert.
		if not sensorAlert.rulesActivated:
			found = False
			for sensor in self.sensors:
				if sensor.sensorId == sensorAlert.sensorId:
					sensor.lastStateUpdated = serverTime

					# Only update sensor state information if the flag
					# was set in the received message.
					if sensorAlert.changeState:
						sensor.state = sensorAlert.state
					
					# Only update sensor data information if the flag
					# was set in the received message.
					if sensorAlert.hasLatestData:
						if sensorAlert.dataType == sensor.dataType:
							sensor.data = sensorAlert.sensorData
						else:
							logging.error("[%s]: Sensor data type different. "
								% self.fileName
								+ "Skipping data assignment.")

					found = True
					break
			if not found:
				logging.error("[%s]: Sensor of sensor alert " % self.fileName
					+ "not known.")

				return False

		return True


	# is called when a state change event was received from the server
	def receivedStateChange(self, serverTime, sensorId, state, dataType,
		sensorData):

		self.serverTime = serverTime

		# search sensor in list of known sensors
		# => if not known return failure
		sensor = None
		for tempSensor in self.sensors:
			if tempSensor.sensorId == sensorId:
				sensor = tempSensor
				break
		if not sensor:
			logging.error("[%s]: Sensor for state change " % self.fileName
				+ "not known.")

			return False

		# when events are activated
		# => create state change event
		if self.eventsLifeSpan != 0:
			utcTimestamp = int(time.time())
			tempStateEvent = EventStateChange(utcTimestamp)
			tempStateEvent.state = state
			tempStateEvent.description = sensor.description
			tempStateEvent.dataType = sensor.dataType
			tempStateEvent.data = sensor.data

			for node in self.nodes:
				if node.nodeId == sensor.nodeId:
					tempStateEvent.hostname = node.hostname
					self.events.append(tempStateEvent)
					break
			if not tempStateEvent.hostname:
				logging.error("[%s]: Unable to find corresponding " 
					% self.fileName
					+ "node to sensor for state change event.")

		# Change sensor state.
		sensor.state = state
		sensor.lastStateUpdated = serverTime

		if dataType == sensor.dataType:
			sensor.data = sensorData
		else:
			logging.error("[%s]: Sensor data type different. "
				% self.fileName
				+ "Skipping data assignment.")

		return True


	# is called when an incoming server event has to be handled
	def handleEvent(self):

		# check if configured to not store sensor alerts
		# => delete them directly
		if self.sensorAlertLifeSpan == 0:
			del self.sensorAlerts[:]

		# check if version informer instance is set
		# => if not get it from the global data (is only set if
		# automatic update checks are activated)
		if self.versionInformer is None:
			self.versionInformer = self.globalData.versionInformer

		# => get newest known version from the version informer for each node
		else:
			for node in self.nodes:

				found = False
				for repoInstance in self.versionInformer.repoVersions.keys():
					if node.instance.upper() == repoInstance.upper():

						tempVersion = self.versionInformer.repoVersions[
							repoInstance].newestVersion
						tempRev = self.versionInformer.repoVersions[
							repoInstance].newestRev

						# check if a newer version is available than the
						# currently used (or last known version)
						# => create event
						if (node.version < tempVersion
							and node.newestVersion < tempVersion):
							utcTimestamp = int(time.time())
							tempEvent = EventNewVersion(utcTimestamp)
							tempEvent.usedVersion = node.version
							tempEvent.usedRev = node.rev
							tempEvent.newVersion = tempVersion
							tempEvent.newRev = tempRev
							tempEvent.instance = node.instance
							tempEvent.hostname = node.hostname
							if self.eventsLifeSpan != 0:
								self.events.append(tempEvent)

						# check if a newer revision for this version is
						# available than the currently used
						# (or last known version)
						# => create event
						elif node.version == tempVersion:
							if (node.rev < tempRev
								and node.newestRev < tempRev):
								utcTimestamp = int(time.time())
								tempEvent = EventNewVersion(utcTimestamp)
								tempEvent.usedVersion = node.version
								tempEvent.usedRev = node.rev
								tempEvent.newVersion = tempVersion
								tempEvent.newRev = tempRev
								tempEvent.instance = node.instance
								tempEvent.hostname = node.hostname
								if self.eventsLifeSpan != 0:
									self.events.append(tempEvent)

						node.newestVersion \
							= self.versionInformer.repoVersions[
							repoInstance].newestVersion
						node.newestRev \
							= self.versionInformer.repoVersions[
							repoInstance].newestRev

						found = True
						break
				# if instance was not found in online repository
				# => unset newest version and revision
				if not found:
					node.newestVersion = -1.0
					node.newestRev = -1


		# check if a sensor has timed out
		# => create an event for it
		for sensor in self.sensors:
			if (sensor.lastStateUpdated < (self.serverTime
				- (2 * self.connectionTimeout))):

				# create sensor time out event
				# (only add it if node is connected)
				foundNode = None
				for node in self.nodes:
					if node.nodeId == sensor.nodeId:
						foundNode = node
						break
				if foundNode is None:
					logging.error("[%s]: Could not find node with id "
						% self.fileName
						+ "'%d' for sensor with id '%d'."
						% (sensor.nodeId, sensor.sensorId))

					continue
				if foundNode.connected == 1:
					utcTimestamp = int(time.time())
					tempEvent = EventSensorTimeOut(utcTimestamp)
					tempEvent.hostname = foundNode.hostname
					tempEvent.description = sensor.description
					tempEvent.state = sensor.state
					self.events.append(tempEvent)


		# update the local server information
		if not self.storage.updateServerInformation(self.serverTime,
			self.options, self.nodes, self.sensors, self.alerts,
			self.managers, self.alertLevels, self.sensorAlerts):

			logging.error("[%s]: Unable to update server information." 
					% self.fileName)

		else:
			# empty sensor alerts list to prevent it
			# from getting too big
			del self.sensorAlerts[:]