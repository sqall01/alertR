#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import logging
import os
import time
import urwid


# this class is an urwid object for a status
class StatusUrwid:

	def __init__(self, title, statusType, statusValue):

		self.title = title
		self.statusType = statusType
		self.statusValue = statusValue

		self.statusTextWidget = urwid.Text(self.statusType + ": "
			+ str(self.statusValue))
		statusBox = urwid.LineBox(self.statusTextWidget, title=self.title)
		paddedStatusBox = urwid.Padding(statusBox, left=0, right=0)
		self.statusUrwidMap = urwid.AttrMap(paddedStatusBox, "neutral")


	# this function returns the final urwid widget that is used
	# to render the box of a status
	def get(self):
		return self.statusUrwidMap


	# this functipn updates the status type
	def updateStatusType(self, statusType):
		self.statusType = statusType
		self.statusTextWidget.set_text(self.statusType + ": "
			+ str(self.statusValue))


	# this functipn updates the status value
	def updateStatusValue(self, statusValue):
		self.statusValue = statusValue
		self.statusTextWidget.set_text(self.statusType + ": "
			+ str(self.statusValue))


	# this function changes the color of this urwid object to red
	def turnRed(self):
		self.statusUrwidMap.set_attr_map({None: "redColor"})


	# this function changes the color of this urwid object to green
	def turnGreen(self):
		self.statusUrwidMap.set_attr_map({None: "greenColor"})


	# this function changes the color of this urwid object to gray
	def turnGray(self):
		self.statusUrwidMap.set_attr_map({None: "grayColor"})


	# this function changes the color of this urwid object to the
	# neutral color scheme
	def turnNeutral(self):
		self.statusUrwidMap.set_attr_map({None: "neutral"})


# this class is an urwid object for a sensor
class SensorUrwid:

	def __init__(self, sensor, node, connectionTimeout, serverEventHandler):

		# is needed to decide when a sensor has timed out
		self.connectionTimeout = connectionTimeout
		self.serverEventHandler = serverEventHandler

		sensorPileList = list()
		self.descriptionWidget = urwid.Text("Desc.: " + sensor.description)
		sensorPileList.append(self.descriptionWidget)

		sensorPile = urwid.Pile(sensorPileList)
		sensorBox = urwid.LineBox(sensorPile, title="host: " + node.hostname)
		paddedSensorBox = urwid.Padding(sensorBox, left=1, right=1)

		# check if node is connected and set the color accordingly
		# and consider the state of the sensor (1 = triggered)
		if node.connected == 0:
			self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox,
				"disconnected")
			self.sensorUrwidMap.set_focus_map({None: "disconnected_focus"})

		# check if the node is connected and no sensor alert is triggered
		elif (node.connected == 1
			and sensor.state != 1):
			self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox, "connected")
			self.sensorUrwidMap.set_focus_map({None: "connected_focus"})

		# last possible combination is a triggered sensor alert
		else:
			self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox, "sensoralert")
			self.sensorUrwidMap.set_focus_map({None: "sensoralert_focus"})

		# check if sensor has timed out and change color accordingly
		# and consider the state of the sensor (1 = triggered)
		if (sensor.lastStateUpdated < (self.serverEventHandler.serverTime
			- (2 * self.connectionTimeout))
			and sensor.state != 1):
			self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox,
				"timedout")
			self.sensorUrwidMap.set_focus_map({None: "timedout_focus"})

		# store reference to sensor object and node object
		self.sensor = sensor
		self.node = node

		# store reference in sensor object to this urwid sensor object
		self.sensor.sensorUrwid = self


	# this function returns the final urwid widget that is used
	# to render the box of a sensor
	def get(self):
		return self.sensorUrwidMap


	# this function updates the description of the object
	def updateDescription(self, description):
		self.descriptionWidget.set_text("Desc.: " + description)


	# this function updates the connected status of the object
	# (and changes color arcordingly)
	def updateConnected(self, connected):

		# change color according to connection state
		# and consider the state of the sensor (1 = triggered)
		if (connected == 0
			and self.sensor.state != 1):
			self.sensorUrwidMap.set_attr_map({None: "disconnected"})
			self.sensorUrwidMap.set_focus_map({None: "disconnected_focus"})
		elif (connected == 1
			and self.sensor.state != 1):
			self.sensorUrwidMap.set_attr_map({None: "connected"})
			self.sensorUrwidMap.set_focus_map({None: "connected_focus"})

		# check if sensor has timed out and change color accordingly
		# and consider the state of the sensor (1 = triggered)
		if (self.sensor.lastStateUpdated < (self.serverEventHandler.serverTime
			- (2 * self.connectionTimeout))
			and self.sensor.state != 1):
			self.sensorUrwidMap.set_attr_map({None: "timedout"})
			self.sensorUrwidMap.set_focus_map({None: "timedout_focus"})


	# this function updates the last update status of the object
	# (and changes color arcordingly)
	def updateLastUpdated(self, lastStateUpdated):

		# check if sensor has timed out and change color accordingly
		if (lastStateUpdated < (self.serverEventHandler.serverTime
			- (2 * self.connectionTimeout))
			and self.sensor.state != 1):
			self.sensorUrwidMap.set_attr_map({None: "timedout"})
			self.sensorUrwidMap.set_focus_map({None: "timedout_focus"})


	# this function updates the state of the object
	# (and changes color arcordingly)
	def updateState(self, state):

		# check if the node is connected and change the color accordingly
		if self.node.connected == 0:
			self.sensorUrwidMap.set_attr_map({None: "disconnected"})
			self.sensorUrwidMap.set_focus_map({None: "disconnected_focus"})

		else:
			# check to which state the color should be changed
			if state == 0:
				self.sensorUrwidMap.set_attr_map({None: "connected"})
				self.sensorUrwidMap.set_focus_map({None: "connected_focus"})
				# check if the sensor timed out and change 
				# the color accordingly
				if (self.sensor.lastStateUpdated
					< (self.serverEventHandler.serverTime
					- (2 * self.connectionTimeout))):
					self.sensorUrwidMap.set_attr_map({None: "timedout"})
					self.sensorUrwidMap.set_focus_map({None: "timedout_focus"})
			elif state == 1:
				self.sensorUrwidMap.set_attr_map({None: "sensoralert"})
				self.sensorUrwidMap.set_focus_map({None: "sensoralert_focus"})


	# this function updates all internal widgets and checks if
	# the sensor/node still exists
	def updateCompleteWidget(self):

		# check if sensor/node still exists
		if (self.sensor is None
			or self.node is None):

			# return false if object no longer exists
			return False

		self.updateDescription(self.sensor.description)
		self.updateConnected(self.node.connected)
		self.updateLastUpdated(self.sensor.lastStateUpdated)
		self.updateState(self.sensor.state)

		# return true if object was updated
		return True


	# this functions sets the color when the connection to the server
	# has failed
	def setConnectionFail(self):
		self.sensorUrwidMap.set_attr_map({None: "connectionfail"})
		self.sensorUrwidMap.set_focus_map({None: "connectionfail_focus"})


# this class is an urwid object for a detailed sensor output
class SensorDetailedUrwid:

	def __init__(self, sensor, node, alertLevels):

		# TODO
		# needs also a list of sensor alerts that are triggered by this
		# sensor recently

		self.node = node
		self.sensor = sensor

		content = list()

		content.append(urwid.Divider("="))
		content.append(urwid.Text("Node"))
		content.append(urwid.Divider("="))
		temp = self._createNodeWidgetList(node)
		self.nodePileWidget = urwid.Pile(temp)
		content.append(self.nodePileWidget)

		content.append(urwid.Divider())
		content.append(urwid.Divider("="))
		content.append(urwid.Text("Sensor"))
		content.append(urwid.Divider("="))
		temp = self._createSensorWidgetList(sensor)
		self.sensorPileWidget = urwid.Pile(temp)
		content.append(self.sensorPileWidget)

		content.append(urwid.Divider())
		content.append(urwid.Divider("="))
		content.append(urwid.Text("Alert Levels"))
		content.append(urwid.Divider("="))
		temp = self._createAlertLevelsWidgetList(alertLevels)
		self.alertLevelsPileWidget = None
		if temp:
			self.alertLevelsPileWidget = urwid.Pile(temp)
		else:
			self.alertLevelsPileWidget = urwid.Pile([urwid.Text("None")])
		content.append(self.alertLevelsPileWidget)

		# use ListBox here because it handles all the
		# scrolling part automatically
		detailedList = urwid.ListBox(content)
		detailedFrame = urwid.Frame(detailedList,
			footer=urwid.Text("Keys: ESC - Back, Up/Down - Scrolling"))
		self.detailedBox = urwid.LineBox(detailedFrame,
			title="Sensor: " + self.sensor.description)


	# this function creates the detailed output of all alert level objects
	# in a list
	def _createAlertLevelsWidgetList(self, alertLevels):

		temp = list()
		first = True
		for alertLevel in alertLevels:

			if first:
				first = False
			else:
				temp.append(urwid.Divider())
				temp.append(urwid.Divider("-"))

			temp.extend(self._createAlertLevelWidgetList(alertLevel))

		return temp


	# this function creates the detailed output of a alert level object
	# in a list
	def _createAlertLevelWidgetList(self, alertLevel):

		temp = list()

		temp.append(urwid.Text("Alert Level:"))
		temp.append(urwid.Text(str(alertLevel.level)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Name:"))
		temp.append(urwid.Text(alertLevel.name))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Trigger Always:"))
		if alertLevel.triggerAlways == 0:
			temp.append(urwid.Text("No"))
		elif alertLevel.triggerAlways == 1:
			temp.append(urwid.Text("Yes"))
		else:
			temp.append(urwid.Text("Undefined"))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Rules Activated:"))
		if alertLevel.rulesActivated == 0:
			temp.append(urwid.Text("No"))
		elif alertLevel.rulesActivated == 1:
			temp.append(urwid.Text("Yes"))
		else:
			temp.append(urwid.Text("Undefined"))

		return temp


	# this function creates the detailed output of a node object
	# in a list
	def _createNodeWidgetList(self, node):

		temp = list()

		temp.append(urwid.Text("Node ID:"))
		temp.append(urwid.Text(str(node.nodeId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Username:"))
		temp.append(urwid.Text(node.username))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Hostname:"))
		temp.append(urwid.Text(node.hostname))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Node Type:"))
		temp.append(urwid.Text(node.nodeType))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Instance:"))
		temp.append(urwid.Text(node.instance))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Version:"))
		versionWidget = urwid.Text(str(node.version) + "-" + str(node.rev))
		temp.append(versionWidget)
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Connected:"))
		if node.connected == 0:
			temp.append(urwid.AttrMap(urwid.Text("False"),
				"disconnected"))
		elif node.connected == 1:
			temp.append(urwid.AttrMap(urwid.Text("True"),
				"neutral"))
		else:
			temp.append(urwid.AttrMap(urwid.Text("Undefined"),
				"redColor"))

		return temp


	# this function creates the detailed output of a sensor object
	# in a list
	def _createSensorWidgetList(self, sensor):

		temp = list()

		temp.append(urwid.Text("Sensor ID:"))
		temp.append(urwid.Text(str(sensor.sensorId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Remote Sensor ID:"))
		temp.append(urwid.Text(str(sensor.remoteSensorId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Alert Delay:"))
		temp.append(urwid.Text(str(sensor.alertDelay) + " Seconds"))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Description:"))
		temp.append(urwid.Text(sensor.description))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("State:"))
		if sensor.state == 0:
			temp.append(urwid.AttrMap(urwid.Text("Normal"),
				"neutral"))
		elif sensor.state == 1:
			temp.append(urwid.AttrMap(urwid.Text("Triggered"),
				"sensoralert"))
		else:
			temp.append(urwid.AttrMap(urwid.Text("Undefined"),
				"redColor"))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Last Updated (Server Time):"))
		lastUpdatedWidget = urwid.Text(time.strftime("%D %H:%M:%S",
			time.localtime(sensor.lastStateUpdated)))
		temp.append(lastUpdatedWidget)

		return temp


	# this function returns the final urwid widget that is used
	# to render this object
	def get(self):
		return self.detailedBox


	# this function updates all internal widgets
	def updateCompleteWidget(self, alertLevels):

		self.updateNodeDetails()
		self.updateSensorDetails()
		self.updateAlertLevelsDetails(alertLevels)


	# this function updates the alert levels information shown
	def updateAlertLevelsDetails(self, alertLevels):

		# crate new sensor pile content
		temp = self._createAlertLevelsWidgetList(alertLevels)
		
		# create a list of tuples for the pile widget
		pileOptions = self.alertLevelsPileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.alertLevelsPileWidget.contents[:]
		self.alertLevelsPileWidget.contents.extend(temp)


	# this function updates the node information shown
	def updateNodeDetails(self):

		# crate new sensor pile content
		temp = self._createNodeWidgetList(self.node)
		
		# create a list of tuples for the pile widget
		pileOptions = self.nodePileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.nodePileWidget.contents[:]
		self.nodePileWidget.contents.extend(temp)


	# this function updates the sensor information shown
	def updateSensorDetails(self):

		# crate new sensor pile content
		temp = self._createSensorWidgetList(self.sensor)
		
		# create a list of tuples for the pile widget
		pileOptions = self.sensorPileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.sensorPileWidget.contents[:]
		self.sensorPileWidget.contents.extend(temp)


# this class is an urwid object for an alert
class AlertUrwid:

	def __init__(self, alert, node):

		# store reference to alert object and node object
		self.alert = alert
		self.node = node

		# store reference in alert object to this urwid alert object
		self.alert.alertUrwid = self

		alertPileList = list()
		self.descriptionWidget = urwid.Text("Desc.: " + self.alert.description)
		alertPileList.append(self.descriptionWidget)

		alertPile = urwid.Pile(alertPileList)
		alertBox = urwid.LineBox(alertPile, title=node.hostname)
		paddedAlertBox = urwid.Padding(alertBox, left=1, right=1)

		# check if node is connected and set the color accordingly
		if self.node.connected == 0:
			self.alertUrwidMap = urwid.AttrMap(paddedAlertBox,
				"disconnected")
			self.alertUrwidMap.set_focus_map({None: "disconnected_focus"})
		else:
			self.alertUrwidMap = urwid.AttrMap(paddedAlertBox, "connected")
			self.alertUrwidMap.set_focus_map({None: "connected_focus"})


	# this function returns the final urwid widget that is used
	# to render the box of an alert
	def get(self):
		return self.alertUrwidMap


	# this function updates the description of the object
	def updateDescription(self, description):
		self.descriptionWidget.set_text("Desc.: " + description)


	# this function updates the connected status of the object
	# (and changes color arcordingly)
	def updateConnected(self, connected):

		# change color according to connection state
		if connected == 0:
			self.alertUrwidMap.set_attr_map({None: "disconnected"})
			self.alertUrwidMap.set_focus_map({None: "disconnected_focus"})
		else:
			self.alertUrwidMap.set_attr_map({None: "connected"})
			self.alertUrwidMap.set_focus_map({None: "connected_focus"})


	# this function updates all internal widgets and checks if
	# the alert/node still exists
	def updateCompleteWidget(self):

		# check if alert/node still exists
		if (self.alert is None
			or self.node is None):

			# return false if object no longer exists
			return False

		self.updateDescription(self.alert.description)
		self.updateConnected(self.node.connected)

		# return true if object was updated
		return True


	# this functions sets the color when the connection to the server
	# has failed
	def setConnectionFail(self):
		self.alertUrwidMap.set_attr_map({None: "connectionfail"})
		self.alertUrwidMap.set_focus_map({None: "connectionfail_focus"})


# this class is an urwid object for a detailed alert output
class AlertDetailedUrwid:

	def __init__(self, alert, node, alertLevels):

		self.node = node
		self.alert = alert

		content = list()

		content.append(urwid.Divider("="))
		content.append(urwid.Text("Node"))
		content.append(urwid.Divider("="))
		temp = self._createNodeWidgetList(node)
		self.nodePileWidget = urwid.Pile(temp)
		content.append(self.nodePileWidget)

		content.append(urwid.Divider())
		content.append(urwid.Divider("="))
		content.append(urwid.Text("Alert"))
		content.append(urwid.Divider("="))
		temp = self._createAlertWidgetList(alert)
		self.alertPileWidget = urwid.Pile(temp)
		content.append(self.alertPileWidget)

		content.append(urwid.Divider())
		content.append(urwid.Divider("="))
		content.append(urwid.Text("Alert Levels"))
		content.append(urwid.Divider("="))
		temp = self._createAlertLevelsWidgetList(alertLevels)
		self.alertLevelsPileWidget = None
		if temp:
			self.alertLevelsPileWidget = urwid.Pile(temp)
		else:
			self.alertLevelsPileWidget = urwid.Pile([urwid.Text("None")])
		content.append(self.alertLevelsPileWidget)

		# use ListBox here because it handles all the
		# scrolling part automatically
		detailedList = urwid.ListBox(content)
		detailedFrame = urwid.Frame(detailedList,
			footer=urwid.Text("Keys: ESC - Back, Up/Down - Scrolling"))
		self.detailedBox = urwid.LineBox(detailedFrame,
			title="Alert: " + self.alert.description)


	# this function creates the detailed output of all alert level objects
	# in a list
	def _createAlertLevelsWidgetList(self, alertLevels):

		temp = list()
		first = True
		for alertLevel in alertLevels:

			if first:
				first = False
			else:
				temp.append(urwid.Divider())
				temp.append(urwid.Divider("-"))

			temp.extend(self._createAlertLevelWidgetList(alertLevel))

		return temp


	# this function creates the detailed output of a alert level object
	# in a list
	def _createAlertLevelWidgetList(self, alertLevel):

		temp = list()

		temp.append(urwid.Text("Alert Level:"))
		temp.append(urwid.Text(str(alertLevel.level)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Name:"))
		temp.append(urwid.Text(alertLevel.name))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Trigger Always:"))
		if alertLevel.triggerAlways == 0:
			temp.append(urwid.Text("No"))
		elif alertLevel.triggerAlways == 1:
			temp.append(urwid.Text("Yes"))
		else:
			temp.append(urwid.Text("Undefined"))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Rules Activated:"))
		if alertLevel.rulesActivated == 0:
			temp.append(urwid.Text("No"))
		elif alertLevel.rulesActivated == 1:
			temp.append(urwid.Text("Yes"))
		else:
			temp.append(urwid.Text("Undefined"))

		return temp


	# this function creates the detailed output of a alert object
	# in a list
	def _createAlertWidgetList(self, alert):

		temp = list()

		temp.append(urwid.Text("Alert ID:"))
		temp.append(urwid.Text(str(alert.alertId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Remote Alert ID:"))
		temp.append(urwid.Text(str(alert.remoteAlertId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Description:"))
		temp.append(urwid.Text(alert.description))

		return temp


	# this function creates the detailed output of a node object
	# in a list
	def _createNodeWidgetList(self, node):

		temp = list()

		temp.append(urwid.Text("Node ID:"))
		temp.append(urwid.Text(str(node.nodeId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Username:"))
		temp.append(urwid.Text(node.username))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Hostname:"))
		temp.append(urwid.Text(node.hostname))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Node Type:"))
		temp.append(urwid.Text(node.nodeType))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Instance:"))
		temp.append(urwid.Text(node.instance))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Version:"))
		versionWidget = urwid.Text(str(node.version) + "-" + str(node.rev))
		temp.append(versionWidget)
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Connected:"))
		if node.connected == 0:
			temp.append(urwid.AttrMap(urwid.Text("False"),
				"disconnected"))
		elif node.connected == 1:
			temp.append(urwid.AttrMap(urwid.Text("True"),
				"neutral"))
		else:
			temp.append(urwid.AttrMap(urwid.Text("Undefined"),
				"redColor"))

		return temp


	# this function returns the final urwid widget that is used
	# to render this object
	def get(self):
		return self.detailedBox


	# this function updates all internal widgets
	def updateCompleteWidget(self, alertLevels):

		self.updateNodeDetails()
		self.updateAlertDetails()
		self.updateAlertLevelsDetails(alertLevels)


	# this function updates the node information shown
	def updateAlertDetails(self):

		# crate new sensor pile content
		temp = self._createAlertWidgetList(self.alert)
		
		# create a list of tuples for the pile widget
		pileOptions = self.alertPileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.alertPileWidget.contents[:]
		self.alertPileWidget.contents.extend(temp)


	# this function updates the alert levels information shown
	def updateAlertLevelsDetails(self, alertLevels):

		# crate new sensor pile content
		temp = self._createAlertLevelsWidgetList(alertLevels)
		
		# create a list of tuples for the pile widget
		pileOptions = self.alertLevelsPileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.alertLevelsPileWidget.contents[:]
		self.alertLevelsPileWidget.contents.extend(temp)


	# this function updates the node information shown
	def updateNodeDetails(self):

		# crate new sensor pile content
		temp = self._createNodeWidgetList(self.node)
		
		# create a list of tuples for the pile widget
		pileOptions = self.nodePileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.nodePileWidget.contents[:]
		self.nodePileWidget.contents.extend(temp)


# this class is an urwid object for a manager
class ManagerUrwid:

	def __init__(self, manager, node):

		# store reference to manager object and node object
		self.manager = manager
		self.node = node

		# store reference in manager object to this urwid manager object
		self.manager.managerUrwid = self

		managerPileList = list()
		self.descriptionWidget = urwid.Text("Desc.: "
			+ self.manager.description)
		managerPileList.append(self.descriptionWidget)

		managerPile = urwid.Pile(managerPileList)
		managerBox = urwid.LineBox(managerPile, title=node.hostname)
		paddedManagerBox = urwid.Padding(managerBox, left=1, right=1)

		# check if node is connected and set the color accordingly
		if self.node.connected == 0:
			self.managerUrwidMap = urwid.AttrMap(paddedManagerBox,
				"disconnected")
			self.managerUrwidMap.set_focus_map({None: "disconnected_focus"})
		else:
			self.managerUrwidMap = urwid.AttrMap(paddedManagerBox, "connected")
			self.managerUrwidMap.set_focus_map({None: "connected_focus"})


	# this function returns the final urwid widget that is used
	# to render the box of a manager
	def get(self):
		return self.managerUrwidMap


	# this function updates the description of the object
	def updateDescription(self, description):
		self.descriptionWidget.set_text("Desc.: " + description)


	# this function updates the connected status of the object
	# (and changes color arcordingly)
	def updateConnected(self, connected):

		# change color according to connection state
		if connected == 0:
			self.managerUrwidMap.set_attr_map({None: "disconnected"})
			self.managerUrwidMap.set_focus_map({None: "disconnected_focus"})
		else:
			self.managerUrwidMap.set_attr_map({None: "connected"})
			self.managerUrwidMap.set_focus_map({None: "connected_focus"})


	# this function updates all internal widgets and checks if
	# the manager/node still exists
	def updateCompleteWidget(self):

		# check if manager/node still exists
		if (self.manager is None
			or self.node is None):

			# return false if object no longer exists
			return False

		self.updateDescription(self.manager.description)
		self.updateConnected(self.node.connected)

		# return true if object was updated
		return True


	# this functions sets the color when the connection to the server
	# has failed
	def setConnectionFail(self):
		self.managerUrwidMap.set_attr_map({None: "connectionfail"})
		self.managerUrwidMap.set_focus_map({None: "connectionfail_focus"})


# this class is an urwid object for a detailed manager output
class ManagerDetailedUrwid:

	def __init__(self, manager, node):

		self.node = node
		self.manager = manager

		content = list()

		content.append(urwid.Divider("="))
		content.append(urwid.Text("Node"))
		content.append(urwid.Divider("="))
		temp = self._createNodeWidgetList(node)
		self.nodePileWidget = urwid.Pile(temp)
		content.append(self.nodePileWidget)

		content.append(urwid.Divider())
		content.append(urwid.Divider("="))
		content.append(urwid.Text("Manager"))
		content.append(urwid.Divider("="))
		temp = self._createManagerWidgetList(manager)
		self.managerPileWidget = urwid.Pile(temp)
		content.append(self.managerPileWidget)

		# use ListBox here because it handles all the
		# scrolling part automatically
		detailedList = urwid.ListBox(content)
		detailedFrame = urwid.Frame(detailedList,
			footer=urwid.Text("Keys: ESC - Back, Up/Down - Scrolling"))
		self.detailedBox = urwid.LineBox(detailedFrame,
			title="Manager: " + self.manager.description)


	# this function creates the detailed output of a alert object
	# in a list
	def _createManagerWidgetList(self, manager):

		temp = list()

		temp.append(urwid.Text("Manager ID:"))
		temp.append(urwid.Text(str(manager.managerId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Description:"))
		temp.append(urwid.Text(manager.description))

		return temp


	# this function creates the detailed output of a node object
	# in a list
	def _createNodeWidgetList(self, node):

		temp = list()

		temp.append(urwid.Text("Node ID:"))
		temp.append(urwid.Text(str(node.nodeId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Username:"))
		temp.append(urwid.Text(node.username))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Hostname:"))
		temp.append(urwid.Text(node.hostname))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Node Type:"))
		temp.append(urwid.Text(node.nodeType))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Instance:"))
		temp.append(urwid.Text(node.instance))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Version:"))
		versionWidget = urwid.Text(str(node.version) + "-" + str(node.rev))
		temp.append(versionWidget)
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Connected:"))
		if node.connected == 0:
			temp.append(urwid.AttrMap(urwid.Text("False"),
				"disconnected"))
		elif node.connected == 1:
			temp.append(urwid.AttrMap(urwid.Text("True"),
				"neutral"))
		else:
			temp.append(urwid.AttrMap(urwid.Text("Undefined"),
				"redColor"))

		return temp


	# this function returns the final urwid widget that is used
	# to render this object
	def get(self):
		return self.detailedBox


	# this function updates all internal widgets
	def updateCompleteWidget(self):

		self.updateNodeDetails()
		self.updateManagerDetails()


	# this function updates the node information shown
	def updateManagerDetails(self):

		# crate new sensor pile content
		temp = self._createManagerWidgetList(self.manager)
		
		# create a list of tuples for the pile widget
		pileOptions = self.managerPileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.managerPileWidget.contents[:]
		self.managerPileWidget.contents.extend(temp)


	# this function updates the node information shown
	def updateNodeDetails(self):

		# crate new sensor pile content
		temp = self._createNodeWidgetList(self.node)
		
		# create a list of tuples for the pile widget
		pileOptions = self.nodePileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.nodePileWidget.contents[:]
		self.nodePileWidget.contents.extend(temp)


# this class is an urwid object for an alert level
class AlertLevelUrwid:

	def __init__(self, alertLevel):

		# store reference to alert level object
		self.alertLevel = alertLevel

		# store reference in alert level object to
		# this urwid alert level object
		self.alertLevel.alertLevelUrwid = self

		alertLevelPileList = list()
		self.nameWidget = urwid.Text("Name: "
			+ self.alertLevel.name)
		alertLevelPileList.append(self.nameWidget)

		alertLevelPile = urwid.Pile(alertLevelPileList)
		alertLevelBox = urwid.LineBox(alertLevelPile, title="Level: %d" %
			self.alertLevel.level)
		paddedAlertLevelBox = urwid.Padding(alertLevelBox, left=1, right=1)

		# set the color of the urwid object
		self.alertLevelUrwidMap = urwid.AttrMap(paddedAlertLevelBox,
			"greenColor")
		self.alertLevelUrwidMap.set_focus_map({None: "greenColor_focus"})


	# this function returns the final urwid widget that is used
	# to render the box of an alert level
	def get(self):
		return self.alertLevelUrwidMap


	# this function updates the description of the object
	def updateName(self, name):
		self.nameWidget.set_text("Name: " + name)


	# this function changes the color of this urwid object to red
	def turnRed(self):
		self.alertLevelUrwidMap.set_attr_map({None: "redColor"})
		self.alertLevelUrwidMap.set_focus_map({None: "redColor_focus"})


	# this function changes the color of this urwid object to green
	def turnGreen(self):
		self.alertLevelUrwidMap.set_attr_map({None: "greenColor"})
		self.alertLevelUrwidMap.set_focus_map({None: "greenColor_focus"})


	# this function changes the color of this urwid object to gray
	def turnGray(self):
		self.alertLevelUrwidMap.set_attr_map({None: "grayColor"})
		self.alertLevelUrwidMap.set_focus_map({None: "grayColor_focus"})


	# this function changes the color of this urwid object to the
	# neutral color scheme
	def turnNeutral(self):
		self.alertLevelUrwidMap.set_attr_map({None: "neutral"})


	# this function updates all internal widgets and checks if
	# the alert level still exists
	def updateCompleteWidget(self):

		# check if alert level still exists
		if (self.alertLevel is None):

			# return false if object no longer exists
			return False

		self.turnGreen()
		self.updateName(self.alertLevel.name)

		# return true if object was updated
		return True


	# this functions sets the color when the connection to the server
	# has failed
	def setConnectionFail(self):
		self.alertLevelUrwidMap.set_attr_map({None: "connectionfail"})
		self.alertLevelUrwidMap.set_focus_map({None: "connectionfail_focus"})


# this class is an urwid object for a detailed alert level output
class AlertLevelDetailedUrwid:

	def __init__(self, alertLevel, sensors, alerts):

		self.alertLevel = alertLevel

		content = list()

		content.append(urwid.Divider("="))
		content.append(urwid.Text("Alert Level"))
		content.append(urwid.Divider("="))
		temp = self._createAlertLevelWidgetList(alertLevel)
		self.alertLevelPileWidget = urwid.Pile(temp)
		content.append(self.alertLevelPileWidget)

		content.append(urwid.Divider())
		content.append(urwid.Divider("="))
		content.append(urwid.Text("Alerts"))
		content.append(urwid.Divider("="))
		temp = self._createAlertsWidgetList(alerts)
		self.alertsPileWidget = None
		if temp:
			self.alertsPileWidget = urwid.Pile(temp)
		else:
			self.alertsPileWidget = urwid.Pile([urwid.Text("None")])
		content.append(self.alertsPileWidget)

		content.append(urwid.Divider())
		content.append(urwid.Divider("="))
		content.append(urwid.Text("Sensors"))
		content.append(urwid.Divider("="))
		temp = self._createSensorsWidgetList(sensors)
		self.sensorsPileWidget = None
		if temp:
			self.sensorsPileWidget = urwid.Pile(temp)
		else:
			self.sensorsPileWidget = urwid.Pile([urwid.Text("None")])
		content.append(self.sensorsPileWidget)

		# use ListBox here because it handles all the
		# scrolling part automatically
		detailedList = urwid.ListBox(content)
		detailedFrame = urwid.Frame(detailedList,
			footer=urwid.Text("Keys: ESC - Back, Up/Down - Scrolling"))
		self.detailedBox = urwid.LineBox(detailedFrame,
			title="Alert Level: " + self.alertLevel.name)


	# this function creates the detailed output of a alert level object
	# in a list
	def _createAlertLevelWidgetList(self, alertLevel):

		temp = list()

		temp.append(urwid.Text("Alert Level:"))
		temp.append(urwid.Text(str(alertLevel.level)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Name:"))
		temp.append(urwid.Text(alertLevel.name))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Trigger Always:"))
		if alertLevel.triggerAlways == 0:
			temp.append(urwid.Text("No"))
		elif alertLevel.triggerAlways == 1:
			temp.append(urwid.Text("Yes"))
		else:
			temp.append(urwid.Text("Undefined"))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Rules Activated:"))
		if alertLevel.rulesActivated == 0:
			temp.append(urwid.Text("No"))
		elif alertLevel.rulesActivated == 1:
			temp.append(urwid.Text("Yes"))
		else:
			temp.append(urwid.Text("Undefined"))

		return temp


	# this function creates the detailed output of all alert objects
	# in a list
	def _createAlertsWidgetList(self, alerts):

		temp = list()
		first = True
		for alert in alerts:

			if first:
				first = False
			else:
				temp.append(urwid.Divider())
				temp.append(urwid.Divider("-"))

			temp.extend(self._createAlertWidgetList(alert))

		return temp


	# this function creates the detailed output of a alert object
	# in a list
	def _createAlertWidgetList(self, alert):

		temp = list()

		temp.append(urwid.Text("Alert ID:"))
		temp.append(urwid.Text(str(alert.alertId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Remote Alert ID:"))
		temp.append(urwid.Text(str(alert.remoteAlertId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Description:"))
		temp.append(urwid.Text(alert.description))

		return temp


	# this function creates the detailed output of a node object
	# in a list
	def _createNodeWidgetList(self, node):

		temp = list()

		temp.append(urwid.Text("Node ID:"))
		temp.append(urwid.Text(str(node.nodeId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Username:"))
		temp.append(urwid.Text(node.username))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Hostname:"))
		temp.append(urwid.Text(node.hostname))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Node Type:"))
		temp.append(urwid.Text(node.nodeType))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Instance:"))
		temp.append(urwid.Text(node.instance))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Version:"))
		versionWidget = urwid.Text(str(node.version) + "-" + str(node.rev))
		temp.append(versionWidget)
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Connected:"))
		if node.connected == 0:
			temp.append(urwid.AttrMap(urwid.Text("False"),
				"disconnected"))
		elif node.connected == 1:
			temp.append(urwid.AttrMap(urwid.Text("True"),
				"neutral"))
		else:
			temp.append(urwid.AttrMap(urwid.Text("Undefined"),
				"redColor"))

		return temp


	# this function creates the detailed output of all sensor objects
	# in a list
	def _createSensorsWidgetList(self, sensors):

		temp = list()
		first = True
		for sensor in sensors:

			if first:
				first = False
			else:
				temp.append(urwid.Divider())
				temp.append(urwid.Divider("-"))

			temp.extend(self._createSensorWidgetList(sensor))

		return temp


	# this function creates the detailed output of a sensor object
	# in a list
	def _createSensorWidgetList(self, sensor):

		temp = list()

		temp.append(urwid.Text("Sensor ID:"))
		temp.append(urwid.Text(str(sensor.sensorId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Remote Sensor ID:"))
		temp.append(urwid.Text(str(sensor.remoteSensorId)))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Alert Delay:"))
		temp.append(urwid.Text(str(sensor.alertDelay) + " Seconds"))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Description:"))
		temp.append(urwid.Text(sensor.description))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("State:"))
		if sensor.state == 0:
			temp.append(urwid.AttrMap(urwid.Text("Normal"),
				"neutral"))
		elif sensor.state == 1:
			temp.append(urwid.AttrMap(urwid.Text("Triggered"),
				"sensoralert"))
		else:
			temp.append(urwid.AttrMap(urwid.Text("Undefined"),
				"redColor"))
		temp.append(urwid.Divider())

		temp.append(urwid.Text("Last Updated (Server Time):"))
		lastUpdatedWidget = urwid.Text(time.strftime("%D %H:%M:%S",
			time.localtime(sensor.lastStateUpdated)))
		temp.append(lastUpdatedWidget)

		return temp


	# this function returns the final urwid widget that is used
	# to render this object
	def get(self):
		return self.detailedBox


	# this function updates all internal widgets
	def updateCompleteWidget(self, sensors, alerts):

		self.updateAlertLevelDetails()
		self.updateSensorsDetails(sensors)
		self.updateAlertsDetails(alerts)


	# this function updates the alert level information shown
	def updateAlertLevelDetails(self):

		# crate new sensor pile content
		temp = self._createAlertLevelWidgetList(self.alertLevel)
		
		# create a list of tuples for the pile widget
		pileOptions = self.alertLevelPileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.alertLevelPileWidget.contents[:]
		self.alertLevelPileWidget.contents.extend(temp)


	# this function updates the node information shown
	def updateAlertsDetails(self, alerts):

		# crate new sensor pile content
		temp = self._createAlertsWidgetList(alerts)
		
		# create a list of tuples for the pile widget
		pileOptions = self.alertsPileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.alertsPileWidget.contents[:]
		self.alertsPileWidget.contents.extend(temp)


	# this function updates the sensor information shown
	def updateSensorsDetails(self, sensors):

		# crate new sensor pile content
		temp = self._createSensorsWidgetList(sensors)
		
		# create a list of tuples for the pile widget
		pileOptions = self.sensorsPileWidget.options()
		temp = map(lambda x: (x, pileOptions), temp)

		# empty pile widget contents and replace it with the new widgets
		del self.sensorsPileWidget.contents[:]
		self.sensorsPileWidget.contents.extend(temp)


# this class is an urwid object for a sensor alert
class SensorAlertUrwid:

	def __init__(self, sensorAlert, description, timeShowSensorAlert):

		self.sensorAlert = sensorAlert
		self.description = description
		self.timeReceived = self.sensorAlert.timeReceived
		self.timeShowSensorAlert = timeShowSensorAlert

		# generate formatted string from alert levels
		alertLevelsString = ""
		first = True
		for alertLevel in self.sensorAlert.alertLevels:
			if first:
				first = False
			else:
				alertLevelsString += ", "
			alertLevelsString += str(alertLevel)

		# generate the internal urwid widgets
		stringReceivedTime = time.strftime("%D %H:%M:%S",
			time.localtime(self.timeReceived))	
		self.textWidget = urwid.Text(stringReceivedTime + " - " +
			self.description + " (" + alertLevelsString + ")")
		

	# this function returns the final urwid widget that is used
	# to render the sensor alert
	def get(self):
		return self.textWidget


	# this function checks if the sensor alert widget is too old
	def sensorAlertOutdated(self):
		# check if the sensor alert is older than the configured time to
		# show the sensor alerts in the list
		if (int(time.time()) - self.timeReceived) > self.timeShowSensorAlert:
			return True
		return False