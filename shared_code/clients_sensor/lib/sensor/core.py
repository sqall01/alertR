#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import os
import logging
import threading
from typing import Optional, List, Union, Dict, Any
from ..client.serverCommunication import ServerCommunication
from ..globalData import GlobalData
# noinspection PyProtectedMember
from ..globalData.sensorObjects import _SensorData, SensorDataNone, SensorErrorState, SensorObjErrorStateChange,\
    SensorObjSensorAlert, SensorObjStateChange, SensorDataType


class _PollingSensor:
    """
    Internal class that holds the important attributes for a sensor to work
    (this class must be inherited from the used sensor class).
    """

    def __init__(self):

        # Used for logging.
        self._log_tag = os.path.basename(__file__)

        # Id of this sensor on this client.
        self.id = None  # type: Optional[int]

        # Description of this sensor.
        self.description = None  # type: Optional[str]

        # Delay in seconds this sensor has before a sensor alert is
        # issued by the server.
        self.alertDelay = None  # type: Optional[int]

        # Local state of the sensor (either 1 or 0). This state is translated
        # (with the help of "triggerState") into 1 = "triggered" / 0 = "normal"
        # when it is send to the server.
        self.state = None  # type: Optional[int]

        # State the sensor counts as triggered (either 1 or 0).
        self.triggerState = None  # type: Optional[int]

        # A list of alert levels this sensor belongs to.
        self.alertLevels = list()  # type: List[int]

        # Flag that indicates if this sensor should trigger a sensor alert
        # for the state "triggered" (true or false).
        self.triggerAlert = None  # type: Optional[bool]

        # Flag that indicates if this sensor should trigger a sensor alert
        # for the state "normal" (true or false).
        self.triggerAlertNormal = None  # type: Optional[bool]

        # The type of data the sensor holds (i.e., none at all, integer, ...).
        # Type is given by the enum class "SensorDataType".
        self.sensorDataType = None  # type: Optional[int]

        # The actual data the sensor holds.
        self.data = None  # type: Optional[_SensorData]

        # The error state of the sensor.
        self.error_state = SensorErrorState()  # type: SensorErrorState

        # List of events (Sensor Alerts, state change) currently triggered by the Sensor that are not yet processed.
        # This list gives also the timely order in which the events are triggered
        # (first element triggered before the second element and so on).
        self._events = []  # type: List[Union[SensorObjSensorAlert, SensorObjStateChange, SensorObjErrorStateChange]]
        self._events_lock = threading.Lock()

        self._thread = None  # type: Optional[threading.Thread]

        self._exit_flag = False

    def _add_event(self, event: Union[SensorObjSensorAlert, SensorObjStateChange, SensorObjErrorStateChange]):
        """
        Internal function to add an event (e.g., Sensor Alert or state change) for processing.
        :param event:
        """
        with self._events_lock:
            self._events.append(event)

    def _add_sensor_alert(self,
                          state: int,
                          change_state: bool,
                          optional_data: Optional[Dict[str, Any]] = None,
                          has_latest_data: bool = False,
                          sensor_data: Optional[_SensorData] = None):
        """
        Internal function that adds a Sensor Alert for processing.

        Updates Sensor state if change_state flag is set to True.

        Updates Sensor data if has_latest_data flag is set to True.

        If the Sensor configuration disables Sensor Alert events for triggered or normal states the Sensor Alert
        event with this state will be transformed into a state change event (which will lose optional data).
        State change events will be sent if state_change flag is True or has_latest_data flag is True.
        If state_change flag is set to True, the send-state change event contains the state given to the function,
        otherwise the current state of the Sensor is used.
        If has_latest_data flag is set to True, the send-state change event contains the data given to the function,
        otherwise the current data of the Sensor is used.
        If state_change and has_latest_data are False and the corresponding triggered or normal state is disabled
        in the Sensor configuration, the event will be dropped.

        If sensor not in OK state it clears error state and adds an error state change for processing.

        :param state:
        :param change_state:
        :param optional_data:
        :param has_latest_data:
        :param sensor_data:
        """
        sensor_alert = SensorObjSensorAlert()
        sensor_alert.clientSensorId = self.id
        sensor_alert.changeState = change_state

        # Translate local trigger state to the AlertR sensor state.
        if state == self.triggerState:
            sensor_alert.state = 1

        else:
            sensor_alert.state = 0

        if optional_data is not None:
            sensor_alert.hasOptionalData = True
            sensor_alert.optionalData = optional_data

        else:
            sensor_alert.hasOptionalData = False
            sensor_alert.optionalData = None

        sensor_alert.hasLatestData = has_latest_data
        sensor_alert.dataType = self.sensorDataType

        # Throw exception if we did not get Sensor data but we expected it.
        if sensor_data is None and self.sensorDataType != SensorDataType.NONE:
            raise ValueError("Expected data since data type is not NONE")

        if sensor_data is None:
            sensor_alert.data = SensorDataNone()

        else:
            sensor_alert.data = sensor_data

        # Change sensor state if it is set.
        if change_state:
            self.state = state

        # Update sensor data if it has latest data.
        if has_latest_data:
            self.data = sensor_alert.data

        # Set error state to OK (Sensor Alerts can only happen if the Sensor is in no error state).
        # Function only clears error state if it is in not OK state.
        self._clear_error_state()

        # Only submit Sensor Alert event for processing if Sensor configuration allows it.
        # Else, transform Sensor Alert event to state change event if it changed the state or data of the Sensor.
        # Otherwise, drop event.
        if state == self.triggerState:
            if self.triggerAlert:
                self._log_info(self._log_tag, "Sensor Alert for 'triggered' raised.")
                self._add_event(sensor_alert)

            elif change_state:
                # Only send state change event with event data if the Sensor Alert held the latest data.
                if has_latest_data:
                    self._add_state_change(state,
                                           sensor_data)

                # Send state change event with old data from sensor.
                else:
                    self._add_state_change(state,
                                           self.data)

            # If Sensor Alert event did not change the state of the Sensor, but contained the latest data
            # send a state change event with the old state from the sensor.
            elif has_latest_data:
                self._add_state_change(self.state,
                                       sensor_data)

        else:
            if self.triggerAlertNormal:
                self._log_info(self._log_tag, "Sensor Alert for 'normal' raised.")
                self._add_event(sensor_alert)

            elif change_state:
                # Only send state change event with event data if the Sensor Alert held the latest data.
                if has_latest_data:
                    self._add_state_change(state,
                                           sensor_data)

                # Send state change event with old data from sensor.
                else:
                    self._add_state_change(state,
                                           self.data)

            # If Sensor Alert event did not change the state of the Sensor, but contained the latest data
            # send a state change event with the old state from the sensor.
            elif has_latest_data:
                self._add_state_change(self.state,
                                       sensor_data)

    def _add_state_change(self,
                          state: int,
                          sensor_data: Optional[_SensorData] = None):
        """
        Internal function that adds a state change for processing.

        Updates Sensor state.

        Updates Sensor data.

        If sensor not in OK state it clears error state and adds an error state change for processing.

        :param state:
        :param sensor_data:
        """
        state_change = SensorObjStateChange()
        state_change.clientSensorId = self.id

        # Translate local trigger state to the AlertR state.
        if state == self.triggerState:
            state_change.state = 1

        else:
            state_change.state = 0

        state_change.dataType = self.sensorDataType

        # Throw exception if we did not get Sensor data but we expected it.
        if sensor_data is None and self.sensorDataType != SensorDataType.NONE:
            raise ValueError("Expected data since data type is not NONE")

        if sensor_data is None:
            state_change.data = SensorDataNone()
        else:
            state_change.data = sensor_data

        # Set error state to OK (state changes can only happen if the Sensor is in no error state).
        # Function only clears error state if it is in not OK state.
        self._clear_error_state()

        self.state = state
        self.data = state_change.data

        self._add_event(state_change)

    def _clear_error_state(self):
        """
        Internal function to clear the Sensor error state.

        Only clears it if error state is not OK, otherwise does nothing.
        """
        if self.error_state.state == SensorErrorState.OK:
            return

        self._set_error_state(SensorErrorState.OK, "")

    def _execute(self):
        """
        Internal function that implements the actual sensor logic.
        """
        raise NotImplementedError("Function not implemented yet.")

    def _log_debug(self, log_tag: str, msg: str):
        """
        Internal function to log debug messages.
        """
        logging.debug("[%s] [Sensor %d] %s" % (log_tag, self.id, msg))

    def _log_info(self, log_tag: str, msg: str):
        """
        Internal function to log info messages.
        """
        logging.info("[%s] [Sensor %d] %s" % (log_tag, self.id, msg))

    def _log_warning(self, log_tag: str, msg: str):
        """
        Internal function to log warning messages.
        """
        logging.warning("[%s] [Sensor %d] %s" % (log_tag, self.id, msg))

    def _log_error(self, log_tag: str, msg: str):
        """
        Internal function to log error messages.
        """
        logging.error("[%s] [Sensor %d] %s" % (log_tag, self.id, msg))

    def _log_critical(self, log_tag: str, msg: str):
        """
        Internal function to log critical messages.
        """
        logging.critical("[%s] [Sensor %d] %s" % (log_tag, self.id, msg))

    def _log_exception(self, log_tag: str, msg: str):
        """
        Internal function to log exception messages.
        """
        logging.exception("[%s] [Sensor %d] %s" % (log_tag, self.id, msg))

    def _set_error_state(self, error_state: int, msg: str):
        """
        Internal function to set the Sensor error state and
        adding an error state change event to the queue for processing.

        Only sets error state if:
        1) Sensor error state is not OK and sensor error state should be set to OK
        2) Sensor error state is OK and sensor error state should be set to not OK
        Otherwise it does nothing.

        :param error_state:
        :param msg:
        """

        if error_state == SensorErrorState.OK and self.error_state.state != SensorErrorState.OK:
            self.error_state.set_ok()

        elif error_state != SensorErrorState.OK and self.error_state.state == SensorErrorState.OK:
            self.error_state.set_error(error_state, msg)

        else:
            return

        obj = SensorObjErrorStateChange()
        obj.clientSensorId = self.id
        obj.error_state = SensorErrorState.deepcopy(self.error_state)

        self._add_event(obj)

    def exit(self):
        """
        Exits sensor thread.
        """
        self._exit_flag = True

    def get_events(self) -> List[Union[SensorObjSensorAlert, SensorObjStateChange, SensorObjErrorStateChange]]:
        """
        Gets a list of triggered events (e.g., Sensor Alert or state change) not yet processed.
        :return: List of events
        """
        with self._events_lock:
            temp_list = self._events
            self._events = []
            return temp_list

    def initialize(self) -> bool:
        """
        Initializes the sensor.
        :return: success or failure
        """
        raise NotImplementedError("Abstract class.")

    def start(self) -> bool:
        """
        Starts the sensor.
        :return: success or failure
        """
        self._thread = threading.Thread(target=self._execute)
        self._thread.daemon = True
        self._thread.start()
        return True


class SensorExecuter(threading.Thread):
    """
    This class polls the sensor events and sends messages to the server.
    """

    def __init__(self, global_data: GlobalData):
        threading.Thread.__init__(self)
        self._log_tag = os.path.basename(__file__)
        self._global_data = global_data
        self._connection = self._global_data.serverComm  # type: Optional[ServerCommunication]
        self._sensors = self._global_data.sensors

        # Interval in which a full state of the Sensors are send to the server.
        self._full_state_interval = 60

        self._exit_flag = False

        self._is_initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    def execute(self):

        # Time on which the last full sensor states were sent to the server.
        last_full_state_sent = 0

        # Get reference to server communication object.
        while self._connection is None:
            time.sleep(0.5)
            self._connection = self._global_data.serverComm

        self._is_initialized = True

        while True:

            if self._exit_flag:
                return

            # Check if the client is connected to the server
            # => wait and continue loop until client is connected
            if not self._connection.is_connected:
                time.sleep(0.5)
                continue

            # Poll all sensors and send their alerts/states.
            for sensor in self._sensors:
                for event in sensor.get_events():
                    if type(event) == SensorObjSensorAlert:
                        logging.info("[%s]: Sensor alert triggered for Sensor %d with state %d."
                                     % (self._log_tag, sensor.id, event.state))
                        self._connection.send_sensor_alert(event)

                    elif type(event) == SensorObjStateChange:
                        logging.debug("[%s]: State changed for Sensor %d to state %d."
                                      % (self._log_tag, sensor.id, event.state))
                        self._connection.send_state_change(event)

                    elif type(event) == SensorObjErrorStateChange:
                        logging.debug("[%s]: Error state changed for Sensor %d to error state %d"
                                      % (self._log_tag, sensor.id, event.error_state.state))
                        self._connection.send_error_state_change(event)

            # Check if the last state that was sent to the server is older than 60 seconds => send state update
            utc_timestamp = int(time.time())
            if (utc_timestamp - last_full_state_sent) > self._full_state_interval:
                logging.debug("[%s]: Last state timed out." % self._log_tag)

                self._connection.send_sensors_status_update()

                # Update time on which the full state update was sent.
                last_full_state_sent = utc_timestamp

            time.sleep(0.5)

    def exit(self):
        self._exit_flag = True
        for sensor in self._sensors:
            sensor.exit()

    def run(self):
        self.execute()
