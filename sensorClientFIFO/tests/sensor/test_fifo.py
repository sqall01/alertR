import json
import os
import tempfile
import time
from unittest import TestCase
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange, SensorDataType
from lib.sensor.fifo import FIFOSensor


class TestFifoSensor(TestCase):

    def _create_base_sensor(self) -> FIFOSensor:
        sensor = FIFOSensor()
        sensor.id = 1
        sensor.description = "Test Fifo"
        sensor.alertDelay = 0
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.triggerState = 1
        sensor.alertLevels = [1]
        self._sensors.append(sensor)
        return sensor

    def setUp(self):
        self._sensors = []
        self._temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        for sensor in self._sensors:
            sensor.exit()
        self._temp_dir.cleanup()

    def test_sensor_alert_triggered_state_change(self):
        """
        Tests if a Sensor Alert is triggered (with state change).
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": None,
                "hasLatestData": False,
                "changeState": True
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

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

    def test_sensor_alert_triggered_no_state_change(self):
        """
        Tests if a Sensor Alert is triggered (with no state change).
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": None,
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

    def test_sensor_alert_normal_state_change(self):
        """
        Tests if a Sensor Alert is triggered (with state change).
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 0,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": None,
                "hasLatestData": False,
                "changeState": True
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()
        sensor.state = 1

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(1, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has changed.
        self.assertEqual(0, sensor.state)

    def test_sensor_alert_normal_no_state_change(self):
        """
        Tests if a Sensor Alert is triggered (with no state change).
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 0,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": None,
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()
        sensor.state = 1

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(1, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has not changed.
        self.assertEqual(1, sensor.state)

    def test_sensor_alert_data_change(self):
        """
        Tests if a Sensor Alert is triggered (with data change).
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

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
        sensor.sensorData = 1
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has changed.
        self.assertEqual(payload["payload"]["data"], sensor.sensorData)

    def test_sensor_alert_no_data_change(self):
        """
        Tests if a Sensor Alert is triggered (with no data change).
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.INT,
                "data": 1337,
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.INT
        sensor.sensorData = 1
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data hasnot  changed.
        self.assertNotEqual(payload["payload"]["data"], sensor.sensorData)

    def test_state_change_triggered(self):
        """
        Tests if state change is processed correctly (state is changed to triggered).
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

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
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["data"], events[0].sensorData)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

    def test_state_change_normal(self):
        """
        Tests if state change is processed correctly (state is changed to normal).
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "statechange",
            "payload": {
                "state": 0,
                "dataType": SensorDataType.NONE,
                "data": None,
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()
        sensor.state = 1

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(1, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["data"], events[0].sensorData)

        # Make sure sensor state has changed.
        self.assertEqual(0, sensor.state)

    def test_state_change_data_change(self):
        """
        Tests if state change is processed correctly (data is changed).
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

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
        sensor.sensorData = 1
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

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

    def test_illegal_data(self):
        """
        Tests if illegal data is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = "no json at all"

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(payload)

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

    def test_wrong_type(self):
        """
        Tests if wrong message type is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "doesnotexist",
            "payload": {
                "state": 1,
                "dataType": SensorDataType.NONE,
                "data": None,
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

    def test_state_change_illegal_state(self):
        """
        Tests if an illegal state for a state change is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "statechange",
            "payload": {
                "state": 1337,
                "dataType": SensorDataType.NONE,
                "data": None,
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

    def test_state_change_illegal_data_type(self):
        """
        Tests if an illegal data type for a state change is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "statechange",
            "payload": {
                "state": 1,
                "dataType": SensorDataType.INT,
                "data": 1338,
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertIsNone(sensor.sensorData)

    def test_sensor_alert_illegal_state(self):
        """
        Tests if an illegal state for a Sensor Alert is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1337,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": None,
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

    def test_sensor_alert_illegal_data_type(self):
        """
        Tests if an illegal data type for a Sensor Alert is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.INT,
                "data": 1338,
                "hasLatestData": True,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertIsNone(sensor.sensorData)

    def test_sensor_alert_illegal_has_optional_data(self):
        """
        Tests if an illegal has optional data flag for a Sensor Alert is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": 1,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": None,
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertIsNone(sensor.sensorData)

    def test_sensor_alert_illegal_has_latest_data(self):
        """
        Tests if an illegal has latest data flag for a Sensor Alert is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": None,
                "hasLatestData": 1,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertIsNone(sensor.sensorData)

    def test_sensor_alert_illegal_change_state(self):
        """
        Tests if an illegal change state flag for a Sensor Alert is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": None,
                "hasLatestData": False,
                "changeState": 1
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertIsNone(sensor.sensorData)

    def test_sensor_alert_illegal_optional_data(self):
        """
        Tests if an illegal optional data for a Sensor Alert is handled correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": True,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": None,
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.sensorData = None
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertIsNone(sensor.sensorData)

# TODO
# - multiple writes into FIFO file to check \n split
