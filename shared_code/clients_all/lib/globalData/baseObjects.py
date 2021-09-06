#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
from typing import Any, Dict


class InternalState:
    NOT_USED = 0
    STORED = 1
    DELETED = 2


class LocalObject:

    def __init__(self):
        # Internal data used by the manager.
        self.internal_state = InternalState.NOT_USED
        self.internal_data = dict()

        # To lock internal data structure if necessary for multi threaded programs.
        self.internal_data_lock = threading.Lock()

    @staticmethod
    def deepcopy(obj):
        """
        This function copies all attributes of the given object to a new object.
        :param obj:
        :return: object of this class
        """
        raise NotImplementedError("Abstract class.")

    def is_deleted(self):
        return self.internal_state == InternalState.DELETED

    def is_stored(self):
        return self.internal_state == InternalState.STORED

    def copy_to_dict(self) -> Dict[str, Any]:
        """
        Copies this object into a dictionary representation.
        :return: dictionary representation of a copy of this object
        """
        raise NotImplementedError("Abstract class.")

    def deepcopy_obj(self, obj):
        """
        This function copies all attributes of the given object to this object.
        :param obj:
        :return: this object
        """
        raise NotImplementedError("Abstract class.")
