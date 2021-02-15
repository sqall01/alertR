#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import urwid
import types


# This class is an urwid object for the search field.
class SearchViewUrwid:

    def __init__(self, callbackFunction: types.FunctionType):
        self.edit = urwid.Edit()
        editList = urwid.ListBox(urwid.SimpleListWalker([self.edit]))
        editFrame = urwid.Frame(editList, footer=urwid.Text("Keys: ESC - Back, Enter - Search"))
        self.editBox = urwid.LineBox(editFrame, title="Search")

        self.callbackFunction = callbackFunction

        # Connect callback function that is called whenever the state
        # of the edit field changes (a user presses a key).
        # Used to show the search results while typing.
        urwid.connect_signal(self.edit, "change", self.callbackFunction, "")

    def __del__(self):

        # Disconnect callback function.
        if self.edit is not None and self.callbackFunction is not None:
            urwid.disconnect_signal(self.edit, "change", self.callbackFunction, "")

    # This function returns the final urwid widget that is used
    # to render this object.
    def get(self) -> urwid.LineBox:
        return self.editBox

    # Returns entered text.
    def getText(self) -> str:
        return self.edit.edit_text
