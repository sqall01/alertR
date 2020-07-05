import logging
from tests.util import config_logging
from tests.manager.core import TestManagerStorageCore
from tests.globalData.util import compare_managers_content
from lib.globalData.globalData import SystemData
from lib.globalData.localObjects import Manager
from lib.manager.storage import Mysql


class TestManagerStorageManager(TestManagerStorageCore):

    def _create_objects(self, storage: Mysql, system_data: SystemData):
        storage._open_connection()
        for manager in system_data.get_managers_list():
            node = system_data.get_node_by_id(manager.nodeId)
            storage._update_node(node)
            storage._update_manager(manager)
        storage._conn.commit()

    def test_add_manager(self):
        """
        Tests adding of managers to the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_managers_content(self,
                                 system_data.get_managers_list(),
                                 storage._system_data.get_managers_list())

    def test_update_manager(self):
        """
        Tests updating of managers in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        # Update local objects.
        ctr = 0
        for manager in system_data.get_managers_list():
            temp_manager = Manager().deepcopy(manager)
            temp_manager.description = "new_manager_" + str(ctr + 1)
            system_data.update_manager(temp_manager)
            ctr += 1

        # Update database objects.
        storage._open_connection()
        for manager in system_data.get_managers_list():
            storage._update_manager(manager)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_managers_content(self,
                                 system_data.get_managers_list(),
                                 storage._system_data.get_managers_list())

    def test_delete_manager(self):
        """
        Tests deleting of managers in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        # Delete object and check correct deletion.
        for manager in system_data.get_managers_list():
            storage._open_connection()
            storage._delete_manager(manager.managerId)
            storage._conn.commit()

            system_data.delete_manager_by_id(manager.managerId)

            storage.synchronize_database_to_system_data()
            compare_managers_content(self,
                                     system_data.get_managers_list(),
                                     storage._system_data.get_managers_list())
