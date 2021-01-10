#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import urwid
from typing import List
from ..globalData import ManagerObjProfile


# Internal class that represents the edit field for profile selection.
class _ProfileEditUrwid(urwid.Edit):
    def __init__(self,
                 caption: str,
                 callback_fct,
                 delay: int):
        """
        :param caption:
        :param callback_fct:
        :param delay: delay in seconds used for the option change message that is send to change the profile.
        """
        super().__init__(caption,
                         multiline=False)

        self._callback_fct = callback_fct
        self._delay = delay

    def keypress(self, size, key):

        if key in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "backspace"]:
            super().keypress(size, key)
            return

        if key != "enter":
            return

        input_text = self.edit_text.strip()
        if input_text == "":
            return

        profile_id = int(input_text)
        self.set_edit_text("")

        # Handle selected profile.
        self._callback_fct(profile_id, self._delay)

        return


# this class is an urwid object for the profile view
class ProfileChoiceUrwid:

    def __init__(self,
                 profiles: List[ManagerObjProfile],
                 profile_colors: List[str],
                 callback_fct,
                 delay: int):

        self._log_tag = os.path.basename(__file__)
        self._profiles = profiles

        content = list()
        content.append(urwid.Divider())
        for profile in self._profiles:
            text = urwid.Text(str(profile.id) + ". " + profile.name)
            content.append(urwid.AttrMap(text, profile_colors[profile.id % len(profile_colors)]))
            content.append(urwid.Divider())

        edit = _ProfileEditUrwid("Choose target system profile:\n",
                                 callback_fct,
                                 delay)
        content.append(edit)

        self._profile_pile = urwid.Pile(content)

    def get(self):
        """
        This function returns the final urwid widget that is used by the renderer.
        :return:
        """
        return self._profile_pile
