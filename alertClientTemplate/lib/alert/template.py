#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import Optional
from .core import _Alert, SensorAlert


# This class represents an example alert
# (for example a GPIO on a Raspberry Pi which should be set to high
# or code that executes an external command).
class TemplateAlert(_Alert):

    def __init__(self):
        _Alert.__init__(self)

        # this flag is used to signalize if the alert is triggered or not
        self.triggered = None  # type: Optional[bool]

    # this function is called once when the alert client has connected itself
    # to the server (should be use to initialize everything that is needed
    # for the alert)
    def initializeAlert(self):

        # set the state of the alert to "not triggered"
        self.triggered = False

        print("initialized")

        # PLACE YOUR CODE HERE

    def triggerAlert(self, sensorAlert: SensorAlert):

        # only execute if not triggered
        if not self.triggered:

            # set state of alert to "triggered"
            self.triggered = True

            print("trigger alert")

            # PLACE YOUR CODE HERE

        else:

            print("alert already triggered")

            # PLACE YOUR CODE HERE

    def stopAlert(self, sensorAlert: SensorAlert):

        # only execute if the alert was triggered
        if self.triggered:

            # set state of alert to "not triggered"
            self.triggered = False

            print("stopped triggered alert")

            # PLACE YOUR CODE HERE

        else:

            print("alert was not triggered")

            # PLACE YOUR CODE HERE
