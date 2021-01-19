#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import Optional
from .core import _Alert
from ..globalData import ManagerObjSensorAlert, AlertObjProfileChange


# This class represents an example alert
# (for example a GPIO on a Raspberry Pi which should be set to high
# or code that executes an external command).
class TemplateAlert(_Alert):

    def __init__(self):
        _Alert.__init__(self)

        # State of the alert (0 = "normal"; 1 = "triggered").
        self.state = None  # type: Optional[int]

    # this function is called once when the alert client has connected itself
    # to the server (should be use to initialize everything that is needed
    # for the alert)
    def initialize(self):

        # set the state of the alert to "normal"
        self.state = 0

        print("Initialize: initialized")

        # PLACE YOUR CODE HERE

    def alert_triggered(self, sensor_alert: ManagerObjSensorAlert):

        if self.state == 0:
            # Set state of alert to "triggered"
            self.state = sensor_alert.state

        print("Sensor Alert 'Triggered': trigger alert")

        # PLACE YOUR CODE HERE

    def alert_normal(self, sensor_alert: ManagerObjSensorAlert):

        if self.state == 1:
            # Set state of alert to "normal"
            self.state = sensor_alert.state

        print("Sensor Alert 'Normal': trigger alert")

        # PLACE YOUR CODE HERE

    def alert_profile_change(self, profile_change: AlertObjProfileChange):

        print("Profile Change to '%d'" % profile_change.profileId)

        # PLACE YOUR CODE HERE
