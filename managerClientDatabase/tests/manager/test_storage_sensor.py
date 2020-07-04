import logging
from tests.util import config_logging
from tests.manager.core import TestManagerStorageCore
from tests.globalData.util import compare_sensors_content
from lib.globalData.globalData import SystemData
from lib.globalData.localObjects import Sensor, SensorDataType


class TestManagerStorageSensor(TestManagerStorageCore):

    def test_add_sensor(self):
        """
        Tests adding of sensors to the database.
        """
        config_logging(logging.CRITICAL)

        storage = self._init_database()

        system_data = self._create_system_data()

        # Create database objects.
        storage._open_connection()
        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)

        for sensor in system_data.get_sensors_list():
            node = system_data.get_node_by_id(sensor.nodeId)
            storage._update_node(node)
            storage._update_sensor(sensor)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_sensors_content(self,
                                system_data.get_sensors_list(),
                                storage._system_data.get_sensors_list())

    def test_update_sensor(self):
        """
        Tests updating of sensors in the database.
        """
        config_logging(logging.CRITICAL)

        storage = self._init_database()

        system_data = self._create_system_data()

        # Create database objects.
        storage._open_connection()
        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)

        for sensor in system_data.get_sensors_list():
            node = system_data.get_node_by_id(sensor.nodeId)
            storage._update_node(node)
            storage._update_sensor(sensor)
        storage._conn.commit()

        # Update local objects.
        ctr = 0
        for sensor in system_data.get_sensors_list():
            temp_sensor = Sensor().deepcopy(sensor)
            temp_sensor.description = "new_sensor_" + str(ctr + 1)
            temp_sensor.remoteSensorId = ctr
            temp_sensor.alertDelay = ctr + 10
            temp_sensor.lastStateUpdated = ctr + 10
            temp_sensor.state = ctr % 2
            temp_sensor.dataType = SensorDataType.INT
            temp_sensor.data = ctr
            # We started the alert levels in our test data with level 1.
            temp_sensor.alertLevels = [(ctr % len(system_data.get_alert_levels_list())) + 1]
            system_data.update_sensor(temp_sensor)
            ctr += 1

        # Update database objects.
        storage._open_connection()
        for sensor in system_data.get_sensors_list():
            storage._update_sensor(sensor)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_sensors_content(self,
                                system_data.get_sensors_list(),
                                storage._system_data.get_sensors_list())

    def test_delete_sensor(self):
        """
        Tests deleting of sensors in the database.
        """
        config_logging(logging.CRITICAL)

        storage = self._init_database()

        system_data = self._create_system_data()

        # Create database objects.
        storage._open_connection()
        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)

        for sensor in system_data.get_sensors_list():
            node = system_data.get_node_by_id(sensor.nodeId)
            storage._update_node(node)
            storage._update_sensor(sensor)
        storage._conn.commit()

        # Delete object and check correct deletion.
        for sensor in system_data.get_sensors_list():
            storage._open_connection()
            storage._delete_sensor(sensor.sensorId)
            storage._conn.commit()

            system_data.delete_sensor_by_id(sensor.sensorId)

            storage.synchronize_database_to_system_data()
            compare_sensors_content(self,
                                    system_data.get_sensors_list(),
                                    storage._system_data.get_sensors_list())
