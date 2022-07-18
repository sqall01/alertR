import json
import os
import time
from unittest import TestCase
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange, SensorDataType, SensorDataNone, \
    SensorDataInt, SensorErrorState, SensorObjErrorStateChange
from lib.sensor.executer import ExecuterSensor


class TestExecuterSensor(TestCase):

    def _create_base_sensor(self) -> ExecuterSensor:
        sensor = ExecuterSensor()
        sensor.id = 1
        sensor.description = "Test Executer"
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

    def test_basic_sensor_alert_normal(self):
        """
        Tests if a Sensor Alert is triggered through the given exit code.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "exit_code_0.py")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.state = 1

        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(1, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(0, events[0].state)

        # Make sure sensor state has changed.
        self.assertEqual(0, sensor.state)

        # Make sure sensor error state has not changed
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_basic_sensor_alert_triggered(self):
        """
        Tests if a Sensor Alert is triggered through the given exit code.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "exit_code_1.py")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

        # Make sure sensor error state has not changed
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_basic_state_change_normal(self):
        """
        Tests if a state change is triggered through the given exit code.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "exit_code_0.py")

        sensor = self._create_base_sensor()
        sensor.triggerAlertNormal = False

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.state = 1

        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(1, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(0, events[0].state)

        # Make sure sensor state has changed.
        self.assertEqual(0, sensor.state)

        # Make sure sensor error state has not changed
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_basic_state_change_triggered(self):
        """
        Tests if a state change is triggered through the given exit code.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "exit_code_1.py")

        sensor = self._create_base_sensor()
        sensor.triggerAlert = False

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(1, events[0].state)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

        # Make sure sensor error state has not changed
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_not_executable(self):
        """
        Tests if a sensor alert is triggered if process execution fails.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "not_executable.py")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(SensorErrorState.ExecutionError, events[0].error_state.state)
        self.assertTrue(events[0].error_state.msg.startswith("Unable to execute process:"))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure sensor error state has changed
        self.assertEqual(SensorErrorState.ExecutionError, sensor.error_state.state)
        self.assertTrue(sensor.error_state.msg.startswith("Unable to execute process:"))

    def test_timeout(self):
        """
        Tests if a sensor alert is triggered if process times out.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "timeout.py")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(7)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(SensorErrorState.TimeoutError, events[0].error_state.state)
        self.assertEqual("Process timed out.", events[0].error_state.msg)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure sensor error state has changed
        self.assertEqual(SensorErrorState.TimeoutError, sensor.error_state.state)
        self.assertEqual("Process timed out.", sensor.error_state.msg)

    def test_output_handling_sensor_alert(self):
        """
        Tests if output handling processing triggers a Sensor Alert.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "mirror.py")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.INT,
                "data": SensorDataInt(1337, "test unit").copy_to_dict(),
                "hasLatestData": False,
                "changeState": True
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.INT
        sensor.data= SensorDataInt(0, "test unit")
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = True
        sensor.execute.append(target_cmd)
        sensor.execute.append(json.dumps(payload))

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

        # Make sure data has not changed.
        self.assertTrue(SensorDataInt.verify_dict(payload["payload"]["data"]))
        self.assertNotEqual(SensorDataInt.copy_from_dict(payload["payload"]["data"]), sensor.data)

        # Make sure sensor error state has not changed
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_output_handling_state_change(self):
        """
        Tests if output handling processing triggers a state change.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "mirror.py")

        payload = {
            "message": "statechange",
            "payload": {
                "state": 1,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = True
        sensor.execute.append(target_cmd)
        sensor.execute.append(json.dumps(payload))

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertTrue(SensorDataNone.verify_dict(payload["payload"]["data"]))
        self.assertEqual(SensorDataNone.copy_from_dict(payload["payload"]["data"]), events[0].data)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

        # Make sure sensor error state has not changed
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_output_handling_error_state_change(self):
        """
        Tests if output handling processing triggers an error state change.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "mirror.py")

        payload = {
            "message": "sensorerrorstatechange",
            "payload": {
                "error_state": {
                    "state": SensorErrorState.GenericError,
                    "msg": "some error msg"
                }
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = True
        sensor.execute.append(target_cmd)
        sensor.execute.append(json.dumps(payload))

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["error_state"]["state"], events[0].error_state.state)
        self.assertEqual(payload["payload"]["error_state"]["msg"], events[0].error_state.msg)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure sensor error state has changed
        self.assertEqual(SensorErrorState.GenericError, sensor.error_state.state)
        self.assertEqual("some error msg", sensor.error_state.msg)

    def test_output_handling_illegal_data(self):
        """
        Tests if output handling processing triggers an ProcessingError error state.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "mirror.py")
        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = True
        sensor.execute.append(target_cmd)
        sensor.execute.append("no json stuff")

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(SensorErrorState.ProcessingError, events[0].error_state.state)
        self.assertEqual("Illegal script output.", events[0].error_state.msg)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure sensor error state has changed
        self.assertEqual(SensorErrorState.ProcessingError, sensor.error_state.state)
        self.assertEqual("Illegal script output.", sensor.error_state.msg)

    def test_error_state_change_through_state_change_event(self):
        """
        Tests if error state is changed back to normal if a state change event occurs with no new data during while
        a not-OK error state exists.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "exit_code_0.py")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data= SensorDataNone()
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)
        sensor.error_state = SensorErrorState(SensorErrorState.GenericError, "test error")

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.GenericError, sensor.error_state.state)
        self.assertEqual("test error", sensor.error_state.msg)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(SensorErrorState.OK, events[0].error_state.state)
        self.assertEqual("", events[0].error_state.msg)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure sensor error state has changed
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)
