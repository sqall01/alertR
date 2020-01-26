#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import os
import time
import json
from update import VerifiedHTTPSConnection
from internalSensors import VersionInformerSensor
from localObjects import SensorDataType


# Class that represents the internal sensor that
# is responsible to trigger sensor alerts if a
# node has a new version available in the update repository.
class VersionInformerSensor(_InternalSensor):

    def __init__(self):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.NONE


# this class handles the version information for a given instance
class VersionInformation:

    def __init__(self, host, port, serverPath, caFile, instance,
        repoInstanceLocation, logger):

        # used for logging
        self.fileName = os.path.basename(__file__)
        self.logger = logger

        # the updater object is not thread safe
        self.versionInformerLock = threading.Semaphore(1)

        # get global configured data
        self.instance = instance

        # set update server configuration
        self.host = host
        self.port = port
        self.serverPath = serverPath
        self.caFile = caFile
        self.repoInstanceLocation = repoInstanceLocation

        # needed to keep track of the newest version
        self.newestVersion = -1.0
        self.newestRev = -1
        

    # internal function that acquires the lock
    def _acquireLock(self):
        self.logger.debug("[%s]: Acquire lock." % self.fileName)
        self.versionInformerLock.acquire()


    # internal function that releases the lock
    def _releaseLock(self):
        self.logger.debug("[%s]: Release lock." % self.fileName)
        self.versionInformerLock.release()


    # internal function that gets the newest version information from the
    # online repository
    #
    # return True or False
    def _getNewestVersionInformation(self):

        conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)

        # get version string from the server
        versionString = ""
        try:

            conn.request("GET", self.serverPath + "/"
                + self.repoInstanceLocation + "/instanceInfo.json")
            response = conn.getresponse()

            # check if server responded correctly
            if response.status == 200:
                versionString = response.read()

            else:
                raise ValueError("Server response code not 200 (was %d)."
                    % response.status)

        except Exception as e:
            self.logger.exception("[%s]: Getting version information "
                % self.fileName
                + "for instance '%s' failed."
                % self.instance)

            return False


        # parse version information string
        try:
            jsonData = json.loads(versionString)

            version = float(jsonData["version"])
            rev = int(jsonData["rev"])

        except Exception as e:
            self.logger.exception("[%s]: Parsing version information "
                % self.fileName
                + "for instance '%s' failed."
                % self.instance)

            return False

        self.logger.debug("[%s]: Newest version information for instance "
            % self.fileName
            + "'%s': %.3f-%d."
            % (self.instance, version, rev))

        # check if the version on the server is newer than the used one
        # => update information
        if (version > self.newestVersion or
            (rev > self.newestRev and version == self.newestVersion)):

            # update newest known version information
            self.newestVersion = version
            self.newestRev = rev

        return True


    # function that gets the newest version information from the
    # online repository
    def getNewestVersionInformation(self):

        self._acquireLock()

        result = self._getNewestVersionInformation()

        self._releaseLock()

        return result


# this class checks in specific intervals for new versions of all available
# instances in the given repository
class VersionInformer(threading.Thread):

    def __init__(self, host, port, serverPath, caFile, interval, globalData):
        threading.Thread.__init__(self)

        # used for logging
        self.fileName = os.path.basename(__file__)

        # set update server configuration
        self.host = host
        self.port = port
        self.serverPath = serverPath
        self.caFile = caFile

        # get global configured data
        self.globalData = globalData
        self.logger = self.globalData.logger
        self.storage = self.globalData.storage
        self.internalSensors = self.globalData.internalSensors
        self.sensorAlertExecuter = self.globalData.sensorAlertExecuter
        self.updateMaxFails = self.globalData.updateMaxFails

        # set interval for update checking
        self.checkInterval = interval

        self.repoLocations = dict()
        self.repoVersions = dict()

        # Get activated internal sensors.
        self.versionInformerSensor = None
        for internalSensor in self.internalSensors:
            if isinstance(internalSensor, VersionInformerSensor):
                self.versionInformerSensor = internalSensor


    def run(self):

        updateFailCount = 0

        while True:

            # If we had problems fetching version information, only wait half
            # the time for the next version fetching.
            if updateFailCount > 0:
                time.sleep(self.checkInterval / 2)
            else:
                time.sleep(self.checkInterval)

            # Check if updates failed maximum number of times in a row
            # => log and notify user.
            if updateFailCount >= self.updateMaxFails:

                self.logger.error("[%s]: Update checking failed %d "
                    % (self.fileName, updateFailCount)
                    + "times in a row.")

                if self.versionInformerSensor:

                    # If sensor is in state "normal" change it to
                    # state "triggered".
                    changeState = False
                    if self.versionInformerSensor.state == 0:

                        self.versionInformerSensor.state = 1
                        changeState = True

                        # Change sensor state in database.
                        remoteSensorId = \
                            self.versionInformerSensor.remoteSensorId
                        nodeId = self.versionInformerSensor.nodeId
                        state = self.versionInformerSensor.state
                        if not self.storage.updateSensorState(
                            nodeId, # nodeId
                            [(remoteSensorId, state)], # stateList
                            self.logger): # logger

                            self.logger.error("[%s]: Not able to "
                                % self.fileName
                                + "change sensor state for internal "
                                + "version informer sensor.")

                    # Add sensor alert to database for processing.
                    message = "Update checking failed %d " \
                        %  updateFailCount \
                        + "times in a row."
                    dataJson = json.dumps({"message": message})
                    if self.storage.addSensorAlert(
                        self.versionInformerSensor.nodeId, # nodeId
                        self.versionInformerSensor.sensorId, # sensorId
                        self.versionInformerSensor.state, # state
                        dataJson, # dataJson
                        changeState, # changeState
                        False, # hasLatestData
                        SensorDataType.NONE, # sensorData
                        self.logger): # logger

                        # Manually wake up sensor alert executer to process
                        # sensor alerts immediately.
                        self.sensorAlertExecuter.sensorAlertEvent.set()

                    else:
                        self.logger.error("[%s]: Not able to add "
                            % self.fileName
                            + "sensor alert "
                            + "for internal version informer sensor.")

            processSensorAlerts = False

            self.logger.debug("[%s]: Fetching version information from "
                % self.fileName
                + "'https://%s:%d/%s'."
                % (self.host, self.port, self.serverPath))

            conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)

            # get repository information from the server
            repoInfoString = ""
            try:

                conn.request("GET", self.serverPath + "/repoInfo.json")
                response = conn.getresponse()

                # check if server responded correctly
                if response.status == 200:
                    repoInfoString = response.read()

                else:
                    raise ValueError("Server response code not 200 (was %d)."
                        % response.status)

            except Exception as e:
                self.logger.exception("[%s]: Getting repository information "
                    % self.fileName
                    + "failed.")
                updateFailCount += 1
                continue

            # parse repository information string
            try:
                jsonData = json.loads(repoInfoString)

                if not isinstance(jsonData, dict):
                    raise ValueError("Received repository information is "
                        + "not of type dict.")

                # store the information about the repository instances
                self.repoLocations = dict()
                for instance in jsonData["instances"].keys():
                    self.repoLocations[instance] \
                        = jsonData["instances"][instance]["location"]


            except Exception as e:
                self.logger.exception("[%s]: Parsing repository information "
                    % self.fileName
                    + "failed.")
                updateFailCount += 1
                continue

            # update the locations of all version information objects 
            # for all instances in the repository
            for repoInstance in self.repoLocations.keys():

                # if instance version information object already exists
                # => only update repository location
                if repoInstance in self.repoVersions.keys():
                    self.repoVersions[repoInstance].repoInstanceLocation \
                        = self.repoLocations[repoInstance]

                # => add version information object for the current instance
                else:
                    verInfoObj = VersionInformation(self.host, self.port,
                        self.serverPath, self.caFile, repoInstance,
                        self.repoLocations[repoInstance], self.logger)

                    self.repoVersions[repoInstance] = verInfoObj

            # check if instances were removed from the repository
            # and remove them
            for repoInstance in self.repoVersions.keys():
                if not repoInstance in self.repoLocations.keys():
                    del self.repoVersions[repoInstance]

            # get the version information of all version information objects
            versionUpdateFailed = False
            for repoInstance in self.repoVersions.keys():

                verInfoObj = self.repoVersions[repoInstance]
                if not verInfoObj.getNewestVersionInformation():

                    self.logger.error("[%s]: Getting version information "
                    % self.fileName
                    + "for instance '%s' failed."
                    % verInfoObj.instance)

                    versionUpdateFailed = True

            # If version information fetching of at least one instance failed,
            # skip checking process.
            if versionUpdateFailed:
                updateFailCount += 1
                continue

            updateFailCount = 0

            # Get all nodes managed by the server.
            outdatedNodes = set()
            nodeIds = self.storage.getNodeIds(self.logger)
            for nodeId in nodeIds:
                nodeObj = self.storage.getNodeById(nodeId, self.logger)
                # Since a user can be deleted during runtime, check if
                # the node still existed in the database.
                if nodeObj is None:
                    self.logger.error("[%s]: Could not " % self.fileName
                        + "get node with id %d from database."
                        % nodeId)
                    continue

                hostname = nodeObj.hostname
                username = nodeObj.username
                nodeType = nodeObj.nodeType
                instance = nodeObj.instance
                version = nodeObj.version
                rev = nodeObj.rev

                # Check if instance is managed by update repository.
                if instance in self.repoVersions.keys():
                    verInfoObj = self.repoVersions[instance]
                    newVersion = verInfoObj.newestVersion
                    newRev = verInfoObj.newestRev

                    # Check if update repository holds newer version.
                    hasNewVersion = newVersion > version
                    hasNewRev = (newVersion == version
                        and newRev > rev)

                    if hasNewVersion or hasNewRev:
                        outdatedNodes.add(username)

                        self.logger.warning("[%s] New version for node "
                            % self.fileName
                            + "'%s' with username '%s' on host '%s' available "
                            % (instance, username, hostname)
                            + "(current: %.3f-%d; new: %.3f-%d)."
                            % (version, rev, newVersion, newRev))

                        # If the internal sensor is active trigger a
                        # sensor alert.
                        if self.versionInformerSensor:

                            # If sensor is in state "normal" change it to
                            # state "triggered".
                            changeState = False
                            if self.versionInformerSensor.state == 0:

                                self.versionInformerSensor.state = 1
                                changeState = True

                                # Change sensor state in database.
                                remoteSensorId = \
                                    self.versionInformerSensor.remoteSensorId
                                nodeId = self.versionInformerSensor.nodeId
                                state = self.versionInformerSensor.state
                                if not self.storage.updateSensorState(
                                    nodeId, # nodeId
                                    [(remoteSensorId, state)], # stateList
                                    self.logger): # logger

                                    self.logger.error("[%s]: Not able to "
                                        % self.fileName
                                        + "change sensor state for internal "
                                        + "version informer sensor.")

                            # Create message for sensor alert.
                            message = "New version for node '%s' with " \
                                % instance \
                                + "username '%s' on host " \
                                % username \
                                + "'%s' available " \
                                % hostname \
                                + "(current: %.3f-%d; " \
                                % (version, rev) \
                                + "new: %.3f-%d)." \
                                % (newVersion, newRev)
                            dataJson = json.dumps({"message": message,
                                                    "hostname": hostname,
                                                    "username": username,
                                                    "instance": instance,
                                                    "nodeType": nodeType,
                                                    "version": version,
                                                    "rev": rev,
                                                    "newVersion": newVersion,
                                                    "newRev": newRev})

                            # Add sensor alert to database for processing.
                            if self.storage.addSensorAlert(
                                self.versionInformerSensor.nodeId, # nodeId
                                self.versionInformerSensor.sensorId, # sensorId
                                self.versionInformerSensor.state, # state
                                dataJson, # dataJson
                                changeState, # changeState
                                False, # hasLatestData
                                SensorDataType.NONE, # sensorData
                                self.logger): # logger

                                processSensorAlerts = True

                            else:
                                self.logger.error("[%s]: Not able to add "
                                    % self.fileName
                                    + "sensor alert "
                                    + "for internal version informer sensor.")

                # Skip instance if not managed by update repository.
                else:
                    self.logger.info("[%s] Instance '%s' not "
                        % (self.fileName, instance)
                        + "in update repository. Skipping version check.")

            # Check if we do not have any nodes that have an old version
            # left and we still have this sensor triggered.
            # => Change state of sensor and send a sensor alert.
            if (not outdatedNodes
                and self.versionInformerSensor is not None
                and self.versionInformerSensor.state == 1):

                self.versionInformerSensor.state = 0
                message = "All nodes have the newest version."
                dataJson = json.dumps({"message": message})

                # Change sensor state in database.
                remoteSensorId = self.versionInformerSensor.remoteSensorId
                nodeId = self.versionInformerSensor.nodeId
                state = self.versionInformerSensor.state
                if not self.storage.updateSensorState(
                    nodeId, # nodeId
                    [(remoteSensorId, state)], # stateList
                    self.logger): # logger

                    self.logger.error("[%s]: Not able to "
                        % self.fileName
                        + "change sensor state for internal "
                        + "version informer sensor.")

                # Add sensor alert to database for processing.
                if self.storage.addSensorAlert(
                    self.versionInformerSensor.nodeId, # nodeId
                    self.versionInformerSensor.sensorId, # sensorId
                    self.versionInformerSensor.state, # state
                    dataJson, # dataJson
                    True, # changeState
                    False, # hasLatestData
                    SensorDataType.NONE, # sensorData
                    self.logger): # logger

                    processSensorAlerts = True

                else:
                    self.logger.error("[%s]: Not able to add sensor alert "
                        % self.fileName
                        + "for internal version informer sensor.")

            # Wake up sensor alert executer to process sensor alerts.
            if processSensorAlerts:
                self.sensorAlertExecuter.sensorAlertEvent.set()
