import logging
import json
import threading
from typing import Any, List
from unittest import TestCase
from lib.localObjects import AlertLevel, SensorAlert, SensorDataType
from lib.internalSensors import AlertLevelInstrumentationErrorSensor
from lib.storage.core import _Storage
from lib.globalData import GlobalData


class MockSensorAlertExecuter:

    def __init__(self):
        self.sensorAlertEvent = threading.Event()
        self.sensorAlertEvent.clear()


class MockStorage(_Storage):

    def __init__(self):
        self._sensor_alerts = list()  # type: List[SensorAlert]

    @property
    def sensor_alerts(self) -> List[SensorAlert]:
        return self._sensor_alerts

    def addSensorAlert(self,
                       nodeId: int,
                       sensorId: int,
                       state: int,
                       dataJson: str,
                       changeState: bool,
                       hasLatestData: bool,
                       dataType: int,
                       sensorData: Any,
                       logger: logging.Logger = None) -> bool:

        sensor_alert = SensorAlert()
        sensor_alert.nodeId = nodeId
        sensor_alert.sensorId = sensorId
        sensor_alert.state = state
        sensor_alert.changeState = changeState
        sensor_alert.hasLatestData = hasLatestData
        sensor_alert.dataType = dataType
        sensor_alert.sensorData = sensorData
        if dataJson == "":
            sensor_alert.hasOptionalData = False
        else:
            sensor_alert.hasOptionalData = True
            sensor_alert.optionalData = json.loads(dataJson)

        self._sensor_alerts.append(sensor_alert)
        return True


class TestAlertLevelInstrumentationError(TestCase):

    def _create_internal_sensor(self) -> AlertLevelInstrumentationErrorSensor:
        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Level Instrumentation Error Test Case")
        global_data.storage = MockStorage()
        global_data.sensorAlertExecuter = MockSensorAlertExecuter()

        sensor = AlertLevelInstrumentationErrorSensor(global_data)
        sensor.initialize()
        return sensor

    def test_add_sensor_alert(self):
        """
        Tests if the created sensor alert is correctly added for processing.
        """
        internal_sensor = self._create_internal_sensor()
        storage = internal_sensor._storage
        sensor_alert_executer = internal_sensor._sensor_alert_executer

        self.assertEqual(0, len(storage.sensor_alerts))
        self.assertFalse(sensor_alert_executer.sensorAlertEvent.is_set())

        optional_data = dict()
        optional_data["alert_level"] = 1337

        internal_sensor._add_sensor_alert(optional_data)

        self.assertEqual(1, len(storage.sensor_alerts))
        self.assertTrue(sensor_alert_executer.sensorAlertEvent.is_set())

        sensor_alert = storage.sensor_alerts[0]
        self.assertEqual(0, internal_sensor.state)
        self.assertEqual(internal_sensor.nodeId, sensor_alert.nodeId)
        self.assertEqual(internal_sensor.sensorId, sensor_alert.sensorId)
        self.assertEqual(1, sensor_alert.state)
        self.assertFalse(sensor_alert.changeState)
        self.assertFalse(sensor_alert.hasLatestData)
        self.assertEqual(SensorDataType.NONE, sensor_alert.dataType)
        self.assertTrue(sensor_alert.hasOptionalData)
        self.assertTrue("alert_level" in sensor_alert.optionalData.keys())
        self.assertEqual(1337, sensor_alert.optionalData["alert_level"])

    def test_raise_sensor_alert_execution_error(self):
        """
        Tests if a sensor alert for execution error is added for processing.
        """
        internal_sensor = self._create_internal_sensor()
        storage = internal_sensor._storage
        sensor_alert_executer = internal_sensor._sensor_alert_executer

        self.assertEqual(0, len(storage.sensor_alerts))
        self.assertFalse(sensor_alert_executer.sensorAlertEvent.is_set())

        alert_level = AlertLevel()
        alert_level.level = 1
        alert_level.name = "alert_level_1"
        alert_level.triggerAlways = True
        alert_level.triggerAlertTriggered = True
        alert_level.triggerAlertNormal = True
        alert_level.instrumentation_active = True
        alert_level.instrumentation_cmd = "some_instrumentation_script_path"
        alert_level.instrumentation_timeout = 10

        internal_sensor.raise_sensor_alert_execution_error(alert_level)

        self.assertEqual(1, len(storage.sensor_alerts))
        self.assertTrue(sensor_alert_executer.sensorAlertEvent.is_set())

        sensor_alert = storage.sensor_alerts[0]
        self.assertEqual(0, internal_sensor.state)
        self.assertEqual(internal_sensor.nodeId, sensor_alert.nodeId)
        self.assertEqual(internal_sensor.sensorId, sensor_alert.sensorId)
        self.assertEqual(1, sensor_alert.state)
        self.assertFalse(sensor_alert.changeState)
        self.assertFalse(sensor_alert.hasLatestData)
        self.assertEqual(SensorDataType.NONE, sensor_alert.dataType)
        self.assertTrue(sensor_alert.hasOptionalData)
        self.assertTrue("message" in sensor_alert.optionalData.keys())
        self.assertEqual(alert_level.level, sensor_alert.optionalData["alert_level"])
        self.assertEqual(alert_level.instrumentation_cmd, sensor_alert.optionalData["instrumentation_cmd"])
        self.assertEqual(alert_level.instrumentation_timeout, sensor_alert.optionalData["instrumentation_timeout"])

    def test_raise_sensor_alert_exit_code(self):
        """
        Tests if a sensor alert for an invalid exit code is added for processing.
        """
        internal_sensor = self._create_internal_sensor()
        storage = internal_sensor._storage
        sensor_alert_executer = internal_sensor._sensor_alert_executer

        self.assertEqual(0, len(storage.sensor_alerts))
        self.assertFalse(sensor_alert_executer.sensorAlertEvent.is_set())

        alert_level = AlertLevel()
        alert_level.level = 1
        alert_level.name = "alert_level_1"
        alert_level.triggerAlways = True
        alert_level.triggerAlertTriggered = True
        alert_level.triggerAlertNormal = True
        alert_level.instrumentation_active = True
        alert_level.instrumentation_cmd = "some_instrumentation_script_path"
        alert_level.instrumentation_timeout = 10

        internal_sensor.raise_sensor_alert_exit_code(alert_level, 1337)

        self.assertEqual(1, len(storage.sensor_alerts))
        self.assertTrue(sensor_alert_executer.sensorAlertEvent.is_set())

        sensor_alert = storage.sensor_alerts[0]
        self.assertEqual(0, internal_sensor.state)
        self.assertEqual(internal_sensor.nodeId, sensor_alert.nodeId)
        self.assertEqual(internal_sensor.sensorId, sensor_alert.sensorId)
        self.assertEqual(1, sensor_alert.state)
        self.assertFalse(sensor_alert.changeState)
        self.assertFalse(sensor_alert.hasLatestData)
        self.assertEqual(SensorDataType.NONE, sensor_alert.dataType)
        self.assertTrue(sensor_alert.hasOptionalData)
        self.assertTrue("message" in sensor_alert.optionalData.keys())
        self.assertEqual(alert_level.level, sensor_alert.optionalData["alert_level"])
        self.assertEqual(alert_level.instrumentation_cmd, sensor_alert.optionalData["instrumentation_cmd"])
        self.assertEqual(alert_level.instrumentation_timeout, sensor_alert.optionalData["instrumentation_timeout"])
        self.assertEqual(1337, sensor_alert.optionalData["exit_code"])

    def test_raise_sensor_alert_invalid_output(self):
        """
        Tests if a sensor alert for invalid output is added for processing.
        """
        internal_sensor = self._create_internal_sensor()
        storage = internal_sensor._storage
        sensor_alert_executer = internal_sensor._sensor_alert_executer

        self.assertEqual(0, len(storage.sensor_alerts))
        self.assertFalse(sensor_alert_executer.sensorAlertEvent.is_set())

        alert_level = AlertLevel()
        alert_level.level = 1
        alert_level.name = "alert_level_1"
        alert_level.triggerAlways = True
        alert_level.triggerAlertTriggered = True
        alert_level.triggerAlertNormal = True
        alert_level.instrumentation_active = True
        alert_level.instrumentation_cmd = "some_instrumentation_script_path"
        alert_level.instrumentation_timeout = 10

        internal_sensor.raise_sensor_alert_invalid_output(alert_level)

        self.assertEqual(1, len(storage.sensor_alerts))
        self.assertTrue(sensor_alert_executer.sensorAlertEvent.is_set())

        sensor_alert = storage.sensor_alerts[0]
        self.assertEqual(0, internal_sensor.state)
        self.assertEqual(internal_sensor.nodeId, sensor_alert.nodeId)
        self.assertEqual(internal_sensor.sensorId, sensor_alert.sensorId)
        self.assertEqual(1, sensor_alert.state)
        self.assertFalse(sensor_alert.changeState)
        self.assertFalse(sensor_alert.hasLatestData)
        self.assertEqual(SensorDataType.NONE, sensor_alert.dataType)
        self.assertTrue(sensor_alert.hasOptionalData)
        self.assertTrue("message" in sensor_alert.optionalData.keys())
        self.assertEqual(alert_level.level, sensor_alert.optionalData["alert_level"])
        self.assertEqual(alert_level.instrumentation_cmd, sensor_alert.optionalData["instrumentation_cmd"])
        self.assertEqual(alert_level.instrumentation_timeout, sensor_alert.optionalData["instrumentation_timeout"])

    def test_raise_sensor_alert_output_empty(self):
        """
        Tests if a sensor alert for empty output is added for processing.
        """
        internal_sensor = self._create_internal_sensor()
        storage = internal_sensor._storage
        sensor_alert_executer = internal_sensor._sensor_alert_executer

        self.assertEqual(0, len(storage.sensor_alerts))
        self.assertFalse(sensor_alert_executer.sensorAlertEvent.is_set())

        alert_level = AlertLevel()
        alert_level.level = 1
        alert_level.name = "alert_level_1"
        alert_level.triggerAlways = True
        alert_level.triggerAlertTriggered = True
        alert_level.triggerAlertNormal = True
        alert_level.instrumentation_active = True
        alert_level.instrumentation_cmd = "some_instrumentation_script_path"
        alert_level.instrumentation_timeout = 10

        internal_sensor.raise_sensor_alert_output_empty(alert_level)

        self.assertEqual(1, len(storage.sensor_alerts))
        self.assertTrue(sensor_alert_executer.sensorAlertEvent.is_set())

        sensor_alert = storage.sensor_alerts[0]
        self.assertEqual(0, internal_sensor.state)
        self.assertEqual(internal_sensor.nodeId, sensor_alert.nodeId)
        self.assertEqual(internal_sensor.sensorId, sensor_alert.sensorId)
        self.assertEqual(1, sensor_alert.state)
        self.assertFalse(sensor_alert.changeState)
        self.assertFalse(sensor_alert.hasLatestData)
        self.assertEqual(SensorDataType.NONE, sensor_alert.dataType)
        self.assertTrue(sensor_alert.hasOptionalData)
        self.assertTrue("message" in sensor_alert.optionalData.keys())
        self.assertEqual(alert_level.level, sensor_alert.optionalData["alert_level"])
        self.assertEqual(alert_level.instrumentation_cmd, sensor_alert.optionalData["instrumentation_cmd"])
        self.assertEqual(alert_level.instrumentation_timeout, sensor_alert.optionalData["instrumentation_timeout"])

    def test_raise_sensor_alert_timeout(self):
        """
        Tests if a sensor alert for instrumentation timeout is added for processing.
        """
        internal_sensor = self._create_internal_sensor()
        storage = internal_sensor._storage
        sensor_alert_executer = internal_sensor._sensor_alert_executer

        self.assertEqual(0, len(storage.sensor_alerts))
        self.assertFalse(sensor_alert_executer.sensorAlertEvent.is_set())

        alert_level = AlertLevel()
        alert_level.level = 1
        alert_level.name = "alert_level_1"
        alert_level.triggerAlways = True
        alert_level.triggerAlertTriggered = True
        alert_level.triggerAlertNormal = True
        alert_level.instrumentation_active = True
        alert_level.instrumentation_cmd = "some_instrumentation_script_path"
        alert_level.instrumentation_timeout = 10

        internal_sensor.raise_sensor_alert_timeout(alert_level)

        self.assertEqual(1, len(storage.sensor_alerts))
        self.assertTrue(sensor_alert_executer.sensorAlertEvent.is_set())

        sensor_alert = storage.sensor_alerts[0]
        self.assertEqual(0, internal_sensor.state)
        self.assertEqual(internal_sensor.nodeId, sensor_alert.nodeId)
        self.assertEqual(internal_sensor.sensorId, sensor_alert.sensorId)
        self.assertEqual(1, sensor_alert.state)
        self.assertFalse(sensor_alert.changeState)
        self.assertFalse(sensor_alert.hasLatestData)
        self.assertEqual(SensorDataType.NONE, sensor_alert.dataType)
        self.assertTrue(sensor_alert.hasOptionalData)
        self.assertTrue("message" in sensor_alert.optionalData.keys())
        self.assertEqual(alert_level.level, sensor_alert.optionalData["alert_level"])
        self.assertEqual(alert_level.instrumentation_cmd, sensor_alert.optionalData["instrumentation_cmd"])
        self.assertEqual(alert_level.instrumentation_timeout, sensor_alert.optionalData["instrumentation_timeout"])
