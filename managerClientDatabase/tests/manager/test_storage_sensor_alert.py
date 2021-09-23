import logging
import time
from tests.util import config_logging
from tests.manager.core import TestManagerStorageCore
from tests.globalData.util import compare_sensor_alerts_content
from lib.globalData.globalData import SystemData
from lib.globalData.managerObjects import ManagerObjSensorAlert
from lib.manager.storage import Mysql


class TestManagerStorageSensorAlert(TestManagerStorageCore):

    def _create_objects(self, storage: Mysql, system_data: SystemData):
        storage._open_connection()
        for profile in system_data.get_profiles_list():
            storage._update_profile(profile)

        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)

        for sensor in system_data.get_sensors_list():
            node = system_data.get_node_by_id(sensor.nodeId)
            storage._update_node(node)
            storage._update_sensor(sensor)
        storage._conn.commit()

    def test_add_sensor_alert(self):
        """
        Tests adding of sensor alerts to the database.
        """

        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        sensor_list = system_data.get_sensors_list()
        for i in range(len(sensor_list)):
            target_sensor = sensor_list[i % len(sensor_list)]

            sensor_alert = ManagerObjSensorAlert()
            sensor_alert.sensorId = target_sensor.sensorId
            sensor_alert.state = (i % 2)
            sensor_alert.description = "Sensor Alert %d" % i
            sensor_alert.timeReceived = int(time.time())
            sensor_alert.alertLevels = list(target_sensor.alertLevels)
            sensor_alert.hasOptionalData = False
            sensor_alert.changeState = False
            sensor_alert.hasLatestData = False
            sensor_alert.dataType = sensor_list[i].dataType
            sensor_alert.data = sensor_list[i].data

            system_data.add_sensor_alert(sensor_alert)

        storage._open_connection()
        for sensor_alert in system_data.get_sensor_alerts_list():
            storage._add_sensor_alert(sensor_alert)
        storage._conn.commit()
        storage._close_connection()

        storage._open_connection()
        db_sensor_alerts = storage._get_sensor_alerts()
        storage._close_connection()

        compare_sensor_alerts_content(self,
                                      system_data.get_sensor_alerts_list(),
                                      db_sensor_alerts)

    def test_update_server_info_duplicate_sensor_alerts(self):
        """
        Tests adding of sensor alerts to the database via update_server_information duplicates sensor alerts.
        """

        config_logging(logging.ERROR)

        storage = self._init_database()
        storage._sensor_alert_life_span = 2147483647  # max signed 32bit integer

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        sensor_list = system_data.get_sensors_list()
        for i in range(len(sensor_list)):
            target_sensor = sensor_list[i % len(sensor_list)]

            sensor_alert = ManagerObjSensorAlert()
            sensor_alert.sensorId = target_sensor.sensorId
            sensor_alert.state = (i % 2)
            sensor_alert.description = "Sensor Alert %d" % i
            sensor_alert.timeReceived = int(time.time())
            sensor_alert.alertLevels = list(target_sensor.alertLevels)
            sensor_alert.hasOptionalData = False
            sensor_alert.changeState = False
            sensor_alert.hasLatestData = False
            sensor_alert.dataType = sensor_list[i].dataType
            sensor_alert.data = sensor_list[i].data

            system_data.add_sensor_alert(sensor_alert)

        storage.update_server_information(0,
                                          system_data.get_options_list(),
                                          system_data.get_profiles_list(),
                                          system_data.get_nodes_list(),
                                          system_data.get_sensors_list(),
                                          system_data.get_alerts_list(),
                                          system_data.get_managers_list(),
                                          system_data.get_alert_levels_list(),
                                          system_data.get_sensor_alerts_list())

        self.assertEqual(len(system_data.get_sensor_alerts_list()), len(sensor_list))

        # Add same list of sensor alerts again for duplication test.
        storage.update_server_information(0,
                                          system_data.get_options_list(),
                                          system_data.get_profiles_list(),
                                          system_data.get_nodes_list(),
                                          system_data.get_sensors_list(),
                                          system_data.get_alerts_list(),
                                          system_data.get_managers_list(),
                                          system_data.get_alert_levels_list(),
                                          system_data.get_sensor_alerts_list())

        storage._open_connection()
        db_sensor_alerts = storage._get_sensor_alerts()
        storage._close_connection()

        compare_sensor_alerts_content(self,
                                      system_data.get_sensor_alerts_list(),
                                      db_sensor_alerts)
