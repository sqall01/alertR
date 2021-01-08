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
