#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import RPi.GPIO as GPIO
from .core import _PollingSensor
from ..globalData import SensorDataType
from ..globalData.sensorObjects import SensorDataNone


class RaspberryPiGPIOPollingSensor(_PollingSensor):
    """
    Controls one sensor at a gpio pin of the raspberry pi.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.NONE
        self.sensorData = SensorDataNone()

        # the gpio pin number (NOTE: python uses the actual
        # pin number and not the gpio number)
        self.gpioPin = None

        # The counter of the state reads used to verify that the state
        # is read x times before it is actually changed.
        self._curr_state_ctr = 0
        self.thresStateCtr = None

    def _execute(self):

        while True:

            if self._exit_flag:
                return

            time.sleep(0.5)

            # Set state only if threshold of reads with the same state is reached.
            curr_state = GPIO.input(self.gpioPin)
            if curr_state != self.state:
                self._curr_state_ctr += 1
                if self._curr_state_ctr >= self.thresStateCtr:
                    self._add_sensor_alert(curr_state,
                                           True)

            else:
                self._curr_state_ctr = 0

    def initialize(self) -> bool:

        # configure gpio pin and get initial state
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.gpioPin, GPIO.IN)
        self.state = GPIO.input(self.gpioPin)

        return True
