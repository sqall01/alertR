#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

from localObjects import SensorDataType


# Internal class represents an internal sensor of the alarm system server.
class _InternalSensor:

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


# Class that represents the internal sensor that
# is responsible for sensor timeouts.
class SensorTimeoutSensor(_InternalSensor):

	def __init__(self):
		_InternalSensor.__init__(self)

		self.dataType = SensorDataType.NONE

		# A set of ids of the sensors that are timed out.
		self.timeoutSensorIds = set()


# Class that represents the internal sensor that
# is responsible for node timeouts.
class NodeTimeoutSensor(_InternalSensor):

	def __init__(self):
		_InternalSensor.__init__(self)

		self.dataType = SensorDataType.NONE

		# An internal set of ids of the nodes that are timed out.
		self._timeoutNodeIds = set()


	# Returns a copy of the internal timed out node ids set.
	def getTimeoutNodeIds(self):
		return set(self._timeoutNodeIds)


# Class that represents the internal sensor that
# is responsible to trigger sensor alerts if the
# alert system changes is state from activated/deactivated
class AlertSystemActiveSensor(_InternalSensor):

	def __init__(self):
		_InternalSensor.__init__(self)

		self.dataType = SensorDataType.NONE