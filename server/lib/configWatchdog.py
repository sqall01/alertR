#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import time
import logging
import os
import hashlib
from userBackend import CSVBackend


# This class handles all changes to configurations that can be handled
# at runtime.
class ConfigWatchdog(threading.Thread):

    def __init__(self, globalData, configCheckInterval):
        threading.Thread.__init__(self)

        # Get global configured data
        self.globalData = globalData
        self.logger = self.globalData.logger
        self.userBackend = self.globalData.userBackend
        self.managerUpdateExecuter = self.globalData.managerUpdateExecuter
        self.storage = self.globalData.storage
        self.serverSessions = self.globalData.serverSessions

        # File name of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # Get value for the configured check interval.
        self.configCheckInterval = configCheckInterval

        # Set exit flag as false
        self.exitFlag = False

        # Set which configuration files should be checked.
        self.CSVUsersCheck = False
        self.CSVUsersHash  = ""
        self.CSVUsersFile = self.globalData.userBackendCsvFile
        self.CSVUsersLastCheck = 0.0
        if isinstance(self.userBackend, CSVBackend):
            self.CSVUsersCheck = True


    def _createHash(self, fileLocation):
        md5 = hashlib.md5()
        with open(fileLocation, 'rb') as fp:
            while True:
                data = fp.read(4096)
                if not data:
                    break
                md5.update(data)

        return md5.hexdigest()


    # This function synchronizes the existing usernames with
    # existing connections. When a connection still exists with
    # a username which does not exist anymore, it is closed.
    def _syncUsernamesAndConnections(self):

        for serverSession in self.serverSessions:

            # Check if client communication object exists.
            if serverSession.clientComm is None:
                continue

            username = serverSession.clientComm.username
            if username is None:
                continue

            # Close connection to the client if the username
            # does no longer exist.
            if not self.userBackend.userExists(username):

                self.logger.info("[%s]: Username '%s' does not exist anymore. "
                    % (self.fileName, username)
                    + "Closing connection to client.")

                serverSession.closeConnection()


    # This function synchronizes the existing usernames with
    # the entries in the database. When an entry still exists for
    # a username which does not exist anymore, delete it.
    #
    # return True or False
    def _syncUsernamesAndDatabase(self):

        nodesList = self.storage.getNodes(self.logger)

        if nodesList is None:
            self.logger.error("[%s]: Not able to retrieve nodes from database."
                % self.fileName)
            return

        # Check the username of each node if it still exists and delete if
        # it does not.
        for nodeObj in nodesList:
            nodeId = nodeObj.id
            username = nodeObj.username
            nodeType = nodeObj.nodeType

            # Ignore server node.
            if nodeType == "server":
                continue

            if not self.userBackend.userExists(username):

                self.logger.info("[%s]: Username '%s' does not exist anymore. "
                    % (self.fileName, username)
                    + "Removing node from database.")

                if not self.storage.deleteNode(nodeId, self.logger):

                    self.logger.error("[%s]: Not able to delete node with id "
                        % self.fileName
                        + "'%d'."
                        % nodeId)


    def run(self):

        # Synchronize database with usernames in backend once in the
        # beginning in order to catch changes that were made while
        # the server was not running.
        self._syncUsernamesAndDatabase()

        if self.CSVUsersCheck and os.path.isfile(self.CSVUsersFile):
            self.CSVUsersHash = self._createHash(self.CSVUsersFile)
            self.CSVUsersLastCheck = int(time.time())

        while True:
            # Wait 5 seconds before checking time of last received data.
            for i in range(5):
                if self.exitFlag:
                    self.logger.info("[%s]: Exiting ConfigWatchdog."
                        % self.fileName)
                    return
                time.sleep(1)

            # Check CSV users file if we are using it.
            if self.CSVUsersCheck:
                diffTime = int(time.time()) - self.CSVUsersLastCheck
                if diffTime > self.configCheckInterval:

                    self.logger.debug("[%s]: Checking changes of "
                        % self.fileName
                        + "CSV users file.")

                    newHash = self._createHash(self.CSVUsersFile)
                    self.CSVUsersLastCheck = int(time.time())

                    # Reload CSV users file if it has changed.
                    if self.CSVUsersHash != newHash:

                        self.logger.info("[%s]: CSV users file changed."
                            % self.fileName)

                        self.CSVUsersHash = newHash
                        self.userBackend.readUserdata()

                        # Close connections to clients which usernames
                        # are no longer valid.
                        self._syncUsernamesAndConnections()

                        # Synchronize usernames that are no longer valid
                        # with our database.
                        if self._syncUsernamesAndDatabase():
                            # Wake up manager update executer if
                            # we removed a node.
                            self.managerUpdateExecuter.forceStatusUpdate = True
                            self.managerUpdateExecuter.managerUpdateEvent.set()