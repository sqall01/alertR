#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import collections
from typing import Optional
from .systemData import SystemData


# this class is a global configuration class that holds 
# values that are needed all over the client
class GlobalData:

    def __init__(self):

        # version of the used client (and protocol)
        self.version: float = 0.601

        # revision of the used client
        self.rev: int = 0

        # name of this client
        self.name: str = "AlertR Manger Client Database"

        # the instance of this client
        self.instance: str = "managerClientDatabase"

        # interval in which a ping should be send when 
        # no data was received/send     
        self.pingInterval: int = 30

        # type of this node/client
        self.nodeType: str = "manager"

        # path to the configuration file of the client
        self.configFile: str = os.path.dirname(os.path.abspath(__file__)) + "/../config/config.xml"

        # How often the AlertR client should try to connect to the
        # MySQL server when the connection establishment fails.
        self.storageBackendMysqlRetries: int = 5

        # path to the unix socket which is used to communicate
        # with the web page (only set when server is activated
        # in the configuration file)
        self.unixSocketFile = None

        # this flags indicate if email alerts via smtp are active
        self.smtpAlert = None

        # this holds the description of this client
        self.description = None

        # Holds copy of the AlertR system data.
        self.system_data = SystemData()

        # this is the time in seconds when the sensor should be
        # handled as timed out
        self.connectionTimeout: int = 60

        # this variable holds the object of the server communication
        self.serverComm = None

        # instance of the storage backend
        self.storage = None

        # the amount of days sensor alerts are kept in the database before
        # they are removed (value 0 will not store any sensor alerts)
        self.sensorAlertLifeSpan: Optional[int] = None

        # Flag that indicates if this node is registered as persistent
        # (0 or 1).
        self.persistent: Optional[int] = None
