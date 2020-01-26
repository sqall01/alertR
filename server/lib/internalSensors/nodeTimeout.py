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
# is responsible for node timeouts.
class NodeTimeoutSensor(_InternalSensor):

    def __init__(self):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.NONE

        # An internal set of ids of the nodes that are timed out.
        self._timeoutNodeIds = set()  # type: Set[int]

    def getTimeoutNodeIds(self) -> Set[int]:
        """
        Returns a copy of the internal timed out node ids set.

        :return: Copy of the node ids set
        """
        return set(self._timeoutNodeIds)
