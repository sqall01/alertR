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
from .sensorObjects import SensorDataType


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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Option object into a dictionary.
        :return:
        """
        option_dict = {"type": self.type,
                       "value": self.value,
                       }

        return option_dict

    def deepcopy(self, option):
        """
        This function copies all attributes of the given option to this object.
        :param option:
        :return:
        """
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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Profile object into a dictionary.
        :return:
        """
        profile_dict = {"profileId": self.profileId,
                        "name": self.name,
                        }

        return profile_dict

    def deepcopy(self, profile):
        """
        This function copies all attributes of the given profile to this object.
        :param profile:
        :return:
        """
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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Node object into a dictionary.
        :return:
        """
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

    def deepcopy(self, node):
        """
        This function copies all attributes of the given node to this object.
        :param node:
        :return:
        """
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
        self.dataType = None  # type: Optional[SensorDataType]
        self.data = None  # type: Any

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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Sensor object into a dictionary.
        :return:
        """
        sensor_dict = {"nodeId": self.nodeId,
                       "sensorId": self.sensorId,
                       "clientSensorId": self.clientSensorId,
                       "alertDelay": self.alertDelay,
                       "alertLevels": self.alertLevels,
                       "description": self.description,
                       "lastStateUpdated": self.lastStateUpdated,
                       "state": self.state,
                       "dataType": self.dataType,
                       "data": self.data
                       }

        return sensor_dict

    def deepcopy(self, sensor):
        """
        This function copies all attributes of the given sensor to this object.
        :param sensor:
        :return:
        """
        self.nodeId = sensor.nodeId
        self.sensorId = sensor.sensorId
        self.clientSensorId = sensor.clientSensorId
        self.alertDelay = sensor.alertDelay
        self.alertLevels = list(sensor.alertLevels)
        self.description = sensor.description
        self.lastStateUpdated = sensor.lastStateUpdated
        self.state = sensor.state
        self.dataType = sensor.dataType
        self.data = sensor.data
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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Manager object into a dictionary.
        :return:
        """
        manager_dict = {"nodeId": self.nodeId,
                        "managerId": self.managerId,
                        "description": self.description,
                        }

        return manager_dict

    # This function copies all attributes of the given manager to this object.
    def deepcopy(self, manager):
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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Alert object into a dictionary.
        :return:
        """
        alert_dict = {"nodeId": self.nodeId,
                      "alertId": self.alertId,
                      "clientAlertId": self.clientAlertId,
                      "alertLevels": self.alertLevels,
                      "description": self.description,
                      }

        return alert_dict

    def deepcopy(self, alert):
        """
        This function copies all attributes of the given alert to this object.
        :param alert:
        :return:
        """
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
        self.dataType = None  # type: Optional[SensorDataType]
        self.sensorData = None  # type: Any

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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Sensor Alert object into a dictionary.
        :return:
        """
        sensor_alert_dict = {"alertLevels": self.alertLevels,
                             "description": self.description,
                             "sensorId": self.sensorId,
                             "state": self.state,
                             "hasOptionalData": self.hasOptionalData,
                             "optionalData": copy.deepcopy(self.optionalData) if self.hasLatestData else None,
                             "dataType": self.dataType,
                             "data": self.sensorData,
                             "hasLatestData": self.hasLatestData,
                             "changeState": self.changeState
                            }

        return sensor_alert_dict

    def deepcopy(self, sensor_alert):
        """
        This function copies all attributes of the given sensor alert to this object.

        :param sensor_alert:
        :return:
        """
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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Alert Level object into a dictionary.
        :return:
        """
        alert_level_dict = {"level": self.level,
                            "name": self.name,
                            "profiles": self.profiles,
                            "instrumentation_active": self.instrumentation_active,
                            "instrumentation_cmd": self.instrumentation_cmd,
                            "instrumentation_timeout": self.instrumentation_timeout,
                           }

        return alert_level_dict

    def deepcopy(self, alert_level):
        """
        This function copies all attributes of the given alert level to this object.
        :param alert_level:
        :return:
        """
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
