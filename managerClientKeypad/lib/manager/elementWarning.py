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


# this class is an urwid object for the warning view
class WarningUrwid:

    def __init__(self):

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        separator = urwid.Text("")
        self.description = urwid.Text("Sensor 'PLACEHOLDER' in state 'PLACEHOLDER'.",
                                      align="center")

        option1 = urwid.Text("1. Continue", align="center")
        option2 = urwid.Text("2. Abort", align="center")
        instruction = urwid.Text("Please, choose an option.", align="center")

        warningPile = urwid.Pile([self.description, separator, option1, option2, separator, instruction])

        warningBox = urwid.LineBox(warningPile, title="Warning")

        self.warningMap = urwid.AttrMap(warningBox, "redColor")

    # inserts the description and state for the sensor
    # (is called before the warning view is shown)
    def setSensorData(self, description, state):

        if state == 1:
            self.description.set_text("Sensor '%s' in state 'triggered'." % description)

        elif state == 0:
            self.description.set_text("Sensor '%s' in state 'normal'." % description)

        else:

            logging.error("[%s]: Sensor '%s' not in a defined state." % (self.fileName, description))
            self.description.set_text("Sensor '%s' in state 'undefined'." % description)

    # this function returns the final urwid widget that is used
    # by the renderer
    def get(self):
        return self.warningMap
