import logging
from tests.util import config_logging
from tests.manager.core import TestManagerStorageCore
from tests.globalData.util import compare_profiles_content
from lib.globalData.globalData import SystemData
from lib.globalData.managerObjects import ManagerObjProfile
from lib.manager.storage import Mysql


class TestManagerStorageAlertLevel(TestManagerStorageCore):

    def _create_objects(self, storage: Mysql, system_data: SystemData):
        storage._open_connection()
        for profile in system_data.get_profiles_list():
            storage._update_profile(profile)
        storage._conn.commit()

    def test_add_profile(self):
        """
        Tests adding of profiles to the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_profiles_content(self,
                                 system_data.get_profiles_list(),
                                 storage._system_data.get_profiles_list())

    def test_update_profile(self):
        """
        Tests updating of profiles in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        # Update local objects.
        ctr = 0
        for profile in system_data.get_profiles_list():
            temp_profile = ManagerObjProfile().deepcopy(profile)
            temp_profile.name = "new_profile" + str(ctr + 1)

            system_data.update_profile(temp_profile)
            ctr += 1

        # Update database objects.
        storage._open_connection()
        for profile in system_data.get_profiles_list():
            storage._update_profile(profile)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_profiles_content(self,
                                 system_data.get_profiles_list(),
                                 storage._system_data.get_profiles_list())

    def test_delete_profile(self):
        """
        Tests deleting of profiles in the database.
        """
        config_logging(logging.ERROR)

        storage = self._init_database()

        system_data = self._create_system_data()
        self._create_objects(storage, system_data)

        # Delete object and check correct deletion.
        for profile in system_data.get_profiles_list():
            storage._open_connection()
            storage._delete_profile(profile.id)
            storage._conn.commit()

            system_data.delete_profile_by_id(profile.id)

            storage.synchronize_database_to_system_data()
            compare_profiles_content(self,
                                     system_data.get_profiles_list(),
                                     storage._system_data.get_profiles_list())
