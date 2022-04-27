import logging
from tests.util import config_logging
from tests.storage.sqlite_core import TestStorageCore
from tests.storage.util import compare_sensors_content
from lib.localObjects import Sensor
from lib.globalData.sensorObjects import SensorErrorState, SensorDataInt, SensorDataFloat, SensorDataGPS, \
    SensorDataType, SensorDataNone


class TestStorageSensor(TestStorageCore):

    def test_delete_sensor(self):
        """
        Test deleting Sensor objects.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId
        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        compare_sensors_content(self, self.sensors, init_db_sensors)

        removed_sensors = []
        remaining_sensors = list(self.sensors)
        for i in range(len(self.sensors)):
            sensor = self.sensors[i]
            self.assertTrue(storage.delete_sensor(sensor.sensorId))
            removed_sensors.append(sensor)
            remaining_sensors.remove(sensor)

            curr_db_sensors = storage.get_sensors(node_id)

            self.assertEqual(len(self.sensors) - i - 1, len(curr_db_sensors))

            # Check removed sensors are no longer stored in database.
            for curr_db_sensor in curr_db_sensors:
                self.assertFalse(any([obj.sensorId == curr_db_sensor.sensorId for obj in removed_sensors]))

            compare_sensors_content(self, remaining_sensors, curr_db_sensors)

    def test_upsert_sensor_update(self):
        """
        Test update of Sensor object.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId
        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        compare_sensors_content(self, self.sensors, init_db_sensors)

        for sensor in self.sensors:
            sensor.description += "_change"
            sensor.state = 1 - sensor.state
            sensor.error_state = SensorErrorState(SensorErrorState.GenericError,
                                                  "test error")
            sensor.alertLevels.append(2)
            sensor.lastStateUpdated += 1
            sensor.alertDelay += 2
            if sensor.dataType == SensorDataType.INT:
                sensor.data = SensorDataInt(1337, "some unit")
            elif sensor.dataType == SensorDataType.FLOAT:
                sensor.data = SensorDataFloat(1337.0, "some other unit")
            elif sensor.dataType == SensorDataType.GPS:
                sensor.data = SensorDataGPS(1337.0, 1337.0, 1337)

            self.assertTrue(storage.upsert_sensor(sensor))

            curr_db_sensors = storage.get_sensors(node_id)

            compare_sensors_content(self, self.sensors, curr_db_sensors)

    def test_upsert_sensor_insert(self):
        """
        Test insert of Sensor object.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId

        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        new_sensor = Sensor()
        new_sensor.nodeId = node_id
        new_sensor.clientSensorId = 1337
        new_sensor.description = "sensor_new"
        new_sensor.state = 0
        new_sensor.error_state = SensorErrorState()
        new_sensor.alertLevels.append(1337)
        new_sensor.lastStateUpdated = 1337
        new_sensor.alertDelay = 1337
        new_sensor.dataType = SensorDataType.NONE
        new_sensor.data = SensorDataNone()

        self.assertTrue(storage.upsert_sensor(new_sensor))
        new_sensor.sensorId = storage.getSensorId(new_sensor.nodeId, new_sensor.clientSensorId)
        self.sensors.append(new_sensor)

        curr_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors) + 1, len(curr_db_sensors))

        compare_sensors_content(self, self.sensors, curr_db_sensors)

    def test_upsert_sensors_update(self):
        """
        Test update of Sensor objects.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId
        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        compare_sensors_content(self, self.sensors, init_db_sensors)

        for sensor in self.sensors:
            sensor.description += "_change"
            sensor.state = 1 - sensor.state
            sensor.error_state = SensorErrorState(SensorErrorState.GenericError,
                                                  "test error")
            sensor.alertLevels.append(2)
            sensor.lastStateUpdated += 1
            sensor.alertDelay += 2
            if sensor.dataType == SensorDataType.INT:
                sensor.data = SensorDataInt(1337, "some unit")
            elif sensor.dataType == SensorDataType.FLOAT:
                sensor.data = SensorDataFloat(1337.0, "some other unit")
            elif sensor.dataType == SensorDataType.GPS:
                sensor.data = SensorDataGPS(1337.0, 1337.0, 1337)

            self.assertTrue(storage.upsert_sensors(self.sensors))

            curr_db_sensors = storage.get_sensors(node_id)

            compare_sensors_content(self, self.sensors, curr_db_sensors)

    def test_upsert_sensors_insert(self):
        """
        Test insert of Sensor objects.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId

        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        new_sensor = Sensor()
        new_sensor.nodeId = node_id
        new_sensor.clientSensorId = 1337
        new_sensor.description = "sensor_new"
        new_sensor.state = 0
        new_sensor.error_state = SensorErrorState()
        new_sensor.alertLevels.append(1337)
        new_sensor.lastStateUpdated = 1337
        new_sensor.alertDelay = 1337
        new_sensor.dataType = SensorDataType.NONE
        new_sensor.data = SensorDataNone()

        self.sensors.append(new_sensor)

        self.assertTrue(storage.upsert_sensors(self.sensors))

        curr_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors) + 1, len(curr_db_sensors))

        # Update sensor id in sensor object since it only gets assigned from the database.
        for curr_db_sensor in curr_db_sensors:
            if curr_db_sensor.clientSensorId == new_sensor.clientSensorId:
                new_sensor.sensorId = curr_db_sensor.sensorId
                break

        compare_sensors_content(self, self.sensors, curr_db_sensors)

    def test_upsert_sensors_different_node_id(self):
        """
        Test error processing of upsert function if sensors have different node ids.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId

        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        new_sensor = Sensor()
        new_sensor.nodeId = node_id + 1
        new_sensor.clientSensorId = 1337
        new_sensor.description = "sensor_new"
        new_sensor.state = 0
        new_sensor.error_state = SensorErrorState()
        new_sensor.alertLevels.append(1337)
        new_sensor.lastStateUpdated = 1337
        new_sensor.alertDelay = 1337
        new_sensor.dataType = SensorDataType.NONE
        new_sensor.data = SensorDataNone()

        self.sensors.append(new_sensor)

        self.assertFalse(storage.upsert_sensors(self.sensors))

        curr_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(curr_db_sensors))

        compare_sensors_content(self, init_db_sensors, curr_db_sensors)

    def test_upsert_sensors_delete_sensors_not_in_list(self):
        """
        Test if sensors that are stored in database but not part of the argument list are deleted.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId
        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        compare_sensors_content(self, self.sensors, init_db_sensors)

        removed_sensors = []
        for i in range(len(init_db_sensors)):
            sensor = self.sensors[len(init_db_sensors) - 1 - i]
            self.sensors.remove(sensor)
            removed_sensors.append(sensor)

            if not self.sensors:
                break

            self.assertTrue(storage.upsert_sensors(self.sensors))

            curr_db_sensors = storage.get_sensors(node_id)

            compare_sensors_content(self, self.sensors, curr_db_sensors)

            self.assertEqual(len(init_db_sensors) - i - 1, len(curr_db_sensors))

            # Check removed sensors are no longer stored in database.
            for curr_db_sensor in curr_db_sensors:
                self.assertFalse(any([obj.sensorId == curr_db_sensor.sensorId for obj in removed_sensors]))

    def test_upsert_sensors_empty_list(self):
        """
        Test if sensors are not touched if an empty list is given.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId

        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        self.assertFalse(storage.upsert_sensors([]))

        curr_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(curr_db_sensors))

        compare_sensors_content(self, init_db_sensors, curr_db_sensors)

    def test_update_sensor_error_state(self):
        """
        Test update of error state.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId
        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        compare_sensors_content(self, self.sensors, init_db_sensors)

        for sensor in self.sensors:
            sensor.error_state = SensorErrorState(SensorErrorState.GenericError,
                                                  "test error")

            self.assertTrue(storage.update_sensor_error_state(sensor.nodeId,
                                                              sensor.clientSensorId,
                                                              sensor.error_state))

            curr_db_sensors = storage.get_sensors(node_id)

            compare_sensors_content(self, self.sensors, curr_db_sensors)

    def test_get_sensors_in_error_state(self):
        """
        Test getting sensor ids for sensors in an error state.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId
        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        compare_sensors_content(self, self.sensors, init_db_sensors)

        self.assertEqual(len(storage.get_sensor_ids_in_error_state()), 0)

        gt_in_error = set()
        for i in range(len(self.sensors)):
            sensor = self.sensors[i]
            sensor.error_state = SensorErrorState(SensorErrorState.GenericError,
                                                  "test error")
            gt_in_error.add(sensor.sensorId)

            self.assertTrue(storage.update_sensor_error_state(sensor.nodeId,
                                                              sensor.clientSensorId,
                                                              sensor.error_state))

            sensor_ids = storage.get_sensor_ids_in_error_state()
            self.assertEqual(len(sensor_ids), i + 1)

            self.assertEqual(gt_in_error, set(sensor_ids))

    def test_get_sensor_error_state(self):
        """
        Test getting sensor error state.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId
        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        compare_sensors_content(self, self.sensors, init_db_sensors)

        for sensor in self.sensors:

            init_error_state = storage.get_sensor_error_state(sensor.sensorId)

            self.assertEqual(init_error_state, sensor.error_state)

            sensor.error_state = SensorErrorState(SensorErrorState.GenericError,
                                                  "test error")

            self.assertTrue(storage.update_sensor_error_state(sensor.nodeId,
                                                              sensor.clientSensorId,
                                                              sensor.error_state))

            curr_error_state = storage.get_sensor_error_state(sensor.sensorId)

            self.assertEqual(curr_error_state, sensor.error_state)
            self.assertNotEqual(curr_error_state, init_error_state)

    def test_get_sensor_error_state_invalid_sensor_id(self):
        """
        Test getting sensor error state with invalid sensor id.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId
        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        compare_sensors_content(self, self.sensors, init_db_sensors)

        self.assertIsNone(storage.get_sensor_error_state(4567))
