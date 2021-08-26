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


class SensorDataGPS:
    def __init__(self, lat: float, lon: float, utctime: int):
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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the GPS object into a dictionary.
        :return:
        """
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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Sensor Alert object into a dictionary.
        :return:
        """
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
            obj_dict["sensorData"] = self.sensorData.convert_to_dict()

        else:
            obj_dict["sensorData"] = self.sensorData

        return obj_dict

    def deepcopy(self, sensor_alert):
        """
        This function copies all attributes of the given state change to this object.
        :param sensor_alert:
        :return:
        """
        self.clientSensorId = sensor_alert.clientSensorId
        self.state = sensor_alert.state
        self.hasOptionalData = sensor_alert.hasOptionalData
        self.changeState = sensor_alert.changeState
        self.hasLatestData = sensor_alert.hasLatestData
        self.dataType = sensor_alert.dataType

        # Deep copy sensor data.
        if self.dataType == SensorDataType.GPS:
            self.sensorData = SensorDataGPS(sensor_alert.sensorData.lat,
                                            sensor_alert.sensorData.lon,
                                            sensor_alert.sensorData.utctime)

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

    def convert_to_dict(self) -> Dict[str, Any]:
        """
        Converts the Sensor object into a dictionary.
        :return:
        """
        obj_dict = {"clientSensorId": self.clientSensorId,
                    "state": self.state,
                    "dataType": self.dataType
                    }

        # Convert sensor data for dict.
        if self.dataType == SensorDataType.GPS:
            obj_dict["sensorData"] = self.sensorData.convert_to_dict()

        else:
            obj_dict["sensorData"] = self.sensorData

        return obj_dict

    def deepcopy(self, state_change):
        """
        This function copies all attributes of the given state change to this object.
        :param state_change:
        :return:
        """
        self.clientSensorId = state_change.clientSensorId
        self.state = state_change.clientSensorId
        self.dataType = state_change.dataType

        # Deep copy sensor data.
        if self.dataType == SensorDataType.GPS:
            self.sensorData = SensorDataGPS(state_change.sensorData.lat,
                                            state_change.sensorData.lon,
                                            state_change.sensorData.utctime)

        else:
            self.sensorData = state_change.sensorData

        return self
