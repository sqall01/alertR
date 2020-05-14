from unittest import TestCase
from lib.globalData.systemData import SystemData
from lib.localObjects import Node, Alert


class TestSystemDataAlert(TestCase):

    def test_invalid_alert_adding(self):
        """
        Tests sanity checks for Alert object adding.
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

        system_data = SystemData()

        # Test non-existing node.
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
            self.fail("Exception because of non-existing node expected.")

        # Test non-existing alert level.
        system_data = SystemData()

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
        alert.alertLevels = [1]
        alert.description = "alert_1"
        is_exception = False
        try:
            system_data.update_alert(alert)
        except ValueError:
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")
