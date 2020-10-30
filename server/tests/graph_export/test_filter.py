import logging
import xml.etree.ElementTree
from unittest import TestCase
from lib import GlobalData, Sqlite
from lib.config.parser import configure_alert_levels
from graphExport import Filter, get_objects_from_db


class TestFilter(TestCase):

    # Called before each test.
    def setUp(self):
        global_data = GlobalData()

        # Initialize logging.
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%m/%d/%Y %H:%M:%S',
                            level=logging.WARNING)
        global_data.logger = logging.getLogger("graph")

        # Open database.
        global_data.storage = Sqlite("./database.db",
                                     global_data,
                                     read_only=True)

        # Read necessary configurations.
        configRoot = xml.etree.ElementTree.parse("./config.xml").getroot()
        configure_alert_levels(configRoot, global_data)

        self.alert_levels = {}
        for alert_level in global_data.alertLevels:
            self.alert_levels[alert_level.level] = alert_level
        self.nodes, self.alerts, self.sensors = get_objects_from_db(global_data)

    def test_filter_alert_levels(self):

        # Test Alert Level filter.
        obj_filter = Filter(23,
                            None,
                            None,
                            None,
                            None)

        filtered_alert_levels = obj_filter.filter_alert_levels(self.alert_levels,
                                                               self.nodes,
                                                               self.alerts,
                                                               self.sensors)

        found_alert_levels = {23: False}
        orig_len = len(found_alert_levels.keys())
        for alert_level in filtered_alert_levels.keys():
            found_alert_levels[alert_level] = True
        if not all(map(lambda x: found_alert_levels[x], found_alert_levels.keys())):
            self.fail("Wrong Alert Levels returned.")
        if orig_len != len(found_alert_levels.keys()):
            self.fail("Too many Alert Levels returned.")

        # Test Alert filter.
        obj_filter = Filter(None,
                            "user13",
                            0,
                            None,
                            None)

        filtered_alert_levels = obj_filter.filter_alert_levels(self.alert_levels,
                                                               self.nodes,
                                                               self.alerts,
                                                               self.sensors)

        found_alert_levels = {10: False, 11: False}
        orig_len = len(found_alert_levels.keys())
        for alert_level in filtered_alert_levels.keys():
            found_alert_levels[alert_level] = True
        if not all(map(lambda x: found_alert_levels[x], found_alert_levels.keys())):
            self.fail("Wrong Alert Levels returned.")
        if orig_len != len(found_alert_levels.keys()):
            self.fail("Too many Alert Levels returned.")

        # Test Sensor filter.
        obj_filter = Filter(None,
                            None,
                            None,
                            "user1",
                            2)

        filtered_alert_levels = obj_filter.filter_alert_levels(self.alert_levels,
                                                               self.nodes,
                                                               self.alerts,
                                                               self.sensors)

        found_alert_levels = {0: False, 1: False, 13: False, 14: False}
        orig_len = len(found_alert_levels.keys())
        for alert_level in filtered_alert_levels.keys():
            found_alert_levels[alert_level] = True
        if not all(map(lambda x: found_alert_levels[x], found_alert_levels.keys())):
            self.fail("Wrong Alert Levels returned.")
        if orig_len != len(found_alert_levels.keys()):
            self.fail("Too many Alert Levels returned.")

    def test_filter_alerts(self):

        # Test Alert Level filter.
        obj_filter = Filter(23,
                            None,
                            None,
                            None,
                            None)

        filtered_alerts = obj_filter.filter_alerts(self.nodes,
                                                   self.alerts,
                                                   self.sensors)

        found_alerts = {19: False, 21: False}
        orig_len = len(found_alerts.keys())
        for alert in filtered_alerts:
            found_alerts[alert.alertId] = True
        if not all(map(lambda x: found_alerts[x], found_alerts.keys())):
            self.fail("Wrong Alerts returned.")
        if orig_len != len(found_alerts.keys()):
            self.fail("Too many Alerts returned.")

        # Test Alert filter.
        obj_filter = Filter(None,
                            "user13",
                            0,
                            None,
                            None)

        filtered_alerts = obj_filter.filter_alerts(self.nodes,
                                                   self.alerts,
                                                   self.sensors)

        found_alerts = {8: False}
        orig_len = len(found_alerts.keys())
        for alert in filtered_alerts:
            found_alerts[alert.alertId] = True
        if not all(map(lambda x: found_alerts[x], found_alerts.keys())):
            self.fail("Wrong Alerts returned.")
        if orig_len != len(found_alerts.keys()):
            self.fail("Too many Alerts returned.")

        # Test Sensor filter.
        obj_filter = Filter(None,
                            None,
                            None,
                            "user1",
                            2)

        filtered_alerts = obj_filter.filter_alerts(self.nodes,
                                                   self.alerts,
                                                   self.sensors)

        found_alerts = {4: False, 5: False, 16: False, 17: False, 26: False}
        orig_len = len(found_alerts.keys())
        for alert in filtered_alerts:
            found_alerts[alert.alertId] = True
        if not all(map(lambda x: found_alerts[x], found_alerts.keys())):
            self.fail("Wrong Alerts returned.")
        if orig_len != len(found_alerts.keys()):
            self.fail("Too many Alerts returned.")

    def test_filter_sensors(self):

        # Test Alert Level filter.
        obj_filter = Filter(23,
                            None,
                            None,
                            None,
                            None)

        filtered_sensors = obj_filter.filter_sensors(self.nodes,
                                                     self.alerts,
                                                     self.sensors)

        found_sensors = {32: False, 34: False}
        orig_len = len(found_sensors.keys())
        for sensor in filtered_sensors:
            found_sensors[sensor.sensorId] = True
        if not all(map(lambda x: found_sensors[x], found_sensors.keys())):
            self.fail("Wrong Sensors returned.")
        if orig_len != len(found_sensors.keys()):
            self.fail("Too many Sensors returned.")

        # Test Alert filter.
        obj_filter = Filter(None,
                            "user13",
                            0,
                            None,
                            None)

        filtered_sensors = obj_filter.filter_sensors(self.nodes,
                                                     self.alerts,
                                                     self.sensors)

        found_sensors = {35: False, 36: False, 51: False, 52: False, 63: False, 64: False}
        orig_len = len(found_sensors.keys())
        for sensor in filtered_sensors:
            found_sensors[sensor.sensorId] = True
        if not all(map(lambda x: found_sensors[x], found_sensors.keys())):
            self.fail("Wrong Sensors returned.")
        if orig_len != len(found_sensors.keys()):
            self.fail("Too many Sensors returned.")

        # Test Sensor filter.
        obj_filter = Filter(None,
                            None,
                            None,
                            "user1",
                            2)

        filtered_sensors = obj_filter.filter_sensors(self.nodes,
                                                     self.alerts,
                                                     self.sensors)

        found_sensors = {3: False}
        orig_len = len(found_sensors.keys())
        for sensor in filtered_sensors:
            found_sensors[sensor.sensorId] = True
        if not all(map(lambda x: found_sensors[x], found_sensors.keys())):
            self.fail("Wrong Sensors returned.")
        if orig_len != len(found_sensors.keys()):
            self.fail("Too many Sensors returned.")
