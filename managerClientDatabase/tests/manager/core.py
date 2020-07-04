import logging
import xml.etree.ElementTree
from tests.globalData.core import TestSystemDataCore
from lib.globalData.globalData import GlobalData
from lib.manager.storage import Mysql


class TestManagerStorageCore(TestSystemDataCore):

    def _init_database(self) -> Mysql:
        """
        Initializes database for testing.
        :return: storage object
        """
        global_data = GlobalData()

        storage = None
        try:
            config_root = xml.etree.ElementTree.parse(global_data.configFile).getroot()
            backend_username = str(config_root.find("manager").find("storage").attrib["username"])
            backend_password = str(config_root.find("manager").find("storage").attrib["password"])
            backend_server = str(config_root.find("manager").find("storage").attrib["server"])
            backend_port = int(config_root.find("manager").find("storage").attrib["port"])
            backend_database = str(config_root.find("manager").find("storage").attrib["database"])

            storage = Mysql(backend_server,
                            backend_port,
                            backend_database,
                            backend_username,
                            backend_password,
                            global_data)

            storage._open_connection()
            storage._delete_storage()
            storage._conn.commit()
            storage._close_connection()
            storage.create_storage()

        except Exception:
            logging.exception("Unable to initialize database.")
            self.skipTest("Unable to initialize database.")

        return storage
