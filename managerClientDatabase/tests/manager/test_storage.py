import logging
from tests.util import config_logging
from tests.manager.core import TestManagerStorageCore
from tests.globalData.util import compare_nodes_content, compare_alerts_content, compare_managers_content, \
                                  compare_sensors_content, compare_alert_levels_content, compare_options_content, \
                                  compare_profiles_content
from lib.globalData.globalData import SystemData
from lib.globalData.managerObjects import ManagerObjNode, ManagerObjAlert, ManagerObjAlertLevel, ManagerObjManager, \
                                          ManagerObjSensor, ManagerObjOption, ManagerObjProfile
from lib.globalData.sensorObjects import SensorDataType, SensorDataInt


class TestManagerStorage(TestManagerStorageCore):

    def test_add_data(self):
        """
        Tests adding of system information to the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        # Create database objects.
        system_data = self._create_system_data()
        storage.update_server_information(0,
                                          system_data.get_options_list(),
                                          system_data.get_profiles_list(),
                                          system_data.get_nodes_list(),
                                          system_data.get_sensors_list(),
                                          system_data.get_alerts_list(),
                                          system_data.get_managers_list(),
                                          system_data.get_alert_levels_list(),
                                          [])

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_options_content(self,
                                system_data.get_options_list(),
                                storage._system_data.get_options_list())
        compare_profiles_content(self,
                                 system_data.get_profiles_list(),
                                 storage._system_data.get_profiles_list())
        compare_nodes_content(self,
                              system_data.get_nodes_list(),
                              storage._system_data.get_nodes_list())
        compare_alerts_content(self,
                               system_data.get_alerts_list(),
                               storage._system_data.get_alerts_list())
        compare_managers_content(self,
                                 system_data.get_managers_list(),
                                 storage._system_data.get_managers_list())
        compare_sensors_content(self,
                                system_data.get_sensors_list(),
                                storage._system_data.get_sensors_list())

    def test_update(self):
        """
        Tests updating of system information in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        # Create database objects.
        system_data = self._create_system_data()
        storage.update_server_information(0,
                                          system_data.get_options_list(),
                                          system_data.get_profiles_list(),
                                          system_data.get_nodes_list(),
                                          system_data.get_sensors_list(),
                                          system_data.get_alerts_list(),
                                          system_data.get_managers_list(),
                                          system_data.get_alert_levels_list(),
                                          [])

        # Update local objects.
        ctr = 0
        for option in system_data.get_options_list():
            temp_option = ManagerObjOption.deepcopy(option)
            temp_option.value = ctr
            system_data.update_option(temp_option)
            ctr += 1

        for profile in system_data.get_profiles_list():
            temp_profile = ManagerObjProfile.deepcopy(profile)
            temp_profile.name = "new_profile_" + str(ctr)
            system_data.update_profile(temp_profile)
            ctr += 1

        for alert_level in system_data.get_alert_levels_list():
            temp_alert_level = ManagerObjAlertLevel.deepcopy(alert_level)
            temp_alert_level.name = "new_alert_level_" + str(ctr + 1)
            temp_alert_level.instrumentation_active = (ctr % 2) == 0

            if temp_alert_level.instrumentation_active:
                temp_alert_level.instrumentation_cmd = "alert_level_instrumentation_" + str(ctr + 1)
                temp_alert_level.instrumentation_timeout = 123 + ctr

            system_data.update_alert_level(temp_alert_level)
            ctr += 1

        for node in system_data.get_nodes_list():
            temp_node = ManagerObjNode.deepcopy(node)
            temp_node.hostname = "new_hostname_" + str(ctr + 1)
            temp_node.nodeType = ["alert", "manager", "sensor", "server"][ctr % 4]
            temp_node.instance = "new_instance_" + str(ctr + 1)
            temp_node.connected = (ctr % 2)
            temp_node.version = float(5 + ctr)
            temp_node.rev = ctr
            temp_node.username = "new_username_" + str(ctr + 1)
            temp_node.persistent = (ctr % 2)
            system_data.update_node(temp_node)
            ctr += 1

        for alert in system_data.get_alerts_list():
            temp_alert = ManagerObjAlert.deepcopy(alert)
            temp_alert.description = "new_alert_" + str(ctr + 1)
            temp_alert.clientAlertId = ctr
            # We started the alert levels in our test data with level 1.
            temp_alert.alertLevels = [(ctr % len(system_data.get_alert_levels_list())) + 1]
            system_data.update_alert(temp_alert)
            ctr += 1

        for manager in system_data.get_managers_list():
            temp_manager = ManagerObjManager.deepcopy(manager)
            temp_manager.description = "new_manager_" + str(ctr + 1)
            system_data.update_manager(temp_manager)
            ctr += 1

        for sensor in system_data.get_sensors_list():
            temp_sensor = ManagerObjSensor.deepcopy(sensor)
            temp_sensor.description = "new_sensor_" + str(ctr + 1)
            temp_sensor.clientSensorId = ctr
            temp_sensor.alertDelay = ctr + 10
            temp_sensor.lastStateUpdated = ctr + 10
            temp_sensor.state = ctr % 2
            temp_sensor.dataType = SensorDataType.INT
            temp_sensor.data = SensorDataInt(ctr, "test unit")
            # We started the alert levels in our test data with level 1.
            temp_sensor.alertLevels = [(ctr % len(system_data.get_alert_levels_list())) + 1]
            system_data.update_sensor(temp_sensor)
            ctr += 1

        # Update database objects.
        storage.update_server_information(0,
                                          system_data.get_options_list(),
                                          system_data.get_profiles_list(),
                                          system_data.get_nodes_list(),
                                          system_data.get_sensors_list(),
                                          system_data.get_alerts_list(),
                                          system_data.get_managers_list(),
                                          system_data.get_alert_levels_list(),
                                          [])

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_options_content(self,
                                system_data.get_options_list(),
                                storage._system_data.get_options_list())
        compare_profiles_content(self,
                                 system_data.get_profiles_list(),
                                 storage._system_data.get_profiles_list())
        compare_nodes_content(self,
                              system_data.get_nodes_list(),
                              storage._system_data.get_nodes_list())
        compare_alerts_content(self,
                               system_data.get_alerts_list(),
                               storage._system_data.get_alerts_list())
        compare_managers_content(self,
                                 system_data.get_managers_list(),
                                 storage._system_data.get_managers_list())
        compare_sensors_content(self,
                                system_data.get_sensors_list(),
                                storage._system_data.get_sensors_list())
        compare_alert_levels_content(self,
                                     system_data.get_alert_levels_list(),
                                     storage._system_data.get_alert_levels_list())

    def test_delete_node(self):
        """
        Tests deleting of nodes in system information data in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        # Create database objects.
        system_data = self._create_system_data()
        storage.update_server_information(0,
                                          system_data.get_options_list(),
                                          system_data.get_profiles_list(),
                                          system_data.get_nodes_list(),
                                          system_data.get_sensors_list(),
                                          system_data.get_alerts_list(),
                                          system_data.get_managers_list(),
                                          system_data.get_alert_levels_list(),
                                          [])

        # Delete node objects (most complexity) and check correct deletion.
        for node in system_data.get_nodes_list():
            system_data.delete_node_by_id(node.nodeId)

            storage.update_server_information(0,
                                              system_data.get_options_list(),
                                              system_data.get_profiles_list(),
                                              system_data.get_nodes_list(),
                                              system_data.get_sensors_list(),
                                              system_data.get_alerts_list(),
                                              system_data.get_managers_list(),
                                              system_data.get_alert_levels_list(),
                                              [])

            storage.synchronize_database_to_system_data()
            compare_nodes_content(self,
                                  system_data.get_nodes_list(),
                                  storage._system_data.get_nodes_list())
            compare_alerts_content(self,
                                   system_data.get_alerts_list(),
                                   storage._system_data.get_alerts_list())
            compare_managers_content(self,
                                     system_data.get_managers_list(),
                                     storage._system_data.get_managers_list())
            compare_sensors_content(self,
                                    system_data.get_sensors_list(),
                                    storage._system_data.get_sensors_list())
            compare_alert_levels_content(self,
                                         system_data.get_alert_levels_list(),
                                         storage._system_data.get_alert_levels_list())

    def test_delete_alert_level(self):
        """
        Tests deleting of alert levels in system information data in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        # Create database objects.
        system_data = self._create_system_data()
        storage.update_server_information(0,
                                          system_data.get_options_list(),
                                          system_data.get_profiles_list(),
                                          system_data.get_nodes_list(),
                                          system_data.get_sensors_list(),
                                          system_data.get_alerts_list(),
                                          system_data.get_managers_list(),
                                          system_data.get_alert_levels_list(),
                                          [])

        # Delete alert level objects and check correct deletion.
        for alert_level in system_data.get_alert_levels_list():
            system_data.delete_alert_level_by_level(alert_level.level)

            storage.update_server_information(0,
                                              system_data.get_options_list(),
                                              system_data.get_profiles_list(),
                                              system_data.get_nodes_list(),
                                              system_data.get_sensors_list(),
                                              system_data.get_alerts_list(),
                                              system_data.get_managers_list(),
                                              system_data.get_alert_levels_list(),
                                              [])

            storage.synchronize_database_to_system_data()
            compare_nodes_content(self,
                                  system_data.get_nodes_list(),
                                  storage._system_data.get_nodes_list())
            compare_alerts_content(self,
                                   system_data.get_alerts_list(),
                                   storage._system_data.get_alerts_list())
            compare_managers_content(self,
                                     system_data.get_managers_list(),
                                     storage._system_data.get_managers_list())
            compare_sensors_content(self,
                                    system_data.get_sensors_list(),
                                    storage._system_data.get_sensors_list())
            compare_alert_levels_content(self,
                                         system_data.get_alert_levels_list(),
                                         storage._system_data.get_alert_levels_list())

    def test_delete_profile(self):
        """
        Tests deleting of profiles in system information data in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        # Create database objects.
        system_data = self._create_system_data()
        storage.update_server_information(0,
                                          system_data.get_options_list(),
                                          system_data.get_profiles_list(),
                                          system_data.get_nodes_list(),
                                          system_data.get_sensors_list(),
                                          system_data.get_alerts_list(),
                                          system_data.get_managers_list(),
                                          system_data.get_alert_levels_list(),
                                          [])

        # Delete profile objects and check correct deletion.
        for profile in system_data.get_profiles_list():
            system_data.delete_profile_by_id(profile.profileId)

            storage.update_server_information(0,
                                              system_data.get_options_list(),
                                              system_data.get_profiles_list(),
                                              system_data.get_nodes_list(),
                                              system_data.get_sensors_list(),
                                              system_data.get_alerts_list(),
                                              system_data.get_managers_list(),
                                              system_data.get_alert_levels_list(),
                                              [])

            storage.synchronize_database_to_system_data()
            compare_profiles_content(self,
                                     system_data.get_profiles_list(),
                                     storage._system_data.get_profiles_list())
            compare_nodes_content(self,
                                  system_data.get_nodes_list(),
                                  storage._system_data.get_nodes_list())
            compare_alerts_content(self,
                                   system_data.get_alerts_list(),
                                   storage._system_data.get_alerts_list())
            compare_managers_content(self,
                                     system_data.get_managers_list(),
                                     storage._system_data.get_managers_list())
            compare_sensors_content(self,
                                    system_data.get_sensors_list(),
                                    storage._system_data.get_sensors_list())
            compare_alert_levels_content(self,
                                         system_data.get_alert_levels_list(),
                                         storage._system_data.get_alert_levels_list())
