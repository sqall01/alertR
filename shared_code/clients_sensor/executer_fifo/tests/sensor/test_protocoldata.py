import time
from unittest import TestCase
from lib.sensor.protocoldata import _ProtocolDataSensor


class MockProtocolDataSensor(_ProtocolDataSensor):

    def __init__(self):
        super().__init__()

    def initialize(self) -> bool:
        pass


class TestProtocolDataSensor(TestCase):

    def _create_base_sensor(self) -> MockNumberSensor:
        sensor = MockProtocolDataSensor()
        sensor.id = 1
        sensor.description = "Test Protocol Data"
        sensor.alertDelay = 0
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.triggerState = 1
        sensor.alertLevels = [1]
        self._sensors.append(sensor)
        return sensor

    def setUp(self):
        self._sensors = []

    def tearDown(self):
        for sensor in self._sensors:
            sensor.exit()

    def test_todo(self):
        raise NotImplementedError("TODO")
