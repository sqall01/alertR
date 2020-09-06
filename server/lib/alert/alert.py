#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import os
import time
from typing import List, Optional
from ..server import AsynchronousSender
from ..localObjects import SensorAlert, AlertLevel
from ..globalData import GlobalData


class SensorAlertToHandle:

    def __init__(self,
                 sensor_alert: SensorAlert,
                 alert_levels: List[AlertLevel]):
        self.sensor_alert = sensor_alert
        self.alert_levels = alert_levels


# this class is woken up if a sensor alert is received
# and executes all necessary steps
class SensorAlertExecuter(threading.Thread):

    def __init__(self,
                 globalData: GlobalData):
        threading.Thread.__init__(self)

        # get global configured data
        self.globalData = globalData
        self.logger = self.globalData.logger
        self.manager_update_executer = self.globalData.managerUpdateExecuter
        self.storage = self.globalData.storage
        self.alert_levels = self.globalData.alertLevels
        self.server_sessions = self.globalData.serverSessions

        # file nme of this file (used for logging)
        self.log_tag = os.path.basename(__file__)

        # create an event that is used to wake this thread up
        # and reacte on sensor alert
        self.sensorAlertEvent = threading.Event()
        self.sensorAlertEvent.clear()

        # set exit flag as false
        self.exit_flag = False

        self.sensor_alerts_to_handle = list()  # type: List[SensorAlertToHandle]

    def _preprocess_sensor_alerts(self,
                                  sensorAlertList: Optional[List[SensorAlert]]):
        """
        Internal function that pre-processes sensor alerts from the database.
        All triggered sensor alerts from the database are filtered and separated
        into "sensor alerts locally handled" and "sensor alerts handled by Rule Engine".

        :param sensorAlertList:
        """
        # get the flag if the system is active or not
        is_alert_system_active = self.storage.isAlertSystemActive()

        # check if sensor alerts from the database
        # have to be handled
        for sensor_alert in sensorAlertList:

            # delete sensor alert from the database
            if not self.storage.deleteSensorAlert(sensor_alert.sensorAlertId):
                self.logger.error("[%s]: Not able to delete sensor alert with id '%d' from database."
                                  % (self.log_tag, sensor_alert.sensorAlertId))
                continue

            # get all alert levels that are triggered
            # because of this sensor alert (used as a pre filter)
            triggered_alert_levels = list()
            for configured_alert_level in self.alert_levels:
                for sensor_alert_level_int in sensor_alert.alertLevels:
                    if configured_alert_level.level == sensor_alert_level_int:
                        # check if alert system is active
                        # or alert level triggers always
                        if is_alert_system_active or configured_alert_level.triggerAlways:

                            # check if the configured alert level
                            # should trigger a sensor alert message
                            # when the sensor goes to state "triggered"
                            # => if not skip configured alert level
                            if not configured_alert_level.triggerAlertTriggered and sensor_alert.state == 1:
                                continue

                            # check if the configured alert level
                            # should trigger a sensor alert message
                            # when the sensor goes to state "normal"
                            # => if not skip configured alert level
                            if not configured_alert_level.triggerAlertNormal and sensor_alert.state == 0:
                                continue

                            # Create a list of sensor alerts to handle.
                            triggered_alert_levels.append(configured_alert_level)

            # check if an alert level to trigger was found
            # if not => just ignore it
            if not triggered_alert_levels:
                self.logger.info("[%s]: No alert level to trigger was found." % self.log_tag)

                # Add sensorId of the sensor alert to the queue for state changes of the manager update executer.
                if self.manager_update_executer is not None:

                    # Returns a sensor data object or None.
                    sensor_data_obj = self.storage.getSensorData(sensor_alert.sensorId)

                    if sensor_data_obj is None:
                        self.logger.error("[%s]: Unable to get sensor data from database. Skipping manager "
                                          % self.log_tag
                                          + "notification.")

                    else:
                        manager_state_tuple = (sensor_alert.sensorId, sensor_alert.state, sensor_data_obj)
                        self.manager_update_executer.queueStateChange.append(manager_state_tuple)

                continue

            # update alert levels to trigger
            else:
                # add sensor alert with alert levels
                # to the list of sensor alerts to handle
                self.sensor_alerts_to_handle.append(SensorAlertToHandle(sensor_alert, triggered_alert_levels))

    def _process_sensor_alerts(self):
        """
        Internal function that processes sensor alerts.
        """
        # get the flag if the system is active or not
        is_alert_system_active = self.storage.isAlertSystemActive()

        # check all sensor alerts to handle if they have to be triggered
        for sensor_alert_to_handle in list(self.sensor_alerts_to_handle):
            sensor_alert = sensor_alert_to_handle.sensor_alert

            # get all alert levels that are triggered
            # because of this sensor alert
            triggered_alert_levels = list()
            for configured_alert_level in self.alert_levels:
                for sensor_alert_level in sensor_alert_to_handle.alert_levels:
                    if configured_alert_level.level == sensor_alert_level.level:
                        # check if alert system is active
                        # or alert level triggers always
                        if is_alert_system_active or configured_alert_level.triggerAlways:
                            triggered_alert_levels.append(configured_alert_level)

            # check if an alert level to trigger remains
            # if not => just remove sensor alert to handle from the list
            if not triggered_alert_levels:
                self.logger.info("[%s]: No alert level to trigger remains." % self.log_tag)
                self.sensor_alerts_to_handle.remove(sensor_alert_to_handle)
                continue

            # Update alert levels to trigger.
            # If the sensor alert has a delay, we have to remove
            # all alert levels that do not trigger anymore.
            else:
                sensor_alert_to_handle.alert_levels = triggered_alert_levels

            # check if sensor alert has triggered
            utc_timestamp = int(time.time())
            if (utc_timestamp - sensor_alert.timeReceived) > sensor_alert.alertDelay:

                # generate integer list of alert levels that have triggered
                # (needed for sensor alert message)
                sensor_alert.triggeredAlertLevels = list()
                for triggeredAlertLevel in triggered_alert_levels:
                    sensor_alert.triggeredAlertLevels.append(triggeredAlertLevel.level)

                # send sensor alert to all manager and alert clients
                for server_session in self.server_sessions:
                    # ignore sessions which do not exist yet
                    # and that are not managers
                    if server_session.clientComm is None:
                        continue
                    if (server_session.clientComm.nodeType != "manager"
                       and server_session.clientComm.nodeType != "alert"):
                        continue
                    if not server_session.clientComm.clientInitialized:
                        continue

                    # Only send a sensor alert to a client that actually
                    # handles a triggered alert level.
                    client_alert_levels = server_session.clientComm.clientAlertLevels
                    at_least_one = any(al.level in client_alert_levels for al in triggered_alert_levels)
                    if not at_least_one:
                        continue

                    # sending sensor alert to manager/alert node
                    # via a thread to not block the sensor alert executer
                    sensor_alert_process = AsynchronousSender(self.globalData, server_session.clientComm)
                    # set thread to daemon
                    # => threads terminates when main thread terminates
                    sensor_alert_process.daemon = True
                    sensor_alert_process.sendSensorAlert = True
                    sensor_alert_process.sensorAlert = sensor_alert

                    self.logger.debug("[%s]: Sending sensor alert to manager/alert (%s:%d)."
                                      % (self.log_tag, server_session.clientComm.clientAddress,
                                         server_session.clientComm.clientPort))
                    sensor_alert_process.start()

                # after sensor alert was triggered
                # => remove sensor alert to handle
                self.sensor_alerts_to_handle.remove(sensor_alert_to_handle)

    def run(self):
        """
        this function starts the endless loop of the alert executer thread
        """
        while True:

            # check if thread should terminate
            if self.exit_flag:
                return

            # check if manager update executer object reference does exist
            # => if not get it from the global data
            if self.manager_update_executer is None:
                self.manager_update_executer = self.globalData.managerUpdateExecuter

            # Get a list of all sensor alert objects.
            sensor_alert_list = self.storage.getSensorAlerts()

            # Check if no sensor alerts are to handle and exist in database.
            if (not self.sensor_alerts_to_handle
               and (sensor_alert_list is None or not sensor_alert_list)):
                self.sensorAlertEvent.wait()
                self.sensorAlertEvent.clear()
                continue

            # Filter and separate sensor alerts from the database.
            self._preprocess_sensor_alerts(sensor_alert_list)

            # wake up manager update executer
            # => state change will be transmitted
            # (because it is in the queue)
            if self.manager_update_executer is not None:
                self.manager_update_executer.managerUpdateEvent.set()

            # when no sensor alerts exist to handle => restart loop
            if not self.sensor_alerts_to_handle:
                continue

            # Process sensor alerts that we have to handle.
            self._process_sensor_alerts()

            time.sleep(0.5)

    def exit(self):
        """
        sets the exit flag to shut down the thread
        """
        self.exit_flag = True
