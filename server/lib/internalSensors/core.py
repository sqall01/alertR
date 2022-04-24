#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from ..localObjects import Sensor


# Internal class represents an internal sensor of the alarm system server.
class _InternalSensor(Sensor):

    def __init__(self):
        super().__init__()

    def initialize(self):
        """
        Initializes the sensor and is called during start up of server.
        """
        raise NotImplementedError("Abstract class")
