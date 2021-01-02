#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import os
import time
import json
from typing import Optional
from ..update import Updater
from .core import _InternalSensor
from ..localObjects import SensorDataType
from ..globalData import GlobalData


# This class handles the version information for a given instance.
class VersionInformation:

    def __init__(self,
                 instance: str,
                 url: str,
                 global_data: GlobalData):

        # the updater object is not thread safe
        self._lock = threading.Semaphore(1)

        # used for logging
        self.log_tag = os.path.basename(__file__)

        # get global configured data
        self._instance = instance
        self.url = url
        self.logger = global_data.logger

        # Needed to keep track of the newest version.
        self._version = -1.0
        self._rev = -1

        self.updater = Updater(url, global_data, None, retrieveInfo=False)
        self.updater.setInstance(self._instance, retrieveInfo=False)

    @property
    def instance(self):
        return self._instance

    @property
    def rev(self):
        with self._lock:
            return self._rev

    @property
    def version(self):
        with self._lock:
            return self._version

    def update_version(self) -> bool:
        """
        Updates version information for the given instance.

        :return: Success or Failure
        """
        try:
            instance_info = self.updater.getInstanceInformation()
        except Exception as e:
            self.logger.exception("[%s]: Getting instance information for instance '%s' failed."
                                  % (self.log_tag, self.instance))
            return False

        with self._lock:
            self._version = float(instance_info["version"])
            self._rev = int(instance_info["rev"])

        return True


# Class that represents the internal sensor that
# is responsible to trigger sensor alerts if a
# node has a new version available in the update repository.
class VersionInformerSensor(_InternalSensor):

    def __init__(self,
                 global_data: GlobalData):
        _InternalSensor.__init__(self)

        self.dataType = SensorDataType.NONE

        # used for logging
        self.fileName = os.path.basename(__file__)

        # Get global configured data.
        self.global_data = global_data
        self.logger = self.global_data.logger
        self.update_max_fails = self.global_data.updateMaxFails
        self.sensor_alert_executer = None  # Not available in global data during configuration, set in initialize()
        self.storage = None  # Not available in global data during configuration, set in initialize()

        # set interval for update checking
        self.check_interval = None  # type: Optional[int]

        self.repo_url = None  # type: Optional[str]

        self.repo_instances = list()
        self.repo_versions = dict()

    def _updater(self):

        update_fail_count = 0

        while True:

            # If we had problems fetching version information, only wait half
            # the time for the next version fetching.
            if update_fail_count > 0:
                time.sleep(self.check_interval / 2)
            else:
                time.sleep(self.check_interval)

            # Check if updates failed maximum number of times in a row
            # => log and notify user.
            if update_fail_count >= self.update_max_fails:

                self.logger.error("[%s]: Update checking failed %d times in a row."
                                  % (self.fileName, update_fail_count))

                # If sensor is in state "normal" change it to
                # state "triggered".
                change_state = False
                if self.state == 0:

                    self.state = 1
                    change_state = True

                    # Change sensor state in database.
                    if not self.storage.updateSensorState(self.nodeId,  # nodeId
                                                          [(self.remoteSensorId, self.state)],  # stateList
                                                          self.logger):  # logger
                        self.logger.error("[%s]: Not able to change sensor state for internal version informer sensor."
                                          % self.fileName)

                # Add sensor alert to database for processing.
                message = "Update checking failed %d times in a row." % update_fail_count
                data_json = json.dumps({"message": message})
                if self.storage.addSensorAlert(self.nodeId,  # nodeId
                                               self.sensorId,  # sensorId
                                               self.state,  # state
                                               data_json,  # dataJson
                                               change_state,  # changeState
                                               False,  # hasLatestData
                                               SensorDataType.NONE,  # sensorData
                                               self.logger):  # logger

                    # Manually wake up sensor alert executer to process
                    # sensor alerts immediately.
                    self.sensor_alert_executer.sensorAlertEvent.set()

                else:
                    self.logger.error("[%s]: Not able to add sensor alert for internal version informer sensor."
                                      % self.fileName)

            process_sensor_alerts = False

            self.logger.debug("[%s]: Fetching version information from '%s'." % (self.fileName, self.repo_url))

            # Get repository information from the server.
            updater_obj = Updater(self.repo_url,
                                  self.global_data,
                                  None,
                                  retrieveInfo=False)
            try:
                repo_info = updater_obj.getRepositoryInformation()

                # Store the information about the repository instances
                self.repo_instances = list(repo_info["instances"].keys())

            except Exception as e:
                self.logger.exception("[%s]: Gathering repository information failed." % self.fileName)
                update_fail_count += 1
                continue

            # Create for each instance a version information object (if it does not exist yet).
            for repo_instance in self.repo_instances:
                if repo_instance not in self.repo_versions.keys():
                    ver_info_obj = VersionInformation(repo_instance, self.repo_url, self.global_data)
                    self.repo_versions[repo_instance] = ver_info_obj

            # Check if instances were removed from the repository and remove them.
            for repo_instance in self.repo_versions.keys():
                if repo_instance not in self.repo_instances:
                    del self.repo_versions[repo_instance]

            # Get the version information of all version information objects.
            version_update_failed = False
            for repo_instance in self.repo_versions.keys():

                ver_info_obj = self.repo_versions[repo_instance]
                if not ver_info_obj.update_version():
                    self.logger.error("[%s]: Getting version information for instance '%s' failed."
                                      % (self.fileName, ver_info_obj.instance))
                    version_update_failed = True

            # If version information fetching of at least one instance failed, skip checking process.
            if version_update_failed:
                update_fail_count += 1
                continue

            update_fail_count = 0

            # Get all nodes managed by the server.
            outdated_nodes = set()
            nodeIds = self.storage.getNodeIds(self.logger)
            for nodeId in nodeIds:
                nodeObj = self.storage.getNodeById(nodeId, self.logger)
                # Since a user can be deleted during runtime, check if
                # the node still existed in the database.
                if nodeObj is None:
                    self.logger.error("[%s]: Could not get node with id %d from database." % (self.fileName, nodeId))
                    continue

                hostname = nodeObj.hostname
                username = nodeObj.username
                nodeType = nodeObj.nodeType
                instance = nodeObj.instance
                curr_version = nodeObj.version
                curr_rev = nodeObj.rev

                # Check if instance is managed by update repository.
                if instance in self.repo_versions.keys():
                    ver_info_obj = self.repo_versions[instance]
                    new_version = ver_info_obj.version
                    new_rev = ver_info_obj.rev

                    # Check if update repository holds newer version.
                    hasNewVersion = new_version > curr_version
                    hasNewRev = (new_version == curr_version and new_rev > curr_rev)

                    if hasNewVersion or hasNewRev:
                        outdated_nodes.add(username)

                        self.logger.warning("[%s] New version for node '%s' with username '%s' on host '%s' available "
                                            % (self.fileName, instance, username, hostname)
                                            + "(current: %.3f-%d; new: %.3f-%d)."
                                            % (curr_version, curr_rev, new_version, new_rev))

                        # If sensor is in state "normal" change it to
                        # state "triggered".
                        change_state = False
                        if self.state == 0:

                            self.state = 1
                            change_state = True

                            # Change sensor state in database.
                            if not self.storage.updateSensorState(self.nodeId,  # nodeId
                                                                  [(self.remoteSensorId, self.state)],  # stateList
                                                                  self.logger):  # logger
                                self.logger.error("[%s]: Not able to change sensor state for internal "
                                                  % self.fileName
                                                  + "version informer sensor.")

                        # Create message for sensor alert.
                        message = "New version for node '%s' with username '%s' on host '%s' available " \
                                  % (instance, username, hostname)  \
                                  + "(current: %.3f-%d; new: %.3f-%d)." \
                                  % (curr_version, curr_rev, new_version, new_rev)
                        data_json = json.dumps({"message": message,
                                                "hostname": hostname,
                                                "username": username,
                                                "instance": instance,
                                                "nodeType": nodeType,
                                                "version": curr_version,
                                                "rev": curr_rev,
                                                "newVersion": new_version,
                                                "newRev": new_rev})

                        # Add sensor alert to database for processing.
                        if self.storage.addSensorAlert(self.nodeId,  # nodeId
                                                       self.sensorId,  # sensorId
                                                       self.state,  # state
                                                       data_json,  # dataJson
                                                       change_state,  # changeState
                                                       False,  # hasLatestData
                                                       SensorDataType.NONE,  # sensorData
                                                       self.logger):  # logger
                            process_sensor_alerts = True

                        else:
                            self.logger.error("[%s]: Not able to add sensor alert for internal version informer sensor."
                                              % self.fileName)

                # Skip instance if not managed by update repository.
                else:
                    self.logger.info("[%s] Instance '%s' not in update repository. Skipping version check."
                                     % (self.fileName, instance))

            # Check if we do not have any nodes that have an old version
            # left and we still have this sensor triggered.
            # => Change state of sensor and send a sensor alert.
            if not outdated_nodes and self.state == 1:

                self.state = 0
                message = "All nodes have the newest version."
                data_json = json.dumps({"message": message})

                # Change sensor state in database.
                if not self.storage.updateSensorState(self.nodeId,  # nodeId
                                                      [(self.remoteSensorId, self.state)],  # stateList
                                                      self.logger):  # logger
                    self.logger.error("[%s]: Not able to change sensor state for internal version informer sensor."
                                      % self.fileName)

                # Add sensor alert to database for processing.
                if self.storage.addSensorAlert(self.nodeId,  # nodeId
                                               self.sensorId,  # sensorId
                                               self.state,  # state
                                               data_json,  # dataJson
                                               True,  # changeState
                                               False,  # hasLatestData
                                               SensorDataType.NONE,  # sensorData
                                               self.logger):  # logger
                    process_sensor_alerts = True

                else:
                    self.logger.error("[%s]: Not able to add sensor alert for internal version informer sensor."
                                      % self.fileName)

            # Wake up sensor alert executer to process sensor alerts.
            if process_sensor_alerts:
                self.sensor_alert_executer.sensorAlertEvent.set()

    def initialize(self):

        if self.sensor_alert_executer is None:
            self.sensor_alert_executer = self.global_data.sensorAlertExecuter
        if self.storage is None:
            self.storage = self.global_data.storage

        thread = threading.Thread(target=self._updater)
        thread.daemon = True
        thread.start()
