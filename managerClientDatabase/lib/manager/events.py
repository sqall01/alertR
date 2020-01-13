#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import Optional, Any


# base class for events
class Event:

    def __init__(self, timeOccurred: int):
        self.timeOccurred = timeOccurred


# class that represents a sensor alert event
class EventSensorAlert(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.description = None  # type: Optional[str]
        self.state = None  # type: Optional[int]
        self.alertLevels = list()
        self.dataType = None  # type: Optional[int]
        self.sensorData = None  # type: Any


# class that represents a state change event
class EventStateChange(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.hostname = None  # type: Optional[str]
        self.description = None  # type: Optional[str]
        self.state = None  # type: Optional[int]
        self.dataType = None  # type: Optional[int]
        self.data = None  # type: Any


# class that represents a node changed its connection state event
class EventConnectedChange(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.hostname = None  # type: Optional[str]
        self.nodeType = None  # type: Optional[str]
        self.instance = None  # type: Optional[str]
        self.connected = None  # type: Optional[int]


# class that represents a sensor time out event
class EventSensorTimeOut(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.hostname = None  # type: Optional[str]
        self.description = None  # type: Optional[str]
        self.state = None  # type: Optional[int]


# class that represents a new version for node available event
class EventNewVersion(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.usedVersion = None  # type: Optional[float]
        self.usedRev = None  # type: Optional[int]
        self.newVersion = None  # type: Optional[float]
        self.newRev = None  # type: Optional[int]
        self.instance = None  # type: Optional[str]
        self.hostname = None  # type: Optional[str]


# class that represents a new option received event
class EventNewOption(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.type = None  # type: Optional[str]
        self.value = None  # type: Optional[float]


# class that represents a new node received event
class EventNewNode(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.hostname = None  # type: Optional[str]
        self.nodeType = None  # type: Optional[str]
        self.instance = None  # type: Optional[str]


# class that represents a new sensor received event
class EventNewSensor(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.hostname = None  # type: Optional[str]
        self.description = None  # type: Optional[str]
        self.state = None  # type: Optional[int]


# class that represents a new alert received event
class EventNewAlert(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.hostname = None  # type: Optional[str]
        self.description = None  # type: Optional[str]


# class that represents a new manager received event
class EventNewManager(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.hostname = None  # type: Optional[str]
        self.description = None  # type: Optional[str]


# class that represents an option has changed event
class EventChangeOption(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.type = None  # type: Optional[str]
        self.oldValue = None  # type: Optional[float]
        self.newValue = None  # type: Optional[float]


# class that represents a node has changed event
class EventChangeNode(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.oldHostname = None  # type: Optional[str]
        self.oldNodeType = None  # type: Optional[str]
        self.oldInstance = None  # type: Optional[str]
        self.oldVersion = None  # type: Optional[float]
        self.oldRev = None  # type: Optional[int]
        self.oldUsername = None  # type: Optional[str]
        self.oldPersistent = None  # type: Optional[int]
        self.newHostname = None  # type: Optional[str]
        self.newNodeType = None  # type: Optional[str]
        self.newInstance = None  # type: Optional[str]
        self.newVersion = None  # type: Optional[float]
        self.newRev = None  # type: Optional[int]
        self.newUsername = None  # type: Optional[str]
        self.newPersistent = None  # type: Optional[int]


# class that represents a sensor has changed event
class EventChangeSensor(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.oldAlertDelay = None  # type: Optional[int]
        self.oldDescription = None  # type: Optional[str]
        self.oldRemoteSensorId = None  # type: Optional[int]
        self.newAlertDelay = None  # type: Optional[int]
        self.newDescription = None  # type: Optional[str]
        self.newRemoteSensorId = None  # type: Optional[int]


# class that represents an alert has changed event
class EventChangeAlert(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.oldDescription = None  # type: Optional[str]
        self.oldRemoteAlertId = None  # type: Optional[int]
        self.newDescription = None  # type: Optional[str]
        self.newRemoteAlertId = None  # type: Optional[int]


# class that represents a manager has changed event
class EventChangeManager(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.oldDescription = None  # type: Optional[str]
        self.newDescription = None  # type: Optional[str]


# class that represents a node was deleted event
class EventDeleteNode(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.hostname = None  # type: Optional[str]
        self.nodeType = None  # type: Optional[str]
        self.instance = None  # type: Optional[str]


# class that represents a sensor was deleted event
class EventDeleteSensor(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.description = None  # type: Optional[str]


# class that represents an alert was deleted event
class EventDeleteAlert(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.description = None  # type: Optional[str]


# class that represents a manager was deleted event
class EventDeleteManager(Event):

    def __init__(self, timeOccurred: int):
        Event.__init__(self, timeOccurred)
        self.description = None  # type: Optional[str]
