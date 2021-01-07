#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

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

    # this function updates the status type
    def updateStatusType(self, statusType: str):
        self.statusType = statusType
        self.statusTextWidget.set_text(self.statusType + ": " + str(self.statusValue))

    # this function updates the status value
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