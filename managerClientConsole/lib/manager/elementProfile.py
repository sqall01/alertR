#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import urwid
from typing import List
from ..globalData import ManagerObjProfile


# this class is an urwid object for a detailed manager output
class ProfileChoiceUrwid:

    def __init__(self,
                 profiles: List[ManagerObjProfile],
                 profile_colors: List[str],
                 callback_fct):

        self._profiles = profiles

        content = list()
        content.append(urwid.Divider())
        for profile in self._profiles:
            button = urwid.Button(profile.name)
            urwid.connect_signal(button, 'click', callback_fct, profile)
            content.append(urwid.AttrMap(button, profile_colors[profile.id % len(profile_colors)]))
            content.append(urwid.Divider())

        # Use ListBox here because it handles all the scrolling part automatically.
        detailed_list = urwid.ListBox(urwid.SimpleListWalker(content))
        detailed_frame = urwid.Frame(detailed_list,
                                     footer=urwid.Text("Keys: ESC - Back, "
                                                       + "Up/Down - Move Cursor, "
                                                       + "Enter - Select Element"))
        self._detailed_box = urwid.LineBox(detailed_frame, title="Change Profile")

    def get(self) -> urwid.LineBox:
        """
        This function returns the final urwid widget that is used to render this object.
        :return:
        """
        return self._detailed_box
