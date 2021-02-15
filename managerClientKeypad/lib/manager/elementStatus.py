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

    def __init__(self, title: str, text_type: str, test_value: str):

        self._title = title
        self._text_type = text_type
        self._text_value = test_value

        self._status_text_widget = urwid.Text(self._text_type + ": " + str(self._text_value))
        status_box = urwid.LineBox(self._status_text_widget, title=self._title)
        padded_status_box = urwid.Padding(status_box, left=0, right=0)
        self._status_urwid_map = urwid.AttrMap(padded_status_box, "neutral")

    def get(self):
        """
        This function returns the final urwid widget that is used to render the box of a status.
        :return:
        """
        return self._status_urwid_map

    def update_type(self, text_type: str):
        """
        This function updates the text type
        :param text_type:
        """
        self._text_type = text_type
        self._status_text_widget.set_text(self._text_type + ": " + str(self._text_value))

    def update_value(self, text_value: str):
        """
        This function updates the text value
        :param text_value:
        """
        self._text_value = text_value
        self._status_text_widget.set_text(self._text_type + ": " + str(self._text_value))

    def set_color(self, color: str):
        """
        This function changes the color of this urwid object.
        :param color: the string of the corresponding color palette.
        """
        self._status_urwid_map.set_attr_map({None: color})
