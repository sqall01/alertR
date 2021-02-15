#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import os
import urwid
from typing import List
from .localObjects import SensorWarningState


# this class is an urwid object for the warning view
class WarningUrwid:

    def __init__(self):

        # file nme of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        separator = urwid.Text("")
        self._description = urwid.Text("Sensor 'PLACEHOLDER' in state 'PLACEHOLDER'.",
                                       align="center")

        option1 = urwid.Text("1. Continue", align="center")
        option2 = urwid.Text("2. Abort", align="center")
        instruction = urwid.Text("Please, choose an option.", align="center")

        warning_pile = urwid.Pile([self._description, separator, option1, option2, separator, instruction])

        warning_box = urwid.LineBox(warning_pile, title="Warning")

        self._warning_map = urwid.AttrMap(warning_box, "redColor")

        self._sensor_warning_states = list()

        self._callback_fct = None
        self._callback_fct_args = ()

    def _set_sensor_data(self, description: str, state: int):
        """
        Inserts the description and state for the sensor (is called before the warning view is shown).
        :param description:
        :param state:
        """
        if state == 1:
            self._description.set_text("Sensor '%s' in state 'triggered'." % description)

        elif state == 0:
            self._description.set_text("Sensor '%s' in state 'normal'." % description)

        else:

            logging.error("[%s]: Sensor '%s' not in a defined state." % (self._log_tag, description))
            self._description.set_text("Sensor '%s' in state 'undefined'." % description)

    def execute_callback_fct(self):
        """
        Execute callback function with args.
        """
        if self._callback_fct is not None:
            self._callback_fct(*self._callback_fct_args)

        else:
            logging.error("[%s]: No callback function to execute." % self._log_tag)

    def get(self) -> urwid.AttrMap:
        """
        This function returns the final urwid widget that is used by the renderer.
        :return:
        """
        return self._warning_map

    def prepare_next_warning_state(self) -> bool:
        """
        Prepares the next sensor warning state by setting the texts of the urwid element.
        :return: True if a sensor warning state was prepared, False if no sensor warning state exists.
        """
        if self._sensor_warning_states:
            warning_state = self._sensor_warning_states.pop(0)
            self._set_sensor_data(warning_state.description, warning_state.state)
            return True

        return False

    def set_callback_fct(self, callback_fct, args):
        """
        Set callback function and kwargs.
        :param callback_fct:
        :param args:
        """
        self._callback_fct = callback_fct
        self._callback_fct_args = args

    def set_sensor_warning_states(self, sensor_warnings: List[SensorWarningState]):
        self._sensor_warning_states = list(sensor_warnings)
