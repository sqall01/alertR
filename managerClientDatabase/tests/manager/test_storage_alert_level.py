import logging
from tests.util import config_logging
from tests.manager.core import TestManagerStorageCore
from tests.globalData.util import compare_alert_levels_content
from lib.globalData.globalData import SystemData
from lib.globalData.managerObjects import ManagerObjAlertLevel
from lib.manager.storage import Mysql


class TestManagerStorageAlertLevel(TestManagerStorageCore):

    def _create_objects(self, storage: Mysql, system_data: SystemData):
        storage._open_connection()
        for profile in system_data.get_profiles_list():
            storage._update_profile(profile)

        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)
        storage._conn.commit()

    def test_add_alert_level(self):
        """
        Tests adding of alert levels to the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_alert_levels_content(self,
                                     system_data.get_alert_levels_list(),
                                     storage._system_data.get_alert_levels_list())

    def test_update_alert_level(self):
        """
        Tests updating of alert levels in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        # Update local objects.
        ctr = 0
        for alert_level in system_data.get_alert_levels_list():
            temp_alert_level = ManagerObjAlertLevel.deepcopy(alert_level)
            temp_alert_level.name = "new_alert_level" + str(ctr + 1)
            temp_alert_level.instrumentation_active = (((ctr+1) % 2) == 0)

            if temp_alert_level.instrumentation_active:
                temp_alert_level.instrumentation_cmd = "new_alert_level_instrumentation_" + str(ctr + 1)
                temp_alert_level.instrumentation_timeout = 543 + ctr

            system_data.update_alert_level(temp_alert_level)
            ctr += 1

        # Update database objects.
        storage._open_connection()
        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_alert_levels_content(self,
                                     system_data.get_alert_levels_list(),
                                     storage._system_data.get_alert_levels_list())

    def test_delete_alert_level(self):
        """
        Tests deleting of alert levels in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        # Delete object and check correct deletion.
        for alert_level in system_data.get_alert_levels_list():
            storage._open_connection()
            storage._delete_alert_level(alert_level.level)
            storage._conn.commit()

            system_data.delete_alert_level_by_level(alert_level.level)

            storage.synchronize_database_to_system_data()
            compare_alert_levels_content(self,
                                         system_data.get_alert_levels_list(),
                                         storage._system_data.get_alert_levels_list())
