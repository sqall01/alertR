from tests.globalData.core import TestSystemDataCore
from lib.globalData.systemData import SystemData
from lib.localObjects import Node, Alert


class TestSystemDataAlert(TestSystemDataCore):

    def _invalid_alert_level_missing(self, system_data: SystemData):
        # Test non-existing alert level.
        node = Node()
        node.nodeId = 1
        node.hostname = "hostname_1"
        node.nodeType = "alert"
        node.instance = "instance_1"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_1"
        node.persistent = 1
        system_data.update_node(node)

        alert = Alert()
        alert.nodeId = 1
        alert.alertId = 1
        alert.remoteAlertId = 1
        alert.alertLevels = [99]
        alert.description = "alert_1"
        is_exception = False
        try:
            system_data.update_alert(alert)
        except ValueError:
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")

    def _invalid_node_missing(self, system_data: SystemData):
        # Test non-existing node.
        alert = Alert()
        alert.nodeId = 99
        alert.alertId = 1
        alert.remoteAlertId = 1
        alert.alertLevels = []
        alert.description = "alert_1"
        is_exception = False
        try:
            system_data.update_alert(alert)
        except ValueError:
            is_exception = True
        if not is_exception:
            self.fail("Exception because of non-existing node expected.")

    def _invalid_wrong_node_type(self, system_data: SystemData):
        # Test wrong node type.
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

        alert = Alert()
        alert.nodeId = 1
        alert.alertId = 1
        alert.remoteAlertId = 1
        alert.alertLevels = []
        alert.description = "alert_1"
        is_exception = False
        try:
            system_data.update_alert(alert)
        except ValueError:
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")

    def test_invalid_alert_adding(self):
        """
        Tests sanity checks for Alert object adding.
        """
        system_data = SystemData()
        self._invalid_wrong_node_type(system_data)

        system_data = SystemData()
        self._invalid_node_missing(system_data)

        system_data = SystemData()
        self._invalid_alert_level_missing(system_data)

    def test_invalid_alert_updating(self):
        """
        Tests sanity checks for Alert object updating.
        """
        system_data = self._create_system_data()
        self._invalid_wrong_node_type(system_data)

        system_data = self._create_system_data()
        self._invalid_node_missing(system_data)

        system_data = self._create_system_data()
        self._invalid_alert_level_missing(system_data)

    def test_update_alert(self):
        """
        Test Alert object updating.
        """
        system_data = self._create_system_data()

        # Create changes that should be copied to the stored object.
        new_alerts = []
        for i in range(len(self.alerts)):
            temp_alert = Alert().deepCopy(self.alerts[i])
            temp_alert.description = "new_alert_" + str(i + 1)
            temp_alert.remoteAlertId = i
            # We started the alert levels in our test data with level 1.
            temp_alert.alertLevels = [(i % len(self.alert_levels)) + 1]
            new_alerts.append(temp_alert)

        for i in range(len(new_alerts)):

            # Update store with new object data.
            temp_alert = new_alerts[i]
            system_data.update_alert(temp_alert)

            gt_storage = []
            for j in range(i+1):
                gt_storage.append(new_alerts[j])
            for j in range(i+1, len(new_alerts)):
                gt_storage.append(self.alerts[j])

            stored_alerts = system_data.get_alerts_list()
            if len(stored_alerts) != len(gt_storage):
                self.fail("Wrong number of objects stored.")

            already_processed = []
            for stored_alert in stored_alerts:
                found = False
                for gt_alert in gt_storage:
                    if stored_alert.nodeId == gt_alert.nodeId and stored_alert.alertId == gt_alert.alertId:
                        found = True

                        # Check which objects we already processed to see if we hold an object with
                        # duplicated values.
                        if gt_alert in already_processed:
                            self.fail()
                        already_processed.append(gt_alert)

                        # Only the content of the object should have changed, not the object itself.
                        if stored_alert == gt_alert:
                            self.fail("Store changed object, not content of existing object.")

                        if (stored_alert.remoteAlertId != gt_alert.remoteAlertId
                                or stored_alert.description != gt_alert.description
                                or any(map(lambda x: x not in gt_alert.alertLevels, stored_alert.alertLevels))
                                or any(map(lambda x: x not in stored_alert.alertLevels, gt_alert.alertLevels))):

                            self.fail("Stored object does not have correct content.")

                        break

                if not found:
                    self.fail("Not able to find modified Alert object.")

    def test_delete_alert(self):
        """
        Test Alert object deleting.
        """
        system_data = self._create_system_data()

        for alert in system_data.get_alerts_list():

            system_data.delete_alert_by_id(alert.alertId)

            if not alert.is_deleted():
                self.fail("Alert object not marked as deleted.")

            for stored_alert in system_data.get_alerts_list():
                if stored_alert.is_deleted():
                    self.fail("Stored Alert object marked as deleted.")

                if alert.alertId == stored_alert.alertId:
                    self.fail("Store still contains Alert with id that was deleted.")
