#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import threading
import ssl
from typing import Optional


# Class implements an iterator that iterates over a copy of the
# server sessions.
class ServerSessionsIterator(object):

    def __init__(self, server_sessions):
        self.idx = 0
        self.server_sessions = list(server_sessions)

    def __next__(self):
        if self.idx >= len(self.server_sessions):
            raise StopIteration
        self.idx += 1
        return self.server_sessions[self.idx - 1]

    def next(self):
        return self.__next__()


# Class implements the list of server sessions handled by the server.
class ServerSessions(object):

    def __init__(self):
        self._server_sessions = list()
        self._server_sessions_lock = threading.Lock()

    def append(self, server_session):
        with self._server_sessions_lock:
            self._server_sessions.append(server_session)

    def remove(self, server_session):
        with self._server_sessions_lock:
            self._server_sessions.remove(server_session)

    def __iter__(self):
        with self._server_sessions_lock:
            return ServerSessionsIterator(self._server_sessions)


# this class is a global configuration class that holds
# values that are needed all over the client
class GlobalData:

    def __init__(self):

        # version of the used server (and protocol)
        self.version = 0.700  # type: float

        # revision of the used server
        self.rev = 0  # type: int

        # Used database layout version.
        self.dbVersion = 1  # type: int  # TODO increase version

        # name of this server
        self.name = "AlertR Server"  # type: str

        # the instance of this server
        self.instance = "server"  # type: str

        # instance of the storage backend
        self.storage = None

        # instance of the user credential backend
        self.userBackend = None

        # instance of the thread that handles sensor alerts
        self.sensorAlertExecuter = None

        # instance of the thread that handles manager updates
        self.managerUpdateExecuter = None

        # Object that handles option message processing.
        self.option_executer = None

        # this is the time in seconds when the client times out
        self.connectionTimeout = 90

        # This is the time a "persistent" client does not count as
        # timed out if it disconnects from the server.
        self.gracePeriodTimeout = 90

        # The time a reminder of timed out sensors is raised.
        self.timeoutReminderTime = 86400

        # this is the interval in seconds in which the managers
        # are sent updates of the clients (at least)
        self.managerUpdateInterval = 60.0

        # This is the interval in seconds in which the configuration
        # files that can be reloaded during runtime are checked
        # for changes and reloaded if changed.
        self.configCheckInterval = 60.0

        # path to the configuration file of the client
        self.configFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..",
                                       "config",
                                       "config.xml")

        # path to the csv user credentials file (if csv is used as backend)
        self.userBackendCsvFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               "..",
                                               "config",
                                               "users.csv")

        # path to the sqlite database file (if sqlite is used as backend)
        self.storageBackendSqliteFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     "..",
                                                     "config",
                                                     "database.db")

        # location of the certifiacte file
        self.serverCertFile = None  # type: Optional[str]

        # location of the key file
        self.serverKeyFile = None  # type: Optional[str]

        # do clients authenticate themselves via certificates
        self.useClientCertificates = None  # type: Optional[bool]

        # path to CA that is used to authenticate clients
        self.clientCAFile = None  # type: Optional[str]

        # Get TLS/SSL setting.
        try:
            self.sslProtocol = ssl.PROTOCOL_TLS
        except AttributeError:
            self.sslProtocol = ssl.PROTOCOL_SSLv23
        self.sslOptions = ssl.OP_ALL
        self.sslCiphers = "HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4"

        # Port the server is listening on.
        self.server_port = None  # type: Optional[int]

        # a list of all alert levels that are configured on this server
        self.alertLevels = list()

        # A list of all profiles that are configured on this server.
        self.profiles = list()

        # time the server is waiting on receives until a time out occurs
        self.serverReceiveTimeout = 50.0

        # List of the server's internal sensors.
        self.internalSensors = list()

        # Instance of the connection watchdog object.
        self.connectionWatchdog = None

        # Instance of the config watchdog object.
        self.configWatchdog = None

        # Information concerning logging instances.
        self.logger = None
        self.logdir = None  # type: Optional[str]
        self.loglevel = None  # type: Optional[str]

        # Number of failed attempts for version information fetching
        # from the update repository before generating a notification.
        self.updateMaxFails = 10

        # Unique id of this server (is also the username of this server).
        self.uniqueID = None  # type: Optional[str]

        # List of all sessions that are handled by the server.
        self.serverSessions = ServerSessions()

        # Describes if the survey is activated.
        self.survey_activated = None  # type: Optional[bool]

        # URL for update repository.
        self.update_url = None  # type: Optional[str]
