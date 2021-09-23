#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import threading
import os
import time
from typing import List, Tuple, Optional, Any, Dict
from .instrumentation import Instrumentation, InstrumentationPromise
from ..server import AsynchronousSender
from ..localObjects import SensorAlert, AlertLevel
from ..globalData import GlobalData
from ..internalSensors import AlertLevelInstrumentationErrorSensor


class InstrumentationNotFinished(Exception):
    pass


class InstrumentationNotRun(Exception):
    pass


class InstrumentationNotSuccessful(Exception):
    pass


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

        # Calculate initial time when the sensor alert should be triggered.
        self._time_valid = sensor_alert.timeReceived + sensor_alert.alertDelay

        # State information needed for sensor alert instrumentation.
        self._uses_instrumentation = False
        self._instrumentation_promise = None  # type: Optional[InstrumentationPromise]
        self._instrumentation = None  # type: Optional[Instrumentation]
        self._instrumentation_processed = False

    @property
    def instrumentation(self) -> Instrumentation:
        return self._instrumentation

    @instrumentation.setter
    def instrumentation(self, value: Instrumentation):
        if self._instrumentation is not None:
            raise ValueError("Instrumentation already set.")
        self._instrumentation = value

    @property
    def instrumentation_promise(self) -> Optional[InstrumentationPromise]:
        return self._instrumentation_promise

    @instrumentation_promise.setter
    def instrumentation_promise(self, value: InstrumentationPromise):
        if self._instrumentation_promise is not None:
            raise ValueError("Instrumentation promise already set.")
        self._instrumentation_promise = value

    @property
    def suitable_alert_levels(self) -> List[AlertLevel]:
        """
        Returns a copy of the suitable alert levels
        :return:
        """
        return list(self._suitable_alert_levels)

    @suitable_alert_levels.setter
    def suitable_alert_levels(self, value: List[AlertLevel]):
        self._suitable_alert_levels = value

    @property
    def uses_instrumentation(self) -> bool:
        return self._uses_instrumentation

    @uses_instrumentation.setter
    def uses_instrumentation(self, value: bool):
        self._uses_instrumentation = value

    @property
    def instrumentation_processed(self) -> bool:
        if not self._uses_instrumentation:
            return True
        return self._instrumentation_processed

    @instrumentation_processed.setter
    def instrumentation_processed(self, value: bool):
        self._instrumentation_processed = value

    @property
    def init_sensor_alert(self) -> SensorAlert:
        return self._init_sensor_alert

    @property
    def instrumentation_finished(self) -> bool:
        if not self._uses_instrumentation:
            return True
        if self._instrumentation_promise is None:
            return False
        return self._instrumentation_promise.is_finished()

    @property
    def sensor_alert(self) -> Optional[SensorAlert]:
        if self._uses_instrumentation:
            if self._instrumentation_promise is None:
                raise InstrumentationNotRun("Instrumentation not run yet.")

            elif not self._instrumentation_promise.is_finished():
                raise InstrumentationNotFinished("Instrumentation not finished.")

            elif not self._instrumentation_promise.was_success():
                raise InstrumentationNotSuccessful("Instrumentation not successful.")

            return self._instrumentation_promise.new_sensor_alert

        else:
            return self._init_sensor_alert

    def is_alert_delay_passed(self) -> bool:
        return int(time.time()) >= self._time_valid


class SensorAlertExecuter(threading.Thread):
    """
    This class is woken up if a sensor alert is received and executes all necessary steps
    """

    def __init__(self,
                 globalData: GlobalData):
        threading.Thread.__init__(self)

        # get global configured data
        self._global_data = globalData
        self._logger = self._global_data.logger
        self._manager_update_executer = self._global_data.managerUpdateExecuter
        self._storage = self._global_data.storage
        self._alert_levels = self._global_data.alertLevels  # type: List[AlertLevel]
        self._server_sessions = self._global_data.serverSessions

        # file nme of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        # Create an event that is used to wake this thread up and react on sensor alerts.
        self._sensor_alert_event = threading.Event()
        self._sensor_alert_event.clear()

        self._sensor_alert_queue = []
        self._sensor_alert_queue_lock = threading.Lock()

        self._exit_flag = False

        # Get instance of the internal alert level instrumentation error sensor (if exists).
        self._internal_sensor = None  # type: Optional[AlertLevelInstrumentationErrorSensor]
        for internal_sensor in self._global_data.internalSensors:
            if isinstance(internal_sensor, AlertLevelInstrumentationErrorSensor):
                self._internal_sensor = internal_sensor

    def _filter_sensor_alerts(self, sensor_alert_states: List[SensorAlertState]) -> Tuple[List[SensorAlertState],
                                                                                          List[SensorAlert]]:
        """
        Filters sensor alert states and removes each sensor alert that can no longer satisfy trigger conditions.
        :param sensor_alert_states:
        :return: a new list of sensor alert states to further process and a list of sensor alert that satisfy
        no longer a trigger condition but apply for state/data change messages.
        """
        new_sensor_alert_states = list()
        dropped_sensor_alerts = list()
        for sensor_alert_state in sensor_alert_states:

            # Remove sensor alerts that do not have any suitable alert level.
            if not sensor_alert_state.suitable_alert_levels:
                dropped_sensor_alerts.append(sensor_alert_state.sensor_alert)
                continue

            if sensor_alert_state.uses_instrumentation and sensor_alert_state.instrumentation_finished:
                instrumentation_promise = sensor_alert_state.instrumentation_promise
                if not instrumentation_promise.was_success():
                    self._logger.error("[%s]: Instrumentation for Sensor Alert '%s' failed."
                                       % (self._log_tag, sensor_alert_state.init_sensor_alert.description))
                    dropped_sensor_alerts.append(sensor_alert_state.init_sensor_alert)
                    continue

                # Still update state/data of sensor if sensor alert was suppressed by instrumentation.
                elif instrumentation_promise.new_sensor_alert is None:
                    dropped_sensor_alerts.append(sensor_alert_state.init_sensor_alert)
                    continue

            new_sensor_alert_states.append(sensor_alert_state)

        return new_sensor_alert_states, dropped_sensor_alerts

    def _process_sensor_alert(self, sensor_alert_states: List[SensorAlertState]) -> List[SensorAlertState]:
        """
        Processes the sensor alert states by triggering them if the conditions are satisfied.
        :param sensor_alert_states:
        :return: list of sensor alert states that still need handling
        """
        new_sensor_alert_states = list()
        for sensor_alert_state in sensor_alert_states:

            if sensor_alert_state.is_alert_delay_passed() and sensor_alert_state.instrumentation_processed:
                self._trigger_sensor_alert(sensor_alert_state)

            else:
                new_sensor_alert_states.append(sensor_alert_state)

        return new_sensor_alert_states

    def _queue_manager_update(self, sensor_alerts: List[SensorAlert]):
        """
        Adds data and state of sensor alert to the queue for state changes of the manager update executer
        if received sensor alert does change state or data.
        :param sensor_alerts:
        """

        for sensor_alert in sensor_alerts:
            self._logger.debug("[%s]: Sensor Alert '%s' does not satisfy any trigger condition."
                               % (self._log_tag, sensor_alert.description))

            if (self._manager_update_executer is not None
                    and (sensor_alert.hasLatestData or sensor_alert.changeState)):

                # Get sensor data from the database which contains the correct data for the sensor
                # (either it was updated when the sensor alert message was received and hasLatestData flag was set
                # or it contains the last known data before this sensor alert message which is the correct one).
                sensor_data_obj = self._storage.getSensorData(sensor_alert.sensorId,
                                                              self._logger)
                if sensor_data_obj is None:
                    self._logger.error("[%s]: Unable to get data for Sensor '%d' from database. "
                                       % (self._log_tag, sensor_alert.sensorId)
                                       + "Skipping state change notification.")
                    continue

                # Get sensor state from the database which contains the correct state for the sensor
                # (either it was updated when the sensor alert message was received and changeState flag was set
                # or it contains the last known state before this sensor alert message which is the correct one).
                state = self._storage.getSensorState(sensor_alert.sensorId,
                                                     self._logger)
                if state is None:
                    self._logger.error("[%s]: Unable to get state for Sensor '%d' from database. "
                                       % (self._log_tag, sensor_alert.sensorId)
                                       + "Skipping state change notification.")
                    continue

                self._manager_update_executer.queue_state_change(sensor_alert.sensorId,
                                                                 state,
                                                                 sensor_data_obj)

    def _separate_instrumentation_alert_levels(self,
                                               sensor_alert_states: List[SensorAlertState]) -> List[SensorAlertState]:
        """
        Splits sensor alerts into separated sensor alert states for each alert level that is instrumented.
        NOTE: Does not update the triggered alert levels of the sensor alert object.
        :param sensor_alert_states:
        :return: modified list of sensor alert states
        """
        new_sensor_alert_states = list()
        for base_sensor_alert_state in sensor_alert_states:
            if len(base_sensor_alert_state.suitable_alert_levels) == 1:
                if base_sensor_alert_state.suitable_alert_levels[0].instrumentation_active:
                    base_sensor_alert_state.uses_instrumentation = True
                new_sensor_alert_states.append(base_sensor_alert_state)
                continue

            # Split each sensor alert into separated sensor alerts for each alert level that is instrumented
            # and keep the not-instrumented ones for the base alert level.
            not_instrumented_alert_levels = list()
            for alert_level in list(base_sensor_alert_state.suitable_alert_levels):
                if alert_level.instrumentation_active:

                    # Copy sensor alert for instrumentation and empty triggered alert levels list.
                    new_sensor_alert = SensorAlert().deepcopy(base_sensor_alert_state.sensor_alert)
                    del new_sensor_alert.triggeredAlertLevels[:]

                    new_sensor_alert_state = SensorAlertState(new_sensor_alert, [alert_level])
                    new_sensor_alert_state.uses_instrumentation = True
                    new_sensor_alert_states.append(new_sensor_alert_state)
                else:
                    not_instrumented_alert_levels.append(alert_level)
            base_sensor_alert_state.suitable_alert_levels = not_instrumented_alert_levels

            # If no suitable alert level remains in the base sensor alert state(meaning all alert levels were
            # instrumented and hence have now a separated sensor alert state) remove it.
            if base_sensor_alert_state.suitable_alert_levels:
                new_sensor_alert_states.append(base_sensor_alert_state)

        return new_sensor_alert_states

    def _trigger_sensor_alert(self, sensor_alert_state: SensorAlertState):
        """
        Triggers the given sensor alert by sending messages to the appropriate clients.
        :param sensor_alert_state: sensor alert to trigger
        """

        # Get sensor alert object from state.
        sensor_alert = None
        try:
            sensor_alert = sensor_alert_state.sensor_alert

        except Exception:
            self._logger.exception("[%s]: Unable to get Sensor Alert object from Sensor Alert state."
                                   % self._log_tag)
            return

        # Send sensor alert to all manager and alert clients.
        for server_session in self._server_sessions:
            # Ignore sessions which do not exist yet and that are not alert or manager clients.
            if server_session.clientComm is None:
                continue
            if (server_session.clientComm.nodeType != "manager"
               and server_session.clientComm.nodeType != "alert"):
                continue
            if not server_session.clientComm.clientInitialized:
                continue

            # Only send a sensor alert to a client that actually handles a triggered alert level.
            client_alert_levels = server_session.clientComm.clientAlertLevels
            at_least_one = any(al in client_alert_levels
                               for al in sensor_alert_state.sensor_alert.triggeredAlertLevels)
            if not at_least_one:
                continue

            # Sending sensor alert to manager/alert node via a thread to not block the sensor alert executer.
            sensor_alert_process = AsynchronousSender(self._global_data, server_session.clientComm)
            # set thread to daemon
            # => threads terminates when main thread terminates
            sensor_alert_process.daemon = True
            sensor_alert_process.sendSensorAlert = True
            sensor_alert_process.sensorAlert = sensor_alert

            self._logger.debug("[%s]: Sending Sensor Alert to manager/alert (%s:%d)."
                               % (self._log_tag,
                                  server_session.clientComm.clientAddress,
                                  server_session.clientComm.clientPort))
            sensor_alert_process.start()

    def _update_suitable_alert_levels(self, sensor_alert_states: List[SensorAlertState]):
        """
        Updates the suitable alert levels of each sensor alert state as well as the triggered alert levels of
        the sensor alert object.
        :param sensor_alert_states:
        """

        option = self._storage.get_option_by_type("profile")
        if option is None:
            self._logger.error("[%s]: Unable to get 'profile' option from database." % self._log_tag)
            return
        curr_profile_id = option.value

        for sensor_alert_state in sensor_alert_states:

            # Create a list of currently suitable alert levels.
            suitable_alert_levels = list()
            for alert_level in sensor_alert_state.suitable_alert_levels:

                if sensor_alert_state.uses_instrumentation:

                    if not sensor_alert_state.instrumentation_finished:
                        suitable_alert_levels.append(alert_level)
                        continue

                    # If an instrumentation is used and it is finished, set it as processed since we now check
                    # if it would still satisfy trigger conditions (this is important because the instrumentation
                    # could negate the state of the original sensor alert and we need a state that says it was
                    # processed).
                    sensor_alert_state.instrumentation_processed = True

                    # Instrumentation failed, but it is still suitable and will be filtered out later in the process.
                    if not sensor_alert_state.instrumentation_promise.was_success():
                        suitable_alert_levels.append(alert_level)
                        continue

                    # Instrumentation suppresses sensor alert, but it is still suitable
                    # and will be filtered out later in the process.
                    if sensor_alert_state.sensor_alert is None:
                        suitable_alert_levels.append(alert_level)
                        continue

                    if curr_profile_id in alert_level.profiles:

                        # If the alert level does trigger a sensor alert message for a "triggered" state
                        # while the sensor alert is for the "triggered" state.
                        if alert_level.triggerAlertTriggered and sensor_alert_state.sensor_alert.state == 1:
                            suitable_alert_levels.append(alert_level)
                            continue

                        # If the alert level does trigger a sensor alert message for a "normal" state
                        # while the sensor alert is for the "normal" state.
                        if alert_level.triggerAlertNormal and sensor_alert_state.sensor_alert.state == 0:
                            suitable_alert_levels.append(alert_level)
                            continue

                else:

                    if curr_profile_id in alert_level.profiles:

                        # If the alert level does trigger a sensor alert message for a "triggered" state
                        # while the sensor alert is for the "triggered" state.
                        if alert_level.triggerAlertTriggered and sensor_alert_state.sensor_alert.state == 1:
                            suitable_alert_levels.append(alert_level)
                            continue

                        # If the alert level does trigger a sensor alert message for a "normal" state
                        # while the sensor alert is for the "normal" state.
                        if alert_level.triggerAlertNormal and sensor_alert_state.sensor_alert.state == 0:
                            suitable_alert_levels.append(alert_level)
                            continue

            sensor_alert_state.suitable_alert_levels = suitable_alert_levels

            # NOTE: triggered alert levels does not contain the alert level of the instrumentation before it is finished
            # since the instrumentation script decides if it is actually triggers.
            if sensor_alert_state.uses_instrumentation:
                if (sensor_alert_state.instrumentation_finished
                        and sensor_alert_state.instrumentation_promise.was_success()
                        and sensor_alert_state.sensor_alert is not None):
                    sensor_alert_state.sensor_alert.triggeredAlertLevels = \
                        [al.level for al in sensor_alert_state.suitable_alert_levels]

            else:
                sensor_alert_state.sensor_alert.triggeredAlertLevels = \
                    [al.level for al in sensor_alert_state.suitable_alert_levels]

    def _update_instrumentation(self, sensor_alert_states: List[SensorAlertState]):
        """
        Executes the instrumentation of the alert levels if they have any.
        :param sensor_alert_states:
        """
        for sensor_alert_state in sensor_alert_states:
            if not sensor_alert_state.uses_instrumentation:
                continue

            # Sensor alert states list can contain states with no suitable alert level because filtering them out
            # happens in a later processing step. Hence just ignore them.
            if not sensor_alert_state.suitable_alert_levels:
                continue

            # Ignore sensor alerts that have already a running instrumentation.
            if sensor_alert_state.instrumentation_promise is not None:
                continue

            # Start instrumentation for sensor alert.
            alert_level = sensor_alert_state.suitable_alert_levels[0]
            sensor_alert_state.instrumentation = Instrumentation(alert_level,
                                                                 sensor_alert_state.init_sensor_alert,
                                                                 self._logger,
                                                                 self._internal_sensor)
            sensor_alert_state.instrumentation_promise = sensor_alert_state.instrumentation.execute()

    def add_sensor_alert(self,
                         node_id: int,
                         sensor_id: int,
                         state: int,
                         optional_data: Optional[Dict[str, Any]],
                         change_state: bool,
                         has_latest_data: bool,
                         data_type: int,
                         sensor_data: Any,
                         logger: logging.Logger = None) -> bool:
        """
        Adds Sensor Alert to processing queue.

        :param node_id:
        :param sensor_id:
        :param state:
        :param optional_data:
        :param change_state:
        :param has_latest_data:
        :param data_type:
        :param sensor_data:
        :param logger:
        :return: Success or Failure
        """

        if logger is None:
            logger = self._logger

        sensor_alert = SensorAlert()
        sensor_alert.sensorId = sensor_id
        sensor_alert.nodeId = node_id
        sensor_alert.timeReceived = int(time.time())
        sensor_alert.state = state
        sensor_alert.changeState = change_state
        sensor_alert.hasLatestData = has_latest_data
        sensor_alert.dataType = data_type
        sensor_alert.data = sensor_data

        sensor_alert.hasOptionalData = False
        sensor_alert.optionalData = optional_data
        if optional_data:
            sensor_alert.hasOptionalData = True

        sensor = self._storage.getSensorById(sensor_id, logger)
        if sensor is None:
            logger.error("[%s]: Not able to get sensor %d from database." % (self._log_tag, sensor_id))
            return False

        sensor_alert.description = sensor.description
        sensor_alert.alertDelay = sensor.alertDelay
        sensor_alert.alertLevels = sensor.alertLevels

        with self._sensor_alert_queue_lock:
            self._sensor_alert_queue.append(sensor_alert)

        self._sensor_alert_event.set()
        return True

    def run(self):
        """
        This function starts the endless loop of the alert executer thread.
        """

        curr_sensor_alert_states = list()  # type: List[SensorAlertState]
        while True:

            # check if thread should terminate
            if self._exit_flag:
                return

            # check if manager update executer object reference does exist
            # => if not get it from the global data
            if self._manager_update_executer is None:
                self._manager_update_executer = self._global_data.managerUpdateExecuter

            # Apply a processing state to each sensor alert from the queue.
            while self._sensor_alert_queue:
                with self._sensor_alert_queue_lock:
                    sensor_alert = self._sensor_alert_queue.pop(0)

                sensor_alert_state = SensorAlertState(sensor_alert, self._alert_levels)
                curr_sensor_alert_states.append(sensor_alert_state)

            # Update timestamp of last state updated of alert level instrumentation error sensor
            # to not let it timeout (state never changes of this sensor hence we have to do it artificially).
            utc_timestamp = int(time.time())
            if self._internal_sensor is not None and (utc_timestamp - self._internal_sensor.lastStateUpdated) > 30:

                self._internal_sensor.lastStateUpdated = utc_timestamp
                if not self._storage.updateSensorState(self._internal_sensor.nodeId,  # nodeId
                                                       [(self._internal_sensor.clientSensorId,
                                                         self._internal_sensor.state)],  # stateList
                                                       self._logger):  # logger
                    self._logger.error("[%s]: Not able to change sensor state for internal alert level "
                                       % self._log_tag
                                       + "instrumentation error sensor.")

            # Wait if we do not have any sensor alerts to process.
            if not curr_sensor_alert_states:
                # Timeout after 10 seconds to make sure we see an exit flag change.
                self._sensor_alert_event.wait(10)
                self._sensor_alert_event.clear()
                continue

            # Split sensor alert states into separated states for instrumented alert levels
            # NOTE: does not update triggered alert levels of sensor alert object, hence performed in the beginning.
            curr_sensor_alert_states = self._separate_instrumentation_alert_levels(curr_sensor_alert_states)

            # Update suitable alert levels as well as triggered alert leves of sensor alert object.
            self._update_suitable_alert_levels(curr_sensor_alert_states)

            # Execute instrumentation of alert levels (if they have any).
            self._update_instrumentation(curr_sensor_alert_states)

            # Filter out sensor alert states that can no longer satisfy trigger condition
            # (no suitable alert levels, instrumentation suppresses them, ...)
            curr_sensor_alert_states, dropped_sensor_alerts = self._filter_sensor_alerts(curr_sensor_alert_states)

            curr_sensor_alert_states = self._process_sensor_alert(curr_sensor_alert_states)

            # Queue dropped sensor alerts for state/data updates to manager clients.
            self._queue_manager_update(dropped_sensor_alerts)

            time.sleep(0.5)

    def exit(self):
        """
        sets the exit flag to shut down the thread
        """
        self._exit_flag = True
