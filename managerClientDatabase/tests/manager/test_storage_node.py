import logging
from tests.util import config_logging
from tests.manager.core import TestManagerStorageCore
from tests.globalData.util import compare_nodes_content, compare_alerts_content, compare_managers_content, \
                                  compare_sensors_content
from lib.globalData.globalData import SystemData
from lib.globalData.localObjects import Node
from lib.manager.storage import Mysql


class TestManagerStorageNode(TestManagerStorageCore):

    def _create_objects(self, storage: Mysql, system_data: SystemData):
        storage._open_connection()
        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)

        for node in system_data.get_nodes_list():
            storage._update_node(node)
            if node.nodeType.lower() == "alert":
                for alert in system_data.get_alerts_list():
                    if alert.nodeId == node.nodeId:
                        storage._update_alert(alert)

            elif node.nodeType.lower() == "manager":
                for manager in system_data.get_managers_list():
                    if manager.nodeId == node.nodeId:
                        storage._update_manager(manager)

            elif node.nodeType.lower() in ["sensor", "server"]:
                for sensor in system_data.get_sensors_list():
                    if sensor.nodeId == node.nodeId:
                        storage._update_sensor(sensor)
        storage._conn.commit()

    def test_add_node(self):
        """
        Tests adding of nodes to the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_nodes_content(self,
                              system_data.get_nodes_list(),
                              storage._system_data.get_nodes_list())

    def test_update_node(self):
        """
        Tests updating of nodes in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        # Update local objects.
        ctr = 0
        for node in system_data.get_nodes_list():
            temp_node = Node().deepcopy(node)
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

        # Update database objects.
        storage._open_connection()
        for node in system_data.get_nodes_list():
            storage._update_node(node)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_nodes_content(self,
                              system_data.get_nodes_list(),
                              storage._system_data.get_nodes_list())

        # Update function of database also deletes all Alert, Manager, and Sensor objects if node type changes.
        compare_alerts_content(self,
                               system_data.get_alerts_list(),
                               storage._system_data.get_alerts_list())
        compare_managers_content(self,
                                 system_data.get_managers_list(),
                                 storage._system_data.get_managers_list())
        compare_sensors_content(self,
                                system_data.get_sensors_list(),
                                storage._system_data.get_sensors_list())

    def test_delete_node(self):
        """
        Tests deleting of nodes in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        # Delete object and check correct deletion.
        for node in system_data.get_nodes_list():
            storage._open_connection()
            storage._delete_node(node.nodeId)
            storage._conn.commit()

            system_data.delete_node_by_id(node.nodeId)

            storage.synchronize_database_to_system_data()
            compare_nodes_content(self,
                                  system_data.get_nodes_list(),
                                  storage._system_data.get_nodes_list())

            # Delete function of database also deletes all Alert, Manager, and Sensor objects.
            compare_alerts_content(self,
                                   system_data.get_alerts_list(),
                                   storage._system_data.get_alerts_list())
            compare_managers_content(self,
                                     system_data.get_managers_list(),
                                     storage._system_data.get_managers_list())
            compare_sensors_content(self,
                                    system_data.get_sensors_list(),
                                    storage._system_data.get_sensors_list())
