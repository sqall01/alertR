import logging
from tests.util import config_logging
from tests.manager.core import TestManagerStorageCore
from tests.globalData.util import compare_alerts_content
from lib.globalData.globalData import SystemData
from lib.globalData.localObjects import Alert


class TestManagerStorageAlerts(TestManagerStorageCore):

    def test_add_alert(self):
        """
        Tests adding of alerts to the database.
        """
        config_logging(logging.CRITICAL)

        storage = self._init_database()

        system_data = self._create_system_data()

        # Create database objects.
        storage._open_connection()
        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)

        for alert in system_data.get_alerts_list():
            node = system_data.get_node_by_id(alert.nodeId)
            storage._update_node(node)
            storage._update_alert(alert)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_alerts_content(self,
                               system_data.get_alerts_list(),
                               storage._system_data.get_alerts_list())

    def test_update_alert(self):
        """
        Tests updating of alerts in the database.
        """
        config_logging(logging.CRITICAL)

        storage = self._init_database()

        system_data = self._create_system_data()

        # Create database objects.
        storage._open_connection()
        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)

        for alert in system_data.get_alerts_list():
            node = system_data.get_node_by_id(alert.nodeId)
            storage._update_node(node)
            storage._update_alert(alert)
        storage._conn.commit()

        # Update local objects.
        ctr = 0
        for alert in system_data.get_alerts_list():
            temp_alert = Alert().deepcopy(alert)
            temp_alert.description = "new_alert_" + str(ctr + 1)
            temp_alert.remoteAlertId = ctr
            # We started the alert levels in our test data with level 1.
            temp_alert.alertLevels = [(ctr % len(self.alert_levels)) + 1]
            system_data.update_alert(temp_alert)
            ctr += 1

        # Update database objects.
        storage._open_connection()
        for alert in system_data.get_alerts_list():
            storage._update_alert(alert)
        storage._conn.commit()

        storage._system_data = SystemData()
        storage.synchronize_database_to_system_data()

        compare_alerts_content(self,
                               system_data.get_alerts_list(),
                               storage._system_data.get_alerts_list())

    def test_delete_alert(self):
        """
        Tests deleting of alerts in the database.
        """
        config_logging(logging.CRITICAL)

        storage = self._init_database()

        system_data = self._create_system_data()

        # Create database objects.
        storage._open_connection()
        for alert_level in system_data.get_alert_levels_list():
            storage._update_alert_level(alert_level)

        for alert in system_data.get_alerts_list():
            node = system_data.get_node_by_id(alert.nodeId)
            storage._update_node(node)
            storage._update_alert(alert)
        storage._conn.commit()

        # Delete object and check correct deletion.
        for alert in system_data.get_alerts_list():
            storage._open_connection()
            storage._delete_alert(alert.alertId)
            storage._conn.commit()

            system_data.delete_alert_by_id(alert.alertId)

            storage.synchronize_database_to_system_data()
            compare_alerts_content(self,
                                   system_data.get_alerts_list(),
                                   storage._system_data.get_alerts_list())
