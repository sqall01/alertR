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




	# this function is called when events from the received data should
	# be created
	def tasta(self): # TODO

		# create an event for each received sensor alert
		for sensorAlert in self.sensorAlerts:
			tempEvent = EventSensorAlert(sensorAlert.timeReceived)
			tempEvent.description = sensorAlert.description

			# check if rules were activated for this sensor alert
			# => set sensor alert to "triggered" state
			if sensorAlert.rulesActivated:
				tempEvent.state = 1

			# when no rules were activated
			# => get state from message
			else:
				tempEvent.state = sensorAlert.state
			tempEvent.alertLevels = list(sensorAlert.alertLevels)

			self.events.append(tempEvent)


	# is called when an incoming server event has to be handled
	def handleEvent(self):

		# check if configured to not store sensor alerts
		# => delete them directly
		if self.sensorAlertLifeSpan == 0:
			del self.sensorAlerts[:]

		# check if configured to store events
		# => create events from the received data
		if self.eventsLifeSpan != 0:
			self.tasta()

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
						if (node.version < tempVersion
							and node.newestVersion < tempVersion):

							pass
							# TODO
							# event here for new version available

						# check if a newer revision for this version is
						# available than the currently used
						# (or last known version)
						elif node.version == tempVersion:
							if (node.rev < tempRev
								and node.newestRev < tempRev):

								pass
								# TODO
								# event here for new version available

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















# TODO
# perhaps add event for changes for sensors, nodes etc in storage backend
# (it already has a copy of existing elements)





# TODO
# need additional events

class Event:

	def __init__(self, timeOccurred):
		self.timeOccurred = timeOccurred


class EventSensorAlert(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.description = None
		self.state = None
		self.alertLevels = list()