#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# This enum class gives the different data types of a sensor.
class SensorDataType:
	NONE = 0
	INT = 1
	FLOAT = 2


# This class represents a single sensor of a client.
class Sensor:

	def __init__(self):
		self.sensorId = None
		self.nodeId = None
		self.remoteSensorId = None
		self.description = None
		self.state = None
		self.alertLevels = list()
		self.lastStateUpdated = None
		self.alertDelay = None
		self.dataType = None
		self.data = None


# This class represents a single alert level that is configured.
class AlertLevel:

	def __init__(self):

		# this value indicates the alert level
		self.level = None

		# gives the name of this alert level
		self.name = None

		# this flag indicates if a sensor alert with this alert level
		# should trigger regardless of if the alert system is active or not
		self.triggerAlways = None

		# this flag tells if the alert level should trigger a sensor alert
		# if the sensor goes to state "triggered"
		self.triggerAlertTriggered = None

		# this flag tells if the alert level should also trigger a sensor alert
		# if the sensor goes to state "normal"
		self.triggerAlertNormal = None

		# this flag tells if the alert level has rules activated
		# that has to match before an alert is triggered (flag: True) or
		# if it just triggers when a sensor alert is received (flag: False)
		self.rulesActivated = None

		# a list of rules (rule chain) that have to evaluate before the
		# alert level triggers a sensor alert
		# (the order in which the elements are stored in this list is the
		# order in which the rules have to evaluate)
		self.rules = list()


# This class represents a single sensor alert that was triggered.
class SensorAlert:

	def __init__(self):
		self.sensorAlertId = None
		self.nodeId = None

		# If rulesActivated = true => always set to -1.
		self.sensorId = None

		# Description of the sensor that raised this sensor alert.
		self.description = None

		# Time this sensor alert was received.
		self.timeReceived = None

		# The delay this sensor alert has before it can be triggered.
		self.alertDelay = None

		# State of the sensor alert ("triggered" = 1; "normal" = 0).
		# If rulesActivated = true => always set to 1.
		self.state = None

		# The optional data of the sensor alert (if it has any).
		# If rulesActivated = true => always set to false.
		self.hasOptionalData = None
		self.optionalData = None

		# Does this sensor alert change the state of the sensor?
		self.changeState = None

		# List of alert levels (Integer) that are triggered
		# by this sensor alert.
		self.alertLevels = list()

		# Are rules for this sensor alert activated (true or false)?
		self.rulesActivated = None

		# Does this sensor alert hold the latest data of the sensor?
		self.hasLatestData = None

		# The sensor data type and data that is connected to this sensor alert.
		self.dataType = None
		self.sensorData = None