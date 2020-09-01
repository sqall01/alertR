import logging
import json
import os
from unittest import TestCase
from lib.localObjects import AlertLevel, SensorAlert, SensorDataType
from lib.alert.instrumentation import Instrumentation, InstrumentationPromise


class TestInstrumentation(TestCase):

    def _create_instrumentation_dummy(self) -> Instrumentation:
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

        return Instrumentation(alert_level, sensor_alert, logger)

    def test_process_output_valid(self):
        """
        Tests a valid output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

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

    def test_process_output_invalid_sensor_alert_id(self):
        """
        Tests an invalid sensor alert id output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.sensorAlertId = sensor_alert.sensorAlertId + 1

        # Test instrumentation script output processing.
        self.assertIsNone(instrumentation._process_output(json.dumps(invalid_sensor_alert.convert_to_dict())))

    def test_process_output_invalid_node_id(self):
        """
        Tests an invalid node id output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.nodeId = sensor_alert.nodeId + 1

        # Test instrumentation script output processing.
        self.assertIsNone(instrumentation._process_output(json.dumps(invalid_sensor_alert.convert_to_dict())))

    def test_process_output_invalid_sensor_id(self):
        """
        Tests an invalid sensor id output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.sensorId = sensor_alert.sensorId + 1

        # Test instrumentation script output processing.
        self.assertIsNone(instrumentation._process_output(json.dumps(invalid_sensor_alert.convert_to_dict())))

    def test_process_output_invalid_description(self):
        """
        Tests an invalid description output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.description = sensor_alert.description + "_invalid"

        # Test instrumentation script output processing.
        self.assertIsNone(instrumentation._process_output(json.dumps(invalid_sensor_alert.convert_to_dict())))

    def test_process_output_invalid_time_received(self):
        """
        Tests an invalid time received output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.timeReceived = sensor_alert.timeReceived + 1

        # Test instrumentation script output processing.
        self.assertIsNone(instrumentation._process_output(json.dumps(invalid_sensor_alert.convert_to_dict())))

    def test_process_output_invalid_alert_delay(self):
        """
        Tests an invalid alert delay output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.alertDelay = sensor_alert.alertDelay + 1

        # Test instrumentation script output processing.
        self.assertIsNone(instrumentation._process_output(json.dumps(invalid_sensor_alert.convert_to_dict())))

    def test_process_output_invalid_alert_levels(self):
        """
        Tests an invalid alert levels output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.alertLevels.append(22)

        # Test instrumentation script output processing.
        self.assertIsNone(instrumentation._process_output(json.dumps(invalid_sensor_alert.convert_to_dict())))

    def test_process_output_invalid_triggered_alert_levels(self):
        """
        Tests an invalid triggered alert levels output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.triggeredAlertLevels.append(22)

        # Test instrumentation script output processing.
        self.assertIsNone(instrumentation._process_output(json.dumps(invalid_sensor_alert.convert_to_dict())))

    def test_process_output_invalid_data_type(self):
        """
        Tests an invalid data type output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.dataType = SensorDataType.INT
        invalid_sensor_alert.sensorData = 1

        # Test instrumentation script output processing.
        self.assertIsNone(instrumentation._process_output(json.dumps(invalid_sensor_alert.convert_to_dict())))

    def test_execute_valid(self):
        """
        Tests a valid execution of an instrumentation script.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "mirror.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        promise = InstrumentationPromise(instrumentation._alert_level,
                                         instrumentation._sensor_alert)
        instrumentation._promise = promise

        instrumentation._execute()

        raise NotImplementedError("Does not work")