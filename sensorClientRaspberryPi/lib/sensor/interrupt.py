#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import RPi.GPIO as GPIO
import os
import logging
import time
from .core import _PollingSensor
from ..localObjects import SensorDataType, SensorAlert, StateChange
from typing import Optional


# class that uses edge detection to check a gpio pin of the raspberry pi
class RaspberryPiGPIOInterruptSensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)
        self.fileName = os.path.basename(__file__)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.NONE

        # the gpio pin number (NOTE: python uses the actual
        # pin number and not the gpio number)
        self.gpioPin = None

        # time that has to go by between two triggers
        self.delayBetweenTriggers = None

        # time a sensor is seen as triggered
        self.timeSensorTriggered = None

        # the last time the sensor was triggered
        self.lastTimeTriggered = 0.0

        # the configured edge detection
        self.edge = None

        # the count of interrupts that has to occur before
        # an alert is triggered
        # this is used to relax the edge detection a little bit
        # for example an interrupt is triggered when an falling/rising
        # edge is detected, if your wiring is not good enough isolated
        # it can happen that electro magnetic radiation (because of
        # a starting vacuum cleaner for example) causes a falling/rising edge
        # this option abuses the bouncing of the wiring, this means
        # that the radiation for example only triggers one rising/falling
        # edge and your normal wiring could cause like four detected edges
        # when it is triggered because of the signal bouncing
        # so you could use this circumstance to determine correct triggers
        # from false triggers by setting a threshold of edges that have
        # to be reached before an alert is executed
        self.edgeCountBeforeTrigger = 0
        self.edgeCounter = 0

        # configures if the gpio input is pulled up or down
        self.pulledUpOrDown = None

        # used as internal state set by the interrupt callback
        self._internalState = None

    def _interruptCallback(self, gpioPin: int):

        # Check if the last time we detected an interrupt is longer ago than the configured delay between two triggers
        # => set time and reset edge counter
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.lastTimeTriggered) > self.delayBetweenTriggers:
            self.edgeCounter = 0
            self.lastTimeTriggered = utcTimestamp

        self.edgeCounter += 1

        # if edge counter reaches threshold
        # => trigger state
        if self.edgeCounter >= self.edgeCountBeforeTrigger:
            self._internalState = self.triggerState

            logging.debug("[%s]: Sensor '%s' triggered." % (self.fileName, self.description))

        logging.debug("[%s]: %d Interrupt "
                      % (self.fileName, self.edgeCounter)
                      + "for sensor '%s' triggered."
                      % self.description)

    def initializeSensor(self) -> bool:
        self.hasLatestData = False
        self.changeState = True

        # get the value for the setting if the gpio is pulled up or down
        if self.pulledUpOrDown == 0:
            pulledUpOrDown = GPIO.PUD_DOWN
        elif self.pulledUpOrDown == 1:
            pulledUpOrDown = GPIO.PUD_UP
        else:
            logging.critical("[%s]: Value for pulled up or down setting not known." % self.fileName)
            return False

        # configure gpio pin and get initial state
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.gpioPin, GPIO.IN, pull_up_down=pulledUpOrDown)

        # set initial state to not triggered
        self.state = 1 - self.triggerState
        self._internalState = 1 - self.triggerState

        # set edge detection
        if self.edge == 0:
            GPIO.add_event_detect(self.gpioPin,
                                  GPIO.FALLING,
                                  callback=self._interruptCallback)
        elif self.edge == 1:
            GPIO.add_event_detect(self.gpioPin,
                                  GPIO.RISING,
                                  callback=self._interruptCallback)
        else:
            logging.critical("[%s]: Value for edge detection not known." % self.fileName)
            return False

        return True

    def getState(self) -> int:
        return self.state

    def updateState(self):
        # check if the sensor is triggered and if it is longer
        # triggered than configured => set internal state to normal
        utcTimestamp = int(time.time())
        if self.state == self.triggerState and ((utcTimestamp - self.lastTimeTriggered) > self.timeSensorTriggered):
            self._internalState = 1 - self.triggerState

        # update state to internal state
        self.state = self._internalState

    def forceSendAlert(self) -> Optional[SensorAlert]:
        return None

    def forceSendState(self)  -> Optional[StateChange]:
        return None
