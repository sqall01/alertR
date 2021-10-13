#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import copy
from typing import Optional, List, Any, Dict
from .baseObjects import LocalObject
from .sensorObjects import _SensorData


# this class represents an option of the server
class ManagerObjOption(LocalObject):

    def __init__(self):
        super().__init__()
        self.type = None  # type: Optional[str]
        self.value = None  # type: Optional[int]

    def __str__(self) -> str:
        tmp = "Option (Type: '%s'; " \
              % (str(self.type) if self.type is not None else "None") \
              + "Value: %s)" \
              % (str(self.value) if self.value is not None else "None")
        return tmp

    @staticmethod
    def deepcopy(obj):
        return ManagerObjOption().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        option_dict = {"type": self.type,
                       "value": self.value,
                       }

        return option_dict

    def deepcopy_obj(self, option):
        self.type = option.type
        self.value = option.value
        return self


# this class represents a profile of the server
class ManagerObjProfile(LocalObject):

    def __init__(self):
        super().__init__()
        self.profileId = None  # type: Optional[id]
        self.name = None  # type: Optional[str]

    def __str__(self) -> str:
        tmp = "Profile (Id: %s; " \
              % (str(self.profileId) if self.profileId is not None else "None") \
              + "Name: '%s')" \
              % (str(self.name) if self.name is not None else "None")
        return tmp

    @staticmethod
    def deepcopy(obj):
        return ManagerObjProfile().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        profile_dict = {"profileId": self.profileId,
                        "name": self.name,
                        }

        return profile_dict

    def deepcopy_obj(self, profile):
        self.profileId = profile.profileId
        self.name = profile.name
        return self


# this class represents an node/client of the alert system
# which can be either a sensor, alert or manager
class ManagerObjNode(LocalObject):

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

    def __str__(self) -> str:
        tmp = "Node (Node Id: %s; " \
              % (str(self.nodeId) if self.nodeId is not None else "None") \
              + "Hostname: '%s'; " \
              % (str(self.hostname) if self.hostname is not None else "None") \
              + "Node Type: '%s'; " \
              % (str(self.nodeType) if self.nodeType is not None else "None") \
              + "Instance: '%s'; " \
              % (str(self.instance) if self.instance is not None else "None") \
              + "Username: '%s')" \
              % (str(self.username) if self.username is not None else "None")
        return tmp

    @staticmethod
    def deepcopy(obj):
        return ManagerObjNode().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        node_dict = {"nodeId": self.nodeId,
                     "hostname": self.hostname,
                     "nodeType": self.nodeType,
                     "instance": self.instance,
                     "connected": self.connected,
                     "version": self.version,
                     "rev": self.rev,
                     "username": self.username,
                     "persistent": self.persistent,
                     }

        return node_dict

    def deepcopy_obj(self, node):
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
class ManagerObjSensor(LocalObject):

    def __init__(self):
        super().__init__()
        self.nodeId = None  # type: Optional[int]
        self.sensorId = None  # type: Optional[int]
        self.clientSensorId = None  # type: Optional[int]
        self.alertDelay = None  # type: Optional[int]
        self.alertLevels = list()  # type: List[int]
        self.description = None  # type: Optional[str]
        self.lastStateUpdated = None  # type: Optional[int]
        self.state = None  # type: Optional[int]
        self.dataType = None  # type: Optional[int]
        self.data = None  # type: Optional[_SensorData]

    def __str__(self) -> str:
        tmp = "Sensor (Node Id: %s; " \
              % (str(self.nodeId) if self.nodeId is not None else "None") \
              + "Sensor Id: %s; " \
              % (str(self.sensorId) if self.sensorId is not None else "None") \
              + "Client Sensor Id: %s; " \
              % (str(self.clientSensorId) if self.clientSensorId is not None else "None") \
              + "description: '%s'; " \
              % (str(self.description) if self.description is not None else "None") \
              + "State: %s; " \
              % (str(self.state) if self.state is not None else "None") \
              + "Data: '%s')" \
              % (str(self.data) if self.data is not None else "None")
        return tmp

    @staticmethod
    def deepcopy(obj):
        return ManagerObjSensor().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        sensor_dict = {"nodeId": self.nodeId,
                       "sensorId": self.sensorId,
                       "clientSensorId": self.clientSensorId,
                       "alertDelay": self.alertDelay,
                       "alertLevels": self.alertLevels,
                       "description": self.description,
                       "lastStateUpdated": self.lastStateUpdated,
                       "state": self.state,
                       "dataType": self.dataType,
                       "data": self.data.copy_to_dict()
                       }

        return sensor_dict

    def deepcopy_obj(self, sensor):
        self.nodeId = sensor.nodeId
        self.sensorId = sensor.sensorId
        self.clientSensorId = sensor.clientSensorId
        self.alertDelay = sensor.alertDelay
        self.alertLevels = list(sensor.alertLevels)
        self.description = sensor.description
        self.lastStateUpdated = sensor.lastStateUpdated
        self.state = sensor.state

        if self.data is None or self.dataType != sensor.dataType:
            self.data = sensor.data.deepcopy(sensor.data)
        else:
            self.data.deepcopy_obj(sensor.data)

        self.dataType = sensor.dataType

        return self


# this class represents a manager client of the alert system
class ManagerObjManager(LocalObject):

    def __init__(self):
        super().__init__()
        self.nodeId = None  # type: Optional[int]
        self.managerId = None  # type: Optional[int]
        self.description = None  # type: Optional[str]

    def __str__(self) -> str:
        tmp = "Manager (Node Id: %s; " \
              % (str(self.nodeId) if self.nodeId is not None else "None") \
              + "Manager Id: %s; " \
              % (str(self.managerId) if self.managerId is not None else "None") \
              + "description: '%s'; " \
              % (str(self.description) if self.description is not None else "None")
        return tmp

    @staticmethod
    def deepcopy(obj):
        return ManagerObjManager().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        manager_dict = {"nodeId": self.nodeId,
                        "managerId": self.managerId,
                        "description": self.description,
                        }

        return manager_dict

    # This function copies all attributes of the given manager to this object.
    def deepcopy_obj(self, manager):
        self.nodeId = manager.nodeId
        self.managerId = manager.managerId
        self.description = manager.description
        return self


# this class represents an alert client of the alert system
class ManagerObjAlert(LocalObject):

    def __init__(self):
        super().__init__()
        self.nodeId = None  # type: Optional[int]
        self.alertId = None  # type: Optional[int]
        self.clientAlertId = None  # type: Optional[int]
        self.alertLevels = list()  # type: List[int]
        self.description = None  # type: Optional[str]

    def __str__(self) -> str:
        tmp = "Alert (Node Id: %s; " \
              % (str(self.nodeId) if self.nodeId is not None else "None") \
              + "Alert Id: %s; " \
              % (str(self.alertId) if self.alertId is not None else "None") \
              + "Client Alert Id: %s; " \
              % (str(self.clientAlertId) if self.clientAlertId is not None else "None") \
              + "description: '%s'; " \
              % (str(self.description) if self.description is not None else "None")
        return tmp

    @staticmethod
    def deepcopy(obj):
        return ManagerObjAlert().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        alert_dict = {"nodeId": self.nodeId,
                      "alertId": self.alertId,
                      "clientAlertId": self.clientAlertId,
                      "alertLevels": self.alertLevels,
                      "description": self.description,
                      }

        return alert_dict

    def deepcopy_obj(self, alert):
        self.nodeId = alert.nodeId
        self.alertId = alert.alertId
        self.clientAlertId = alert.clientAlertId
        self.alertLevels = list(alert.alertLevels)
        self.description = alert.description
        return self


# this class represents a triggered sensor alert of the alert system
class ManagerObjSensorAlert(LocalObject):

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
        self.optionalData = None  # type: Optional[Dict[str, Any]]

        # Does this sensor alert change the state of the sensor?
        self.changeState = None  # type: Optional[bool]

        # Does this sensor alert hold the latest data of the sensor?
        self.hasLatestData = None  # type: Optional[bool]

        # The sensor data type and data that is connected to this sensor alert.
        self.dataType = None  # type: Optional[int]
        self.data = None  # type: Optional[_SensorData]

    def __str__(self) -> str:
        tmp = "Sensor Alert (Description: '%s'; " \
              % self.description \
              + "SensorID: %s; " \
              % (str(self.sensorId) if self.sensorId is not None else "None") \
              + "State: %s; " \
              % (str(self.state) if self.state is not None else "None") \
              + "Time Received: %s; " \
              % (str(self.timeReceived) if self.timeReceived is not None else "None") \
              + "Alert Levels: %s)" \
              % ", ".join(map(str, self.alertLevels))
        return tmp

    @staticmethod
    def deepcopy(obj):
        return ManagerObjSensorAlert().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        sensor_alert_dict = {"alertLevels": self.alertLevels,
                             "description": self.description,
                             "sensorId": self.sensorId,
                             "state": self.state,
                             "hasOptionalData": self.hasOptionalData,
                             "optionalData": copy.deepcopy(self.optionalData) if self.hasOptionalData else None,
                             "dataType": self.dataType,
                             "data": self.data.copy_to_dict(),
                             "hasLatestData": self.hasLatestData,
                             "changeState": self.changeState
                             }

        return sensor_alert_dict

    def deepcopy_obj(self, sensor_alert):
        self.sensorId = sensor_alert.sensorId
        self.state = sensor_alert.state
        self.description = sensor_alert.description
        self.timeReceived = sensor_alert.timeReceived
        self.alertLevels = list(sensor_alert.alertLevels)
        self.hasOptionalData = sensor_alert.hasOptionalData
        self.changeState = sensor_alert.changeState
        self.hasLatestData = sensor_alert.hasLatestData

        if self.data is None or self.dataType != sensor_alert.dataType:
            self.data = sensor_alert.deepcopy(sensor_alert.data)
        else:
            self.data.deepcopy_obj(sensor_alert.data)

        self.dataType = sensor_alert.dataType

        if type(sensor_alert.optionalData) == dict:
            self.optionalData = copy.deepcopy(sensor_alert.optionalData)

        else:
            self.optionalData = None

        return self


# this class represents an alert level that is configured on the server
class ManagerObjAlertLevel(LocalObject):

    def __init__(self):
        super().__init__()
        self.level = None  # type: Optional[int]
        self.name = None  # type: Optional[str]
        self.profiles = list()  # type: List[int]
        self.instrumentation_active = None  # type: Optional[bool]
        self.instrumentation_cmd = None  # type: Optional[str]
        self.instrumentation_timeout = None  # type: Optional[int]

    def __str__(self) -> str:
        tmp = "Alert Level (Level: %s; " \
              % (str(self.level) if self.level is not None else "None") \
              + "Name: '%s'; " \
              % (str(self.name) if self.name is not None else "None") \
              + "Profiles: %s; " \
              % ", ".join(map(str, self.profiles)) \
              + "Instrumentation: %s)" \
              % (str(self.instrumentation_active) if self.instrumentation_active is not None else "None")
        return tmp

    @staticmethod
    def deepcopy(obj):
        return ManagerObjAlertLevel().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        alert_level_dict = {"level": self.level,
                            "name": self.name,
                            "profiles": self.profiles,
                            "instrumentation_active": self.instrumentation_active,
                            "instrumentation_cmd": self.instrumentation_cmd,
                            "instrumentation_timeout": self.instrumentation_timeout,
                            }

        return alert_level_dict

    def deepcopy_obj(self, alert_level):
        self.level = alert_level.level
        self.name = alert_level.name
        self.profiles = list(alert_level.profiles)
        self.instrumentation_active = alert_level.instrumentation_active
        if self.instrumentation_active:
            self.instrumentation_cmd = alert_level.instrumentation_cmd
            self.instrumentation_timeout = alert_level.instrumentation_timeout

        else:
            self.instrumentation_cmd = None
            self.instrumentation_timeout = None
        return self
