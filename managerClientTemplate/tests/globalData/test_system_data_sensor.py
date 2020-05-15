from tests.globalData.core import TestSystemDataCore
from lib.globalData.systemData import SystemData
from lib.localObjects import Node, Sensor, SensorDataType


class TestSystemDataSensor(TestSystemDataCore):

    def _invalid_wrong_node_type(self, system_data: SystemData):
        # Test invalid node type.
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

    def _invalid_node_missing(self, system_data: SystemData):
        # Test non-existing node.
        sensor = Sensor()
        sensor.nodeId = 99
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

    def _invalid_alert_level_missing(self, system_data: SystemData):
        # Test non-existing alert level.
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

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.sensorId = 1
        sensor.remoteSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [99]
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

    def test_invalid_sensor_adding(self):
        """
        Tests sanity checks for Sensor object adding.
        """
        system_data = SystemData()
        self._invalid_wrong_node_type(system_data)

        system_data = SystemData()
        self._invalid_node_missing(system_data)

        system_data = SystemData()
        self._invalid_alert_level_missing(system_data)

    def test_invalid_sensor_updating(self):
        """
        Tests sanity checks for Sensor object updating.
        """
        system_data = self._create_system_data()
        self._invalid_wrong_node_type(system_data)

        system_data = self._create_system_data()
        self._invalid_node_missing(system_data)

        system_data = self._create_system_data()
        self._invalid_alert_level_missing(system_data)

    def test_update_sensor(self):
        """
        Test Sensor object updating.
        """
        system_data = self._create_system_data()

        # Create changes that should be copied to the stored object.
        new_sensors = []
        for i in range(len(self.sensors)):
            temp_sensor = Sensor().deepCopy(self.sensors[i])
            temp_sensor.description = "new_sensor_" + str(i + 1)
            temp_sensor.remoteSensorId = i
            temp_sensor.alertDelay = i + 10
            temp_sensor.lastStateUpdated = i + 10
            temp_sensor.state = i % 2
            temp_sensor.dataType = SensorDataType.INT
            temp_sensor.data = i
            # We started the alert levels in our test data with level 1.
            temp_sensor.alertLevels = [(i % len(self.alert_levels)) + 1]
            new_sensors.append(temp_sensor)

        for i in range(len(new_sensors)):

            # Update store with new object data.
            temp_sensor = new_sensors[i]
            system_data.update_sensor(temp_sensor)

            gt_storage = []
            for j in range(i+1):
                gt_storage.append(new_sensors[j])
            for j in range(i+1, len(new_sensors)):
                gt_storage.append(self.sensors[j])

            stored_sensors = system_data.get_sensors_list()
            if len(stored_sensors) != len(gt_storage):
                self.fail("Wrong number of objects stored.")

            already_processed = []
            for stored_sensor in stored_sensors:
                found = False
                for gt_sensor in gt_storage:
                    if stored_sensor.nodeId == gt_sensor.nodeId and stored_sensor.sensorId == gt_sensor.sensorId:
                        found = True

                        # Check which objects we already processed to see if we hold an object with
                        # duplicated values.
                        if gt_sensor in already_processed:
                            self.fail()
                        already_processed.append(gt_sensor)

                        # Only the content of the object should have changed, not the object itself.
                        if stored_sensor == gt_sensor:
                            self.fail("Store changed object, not content of existing object.")

                        if (stored_sensor.remoteSensorId != gt_sensor.remoteSensorId
                                or stored_sensor.description != gt_sensor.description
                                or stored_sensor.alertDelay != gt_sensor.alertDelay
                                or stored_sensor.lastStateUpdated != gt_sensor.lastStateUpdated
                                or stored_sensor.state != gt_sensor.state
                                or stored_sensor.dataType != gt_sensor.dataType
                                or stored_sensor.data != gt_sensor.data
                                or any(map(lambda x: x not in gt_sensor.alertLevels, stored_sensor.alertLevels))
                                or any(map(lambda x: x not in stored_sensor.alertLevels, gt_sensor.alertLevels))):

                            self.fail("Stored object does not have correct content.")

                        break

                if not found:
                    self.fail("Not able to find modified Sensor object.")
