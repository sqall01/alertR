from tests.globalData.core import TestSystemDataCore
from lib.globalData.managerObjects import ManagerObjNode
from lib.globalData.baseObjects import InternalState


class TestSystemDataNode(TestSystemDataCore):

    def test_change_node_type_alert(self):
        """
        Test if a change from an "alert" node type to another is handled correctly.
        """
        system_data = self._create_alert_levels()
        system_data = self._create_alerts(system_data)
        new_node_type = "sensor"

        for i in range(len(self.alerts)):
            alert = self.alerts[i]
            stored_alert = system_data.get_alert_by_id(alert.alertId)
            target_node = system_data.get_node_by_id(alert.nodeId)
            if target_node is None:
                self.fail("Node does not exist.")

            # Update node type.
            new_node = ManagerObjNode().deepcopy(target_node)
            new_node.nodeType = new_node_type
            system_data.update_node(new_node)

            if (len(self.alerts) - (i + 1)) != len(system_data.get_alerts_list()):
                self.fail("Wrong number of Alert objects stored.")

            if target_node.nodeType != new_node_type:
                self.fail("Node type update failed.")

            if len(self.nodes) != len(system_data.get_nodes_list()):
                self.fail("Number of stored nodes changed.")

            if stored_alert.internal_state != InternalState.DELETED:
                self.fail("Alert object state not set to DELETED.")

    def test_change_node_type_manager(self):
        """
        Test if a change from an "manager" node type to another is handled correctly.
        """
        system_data = self._create_managers()
        new_node_type = "sensor"

        for i in range(len(self.managers)):
            manager = self.managers[i]
            stored_manager = system_data.get_manager_by_id(manager.managerId)
            target_node = system_data.get_node_by_id(manager.nodeId)
            if target_node is None:
                self.fail("Node does not exist.")

            # Update node type.
            new_node = ManagerObjNode().deepcopy(target_node)
            new_node.nodeType = new_node_type
            system_data.update_node(new_node)

            if (len(self.managers) - (i + 1)) != len(system_data.get_managers_list()):
                self.fail("Wrong number of Manager objects stored.")

            if target_node.nodeType != new_node_type:
                self.fail("Node type update failed.")

            if len(self.nodes) != len(system_data.get_nodes_list()):
                self.fail("Number of stored nodes changed.")

            if stored_manager.internal_state != InternalState.DELETED:
                self.fail("Manager object state not set to DELETED.")

    def test_change_node_type_sensor(self):
        """
        Test if a change from an "sensor" node type to another is handled correctly.
        """
        system_data = self._create_alert_levels()
        system_data = self._create_sensors(system_data)
        new_node_type = "alert"

        for i in range(len(self.sensors)):
            sensor = self.sensors[i]
            stored_sensor = system_data.get_sensor_by_id(sensor.sensorId)
            target_node = system_data.get_node_by_id(sensor.nodeId)
            if target_node is None:
                self.fail("Node does not exist.")

            # Update node type.
            new_node = ManagerObjNode().deepcopy(target_node)
            new_node.nodeType = new_node_type
            system_data.update_node(new_node)

            if (len(self.sensors) - (i + 1)) != len(system_data.get_sensors_list()):
                self.fail("Wrong number of Sensor objects stored.")

            if target_node.nodeType != new_node_type:
                self.fail("Node type update failed.")

            if len(self.nodes) != len(system_data.get_nodes_list()):
                self.fail("Number of stored nodes changed.")

            if stored_sensor.internal_state != InternalState.DELETED:
                self.fail("Sensor object state not set to DELETED.")

    def test_delete_node(self):
        """
        Test Node object deleting.
        """
        system_data = self._create_system_data()

        for node in system_data.get_nodes_list():

            corresponding_alerts = system_data.get_alerts_by_node_id(node.nodeId)
            corresponding_managers = system_data.get_managers_by_node_id(node.nodeId)
            corresponding_sensors = system_data.get_sensors_by_node_id(node.nodeId)

            system_data.delete_node_by_id(node.nodeId)

            if not node.is_deleted():
                self.fail("Node object not marked as deleted.")

            for stored_node in system_data.get_nodes_list():
                if stored_node.is_deleted():
                    self.fail("Stored Node object marked as deleted.")

                if node.nodeId == stored_node.nodeId:
                    self.fail("Store still contains Node with id that was deleted.")

            for alert in corresponding_alerts:
                if not alert.is_deleted():
                    self.fail("Alert object not deleted.")

            for manager in corresponding_managers:
                if not manager.is_deleted():
                    self.fail("Manager object not deleted.")

            for sensor in corresponding_sensors:
                if not sensor.is_deleted():
                    self.fail("Sensor object not deleted.")
