#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from .core import _InternalSensor
from ..localObjects import SensorDataType
from typing import Set


# Class that represents the internal sensor that
# is responsible for sensor timeouts.
class SensorTimeoutSensor(_InternalSensor):

    def __init__(self):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.NONE

        # A set of ids of the sensors that are timed out.
        self.timeoutSensorIds = set()  # type: Set[int]

    def initialize(self):
        pass
