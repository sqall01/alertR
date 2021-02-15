from tests.globalData.core import TestSystemDataCore
from tests.globalData.util import compare_profiles_content, compare_options_content, compare_alert_levels_content, \
    compare_alerts_content, compare_managers_content, compare_nodes_content, compare_sensors_content
from lib.manager.core import BaseManagerEventHandler
from lib.globalData.globalData import GlobalData


class TestManagerCoreStatusUpdate(TestSystemDataCore):

    def test_content_update(self):
        """
        Tests status update of content.
        """
        global_data = GlobalData()
        global_data.system_data = self._create_system_data()
        event_handler = BaseManagerEventHandler(global_data)

        # Update local objects.
        ctr = 1
        for option in self.options:
            option.value += ctr
            ctr += 1

        for profile in self.profiles:
            profile.name += "_new_" + str(ctr)
            ctr += 1

        for alert_level in self.alert_levels:
            alert_level.name += "_new_" + str(ctr)
            ctr += 1

        for node in self.nodes:
            node.hostname += "_new_" + str(ctr)
            ctr += 1

        for alert in self.alerts:
            alert.description += "_new_" + str(ctr)
            ctr += 1

        for sensor in self.sensors:
            sensor.description += "_new_" + str(ctr)
            ctr += 1

        for manager in self.managers:
            manager.description += "_new_" + str(ctr)
            ctr += 1

        # Check stored and local objects differ.
        for stored_option in global_data.system_data.get_options_list():
            found = False
            for local_option in self.options:
                if local_option.type == stored_option.type:
                    found = True
                    if local_option == stored_option:
                        self.fail("Local and stored object have not the same object.")

                    if local_option.value == stored_option.value:
                        self.fail("Local and stored object have the same content.")

                    break

            if not found:
                self.fail("Stored Option object not found in local objects.")

        # Check stored and local objects differ.
        for stored_profile in global_data.system_data.get_profiles_list():
            found = False
            for local_profile in self.profiles:
                if local_profile.profileId == stored_profile.profileId:
                    found = True
                    if local_profile == stored_profile:
                        self.fail("Local and stored object have not the same object.")

                    if local_profile.name == stored_profile.name:
                        self.fail("Local and stored object have the same content.")

                    break

            if not found:
                self.fail("Stored Option object not found in local objects.")

        for stored_alert_level in global_data.system_data.get_alert_levels_list():
            found = False
            for local_alert_level in self.alert_levels:
                if local_alert_level.level == stored_alert_level.level:
                    found = True
                    if local_alert_level == stored_alert_level:
                        self.fail("Local and stored object are the same object.")

                    if local_alert_level.name == stored_alert_level.name:
                        self.fail("Local and stored object have the same content.")

                    break

            if not found:
                self.fail("Stored Alert Level object not found in local objects.")

        for stored_node in global_data.system_data.get_nodes_list():
            found = False
            for local_node in self.nodes:
                if local_node.nodeId == stored_node.nodeId:
                    found = True
                    if local_node == stored_node:
                        self.fail("Local and stored object are the same object.")

                    if local_node.hostname == stored_node.hostname:
                        self.fail("Local and stored object have the same content.")

                    break

            if not found:
                self.fail("Stored Node object not found in local objects.")

        for stored_alert in global_data.system_data.get_alerts_list():
            found = False
            for local_alert in self.alerts:
                if local_alert.alertId == stored_alert.alertId:
                    found = True
                    if local_alert == stored_alert:
                        self.fail("Local and stored object are the same object.")

                    if local_alert.description == stored_alert.description:
                        self.fail("Local and stored object have the same content.")

                    break

            if not found:
                self.fail("Stored Alert object not found in local objects.")

        for stored_manager in global_data.system_data.get_managers_list():
            found = False
            for local_manager in self.managers:
                if local_manager.managerId == stored_manager.managerId:
                    found = True
                    if local_manager == stored_manager:
                        self.fail("Local and stored object are the same object.")

                    if local_manager.description == stored_manager.description:
                        self.fail("Local and stored object have the same content.")

                    break

            if not found:
                self.fail("Stored Manager object not found in local objects.")

        for stored_sensor in global_data.system_data.get_sensors_list():
            found = False
            for local_sensor in self.sensors:
                if local_sensor.sensorId == stored_sensor.sensorId:
                    found = True
                    if local_sensor == stored_sensor:
                        self.fail("Local and stored object are the same object.")

                    if local_sensor.description == stored_sensor.description:
                        self.fail("Local and stored object have the same content.")

                    break

            if not found:
                self.fail("Stored Sensor object not found in local objects.")

        if not event_handler.status_update(1337,
                                           self.options,
                                           self.profiles,
                                           self.nodes,
                                           self.sensors,
                                           self.managers,
                                           self.alerts,
                                           self.alert_levels):
            self.fail("Status update failed.")

        if event_handler.msg_time != 1337:
            self.fail("Server time update failed.")

        # Check changes are stored.
        compare_options_content(self, self.options, global_data.system_data.get_options_list())
        compare_profiles_content(self, self.profiles, global_data.system_data.get_profiles_list())
        compare_alert_levels_content(self, self.alert_levels, global_data.system_data.get_alert_levels_list())
        compare_nodes_content(self, self.nodes, global_data.system_data.get_nodes_list())
        compare_alerts_content(self, self.alerts, global_data.system_data.get_alerts_list())
        compare_managers_content(self, self.managers, global_data.system_data.get_managers_list())
        compare_sensors_content(self, self.sensors, global_data.system_data.get_sensors_list())

    def test_all_object_deletion(self):
        """
        Tests status update of deleting all objects.
        """
        global_data = GlobalData()
        global_data.system_data = self._create_system_data()
        event_handler = BaseManagerEventHandler(global_data)

        if not event_handler.status_update(0,
                                           [],
                                           [],
                                           [],
                                           [],
                                           [],
                                           [],
                                           []):
            self.fail("Status update failed.")

        if len(global_data.system_data.get_options_list()) != 0:
            self.fail("Option objects still stored.")

        if len(global_data.system_data.get_profiles_list()) != 0:
            self.fail("Profile objects still stored.")

        if len(global_data.system_data.get_alert_levels_list()) != 0:
            self.fail("Alert Level objects still stored.")

        if len(global_data.system_data.get_nodes_list()) != 0:
            self.fail("Node objects still stored.")

        if len(global_data.system_data.get_alerts_list()) != 0:
            self.fail("Alert objects still stored.")

        if len(global_data.system_data.get_managers_list()) != 0:
            self.fail("Manager objects still stored.")

        if len(global_data.system_data.get_sensors_list()) != 0:
            self.fail("Sensor objects still stored.")

    def test_object_deletion(self):
        """
        Tests status update of object deletion.
        """
        global_data = GlobalData()
        global_data.system_data = self._create_system_data()
        event_handler = BaseManagerEventHandler(global_data)

        # Remove single local object
        # IMPORTANT: Ignore alert level/node/profile here,
        # since the deletion of a alert level/node/profile object also deletes other objects.
        ctr = 0
        option_to_remove = self.options[ctr % len(self.options)]
        self.options.remove(option_to_remove)

        ctr += 1
        alert_to_remove = self.alerts[ctr % len(self.alerts)]
        self.alerts.remove(alert_to_remove)

        ctr += 1
        manager_to_remove = self.managers[ctr % len(self.managers)]
        self.managers.remove(manager_to_remove)

        ctr += 1
        sensor_to_remove = self.sensors[ctr % len(self.sensors)]
        self.sensors.remove(sensor_to_remove)

        if len(self.options) != (len(global_data.system_data.get_options_list()) - 1):
            self.fail("Local objects list connected to stored data.")

        if len(self.alerts) != (len(global_data.system_data.get_alerts_list()) - 1):
            self.fail("Local objects list connected to stored data.")

        if len(self.managers) != (len(global_data.system_data.get_managers_list()) - 1):
            self.fail("Local objects list connected to stored data.")

        if len(self.sensors) != (len(global_data.system_data.get_sensors_list()) - 1):
            self.fail("Local objects list connected to stored data.")

        if not event_handler.status_update(0,
                                           self.options,
                                           self.profiles,
                                           self.nodes,
                                           self.sensors,
                                           self.managers,
                                           self.alerts,
                                           self.alert_levels):
            self.fail("Status update failed.")

        if len(self.options) != len(global_data.system_data.get_options_list()):
            self.fail("Number of stored objects wrong.")

        if len(self.profiles) != len(global_data.system_data.get_profiles_list()):
            self.fail("Number of stored objects wrong.")

        if len(self.alert_levels) != len(global_data.system_data.get_alert_levels_list()):
            self.fail("Number of stored objects wrong.")

        if len(self.nodes) != len(global_data.system_data.get_nodes_list()):
            self.fail("Number of stored objects wrong.")

        if len(self.alerts) != len(global_data.system_data.get_alerts_list()):
            self.fail("Number of stored objects wrong.")

        if len(self.managers) != len(global_data.system_data.get_managers_list()):
            self.fail("Number of stored objects wrong.")

        if len(self.sensors) != len(global_data.system_data.get_sensors_list()):
            self.fail("Number of stored objects wrong.")

        # Check changes are stored.
        for stored_option in global_data.system_data.get_options_list():
            if stored_option.type == option_to_remove.type:
                self.fail("Object not removed from store.")

            found = False
            for local_option in self.options:
                if local_option.type == stored_option.type:
                    found = True
                    if local_option == stored_option:
                        self.fail("Local and stored object are the same object.")

                    break

            if not found:
                self.fail("Stored Option object not found in local objects.")

        for stored_alert in global_data.system_data.get_alerts_list():
            if stored_alert.alertId == alert_to_remove.alertId:
                self.fail("Object not removed from store.")

            found = False
            for local_alert in self.alerts:
                if local_alert.alertId == stored_alert.alertId:
                    found = True
                    if local_alert == stored_alert:
                        self.fail("Local and stored object are the same object.")

                    break

            if not found:
                self.fail("Stored Alert object not found in local objects.")

        for stored_manager in global_data.system_data.get_managers_list():
            if stored_manager.managerId == manager_to_remove.managerId:
                self.fail("Object not removed from store.")

            found = False
            for local_manager in self.managers:
                if local_manager.managerId == stored_manager.managerId:
                    found = True
                    if local_manager == stored_manager:
                        self.fail("Local and stored object are the same object.")

                    break

            if not found:
                self.fail("Stored Manager object not found in local objects.")

        for stored_sensor in global_data.system_data.get_sensors_list():
            if stored_sensor.sensorId == sensor_to_remove.sensorId:
                self.fail("Object not removed from store.")

            found = False
            for local_sensor in self.sensors:
                if local_sensor.sensorId == stored_sensor.sensorId:
                    found = True
                    if local_sensor == stored_sensor:
                        self.fail("Local and stored object are the same object.")

                    break

            if not found:
                self.fail("Stored Sensor object not found in local objects.")

        compare_profiles_content(self, self.profiles, global_data.system_data.get_profiles_list())
        compare_alert_levels_content(self, self.alert_levels, global_data.system_data.get_alert_levels_list())
        compare_nodes_content(self, self.nodes, global_data.system_data.get_nodes_list())

    def test_node_deletion(self):
        """
        Tests status update of node deletion.
        """
        global_data = GlobalData()
        global_data.system_data = self._create_system_data()
        event_handler = BaseManagerEventHandler(global_data)

        # Remove single local object
        ctr = 0
        node_to_remove = self.nodes[ctr % len(self.nodes)]
        self.nodes.remove(node_to_remove)

        if len(self.nodes) != (len(global_data.system_data.get_nodes_list()) - 1):
            self.fail("Local objects list connected to stored data.")

        if not event_handler.status_update(0,
                                           self.options,
                                           self.profiles,
                                           self.nodes,
                                           self.sensors,
                                           self.managers,
                                           self.alerts,
                                           self.alert_levels):
            self.fail("Status update failed.")

        if len(self.nodes) != len(global_data.system_data.get_nodes_list()):
            self.fail("Number of stored objects wrong.")

        # Check changes are stored.
        for stored_node in global_data.system_data.get_nodes_list():
            if stored_node.nodeId == node_to_remove.nodeId:
                self.fail("Object not removed from store.")

            found = False
            for local_node in self.nodes:
                if local_node.nodeId == stored_node.nodeId:
                    found = True
                    if local_node == stored_node:
                        self.fail("Local and stored object are the same object.")

                    break

            if not found:
                self.fail("Stored Node object not found in local objects.")

    def test_profile_deletion(self):
        """
        Tests status update of profile deletion.
        """
        global_data = GlobalData()
        global_data.system_data = self._create_system_data()
        event_handler = BaseManagerEventHandler(global_data)

        # Remove single local object
        ctr = 0
        profile_to_remove = self.profiles[ctr % len(self.profiles)]
        self.profiles.remove(profile_to_remove)

        if len(self.profiles) != (len(global_data.system_data.get_profiles_list()) - 1):
            self.fail("Local objects list connected to stored data.")

        if not event_handler.status_update(0,
                                           self.options,
                                           self.profiles,
                                           self.nodes,
                                           self.sensors,
                                           self.managers,
                                           self.alerts,
                                           self.alert_levels):
            self.fail("Status update failed.")

        if len(self.profiles) != len(global_data.system_data.get_profiles_list()):
            self.fail("Number of stored objects wrong.")

        # Check changes are stored.
        for stored_profile in global_data.system_data.get_profiles_list():
            if stored_profile.profileId == profile_to_remove.profileId:
                self.fail("Object not removed from store.")

            found = False
            for local_profile in self.profiles:
                if local_profile.profileId == stored_profile.profileId:
                    found = True
                    if local_profile == stored_profile:
                        self.fail("Local and stored object are the same object.")

                    break

            if not found:
                self.fail("Stored Profile object not found in local objects.")

    def test_alert_level_deletion(self):
        """
        Tests status update of alert level deletion.
        """
        global_data = GlobalData()
        global_data.system_data = self._create_system_data()
        event_handler = BaseManagerEventHandler(global_data)

        # Remove single local object
        ctr = 0
        alert_level_to_remove = self.alert_levels[ctr % len(self.alert_levels)]
        self.alert_levels.remove(alert_level_to_remove)

        if len(self.alert_levels) != (len(global_data.system_data.get_alert_levels_list()) - 1):
            self.fail("Local objects list connected to stored data.")

        if not event_handler.status_update(0,
                                           self.options,
                                           self.profiles,
                                           self.nodes,
                                           self.sensors,
                                           self.managers,
                                           self.alerts,
                                           self.alert_levels):
            self.fail("Status update failed.")

        if len(self.alert_levels) != len(global_data.system_data.get_alert_levels_list()):
            self.fail("Number of stored objects wrong.")

        # Check changes are stored.
        for stored_alert_level in global_data.system_data.get_alert_levels_list():
            if stored_alert_level.level == alert_level_to_remove.level:
                self.fail("Object not removed from store.")

            found = False
            for local_alert_level in self.alert_levels:
                if local_alert_level.level == stored_alert_level.level:
                    found = True
                    if local_alert_level == stored_alert_level:
                        self.fail("Local and stored object are the same object.")

                    break

            if not found:
                self.fail("Stored Alert Level object not found in local objects.")
