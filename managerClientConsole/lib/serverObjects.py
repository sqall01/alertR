#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

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
		self.connected = None

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
		self.alertLevel = None
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


# this class represents an alert client of the alert system
class Alert:

	def __init__(self):
		self.nodeId = None
		self.alertId = None
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
		self.sensorId = None
		self.state = None
		self.timeReceived = None