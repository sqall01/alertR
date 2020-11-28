#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import copy
import threading
from typing import Optional, List, Any, Dict


class InternalState:
    NOT_USED = 0
    STORED = 1
    DELETED = 2


# This enum class gives the different data types of a sensor.
class SensorDataType:
    NONE = 0
    INT = 1
    FLOAT = 2


class LocalObject:

    def __init__(self):
        # Internal data used by the manager.
        self.internal_state = InternalState.NOT_USED
        self.internal_data = dict()

        # To lock internal data structure if necessary for multi threaded programs.
        self.internal_data_lock = threading.Lock()

    def is_deleted(self):
        return self.internal_state == InternalState.DELETED

    def is_stored(self):
        return self.internal_state == InternalState.STORED

    def deepcopy(self, obj):
        raise NotImplementedError("Abstract class.")


# this class represents an option of the server
class Option(LocalObject):

    def __init__(self):
        super().__init__()
        self.type = None  # type: Optional[str]
        self.value = None  # type: Optional[float]

    def deepcopy(self, option):
        self.type = option.type
        self.value = option.value
        return self


# this class represents an node/client of the alert system
# which can be either a sensor, alert or manager
class Node(LocalObject):

    def __init__(self):
        super().__init__()
        self.nodeId = None  # type: Optional[int]
        self.hostname = None  # type: Optional[str]
        self.nodeType = None  # type: Optional[str]
        self.instance = None  # type: Optional[str]
        self.connected = None  # type: Optional[int]
        self.version = None  # type: Optional[float]
        self.rev = None  # type: Optional[int]
        self.username = None  # type: Optional[str]
        self.persistent = None  # type: Optional[int]

    # This function copies all attributes of the given node to this object.
    def deepcopy(self, node):
        self.nodeId = node.nodeId
        self.hostname = node.hostname
        self.nodeType = node.nodeType
        self.instance = node.instance
        self.connected = node.connected
        self.version = node.version
        self.rev = node.rev
        self.username = node.username
        self.persistent = node.persistent
        return self


# this class represents a sensor client of the alert system
class Sensor(LocalObject):

    def __init__(self):
        super().__init__()
        self.nodeId = None  # type: Optional[int]
        self.sensorId = None  # type: Optional[int]
        self.remoteSensorId = None  # type: Optional[int]
        self.alertDelay = None  # type: Optional[int]
        self.alertLevels = list()  # type: List[int]
        self.description = None  # type: Optional[str]
        self.lastStateUpdated = None  # type: Optional[int]
        self.state = None  # type: Optional[int]
        self.dataType = None  # type: Optional[int]
        self.data = None  # type: Any

    # This function copies all attributes of the given sensor to this object.
    def deepcopy(self, sensor):
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
        return self


# this class represents a manager client of the alert system
class Manager(LocalObject):

    def __init__(self):
        super().__init__()
        self.nodeId = None  # type: Optional[int]
        self.managerId = None  # type: Optional[int]
        self.description = None  # type: Optional[str]

    # This function copies all attributes of the given manager to this object.
    def deepcopy(self, manager):
        self.nodeId = manager.nodeId
        self.managerId = manager.managerId
        self.description = manager.description
        return self


# this class represents an alert client of the alert system
class Alert(LocalObject):

    def __init__(self):
        super().__init__()
        self.nodeId = None  # type: Optional[int]
        self.alertId = None  # type: Optional[int]
        self.remoteAlertId = None  # type: Optional[int]
        self.alertLevels = list()  # type: List[int]
        self.description = None  # type: Optional[str]

    # This function copies all attributes of the given alert to this object.
    def deepcopy(self, alert):
        self.nodeId = alert.nodeId
        self.alertId = alert.alertId
        self.remoteAlertId = alert.remoteAlertId
        self.alertLevels = list(alert.alertLevels)
        self.description = alert.description
        return self


# this class represents a triggered sensor alert of the alert system
class SensorAlert(LocalObject):

    def __init__(self):
        super().__init__()

        self.sensorId = None  # type: Optional[int]

        # State of the sensor alert ("triggered" = 1; "normal" = 0).
        self.state = None  # type: Optional[int]

        # Description of the sensor that raised this sensor alert.
        self.description = None  # type: Optional[str]

        # Time this sensor alert was received.
        self.timeReceived = None  # type: Optional[int]

        # List of alert levels (Integer) that are triggered
        # by this sensor alert.
        self.alertLevels = list()  # type: List[int]

        # The optional data of the sensor alert (if it has any).
        self.hasOptionalData = None  # type: Optional[bool]
        self.optionalData = None  # type: Dict[str, Any]

        # Does this sensor alert change the state of the sensor?
        self.changeState = None  # type: Optional[bool]

        # Does this sensor alert hold the latest data of the sensor?
        self.hasLatestData = None  # type: Optional[bool]

        # The sensor data type and data that is connected to this sensor alert.
        self.dataType = None  # type: Optional[int]
        self.sensorData = None  # type: Any

    def __str__(self):
        tmp = "Sensor Alert (Description: '%s'; " \
              % self.description \
              + "SensorID: %s; " \
              % str(self.sensorId) if self.sensorId is not None else "None" \
              + "State: %s; " \
              % str(self.state) if self.state is not None else "None" \
              + "Time Received: %s; " \
              % str(self.timeReceived) if self.timeReceived is not None else "None" \
              + "Alert Levels: %s)" \
              % ", ".join(map(str, self.alertLevels))
        return tmp

    # This function copies all attributes of the given sensor alert to this object.
    def deepcopy(self, sensor_alert):
        self.sensorId = sensor_alert.sensorId
        self.state = sensor_alert.state
        self.description = sensor_alert.description
        self.timeReceived = sensor_alert.timeReceived
        self.alertLevels = list(sensor_alert.alertLevels)
        self.hasOptionalData = sensor_alert.hasOptionalData
        self.changeState = sensor_alert.changeState
        self.hasLatestData = sensor_alert.hasLatestData
        self.dataType = sensor_alert.dataType
        self.sensorData = sensor_alert.sensorData

        if type(sensor_alert.optionalData) == dict:
            self.optionalData = copy.deepcopy(sensor_alert.optionalData)

        else:
            self.optionalData = None

        return self


# this class represents an alert level that is configured on the server
class AlertLevel(LocalObject):

    def __init__(self):
        super().__init__()
        self.level = None  # type: Optional[int]
        self.name = None  # type: Optional[str]
        self.triggerAlways = None  # type: Optional[int]
        self.instrumentation_active = None  # type: Optional[bool]
        self.instrumentation_cmd = None  # type: Optional[str]
        self.instrumentation_timeout = None  # type: Optional[int]

    # This function copies all attributes of the given alert level to this object.
    def deepcopy(self, alert_level):
        self.level = alert_level.level
        self.name = alert_level.name
        self.triggerAlways = alert_level.triggerAlways
        self.instrumentation_active = alert_level.instrumentation_active
        if self.instrumentation_active:
            self.instrumentation_cmd = alert_level.instrumentation_cmd
            self.instrumentation_timeout = alert_level.instrumentation_timeout

        else:
            self.instrumentation_cmd = None
            self.instrumentation_timeout = None
        return self
