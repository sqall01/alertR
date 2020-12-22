#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import Optional, List, Dict, Any


# This enum class gives the different data types of a sensor.
class SensorDataType:
    NONE = 0
    INT = 1
    FLOAT = 2


# This class represents a single sensor alert that was triggered.
class SensorAlert:

    def __init__(self):
        self.sensorId = None  # type: Optional[int]

        # Description of the sensor that raised this sensor alert.
        self.description = None  # type: Optional[str]

        # Time this sensor alert was received.
        self.timeReceived = None  # type: Optional[int]

        # State of the sensor alert ("triggered" = 1; "normal" = 0).
        self.state = None  # type: Optional[int]

        # The optional data of the sensor alert (if it has any).
        self.hasOptionalData = None  # type: Optional[bool]
        self.optionalData = None

        # Does this sensor alert change the state of the sensor?
        self.changeState = None  # type: Optional[bool]

        # List of alert levels (Integer) that are triggered
        # by this sensor alert.
        self.alertLevels = list()  # type: List[int]

        # Does this sensor alert hold the latest data of the sensor?
        self.hasLatestData = None  # type: Optional[bool]

        # The sensor data type and data that is connected to this sensor alert.
        self.dataType = None  # type: Optional[int]
        self.sensorData = None

    # Converts the SensorAlert object into a dictionary.
    def convertToDict(self) -> Dict[str, Any]:
        sensorAlertDict = {"alertLevels": self.alertLevels,
                           "description": self.description,
                           "sensorId": self.sensorId,
                           "state": self.state,
                           "hasOptionalData": self.hasOptionalData,
                           "optionalData": self.optionalData,
                           "dataType": self.dataType,
                           "data": self.sensorData,
                           "hasLatestData": self.hasLatestData,
                           "changeState": self.changeState
        }

        return sensorAlertDict
