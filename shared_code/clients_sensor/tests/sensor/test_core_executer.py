import time
from unittest import TestCase
from .core import MockServerCommunication, MockSensors
from lib.globalData.globalData import GlobalData
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange, SensorDataType
from lib.sensor.core import SensorExecuter


class TestSensorExecuter(TestCase):

    def setUp(self):
        self._sensors = []
        self._sensors.append(MockSensors())
        self._communication = MockServerCommunication()

        self._global_data = GlobalData()
        self._global_data.serverComm = self._communication
        self._global_data.sensors = list(self._sensors)

        self._sensor_executer = SensorExecuter(self._global_data)
        self._sensor_executer.daemon = True

    def tearDown(self):
        self._sensor_executer.exit()

    def test_event_triggered(self):
        """
        Tests the correct processing of Sensor Alerts and state changes for one sensor as well as the correct order.
        """
        num_events = 11
        self._sensor_executer.start()

        time.sleep(1)

        self.assertEqual(len(self._communication.send_sensor_alerts), 0)
        self.assertEqual(len(self._communication.send_state_changes), 0)

        sensor = self._sensors[0]
        gt_events_list = []
        num_sensor_alerts = 0
        num_state_changes = 0
        for i in range(num_events):
            if i % 2 == 0:
                sensor_alert = SensorObjSensorAlert()
                sensor_alert.clientSensorId = i
                sensor_alert.state = 1
                sensor_alert.hasOptionalData = False
                sensor_alert.changeState = False
                sensor_alert.hasLatestData = False
                sensor_alert.dataType = SensorDataType.NONE
                sensor.add_sensor_alert(sensor_alert)
                gt_events_list.append(sensor_alert)
                num_sensor_alerts += 1

            else:
                state_change = SensorObjStateChange()
                state_change.clientSensorId = i
                state_change.state = 1
                state_change.dataType = SensorDataType.NONE
                sensor.add_state_change(state_change)
                gt_events_list.append(state_change)
                num_state_changes += 1

        time.sleep(1)

        self.assertEqual(len(self._communication.send_sensor_alerts), num_sensor_alerts)
        self.assertEqual(len(self._communication.send_state_changes), num_state_changes)

        # Order send send events.
        ordered_events = []
        ordered_events.extend(self._communication.send_sensor_alerts)
        ordered_events.extend(self._communication.send_state_changes)
        ordered_events.sort(key=lambda data_tuple: data_tuple[0])

        for i in range(len(gt_events_list)):
            self.assertEqual(gt_events_list[i].clientSensorId, ordered_events[i][1].clientSensorId)

    def test_event_triggered_no_connection(self):
        """
        Tests waiting of processing until connection is available.
        """
        num_events = 5
        self._communication._is_connected = False
        self._sensor_executer.start()

        time.sleep(1)

        self.assertEqual(len(self._communication.send_sensor_alerts), 0)
        self.assertEqual(len(self._communication.send_state_changes), 0)

        sensor = self._sensors[0]
        gt_events_list = []
        num_sensor_alerts = 0
        num_state_changes = 0
        for i in range(num_events):
            if i % 2 == 0:
                sensor_alert = SensorObjSensorAlert()
                sensor_alert.clientSensorId = i
                sensor_alert.state = 1
                sensor_alert.hasOptionalData = False
                sensor_alert.changeState = False
                sensor_alert.hasLatestData = False
                sensor_alert.dataType = SensorDataType.NONE
                sensor.add_sensor_alert(sensor_alert)
                gt_events_list.append(sensor_alert)
                num_sensor_alerts += 1

            else:
                state_change = SensorObjStateChange()
                state_change.clientSensorId = i
                state_change.state = 1
                state_change.dataType = SensorDataType.NONE
                sensor.add_state_change(state_change)
                gt_events_list.append(state_change)
                num_state_changes += 1

        time.sleep(1)

        self.assertEqual(len(self._communication.send_sensor_alerts), 0)
        self.assertEqual(len(self._communication.send_state_changes), 0)

        self._communication._is_connected = True
        time.sleep(1)

        self.assertEqual(len(self._communication.send_sensor_alerts), num_sensor_alerts)
        self.assertEqual(len(self._communication.send_state_changes), num_state_changes)

    def test_full_state_update_interval(self):
        """
        Tests if in the given interval a full state update of the sensors is sent to the server.
        """
        self._sensor_executer._full_state_interval = 3
        self._sensor_executer.start()

        time.sleep(0.5)

        # Check if initial full state interval was sent (which is directly send when executer starts).
        self.assertEqual(1, len(self._communication.send_sensors_status_updates))

        time.sleep(self._sensor_executer._full_state_interval + 2)

        self.assertEqual(2, len(self._communication.send_sensors_status_updates))
