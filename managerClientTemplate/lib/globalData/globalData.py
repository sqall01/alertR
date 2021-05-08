#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
from typing import Optional
from .systemData import SystemData


# this class is a global configuration class that holds 
# values that are needed all over the client
class GlobalData:

    def __init__(self):

        # version of the used client (and protocol)
        self.version = 0.800  # type: float

        # revision of the used client
        self.rev = 1  # type: int

        # name of this client
        self.name = "AlertR Manager Client Template"  # type: str

        # the instance of this client
        self.instance = "managerClientTemplate"  # type: str

        # interval in which a ping should be send when 
        # no data was received/send     
        self.pingInterval = 30  # type: int

        # type of this node/client
        self.nodeType = "manager"  # type: str

        # path to the configuration file of the client
        self.configFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..",
                                       "..",
                                       "config",
                                       "config.xml")  # type: str

        # this flags indicate if email alerts via smtp are active
        self.smtpAlert = None

        # this holds the description of this client
        self.description = None

        # Holds copy of the AlertR system data.
        self.system_data = SystemData()

        # this variable holds the object of the server communication
        self.serverComm = None

        # Flag that indicates if this node is registered as persistent
        # (0 or 1).
        self.persistent = None  # type: Optional[int]
