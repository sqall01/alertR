#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import time
import os
from typing import List, Optional, Set, Tuple
from ..localObjects import Sensor
from ..internalSensors import NodeTimeoutSensor
from ..globalData.globalData import GlobalData


# This class handles all timeouts of nodes, sensors, and so on.
class ConnectionWatchdog(threading.Thread):

    def __init__(self,
                 globalData: GlobalData,
                 connectionTimeout: int):
        threading.Thread.__init__(self)

        # get global configured data
        self.globalData = globalData
        self.logger = self.globalData.logger
        self.storage = self.globalData.storage
        self.managerUpdateExecuter = self.globalData.managerUpdateExecuter
        self.sensorAlertExecuter = self.globalData.sensorAlertExecuter
        self.internalSensors = self.globalData.internalSensors
        self.serverSessions = self.globalData.serverSessions

        # file name of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # Get value for the configured timeout of a session.
        self.connectionTimeout = connectionTimeout
        self.timeoutReminderTime = self.globalData.timeoutReminderTime

        # set exit flag as false
        self.exitFlag = False

        # Flag that indicates if the connection watchdog is initialized.
        self._isInitialized = False

        # The node id of this server instance in the database.
        self.serverNodeId = None

        # Set up needed data structures for node timeouts.
        self._timeoutNodeIds = set()
        self._preTimeoutNodeIds = set()  # type: Set[Tuple[int, int]]
        self.nodeTimeoutSensor = None
        self._lastNodeTimeoutReminder = 0
        self.gracePeriodTimeout = self.globalData.gracePeriodTimeout
        self._nodeTimeoutLock = threading.Lock()

        # Get activated internal sensors.
        for internalSensor in self.internalSensors:
            if isinstance(internalSensor, NodeTimeoutSensor):
                # Use set of node timeout sensor if it is activated.
                self._timeoutNodeIds = internalSensor.get_ptr_timeout_node_ids()
                self.nodeTimeoutSensor = internalSensor

    def _acquireNodeTimeoutLock(self):
        """
        Internal function that acquires the node timeout sensor lock.
        """
        self._nodeTimeoutLock.acquire()

    def _releaseNodeTimeoutLock(self):
        """
        Internal function that releases the node timeout sensor lock.
        """
        self._nodeTimeoutLock.release()

    def _processNewNodeTimeouts(self):
        """
        Internal function that processes new occurred node timeouts and raises alarm.
        """
        # Get all nodes that are longer in the pre-timeout set
        # then the allowed grace period.
        newTimeouts = set()
        currentTime = int(time.time())
        self._acquireNodeTimeoutLock()
        for preTuple in set(self._preTimeoutNodeIds):
            if (currentTime - preTuple[1]) > self.gracePeriodTimeout:
                newTimeouts.add(preTuple[0])
                self._preTimeoutNodeIds.remove(preTuple)
        self._releaseNodeTimeoutLock()

        # Add all nodes to the timeout list that are longer timed-out
        # then the allowed grace period.
        for nodeId in newTimeouts:
            self.addNodeTimeout(nodeId)

        # Check all server sessions if the connection timed out.
        for serverSession in self.serverSessions:

            # Check if client communication object exists.
            if serverSession.clientComm is None:
                continue

            # Check if the time of the data last received lies
            # too far in the past => kill connection.
            utcTimestamp = int(time.time())
            if (utcTimestamp - serverSession.clientComm.lastRecv) >= self.connectionTimeout:
                self.logger.error("[%s]: Connection to client timed out. Closing connection (%s:%d)."
                                  % (self.fileName, serverSession.clientAddress, serverSession.clientPort))

                serverSession.closeConnection()

                nodeId = serverSession.clientComm.nodeId
                if nodeId is None or nodeId in self._timeoutNodeIds:
                    continue

                self.addNodeTimeout(nodeId)

    def _processOldNodeTimeouts(self):
        """
        Internal function that processes old occurred node timeouts and raises alarm when they are no longer timed out.
        """
        # Check all server sessions if a timed out connection reconnected.
        for serverSession in self.serverSessions:

            # Check if client communication object exists.
            if serverSession.clientComm is None:
                continue

            nodeId = serverSession.clientComm.nodeId
            if nodeId is None or nodeId not in self._timeoutNodeIds:
                continue

            self.removeNodeTimeout(nodeId)

    def _processTimeoutReminder(self):
        """
        Internal function that checks if a reminder of a timeout has to be raised.
        """

        # Reset timeout reminder if necessary.
        if not self._timeoutNodeIds and self._lastNodeTimeoutReminder != 0:
            self._lastNodeTimeoutReminder = 0

        # When nodes are still timed out check if a reminder
        # has to be raised.
        elif self._timeoutNodeIds:

            # Check if a node timeout reminder has to be raised.
            utcTimestamp = int(time.time())
            if (utcTimestamp - self._lastNodeTimeoutReminder) >= self.timeoutReminderTime:

                self._lastNodeTimeoutReminder = utcTimestamp

                self.logger.error("[%s]: %d Nodes still timed out."
                                  % (self.fileName, len(self._timeoutNodeIds)))

                for nodeId in set(self._timeoutNodeIds):
                    nodeObj = self.storage.getNodeById(nodeId)
                    # Since a user can be deleted during runtime, check if the
                    # node still existed in the database.
                    if nodeObj is None:
                        self.logger.error("[%s]: Could not get node with id %d from database."
                                          % (self.fileName, nodeId))
                        self.removeNodeTimeout(nodeId)
                        continue
                    self.logger.error("[%s]: Node '%s' with username '%s' on host '%s' still timed out."
                                      % (self.fileName, nodeObj.instance, nodeObj.username, nodeObj.hostname))

                # Raise sensor alert for internal node timeout sensor.
                if self.nodeTimeoutSensor is not None:
                    self.nodeTimeoutSensor.reminder()

    def _syncDbAndConnections(self):
        """
        Internal function that synchronizes actual connected nodes and as connected marked nodes in the database
        (if for some internal error reason they are out of sync).
        """
        sendManagerUpdates = False

        # Get all node ids from database that are connected.
        # Returns a list of node ids.
        nodeIds = self.storage.getAllConnectedNodeIds()
        if nodeIds is None:
            self.logger.error("[%s]: Could not get node ids from database." % self.fileName)

        else:

            # Check if node marked as connected got a connection
            # to the server.
            for nodeId in nodeIds:
                found = False

                # Skip node id of this server instance.
                if nodeId == self.serverNodeId:
                    continue

                # Skip node ids that have an active connection
                # to this server.
                for serverSession in self.serverSessions:

                    # Check if client communication object exists and
                    # client is initialized.
                    if serverSession.clientComm is None or not serverSession.clientComm.clientInitialized:
                        continue

                    if serverSession.clientComm.nodeId == nodeId:
                        found = True
                        break
                if found:
                    continue

                # If no server session was found with the node id
                # => node is not connected to the server.
                self.logger.debug("[%s]: Marking node '%d' as not connected." % (self.fileName, nodeId))

                if not self.storage.markNodeAsNotConnected(nodeId):
                    self.logger.error("[%s]: Could not mark node as not connected in database." % self.fileName)

                sendManagerUpdates = True

            # Check if all connections to the server are marked as connected
            # in the database.
            for serverSession in self.serverSessions:

                # Check if client communication object exists and
                # client is initialized.
                if serverSession.clientComm is None or not serverSession.clientComm.clientInitialized:
                    continue

                nodeId = serverSession.clientComm.nodeId
                if nodeId not in nodeIds:

                    # If server session was found but not marked as connected
                    # in database => mark node as connected in database.
                    self.logger.debug("[%s]: Marking node '%d' as connected." % (self.fileName, nodeId))

                    if not self.storage.markNodeAsConnected(nodeId):
                        self.logger.error("[%s]: Could not mark node as connected in database." % self.fileName)

        # Wake up manager update executer and force to send an update to
        # all managers.
        if sendManagerUpdates:
            self.managerUpdateExecuter.force_status_update()

    def addNodeTimeout(self,
                       nodeId: int):
        """
        Public function that sets a node as "timed out" by its id.
        This function also takes into account if the node is set as "persistent".

        :param nodeId:
        :return:
        """
        self._acquireNodeTimeoutLock()

        # Remove node id from the pre-timeout set if it exists
        # because it is now an official timeout.
        for preTuple in set(self._preTimeoutNodeIds):
            if nodeId == preTuple[0]:
                self._preTimeoutNodeIds.remove(preTuple)
                break

        # Needed to check if a node timeout has occurred when there was
        # no timeout before.
        wasEmpty = True
        if self._timeoutNodeIds:
            wasEmpty = False

        # Only process node timeout if we do not already know about it.
        if nodeId not in self._timeoutNodeIds:

            nodeObj = self.storage.getNodeById(nodeId)
            # Since a user can be deleted during runtime, check if
            # the node still existed in the database.
            if nodeObj is None:
                self.logger.error("[%s]: Could not get node with id %d from database." % (self.fileName, nodeId))
                self.logger.error("[%s]: Node with id %d timed out (not able to determine persistence)."
                                  % (self.fileName, nodeId))
                self._releaseNodeTimeoutLock()
                return

            # Check if client is not persistent and therefore
            # allowed to timeout or disconnect.
            # => Ignore timeout/disconnect.
            if nodeObj.persistent == 0:
                self._releaseNodeTimeoutLock()
                return

            self._timeoutNodeIds.add(nodeId)

            self.logger.critical("[%s]: Node '%s' with username '%s' on host '%s' timed out."
                                 % (self.fileName, nodeObj.instance, nodeObj.username, nodeObj.hostname))

            # Trigger a sensor alert if we have the internal sensor activated.
            if self.nodeTimeoutSensor is not None:
                self.nodeTimeoutSensor.node_timed_out(nodeObj)

        # Start node timeout reminder timer when the node timeout list
        # was empty before.
        if wasEmpty and self._timeoutNodeIds:
            utcTimestamp = int(time.time())
            self._lastNodeTimeoutReminder = utcTimestamp

        self._releaseNodeTimeoutLock()

    def addNodePreTimeout(self,
                          nodeId: int):
        """
        Public function that sets a node on the pre-timeout list.
        The pre-timeout list exists to cope with short disconnects because of
        network transmission errors that are almost instantly resolved by a reconnect of the client.
        This function also takes into account if the node is set as "persistent".

        :param nodeId:
        :return:
        """
        self._acquireNodeTimeoutLock()

        # Ignore node if it is already timed out.
        if nodeId in self._timeoutNodeIds:
            self._releaseNodeTimeoutLock()
            return

        # Check if node already in pre-timeout set => ignore it.
        found = False
        for preTuple in self._preTimeoutNodeIds:
            if nodeId == preTuple[0]:
                found = True
                break
        if found:
            self._releaseNodeTimeoutLock()
            return

        nodeObj = self.storage.getNodeById(nodeId)
        # Since a user can be deleted during runtime, check if
        # the node still existed in the database.
        if nodeObj is None:
            self.logger.error("[%s]: Could not get node with id %d from database." % (self.fileName, nodeId))
            self.logger.error("[%s]: Node with id %d pre-timed out (not able to determine persistence)."
                              % (self.fileName, nodeId))
            self._releaseNodeTimeoutLock()
            return

        # Check if client is not persistent and therefore
        # allowed to timeout or disconnect.
        # => Ignore timeout/disconnect.
        if nodeObj.persistent == 0:
            self._releaseNodeTimeoutLock()
            return

        instance = nodeObj.instance
        username = nodeObj.username
        hostname = nodeObj.hostname
        self.logger.debug("[%s]: Adding node '%s' with username '%s' on host '%s' to pre-timeout set."
                          % (self.fileName, instance, username, hostname))

        # Add node id with time that timeout occurred into pre-timeout set.
        utcTimestamp = int(time.time())
        self._preTimeoutNodeIds.add((nodeId, utcTimestamp))

        self._releaseNodeTimeoutLock()

    def isInitialized(self) -> bool:
        """
        Returns if the connection watchdog is initialized.

        :return:
        """
        return self._isInitialized

    def removeNodeTimeout(self,
                          nodeId: int):
        """
        Public function that clears a node from "timed out" by its id.
        It also removes the node from the pre-timeout set.

        :param nodeId:
        :return:
        """
        self._acquireNodeTimeoutLock()

        # Remove node id from the pre-timeout set if it exists.
        # If it exists it is also not in the timeout set.
        for preTuple in set(self._preTimeoutNodeIds):
            if nodeId == preTuple[0]:
                self.logger.debug("[%s]: Removing node with id %d from pre-timeout set."
                                  % (self.fileName, nodeId))
                self._preTimeoutNodeIds.remove(preTuple)
                self._releaseNodeTimeoutLock()
                return

        # Only process node timeout if we know about it.
        if nodeId in self._timeoutNodeIds:
            self._timeoutNodeIds.remove(nodeId)

            nodeObj = self.storage.getNodeById(nodeId)
            # Since a user can be deleted during runtime, check if
            # the node still existed in the database.
            if nodeObj is None:
                self.logger.error("[%s]: Could not get node with id %d from database." % (self.fileName, nodeId))
                self.logger.error("[%s]: Removing node with id %d from timed out set." % (self.fileName, nodeId))
                self._releaseNodeTimeoutLock()
                return

            self.logger.error("[%s]: Node '%s' with username '%s' on host '%s' reconnected."
                              % (self.fileName, nodeObj.instance, nodeObj.username, nodeObj.hostname))

            # Trigger a sensor alert if we have the internal sensor activated.
            if self.nodeTimeoutSensor is not None:
                self.nodeTimeoutSensor.node_back(nodeObj)

        # Reset node timeout reminder timer when the sensor timeout list is empty.
        if not self._timeoutNodeIds:
            self._lastNodeTimeoutReminder = 0.0

        self._releaseNodeTimeoutLock()

    def run(self):

        uniqueID = self.storage.getUniqueID()
        self.serverNodeId = self.storage.getNodeId(uniqueID)

        # Since we just started no node is connected to this server instance,
        # therefore mark all nodes as disconnected.
        connectedNodes = self.storage.getAllConnectedNodeIds()
        for nodeId in connectedNodes:
            if nodeId == self.serverNodeId:
                continue
            self.storage.markNodeAsNotConnected(nodeId)

        # Add all persistent nodes to the pre-timeout set in order to give
        # them time to reconnect to the server.
        persistentNodes = self.storage.getAllPersistentNodeIds()
        for nodeId in persistentNodes:
            if nodeId == self.serverNodeId:
                continue
            self.addNodePreTimeout(nodeId)

        # Set connection watchdog as initialized so that the server can
        # start and accept connections.
        self._isInitialized = True

        while True:
            # wait 5 seconds before checking time of last received data
            for i in range(5):
                if self.exitFlag:
                    self.logger.info("[%s]: Exiting ConnectionWatchdog." % self.fileName)
                    return
                time.sleep(1)

            # Synchronize view on connected nodes (actual connected nodes
            # and database)
            self._syncDbAndConnections()

            # Check all server sessions if the connection timed out.
            self._processNewNodeTimeouts()

            # Process nodes that timed out but reconnected.
            self._processOldNodeTimeouts()

            # Process reminder of timeouts.
            self._processTimeoutReminder()

    def exit(self):
        """
        sets the exit flag to shut down the thread
        """
        self.exitFlag = True
