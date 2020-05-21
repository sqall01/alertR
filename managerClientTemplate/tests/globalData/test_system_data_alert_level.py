from tests.globalData.core import TestSystemDataCore
from lib.localObjects import AlertLevel


class TestSystemDataAlertLevel(TestSystemDataCore):

    def test_update_alert_level(self):
        """
        Test Alert Level object updating.
        """
        system_data = self._create_alert_levels()

        # Create changes that should be copied to the stored object.
        new_alert_levels = []
        for i in range(len(self.alert_levels)):
            temp_alert_level = AlertLevel().deepCopy(self.alert_levels[i])
            temp_alert_level.name = "new_alert_level" + str(i + 1)
            temp_alert_level.triggerAlways = ((i % 2) == 0)
            temp_alert_level.rulesActivated = (((i+1) % 2) == 0)
            new_alert_levels.append(temp_alert_level)

        for i in range(len(new_alert_levels)):

            # Update store with new object data.
            temp_alert_level = new_alert_levels[i]
            system_data.update_alert_level(temp_alert_level)

            gt_storage = []
            for j in range(i+1):
                gt_storage.append(new_alert_levels[j])
            for j in range(i+1, len(new_alert_levels)):
                gt_storage.append(self.alert_levels[j])

            stored_alert_levels = system_data.get_alert_levels_list()
            if len(stored_alert_levels) != len(gt_storage):
                self.fail("Wrong number of objects stored.")

            already_processed = []
            for stored_alert_level in stored_alert_levels:
                found = False
                for gt_alert_level in gt_storage:
                    if stored_alert_level.level == gt_alert_level.level:
                        found = True

                        # Check which objects we already processed to see if we hold an object with
                        # duplicated values.
                        if gt_alert_level in already_processed:
                            self.fail()
                        already_processed.append(gt_alert_level)

                        # Only the content of the object should have changed, not the object itself.
                        if stored_alert_level == gt_alert_level:
                            self.fail("Store changed object, not content of existing object.")

                        if (stored_alert_level.name != gt_alert_level.name
                                or stored_alert_level.triggerAlways != gt_alert_level.triggerAlways
                                or stored_alert_level.rulesActivated != gt_alert_level.rulesActivated):
                            self.fail("Stored object does not have correct content.")

                        break

                if not found:
                    self.fail("Not able to find modified Alert Level object.")

    def test_delete_alert_level(self):
        """
        Test Alert Level object deleting.
        """
        system_data = self._create_system_data()

        for alert_level in system_data.get_alert_levels_list():

            # Get Alerts and Sensors that use this alert level.
            corresponding_alerts = []
            for alert in system_data.get_alerts_list():
                if alert_level.level in alert.alertLevels:
                    corresponding_alerts.append(alert)

            corresponding_sensors = []
            for sensor in system_data.get_sensors_list():
                if alert_level.level in sensor.alertLevels:
                    corresponding_sensors.append(sensor)

            system_data.delete_alert_level_by_level(alert_level.level)

            if not alert_level.is_deleted():
                self.fail("Alert Level object not marked as deleted.")

            for stored_alert_level in system_data.get_alert_levels_list():
                if stored_alert_level.is_deleted():
                    self.fail("Stored Alert Level object marked as deleted.")

                if alert_level.level == stored_alert_level.level:
                    self.fail("Store still contains Alert Level with level that was deleted.")

            for alert in corresponding_alerts:
                if alert_level.level in alert.alertLevels:
                    self.fail("Alert object still contains deleted alert level.")

            for sensor in corresponding_sensors:
                if alert_level.level in sensor.alertLevels:
                    self.fail("Sensor object still contains deleted alert level.")
