import logging
from tests.util import config_logging
from tests.manager.core import TestManagerStorageCore
from tests.globalData.util import compare_options_content
from lib.globalData.globalData import GlobalData, SystemData
from lib.globalData.localObjects import Option


class TestManagerStorageOptions(TestManagerStorageCore):

    def test_add_option(self):
        """
        Tests adding of options to the database.
        """
        config_logging(logging.CRITICAL)

        storage = self._init_database()

        system_data = self._create_system_data()

        storage._open_connection()
        for option in system_data.get_options_list():
            storage._update_option(option)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_options_content(self,
                                system_data.get_options_list(),
                                storage._system_data.get_options_list())

    def test_update_option(self):
        """
        Tests updating of options in the database.
        """
        config_logging(logging.CRITICAL)

        storage = self._init_database()

        system_data = self._create_system_data()

        # Create database objects.
        storage._open_connection()
        for option in system_data.get_options_list():
            storage._update_option(option)
        storage._conn.commit()

        # Update local objects.
        ctr = 5
        for option in system_data.get_options_list():
            temp_option = Option().deepcopy(option)
            temp_option.value = float(ctr)
            system_data.update_option(temp_option)
            ctr += 1

        # Update database objects.
        storage._open_connection()
        for option in system_data.get_options_list():
            storage._update_option(option)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_options_content(self,
                                system_data.get_options_list(),
                                storage._system_data.get_options_list())

    def test_delete_option(self):
        """
        Tests deleting of options in the database.
        """
        config_logging(logging.CRITICAL)

        storage = self._init_database()

        system_data = self._create_system_data()

        # Create database objects.
        storage._open_connection()
        for option in system_data.get_options_list():
            storage._update_option(option)
        storage._conn.commit()

        # Delete object and check correct deletion.
        for option in system_data.get_options_list():
            storage._open_connection()
            storage._delete_option(option.type)
            storage._conn.commit()

            system_data.delete_option_by_type(option.type)

            storage.synchronize_database_to_system_data()
            compare_options_content(self,
                                    system_data.get_options_list(),
                                    storage._system_data.get_options_list())
