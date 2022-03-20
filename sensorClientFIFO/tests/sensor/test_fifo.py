import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from unittest import TestCase
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange, SensorDataType, SensorDataNone, \
    SensorErrorState, SensorObjErrorStateChange
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

    def test_sensor_alert(self):
        """
        Tests if a Sensor Alert is triggered.
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
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": False,
                "changeState": True
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

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

        # Make sure sensor error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_state_change(self):
        """
        Tests if state change is processed correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

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
        sensor.data = SensorDataNone()
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(SensorDataNone.copy_from_dict(payload["payload"]["data"]), events[0].data)

        # Make sure sensor state has not changed.
        self.assertEqual(1, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_error_state_change(self):
        """
        Tests if error state change is processed correctly.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        payload = {
            "message": "errorstatechange",
            "payload": {
                "error_state": {
                    "state": SensorErrorState.GenericError,
                    "msg": "some msg"
                }
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        with open(fifo_file, 'w') as fp:
            fp.write(json.dumps(payload))

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["error_state"]["state"], SensorErrorState.GenericError)
        self.assertEqual(payload["payload"]["error_state"]["msg"], "some msg")

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure sensor error state has changed
        self.assertEqual(SensorErrorState.GenericError, sensor.error_state.state)
        self.assertEqual("some msg", sensor.error_state.msg)

    def test_data_processing_illegal_data(self):
        """
        Tests if data processing triggers an ProcessingError error state.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")
        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        sensor.initialize()

        sensor.start()

        time.sleep(0.5)

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        with open(fifo_file, 'w') as fp:
            fp.write("illegal data")

        time.sleep(1.0)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(SensorErrorState.ProcessingError, events[0].error_state.state)
        self.assertEqual("Received illegal data.", events[0].error_state.msg)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure sensor error state has changed
        self.assertEqual(SensorErrorState.ProcessingError, sensor.error_state.state)
        self.assertEqual("Received illegal data.", sensor.error_state.msg)

    def test_create_fifo(self):
        """
        Tests if creating a FIFO file retries if an error occurs.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        # Shorten wait time for retrying to create FIFO file to shorten the time the test needs.
        sensor._fifo_retry_time = 0.5

        # Delete directory to prevent creation of FIFO file.
        shutil.rmtree(self._temp_dir.name)

        thread = threading.Thread(target=sensor._create_fifo_file, daemon=True)
        thread.start()

        time.sleep(0.5)

        self.assertFalse(os.path.exists(fifo_file))

        # Create directory to enable FIFO file creation.
        os.mkdir(self._temp_dir.name)

        time.sleep(1.0)

        self.assertTrue(os.path.exists(fifo_file))
        self.assertFalse(thread.is_alive())

    def test_read_fifo(self):
        """
        Tests if data written into FIFO is stored correctly in queue.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        num_writes = 11

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        thread = threading.Thread(target=sensor._thread_read_fifo, daemon=True)
        thread.start()

        time.sleep(0.5)

        self.assertTrue(os.path.exists(fifo_file))

        for i in range(num_writes):
            with open(fifo_file, 'w') as fp:
                fp.write(str(i))

            # NOTE: the FIFO read would fail to distinguish the messages if too fast writes occur.
            # The reason for this is because we do not use a protocol which contains the length of
            # the message and thus we cannot differentiate messages if they are returned together while calling
            # read ones. We do not want to introduce a length into the protocol because it would destroy the easy
            # way to use "echo 'JSON_STUFF' > sensor.fifo" for the sensor. We distinguish messages by a newline.
            # Thus we need a short sleep period before we can continue writing to it without using newlines.
            time.sleep(0.5)

        time.sleep(0.5)

        self.assertEqual(num_writes, len(sensor._data_queue))
        for i in range(num_writes):
            self.assertEqual(str(i), sensor._data_queue[i])

    def test_read_fifo_newline(self):
        """
        Tests if data written into FIFO separated by a newline is correctly split.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")

        num_writes = 11

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        thread = threading.Thread(target=sensor._thread_read_fifo, daemon=True)
        thread.start()

        time.sleep(0.5)

        self.assertTrue(os.path.exists(fifo_file))

        for i in range(num_writes):
            with open(fifo_file, 'w') as fp:
                fp.write(str(i) + "\n")

        time.sleep(0.5)

        self.assertEqual(num_writes, len(sensor._data_queue))
        for i in range(num_writes):
            self.assertEqual(str(i), sensor._data_queue[i])

    def test_read_fifo_newline_multi_write(self):
        """
        Tests if data written into FIFO concurrently separated by a newline is correctly split.
        """
        fifo_file = os.path.join(self._temp_dir.name,
                                 "sensor1.fifo")
        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "fifo_scripts",
                                  "write_fifo.py")

        num_writes_per_process = 21
        num_processes = 4

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.umask = int("0000", 8)
        sensor.fifoFile = fifo_file

        thread = threading.Thread(target=sensor._thread_read_fifo, daemon=True)
        thread.start()

        time.sleep(0.5)

        self.assertTrue(os.path.exists(fifo_file))

        processes = []
        for i in range(num_processes):
            processes.append(subprocess.Popen([target_cmd, fifo_file,
                                               str(i*num_writes_per_process),
                                               str((i+1)*num_writes_per_process)]))

        for i in range(num_processes):
            processes[i].wait()

        self.assertEqual(num_processes * num_writes_per_process, len(sensor._data_queue))

        # Check if every value is unique.
        data_queue_set = set(map(lambda x: int(x), sensor._data_queue))
        self.assertEqual(num_processes * num_writes_per_process, len(data_queue_set))

        # Check if each written element is in data queue.
        for i in range(num_processes * num_writes_per_process):
            self.assertTrue(i in data_queue_set)
