from tests.globalData.core import TestSystemDataCore
from tests.globalData.util import compare_alerts_content
from lib.globalData.systemData import SystemData
from lib.globalData.managerObjects import ManagerObjNode, ManagerObjAlert


class TestSystemDataAlert(TestSystemDataCore):

    def _invalid_alert_level_missing(self, system_data: SystemData):
        # Test non-existing alert level.
        node = ManagerObjNode()
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

        alert = ManagerObjAlert()
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
        alert = ManagerObjAlert()
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
        node = ManagerObjNode()
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

        alert = ManagerObjAlert()
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
            temp_alert = ManagerObjAlert().deepcopy(self.alerts[i])
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
            compare_alerts_content(self, gt_storage, stored_alerts)

    def test_delete_alert(self):
        """
        Test Alert object deleting.
        """
        system_data = self._create_alerts()

        for alert in system_data.get_alerts_list():

            system_data.delete_alert_by_id(alert.alertId)

            if not alert.is_deleted():
                self.fail("Alert object not marked as deleted.")

            for stored_alert in system_data.get_alerts_list():
                if stored_alert.is_deleted():
                    self.fail("Stored Alert object marked as deleted.")

                if alert.alertId == stored_alert.alertId:
                    self.fail("Store still contains Alert with id that was deleted.")
