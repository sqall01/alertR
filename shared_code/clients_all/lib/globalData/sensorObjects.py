#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import copy
import time
from enum import Enum
from typing import Optional, Dict, Any
from .baseObjects import LocalObject


class _SensorData:
    def __init__(self):
        pass

    def __eq__(self, other):
        raise NotImplementedError("Abstract class.")

    def __str__(self) -> str:
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

    @staticmethod
    def verify_type(data_type: int):
        """
        This function verifies if the given data type matches to this object.
        :return: correct or not
        """
        raise NotImplementedError("Abstract class.")

    def copy_to_dict(self) -> Dict[str, Any]:
        """
        Copies the object's data into a dictionary.
        :return: dictionary representation of a copy of this object
        """
        raise NotImplementedError("Abstract class.")

    def deepcopy_obj(self, obj):
        """
        This function copies all attributes of the given object to this object.
        :param obj:
        :return: this object
        """
        raise NotImplementedError("Abstract class.")


class SensorDataNone(_SensorData):
    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        return type(other) == SensorDataNone

    def __str__(self) -> str:
        return "None"

    @staticmethod
    def copy_from_dict(data: Dict[str, Any]):
        return SensorDataNone()

    @staticmethod
    def deepcopy(obj):
        return SensorDataNone()

    @staticmethod
    def verify_dict(data: Dict[str, Any]) -> bool:
        if (isinstance(data, dict)
                and not list(data.keys())):
            return True
        return False

    @staticmethod
    def verify_type(data_type: int):
        return data_type == SensorDataType.NONE

    def copy_to_dict(self) -> Dict[str, Any]:
        return {}

    def deepcopy_obj(self, obj):
        return self


class SensorDataInt(_SensorData):
    def __init__(self, value: int, unit: str):
        super().__init__()
        self._value = value
        self._unit = unit

    def __eq__(self, other):
        return (type(other) == SensorDataInt
                and self._value == other.value
                and self._unit == other.unit)

    def __str__(self) -> str:
        return "%d %s" % (self._value, self._unit)

    @property
    def value(self) -> int:
        return self._value

    @property
    def unit(self) -> str:
        return self._unit

    @staticmethod
    def copy_from_dict(data: Dict[str, Any]):
        return SensorDataInt(data["value"],
                             data["unit"])

    @staticmethod
    def deepcopy(obj):
        return SensorDataInt(obj.value,
                             obj.unit)

    @staticmethod
    def verify_dict(data: Dict[str, Any]) -> bool:
        if (isinstance(data, dict)
                and all([x in data.keys() for x in ["value", "unit"]])
                and len(data.keys()) == 2
                and isinstance(data["value"], int)
                and isinstance(data["unit"], str)):
            return True
        return False

    @staticmethod
    def verify_type(data_type: int):
        return data_type == SensorDataType.INT

    def copy_to_dict(self) -> Dict[str, Any]:
        obj_dict = {"value": self._value,
                    "unit": self._unit,
                    }

        return obj_dict

    def deepcopy_obj(self, obj):
        self._value = obj.value
        self._unit = obj.unit
        return self


class SensorDataFloat(_SensorData):
    def __init__(self, value: float, unit: str):
        super().__init__()
        self._value = value
        self._unit = unit

    def __eq__(self, other):
        return (type(other) == SensorDataFloat
                and self._value == other.value
                and self._unit == other.unit)

    def __str__(self) -> str:
        return "%f %s" % (self._value, self._unit)

    @property
    def value(self) -> float:
        return self._value

    @property
    def unit(self) -> str:
        return self._unit

    @staticmethod
    def copy_from_dict(data: Dict[str, Any]):
        return SensorDataFloat(data["value"],
                               data["unit"])

    @staticmethod
    def deepcopy(obj):
        return SensorDataFloat(obj.value,
                               obj.unit)

    @staticmethod
    def verify_dict(data: Dict[str, Any]) -> bool:
        if (isinstance(data, dict)
                and all([x in data.keys() for x in ["value", "unit"]])
                and len(data.keys()) == 2
                and isinstance(data["value"], float)
                and isinstance(data["unit"], str)):
            return True
        return False

    @staticmethod
    def verify_type(data_type: int):
        return data_type == SensorDataType.FLOAT

    def copy_to_dict(self) -> Dict[str, Any]:
        obj_dict = {"value": self._value,
                    "unit": self._unit,
                    }

        return obj_dict

    def deepcopy_obj(self, obj):
        self._value = obj.value
        self._unit = obj.unit
        return self


class SensorDataGPS(_SensorData):
    def __init__(self, lat: float, lon: float, utctime: int):
        super().__init__()
        self._lat = lat
        self._lon = lon
        self._utctime = utctime

    def __eq__(self, other):
        return (type(other) == SensorDataGPS
                and self._lat == other.lat
                and self._lon == other.lon
                and self._utctime == other.utctime)

    def __str__(self) -> str:
        time_str = time.strftime("%d %b %Y at %H:%M:%S", time.localtime(self._utctime))
        return "(Lat: %f, Lon: %f) %s" % (self._lat, self._lon, time_str)

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
                and len(data.keys()) == 3
                and isinstance(data["lat"], float)
                and -90.0 <= data["lat"] <= 90.0
                and isinstance(data["lon"], float)
                and -180.0 <= data["lon"] <= 180.0
                and isinstance(data["utctime"], int)
                and 0 <= data["utctime"]):
            return True
        return False

    @staticmethod
    def verify_type(data_type: int):
        return data_type == SensorDataType.GPS

    def copy_to_dict(self) -> Dict[str, Any]:
        obj_dict = {"lat": self._lat,
                    "lon": self._lon,
                    "utctime": self._utctime,
                    }

        return obj_dict

    def deepcopy_obj(self, obj):
        self._lat = obj.lat
        self._lon = obj.lon
        self._utctime = obj.utctime
        return self


class SensorDataType(Enum):
    """
    This enum class gives the different data types of a sensor.
    """
    NONE = 0
    INT = 1
    FLOAT = 2
    GPS = 3

    _sensor_class_map = {0: SensorDataNone,
                         1: SensorDataInt,
                         2: SensorDataFloat,
                         3: SensorDataGPS}

    @classmethod
    def has_value(cls, value: int) -> bool:
        return value in cls._value2member_map.keys()

    @classmethod
    def get_sensor_data_class(cls, k: int):
        return cls._sensor_class_map[k]


class SensorOrdering(Enum):
    """
    This enum class gives the different orderings used to check if the data of a sensor exceeds a threshold.
    """
    LT = 0
    EQ = 1
    GT = 2

    @classmethod
    def has_value(cls, value: int):
        return value in cls._value2member_map.keys()


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
        self.sensorData = None  # type: Optional[_SensorData]

    @staticmethod
    def deepcopy(obj):
        return SensorObjSensorAlert().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        obj_dict = {"clientSensorId": self.clientSensorId,
                    "state": self.state,
                    "hasOptionalData": self.hasOptionalData,
                    "optionalData": copy.deepcopy(self.optionalData) if self.hasLatestData else None,
                    "changeState": self.changeState,
                    "hasLatestData": self.hasLatestData,
                    "dataType": self.dataType,
                    "sensorData": self.sensorData.copy_to_dict()
                    }

        return obj_dict

    def deepcopy_obj(self, sensor_alert):
        self.clientSensorId = sensor_alert.clientSensorId
        self.state = sensor_alert.state
        self.hasOptionalData = sensor_alert.hasOptionalData
        self.changeState = sensor_alert.changeState
        self.hasLatestData = sensor_alert.hasLatestData
        self.dataType = sensor_alert.dataType

        # Deep copy sensor data.
        if self.sensorData is None:
            self.sensorData = sensor_alert.sensorData.deepcopy(sensor_alert.sensorData)
        else:
            self.sensorData.deepcopy_obj(sensor_alert.sensorData)

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
        self.sensorData = None  # type: Optional[_SensorData]

    @staticmethod
    def deepcopy(obj):
        return SensorObjStateChange().deepcopy_obj(obj)

    def copy_to_dict(self) -> Dict[str, Any]:
        obj_dict = {"clientSensorId": self.clientSensorId,
                    "state": self.state,
                    "dataType": self.dataType,
                    "sensorData": self.sensorData.copy_to_dict()
                    }

        return obj_dict

    def deepcopy_obj(self, state_change):
        self.clientSensorId = state_change.clientSensorId
        self.state = state_change.clientSensorId
        self.dataType = state_change.dataType

        # Deep copy sensor data.
        if self.sensorData is None:
            self.sensorData = state_change.sensorData.deepcopy(state_change.sensorData)
        else:
            self.sensorData.deepcopy_obj(state_change.sensorData)

        return self
