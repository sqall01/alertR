#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import copy
from typing import Optional, List, Any, Dict
# noinspection PyProtectedMember
from .globalData.sensorObjects import SensorDataType, SensorErrorState, _SensorData


# This class contains the error codes used by the alertr.de server.
class ErrorCodes:
    NO_ERROR = 0
    DATABASE_ERROR = 1
    AUTH_ERROR = 2
    ILLEGAL_MSG_ERROR = 3
    SESSION_EXPIRED = 4


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
        self.clientAlertId = None  # type: Optional[int]
        self.alertLevels = list()  # type: List[int]
        self.description = None  # type: Optional[str]


# This class represents a single sensor of a node.
class Sensor:

    def __init__(self):
        self.sensorId = None  # type: Optional[int]
        self.nodeId = None  # type: Optional[int]
        self.clientSensorId = None  # type: Optional[int]
        self.description = None  # type: Optional[str]
        self.state = None  # type: Optional[int]
        self.error_state = None  # type: Optional[SensorErrorState]
        self.alertLevels = list()  # type: List[int]
        self.alertDelay = None  # type: Optional[int]
        self.dataType = None  # type: Optional[int]
        self.data = None  # type: Optional[_SensorData]

    def deepcopy(self, sensor):
        """
        Copies the values of the object given as parameter into this object.
        :param sensor: object to copy values from.
        :return: pointer to this object
        """
        self.sensorId = sensor.sensorId
        self.nodeId = sensor.nodeId
        self.clientSensorId = sensor.clientSensorId
        self.description = sensor.description
        self.state = sensor.state
        self.alertLevels = list(sensor.alertLevels)
        self.alertDelay = sensor.alertDelay
        self.dataType = sensor.dataType

        # Deep copy sensor data.
        sensor_data_class = SensorDataType.get_sensor_data_class(self.dataType)
        self.data = sensor_data_class.deepcopy(sensor.data)

        return self


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

        # this flag tells if the alert level should trigger a sensor alert
        # if the sensor goes to state "triggered"
        self.triggerAlertTriggered = None  # type: Optional[bool]

        # this flag tells if the alert level should also trigger a sensor alert
        # if the sensor goes to state "normal"
        self.triggerAlertNormal = None  # type: Optional[bool]

        # Instrumentation settings.
        self.instrumentation_active = None  # type: Optional[bool]
        self.instrumentation_cmd = None  # type: Optional[str]
        self.instrumentation_timeout = None  # type: Optional[int]

        # List of profile ids for which this alert level triggers a sensor alert.
        # Meaning the system has to use one of the profiles in this list before the alert level triggers a sensor alert.
        self.profiles = list()  # type: List[int]


# This class represents a single sensor alert that was triggered.
class SensorAlert:

    def __init__(self):
        self.nodeId = None  # type: Optional[int]

        self.sensorId = None  # type: Optional[int]

        # Description of the sensor that raised this sensor alert.
        self.description = None  # type: Optional[str]

        # Time this sensor alert was received.
        self.timeReceived = None  # type: Optional[int]

        # The delay this sensor alert has before it can be triggered.
        self.alertDelay = None  # type: Optional[int]

        # State of the sensor alert ("triggered" = 1; "normal" = 0).
        self.state = None  # type: Optional[int]

        # The optional data of the sensor alert (if it has any).
        self.hasOptionalData = None  # type: Optional[bool]
        self.optionalData = None  # type: Optional[Dict[str, Any]]

        # Does this sensor alert change the state of the sensor?
        self.changeState = None  # type: Optional[bool]

        # List of alert levels (Integer) that this sensor alert belongs to.
        self.alertLevels = list()  # type: List[int]

        # List of alert levels (Integer) that are currently triggered by this sensor alert.
        self.triggeredAlertLevels = list()  # type: List[int]

        # Does this sensor alert hold the latest data of the sensor?
        self.hasLatestData = None  # type: Optional[bool]

        # The sensor data type and data that is connected to this sensor alert.
        self.dataType = None  # type: Optional[int]
        self.data = None  # type: Optional[_SensorData]

    @staticmethod
    def convert_from_dict(sensor_alert_dict: Dict[str, Any]):
        """
        Creates a Sensor Alert object from a dictionary.
        :param sensor_alert_dict:
        :return: Sensor Alert object
        """
        sensor_alert = SensorAlert()
        sensor_alert.nodeId = sensor_alert_dict["nodeId"]
        sensor_alert.sensorId = sensor_alert_dict["sensorId"]
        sensor_alert.description = sensor_alert_dict["description"]
        sensor_alert.timeReceived = sensor_alert_dict["timeReceived"]
        sensor_alert.alertDelay = sensor_alert_dict["alertDelay"]
        sensor_alert.state = sensor_alert_dict["state"]
        sensor_alert.hasOptionalData = sensor_alert_dict["hasOptionalData"]
        sensor_alert.optionalData = sensor_alert_dict["optionalData"]
        sensor_alert.changeState = sensor_alert_dict["changeState"]
        sensor_alert.alertLevels = sensor_alert_dict["alertLevels"]
        sensor_alert.triggeredAlertLevels = sensor_alert_dict["triggeredAlertLevels"]
        sensor_alert.hasLatestData = sensor_alert_dict["hasLatestData"]
        sensor_alert.dataType = sensor_alert_dict["dataType"]

        sensor_data_class = SensorDataType.get_sensor_data_class(sensor_alert.dataType)
        sensor_alert.data = sensor_data_class.copy_from_dict(sensor_alert_dict["data"])

        return sensor_alert

    @staticmethod
    def verify_dict(data: Dict[str, Any]) -> bool:
        if "nodeId" not in data.keys() or type(data["nodeId"]) != int:
            return False

        if "sensorId" not in data.keys() or type(data["sensorId"]) != int:
            return False

        if "description" not in data.keys() or type(data["description"]) != str:
            return False

        if "timeReceived" not in data.keys() or type(data["timeReceived"]) != int:
            return False

        if "alertDelay" not in data.keys() or type(data["alertDelay"]) != int:
            return False

        if "state" not in data.keys() or type(data["state"]) != int or data["state"] not in [0, 1]:
            return False

        if "hasOptionalData" not in data.keys() or type(data["hasOptionalData"]) != bool:
            return False

        if data["hasOptionalData"] and ("optionalData" not in data.keys() or type(data["optionalData"]) != dict):
            return False

        if "alertDelay" not in data.keys() or type(data["alertDelay"]) != int:
            return False

        if "changeState" not in data.keys() or type(data["changeState"]) != bool:
            return False

        if ("alertLevels" not in data.keys()
                or type(data["alertLevels"]) != list
                or not all(isinstance(item, int) for item in data["alertLevels"])):
            return False

        if ("triggeredAlertLevels" not in data.keys()
                or type(data["triggeredAlertLevels"]) != list
                or not all(isinstance(item, int) for item in data["triggeredAlertLevels"])):
            return False

        if "hasLatestData" not in data.keys() or type(data["hasLatestData"]) != bool:
            return False

        if ("dataType" not in data.keys()
                or type(data["dataType"]) != int
                or not SensorDataType.has_value(data["dataType"])):
            return False

        sensor_data_class = SensorDataType.get_sensor_data_class(data["dataType"])
        if "data" not in data.keys() or not sensor_data_class.verify_dict(data["data"]):
            return False

        return True

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Sensor Alert object into a dictionary.
        :return: dictionary representation of the Sensor Alert object.
        """
        sensor_alert_dict = {"nodeId": self.nodeId,
                             "sensorId": self.sensorId,
                             "description": self.description,
                             "timeReceived": self.timeReceived,
                             "alertDelay": self.alertDelay,
                             "state": self.state,
                             "hasOptionalData": self.hasOptionalData,
                             "optionalData": self.optionalData,
                             "changeState": self.changeState,
                             "alertLevels": self.alertLevels,
                             "triggeredAlertLevels": self.triggeredAlertLevels,
                             "hasLatestData": self.hasLatestData,
                             "dataType": self.dataType,
                             "data": self.data.copy_to_dict()
                             }

        return sensor_alert_dict

    def deepcopy(self, sensor_alert):
        """
        Copies the values of the object given as parameter into this object.
        :param sensor_alert: object to copy values from.
        :return: pointer to this object
        """
        self.nodeId = sensor_alert.nodeId
        self.sensorId = sensor_alert.sensorId
        self.description = sensor_alert.description
        self.timeReceived = sensor_alert.timeReceived
        self.alertDelay = sensor_alert.alertDelay
        self.state = sensor_alert.state
        self.hasOptionalData = sensor_alert.hasOptionalData
        self.changeState = sensor_alert.changeState
        self.alertLevels = list(sensor_alert.alertLevels)
        self.triggeredAlertLevels = list(sensor_alert.triggeredAlertLevels)
        self.hasLatestData = sensor_alert.hasLatestData
        self.dataType = sensor_alert.dataType

        if type(sensor_alert.optionalData) == dict:
            self.optionalData = copy.deepcopy(sensor_alert.optionalData)

        else:
            self.optionalData = None

        # Deep copy sensor data.
        sensor_data_class = SensorDataType.get_sensor_data_class(self.dataType)
        self.data = sensor_data_class.deepcopy(sensor_alert.data)

        return self


# This class represents sensor data.
class SensorData:

    def __init__(self):
        self.sensorId = None  # type: Optional[int]
        self.dataType = None  # type: Optional[int]
        self.data = None  # type: Optional[_SensorData]


class Option:

    def __init__(self):
        self.type = None  # type: Optional[str]
        self.value = None  # type: Optional[int]

    def deepcopy(self, option):
        """
        This function copies all attributes of the given option to this object.
        :param option:
        :return:
        """
        self.type = option.type
        self.value = option.value
        return self


class Profile:

    def __init__(self):
        self.profileId = None  # type: Optional[id]
        self.name = None  # type: Optional[str]
