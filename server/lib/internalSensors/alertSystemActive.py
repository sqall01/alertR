#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from ..localObjects import SensorDataType
from .core import _InternalSensor


# Class that represents the internal sensor that
# is responsible to trigger sensor alerts if the
# alert system changes is state from activated/deactivated
class AlertSystemActiveSensor(_InternalSensor):

    def __init__(self):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.NONE
