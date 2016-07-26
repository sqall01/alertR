#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

# This enum class gives the different data types of a sensor.
class SensorDataType:
	NONE = 0
	INT = 1
	FLOAT = 2


# This enum class gives the different orderings used to check if the data of a
# sensor exceeds a threshold.
class Ordering:
	LT = 0
	EQ = 1
	GT = 2


# This class represents a triggered sensor alert of the sensor.
class SensorAlert:

	def __init__(self):

		# Sensor id of the local sensor.
		self.clientSensorId = None

		# State of the sensor alert ("triggered" = 1; "normal" = 0).
		self.state = None

		# The optional data of the sensor alert (if it has any).
		self.hasOptionalData = None
		self.optionalData = None

		# Does this sensor alert change the state of the sensor?
		self.changeState = None

		# Does this sensor alert hold the latest data of the sensor?
		self.hasLatestData = None

		# The sensor data type and data that is connected to this sensor alert.
		self.dataType = None
		self.sensorData = None


# This class represents a state change of the sensor.
class StateChange:

	def __init__(self):

		# Sensor id of the local sensor.
		self.clientSensorId = None

		# State of the sensor alert ("triggered" = 1; "normal" = 0).
		self.state = None

		# The sensor data type and data that is connected to this sensor alert.
		self.dataType = None
		self.sensorData = None