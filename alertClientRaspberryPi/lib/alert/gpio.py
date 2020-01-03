#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import os
import logging
import threading
import RPi.GPIO as GPIO
from .core import _Alert, SensorAlert
from typing import Optional


# this function represents an alert that sets the Raspberry Pi GPIO to high
# or low if triggered
class RaspberryPiGPIOAlert(_Alert):

    def __init__(self):
        _Alert.__init__(self)

        # File nme of this file (used for logging).
        self.log_tag = os.path.basename(__file__)

        # this flag is used to signalize if the alert is triggered or not
        self.triggered = None

        # the gpio pin number (NOTE: python uses the actual
        # pin number and not the gpio number)
        self.gpioPin = None
        self.state_lock = threading.Lock()

        # the state the gpio pin is set to when no alert is triggered
        self.gpioPinStateNormal = None

        # the state the gpio pin is set to when the alert is triggered
        self.gpioPinStateTriggered = None

        # Time in seconds the gpio pin is reseted to the normal state
        # after it was triggered (if set to 0 this feature is deactivated).
        self.gpioResetStateTime = 0
        self.gpio_reset_thread = None  # type: Optional[RaspberryPiGPIOReset]

    # Function that sets alert state.
    def set_state(self, state: bool):

        with self.state_lock:
            if state and not self.triggered:
                self.triggered = True
                GPIO.output(self.gpioPin, self.gpioPinStateTriggered)
            elif not state and self.triggered:
                self.triggered = False
                GPIO.output(self.gpioPin, self.gpioPinStateNormal)

    # Function that returns the alert state.
    def get_state(self) -> bool:
        with self.state_lock:
            return self.triggered

    # this function is called once when the alert client has connected itself
    # to the server
    def initializeAlert(self):

        # set the state of the alert to "not triggered"
        self.triggered = False

        # configure gpio pin and set initial state
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.gpioPin, GPIO.OUT)
        GPIO.output(self.gpioPin, self.gpioPinStateNormal)

    # this function is called when this alert is triggered
    def triggerAlert(self, sensorAlert: SensorAlert):

        state = self.get_state()

        # only execute if not triggered
        if not state:
            self.set_state(True)

            # Start thread to reset gpio pin.
            if self.gpioResetStateTime > 0:

                # Ask already running thread to stop (if exists).
                if self.gpio_reset_thread is not None:
                    self.gpio_reset_thread.set_exit()

                self.gpio_reset_thread = RaspberryPiGPIOReset(self)
                # set thread to daemon
                # => threads terminates when main thread terminates
                self.gpio_reset_thread.daemon = True
                self.gpio_reset_thread.start()

    # this function is called when the alert is stopped
    def stopAlert(self, sensorAlert: SensorAlert):

        state = self.get_state()

        # only execute if the alert was triggered
        if state:
            self.set_state(False)


class RaspberryPiGPIOReset(threading.Thread):
    """
    GPIO reset watchdog that runs in a thread.
    Resets the GPIO when a timer is up.
    """
    def __init__(self, alert: RaspberryPiGPIOAlert):
        """
        Initialization function.

        :param alert: The corresponding alert object.
        """
        threading.Thread.__init__(self)

        self.alert = alert

        self.exit_flag = False
        self.lock = threading.Lock()
        self.reset_time = alert.gpioResetStateTime

    def set_exit(self):
        """
        Sets the thread to stop.
        """
        with self.lock:
            self.exit_flag = True

    def get_exit(self) -> bool:
        """
        Gets the exit status of the thread.

        :return: exist status of the thread.
        """
        with self.lock:
            return self.exit_flag

    def run(self):
        """
        Runs a timer and resets the GPIO pin of the alert object if it is up.
        """

        # Wait until the reset time was reached.
        end_time = int(time.time()) + self.reset_time
        while int(time.time()) < end_time:
            time.sleep(1)

            state = self.alert.get_state()
            exit = self.get_exit()

            # Stop thread if the alert is not triggered anymore or
            # if we were asked to stop.
            if not state or exit:
                self.set_exit()
                return

        logging.info("[%s]: Resetting alert with id %d to normal state after %d seconds."
                     % (self.alert.log_tag, self.alert.id, self.reset_time))

        self.alert.set_state(False)
        self.set_exit()
