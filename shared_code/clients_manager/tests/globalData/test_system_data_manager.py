from tests.globalData.core import TestSystemDataCore
from lib.globalData.systemData import SystemData
from lib.localObjects import Node, Manager


class TestSystemDataManager(TestSystemDataCore):

    def _invalid_node_missing(self, system_data: SystemData):
        # Test non-existing node.
        manager = Manager()
        manager.nodeId = 99
        manager.managerId = 1
        manager.description = "manager_1"
        is_exception = False
        try:
            system_data.update_manager(manager)
        except ValueError:
            is_exception = True
        if not is_exception:
            self.fail("Exception because of non-existing node expected.")

    def _invalid_wrong_node_type(self, system_data: SystemData):
        # Test invalid node type.
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

    def test_invalid_manager_adding(self):
        """
        Tests sanity checks for Manager object adding.
        """
        system_data = SystemData()
        self._invalid_wrong_node_type(system_data)

        system_data = SystemData()
        self._invalid_node_missing(system_data)

    def test_invalid_manager_updating(self):
        """
        Tests sanity checks for Manager object updating.
        """
        system_data = self._create_system_data()
        self._invalid_wrong_node_type(system_data)

        system_data = self._create_system_data()
        self._invalid_node_missing(system_data)

    def test_update_manager(self):
        """
        Test Manager object updating.
        """
        system_data = self._create_system_data()

        # Create changes that should be copied to the stored object.
        new_managers = []
        for i in range(len(self.managers)):
            temp_manager = Manager().deepcopy(self.managers[i])
            temp_manager.description = "new_manager_" + str(i + 1)
            new_managers.append(temp_manager)

        for i in range(len(new_managers)):

            # Update store with new object data.
            temp_manager = new_managers[i]
            system_data.update_manager(temp_manager)

            gt_storage = []
            for j in range(i+1):
                gt_storage.append(new_managers[j])
            for j in range(i+1, len(new_managers)):
                gt_storage.append(self.managers[j])

            stored_managers = system_data.get_managers_list()
            if len(stored_managers) != len(gt_storage):
                self.fail("Wrong number of objects stored.")

            already_processed = []
            for stored_manager in stored_managers:
                found = False
                for gt_manager in gt_storage:
                    if stored_manager.nodeId == gt_manager.nodeId and stored_manager.managerId == gt_manager.managerId:
                        found = True

                        # Check which objects we already processed to see if we hold an object with
                        # duplicated values.
                        if gt_manager in already_processed:
                            self.fail()
                        already_processed.append(gt_manager)

                        # Only the content of the object should have changed, not the object itself.
                        if stored_manager == gt_manager:
                            self.fail("Store changed object, not content of existing object.")

                        if stored_manager.description != gt_manager.description:
                            self.fail("Stored object does not have correct content.")

                        break

                if not found:
                    self.fail("Not able to find modified Manager object.")

    def test_delete_manager(self):
        """
        Test Manager object deleting.
        """
        system_data = self._create_managers()

        for manager in system_data.get_managers_list():

            system_data.delete_manager_by_id(manager.managerId)

            if not manager.is_deleted():
                self.fail("Manager object not marked as deleted.")

            for stored_manager in system_data.get_managers_list():
                if stored_manager.is_deleted():
                    self.fail("Stored Manager object marked as deleted.")

                if manager.managerId == stored_manager.managerId:
                    self.fail("Store still contains Manager with id that was deleted.")
