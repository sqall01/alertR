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
from typing import Optional, Union, Dict
from .number import _NumberSensor
from ..globalData.sensorObjects import SensorDataFloat, SensorDataInt, SensorDataType


class WindSpeedCalculator:

    def __init__(self, gpio_pin: int, radius_cm: float, signals_per_rotation: int):
        self._signals_per_rotation = float(signals_per_rotation)
        self._gpio_pin = gpio_pin

        # Attributes important to wind speed calculation
        self._wind_ctr_lock = threading.Lock()
        self._wind_ctr = 0.0
        self._wind_interval = 2.0  # in seconds
        self._km_per_h = 0.0
        self._circumference_cm = (2.0 * math.pi) * radius_cm

        # Configure gpio pin and get initial state
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self._gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self._gpio_pin,
                              GPIO.FALLING,
                              callback=self._interrupt_callback)

        self._thread_calculate_speed = threading.Thread(target=self._calculate_speed)
        self._thread_calculate_speed.daemon = True
        self._thread_calculate_speed.start()

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
            rotations = wind_ctr / self._signals_per_rotation
            dist_km = (self._circumference_cm * rotations) / 100000.0
            km_per_sec = dist_km / self._wind_interval
            self._km_per_h = round(km_per_sec * 3600.0, 2)

    def _interrupt_callback(self, _: int):
        """
        This function is called on falling edges on the GPIO and counts the number of interrupts.
        """
        with self._wind_ctr_lock:
            self._wind_ctr += 1.0

    def get_wind_speed(self) -> float:
        return self._km_per_h


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
        self.signals_per_rotation = None  # type: Optional[int]
        self.onlyMaxInterval = None  # type: Optional[int]

        # The interval in seconds in which an update of the current held data
        # should be sent to the server.
        self.interval = None  # type: Optional[int]

        # the gpio pin number (NOTE: python uses the actual
        # pin number and not the gpio number)
        self.gpioPin = None

        self._last_data_update = 0.0

        # This sensor type string is used for log messages.
        self._log_desc = "Wind speed"

        self._wind_speed_calculator = None  # type: Optional[WindSpeedCalculator]

        # Global mapping of all windspeed calculators.
        self.wind_speed_calculator_map = None  # type: Optional[int, WindSpeedCalculator]

        self._wind_speed = 0.0
        self._wind_speed_history = dict()  # type: Dict[int, float]

    def _get_data(self) -> Optional[Union[SensorDataInt, SensorDataFloat]]:
        """
        Internal function that returns the current wind speed.

        :return: wind speed value or None
        """

        # Only report the highest value to the AlertR system in the given send interval.
        utc_timestamp = int(time.time())
        temp_wind_speed = self._wind_speed_calculator.get_wind_speed()
        if temp_wind_speed > self._wind_speed:
            self._wind_speed = temp_wind_speed

        if (utc_timestamp - self._last_data_update) > self.interval:
            self._last_data_update = utc_timestamp

            # Search for highest wind speed in the set interval if it was configured.
            if self.onlyMaxInterval != 0:
                self._wind_speed_history[utc_timestamp] = self._wind_speed

                # Delete old wind speed data
                for wind_speed_time in list(self._wind_speed_history.keys()):
                    if wind_speed_time + self.onlyMaxInterval < utc_timestamp:
                        del self._wind_speed_history[wind_speed_time]

                self._wind_speed = max(self._wind_speed_history.values())

            data = SensorDataFloat(self._wind_speed, self._unit)

            self._log_debug(self._log_tag, "Wind speed for '%s': %.2f km/h" % (self.description, self._wind_speed))

            self._wind_speed = 0.0

            return data

        return self.data

    def initialize(self) -> bool:
        # Make sure we only have one wind speed calculator object per GPIO.
        if self.gpioPin not in self.wind_speed_calculator_map.keys():
            self.wind_speed_calculator_map[self.gpioPin] = WindSpeedCalculator(self.gpioPin,
                                                                               self.radius_cm,
                                                                               self.signals_per_rotation)
        self._wind_speed_calculator = self.wind_speed_calculator_map[self.gpioPin]

        self.state = 1 - self.triggerState

        return True

    def start(self) -> bool:
        """
        Starts the wind speed sensor and checks if the object has necessary values set.

        :return: success or failure
        """
        return super().start()
