from lib.globalData.baseObjects import InternalState
from tests.globalData.core import TestSystemDataCore


class TestSystemDataGeneral(TestSystemDataCore):

    def test_valid_creation(self):
        system_data = self._create_system_data()

        # Check if created options are stored.
        stored_options = system_data.get_options_list()
        for created_option in self.options:
            found = False
            for stored_option in stored_options:
                if (stored_option.type == created_option.type
                        and stored_option.internal_state == InternalState.STORED):
                    found = True
                    break
            if not found:
                self.fail("Option %s not stored." % created_option.type)

        # Check if created alert levels are stored.
        stored_alert_levels = system_data.get_alert_levels_list()
        for created_alert_level in self.alert_levels:
            found = False
            for stored_alert_level in stored_alert_levels:
                if (stored_alert_level.level == created_alert_level.level
                        and stored_alert_level.internal_state == InternalState.STORED):
                    found = True
                    break
            if not found:
                self.fail("Alert Level %d not stored." % created_alert_level.level)

        # Check if created nodes are stored.
        stored_nodes = system_data.get_nodes_list()
        for created_node in self.nodes:
            found = False
            for stored_node in stored_nodes:
                if (stored_node.nodeId == created_node.nodeId
                        and stored_node.internal_state == InternalState.STORED):
                    found = True
                    break
            if not found:
                self.fail("Node %d not stored." % created_node.nodeId)

        # Check if created alerts are stored.
        stored_alerts = system_data.get_alerts_list()
        for created_alert in self.alerts:
            found = False
            for stored_alert in stored_alerts:
                if (stored_alert.nodeId == created_alert.nodeId
                        and stored_alert.alertId == created_alert.alertId
                        and stored_alert.internal_state == InternalState.STORED):
                    found = True
                    break
            if not found:
                self.fail("Alert %d not stored." % created_alert.alertId)

        # Check if created managers are stored.
        stored_managers = system_data.get_managers_list()
        for created_manager in self.managers:
            found = False
            for stored_manager in stored_managers:
                if (stored_manager.nodeId == created_manager.nodeId
                        and stored_manager.managerId == created_manager.managerId
                        and stored_manager.internal_state == InternalState.STORED):
                    found = True
                    break
            if not found:
                self.fail("Manager %d not stored." % created_manager.managerId)

        # Check if created sensors are stored.
        stored_sensors = system_data.get_sensors_list()
        for created_sensor in self.sensors:
            found = False
            for stored_sensor in stored_sensors:
                if (stored_sensor.nodeId == created_sensor.nodeId
                        and stored_sensor.sensorId == created_sensor.sensorId
                        and stored_sensor.internal_state == InternalState.STORED):
                    found = True
                    break
            if not found:
                self.fail("Sensor %d not stored." % created_sensor.sensorId)
