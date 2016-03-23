#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.


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