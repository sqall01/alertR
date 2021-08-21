#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import re
import os
import logging
import time
from typing import Tuple
from .gps import _GPSSensor
from ..globalData import SensorDataType


class ChasRSensor(_GPSSensor):
    """
    Represents one ChasR GPS device.
    """
    def __init__(self):
        super().__init__()

        # TODO

    def _get_data(self) -> Tuple[float, float]:
        # TODO
        raise NotImplementedError("TODO")