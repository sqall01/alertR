from unittest import TestCase
from lib.globalData.systemData import SystemData
from lib.localObjects import Option, AlertLevel, Node, Alert, Manager, Sensor, SensorDataType


class TestCommunicationStress(TestCase):

    def _create_system_data(self) -> SystemData:
        alert_levels = []
        nodes = []
        alerts = []
        managers = []
        sensors = []
        options = []
        system_data = SystemData()

        alert_level = AlertLevel()
        alert_level.level = 1
        alert_level.name = "Alert Level One"
        alert_level.triggerAlways = True
        alert_level.rulesActivated = True
        alert_levels.append(alert_level)
        system_data.update_alert_level(AlertLevel().deepCopy(alert_level))

        alert_level = AlertLevel()
        alert_level.level = 2
        alert_level.name = "Alert Level Two"
        alert_level.triggerAlways = False
        alert_level.rulesActivated = False
        alert_levels.append(alert_level)
        system_data.update_alert_level(AlertLevel().deepCopy(alert_level))

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
        nodes.append(node)
        system_data.update_node(Node().deepCopy(node))

        alert = Alert()
        alert.nodeId = 1
        alert.alertId = 1
        alert.remoteAlertId = 1
        alert.alertLevels = [1, 2]
        alert.description = "alert_1"
        alerts.append(alert)
        system_data.update_alert(Alert().deepCopy(alert))

        node = Node()
        node.nodeId = 2
        node.hostname = "hostname_2"
        node.nodeType = "alert"
        node.instance = "instance_2"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_2"
        node.persistent = 1
        nodes.append(node)
        system_data.update_node(Node().deepCopy(node))

        alert = Alert()
        alert.nodeId = 2
        alert.alertId = 2
        alert.remoteAlertId = 1
        alert.alertLevels = [1, 2]
        alert.description = "alert_2"
        alerts.append(alert)
        system_data.update_alert(Alert().deepCopy(alert))

        node = Node()
        node.nodeId = 3
        node.hostname = "hostname_3"
        node.nodeType = "manager"
        node.instance = "instance_3"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_3"
        node.persistent = 1
        nodes.append(node)
        system_data.update_node(Node().deepCopy(node))

        manager = Manager()
        manager.nodeId = 3
        manager.managerId = 1
        manager.description = "manager_1"
        managers.append(manager)
        system_data.update_manager(Manager().deepCopy(manager))

        node = Node()
        node.nodeId = 4
        node.hostname = "hostname_4"
        node.nodeType = "manager"
        node.instance = "instance_4"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_4"
        node.persistent = 1
        nodes.append(node)
        system_data.update_node(Node().deepCopy(node))

        manager = Manager()
        manager.nodeId = 4
        manager.managerId = 2
        manager.description = "manager_2"
        managers.append(manager)
        system_data.update_manager(Manager().deepCopy(manager))

        node = Node()
        node.nodeId = 5
        node.hostname = "hostname_5"
        node.nodeType = "sensor"
        node.instance = "instance_5"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_5"
        node.persistent = 1
        nodes.append(node)
        system_data.update_node(Node().deepCopy(node))

        sensor = Sensor()
        sensor.nodeId = 5
        sensor.sensorId = 1
        sensor.remoteSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [1, 2]
        sensor.description = "sensor_1"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        sensors.append(sensor)
        system_data.update_sensor(Sensor().deepCopy(sensor))

        node = Node()
        node.nodeId = 6
        node.hostname = "hostname_6"
        node.nodeType = "sensor"
        node.instance = "instance_6"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_6"
        node.persistent = 1
        nodes.append(node)
        system_data.update_node(Node().deepCopy(node))

        sensor = Sensor()
        sensor.nodeId = 6
        sensor.sensorId = 2
        sensor.remoteSensorId = 2
        sensor.alertDelay = 0
        sensor.alertLevels = [1, 2]
        sensor.description = "sensor_2"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        sensors.append(sensor)
        system_data.update_sensor(Sensor().deepCopy(sensor))

        option = Option()
        option.type = "type_1"
        option.value = 1.0
        options.append(option)
        system_data.update_option(Option().deepCopy(option))

        option = Option()
        option.type = "type_2"
        option.value = 1.0
        options.append(option)
        system_data.update_option(Option().deepCopy(option))

        self.alert_levels = alert_levels
        self.alerts = alerts
        self.managers = managers
        self.nodes = nodes
        self.options = options
        self.sensors = sensors

        return system_data

    def test_valid_creation(self):
        system_data = self._create_system_data()

        # Check if created options are stored.
        stored_options = system_data.get_options_list()
        for created_option in self.options:
            found = False
            for stored_option in stored_options:
                if stored_option.type == created_option.type:
                    found = True
                    break
            if not found:
                self.fail("Option %s not stored." % created_option.type)

        # Check if created alert levels are stored.
        stored_alert_levels = system_data.get_alert_levels_list()
        for created_alert_level in self.alert_levels:
            found = False
            for stored_alert_level in stored_alert_levels:
                if stored_alert_level.level == created_alert_level.level:
                    found = True
                    break
            if not found:
                self.fail("Alert Level %d not stored." % created_alert_level.level)

        # Check if created nodes are stored.
        stored_nodes = system_data.get_nodes_list()
        for created_node in self.nodes:
            found = False
            for stored_node in stored_nodes:
                if stored_node.nodeId == created_node.nodeId:
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
                        and stored_alert.alertId == created_alert.alertId):
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
                        and stored_manager.managerId == created_manager.managerId):
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
                        and stored_sensor.sensorId == created_sensor.sensorId):
                    found = True
                    break
            if not found:
                self.fail("Sensor %d not stored." % created_sensor.sensorId)

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

    def test_invalid_manager_adding(self):
        """
        Tests sanity checks for Manager object adding.
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

        system_data = SystemData()

        # Test non-existing node.
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
            self.fail("Exception because of non-existing node expected.")

    def test_invalid_sensor_adding(self):
        """
        Tests sanity checks for Sensor object adding.
        """
        # Test invalid node type.
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

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.sensorId = 1
        sensor.remoteSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = []
        sensor.description = "sensor_1"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        is_exception = False
        try:
            system_data.update_sensor(sensor)
        except ValueError:
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")

        system_data = SystemData()

        # Test non-existing node.
        sensor = Sensor()
        sensor.nodeId = 1
        sensor.sensorId = 1
        sensor.remoteSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = []
        sensor.description = "sensor_1"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        is_exception = False
        try:
            system_data.update_sensor(sensor)
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

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.sensorId = 1
        sensor.remoteSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = []
        sensor.description = "sensor_1"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        is_exception = False
        try:
            system_data.update_sensor(sensor)
        except ValueError:
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")
