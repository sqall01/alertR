#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import time
import os
import json
from typing import List, Optional
from ..localObjects import SensorDataType, Sensor
from ..globalData import GlobalData
from ..internalSensors import NodeTimeoutSensor, SensorTimeoutSensor


# TODO move internal sensor logic to sensors corresponding class


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

        # Set up needed data structures for sensor timeouts.
        self.timeoutSensorIds = set()
        self.sensorTimeoutSensor = None
        self.lastSensorTimeoutReminder = 0.0

        # Set up needed data structures for node timeouts.
        self._timeoutNodeIds = set()
        self._preTimeoutNodeIds = set()
        self.nodeTimeoutSensor = None
        self._lastNodeTimeoutReminder = 0.0
        self.gracePeriodTimeout = self.globalData.gracePeriodTimeout
        self._nodeTimeoutLock = threading.Lock()

        # Get activated internal sensors.
        for internalSensor in self.internalSensors:
            if isinstance(internalSensor, SensorTimeoutSensor):
                # Use set of sensor timeout sensor if it is activated.
                self.timeoutSensorIds = internalSensor.timeoutSensorIds
                self.sensorTimeoutSensor = internalSensor
            elif isinstance(internalSensor, NodeTimeoutSensor):
                # Use set of node timeout sensor if it is activated.
                self._timeoutNodeIds = internalSensor._timeoutNodeIds
                self.nodeTimeoutSensor = internalSensor

    def _acquireNodeTimeoutLock(self):
        """
        Internal function that acquires the node timeout sensor lock.
        """
        self.logger.debug("[%s]: Acquire node timeout sensor lock." % self.fileName)
        self._nodeTimeoutLock.acquire()

    def _releaseNodeTimeoutLock(self):
        """
        Internal function that releases the node timeout sensor lock.
        """
        self.logger.debug("[%s]: Release node timeout sensor lock." % self.fileName)
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

    def _processNewSensorTimeouts(self,
                                  sensorsTimeoutList: Optional[List[Sensor]]):
        """
        Internal function that processes new occurred sensor timeouts and raises alarm.

        :param sensorsTimeoutList:
        """
        if sensorsTimeoutList is None:
            return

        processSensorAlerts = False

        # Needed to check if a sensor timeout has occurred when there was
        # no timeout before.
        wasEmpty = True
        if self.timeoutSensorIds:
            wasEmpty = False

        # Generate an alert for every timed out sensor
        # (self.logger + internal "sensor timeout" sensor).
        for sensorObj in sensorsTimeoutList:
            sensorId = sensorObj.sensorId
            nodeId = sensorObj.nodeId
            nodeObj = self.storage.getNodeById(nodeId)
            # Since a user can be deleted during runtime, check if the
            # node still existed in the database.
            if nodeObj is None:
                self.logger.error("[%s]: Could not get node with id %d from database." % (self.fileName, nodeId))
                continue

            hostname = nodeObj.hostname
            username = nodeObj.username
            nodeType = nodeObj.nodeType
            instance = nodeObj.instance
            lastStateUpdated = sensorObj.lastStateUpdated
            description = sensorObj.description
            if hostname is None:
                self.logger.error("[%s]: Could not get hostname for node from database." % self.fileName)
                self.timeoutSensorIds.add(sensorId)
                continue

            self.logger.critical("[%s]: Sensor with description '%s' from host '%s' timed out. "
                                 % (self.fileName, description, hostname)
                                 + "Last state received at %s."
                                 % time.strftime("%D %H:%M:%S", time.localtime(lastStateUpdated)))

            # Check if sensor time out occurred for the first time
            # and internal sensor is activated.
            # => Trigger a sensor alert.
            if sensorId not in self.timeoutSensorIds and self.sensorTimeoutSensor is not None:

                    # If internal sensor is in state "normal", change the
                    # state to "triggered" with the raised sensor alert.
                    changeState = False
                    if self.sensorTimeoutSensor.state == 0:

                        self.sensorTimeoutSensor.state = 1
                        changeState = True

                        # Change sensor state in database.
                        if not self.storage.updateSensorState(self.sensorTimeoutSensor.nodeId,  # nodeId
                                                              [(self.sensorTimeoutSensor.remoteSensorId,
                                                               self.sensorTimeoutSensor.state)],  # stateList
                                                              self.logger):  # logger
                            self.logger.error("[%s]: Not able to change sensor state for internal sensor "
                                              % self.fileName
                                              + "timeout sensor.")

                    # Create message for sensor alert.
                    message = "Sensor '%s' on host '%s' timed out." % (description, hostname)
                    dataJson = json.dumps({"message": message,
                                           "description": description,
                                           "hostname": hostname,
                                           "username": username,
                                           "instance": instance,
                                           "nodeType": nodeType})

                    # Add sensor alert to database for processing.
                    if self.storage.addSensorAlert(self.sensorTimeoutSensor.nodeId,  # nodeId
                                                   self.sensorTimeoutSensor.sensorId,  # sensorId
                                                   1,  # state
                                                   dataJson,  # dataJson
                                                   changeState,  # changeState
                                                   False,  # hasLatestData
                                                   SensorDataType.NONE,  # sensorData
                                                   self.logger):  # logger
                        processSensorAlerts = True

                    else:
                        self.logger.error("[%s]: Not able to add sensor alert for internal sensor timeout sensor."
                                          % self.fileName)

            self.timeoutSensorIds.add(sensorId)

        # Wake up sensor alert executer to process sensor alerts.
        if processSensorAlerts:
            self.sensorAlertExecuter.sensorAlertEvent.set()

        # Start sensor timeout reminder timer when the sensor timeout list
        # was empty before.
        if wasEmpty and self.timeoutSensorIds:
            utcTimestamp = int(time.time())
            self.lastSensorTimeoutReminder = utcTimestamp

    def _processOldSensorTimeouts(self,
                                  sensorsTimeoutList: Optional[List[Sensor]]):
        """
        Internal function that processes old occurred sensor timeouts
        and raises alarm when they are no longer timed out.

        :param sensorsTimeoutList:
        """
        if sensorsTimeoutList is None:
            return

        processSensorAlerts = False

        # check if a timed out sensor has reconnected and
        # updated its state and generate a notification
        for sensorId in set(self.timeoutSensorIds):

            # Skip if an old timed out sensor is still timed out.
            found = False
            for sensorObj in sensorsTimeoutList:
                if sensorId == sensorObj.sensorId:
                    found = True
                    break
            if found:
                continue

            # Sensor is no longer timed out.
            self.timeoutSensorIds.remove(sensorId)

            sensorObj = self.storage.getSensorById(sensorId)

            # Check if the sensor could be found in the database.
            if sensorObj is None:
                self.logger.error("[%s]: Could not get sensor with id %d from database." % (self.fileName, sensorId))
                continue

            nodeId = sensorObj.nodeId
            nodeObj = self.storage.getNodeById(nodeId)
            # Since a user can be deleted during runtime, check if the
            # node still existed in the database.
            if nodeObj is None:
                self.logger.error("[%s]: Could not get node with id %d from database."
                                  % (self.fileName, nodeId))
                continue

            hostname = nodeObj.hostname
            username = nodeObj.username
            nodeType = nodeObj.nodeType
            instance = nodeObj.instance
            description = sensorObj.description
            lastStateUpdated = sensorObj.lastStateUpdated

            self.logger.critical("[%s]: Sensor with description '%s' from host '%s' has "
                                 % (self.fileName, description, hostname)
                                 + "reconnected. Last state received at %s"
                                 % time.strftime("%D %H:%M:%S", time.localtime(lastStateUpdated)))

            # Check if internal sensor is activated.
            # => Trigger a sensor alert.
            if self.sensorTimeoutSensor is not None:

                # If internal sensor is in state "triggered" and
                # no sensor is timed out at the moment, change the
                # state to "normal" with the raised sensor alert.
                changeState = False
                if self.sensorTimeoutSensor.state == 1 and not self.timeoutSensorIds:
                    self.sensorTimeoutSensor.state = 0
                    changeState = True

                    # Change sensor state in database.
                    if not self.storage.updateSensorState(self.sensorTimeoutSensor.nodeId,  # nodeId
                                                          [(self.sensorTimeoutSensor.remoteSensorId,
                                                           self.sensorTimeoutSensor.state)],  # stateList
                                                          self.logger):  # logger
                        self.logger.error("[%s]: Not able to change sensor state for internal sensor timeout sensor."
                                          % self.fileName)

                # Create message for sensor alert.
                message = "Sensor '%s' on host '%s' reconnected." % (description, hostname)
                dataJson = json.dumps({"message": message,
                                       "description": description,
                                       "hostname": hostname,
                                       "username": username,
                                       "instance": instance,
                                       "nodeType": nodeType})

                if self.storage.addSensorAlert(self.sensorTimeoutSensor.nodeId,  # nodeId
                                               self.sensorTimeoutSensor.sensorId,  # sensorId
                                               0,  # state
                                               dataJson,  # dataJson
                                               changeState,  # changeState
                                               False,  # hasLatestData
                                               SensorDataType.NONE,  # sensorData
                                               self.logger):  # logger
                    processSensorAlerts = True

                else:
                    self.logger.error("[%s]: Not able to add sensor alert for internal sensor timeout sensor."
                                      % self.fileName)

        # Wake up sensor alert executer to process sensor alerts.
        if processSensorAlerts:
            self.sensorAlertExecuter.sensorAlertEvent.set()

        # Reset sensor timeout reminder timer when the sensor timeout list
        # is empty.
        if not self.timeoutSensorIds:
            self.lastSensorTimeoutReminder = 0.0

    def _processTimeoutReminder(self):
        """
        Internal function that checks if a reminder of a timeout has to be raised.
        """
        processSensorAlerts = False

        # Reset timeout reminder if necessary.
        if not self.timeoutSensorIds and self.lastSensorTimeoutReminder != 0.0:
            self.lastSensorTimeoutReminder = 0.0

        # When sensors are still timed out check if a reminder
        # has to be raised.
        elif self.timeoutSensorIds:

            # Check if a sensor timeout reminder has to be raised.
            utcTimestamp = int(time.time())
            if (utcTimestamp - self.lastSensorTimeoutReminder) >= self.timeoutReminderTime:

                self.lastSensorTimeoutReminder = utcTimestamp

                # Raise sensor alert for internal sensor timeout sensor.
                if self.sensorTimeoutSensor is not None:

                    # Create message and sensors field for sensor alert.
                    message = "%d sensor(s) still timed out:" % len(self.timeoutSensorIds)
                    sensorsField = list()
                    for sensorId in set(self.timeoutSensorIds):

                        # Get sensor object.
                        sensorObj = self.storage.getSensorById(sensorId)

                        # Since a user can be deleted during runtime, check if
                        # the node/sensor still existed in the database. Since
                        # the node does not exist anymore, remove the sensor
                        # from the timeout list.
                        if sensorObj is None:
                            self.logger.error("[%s]: Could not get sensor with id %d from database."
                                              % (self.fileName, sensorId))
                            self.timeoutSensorIds.remove(sensorId)
                            continue

                        # Get sensor details.
                        nodeId = sensorObj.nodeId
                        nodeObj = self.storage.getNodeById(nodeId)
                        # Since a user can be deleted during runtime, check if
                        # the node still existed in the database. Since the
                        # node does not exist anymore, remove the sensor
                        # from the timeout list.
                        if nodeObj is None:
                            self.logger.error("[%s]: Could not get node with id %d from database."
                                              % (self.fileName, nodeId))
                            self.timeoutSensorIds.remove(sensorId)
                            continue

                        hostname = nodeObj.hostname
                        username = nodeObj.username
                        nodeType = nodeObj.nodeType
                        instance = nodeObj.instance
                        description = sensorObj.description
                        lastStateUpdated = sensorObj.lastStateUpdated
                        lastStateUpdateStr = time.strftime("%D %H:%M:%S", time.localtime(lastStateUpdated))
                        if hostname is None:
                            self.logger.error("[%s]: Could not get hostname for node from database."
                                              % self.fileName)
                            continue

                        sensorField = {"description": description,
                                       "hostname": hostname,
                                       "username": username,
                                       "instance": instance,
                                       "nodeType": nodeType,
                                       "lastStateUpdated": lastStateUpdated}

                        message += " Host: '%s', Sensor: '%s', Last seen: %s;" \
                                   % (hostname, description, lastStateUpdateStr)

                        sensorsField.append(sensorField)

                    dataJson = json.dumps({"message": message,
                                           "sensors": sensorsField})

                    # Add sensor alert to database for processing.
                    if self.storage.addSensorAlert(self.sensorTimeoutSensor.nodeId,  # nodeId
                                                   self.sensorTimeoutSensor.sensorId,  # sensorId
                                                   1,  # state
                                                   dataJson,  # dataJson
                                                   False,  # changeState
                                                   False,  # hasLatestData
                                                   SensorDataType.NONE,  # sensorData
                                                   self.logger):  # logger
                        processSensorAlerts = True

                    else:
                        self.logger.error("[%s]: Not able to add sensor alert for internal sensor timeout sensor."
                                          % self.fileName)

        # Reset timeout reminder if necessary.
        if not self._timeoutNodeIds and self._lastNodeTimeoutReminder != 0.0:
            self._lastNodeTimeoutReminder = 0.0

        # When nodes are still timed out check if a reminder
        # has to be raised.
        elif self._timeoutNodeIds:

            # Check if a node timeout reminder has to be raised.
            utcTimestamp = int(time.time())
            if (utcTimestamp - self._lastNodeTimeoutReminder) >= self.timeoutReminderTime:

                self._lastNodeTimeoutReminder = utcTimestamp

                # Raise sensor alert for internal node timeout sensor.
                if self.nodeTimeoutSensor is not None:

                    # Create message and nodes field for sensor alert.
                    message = "%d node(s) still timed out:" % len(self._timeoutNodeIds)
                    nodesField = list()
                    for nodeId in set(self._timeoutNodeIds):

                        nodeObj = self.storage.getNodeById(nodeId)
                        # Since a user can be deleted during runtime, check if
                        # the node still existed in the database. Since the
                        # node does not exist anymore, remove the node
                        # from the timeout list.
                        if nodeObj is None:
                            self.logger.error("[%s]: Could not get node with id %d from database."
                                              % (self.fileName, nodeId))
                            self.removeNodeTimeout(nodeId)
                            continue

                        instance = nodeObj.instance
                        username = nodeObj.username
                        nodeType = nodeObj.nodeType
                        hostname = nodeObj.hostname

                        nodeField = {"hostname": hostname,
                                     "username": username,
                                     "instance": instance,
                                     "nodeType": nodeType}

                        message += " Node: '%s, Username: '%s', Hostname: '%s';" \
                                   % (str(instance), str(username), str(hostname))

                        nodesField.append(nodeField)

                    dataJson = json.dumps({"message": message,
                                           "nodes": nodesField})

                    # Add sensor alert to database for processing.
                    if self.storage.addSensorAlert(self.nodeTimeoutSensor.nodeId,  # nodeId
                                                   self.nodeTimeoutSensor.sensorId,  # sensorId
                                                   1,  # state
                                                   dataJson,  # dataJson
                                                   False,  # changeState
                                                   False,  # hasLatestData
                                                   SensorDataType.NONE,  # sensorData
                                                   self.logger):  # logger
                        processSensorAlerts = True

                    else:
                        self.logger.error("[%s]: Not able to add sensor alert for internal node timeout sensor."
                                          % self.fileName)

        # Wake up sensor alert executer to process sensor alerts.
        if processSensorAlerts:
            self.sensorAlertExecuter.sensorAlertEvent.set()

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
            self.managerUpdateExecuter.forceStatusUpdate = True
            self.managerUpdateExecuter.managerUpdateEvent.set()

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

        processSensorAlerts = False

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
            if not nodeObj.persistent:
                self._releaseNodeTimeoutLock()
                return

            instance = nodeObj.instance
            nodeType = nodeObj.nodeType
            username = nodeObj.username
            hostname = nodeObj.hostname

            self._timeoutNodeIds.add(nodeId)

            self.logger.error("[%s]: Node '%s' with username '%s' on host '%s' timed out."
                              % (self.fileName, instance, username, hostname))

            if self.nodeTimeoutSensor is not None:

                # If internal sensor is in state "normal", change the
                # state to "triggered" with the raised sensor alert.
                changeState = False
                if self.nodeTimeoutSensor.state == 0:

                    self.nodeTimeoutSensor.state = 1
                    changeState = True

                    # Change sensor state in database.
                    if not self.storage.updateSensorState(self.nodeTimeoutSensor.nodeId,  # nodeId
                                                          [(self.nodeTimeoutSensor.remoteSensorId,
                                                           self.nodeTimeoutSensor.state)],  # stateList
                                                          self.logger):  # logger

                        self.logger.error("[%s]: Not able to change sensor state for internal node timeout sensor."
                                          % self.fileName)

                # Create message for sensor alert.
                message = "Node '%s' with username '%s' on host '%s' timed out." \
                          % (str(instance), str(username), str(hostname))
                dataJson = json.dumps({"message": message,
                                       "hostname": hostname,
                                       "username": username,
                                       "instance": instance,
                                       "nodeType": nodeType})

                # Add sensor alert to database for processing.
                if self.storage.addSensorAlert(self.nodeTimeoutSensor.nodeId,  # nodeId
                                               self.nodeTimeoutSensor.sensorId,  # sensorId
                                               1,  # state
                                               dataJson,  # dataJson
                                               changeState,  # changeState
                                               False,  # hasLatestData
                                               SensorDataType.NONE,  # sensorData
                                               self.logger):  # logger
                    processSensorAlerts = True

                else:
                    self.logger.error("[%s]: Not able to add sensor alert for internal node timeout sensor."
                                      % self.fileName)

        # Wake up sensor alert executer to process sensor alerts.
        if processSensorAlerts:
            self.sensorAlertExecuter.sensorAlertEvent.set()

        # Start node timeout reminder timer when the sensor timeout list
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
        if not nodeObj.persistent:
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

        processSensorAlerts = False

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

            instance = nodeObj.instance
            nodeType = nodeObj.nodeType
            username = nodeObj.username
            hostname = nodeObj.hostname

            self.logger.error("[%s]: Node '%s' with username '%s' on host '%s' reconnected."
                              % (self.fileName, instance, username, hostname))

            if self.nodeTimeoutSensor is not None:

                # If internal sensor is in state "triggered" and there is no
                # timed out node left, change the
                # state to "normal" with the raised sensor alert.
                changeState = False
                if self.nodeTimeoutSensor.state == 1 and not self._timeoutNodeIds:
                    self.nodeTimeoutSensor.state = 0
                    changeState = True

                    # Change sensor state in database.
                    if not self.storage.updateSensorState(self.nodeTimeoutSensor.nodeId,  # nodeId
                                                          [(self.nodeTimeoutSensor.remoteSensorId,
                                                           self.nodeTimeoutSensor.state)],  # stateList
                                                          self.logger):  # logger
                        self.logger.error("[%s]: Not able to change sensor state for internal node timeout sensor."
                                          % self.fileName)

                # Create message for sensor alert.
                message = "Node '%s' with username '%s' on host '%s' reconnected." \
                          % (str(instance), str(username), str(hostname))
                dataJson = json.dumps({"message": message,
                                       "hostname": hostname,
                                       "username": username,
                                       "instance": instance,
                                       "nodeType": nodeType})

                # Add sensor alert to database for processing.
                if self.storage.addSensorAlert(self.nodeTimeoutSensor.nodeId,  # nodeId
                                               self.nodeTimeoutSensor.sensorId,  # sensorId
                                               0,  # state
                                               dataJson,  # dataJson
                                               changeState,  # changeState
                                               False,  # hasLatestData
                                               SensorDataType.NONE,  # sensorData
                                               self.logger):  # logger
                    processSensorAlerts = True

                else:
                    self.logger.error("[%s]: Not able to add sensor alert for internal node timeout sensor."
                                      % self.fileName)

        # Wake up sensor alert executer to process sensor alerts.
        if processSensorAlerts:
            self.sensorAlertExecuter.sensorAlertEvent.set()

        # Reset node timeout reminder timer when the sensor timeout list
        # is empty.
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

            # Get list of sensor objects that have timed out.
            utcTimestamp = int(time.time())
            sensorsTimeoutList = self.storage.getSensorsUpdatedOlderThan(utcTimestamp
                                                                         - int(1.5 * self.gracePeriodTimeout))

            # Process occurred sensor time outs (and if they newly occurred).
            self._processNewSensorTimeouts(sensorsTimeoutList)

            # Process sensors that timed out but reconnected.
            self._processOldSensorTimeouts(sensorsTimeoutList)

            # Process reminder of timeouts.
            self._processTimeoutReminder()

            # Update time of all internal sensors in order to avoid
            # timeouts of these sensors.
            for internalSensor in self.internalSensors:
                if not self.storage.updateSensorTime(internalSensor.sensorId):
                    self.logger.error("[%s]: Not able to update sensor time for internal sensor with sensor id %d "
                                      % (self.fileName, internalSensor.sensorId)
                                      + "sensors.")

    def exit(self):
        """
        sets the exit flag to shut down the thread
        """
        self.exitFlag = True
