#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.
import copy
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

        # Instrumentation settings.
        self.instrumentation_active = None  # type: Optional[bool]
        self.instrumentation_cmd = None  # type: Optional[str]
        self.instrumentation_timeout = None  # type: Optional[int]


# This class represents a single sensor alert that was triggered.
class SensorAlert:

    def __init__(self):
        self.sensorAlertId = None  # type: Optional[int]
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
        self.optionalData = None  # type: Dict[str, Any]

        # Does this sensor alert change the state of the sensor?
        self.changeState = None  # type: Optional[bool]

        # List of alert levels (Integer) that this sensor alert belongs to.
        self.alertLevels = list()  # type: List[int]

        # List of alert levels (Integer) that are currently triggered
        # by this sensor alert.
        self.triggeredAlertLevels = list()  # type: List[int]

        # Does this sensor alert hold the latest data of the sensor?
        self.hasLatestData = None  # type: Optional[bool]

        # The sensor data type and data that is connected to this sensor alert.
        self.dataType = None  # type: Optional[int]
        self.sensorData = None  # type: Any

    @staticmethod
    def convert_from_dict(sensor_alert_dict: Dict[str, Any]):
        """
        Creates a Sensor Alert object from a dictionary.
        :param sensor_alert_dict:
        :return: Sensor Alert object
        """
        sensor_alert = SensorAlert()
        sensor_alert.sensorAlertId = sensor_alert_dict["sensorAlertId"]
        sensor_alert.nodeId  = sensor_alert_dict["nodeId"]
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
        sensor_alert.sensorData = sensor_alert_dict["data"]

        # Verify data types of attributes (raises ValueError if type is wrong).
        sensor_alert.verify_types()

        return sensor_alert

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Sensor Alert object into a dictionary.
        :return: dictionary representation of the Sensor Alert object.
        """
        sensor_alert_dict = {"sensorAlertId": self.sensorAlertId,
                             "nodeId": self.nodeId,
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
                             "data": self.sensorData,
        }

        return sensor_alert_dict

    def deepcopy(self, sensor_alert):
        """
        Copies the values of the object given as parameter into this object.
        :param sensor_alert: object to copy values from.
        :return: pointer to this object
        """
        self.sensorAlertId = sensor_alert.sensorAlertId
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
        self.sensorData = sensor_alert.sensorData

        if type(sensor_alert.optionalData) == dict:
            self.optionalData = copy.deepcopy(sensor_alert.optionalData)

        else:
            self.optionalData = None

        return self

    def verify_types(self):
        """
        Verifies data types of attributes (raises ValueError if attribute is wrong).
        """
        if type(self.sensorAlertId) != int:
            raise ValueError("sensorAlertId not valid")

        if type(self.nodeId) != int:
            raise ValueError("nodeId not valid")

        if type(self.sensorId) != int:
            raise ValueError("sensorId not valid")

        if type(self.description) != str:
            raise ValueError("description not valid")

        if type(self.timeReceived) != int:
            raise ValueError("timeReceived not valid")

        if type(self.alertDelay) != int:
            raise ValueError("alertDelay not valid")

        if (type(self.state) != int
                or self.state not in [0, 1]):
            raise ValueError("state not valid")

        if type(self.hasOptionalData) != bool:
            raise ValueError("hasOptionalData not valid")

        if self.hasOptionalData and type(self.optionalData) != dict:
            raise ValueError("optionalData not valid")

        if type(self.alertDelay) != int:
            raise ValueError("alertDelay not valid")

        if type(self.changeState) != bool:
            raise ValueError("changeState not valid")

        if (type(self.alertLevels) != list
                or not all(isinstance(item, int) for item in self.alertLevels)):
            raise ValueError("alertLevels not valid")

        if (type(self.triggeredAlertLevels) != list
                or not all(isinstance(item, int) for item in self.triggeredAlertLevels)):
            raise ValueError("triggeredAlertLevels not valid")

        if type(self.hasLatestData) != bool:
            raise ValueError("hasLatestData not valid")

        if (type(self.dataType) != int
                or self.dataType not in [SensorDataType.NONE, SensorDataType.INT, SensorDataType.FLOAT]):
            raise ValueError("dataType not valid")

        if self.dataType == SensorDataType.NONE and self.sensorData is not None:
            raise ValueError("data not valid")

        if self.dataType == SensorDataType.INT and not isinstance(self.sensorData, int):
            raise ValueError("data not valid")

        if self.dataType == SensorDataType.FLOAT and not isinstance(self.sensorData, float):
            raise ValueError("data not valid")


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
