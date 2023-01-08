#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import RPi.GPIO as GPIO
import os
import time
from .core import _PollingSensor
from ..globalData import SensorDataType
from ..globalData.sensorObjects import SensorDataNone


class RaspberryPiGPIOInterruptSensor(_PollingSensor):
    """
    Uses edge detection to check a gpio pin of the raspberry pi.
    """

    def __init__(self):
        _PollingSensor.__init__(self)
        self._log_tag = os.path.basename(__file__)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.NONE
        self.data = SensorDataNone()

        # the gpio pin number (NOTE: python uses the actual
        # pin number and not the gpio number)
        self.gpioPin = None

        # time that has to go by between two triggers
        self.delayBetweenTriggers = None

        # time a sensor is seen as triggered
        self.timeSensorTriggered = None

        # the last time the sensor was triggered
        self._last_time_triggered = 0.0

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
        self._edge_counter = 0

        # configures if the gpio input is pulled up or down
        self.pulledUpOrDown = None

        # used as internal state set by the interrupt callback
        self._internal_state = None

    def _execute(self):

        while True:

            if self._exit_flag:
                return

            time.sleep(0.5)

            # Check if the sensor is triggered and if it is longer triggered than configured
            # => set internal state to normal
            utc_timestamp = int(time.time())
            if (self.state == self.triggerState
                    and ((utc_timestamp - self._last_time_triggered) > self.timeSensorTriggered)):
                self._internal_state = 1 - self.triggerState

            if self.state != self._internal_state:
                self._add_sensor_alert(self._internal_state,
                                       True)

    def _interrupt_callback(self, channel: int):

        # Check if the last time we detected an interrupt is longer ago than the configured delay between two triggers
        # => set time and reset edge counter
        utc_timestamp = int(time.time())
        if (utc_timestamp - self._last_time_triggered) > self.delayBetweenTriggers:
            self._edge_counter = 0
            self._last_time_triggered = utc_timestamp

        self._edge_counter += 1

        self._log_debug(self._log_tag, "%d Interrupt for sensor triggered." % self._edge_counter)

        # if edge counter reaches threshold
        # => trigger state
        if self._edge_counter >= self.edgeCountBeforeTrigger:
            self._internal_state = self.triggerState

            self._log_debug(self._log_tag, "Sensor triggered.")

    def initialize(self) -> bool:

        # Get the value for the setting if the gpio is pulled up or down.
        if self.pulledUpOrDown == 0:
            pulledUpOrDown = GPIO.PUD_DOWN
        elif self.pulledUpOrDown == 1:
            pulledUpOrDown = GPIO.PUD_UP
        else:
            self._log_critical(self._log_tag, "Value for pulled up or down setting not known.")
            return False

        # Configure gpio pin and get initial state.
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.gpioPin, GPIO.IN, pull_up_down=pulledUpOrDown)

        # set initial state to not triggered
        self.state = 1 - self.triggerState
        self._internal_state = 1 - self.triggerState

        # set edge detection
        if self.edge == 0:
            GPIO.add_event_detect(self.gpioPin,
                                  GPIO.FALLING,
                                  callback=self._interrupt_callback)
        elif self.edge == 1:
            GPIO.add_event_detect(self.gpioPin,
                                  GPIO.RISING,
                                  callback=self._interrupt_callback)
        else:
            self._log_critical(self._log_tag, "Value for edge detection not known.")
            return False

        return True
