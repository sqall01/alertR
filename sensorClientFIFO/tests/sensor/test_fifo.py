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
        self.assertEqual(1, events[0].state)

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
        self.assertEqual(1, events[0].state)

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
        self.assertEqual(0, events[0].state)

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
        self.assertEqual(0, events[0].state)

        # Make sure sensor state has not changed.
        self.assertEqual(1, sensor.state)


# TODO
# - multiple writes into FIFO file to check \n split
