import logging
from typing import Any, List, Tuple, Optional, Dict
from collections import defaultdict
from unittest import TestCase
from lib.localObjects import SensorAlert, Option, Profile
from lib.internalSensors import ProfileChangeSensor
from lib.globalData import GlobalData
from lib.storage.core import _Storage


class MockSensorAlertExecuter:

    def __init__(self):
        self._sensor_alerts = list()  # type: List[SensorAlert]
        self.is_working = True

    @property
    def sensor_alerts(self) -> List[SensorAlert]:
        return self._sensor_alerts

    def add_sensor_alert(self,
                         node_id: int,
                         sensor_id: int,
                         state: int,
                         optional_data: Optional[Dict[str, Any]],
                         change_state: bool,
                         has_latest_data: bool,
                         data_type: int,
                         sensor_data: Any,
                         logger: logging.Logger = None) -> bool:

        if not self.is_working:
            return False

        sensor_alert = SensorAlert()
        sensor_alert.nodeId = node_id
        sensor_alert.sensorId = sensor_id
        sensor_alert.state = state
        sensor_alert.changeState = change_state
        sensor_alert.hasLatestData = has_latest_data
        sensor_alert.dataType = data_type
        sensor_alert.sensorData = sensor_data

        sensor_alert.hasOptionalData = False
        sensor_alert.optionalData = optional_data
        if optional_data:
            sensor_alert.hasOptionalData = True

        self._sensor_alerts.append(sensor_alert)
        return True


class MockStorage(_Storage):

    def __init__(self):
        self._options = list()
        self.is_working = True

        self._sensor_data = defaultdict(list)

    @property
    def sensor_data(self):
        return self._sensor_data

    def updateSensorData(self,
                         node_id: int,
                         data_list: List[Tuple[int, Any]],
                         logger: logging.Logger = None) -> bool:

        if not self.is_working:
            return False

        for data_set in data_list:
            self._sensor_data[node_id].append(data_set)

        return True


class TestProfileChange(TestCase):

    def _create_internal_sensor(self) -> Tuple[ProfileChangeSensor, GlobalData]:
        global_data = GlobalData()
        global_data.logger = logging.getLogger("Profile Change Test Case")
        global_data.sensorAlertExecuter = MockSensorAlertExecuter()

        global_data.storage = MockStorage()

        profile = Profile()
        profile.profileId = 1
        profile.name = "profile_1"
        global_data.profiles.append(profile)

        profile = Profile()
        profile.profileId = 2
        profile.name = "profile_2"
        global_data.profiles.append(profile)

        sensor = ProfileChangeSensor(global_data)
        sensor.initialize()
        sensor.data = 1
        sensor.nodeId = 1
        sensor.remoteSensorId = 2
        return sensor, global_data

    def test_base_process_option(self):
        """
        Tests basic processing of an option that contains a system profile change.
        """
        sensor, global_data = self._create_internal_sensor()

        option = Option()
        option.type = "profile"
        option.value = 2.0

        self.assertEqual(sensor.data, 1)

        sensor.process_option(option)

        self.assertEqual(sensor.data, 2)

        sensor_data = global_data.storage.sensor_data
        self.assertEqual(len(sensor_data.keys()), 1)
        self.assertTrue(sensor.nodeId in sensor_data.keys())

        data_list = sensor_data[sensor.nodeId]
        self.assertEqual(len(data_list), 1)
        self.assertEqual(data_list[0][0], sensor.remoteSensorId)
        self.assertEqual(data_list[0][1], sensor.data)

        sensor_alert_executer = global_data.sensorAlertExecuter
        self.assertEqual(len(sensor_alert_executer.sensor_alerts), 1)
        self.assertEqual(sensor_alert_executer.sensor_alerts[0].sensorData, int(option.value))

    def test_wrong_option_type(self):
        """
        Tests error handling of an option processing that is not for system profile changes.
        """
        sensor, global_data = self._create_internal_sensor()

        option = Option()
        option.type = "does_not_exist"
        option.value = 2.0

        self.assertEqual(sensor.data, 1)

        sensor.process_option(option)

        self.assertEqual(sensor.data, 1)

        sensor_data = global_data.storage.sensor_data
        self.assertEqual(len(sensor_data.keys()), 0)

        sensor_alert_executer = global_data.sensorAlertExecuter
        self.assertEqual(len(sensor_alert_executer.sensor_alerts), 0)

    def test_profile_does_not_exist(self):
        """
        Tests error handling of an option processing that contains a not existing profile.
        """
        sensor, global_data = self._create_internal_sensor()

        option = Option()
        option.type = "profile"
        option.value = 1337.0

        self.assertEqual(sensor.data, 1)

        sensor.process_option(option)

        self.assertEqual(sensor.data, 1)

        sensor_data = global_data.storage.sensor_data
        self.assertEqual(len(sensor_data.keys()), 0)

        sensor_alert_executer = global_data.sensorAlertExecuter
        self.assertEqual(len(sensor_alert_executer.sensor_alerts), 0)

    def test_faulty_storage(self):
        """
        Tests error handling of an option processing that has a faulty storage
        """
        sensor, global_data = self._create_internal_sensor()
        global_data.storage.is_working = False

        option = Option()
        option.type = "profile"
        option.value = 2.0

        self.assertEqual(sensor.data, 1)

        sensor.process_option(option)

        self.assertEqual(sensor.data, 1)

        sensor_data = global_data.storage.sensor_data
        self.assertEqual(len(sensor_data.keys()), 0)

        sensor_alert_executer = global_data.sensorAlertExecuter
        self.assertEqual(len(sensor_alert_executer.sensor_alerts), 0)

    def test_faulty_sensor_alert_executer(self):
        """
        Tests error handling of an option processing that has a faulty sensor alert executer.
        """
        sensor, global_data = self._create_internal_sensor()
        global_data.sensorAlertExecuter.is_working = False

        option = Option()
        option.type = "profile"
        option.value = 2.0

        self.assertEqual(sensor.data, 1)

        sensor.process_option(option)

        self.assertEqual(sensor.data, 2)

        sensor_data = global_data.storage.sensor_data
        self.assertEqual(len(sensor_data.keys()), 1)

        sensor_alert_executer = global_data.sensorAlertExecuter
        self.assertEqual(len(sensor_alert_executer.sensor_alerts), 0)
