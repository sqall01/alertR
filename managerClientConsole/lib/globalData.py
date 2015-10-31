#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import os


# this class is a global configuration class that holds 
# values that are needed all over the client
class GlobalData:

	def __init__(self):

		# version of the used client (and protocol)
		self.version = 0.301

		# revision of the used client
		self.rev = 0

		# name of this client
		self.name = "alertR Manager Client Console"

		# the instance of this client
		self.instance = "managerClientConsole"

		# interval in which a ping should be send when 
		# no data was received/send		
		self.pingInterval = 30

		# type of this node/client
		self.nodeType = "manager"

		# path to the configuration file of the client
		self.configFile = os.path.dirname(os.path.abspath(__file__)) \
			+ "/../config/config.xml"

		# this flags indicate if email alerts via smtp are active
		self.smtpAlert = None

		# this holds the description of this client
		self.description = None

		# this is a list of all option objects that are received
		self.options = list()

		# this is a list of all node objects that are received
		self.nodes = list()

		# this is a list of all sensor objects that are received
		self.sensors = list()

		# this is a list of all manager objects that are received
		self.managers = list()

		# this is a list of all alert objects that are received
		self.alerts = list()

		# this is a list of all sensor alert objects that are received
		self.sensorAlerts = list()

		# this is a list of all alert level objects that are received
		self.alertLevels = list()

		# this is the instance of the screen updateter object that is
		# responsible of updating the screen
		self.screenUpdater = None

		# this variable holds the object of the server communication
		self.serverComm = None

		# this option tells the screen thread if
		# the "connected" information should be shown
		# for a sensor
		self.urwidSensorShowConnected = None

		# this option tells the screen thread if
		# the "alert delay" information should be shown
		# for a sensor
		self.urwidSensorShowAlertDelay = None

		# this option tells the screen thread if
		# the "last updated" information should be shown
		# for a sensor
		self.urwidSensorShowLastUpdated = None

		# this option tells the screen thread if
		# the "state" information should be shown
		# for a sensor		
		self.urwidSensorShowState = None

		# this option tells the screen thread if
		# the "alert levels" information should be shown
		# for a sensor
		self.urwidSensorShowAlertLevels = None

		# this option tells the screen thread if
		# the "alert levels" information should be shown
		# for an alert
		self.urwidAlertShowAlertLevels = None

		# this option tells the screen thread if
		# the "trigger always" information should be shown
		# for an alert level
		self.urwidAlertLevelShowTriggerAlways = None

		# this is the time in seconds when the sensor should be
		# displayed as timed out
		self.connectionTimeout = 60

		# the time in seconds how long a triggered sensor alert
		# should be displayed in the list
		self.timeShowSensorAlert = None

		# the maximum of sensor alerts that are shown in the list
		# (when the count is above this value, the oldest sensor alert
		# will be removed from the list)
		self.maxCountShowSensorAlert = None

		# the maximum number of sensors that is shown per sensor page
		self.maxCountShowSensorsPerPage = None

		# the maximum number of alerts that is shown per alert page
		self.maxCountShowAlertsPerPage = None

		# the maximum number of managers that is shown per manager page
		self.maxCountShowManagersPerPage = None

		# the maximum number of alert levels that is shown per alert level page
		self.maxCountShowAlertLevelsPerPage = None

		# this is an instance of the console object that handles
		# the screen
		self.console = None