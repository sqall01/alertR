#!/usr/bin/env python3

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
        self.state = None  # type: Optional[int]

        # the gpio pin number (NOTE: python uses the actual
        # pin number and not the gpio number)
        self.gpio_pin = None  # type: Optional[int]
        self.state_lock = threading.Lock()

        # the state the gpio pin is set to when no alert is triggered
        self.gpio_pin_state_normal = None

        # the state the gpio pin is set to when the alert is triggered
        self.gpio_pin_state_triggered = None

        # If handling of the received messages are activated.
        self.recv_triggered_activated = False
        self.recv_normal_activated = False
        self.recv_off_activated = False

        # States the Alert object should be set to when sensor alert message with corresponding state is received.
        self.recv_triggered_state = None  # type: Optional[int]
        self.recv_normal_state = None  # type: Optional[int]

        # If the reset of the gpio pin is activated.
        self.gpio_reset_activated = False

        # Time in seconds the gpio pin is reseted to the normal state
        # after it was triggered (if set to 0 this feature is deactivated).
        self.gpio_reset_state_time = 0
        self.gpio_reset_thread = None  # type: Optional[RaspberryPiGPIOReset]

    def set_state(self, new_state: int):
        """
        Sets the state the Alert is currently in.

        :param new_state: 0 (normal) or 1 (triggered)
        """
        with self.state_lock:
            if new_state == 1 and self.state == 0:
                self.state = 1
                GPIO.output(self.gpio_pin, self.gpio_pin_state_triggered)
            elif new_state == 0 and self.state == 1:
                self.state = 0
                GPIO.output(self.gpio_pin, self.gpio_pin_state_normal)

    def get_state(self) -> int:
        """
        Returns the state the Alert is currently in.

        :return: state: 0 (normal) or 1 (triggered)
        """
        with self.state_lock:
            return self.state

    def initialize(self):
        """
        Is called when Alert Client is started to initialize the Alert object.
        """

        # Set the state of the alert to "normal".
        self.state = 0

        # configure gpio pin and set initial state
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.gpio_pin, GPIO.OUT)
        GPIO.output(self.gpio_pin, self.gpio_pin_state_normal)

    def _process_state_change(self, target_state: int):

        curr_state = self.get_state()

        # Only execute if we are not in the state already.
        if curr_state != target_state:

            logging.debug("[%s]: Setting Alert '%d' into state %d."
                          % (self.log_tag, self.id, target_state))

            self.set_state(target_state)

            # Start reset watchdog if reset is activated and target state of Alert object was "triggered".
            if self.gpio_reset_activated and target_state == 1:

                logging.debug("[%s]: Starting reset watchdog for Alert '%d' with %d seconds."
                              % (self.log_tag, self.id, self.gpio_reset_state_time))

                # Ask already running thread to stop (if exists).
                if self.gpio_reset_thread is not None:
                    self.gpio_reset_thread.set_exit()

                self.gpio_reset_thread = RaspberryPiGPIOReset(self)
                # set thread to daemon
                # => threads terminates when main thread terminates
                self.gpio_reset_thread.daemon = True
                self.gpio_reset_thread.start()

        else:
            logging.debug("[%s]: Alert '%d' already in state %d." % (self.log_tag, self.id, curr_state))

    def alert_triggered(self, sensor_alert: SensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 1.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        if not self.recv_triggered_activated:
            return

        self._process_state_change(self.recv_triggered_state)

    def alert_normal(self, sensor_alert: SensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 0.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        if not self.recv_normal_activated:
            return

        self._process_state_change(self.recv_normal_state)

    def alert_off(self):
        """
        Is called when Alert Client receives a "sensoralertsoff" message which is
        sent as soon as AlertR alarm status is deactivated.
        """
        if not self.recv_off_activated:
            return

        self._process_state_change(0)


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
        self.reset_time = alert.gpio_reset_state_time

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

            curr_state = self.alert.get_state()
            curr_exit = self.get_exit()

            # Stop thread if the alert is not triggered anymore or
            # if we were asked to stop.
            if curr_state == 0 or curr_exit:
                self.set_exit()
                return

        logging.info("[%s]: Resetting alert with id %d to normal state after %d seconds."
                     % (self.alert.log_tag, self.alert.id, self.reset_time))

        self.alert.set_state(0)
        self.set_exit()
