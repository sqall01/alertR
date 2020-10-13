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
from typing import List, Optional, Tuple
from ..server import AsynchronousSender
from ..localObjects import SensorAlert, AlertLevel
from ..globalData import GlobalData







class SensorAlertState:

    def __init__(self,
                 sensor_alert: SensorAlert,
                 alert_levels: List[AlertLevel]):

        self._init_sensor_alert = sensor_alert

        # Consider all alert levels of the sensor alert initially as suitable.
        self._suitable_alert_levels = list()  # type: List[AlertLevel]
        for alert_level in alert_levels:
            if alert_level.level in sensor_alert.alertLevels:
                self._suitable_alert_levels.append(alert_level)

        # TODO create state such as alert delay, instrumentation, ...

    @property
    def suitable_alert_levels(self) -> List[AlertLevel]:
        """
        Returns a copy of the triggered alert levels
        :return:
        """
        return list(self._suitable_alert_levels)

    @suitable_alert_levels.setter
    def suitable_alert_levels(self, value: List[AlertLevel]):
        self._suitable_alert_levels = value

    @property
    def sensor_alert(self) -> SensorAlert:
        # TODO: decide if we are using the initial or instrumented sensor alert
        return self._init_sensor_alert





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
        self._manager_update_executer = self.globalData.managerUpdateExecuter
        self.storage = self.globalData.storage
        self._alert_levels = self.globalData.alertLevels  # type: List[AlertLevel]
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









        self._sensor_alert_states = list()  # type: List[SensorAlertState]








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
            for configured_alert_level in self._alert_levels:
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














    def _filter_sensor_alerts(self, sensor_alert_states: List[SensorAlertState]) -> Tuple[List[SensorAlertState],
                                                                                          List[SensorAlertState]]:
        """
        Filters sensor alert states and removes each sensor alert that can no longer satisfy trigger conditions.
        :param sensor_alert_states:
        :return: a new list of sensor alert states to further process and a list of sensor alert states that satisfy
        no longer a trigger condition
        """
        new_sensor_alert_states = list()
        removed_sensor_alert_states = list()
        for sensor_alert_state in sensor_alert_states:

            # Remove sensor alerts that do not have any suitable alert level.
            if not sensor_alert_state.suitable_alert_levels:
                removed_sensor_alert_states.append(sensor_alert_state)
                continue

            new_sensor_alert_states.append(sensor_alert_state)

        return new_sensor_alert_states, removed_sensor_alert_states

    def _update_suitable_alert_levels(self, sensor_alert_states: List[SensorAlertState]):
        """
        Updates the suitable alert levels of each sensor alert state.
        :param sensor_alert_states:
        """
        is_alert_system_active = self.storage.isAlertSystemActive()

        for sensor_alert_state in sensor_alert_states:

            # Create a list of currently suitable alert levels.
            suitable_alert_levels = list()
            for alert_level in sensor_alert_state.suitable_alert_levels:

                if alert_level.triggerAlways or is_alert_system_active:

                    # If the alert level does not trigger a sensor alert message for a "triggered" state
                    # while the sensor alert is for the "triggered" state, skip it.
                    if not alert_level.triggerAlertTriggered and sensor_alert_state.sensor_alert.state == 1:
                        continue

                    # If the alert level does not trigger a sensor alert message for a "normal" state
                    # while the sensor alert is for the "normal" state, skip it.
                    if not alert_level.triggerAlertNormal and sensor_alert_state.sensor_alert.state == 0:
                        continue

                    suitable_alert_levels.append(alert_level)

            sensor_alert_state.suitable_alert_levels = suitable_alert_levels

    def run(self):
        """
        This function starts the endless loop of the alert executer thread.
        """
        while True:

            # check if thread should terminate
            if self.exit_flag:
                return

            # check if manager update executer object reference does exist
            # => if not get it from the global data
            if self._manager_update_executer is None:
                self._manager_update_executer = self.globalData.managerUpdateExecuter

            # Apply a processing state to each sensor alert from the database.
            sensor_alert_list = self.storage.getSensorAlerts()
            for sensor_alert in sensor_alert_list:

                # Delete sensor alert from the database.
                if not self.storage.deleteSensorAlert(sensor_alert.sensorAlertId):
                    self.logger.error("[%s]: Not able to delete sensor alert with id '%d' from database."
                                      % (self.log_tag, sensor_alert.sensorAlertId))
                    continue

                sensor_alert_state = SensorAlertState(sensor_alert, self._alert_levels)
                self._sensor_alert_states.append(sensor_alert_state)

            # Wait if we do not have any sensor alerts to process.
            if not self._sensor_alert_states:
                self.sensorAlertEvent.wait()
                self.sensorAlertEvent.clear()
                continue

            self._update_suitable_alert_levels(self._sensor_alert_states)

            self._sensor_alert_states, dropped_sensor_alert_states = \
                self._filter_sensor_alerts(self._sensor_alert_states)




            # TODO replace process_sensor_alerts()
            # Process sensor alerts that we have to handle.
            self._process_sensor_alerts()





            # TODO the following is new code
            # Add data and state of sensor alert to the queue for state changes of the manager update executer
            # if received sensor alert does change state or data.
            for sensor_alert_state in dropped_sensor_alert_states:
                self.logger.info("[%s]: Sensor Alert '%s' does not satisfy any trigger condition."
                                 % (self.log_tag, sensor_alert_state.sensor_alert.description))

                if self._manager_update_executer is not None:
                    if sensor_alert_state.sensor_alert.hasLatestData or sensor_alert_state.sensor_alert.changeState:

                        # Returns a sensor data object or None.
                        sensor_data_obj = self.storage.getSensorData(sensor_alert_state.sensor_alert.sensorId)

                        manager_state_tuple = (sensor_alert_state.sensor_alert.sensorId,
                                               sensor_alert_state.sensor_alert.state,
                                               sensor_data_obj)
                        self._manager_update_executer.queueStateChange.append(manager_state_tuple)

            # Wake up manager update executer to transmit the state change
            if dropped_sensor_alert_states and self._manager_update_executer is not None:
                self._manager_update_executer.managerUpdateEvent.set()

            time.sleep(0.5)

    def exit(self):
        """
        sets the exit flag to shut down the thread
        """
        self.exit_flag = True
