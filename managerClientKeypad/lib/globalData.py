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
        self.name = "AlertR Manager Client Keypad"  # type: str

        # the instance of this client
        self.instance = "managerClientKeypad"  # type: str

        # interval in which a ping should be send when 
        # no data was received/send     
        self.pingInterval = 30  # type: int

        # type of this node/client
        self.nodeType = "manager"  # type: str

        # path to the configuration file of the client
        self.configFile = os.path.dirname(os.path.abspath(__file__)) + "/../config/config.xml"  # type: str

        # this flags indicate if email alerts via smtp are active
        self.smtpAlert = None

        # this holds the description of this client
        self.description = None  # type: Optional[str]

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

        # this is the instance of the screen updateter object that is
        # responsible of updating the screen
        self.screenUpdater = None

        # this variable holds the object of the server communication
        self.serverComm = None

        # this is the time in seconds when the screen should be locked
        # (if it was unlocked by the user)
        self.unlockedScreenTimeout = 20  # type: int

        # this is an instance of the console object that handles
        # the screen
        self.console = None

        # this is a list of pins that allow the user to unlock the screen
        # of the manager
        self.pins = list()

        # the time given in seconds which are used by the time delayed
        # activation of the alert system (this option is given to the user
        # in the menu)
        self.timeDelayedActivation = None  # type: Optional[int]

        # the object that is used to output audio (if activated)
        self.audioOutput = None

        # list of sensor states that cause a warning confirmation message
        # before the alarm system is activated
        self.sensorWarningStates = list()

        # Flag that indicates if this node is registered as persistent
        # (0 or 1).
        self.persistent = None  # type: Optional[int]
