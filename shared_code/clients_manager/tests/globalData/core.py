from unittest import TestCase
from typing import Optional
from lib.globalData.systemData import SystemData
from lib.globalData.managerObjects import ManagerObjOption, ManagerObjAlertLevel, ManagerObjNode, ManagerObjAlert, \
    ManagerObjManager, ManagerObjSensor, ManagerObjProfile
from lib.globalData.sensorObjects import SensorDataType


class TestSystemDataCore(TestCase):

    def _create_alert_levels(self, system_data: Optional[SystemData] = None) -> SystemData:

        if system_data is None:
            system_data = self._create_profiles()

        alert_level = ManagerObjAlertLevel()
        alert_level.level = 1
        alert_level.name = "alert_level_1"
        alert_level.triggerAlways = 1
        alert_level.profiles = [0]
        alert_level.instrumentation_active = True
        alert_level.instrumentation_cmd = "instrumentation_cmd_1"
        alert_level.instrumentation_timeout = 1234
        self.alert_levels.append(alert_level)
        system_data.update_alert_level(ManagerObjAlertLevel().deepcopy(alert_level))

        alert_level = ManagerObjAlertLevel()
        alert_level.level = 2
        alert_level.name = "alert_level_2"
        alert_level.triggerAlways = 1
        alert_level.profiles = [1]
        alert_level.instrumentation_active = False
        self.alert_levels.append(alert_level)
        system_data.update_alert_level(ManagerObjAlertLevel().deepcopy(alert_level))

        alert_level = ManagerObjAlertLevel()
        alert_level.level = 3
        alert_level.name = "alert_level_3"
        alert_level.triggerAlways = 1
        alert_level.profiles = [0, 2]
        alert_level.instrumentation_active = False
        self.alert_levels.append(alert_level)
        system_data.update_alert_level(ManagerObjAlertLevel().deepcopy(alert_level))

        return system_data

    def _create_alerts(self, system_data: Optional[SystemData] = None) -> SystemData:

        if system_data is None:
            system_data = self._create_alert_levels()

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
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        alert = ManagerObjAlert()
        alert.nodeId = 1
        alert.alertId = 2
        alert.remoteAlertId = 0
        alert.alertLevels = [1]
        alert.description = "alert_1"
        self.alerts.append(alert)
        system_data.update_alert(ManagerObjAlert().deepcopy(alert))

        node = ManagerObjNode()
        node.nodeId = 2
        node.hostname = "hostname_2"
        node.nodeType = "alert"
        node.instance = "instance_2"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_2"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        alert = ManagerObjAlert()
        alert.nodeId = 2
        alert.alertId = 1
        alert.remoteAlertId = 3
        alert.alertLevels = [2]
        alert.description = "alert_2"
        self.alerts.append(alert)
        system_data.update_alert(ManagerObjAlert().deepcopy(alert))

        node = ManagerObjNode()
        node.nodeId = 3
        node.hostname = "hostname_3"
        node.nodeType = "alert"
        node.instance = "instance_3"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_3"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        alert = ManagerObjAlert()
        alert.nodeId = 3
        alert.alertId = 3
        alert.remoteAlertId = 1
        alert.alertLevels = [1, 2]
        alert.description = "alert_3"
        self.alerts.append(alert)
        system_data.update_alert(ManagerObjAlert().deepcopy(alert))

        return system_data

    def _create_managers(self, system_data: Optional[SystemData] = None) -> SystemData:

        if system_data is None:
            system_data = SystemData()
            self.alert_levels = []
            self.alerts = []
            self.managers = []
            self.nodes = []
            self.options = []
            self.profiles = []
            self.sensors = []

        node = ManagerObjNode()
        node.nodeId = 4
        node.hostname = "hostname_4"
        node.nodeType = "manager"
        node.instance = "instance_4"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_4"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        manager = ManagerObjManager()
        manager.nodeId = 4
        manager.managerId = 1
        manager.description = "manager_1"
        self.managers.append(manager)
        system_data.update_manager(ManagerObjManager().deepcopy(manager))

        node = ManagerObjNode()
        node.nodeId = 5
        node.hostname = "hostname_5"
        node.nodeType = "manager"
        node.instance = "instance_5"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_5"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        manager = ManagerObjManager()
        manager.nodeId = 5
        manager.managerId = 2
        manager.description = "manager_2"
        self.managers.append(manager)
        system_data.update_manager(ManagerObjManager().deepcopy(manager))

        node = ManagerObjNode()
        node.nodeId = 6
        node.hostname = "hostname_6"
        node.nodeType = "manager"
        node.instance = "instance_6"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_6"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        manager = ManagerObjManager()
        manager.nodeId = 6
        manager.managerId = 3
        manager.description = "manager_3"
        self.managers.append(manager)
        system_data.update_manager(ManagerObjManager().deepcopy(manager))

        return system_data

    def _create_sensors(self, system_data: Optional[SystemData] = None) -> SystemData:

        if system_data is None:
            system_data = self._create_alert_levels()

        node = ManagerObjNode()
        node.nodeId = 7
        node.hostname = "hostname_7"
        node.nodeType = "sensor"
        node.instance = "instance_7"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_7"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = 7
        sensor.sensorId = 1
        sensor.remoteSensorId = 2
        sensor.alertDelay = 0
        sensor.alertLevels = [2]
        sensor.description = "sensor_1"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor().deepcopy(sensor))

        node = ManagerObjNode()
        node.nodeId = 8
        node.hostname = "hostname_8"
        node.nodeType = "sensor"
        node.instance = "instance_8"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_8"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = 8
        sensor.sensorId = 2
        sensor.remoteSensorId = 3
        sensor.alertDelay = 0
        sensor.alertLevels = [1, 2]
        sensor.description = "sensor_2"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor().deepcopy(sensor))

        node = ManagerObjNode()
        node.nodeId = 9
        node.hostname = "hostname_9"
        node.nodeType = "sensor"
        node.instance = "instance_9"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_9"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = 9
        sensor.sensorId = 3
        sensor.remoteSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [1]
        sensor.description = "sensor_3"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor().deepcopy(sensor))

        node = ManagerObjNode()
        node.nodeId = 10
        node.hostname = "hostname_server_10"
        node.nodeType = "server"
        node.instance = "instance_10"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_10"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = 10
        sensor.sensorId = 4
        sensor.remoteSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [3]
        sensor.description = "server_sensor_1"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor().deepcopy(sensor))

        node = ManagerObjNode()
        node.nodeId = 11
        node.hostname = "hostname_server_11"
        node.nodeType = "server"
        node.instance = "instance_11"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_11"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = 11
        sensor.sensorId = 5
        sensor.remoteSensorId = 4
        sensor.alertDelay = 0
        sensor.alertLevels = [1, 2]
        sensor.description = "server_sensor_2"
        sensor.lastStateUpdated = 0
        sensor.state = 1
        sensor.dataType = SensorDataType.NONE
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor().deepcopy(sensor))

        node = ManagerObjNode()
        node.nodeId = 12
        node.hostname = "hostname_server_12"
        node.nodeType = "server"
        node.instance = "instance_12"
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_12"
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode().deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = 12
        sensor.sensorId = 6
        sensor.remoteSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [2]
        sensor.description = "server_sensor_3"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor().deepcopy(sensor))

        return system_data

    def _create_options(self, system_data: Optional[SystemData] = None) -> SystemData:

        if system_data is None:
            system_data = SystemData()
            self.alert_levels = []
            self.alerts = []
            self.managers = []
            self.nodes = []
            self.options = []
            self.profiles = []
            self.sensors = []

        option = ManagerObjOption()
        option.type = "type_1"
        option.value = 1.0
        self.options.append(option)
        system_data.update_option(ManagerObjOption().deepcopy(option))

        option = ManagerObjOption()
        option.type = "type_2"
        option.value = 2.0
        self.options.append(option)
        system_data.update_option(ManagerObjOption().deepcopy(option))

        option = ManagerObjOption()
        option.type = "type_3"
        option.value = 3.0
        self.options.append(option)
        system_data.update_option(ManagerObjOption().deepcopy(option))

        return system_data

    def _create_profiles(self, system_data: Optional[SystemData] = None) -> SystemData:

        if system_data is None:
            system_data = SystemData()
            self.alert_levels = []
            self.alerts = []
            self.managers = []
            self.nodes = []
            self.options = []
            self.profiles = []
            self.sensors = []

        profile = ManagerObjProfile()
        profile.id = 0
        profile.name = "profile_0"
        self.profiles.append(profile)
        system_data.update_profile(ManagerObjProfile().deepcopy(profile))

        profile = ManagerObjProfile()
        profile.id = 1
        profile.name = "profile_1"
        self.profiles.append(profile)
        system_data.update_profile(ManagerObjProfile().deepcopy(profile))

        profile = ManagerObjProfile()
        profile.id = 2
        profile.name = "profile_2"
        self.profiles.append(profile)
        system_data.update_profile(ManagerObjProfile().deepcopy(profile))

        return system_data

    def _create_system_data(self) -> SystemData:
        system_data = self._create_options()
        system_data = self._create_profiles(system_data)
        system_data = self._create_alert_levels(system_data)
        system_data = self._create_alerts(system_data)
        system_data = self._create_managers(system_data)
        system_data = self._create_sensors(system_data)

        return system_data
