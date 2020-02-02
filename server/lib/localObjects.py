#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import Optional, List, Any, Dict


# This class contains the error codes used by the alertr.de server.
class ErrorCodes:
    NO_ERROR = 0
    DATABASE_ERROR = 1
    AUTH_ERROR = 2
    ILLEGAL_MSG_ERROR = 3
    SESSION_EXPIRED = 4


# This enum class gives the different data types of a sensor.
class SensorDataType:
    NONE = 0
    INT = 1
    FLOAT = 2


# This class represents a single node of the system.
class Node:

    def __init__(self):
        self.id = None  # type: Optional[int]
        self.hostname = None  # type: Optional[str]
        self.username = None  # type: Optional[str]
        self.nodeType = None  # type: Optional[str]
        self.instance = None  # type: Optional[str]
        self.connected = None  # type: Optional[int]
        self.version = None  # type: Optional[float]
        self.rev = None  # type: Optional[int]
        self.persistent = None  # type: Optional[int]
        

# This class represents a single alert of a node.
class Alert:

    def __init__(self):
        self.nodeId = None  # type: Optional[int]
        self.alertId = None  # type: Optional[int]
        self.remoteAlertId = None  # type: Optional[int]
        self.alertLevels = list()  # type: List[int]
        self.description = None  # type: Optional[str]


# This class represents a single sensor of a node.
class Sensor:

    def __init__(self):
        self.sensorId = None  # type: Optional[int]
        self.nodeId = None  # type: Optional[int]
        self.remoteSensorId = None  # type: Optional[int]
        self.description = None  # type: Optional[str]
        self.state = None  # type: Optional[int]
        self.alertLevels = list()  # type: List[int]
        self.lastStateUpdated = None  # type: Optional[int]
        self.alertDelay = None  # type: Optional[int]
        self.dataType = None  # type: Optional[int]
        self.data = None


# This class represents a single manager of a node.
class Manager:

    def __init__(self):
        self.nodeId = None  # type: Optional[int]
        self.managerId = None  # type: Optional[int]
        self.description = None  # type: Optional[str]


# This class represents a single alert level that is configured.
class AlertLevel:

    def __init__(self):

        # this value indicates the alert level
        self.level = None  # type: Optional[int]

        # gives the name of this alert level
        self.name = None  # type: Optional[str]

        # this flag indicates if a sensor alert with this alert level
        # should trigger regardless of if the alert system is active or not
        self.triggerAlways = None  # type: Optional[bool]

        # this flag tells if the alert level should trigger a sensor alert
        # if the sensor goes to state "triggered"
        self.triggerAlertTriggered = None  # type: Optional[bool]

        # this flag tells if the alert level should also trigger a sensor alert
        # if the sensor goes to state "normal"
        self.triggerAlertNormal = None  # type: Optional[bool]

        # this flag tells if the alert level has rules activated
        # that has to match before an alert is triggered (flag: True) or
        # if it just triggers when a sensor alert is received (flag: False)
        self.rulesActivated = None  # type: Optional[bool]

        # a list of rules (rule chain) that have to evaluate before the
        # alert level triggers a sensor alert
        # (the order in which the elements are stored in this list is the
        # order in which the rules have to evaluate)
        self.rules = list()


# This class represents a single sensor alert that was triggered.
class SensorAlert:

    def __init__(self):
        self.sensorAlertId = None  # type: Optional[int]
        self.nodeId = None  # type: Optional[int]

        # If rulesActivated = true => always set to -1.
        self.sensorId = None  # type: Optional[int]

        # Description of the sensor that raised this sensor alert.
        self.description = None  # type: Optional[str]

        # Time this sensor alert was received.
        self.timeReceived = None  # type: Optional[int]

        # The delay this sensor alert has before it can be triggered.
        self.alertDelay = None  # type: Optional[int]

        # State of the sensor alert ("triggered" = 1; "normal" = 0).
        # If rulesActivated = true => always set to 1.
        self.state = None  # type: Optional[int]

        # The optional data of the sensor alert (if it has any).
        # If rulesActivated = true => always set to false.
        self.hasOptionalData = None  # type: Optional[bool]
        self.optionalData = None  # type: Dict[str, Any]

        # Does this sensor alert change the state of the sensor?
        self.changeState = None  # type: Optional[bool]

        # List of alert levels (Integer) that this sensor alert belongs to.
        self.alertLevels = list()  # type: List[int]

        # List of alert levels (Integer) that are currently triggered
        # by this sensor alert.
        self.triggeredAlertLevels = list()  # type: List[int]

        # Are rules for this sensor alert activated (true or false)?
        self.rulesActivated = None  # type: Optional[bool]

        # Does this sensor alert hold the latest data of the sensor?
        self.hasLatestData = None  # type: Optional[bool]

        # The sensor data type and data that is connected to this sensor alert.
        self.dataType = None  # type: Optional[int]
        self.sensorData = None  # type: Any


# This class represents sensor data.
class SensorData:

    def __init__(self):
        self.sensorId = None  # type: Optional[int]
        self.dataType = None  # type: Optional[int]
        self.data = None  # type: Any


class Option:

    def __init__(self):
        self.type = None  # type: Optional[str]
        self.value = None  # type: Optional[float]
