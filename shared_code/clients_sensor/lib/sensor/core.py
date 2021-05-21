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
from typing import Optional, List, Union
from ..globalData import GlobalData
from ..globalData import SensorObjSensorAlert, SensorObjStateChange


# Internal class that holds the important attributes
# for a sensor to work (this class must be inherited from the
# used sensor class).
class _PollingSensor:

    def __init__(self):

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
        self.sensorData = None  # type: Optional[int, float]

        # List of events (Sensor Alerts, state change) currently triggered by the Sensor that are not yet processed.
        # This list gives also the timely order in which the events are triggered
        # (first element triggered before the second element and so on).
        self._events = []  # type: List[Union[SensorObjSensorAlert, SensorObjStateChange]]
        self._events_lock = threading.Lock()

        self._thread = None  # type: Optional[threading.Thread]

    def _add_event(self, event: Union[SensorObjSensorAlert, SensorObjStateChange]):
        """
        Internal function to add an event (e.g., Sensor Alert or state change) for processing.
        :param event:
        """
        with self._events_lock:
            self._events.append(event)

    def _execute(self):
        """
        Internal function that implements the actual sensor logic.
        """
        raise NotImplementedError("Function not implemented yet.")

    def get_events(self) -> List[Union[SensorObjSensorAlert, SensorObjStateChange]]:
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
        raise NotImplementedError("Function not implemented yet.")

    def start(self) -> bool:
        """
        Starts the sensor.
        :return: success or failure
        """
        self._thread = threading.Thread(target=self._execute)
        self._thread.daemon = True
        self._thread.start()
        return True


# this class polls the sensor states and triggers alerts and state changes
class SensorExecuter(threading.Thread):

    def __init__(self, global_data: GlobalData):
        threading.Thread.__init__(self)
        self._log_tag = os.path.basename(__file__)
        self._global_data = global_data
        self._connection = self._global_data.serverComm
        self._sensors = self._global_data.sensors

        # Interval in which a full state of the Sensors are send to the server.
        self._full_state_interval = 60

        self._exit_flag = False

    def execute(self):

        # Time on which the last full sensor states were sent to the server.
        last_full_state_sent = 0

        # Get reference to server communication object.
        while self._connection is None:
            time.sleep(0.5)
            self._connection = self._global_data.serverComm

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
                        logging.info("[%s]: Sensor alert triggered by '%s' with state %d."
                                     % (self._log_tag, sensor.description, event.state))
                        self._connection.send_sensor_alert(event)

                    elif type(event) == SensorObjStateChange:
                        logging.debug("[%s]: State changed by '%s' to state %d."
                                      % (self._log_tag, sensor.description, event.state))
                        self._connection.send_state_change(event)

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

    def run(self):
        self.execute()
