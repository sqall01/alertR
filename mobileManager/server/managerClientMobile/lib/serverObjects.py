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
from events import EventSensorAlert, EventNewVersion, EventStateChange


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

		# used by mobile manager only:
		# newest known version
		self.newestVersion = -1.0
		self.newestRev = -1

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
		self.alertDelay = None
		self.alertLevels = list()
		self.description = None
		self.lastStateUpdated = None
		self.state = None
		self.serverTime = None

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
		self.rulesActivated = None
		self.sensorId = None
		self.state = None
		self.description = None
		self.timeReceived = None
		self.alertLevels = list()
		self.dataTransfer = None
		self.data = None


# this class represents an alert level that is configured on the server
class AlertLevel:

	def __init__(self):
		self.smtpActivated = None
		self.toAddr = None
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

		# file nme of this file (used for logging)
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












	# TODO
	# outsource status update handler from client.py to this class








	def receivedSensorAlert(self, serverTime, rulesActivated, sensorId, state,
		description, alertLevels, dataTransfer, data):


		timeReceived = int(time.time())








		# TODO
		# specific for this manager => remove before copying to other managers

		# when events are activated
		# => create events
		if self.eventsLifeSpan != 0:

			# create sensor alert event
			tempEvent = EventSensorAlert(timeReceived)
			tempEvent.description = description
			tempEvent.state = state
			tempEvent.alertLevels = list(alertLevels)
			self.events.append(tempEvent)

			# when rules are not activated
			# => create state change event
			if not rulesActivated:
				tempStateEvent = EventStateChange(int(time.time()))
				tempStateEvent.state = state
				triggeredSensor = None
				for sensor in self.sensors:
					if sensor.sensorId == sensorId:
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












		# generate sensor alert object
		sensorAlert = SensorAlert()
		sensorAlert.rulesActivated = rulesActivated
		sensorAlert.sensorId = sensorId
		sensorAlert.description = description
		sensorAlert.state = state
		sensorAlert.timeReceived = timeReceived
		sensorAlert.alertLevels = alertLevels
		sensorAlert.dataTransfer = dataTransfer
		sensorAlert.data = data
		self.sensorAlerts.append(sensorAlert)

		# if rules are not activated (and therefore the sensor alert was
		# only triggered by one distinct sensor)
		# => update information in sensor which triggered the alert
		if not rulesActivated:
			for sensor in self.sensors:
				if sensor.sensorId == sensorId:
					sensor.state = state
					sensor.lastStateUpdated = serverTime
					sensor.serverTime = serverTime
					break

		return True











	def receivedStateChange(self, serverTime, sensorId, state):




		# TODO
		# specific for this manager => remove before copying to other managers


		# when events are activated
		# => create state change event
		if self.eventsLifeSpan != 0:
			tempStateEvent = EventStateChange(int(time.time()))
			tempStateEvent.state = state
			triggeredSensor = None
			for sensor in self.sensors:
				if sensor.sensorId == sensorId:
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










		# search sensor in list of known sensors
		# => if not known return failure
		found = False
		for sensor in self.sensors:

			# when found => mark sensor as checked and update information
			if sensor.sensorId == sensorId:
				sensor.state = state
				sensor.lastStateUpdated = serverTime
				sensor.serverTime = serverTime

				found = True
				break
		if not found:
			logging.error("[%s]: Sensor for state change " % self.fileName
				+ "not known.")

			return False

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
							tempEvent = EventNewVersion(int(time.time()))
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
								tempEvent = EventNewVersion(int(time.time()))
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

		# update the local server information
		if not self.storage.updateServerInformation(self.options, self.nodes,
			self.sensors, self.alerts, self.managers, self.alertLevels,
			self.sensorAlerts):

			logging.error("[%s]: Unable to update server information." 
					% self.fileName)

		else:
			# empty sensor alerts list to prevent it
			# from getting too big
			del self.sensorAlerts[:]