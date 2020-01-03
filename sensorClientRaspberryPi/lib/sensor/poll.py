#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import RPi.GPIO as GPIO
from .core import _PollingSensor
from ..localObjects import SensorDataType, SensorAlert, StateChange
from typing import Optional

# class that controls one sensor at a gpio pin of the raspberry pi
class RaspberryPiGPIOPollingSensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.NONE

        # the gpio pin number (NOTE: python uses the actual
        # pin number and not the gpio number)
        self.gpioPin = None

        # The counter of the state reads used to verify that the state
        # is read x times before it is actually changed.
        self.currStateCtr = 0
        self.thresStateCtr = None

    def initializeSensor(self) -> bool:
        self.hasLatestData = False
        self.changeState = True

        # configure gpio pin and get initial state
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.gpioPin, GPIO.IN)
        self.state = GPIO.input(self.gpioPin)
        self.tempState = self.state

        return True

    def getState(self) -> int:
        return self.state

    def updateState(self):

        # Set state only if threshold of reads with the same state is reached.
        currState = GPIO.input(self.gpioPin)
        if currState != self.state:
            self.currStateCtr += 1
            if self.currStateCtr >= self.thresStateCtr:
                self.state = currState
        else:
            self.currStateCtr = 0

    def forceSendAlert(self) -> Optional[SensorAlert]:
        return None

    def forceSendState(self) -> Optional[StateChange]:
        return None
