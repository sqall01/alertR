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


# this class is a global configuration class that holds 
# values that are needed all over the client
class GlobalData:

    def __init__(self):

        # version of the used client (and protocol)
        self.version = 0.600  # type: float

        # revision of the used client
        self.rev = 2  # type: int

        # name of this client
        self.name = "AlertR Manager Client Database"  # type: str

        # the instance of this client
        self.instance = "managerClientDatabase"  # type: str

        # interval in which a ping should be send when 
        # no data was received/send     
        self.pingInterval = 30  # type: int

        # type of this node/client
        self.nodeType = "manager"  # type: str

        # path to the configuration file of the client
        self.configFile = os.path.dirname(os.path.abspath(__file__)) + "/../config/config.xml"  # type: str

        # How often the AlertR client should try to connect to the
        # MySQL server when the connection establishment fails.
        self.storageBackendMysqlRetries = 5  # type: int

        # path to the unix socket which is used to communicate
        # with the web page (only set when server is activated
        # in the configuration file)
        self.unixSocketFile = None

        # this flags indicate if email alerts via smtp are active
        self.smtpAlert = None

        # this holds the description of this client
        self.description = None

        # this is a list of all option objects that are received
        self.options = list()

        # this is a list of all node objects that are received
        self.nodes = list()

        # this is a list of all sensor objects that are received
        self.sensors = list()

        # this is a list of all manager objects that are received
        self.managers = list()

        # this is a list of all alert objects that are received
        self.alerts = list()

        # this is a list of all sensor alert objects that are received
        self.sensorAlerts = list()

        # this is a list of all alert level objects that are received
        self.alertLevels = list()

        # this is the time in seconds when the sensor should be
        # handled as timed out
        self.connectionTimeout = 60  # type: int

        # this variable holds the object of the server communication
        self.serverComm = None

        # instance of the storage backend
        self.storage = None

        # the amount of days sensor alerts are kept in the database before
        # they are removed (value 0 will not store any sensor alerts)
        self.sensorAlertLifeSpan = None  # type: Optional[int]

        # the amount of days events are kept in the database before
        # they are removed (value 0 will not store any events)
        self.eventsLifeSpan = None  # type: Optional[int]

        # a (thread safe) list of events that are occurred
        # (an event is anything that has happened on the
        # alert system for example a sensor alert, a state change
        # of an sensor, an option change etc.)
        self.events = collections.deque()

        # Flag that indicates if this node is registered as persistent
        # (0 or 1).
        self.persistent = None  # type: Optional[int]
