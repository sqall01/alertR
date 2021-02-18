import logging
import json
import os
import time
from typing import Dict, Any, List
from unittest import TestCase
from lib.internalSensors import AlertLevelInstrumentationErrorSensor
from lib.localObjects import AlertLevel, SensorAlert, SensorDataType
from lib.alert.instrumentation import Instrumentation
from lib.globalData import GlobalData


class MockInternalSensor(AlertLevelInstrumentationErrorSensor):

    def __init__(self):
        global_data = GlobalData()
        super().__init__(global_data)

        self._optional_data = list()  # type: List[Dict[str, Any]]

    @property
    def optional_data(self) -> List[Dict[str, Any]]:
        return self._optional_data

    def _add_sensor_alert(self, optional_data: Dict[str, Any]):
        self._optional_data.append(optional_data)


class TestInstrumentation(TestCase):

    def _create_instrumentation_dummy(self) -> Instrumentation:
        alert_level = AlertLevel()
        alert_level.level = 1
        alert_level.name = "Instrumentation Alert Level"
        alert_level.triggerAlertTriggered = True
        alert_level.triggerAlertNormal = True
        alert_level.instrumentation_cmd = "dummy.py"
        alert_level.instrumentation_timeout = 10

        sensor_alert = SensorAlert()
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

        arg = sensor_alert.convert_to_dict()
        arg["instrumentationAlertLevel"] = sensor_alert.alertLevels[0]

        # Test instrumentation script output processing.
        was_success, new_sensor_alert = instrumentation._process_output(json.dumps(arg))

        # NOTE: triggeredAlertLevels are not passed to the instrumentation script (since they do not have
        # any significant information value) and hence get lost.
        self.assertTrue(was_success)
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
        self.assertEqual(sensor_alert.hasLatestData, new_sensor_alert.hasLatestData)
        self.assertEqual(sensor_alert.dataType, new_sensor_alert.dataType)
        self.assertEqual(sensor_alert.sensorData, new_sensor_alert.sensorData)
        self.assertEqual(0, len(new_sensor_alert.triggeredAlertLevels))

    def test_process_output_invalid_node_id(self):
        """
        Tests an invalid node id output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.nodeId = sensor_alert.nodeId + 1

        arg = invalid_sensor_alert.convert_to_dict()
        arg["instrumentationAlertLevel"] = sensor_alert.alertLevels[0]

        # Test instrumentation script output processing.
        was_success, new_sensor_alert = instrumentation._process_output(json.dumps(arg))
        self.assertFalse(was_success)
        self.assertIsNone(new_sensor_alert)

    def test_process_output_invalid_sensor_id(self):
        """
        Tests an invalid sensor id output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.sensorId = sensor_alert.sensorId + 1

        arg = invalid_sensor_alert.convert_to_dict()
        arg["instrumentationAlertLevel"] = sensor_alert.alertLevels[0]

        # Test instrumentation script output processing.
        was_success, new_sensor_alert = instrumentation._process_output(json.dumps(arg))
        self.assertFalse(was_success)
        self.assertIsNone(new_sensor_alert)

    def test_process_output_invalid_description(self):
        """
        Tests an invalid description output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.description = sensor_alert.description + "_invalid"

        arg = invalid_sensor_alert.convert_to_dict()
        arg["instrumentationAlertLevel"] = sensor_alert.alertLevels[0]

        # Test instrumentation script output processing.
        was_success, new_sensor_alert = instrumentation._process_output(json.dumps(arg))
        self.assertFalse(was_success)
        self.assertIsNone(new_sensor_alert)

    def test_process_output_invalid_time_received(self):
        """
        Tests an invalid time received output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.timeReceived = sensor_alert.timeReceived + 1

        arg = invalid_sensor_alert.convert_to_dict()
        arg["instrumentationAlertLevel"] = sensor_alert.alertLevels[0]

        # Test instrumentation script output processing.
        was_success, new_sensor_alert = instrumentation._process_output(json.dumps(arg))
        self.assertFalse(was_success)
        self.assertIsNone(new_sensor_alert)

    def test_process_output_invalid_alert_delay(self):
        """
        Tests an invalid alert delay output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.alertDelay = sensor_alert.alertDelay + 1

        arg = invalid_sensor_alert.convert_to_dict()
        arg["instrumentationAlertLevel"] = sensor_alert.alertLevels[0]

        # Test instrumentation script output processing.
        was_success, new_sensor_alert = instrumentation._process_output(json.dumps(arg))
        self.assertFalse(was_success)
        self.assertIsNone(new_sensor_alert)

    def test_process_output_invalid_alert_levels(self):
        """
        Tests an invalid alert levels output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.alertLevels.append(22)

        arg = invalid_sensor_alert.convert_to_dict()
        arg["instrumentationAlertLevel"] = sensor_alert.alertLevels[0]

        # Test instrumentation script output processing.
        was_success, new_sensor_alert = instrumentation._process_output(json.dumps(arg))
        self.assertFalse(was_success)
        self.assertIsNone(new_sensor_alert)

    def test_process_output_invalid_instrumentation_alert_level(self):
        """
        Tests an invalid instrumentation alert level output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)

        arg = invalid_sensor_alert.convert_to_dict()
        arg["instrumentationAlertLevel"] = 22

        # Test instrumentation script output processing.
        was_success, new_sensor_alert = instrumentation._process_output(json.dumps(arg))
        self.assertFalse(was_success)
        self.assertIsNone(new_sensor_alert)

    def test_process_output_invalid_data_type(self):
        """
        Tests an invalid data type output processing of an instrumentation script.
        """
        instrumentation = self._create_instrumentation_dummy()
        sensor_alert = instrumentation._sensor_alert

        invalid_sensor_alert = SensorAlert().deepcopy(sensor_alert)
        invalid_sensor_alert.dataType = SensorDataType.INT
        invalid_sensor_alert.sensorData = 1

        arg = invalid_sensor_alert.convert_to_dict()
        arg["instrumentationAlertLevel"] = sensor_alert.alertLevels[0]

        # Test instrumentation script output processing.
        was_success, new_sensor_alert = instrumentation._process_output(json.dumps(arg))
        self.assertFalse(was_success)
        self.assertIsNone(new_sensor_alert)

    def test_execute_valid_blocking(self):
        """
        Tests a valid execution of an instrumentation script.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "mirror.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd

        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertTrue(promise.was_success())

        # NOTE: triggeredAlertLevels are not passed to the instrumentation script (since they do not have
        # any significant information value) and hence get lost.
        sensor_alert = promise.orig_sensor_alert
        new_sensor_alert = promise.new_sensor_alert
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
        self.assertEqual(sensor_alert.hasLatestData, new_sensor_alert.hasLatestData)
        self.assertEqual(sensor_alert.dataType, new_sensor_alert.dataType)
        self.assertEqual(sensor_alert.sensorData, new_sensor_alert.sensorData)

    def test_execute_valid_non_blocking(self):
        """
        Tests a valid execution of an instrumentation script.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "mirror.py")
        timeout = 5

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        instrumentation._alert_level.instrumentation_timeout = timeout

        # Execute instrumentation script non-blocking.
        promise = instrumentation.execute()

        time.sleep(timeout*2)

        self.assertTrue(promise.is_finished())
        self.assertTrue(promise.was_success())

        # NOTE: triggeredAlertLevels are not passed to the instrumentation script (since they do not have
        # any significant information value) and hence get lost.
        sensor_alert = promise.orig_sensor_alert
        new_sensor_alert = promise.new_sensor_alert
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
        self.assertEqual(sensor_alert.hasLatestData, new_sensor_alert.hasLatestData)
        self.assertEqual(sensor_alert.dataType, new_sensor_alert.dataType)
        self.assertEqual(sensor_alert.sensorData, new_sensor_alert.sensorData)

    def test_execute_valid_suppress(self):
        """
        Tests a valid execution of an instrumentation script which suppresses a sensor alert.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "suppress.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd

        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertTrue(promise.was_success())

        new_sensor_alert = promise.new_sensor_alert
        self.assertIsNone(new_sensor_alert)

    def test_execute_invalid_no_cmd(self):
        """
        Tests an invalid execution of an instrumentation script (script does not exist).
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "does_not_exist.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd

        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertFalse(promise.was_success())

    def test_execute_invalid_empty(self):
        """
        Tests an invalid execution of an instrumentation script (script does not output anything).
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "empty.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd

        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertFalse(promise.was_success())

    def test_execute_invalid_empty_internal_sensor(self):
        """
        Tests an invalid execution of an instrumentation script (script does not output anything) with internal sensor.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "empty.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        internal_sensor = MockInternalSensor()
        instrumentation._internal_sensor = internal_sensor

        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertEqual(1, len(internal_sensor.optional_data))
        self.assertEqual(instrumentation._alert_level.level, internal_sensor.optional_data[0]["alert_level"])

    def test_execute_invalid_not_executable(self):
        """
        Tests an invalid execution of an instrumentation script (script is not executable).
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "not_executable.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd

        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertFalse(promise.was_success())

    def test_execute_invalid_not_executable_internal_sensor(self):
        """
        Tests an invalid execution of an instrumentation script (script is not executable) with internal sensor.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "not_executable.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        internal_sensor = MockInternalSensor()
        instrumentation._internal_sensor = internal_sensor

        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertEqual(1, len(internal_sensor.optional_data))
        self.assertEqual(instrumentation._alert_level.level, internal_sensor.optional_data[0]["alert_level"])

    def test_execute_invalid_timeout_blocking(self):
        """
        Tests an invalid execution of an instrumentation script (script times out).
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "timeout.py")

        # timeout script waits 60 seconds.
        timeout = 5

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        instrumentation._alert_level.instrumentation_timeout = timeout

        # Since we have a blocking execution, we do not need to wait here.
        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertFalse(promise.was_success())

    def test_execute_invalid_timeout_blocking_internal_sensor(self):
        """
        Tests an invalid execution of an instrumentation script (script times out) with internal sensor.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "timeout.py")

        # timeout script waits 60 seconds.
        timeout = 5

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        instrumentation._alert_level.instrumentation_timeout = timeout

        internal_sensor = MockInternalSensor()
        instrumentation._internal_sensor = internal_sensor

        # Since we have a blocking execution, we do not need to wait here.
        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertEqual(1, len(internal_sensor.optional_data))
        self.assertEqual(instrumentation._alert_level.level, internal_sensor.optional_data[0]["alert_level"])

    def test_execute_invalid_timeout_non_blocking(self):
        """
        Tests an invalid execution of an instrumentation script (script times out).
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "timeout.py")

        # timeout script waits 60 seconds.
        timeout = 5

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        instrumentation._alert_level.instrumentation_timeout = timeout

        # Execute instrumentation script non-blocking.
        promise = instrumentation.execute()

        time.sleep(timeout/2)

        self.assertFalse(promise.is_finished())

        self.assertTrue(promise.is_finished(timeout=timeout*2))
        self.assertFalse(promise.was_success())

    def test_execute_invalid_exit_code(self):
        """
        Tests an invalid execution of an instrumentation script (exit code 1).
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "exit_code_1.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd

        # Since we have a blocking execution, we do not need to wait here.
        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertFalse(promise.was_success())

    def test_execute_invalid_exit_code_internal_sensor(self):
        """
        Tests an invalid execution of an instrumentation script (exit code 1) with internal sensor.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "exit_code_1.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        internal_sensor = MockInternalSensor()
        instrumentation._internal_sensor = internal_sensor

        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertEqual(1, len(internal_sensor.optional_data))
        self.assertEqual(instrumentation._alert_level.level, internal_sensor.optional_data[0]["alert_level"])

    def test_execute_invalid_output(self):
        """
        Tests an invalid execution of an instrumentation script (invalid output).
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "invalid_output.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd

        # Since we have a blocking execution, we do not need to wait here.
        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertFalse(promise.was_success())

    def test_execute_invalid_output_internal_sensor(self):
        """
        Tests an invalid execution of an instrumentation script (invalid output) with internal sensor.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "invalid_output.py")

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        internal_sensor = MockInternalSensor()
        instrumentation._internal_sensor = internal_sensor

        promise = instrumentation._execute()

        self.assertTrue(promise.is_finished())
        self.assertEqual(1, len(internal_sensor.optional_data))
        self.assertEqual(instrumentation._alert_level.level, internal_sensor.optional_data[0]["alert_level"])

    def test_execute_twice(self):
        """
        Tests a valid execution of an instrumentation script and if it is only executed once while called twice.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "mirror_with_timestamp.py")

        timeout = 5

        # Prepare instrumentation object.
        instrumentation = self._create_instrumentation_dummy()
        instrumentation._alert_level.instrumentation_cmd = target_cmd
        instrumentation._alert_level.instrumentation_timeout = timeout

        # Execute instrumentation script non-blocking.
        promise_first = instrumentation.execute()

        time.sleep(timeout+2)

        self.assertTrue(promise_first.is_finished())
        self.assertTrue(promise_first.was_success())

        timestamp_first = promise_first.new_sensor_alert.optionalData["timestamp"]

        # Execute instrumentation script non-blocking.
        promise_second = instrumentation.execute()

        time.sleep(timeout+2)

        self.assertTrue(promise_first.is_finished())
        self.assertTrue(promise_first.was_success())

        self.assertEqual(promise_first, promise_second)

        # Instrumentation script adds timestamp of execution to the output, check if they are the same
        # to verify that the instrumentation script was only executed once.
        timestamp_second = promise_second.new_sensor_alert.optionalData["timestamp"]
        self.assertEqual(timestamp_first, timestamp_second)
