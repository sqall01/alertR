#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# This enum class gives the different data types of a sensor.
class SensorDataType:
    NONE = 0
    INT = 1
    FLOAT = 2


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
        self.instance = None
        self.connected = None
        self.version = None
        self.rev = None
        self.username = None
        self.persistent = None

        # flag that marks this object as checked
        # (is used to verify if this object is still connected to the server)
        self.checked = False

        # used for urwid only:
        # reference to the sensor urwid object
        self.sensorUrwid = None

        # used for urwid only:
        # reference to the alert urwid object
        self.alertUrwid = None

    # This function copies all attributes of the given node to this object.
    def deepCopy(self, node):
        self.nodeId = node.nodeId
        self.hostname = node.hostname
        self.nodeType = node.nodeType
        self.instance = node.instance
        self.connected = node.connected
        self.version = node.version
        self.rev = node.rev
        self.username = node.username
        self.persistent = node.persistent


# this class represents a sensor client of the alert system
class Sensor:

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

        # flag that marks this object as checked
        # (is used to verify if this object is still connected to the server)
        self.checked = False

        # used for urwid only:
        # reference to the sensor urwid object
        self.sensorUrwid = None

    # This function copies all attributes of the given sensor to this object.
    def deepCopy(self, sensor):
        self.nodeId = sensor.nodeId
        self.sensorId = sensor.sensorId
        self.remoteSensorId = sensor.remoteSensorId
        self.alertDelay = sensor.alertDelay
        self.alertLevels = list(sensor.alertLevels)
        self.description = sensor.description
        self.lastStateUpdated = sensor.lastStateUpdated
        self.state = sensor.state
        self.dataType = sensor.dataType
        self.data = sensor.data


# this class represents a manager client of the alert system
class Manager:

    def __init__(self):
        self.nodeId = None
        self.managerId = None
        self.description = None

        # flag that marks this object as checked
        # (is used to verify if this object is still connected to the server)
        self.checked = False

        # used for urwid only:
        # reference to the manager urwid object
        self.managerUrwid = None

    # This function copies all attributes of the given manager to this object.
    def deepCopy(self, manager):
        self.nodeId = manager.nodeId
        self.managerId = manager.managerId
        self.description = manager.description


# this class represents an alert client of the alert system
class Alert:

    def __init__(self):
        self.nodeId = None
        self.alertId = None
        self.remoteAlertId = None
        self.alertLevels = list()
        self.description = None

        # flag that marks this object as checked
        # (is used to verify if this object is still connected to the server)
        self.checked = False

        # used for urwid only:
        # reference to the alert urwid object
        self.alertUrwid = None

    # This function copies all attributes of the given alert to this object.
    def deepCopy(self, alert):
        self.nodeId = alert.nodeId
        self.alertId = alert.alertId
        self.remoteAlertId = alert.remoteAlertId
        self.alertLevels = list(alert.alertLevels)
        self.description = alert.description


# this class represents a triggered sensor alert of the alert system
class SensorAlert:

    def __init__(self):

        # Are rules for this sensor alert activated (true or false)?
        self.rulesActivated = None

        # If rulesActivated = true => always set to -1.
        self.sensorId = None

        # State of the sensor alert ("triggered" = 1; "normal" = 0).
        # If rulesActivated = true => always set to 1.
        self.state = None

        # Description of the sensor that raised this sensor alert.
        self.description = None

        # Time this sensor alert was received.
        self.timeReceived = None

        # List of alert levels (Integer) that are triggered
        # by this sensor alert.
        self.alertLevels = list()

        # The optional data of the sensor alert (if it has any).
        # If rulesActivated = true => always set to false.
        self.hasOptionalData = None
        self.optionalData = None

        # Does this sensor alert change the state of the sensor?
        self.changeState = None

        # Does this sensor alert hold the latest data of the sensor?
        self.hasLatestData = None

        # The sensor data type and data that is connected to this sensor alert.
        self.dataType = None
        self.sensorData = None


# this class represents an alert level that is configured on the server
class AlertLevel:

    def __init__(self):
        self.level = None
        self.name = None
        self.triggerAlways = None
        self.rulesActivated = None

        # flag that marks this object as checked
        # (is used to verify if this object is still connected to the server)
        self.checked = False

        # used for urwid only:
        # reference to the alert urwid object
        self.alertLevelUrwid = None
