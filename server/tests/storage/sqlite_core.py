import tempfile
import os
import logging
import shutil
from unittest import TestCase
from typing import Optional, List
from lib.localObjects import Option
from lib.storage.sqlite import Sqlite
from lib.globalData.globalData import GlobalData


class TestStorageCore(TestCase):

    def _clean_up_storage(self):
        if self.temp_dir is not None:
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass

    def _create_options(self, storage: Optional[Sqlite] = None) -> Sqlite:

        if storage is None:
            self.addCleanup(self._clean_up_storage)

            self.temp_dir = tempfile.mkdtemp()
            self.global_data = GlobalData()
            self.global_data.storageBackendSqliteFile = os.path.join(self.temp_dir, "database.db")
            self.global_data.logger = logging.getLogger("server")

            storage = Sqlite(self.global_data.storageBackendSqliteFile,
                             self.global_data)
            self.options = []  # type: List[Option]

        # Account for implicit option "profile" which is created on storage creation.
        option = storage.get_option_by_type("profile")
        self.options.append(option)

        option = Option()
        option.type = "type_1"
        option.value = 1
        self.options.append(option)
        storage.update_option_by_obj(option)

        option = Option()
        option.type = "type_2"
        option.value = 2
        self.options.append(option)
        storage.update_option_by_obj(option)

        option = Option()
        option.type = "type_3"
        option.value = 3
        self.options.append(option)
        storage.update_option_by_obj(option)

        return storage
