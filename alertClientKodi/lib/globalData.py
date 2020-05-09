#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from typing import Optional


# this class is a global configuration class that holds 
# values that are needed all over the client
class GlobalData:

    def __init__(self):

        # version of the used client (and protocol)
        self.version = 0.600  # type: float

        # revision of the used client
        self.rev = 2  # type: int

        # name of this client
        self.name = "AlertR Alert Client Kodi"  # type: str

        # the instance of this client
        self.instance = "alertClientKodi"  # type: str

        # interval in which a ping should be send when 
        # no data was received/send
        self.pingInterval = 30  # type: int

        # type of this node/client
        self.nodeType = "alert"  # type: str

        # path to the configuration file of the client
        self.configFile = os.path.dirname(os.path.abspath(__file__)) + "/../config/config.xml"  # type: str

        # instance of the email alerting object
        self.smtpAlert = None

        # this is a list of all alert objects that are managed by
        # this client
        self.alerts = list()

        # this variable holds the object of the server communication
        self.serverComm = None

        # Flag that indicates if this node is registered as persistent
        # (0 or 1).
        self.persistent = None  # type: Optional[int]
