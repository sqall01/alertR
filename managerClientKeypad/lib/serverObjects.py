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

		# flag that marks this object as checked
		# (is used to verify if this object is still connected to the server)
		self.checked = False

		# used for urwid only:
		# reference to the sensor urwid object
		self.sensorUrwid = None

		# used for urwid only:
		# reference to the alert urwid object
		self.alertUrwid = None


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

		# flag that marks this object as checked
		# (is used to verify if this object is still connected to the server)
		self.checked = False

		# used for urwid only:
		# reference to the sensor urwid object
		self.sensorUrwid = None


# this class represents a manager client of the alert system
class Manager:

	def __init__(self):
		self.nodeId = None
		self.managerId = None
		self.description = None

		# flag that marks this object as checked
		# (is used to verify if this object is still connected to the server)
		self.checked = False

		# used for urwid only:
		# reference to the manager urwid object
		self.managerUrwid = None


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

		# used for urwid only:
		# reference to the alert urwid object
		self.alertUrwid = None


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

		# The data of the sensor alert (if it has any).
		# If rulesActivated = true => always set to false.
		self.dataTransfer = None
		self.data = None

		# Does this sensor alert change the state of the sensor?
		self.changeState = None


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

		# used for urwid only:
		# reference to the alert urwid object
		self.alertLevelUrwid = None


# this class handles an incoming server event (sensor alert message,
# status update, ...)
class ServerEventHandler:

	def __init__(self, globalData):

		# file name of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# get global configured data
		self.globalData = globalData
		self.screenUpdater = self.globalData.screenUpdater
		self.options = self.globalData.options
		self.nodes = self.globalData.nodes
		self.sensors = self.globalData.sensors
		self.managers = self.globalData.managers
		self.alerts = self.globalData.alerts
		self.alertLevels = self.globalData.alertLevels
		self.sensorAlerts = self.globalData.sensorAlerts

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
		for node in self.nodes:
			if node.checked is False:

				# check if node object has a link to the sensor urwid object
				if not node.sensorUrwid is None:
					# check if sensor urwid object is linked to node object
					if not node.sensorUrwid.node is None:
						# used for urwid only:
						# remove reference from urwid object to node object
						# (the objects are double linked)
						node.sensorUrwid.node = None

				# check if node object has a link to the alert urwid object
				elif not node.alertUrwid is None:
					# check if sensor urwid object is linked to node object
					if not node.alertUrwid.node is None:
						# used for urwid only:
						# remove reference from urwid object to node object
						# (the objects are double linked)
						node.alertUrwid.node = None

				# remove sensor from list of sensors
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.nodes.remove(node)

		for sensor in self.sensors:
			if sensor.checked is False:

				# check if sensor object has a link to the sensor urwid object
				if not sensor.sensorUrwid is None:
					# check if sensor urwid object is linked to sensor object
					if not sensor.sensorUrwid.sensor is None:
						# used for urwid only:
						# remove reference from urwid object to sensor object
						# (the objects are double linked)
						sensor.sensorUrwid.sensor = None

				# remove sensor from list of sensors
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.sensors.remove(sensor)

		for manager in self.managers:
			if manager.checked is False:

				# check if manager object has a link to the 
				# manager urwid object
				if not manager.managerUrwid is None:
					# check if manager urwid object is linked to manager object
					if not manager.managerUrwid.manager is None:
						# used for urwid only:
						# remove reference from urwid object to manager object
						# (the objects are double linked)
						manager.managerUrwid.manager = None

				# remove manager from list of managers
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.managers.remove(manager)

		for alert in self.alerts:
			if alert.checked is False:

				# check if alert object has a link to the alert urwid object
				if not alert.alertUrwid is None:
					# check if alert urwid object is linked to alert object
					if not alert.alertUrwid.alert is None:
						# used for urwid only:
						# remove reference from urwid object to alert object
						# (the objects are double linked)
						alert.alertUrwid.alert = None

				# remove alert from list of alerts
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.alerts.remove(alert)

		for alertLevel in self.alertLevels:
			if alertLevel.checked is False:

				# check if alert level object has a link to 
				# the alert level urwid object
				if not alertLevel.alertLevelUrwid is None:
					# check if alert level urwid object is 
					# linked to alert level object
					if not alertLevel.alertLevelUrwid.alertLevel is None:
						# used for urwid only:
						# remove reference from urwid object to 
						# alert level object
						# (the objects are double linked)
						alertLevel.alertLevelUrwid.alertLevel = None

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
					option.value = recvOption.value
					found = True
					break
			# when not found => add option to list
			if not found:
				recvOption.checked = True
				self.options.append(recvOption)

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
					node.hostname = recvNode.hostname
					node.nodeType = recvNode.nodeType
					node.instance = recvNode.instance
					node.connected = recvNode.connected
					node.version = recvNode.version
					node.rev = recvNode.rev
					node.username = recvNode.username
					found = True
					break
			# when not found => add node to list
			if not found:
				recvNode.checked = True
				self.nodes.append(recvNode)

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

					sensor.nodeId = recvSensor.nodeId
					sensor.remoteSensorId = recvSensor.remoteSensorId
					sensor.alertDelay = recvSensor.alertDelay
					sensor.alertLevels = recvSensor.alertLevels
					sensor.description = recvSensor.description

					# only update state if it is older than received one
					if recvSensor.lastStateUpdated > sensor.lastStateUpdated:
						sensor.lastStateUpdated = recvSensor.lastStateUpdated
						sensor.state = recvSensor.state

					found = True
					break
			# when not found => add sensor to list
			if not found:
				recvSensor.checked = True
				self.sensors.append(recvSensor)

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
					manager.nodeId = recvManager.nodeId
					manager.description = recvManager.description
					found = True
					break
			# when not found => add manager to list
			if not found:
				recvManager.checked = True
				self.managers.append(recvManager)

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
					alert.nodeId = recvAlert.nodeId
					alert.remoteAlertId = recvAlert.remoteAlertId
					alert.alertLevels = recvAlert.alertLevels
					alert.description = recvAlert.description
					found = True
					break

			# when not found => add alert to list
			if not found:
				recvAlert.checked = True
				self.alerts.append(recvAlert)

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

		# If rules are not activated (and therefore the sensor alert was
		# only triggered by one distinct sensor).
		# => Update information in sensor which triggered the sensor alert.
		if not sensorAlert.rulesActivated:
			for sensor in self.sensors:
				if sensor.sensorId == sensorAlert.sensorId:
					sensor.lastStateUpdated = serverTime

					# Only update sensor state information if the flag
					# was set in the received message.
					if sensorAlert.changeState:
						sensor.state = sensorAlert.state

					break

		return True


	# is called when a state change event was received from the server
	def receivedStateChange(self, serverTime, sensorId, state):

		self.serverTime = serverTime

		# search sensor in list of known sensors
		# => if not known return failure
		found = False
		for sensor in self.sensors:

			# when found => mark sensor as checked and update information
			if sensor.sensorId == sensorId:
				sensor.state = state
				sensor.lastStateUpdated = serverTime

				found = True
				break
		if not found:
			logging.error("[%s]: Sensor for state change " % self.fileName
				+ "not known.")

			return False

		return True


	# is called when an incoming server event has to be handled
	def handleEvent(self):

		# wake up the screen updater
		self.screenUpdater.screenUpdaterEvent.set()