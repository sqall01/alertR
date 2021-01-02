#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import os
import time
import urwid


# this class is an urwid object for a status
class StatusUrwid:

    def __init__(self, title: str, statusType: str, statusValue: str):

        self.title = title
        self.statusType = statusType
        self.statusValue = statusValue

        self.statusTextWidget = urwid.Text(self.statusType + ": " + str(self.statusValue))
        statusBox = urwid.LineBox(self.statusTextWidget, title=self.title)
        paddedStatusBox = urwid.Padding(statusBox, left=0, right=0)
        self.statusUrwidMap = urwid.AttrMap(paddedStatusBox, "neutral")

    # this function returns the final urwid widget that is used
    # to render the box of a status
    def get(self):
        return self.statusUrwidMap

    # this functipn updates the status type
    def updateStatusType(self, statusType: str):
        self.statusType = statusType
        self.statusTextWidget.set_text(self.statusType + ": " + str(self.statusValue))

    # this functipn updates the status value
    def updateStatusValue(self, statusValue: str):
        self.statusValue = statusValue
        self.statusTextWidget.set_text(self.statusType + ": " + str(self.statusValue))

    # this function changes the color of this urwid object to red
    def turnRed(self):
        self.statusUrwidMap.set_attr_map({None: "redColor"})

    # this function changes the color of this urwid object to green
    def turnGreen(self):
        self.statusUrwidMap.set_attr_map({None: "greenColor"})

    # this function changes the color of this urwid object to gray
    def turnGray(self):
        self.statusUrwidMap.set_attr_map({None: "grayColor"})

    # this function changes the color of this urwid object to the
    # neutral color scheme
    def turnNeutral(self):
        self.statusUrwidMap.set_attr_map({None: "neutral"})


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


# this class is an urwid object for the pin field object
class PinUrwid(urwid.Edit):

    def __init__(self, caption: str, multiline: bool, mask: str, console):
        super().__init__(caption, multiline=multiline, mask=mask)

        self.fileName = os.path.basename(__file__)
        self.console = console

    # this functions handles the key presses
    def keypress(self, size: int, key: str) -> str:

        if key != "enter":
            return super(PinUrwid, self).keypress(size, key)

        # get user input and clear pin field
        inputPin = self.edit_text.strip()
        self.set_edit_text("")

        # check given pin
        if not self.console.checkPin(inputPin):
            return ""

        # set time the screen was unlocked
        self.console.screenUnlockedTime = int(time.time())

        logging.info("[%s] Unlocking screen." % self.fileName)

        # show menu
        self.console.showMenuView()

        return ""
