from unittest import TestCase
from typing import Optional
from lib.globalData.systemData import SystemData
from lib.globalData.managerObjects import ManagerObjOption, ManagerObjAlertLevel, ManagerObjNode, ManagerObjAlert, \
    ManagerObjManager, ManagerObjSensor, ManagerObjProfile
from lib.globalData.sensorObjects import SensorDataType, SensorDataGPS, SensorDataNone, SensorDataFloat, \
    SensorDataInt, SensorErrorState


class TestSystemDataCore(TestCase):

    def setUp(self):
        self._next_node_id = 1
        self._next_alert_id = 1
        self._next_sensor_id = 1
        self._next_manager_id = 1

    def _create_alert_levels(self, system_data: Optional[SystemData] = None) -> SystemData:

        if system_data is None:
            system_data = self._create_profiles()

        alert_level = ManagerObjAlertLevel()
        alert_level.level = 1
        alert_level.name = "alert_level_1"
        alert_level.profiles = [0]
        alert_level.instrumentation_active = True
        alert_level.instrumentation_cmd = "instrumentation_cmd_1"
        alert_level.instrumentation_timeout = 1234
        self.alert_levels.append(alert_level)
        system_data.update_alert_level(ManagerObjAlertLevel.deepcopy(alert_level))

        alert_level = ManagerObjAlertLevel()
        alert_level.level = 2
        alert_level.name = "alert_level_2"
        alert_level.profiles = [1]
        alert_level.instrumentation_active = False
        self.alert_levels.append(alert_level)
        system_data.update_alert_level(ManagerObjAlertLevel.deepcopy(alert_level))

        alert_level = ManagerObjAlertLevel()
        alert_level.level = 3
        alert_level.name = "alert_level_3"
        alert_level.profiles = [0, 2]
        alert_level.instrumentation_active = False
        self.alert_levels.append(alert_level)
        system_data.update_alert_level(ManagerObjAlertLevel.deepcopy(alert_level))

        return system_data

    def _create_alerts(self, system_data: Optional[SystemData] = None) -> SystemData:

        if system_data is None:
            system_data = self._create_alert_levels()

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "alert"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        alert = ManagerObjAlert()
        alert.nodeId = self._next_node_id
        alert.alertId = self._next_alert_id
        alert.clientAlertId = 0
        alert.alertLevels = [1]
        alert.description = "alert_" + str(self._next_alert_id)
        self.alerts.append(alert)
        system_data.update_alert(ManagerObjAlert.deepcopy(alert))

        self._next_node_id += 1
        self._next_alert_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "alert"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        alert = ManagerObjAlert()
        alert.nodeId = self._next_node_id
        alert.alertId = self._next_alert_id
        alert.clientAlertId = 3
        alert.alertLevels = [2]
        alert.description = "alert_" + str(self._next_alert_id)
        self.alerts.append(alert)
        system_data.update_alert(ManagerObjAlert.deepcopy(alert))

        self._next_node_id += 1
        self._next_alert_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "alert"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        alert = ManagerObjAlert()
        alert.nodeId = self._next_node_id
        alert.alertId = self._next_alert_id
        alert.clientAlertId = 1
        alert.alertLevels = [1, 2]
        alert.description = "alert_" + str(self._next_alert_id)
        self.alerts.append(alert)
        system_data.update_alert(ManagerObjAlert.deepcopy(alert))

        self._next_node_id += 1
        self._next_alert_id += 1

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
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "manager"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        manager = ManagerObjManager()
        manager.nodeId = self._next_node_id
        manager.managerId = self._next_manager_id
        manager.description = "manager_" + str(self._next_manager_id)
        self.managers.append(manager)
        system_data.update_manager(ManagerObjManager.deepcopy(manager))

        self._next_node_id += 1
        self._next_manager_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "manager"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        manager = ManagerObjManager()
        manager.nodeId = self._next_node_id
        manager.managerId = self._next_manager_id
        manager.description = "manager_" + str(self._next_manager_id)
        self.managers.append(manager)
        system_data.update_manager(ManagerObjManager.deepcopy(manager))

        self._next_node_id += 1
        self._next_manager_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "manager"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        manager = ManagerObjManager()
        manager.nodeId = self._next_node_id
        manager.managerId = self._next_manager_id
        manager.description = "manager_" + str(self._next_manager_id)
        self.managers.append(manager)
        system_data.update_manager(ManagerObjManager.deepcopy(manager))

        self._next_node_id += 1
        self._next_manager_id += 1

        return system_data

    def _create_sensors(self, system_data: Optional[SystemData] = None) -> SystemData:

        if system_data is None:
            system_data = self._create_alert_levels()

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "sensor"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = self._next_node_id
        sensor.sensorId = self._next_sensor_id
        sensor.clientSensorId = 2
        sensor.alertDelay = 0
        sensor.alertLevels = [2]
        sensor.description = "sensor_" + str(self._next_sensor_id)
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.error_state = SensorErrorState()
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor.deepcopy(sensor))

        self._next_node_id += 1
        self._next_sensor_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "sensor"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = self._next_node_id
        sensor.sensorId = self._next_sensor_id
        sensor.clientSensorId = 3
        sensor.alertDelay = 0
        sensor.alertLevels = [1, 2]
        sensor.description = "sensor_" + str(self._next_sensor_id)
        sensor.state = 0
        sensor.dataType = SensorDataType.INT
        sensor.data = SensorDataInt(1337, "test unit")
        sensor.error_state = SensorErrorState()
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor.deepcopy(sensor))

        self._next_node_id += 1
        self._next_sensor_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "sensor"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = self._next_node_id
        sensor.sensorId = self._next_sensor_id
        sensor.clientSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [1]
        sensor.description = "sensor_" + str(self._next_sensor_id)
        sensor.state = 0
        sensor.dataType = SensorDataType.FLOAT
        sensor.data = SensorDataFloat(1337.0, "test unit")
        sensor.error_state = SensorErrorState()
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor.deepcopy(sensor))

        self._next_node_id += 1
        self._next_sensor_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_" + str(self._next_node_id)
        node.nodeType = "sensor"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = self._next_node_id
        sensor.sensorId = self._next_sensor_id
        sensor.clientSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [1]
        sensor.description = "sensor_" + str(self._next_sensor_id)
        sensor.state = 0
        sensor.dataType = SensorDataType.GPS
        sensor.data = SensorDataGPS(99.0,
                                    10.0,
                                    1337)
        sensor.error_state = SensorErrorState()
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor.deepcopy(sensor))

        self._next_node_id += 1
        self._next_sensor_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_server_" + str(self._next_node_id)
        node.nodeType = "server"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = self._next_node_id
        sensor.sensorId = self._next_sensor_id
        sensor.clientSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [3]
        sensor.description = "server_sensor_" + str(self._next_sensor_id)
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.error_state = SensorErrorState()
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor.deepcopy(sensor))

        self._next_node_id += 1
        self._next_sensor_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_server_" + str(self._next_node_id)
        node.nodeType = "server"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = self._next_node_id
        sensor.sensorId = self._next_sensor_id
        sensor.clientSensorId = 4
        sensor.alertDelay = 0
        sensor.alertLevels = [1, 2]
        sensor.description = "server_sensor_" + str(self._next_sensor_id)
        sensor.state = 1
        sensor.dataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.error_state = SensorErrorState()
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor.deepcopy(sensor))

        self._next_node_id += 1
        self._next_sensor_id += 1

        node = ManagerObjNode()
        node.nodeId = self._next_node_id
        node.hostname = "hostname_server_" + str(self._next_node_id)
        node.nodeType = "server"
        node.instance = "instance_" + str(self._next_node_id)
        node.connected = 1
        node.version = 1.0
        node.rev = 0
        node.username = "username_" + str(self._next_node_id)
        node.persistent = 1
        self.nodes.append(node)
        system_data.update_node(ManagerObjNode.deepcopy(node))

        sensor = ManagerObjSensor()
        sensor.nodeId = self._next_node_id
        sensor.sensorId = self._next_sensor_id
        sensor.clientSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [2]
        sensor.description = "server_sensor_" + str(self._next_sensor_id)
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.error_state = SensorErrorState()
        self.sensors.append(sensor)
        system_data.update_sensor(ManagerObjSensor.deepcopy(sensor))

        self._next_node_id += 1
        self._next_sensor_id += 1

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
        option.value = 1
        self.options.append(option)
        system_data.update_option(ManagerObjOption.deepcopy(option))

        option = ManagerObjOption()
        option.type = "type_2"
        option.value = 2
        self.options.append(option)
        system_data.update_option(ManagerObjOption.deepcopy(option))

        option = ManagerObjOption()
        option.type = "type_3"
        option.value = 3
        self.options.append(option)
        system_data.update_option(ManagerObjOption.deepcopy(option))

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
        profile.profileId = 0
        profile.name = "profile_0"
        self.profiles.append(profile)
        system_data.update_profile(ManagerObjProfile.deepcopy(profile))

        profile = ManagerObjProfile()
        profile.profileId = 1
        profile.name = "profile_1"
        self.profiles.append(profile)
        system_data.update_profile(ManagerObjProfile.deepcopy(profile))

        profile = ManagerObjProfile()
        profile.profileId = 2
        profile.name = "profile_2"
        self.profiles.append(profile)
        system_data.update_profile(ManagerObjProfile.deepcopy(profile))

        return system_data

    def _create_system_data(self) -> SystemData:
        system_data = self._create_options()
        system_data = self._create_profiles(system_data)
        system_data = self._create_alert_levels(system_data)
        system_data = self._create_alerts(system_data)
        system_data = self._create_managers(system_data)
        system_data = self._create_sensors(system_data)

        return system_data
