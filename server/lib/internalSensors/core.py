#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import Optional, List, Any


# Internal class represents an internal sensor of the alarm system server.
class _InternalSensor:

    def __init__(self):
        self.nodeId = None  # type: Optional[int]
        self.sensorId = None  # type: Optional[int]
        self.clientSensorId = None  # type: Optional[int]
        self.alertDelay = None  # type: Optional[int]
        self.alertLevels = list()  # type: List[int]
        self.description = None  # type: Optional[str]
        self.lastStateUpdated = None  # type: Optional[int]
        self.state = None  # type: Optional[int]
        self.dataType = None  # type: Optional[int]
        self.data = None  # type: Any

    def initialize(self):
        """
        Initializes the sensor and is called during start up of server.
        """
        raise NotImplemented("Function not implemented yet.")
