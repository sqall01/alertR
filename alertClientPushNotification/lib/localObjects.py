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


# This class represents a single sensor alert that was triggered.
class SensorAlert:

	def __init__(self):
		# If rulesActivated = true => always set to -1.
		self.sensorId = None

		# Description of the sensor that raised this sensor alert.
		self.description = None

		# Time this sensor alert was received.
		self.timeReceived = None

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


	# Converts the SensorAlert object into a dictionary.
	def convertToDict(self):
		sensorAlertDict = {"alertLevels": self.alertLevels,
			"description": self.description,
			"rulesActivated": self.rulesActivated,
			"sensorId": self.sensorId,
			"state": self.state,
			"hasOptionalData": self.hasOptionalData,
			"optionalData": self.optionalData,
			"dataType": self.dataType,
			"data": self.sensorData,
			"hasLatestData": self.hasLatestData,
			"changeState": self.changeState
		}

		return sensorAlertDict