#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import copy
from typing import Optional, Dict, Any, Union
from .baseObjects import LocalObject


# This enum class gives the different data types of a sensor.
class SensorDataType:
    NONE = 0
    INT = 1
    FLOAT = 2
    GPS = 3


# This enum class gives the different orderings used to check if the data of a
# sensor exceeds a threshold.
class SensorOrdering:
    LT = 0
    EQ = 1
    GT = 2


class _SensorData:
    def __init__(self):
        pass

    def __eq__(self, other):
        raise NotImplementedError("Abstract class.")

    @staticmethod
    def copy_from_dict(data: Dict[str, Any]):
        """
        This function creates from the given dictionary an object of this class.
        This function has to succeed if verify_dict() says dictionary is correct.
        :param data:
        :return: object of this class
        """
        raise NotImplementedError("Abstract class.")

    @staticmethod
    def deepcopy(obj):
        """
        This function copies all attributes of the given object to a new data object.
        :param obj:
        :return: object of this class
        """
        raise NotImplementedError("Abstract class.")

    @staticmethod
    def verify_dict(data: Dict[str, Any]) -> bool:
        """
        This function verifies the given dictionary representing this object for correctness.
        Meaning, if verify_dict() succeeds, copy_from_dict() has to be able to create a valid object.
        :return: correct or not
        """
        raise NotImplementedError("Abstract class.")

    def copy_to_dict(self) -> Dict[str, Any]:
        """
        Copies the object's data into a dictionary.
        :return: dictionary representation of a copy of this object
        """
        raise NotImplementedError("Abstract class.")


class SensorDataGPS(_SensorData):
    def __init__(self, lat: float, lon: float, utctime: int):
        super().__init__()
        self._lat = lat
        self._lon = lon
        self._utctime = utctime

    def __eq__(self, other):
        return self._lat == other.lat and self._lon == other.lon and self._utctime == other.utctime

    @property
    def lat(self) -> float:
        return self._lat

    @property
    def lon(self) -> float:
        return self._lon

    @property
    def utctime(self) -> int:
        return self._utctime

    @staticmethod
    def copy_from_dict(data: Dict[str, Any]):
        return SensorDataGPS(data["lat"],
                             data["lon"],
                             data["utctime"])

    @staticmethod
    def deepcopy(obj):
        return SensorDataGPS(obj.lat,
                             obj.lon,
                             obj.utctime)

    @staticmethod
    def verify_dict(data: Dict[str, Any]) -> bool:
        if (isinstance(data, dict)
                and all([x in data.keys() for x in ["lat", "lon", "utctime"]])
                and isinstance(data["lat"], float)
                and isinstance(data["lon"], float)
                and isinstance(data["utctime"], int)):
            return True
        return False

    def copy_to_dict(self) -> Dict[str, Any]:
        obj_dict = {"lat": self._lat,
                    "lon": self._lon,
                    "utctime": self._utctime,
                    }

        return obj_dict


# This class represents a triggered sensor alert of the sensor.
class SensorObjSensorAlert(LocalObject):

    def __init__(self):
        super().__init__()

        # Sensor id of the local sensor.
        self.clientSensorId = None  # type: Optional[int]

        # State of the sensor alert ("triggered" = 1; "normal" = 0).
        self.state = None  # type: Optional[int]

        # The optional data of the sensor alert (if it has any).
        self.hasOptionalData = None  # type: Optional[bool]
        self.optionalData = None

        # Does this sensor alert change the state of the sensor?
        self.changeState = None  # type: Optional[bool]

        # Does this sensor alert hold the latest data of the sensor?
        self.hasLatestData = None  # type: Optional[bool]

        # The sensor data type and data that is connected to this sensor alert.
        self.dataType = None  # type: Optional[int]
        self.sensorData = None  # type: Optional[Union[int, float, SensorDataGPS]]

    def copy_to_dict(self) -> Dict[str, Any]:
        obj_dict = {"clientSensorId": self.clientSensorId,
                    "state": self.state,
                    "hasOptionalData": self.hasOptionalData,
                    "optionalData": copy.deepcopy(self.optionalData) if self.hasLatestData else None,
                    "changeState": self.changeState,
                    "hasLatestData": self.hasLatestData,
                    "dataType": self.dataType,
                    }

        # Convert sensor data for dict.
        if self.dataType == SensorDataType.GPS:
            obj_dict["sensorData"] = self.sensorData.copy_to_dict()

        else:
            obj_dict["sensorData"] = self.sensorData

        return obj_dict

    def deepcopy(self, sensor_alert):
        self.clientSensorId = sensor_alert.clientSensorId
        self.state = sensor_alert.state
        self.hasOptionalData = sensor_alert.hasOptionalData
        self.changeState = sensor_alert.changeState
        self.hasLatestData = sensor_alert.hasLatestData
        self.dataType = sensor_alert.dataType

        # Deep copy sensor data.
        if self.dataType == SensorDataType.GPS:
            self.sensorData = SensorDataGPS.deepcopy(sensor_alert.sensorData)

        else:
            self.sensorData = sensor_alert.sensorData

        if type(sensor_alert.optionalData) == dict:
            self.optionalData = copy.deepcopy(sensor_alert.optionalData)

        else:
            self.optionalData = None

        return self


# This class represents a state change of the sensor.
class SensorObjStateChange(LocalObject):

    def __init__(self):
        super().__init__()

        # Sensor id of the local sensor.
        self.clientSensorId = None  # type: Optional[int]

        # State of the sensor alert ("triggered" = 1; "normal" = 0).
        self.state = None  # type: Optional[int]

        # The sensor data type and data that is connected to this sensor alert.
        self.dataType = None  # type: Optional[int]
        self.sensorData = None  # type: Optional[Union[int, float, SensorDataGPS]]

    def copy_to_dict(self) -> Dict[str, Any]:
        obj_dict = {"clientSensorId": self.clientSensorId,
                    "state": self.state,
                    "dataType": self.dataType
                    }

        # Convert sensor data for dict.
        if self.dataType == SensorDataType.GPS:
            obj_dict["sensorData"] = self.sensorData.copy_to_dict()

        else:
            obj_dict["sensorData"] = self.sensorData

        return obj_dict

    def deepcopy(self, state_change):
        self.clientSensorId = state_change.clientSensorId
        self.state = state_change.clientSensorId
        self.dataType = state_change.dataType

        # Deep copy sensor data.
        if self.dataType == SensorDataType.GPS:
            self.sensorData = SensorDataGPS.deepcopy(state_change.sensorData)

        else:
            self.sensorData = state_change.sensorData

        return self
