from tests.globalData.core import TestSystemDataCore
from lib.globalData.systemData import SystemData
from lib.globalData.managerObjects import ManagerObjSensorAlert
from lib.globalData.sensorObjects import SensorDataType, SensorDataInt, SensorDataNone
from lib.globalData.baseObjects import InternalState


class TestSystemDataSensorAlert(TestSystemDataCore):

    @staticmethod
    def _callback_delete_sensor_alert(sensor_alert: ManagerObjSensorAlert) -> bool:
        return sensor_alert.internal_data["test_delete"]

    def _invalid_alert_level_missing(self, system_data: SystemData):
        # Test non-existing alert level.
        sensor_alert = ManagerObjSensorAlert()
        sensor_alert.sensorId = self.sensors[0].sensorId
        sensor_alert.state = 0
        sensor_alert.alertLevels = [99]
        sensor_alert.hasOptionalData = False
        sensor_alert.optionalData = None
        sensor_alert.changeState = True
        sensor_alert.hasLatestData = False
        sensor_alert.dataType = SensorDataType.NONE
        sensor_alert.data = SensorDataNone()
        sensor_alert.timeReceived = 0

        is_exception = False
        try:
            system_data.add_sensor_alert(sensor_alert)
        except ValueError as e:
            self.assertTrue("Alert Level" in str(e) and "corresponding to sensor alert does not exist" in str(e))
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")

    def _invalid_sensor_missing(self, system_data: SystemData):
        # Test non-existing sensor.
        sensor_alert = ManagerObjSensorAlert()
        sensor_alert.sensorId = 99
        sensor_alert.state = 0
        sensor_alert.alertLevels = [self.alert_levels[0].level]
        sensor_alert.hasOptionalData = False
        sensor_alert.optionalData = None
        sensor_alert.changeState = True
        sensor_alert.hasLatestData = False
        sensor_alert.dataType = SensorDataType.NONE
        sensor_alert.data = SensorDataNone()
        sensor_alert.timeReceived = 0

        is_exception = False
        try:
            system_data.add_sensor_alert(sensor_alert)
        except ValueError as e:
            self.assertTrue("Sensor" in str(e) and "corresponding to sensor alert does not exist" in str(e))
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")

    def _invalid_sensor_missing_alert_level(self, system_data: SystemData):
        # Test sensor does not handle alert level.
        sensor_alert = ManagerObjSensorAlert()
        sensor_alert.sensorId = self.sensors[0].sensorId
        sensor_alert.state = 0
        sensor_alert.alertLevels = []
        for alert_level in self.alert_levels:
            if alert_level.level not in self.sensors[0].alertLevels:
                sensor_alert.alertLevels.append(alert_level.level)
        sensor_alert.hasOptionalData = False
        sensor_alert.optionalData = None
        sensor_alert.changeState = True
        sensor_alert.hasLatestData = False
        sensor_alert.dataType = SensorDataType.NONE
        sensor_alert.data = SensorDataNone()
        sensor_alert.timeReceived = 0

        is_exception = False
        try:
            system_data.add_sensor_alert(sensor_alert)
        except ValueError as e:
            self.assertTrue("does not handle Alert Level" in str(e))
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")

    def _invalid_wrong_data_type(self, system_data: SystemData):
        # Test data type mismatch.
        sensor_alert = ManagerObjSensorAlert()
        sensor_alert.sensorId = self.sensors[0].sensorId
        sensor_alert.state = 0
        sensor_alert.alertLevels = [self.sensors[0].alertLevels[0]]
        sensor_alert.hasOptionalData = False
        sensor_alert.optionalData = None
        sensor_alert.changeState = True
        sensor_alert.hasLatestData = False
        sensor_alert.dataType = SensorDataType.INT
        sensor_alert.data = SensorDataInt(0, "test unit")
        sensor_alert.timeReceived = 0

        is_exception = False
        try:
            system_data.add_sensor_alert(sensor_alert)
        except ValueError as e:
            self.assertTrue("corresponding to sensor alert has different data type" in str(e))
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")

    def test_add_sensor_alert(self):
        """
        Test Sensor Alert object adding.
        """
        system_data = self._create_sensors()

        # Create objects that should be added.
        new_sensor_alerts = []
        for i in range(len(self.sensors)):
            temp_sensor_alert = ManagerObjSensorAlert()
            temp_sensor_alert.sensorId = self.sensors[i % len(self.sensors)].sensorId
            temp_sensor_alert.state = i % 2
            temp_sensor_alert.alertLevels = list(self.sensors[i % len(self.sensors)].alertLevels)
            temp_sensor_alert.hasOptionalData = False
            temp_sensor_alert.optionalData = None
            temp_sensor_alert.changeState = (i % 2) == 0
            temp_sensor_alert.hasLatestData = False
            temp_sensor_alert.dataType = self.sensors[i % len(self.sensors)].dataType
            temp_sensor_alert.data = self.sensors[i % len(self.sensors)].data
            temp_sensor_alert.timeReceived = i + 5
            new_sensor_alerts.append(temp_sensor_alert)

        for i in range(len(new_sensor_alerts)):

            # Add new object to store.
            temp_sensor_alert = new_sensor_alerts[i]
            system_data.add_sensor_alert(temp_sensor_alert)

            if temp_sensor_alert.internal_state != InternalState.STORED:
                self.fail("Sensor Alert object not stored in storage.")

            stored_sensor_alerts = system_data.get_sensor_alerts_list()
            if len(stored_sensor_alerts) != (i + 1):
                self.fail("Wrong number of objects stored.")

            latest_received = -1
            for stored_sensor_alerts in stored_sensor_alerts:

                if latest_received > stored_sensor_alerts.timeReceived:
                    self.fail("Sensor Alerts not stored in correct order.")

    def test_delete_sensor_alerts_received_before(self):
        """
        Test Sensor Alert object deleting for sensor alerts with a received time before a given timestamp.
        """
        number_sensor_alerts = 10
        system_data = self._create_sensors()

        # Create objects.
        new_sensor_alerts = []
        for i in range(number_sensor_alerts):
            temp_sensor_alert = ManagerObjSensorAlert()
            temp_sensor_alert.sensorId = self.sensors[i % len(self.sensors)].sensorId
            temp_sensor_alert.state = i % 2
            temp_sensor_alert.alertLevels = list(self.sensors[i % len(self.sensors)].alertLevels)
            temp_sensor_alert.hasOptionalData = False
            temp_sensor_alert.optionalData = None
            temp_sensor_alert.changeState = (i % 2) == 0
            temp_sensor_alert.hasLatestData = False
            temp_sensor_alert.dataType = self.sensors[i % len(self.sensors)].dataType
            temp_sensor_alert.data = self.sensors[i % len(self.sensors)].data
            temp_sensor_alert.timeReceived = i
            new_sensor_alerts.append(temp_sensor_alert)
            system_data.add_sensor_alert(temp_sensor_alert)

        for i in range(int(number_sensor_alerts / 2), (number_sensor_alerts + 1)):

            system_data.delete_sensor_alerts_received_before(i)

            for j in range(i):
                if not new_sensor_alerts[j].is_deleted():
                    self.fail("Sensor Alert object not marked as deleted.")

            for j in range(i, number_sensor_alerts):
                if new_sensor_alerts[j].is_deleted():
                    self.fail("Sensor Alert object marked as deleted.")

            for sensor_alert in system_data.get_sensor_alerts_list():
                if sensor_alert.timeReceived < i:
                    self.fail("Sensor Alert object still stored that is younger than deleted timestamp.")

    def test_delete_sensor_alerts_with_callback(self):
        """
        Test Sensor Alert object deleting with callback function.
        """
        number_sensor_alerts = 10
        system_data = self._create_sensors()

        # Create objects.
        all_sensor_alerts = []
        to_delete_sensor_alerts = []
        to_remain_sensor_alerts = []
        for i in range(number_sensor_alerts):
            temp_sensor_alert = ManagerObjSensorAlert()
            temp_sensor_alert.sensorId = self.sensors[i % len(self.sensors)].sensorId
            temp_sensor_alert.state = i % 2
            temp_sensor_alert.alertLevels = list(self.sensors[i % len(self.sensors)].alertLevels)
            temp_sensor_alert.hasOptionalData = False
            temp_sensor_alert.optionalData = None
            temp_sensor_alert.changeState = (i % 2) == 0
            temp_sensor_alert.hasLatestData = False
            temp_sensor_alert.dataType = self.sensors[i % len(self.sensors)].dataType
            temp_sensor_alert.data = self.sensors[i % len(self.sensors)].data
            temp_sensor_alert.timeReceived = i
            all_sensor_alerts.append(temp_sensor_alert)
            if i % 2 == 0:
                to_delete_sensor_alerts.append(temp_sensor_alert)
                temp_sensor_alert.internal_data["test_delete"] = True
            else:
                to_remain_sensor_alerts.append(temp_sensor_alert)
                temp_sensor_alert.internal_data["test_delete"] = False
            system_data.add_sensor_alert(temp_sensor_alert)

        system_data.delete_sensor_alerts_with_callback(TestSystemDataSensorAlert._callback_delete_sensor_alert)

        self.assertEqual(len(system_data.get_sensor_alerts_list()), len(to_remain_sensor_alerts))

        for sensor_alert in to_delete_sensor_alerts:
            self.assertTrue(sensor_alert.is_deleted())

        for sensor_alert in to_remain_sensor_alerts:
            self.assertFalse(sensor_alert.is_deleted())

        for sensor_alert in system_data.get_sensor_alerts_list():
            self.assertTrue(sensor_alert in to_remain_sensor_alerts)

    def test_invalid_sensor_alert_adding(self):
        """
        Tests sanity checks for Sensor Alert object adding.
        """
        system_data = self._create_sensors()
        self._invalid_alert_level_missing(system_data)

        system_data = self._create_sensors()
        self._invalid_sensor_missing(system_data)

        system_data = self._create_sensors()
        self._invalid_sensor_missing_alert_level(system_data)

        system_data = self._create_sensors()
        self._invalid_wrong_data_type(system_data)
