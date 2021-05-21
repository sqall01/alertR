import json
import os
import time
from unittest import TestCase
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange, SensorDataType
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
        return sensor

    def test_basic_sensor_alert_normal(self):
        """
        Tests if a Sensor Alert is triggered through the given exit code.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "exit_code_0.py")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.state = 1

        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(1, sensor.state)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(0, events[0].state)

        # Make sure sensor state has changed.
        self.assertEqual(0, sensor.state)

    def test_basic_sensor_alert_triggered(self):
        """
        Tests if a Sensor Alert is triggered through the given exit code.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "exit_code_1.py")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

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
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.state = 1

        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(1, sensor.state)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(0, events[0].state)

        # Make sure sensor state has changed.
        self.assertEqual(0, sensor.state)

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
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(1, events[0].state)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

    def test_not_executable(self):
        """
        Tests if a sensor alert is triggered if process execution fails.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "not_executable.py")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.timeout = 5
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].hasOptionalData)
        self.assertEqual("Unable to execute process", events[0].optionalData["message"])

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

    def test_timeout(self):
        """
        Tests if a sensor alert is triggered if process times out.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "timeout.py")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = False
        sensor.execute.append(target_cmd)

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        time.sleep(7)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].hasOptionalData)
        self.assertEqual("Timeout", events[0].optionalData["message"])

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

    def test_output_handling_sensor_alert_triggered(self):
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
                "data": 1337,
                "hasLatestData": False,
                "changeState": True
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.INT
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = True
        sensor.execute.append(target_cmd)
        sensor.execute.append(json.dumps(payload))

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

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
        self.assertNotEqual(payload["payload"]["data"], sensor.sensorData)

    def test_output_handling_sensor_alert_data_change(self):
        """
        Tests if output handling processing triggers a Sensor Alert and changes data.
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
                "data": 1337,
                "hasLatestData": True,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.INT
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = True
        sensor.execute.append(target_cmd)
        sensor.execute.append(json.dumps(payload))

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["data"], events[0].sensorData)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has changed.
        self.assertEqual(1337, sensor.sensorData)

    def test_output_handling_state_change_triggered(self):
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
                "data": None,
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = True
        sensor.execute.append(target_cmd)
        sensor.execute.append(json.dumps(payload))

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

    def test_output_handling_state_change_data(self):
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
                "dataType": SensorDataType.INT,
                "data": 1337,
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.INT
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = True
        sensor.execute.append(target_cmd)
        sensor.execute.append(json.dumps(payload))

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["data"], events[0].sensorData)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

        # Make sure sensor data has changed.
        self.assertEqual(payload["payload"]["data"], sensor.sensorData)

    def test_output_handling_illegal_data(self):
        """
        Tests if output handling processing triggers a Sensor Alert for illegal data.
        """
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "executer_scripts",
                                  "mirror.py")
        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.timeout = 2
        sensor.intervalToCheck = 60
        sensor.parseOutput = True
        sensor.execute.append(target_cmd)
        sensor.execute.append("no json stuff")

        sensor.initialize()
        sensor.start()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        time.sleep(1.5)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].hasOptionalData)
        self.assertEqual("Illegal output", events[0].optionalData["message"])

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

    def test_output_handling_illegal_something(self):
        # TODO
        raise NotImplementedError("TODO: error handling in output parsing")
