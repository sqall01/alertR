#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from .core import _PollingSensor
from ..globalData import SensorDataType
from ..globalData.sensorObjects import SensorDataNone, SensorDataInt, SensorDataFloat, SensorDataGPS, SensorErrorState


class DevSensor(_PollingSensor):
    """
    Class that represents one emulated sensor that can be triggered via keyboard.
    """

    def __init__(self):
        _PollingSensor.__init__(self)

        # used for logging
        self._log_tag = os.path.basename(__file__)

    def __str__(self) -> str:
        return "ID: %d\n" % self.id \
               + "State: %d\n" % self.state \
               + "Error State: %s\n" % self.error_state \
               + "Data: %s" % str(self.data)

    def _execute(self):
        pass

    def _ui_change_state(self):
        # Show sensor values before giving options.
        print("#"*80)
        print(str(self))
        print()

        print("-" * 40)
        print("1. Set sensor state to 'Normal' via Sensor Alert event.")
        print("2. Set sensor state to 'Triggered' via Sensor Alert event.")
        print("3. Set sensor state to 'Normal' via Change State event.")
        print("4. Set sensor state to 'Triggered' via Change State event.")
        print("")

        option_id = int(input("Please enter option: "))

        # Quick way to clear the screen.
        os.system('clear' if os.name == 'posix' else 'cls')

        if option_id == 1:
            self._add_sensor_alert(1 - self.triggerState,
                                   True,
                                   sensor_data=self.data)

        elif option_id == 2:
            self._add_sensor_alert(self.triggerState,
                                   True,
                                   sensor_data=self.data)

        elif option_id == 3:
            self._add_state_change(1 - self.triggerState,
                                   self.data)

        elif option_id == 4:
            self._add_state_change(self.triggerState,
                                   self.data)

        else:
            print("Invalid option.")

    def _ui_change_error_state(self):
        # Show sensor values before giving options.
        print("#"*80)
        print(str(self))
        print()

        print("-" * 40)
        if self.error_state.state == SensorErrorState.OK:
            error_state = int(input("Set new sensor error state: "))
            msg = input("Set new sensor error message: ")
            self._set_error_state(error_state, msg)

        else:
            self._clear_error_state()

        # Quick way to clear the screen.
        os.system('clear' if os.name == 'posix' else 'cls')

        print("Set sensor error state to: %s" % str(self.error_state))

    def _ui_change_data(self):
        # Show sensor values before giving options.
        print("#"*80)
        print(str(self))
        print()

        print("-" * 40)
        if self.sensorDataType == SensorDataType.INT:
            value = int(input("Set new integer value: "))
            unit = input("Set new unit: ")
            self.data = SensorDataInt(value, unit)

        elif self.sensorDataType == SensorDataType.FLOAT:
            value = float(input("Set new float value: "))
            unit = input("Set new unit: ")
            self.data = SensorDataFloat(value, unit)

        elif self.sensorDataType == SensorDataType.GPS:
            lat = float(input("Set new latitude value: "))
            lon = float(input("Set new longitude value: "))
            utctime = int(input("Set new utc timestamp value: "))
            self.data = SensorDataGPS(lat, lon, utctime)

        else:
            return

        # Quick way to clear the screen.
        os.system('clear' if os.name == 'posix' else 'cls')

        self._add_state_change(self.state,
                               self.data)
        print("Set sensor data to: %s" % str(self.data))

    def initialize(self) -> bool:
        self.state = 1 - self.triggerState

        # Initialize the data the sensor holds.
        if self.sensorDataType == SensorDataType.NONE:
            self.data = SensorDataNone()

        if self.sensorDataType == SensorDataType.INT:
            self.data = SensorDataInt(0, "Dev")

        elif self.sensorDataType == SensorDataType.FLOAT:
            self.data = SensorDataFloat(0.0, "Dev")

        elif self.sensorDataType == SensorDataType.GPS:
            self.data = SensorDataGPS(0.0, 0.0, 0)

        return True

    def ui_change_values(self):
        # Show sensor values before giving options.
        print("#"*80)
        print(str(self))
        print()

        print("-" * 40)
        print("1. Change sensor state.")
        print("2. Change sensor error state.")
        if self.sensorDataType != SensorDataType.NONE:
            print("3. Change sensor data.")
        print()

        option_id = int(input("Please enter option: "))

        # Quick way to clear the screen.
        os.system('clear' if os.name == 'posix' else 'cls')

        if option_id == 1:
            self._ui_change_state()

        elif option_id == 2:
            self._ui_change_error_state()

        elif option_id == 3 and self.sensorDataType != SensorDataType.NONE:
            self._ui_change_data()

        else:
            print("Invalid option.")
