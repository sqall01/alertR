from unittest import TestCase
from lib.globalData.systemData import SystemData
from lib.localObjects import Node, Manager


class TestSystemDataManager(TestCase):

    def test_invalid_manager_adding(self):
        """
        Tests sanity checks for Manager object adding.
        """

        # Test invalid node type.
        system_data = SystemData()

        node = Node()
        node.nodeId = 1
        node.hostname = "hostname_1"
        node.nodeType = "sensor"
        node.instance = "instance_1"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_1"
        node.persistent = 1
        system_data.update_node(node)

        manager = Manager()
        manager.nodeId = 1
        manager.managerId = 1
        manager.description = "manager_1"
        is_exception = False
        try:
            system_data.update_manager(manager)
        except ValueError:
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")

        system_data = SystemData()

        # Test non-existing node.
        manager = Manager()
        manager.nodeId = 1
        manager.managerId = 1
        manager.description = "manager_1"
        is_exception = False
        try:
            system_data.update_manager(manager)
        except ValueError:
            is_exception = True
        if not is_exception:
            self.fail("Exception because of non-existing node expected.")
