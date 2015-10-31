#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.


# base class for events
class Event:

	def __init__(self, timeOccurred):
		self.timeOccurred = timeOccurred


# class that represents a sensor alert event
class EventSensorAlert(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.description = None
		self.state = None
		self.alertLevels = list()


# class that represents a state change event
class EventStateChange(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.hostname = None
		self.description = None
		self.state = None


# class that represents a node changed its connection state event
class EventConnectedChange(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.hostname = None
		self.nodeType = None
		self.instance = None
		self.connected = None


# class that represents a sensor time out event
class EventSensorTimeOut(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.hostname = None
		self.description = None
		self.state = None


# class that represents a new version for node available event
class EventNewVersion(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.usedVersion = None
		self.usedRev = None
		self.newVersion = None
		self.newRev = None
		self.instance = None
		self.hostname = None


# class that represents a new option received event
class EventNewOption(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.type = None
		self.value = None


# class that represents a new node received event
class EventNewNode(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.hostname = None
		self.nodeType = None
		self.instance = None


# class that represents a new sensor received event
class EventNewSensor(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.hostname = None
		self.description = None
		self.state = None


# class that represents a new alert received event
class EventNewAlert(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.hostname = None
		self.description = None


# class that represents a new manager received event
class EventNewManager(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.hostname = None
		self.description = None


# class that represents an option has changed event
class EventChangeOption(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.type = None
		self.oldValue = None
		self.newValue = None


# class that represents a node has changed event
class EventChangeNode(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.oldHostname = None
		self.oldNodeType = None
		self.oldInstance = None
		self.oldVersion = None
		self.oldRev = None
		self.oldUsername = None
		self.newHostname = None
		self.newNodeType = None
		self.newInstance = None
		self.newVersion = None
		self.newRev = None
		self.newUsername = None


# class that represents a sensor has changed event
class EventChangeSensor(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.oldAlertDelay = None
		self.oldDescription = None
		self.oldRemoteSensorId = None
		self.newAlertDelay = None
		self.newDescription = None
		self.newRemoteSensorId = None


# class that represents an alert has changed event
class EventChangeAlert(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.oldDescription = None
		self.oldRemoteAlertId = None
		self.newDescription = None
		self.newRemoteAlertId = None


# class that represents a manager has changed event
class EventChangeManager(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.oldDescription = None
		self.newDescription = None


# class that represents a node was deleted event
class EventDeleteNode(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.hostname = None
		self.nodeType = None
		self.instance = None


# class that represents a sensor was deleted event
class EventDeleteSensor(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.description = None


# class that represents an alert was deleted event
class EventDeleteAlert(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.description = None


# class that represents a manager was deleted event
class EventDeleteManager(Event):

	def __init__(self, timeOccurred):
		Event.__init__(self, timeOccurred)
		self.description = None