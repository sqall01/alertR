from unittest import TestCase
from lib.globalData.systemData import SystemData
from lib.localObjects import Node, Sensor, SensorDataType


class TestSystemDataSensor(TestCase):

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
