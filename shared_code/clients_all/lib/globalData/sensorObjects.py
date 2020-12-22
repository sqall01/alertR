#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import copy
from typing import Optional
from .baseObjects import LocalObject


# This enum class gives the different data types of a sensor.
class SensorDataType:
    NONE = 0
    INT = 1
    FLOAT = 2


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
        self.sensorData = None  # type: Optional[int, float]

    # This function copies all attributes of the given state change to this object.
    def deepcopy(self, sensor_alert):
        self.clientSensorId = sensor_alert.clientSensorId
        self.state = sensor_alert.state
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
        self.sensorData = None  # type: Optional[int, float]

    # This function copies all attributes of the given state change to this object.
    def deepcopy(self, state_change):
        self.clientSensorId = state_change.clientSensorId
        self.state = state_change.clientSensorId
        self.dataType = state_change.dataType
        self.sensorData = state_change.sensorData
        return self
