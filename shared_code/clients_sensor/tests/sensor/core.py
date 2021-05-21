import time
from typing import List, Tuple
from lib.client.communication import Promise
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange
from lib.sensor.core import _PollingSensor


class MockServerCommunication:

    def __init__(self):
        self._is_connected = True
        self._send_sensor_alerts = []  # type: List[Tuple[float, SensorObjSensorAlert]]
        self._send_state_changes = []  # type: List[Tuple[float, SensorObjStateChange]]
        self._send_sensors_status_updates = []  # type: List[int]

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def send_sensor_alerts(self) -> List[Tuple[float, SensorObjSensorAlert]]:
        return self._send_sensor_alerts

    @property
    def send_sensors_status_updates(self) -> List[int]:
        return self._send_sensors_status_updates

    @property
    def send_state_changes(self) -> List[Tuple[float, SensorObjStateChange]]:
        return self._send_state_changes

    def send_sensor_alert(self,
                          sensor_alert: SensorObjSensorAlert) -> Promise:
        self._send_sensor_alerts.append((time.time(), sensor_alert))
        return Promise("sensoralert", "place holder sensoralert msg")

    def send_state_change(self,
                          state_change: SensorObjStateChange) -> Promise:
        self._send_state_changes.append((time.time(), state_change))
        return Promise("statechange", "place holder statechange msg")

    def send_sensors_status_update(self):
        self._send_sensors_status_updates.append(int(time.time()))
        return Promise("status", "place holder status msg")


class MockSensors(_PollingSensor):

    def __init__(self):
        super().__init__()

    def _execute(self):
        pass

    def add_sensor_alert(self, sensor_alert: SensorObjSensorAlert):
        self._add_event(sensor_alert)

    def add_state_change(self, state_change: SensorObjStateChange):
        self._add_event(state_change)

    def initialize(self) -> bool:
        return True
