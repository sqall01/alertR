#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import math
import os
import threading
import time
import RPi.GPIO as GPIO
from typing import Optional, Union
from .number import _NumberSensor
from ..globalData.sensorObjects import SensorDataFloat, SensorDataInt, SensorDataType


class RaspberryPiGPIOWindSpeedSensor(_NumberSensor):
    """
    Controls one wind speed sensor at a gpio pin of the raspberry pi.
    """

    def __init__(self):
        _NumberSensor.__init__(self)

        self._unit = "km/h"

        # Used for logging.
        self._log_tag = os.path.basename(__file__)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.FLOAT
        self.data = SensorDataFloat(0.0, self._unit)

        self.radius_cm = None  # type: Optional[float]
        self.signals_per_rotation = None  # type: Optional[float]

        # The interval in seconds in which an update of the current held data
        # should be sent to the server.
        self.interval = None  # type: Optional[int]

        self._thread_calculate_speed = None  # type: Optional[threading.Thread]

        # the gpio pin number (NOTE: python uses the actual
        # pin number and not the gpio number)
        self.gpioPin = None

        self._bouncetime = 2
        self._last_data_update = 0.0

        # Attributes important to wind speed calculation
        self._wind_ctr_lock = threading.Lock()
        self._wind_ctr = 0.0
        self._wind_interval = 2.0  # in seconds
        self._wind_speed_lock = threading.Lock()
        self._wind_speed = 0.0
        self._circumference_cm = None  # type: Optional[float]

        # This sensor type string is used for log messages.
        self._log_desc = "Wind speed"

    def _calculate_speed(self):
        """
        This internal function is started in a thread to periodically update the current wind speed.
        """
        while True:
            time.sleep(self._wind_interval)

            """
            Reference: https://projects.raspberrypi.org/en/projects/build-your-own-weather-station/5
            - Formula: speed = ( (signals / 2) * (2 * pi * radius) ) / time
            """
            with self._wind_ctr_lock:
                wind_ctr = self._wind_ctr
                self._wind_ctr = 0.0
            rotations = wind_ctr / self.signals_per_rotation
            dist_km = (self._circumference_cm * rotations) / 100000.0
            km_per_sec = dist_km / self._wind_interval
            km_per_h = round(km_per_sec * 3600.0, 2)

            # TODO remove after testing
            self._log_debug(self._log_tag, "Wind speed for '%s': %.2f km/h" % (self.description, km_per_h))

            # Set the highest wind speed as the one that will be reported to AlertR.
            if km_per_h > self._wind_speed:
                with self._wind_speed_lock:
                    self._wind_speed = km_per_h

    def _get_data(self) -> Optional[Union[SensorDataInt, SensorDataFloat]]:
        """
        Internal function that returns the current wind speed.

        :return: wind speed value or None
        """

        utc_timestamp = int(time.time())
        if (utc_timestamp - self._last_data_update) > self.interval:
            self._last_data_update = utc_timestamp

            self._log_debug(self._log_tag, "Wind speed for '%s': %.2f km/h" % (self.description, self._wind_speed))

            self.data = SensorDataFloat(self._wind_speed, self._unit)
            with self._wind_speed_lock:
                self._wind_speed = 0.0

        return self.data

    def _interrupt_callback(self, channel: int):
        """
        This function is called on falling edges on the GPIO and counts the number of interrupts.
        """
        with self._wind_ctr_lock:
            self._wind_ctr += 1.0

    def initialize(self) -> bool:
        # Configure gpio pin and get initial state
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.gpioPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.gpioPin,
                              GPIO.FALLING,
                              callback=self._interrupt_callback,
                              bouncetime=self._bouncetime)

        self._circumference_cm = (2.0 * math.pi) * self.radius_cm

        self.state = 1 - self.triggerState

        return True

    def start(self) -> bool:
        """
        Starts the wind speed sensor and checks if the object has necessary values set.

        :return: success or failure
        """
        self._thread_calculate_speed = threading.Thread(target=self._calculate_speed)
        self._thread_calculate_speed.daemon = True
        self._thread_calculate_speed.start()
        return super().start()
