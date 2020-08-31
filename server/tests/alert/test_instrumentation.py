import logging
import json
from unittest import TestCase
from lib.localObjects import AlertLevel, SensorAlert, SensorDataType
from lib.alert.instrumentation import Instrumentation, InstrumentationPromise


class TestInstrumentation(TestCase):

    def test_process_output_valid(self):
        """
        Tests a valid output processing of an instrumentation script.
        """

        alert_level = AlertLevel()
        alert_level.level = 1
        alert_level.name = "Instrumentation Alert Level"
        alert_level.triggerAlways = True
        alert_level.triggerAlertTriggered = True
        alert_level.triggerAlertNormal = True
        alert_level.instrumentation_cmd = "dummy.py"
        alert_level.instrumentation_timeout = 10

        sensor_alert = SensorAlert()
        sensor_alert.sensorAlertId = 1
        sensor_alert.nodeId = 2
        sensor_alert.sensorId = 3
        sensor_alert.description = "Instrumentation Sensor Alert"
        sensor_alert.timeReceived = 1337
        sensor_alert.alertDelay = 20
        sensor_alert.state = 1
        sensor_alert.hasOptionalData = False
        sensor_alert.changeState = False
        sensor_alert.alertLevels = [1]
        sensor_alert.triggeredAlertLevels = [1]
        sensor_alert.hasLatestData = False
        sensor_alert.dataType = SensorDataType.NONE
        sensor_alert.sensorData = None

        logger = logging.getLogger("Instrumentation Test Case")

        instrumentation = Instrumentation(alert_level, sensor_alert, logger)

        # Test instrumentation script output processing.
        new_sensor_alert = instrumentation._process_output(json.dumps(sensor_alert.convert_to_dict()))

        self.assertEqual(sensor_alert.sensorAlertId, new_sensor_alert.sensorAlertId)
        self.assertEqual(sensor_alert.nodeId, new_sensor_alert.nodeId)
        self.assertEqual(sensor_alert.sensorId, new_sensor_alert.sensorId)
        self.assertEqual(sensor_alert.description, new_sensor_alert.description)
        self.assertEqual(sensor_alert.timeReceived, new_sensor_alert.timeReceived)
        self.assertEqual(sensor_alert.alertDelay, new_sensor_alert.alertDelay)
        self.assertEqual(sensor_alert.state, new_sensor_alert.state)
        self.assertEqual(sensor_alert.hasOptionalData, new_sensor_alert.hasOptionalData)
        self.assertEqual(sensor_alert.optionalData, new_sensor_alert.optionalData)
        self.assertEqual(sensor_alert.changeState, new_sensor_alert.changeState)
        self.assertTrue(all(map(lambda x: x in sensor_alert.alertLevels,
                                new_sensor_alert.alertLevels)))
        self.assertTrue(all(map(lambda x: x in new_sensor_alert.alertLevels,
                                sensor_alert.alertLevels)))
        self.assertTrue(all(map(lambda x: x in sensor_alert.triggeredAlertLevels,
                                new_sensor_alert.triggeredAlertLevels)))
        self.assertTrue(all(map(lambda x: x in new_sensor_alert.triggeredAlertLevels,
                                sensor_alert.triggeredAlertLevels)))
        self.assertEqual(sensor_alert.hasLatestData, new_sensor_alert.hasLatestData)
        self.assertEqual(sensor_alert.dataType, new_sensor_alert.dataType)
        self.assertEqual(sensor_alert.sensorData, new_sensor_alert.sensorData)
