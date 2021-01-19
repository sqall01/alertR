#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import Optional, List, Any, Dict
from .baseObjects import LocalObject


# this class represents an profile change of the server
class AlertObjProfileChange(LocalObject):

    def __init__(self):
        super().__init__()
        self.profileId = None  # type: Optional[int]

    def __str__(self) -> str:
        tmp = "ProfileChange (Id: %s)" \
              % (str(self.profileId) if self.profileId is not None else "None")
        return tmp

    def deepcopy(self, profile_change):
        """
        This function copies all attributes of the given profile change to this object.
        :param profile_change:
        :return:
        """
        self.profileId = profile_change.profileId
        return self
