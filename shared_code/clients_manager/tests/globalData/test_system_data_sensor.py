from tests.globalData.core import TestSystemDataCore
from tests.globalData.util import compare_sensors_content
from lib.globalData.systemData import SystemData
from lib.globalData.managerObjects import ManagerObjNode, ManagerObjSensor, ManagerObjSensorAlert
from lib.globalData.sensorObjects import SensorDataType, SensorDataNone, SensorDataInt


class TestSystemDataSensor(TestSystemDataCore):

    def _invalid_wrong_node_type(self, system_data: SystemData):
        # Test invalid node type.
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
        system_data.update_node(node)

        sensor = ManagerObjSensor()
        sensor.nodeId = 1
        sensor.sensorId = 1
        sensor.clientSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = []
        sensor.description = "sensor_1"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        is_exception = False
        try:
            system_data.update_sensor(sensor)
        except ValueError as e:
            self.assertTrue("not of correct type for corresponding sensor" in str(e))
            is_exception = True
        if not is_exception:
            self.fail("Exception because of wrong node type expected.")

        system_data = SystemData()

    def _invalid_node_missing(self, system_data: SystemData):
        # Test non-existing node.
        sensor = ManagerObjSensor()
        sensor.nodeId = 99
        sensor.sensorId = 1
        sensor.clientSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = []
        sensor.description = "sensor_1"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        is_exception = False
        try:
            system_data.update_sensor(sensor)
        except ValueError as e:
            self.assertTrue("for corresponding sensor" in str(e) and "does not exist" in str(e))
            is_exception = True
        if not is_exception:
            self.fail("Exception because of non-existing node expected.")

    def _invalid_alert_level_missing(self, system_data: SystemData):
        # Test non-existing alert level.
        node = ManagerObjNode()
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

        sensor = ManagerObjSensor()
        sensor.nodeId = 1
        sensor.sensorId = 1
        sensor.clientSensorId = 1
        sensor.alertDelay = 0
        sensor.alertLevels = [99]
        sensor.description = "sensor_1"
        sensor.lastStateUpdated = 0
        sensor.state = 0
        sensor.dataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        is_exception = False
        try:
            system_data.update_sensor(sensor)
        except ValueError as e:
            self.assertTrue("Alert Level" in str(e) and "does not exist for sensor" in str(e))
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
            temp_sensor = ManagerObjSensor.deepcopy(self.sensors[i])
            temp_sensor.description = "new_sensor_" + str(i + 1)
            temp_sensor.clientSensorId = i
            temp_sensor.alertDelay = i + 10
            temp_sensor.lastStateUpdated = i + 10
            temp_sensor.state = i % 2
            temp_sensor.dataType = SensorDataType.INT
            temp_sensor.data = SensorDataInt(i, "test unit")
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
            compare_sensors_content(self, gt_storage, stored_sensors)

    def test_delete_sensor(self):
        """
        Test dataSensor object deleting.
        """
        system_data = self._create_sensors()
        number_sensor_alerts = 3

        for i in range(len(self.sensors)):
            for j in range(number_sensor_alerts):
                temp_sensor_alert = ManagerObjSensorAlert()
                temp_sensor_alert.sensorId = self.sensors[i % len(self.sensors)].sensorId
                temp_sensor_alert.state = j % 2
                temp_sensor_alert.alertLevels = list(self.sensors[i % len(self.sensors)].alertLevels)
                temp_sensor_alert.hasOptionalData = False
                temp_sensor_alert.optionalData = None
                temp_sensor_alert.changeState = (j % 2) == 0
                temp_sensor_alert.hasLatestData = False
                temp_sensor_alert.dataType = self.sensors[i % len(self.sensors)].dataType
                temp_sensor_alert.data = self.sensors[i % len(self.sensors)].data
                temp_sensor_alert.timeReceived = j
                system_data.add_sensor_alert(temp_sensor_alert)

        idx = 0
        for sensor in system_data.get_sensors_list():

            system_data.delete_sensor_by_id(sensor.sensorId)

            if not sensor.is_deleted():
                self.fail("Sensor object not marked as deleted.")

            for stored_sensor in system_data.get_sensors_list():
                if stored_sensor.is_deleted():
                    self.fail("Stored Sensor object marked as deleted.")

                if sensor.sensorId == stored_sensor.sensorId:
                    self.fail("Store still contains Sensor with id that was deleted.")

            if ((len(self.sensors) - (idx + 1)) * number_sensor_alerts) != len(system_data.get_sensor_alerts_list()):
                self.fail("Wrong number of Sensor Alerts remaining stored.")

            for sensor_alert in system_data.get_sensor_alerts_list():
                if sensor_alert.sensorId == sensor.sensorId:
                    self.fail("Sensor Alerts corresponding to Sensor object not deleted.")

            idx += 1

    def test_sensor_alert(self):
        """
        Test Sensor Alert state change.
        """
        system_data = self._create_sensors()

        for i in range(len(self.sensors)):
            curr_sensor = self.sensors[i]
            stored_sensor = system_data.get_sensor_by_id(curr_sensor.sensorId)

            if (stored_sensor.clientSensorId != curr_sensor.clientSensorId
                    or stored_sensor.description != curr_sensor.description
                    or stored_sensor.alertDelay != curr_sensor.alertDelay
                    or stored_sensor.lastStateUpdated != curr_sensor.lastStateUpdated
                    or stored_sensor.state != curr_sensor.state
                    or stored_sensor.dataType != curr_sensor.dataType
                    or stored_sensor.data != curr_sensor.data
                    or any(map(lambda x: x not in curr_sensor.alertLevels, stored_sensor.alertLevels))
                    or any(map(lambda x: x not in stored_sensor.alertLevels, curr_sensor.alertLevels))):
                self.fail("Stored object does not have initially correct content.")

            sensor_alert = ManagerObjSensorAlert()
            sensor_alert.sensorId = curr_sensor.sensorId
            sensor_alert.state = 1 - curr_sensor.state
            sensor_alert.alertLevels = curr_sensor.alertLevels
            sensor_alert.hasOptionalData = False
            sensor_alert.optionalData = None
            sensor_alert.changeState = True
            sensor_alert.hasLatestData = False
            sensor_alert.dataType = curr_sensor.dataType
            sensor_alert.data = curr_sensor.data
            sensor_alert.timeReceived = 0
            system_data.add_sensor_alert(sensor_alert)

            if (stored_sensor.clientSensorId != curr_sensor.clientSensorId
                    or stored_sensor.description != curr_sensor.description
                    or stored_sensor.alertDelay != curr_sensor.alertDelay
                    or stored_sensor.lastStateUpdated != curr_sensor.lastStateUpdated
                    or stored_sensor.dataType != curr_sensor.dataType
                    or stored_sensor.data != curr_sensor.data
                    or any(map(lambda x: x not in curr_sensor.alertLevels, stored_sensor.alertLevels))
                    or any(map(lambda x: x not in stored_sensor.alertLevels, curr_sensor.alertLevels))):
                self.fail("Stored object does not have correct content after adding Sensor Alert.")

            if stored_sensor.state == curr_sensor.state:
                self.fail("State of Sensor object was not updated.")

            # Check nothing has changed in other Sensor objects
            # (update state of current sensor manually for this check).
            curr_sensor.state = stored_sensor.state
            for gt_sensor in self.sensors:
                found = False
                for stored_sensor in system_data.get_sensors_list():
                    if stored_sensor.sensorId == gt_sensor.sensorId:
                        found = True
                        if (stored_sensor.clientSensorId != gt_sensor.clientSensorId
                                or stored_sensor.description != gt_sensor.description
                                or stored_sensor.alertDelay != gt_sensor.alertDelay
                                or stored_sensor.lastStateUpdated != gt_sensor.lastStateUpdated
                                or stored_sensor.state != gt_sensor.state
                                or stored_sensor.dataType != gt_sensor.dataType
                                or stored_sensor.data != gt_sensor.data
                                or any(map(lambda x: x not in gt_sensor.alertLevels, stored_sensor.alertLevels))
                                or any(map(lambda x: x not in stored_sensor.alertLevels, gt_sensor.alertLevels))):
                            self.fail("Sensor content has changed.")

                        break

                if not found:
                    self.fail("Not able to find Sensor object corresponding to created sensors.")

            if len(self.sensors) != len(system_data.get_sensors_list()):
                self.fail("Number of stored Sensor objects differ from created ones.")

    def test_sensor_state_change(self):
        """
        Test Sensor state change.
        """
        system_data = self._create_sensors()

        for i in range(len(self.sensors)):
            curr_sensor = self.sensors[i]
            stored_sensor = system_data.get_sensor_by_id(curr_sensor.sensorId)

            if (stored_sensor.clientSensorId != curr_sensor.clientSensorId
                    or stored_sensor.description != curr_sensor.description
                    or stored_sensor.alertDelay != curr_sensor.alertDelay
                    or stored_sensor.lastStateUpdated != curr_sensor.lastStateUpdated
                    or stored_sensor.state != curr_sensor.state
                    or stored_sensor.dataType != curr_sensor.dataType
                    or stored_sensor.data != curr_sensor.data
                    or any(map(lambda x: x not in curr_sensor.alertLevels, stored_sensor.alertLevels))
                    or any(map(lambda x: x not in stored_sensor.alertLevels, curr_sensor.alertLevels))):
                self.fail("Stored object does not have initially correct content.")

            system_data.sensor_state_change(stored_sensor.sensorId,
                                            1 - stored_sensor.state,
                                            stored_sensor.dataType,
                                            stored_sensor.data)

            if (stored_sensor.clientSensorId != curr_sensor.clientSensorId
                    or stored_sensor.description != curr_sensor.description
                    or stored_sensor.alertDelay != curr_sensor.alertDelay
                    or stored_sensor.lastStateUpdated != curr_sensor.lastStateUpdated
                    or stored_sensor.dataType != curr_sensor.dataType
                    or stored_sensor.data != curr_sensor.data
                    or any(map(lambda x: x not in curr_sensor.alertLevels, stored_sensor.alertLevels))
                    or any(map(lambda x: x not in stored_sensor.alertLevels, curr_sensor.alertLevels))):
                self.fail("Stored object does not have correct content after state change.")

            if stored_sensor.state == curr_sensor.state:
                self.fail("State of Sensor object was not updated.")

            # Check nothing has changed in other Sensor objects
            # (update state of current sensor manually for this check).
            curr_sensor.state = stored_sensor.state
            for gt_sensor in self.sensors:
                found = False
                for stored_sensor in system_data.get_sensors_list():
                    if stored_sensor.sensorId == gt_sensor.sensorId:
                        found = True
                        if (stored_sensor.clientSensorId != gt_sensor.clientSensorId
                                or stored_sensor.description != gt_sensor.description
                                or stored_sensor.alertDelay != gt_sensor.alertDelay
                                or stored_sensor.lastStateUpdated != gt_sensor.lastStateUpdated
                                or stored_sensor.state != gt_sensor.state
                                or stored_sensor.dataType != gt_sensor.dataType
                                or stored_sensor.data != gt_sensor.data
                                or any(map(lambda x: x not in gt_sensor.alertLevels, stored_sensor.alertLevels))
                                or any(map(lambda x: x not in stored_sensor.alertLevels, gt_sensor.alertLevels))):
                            self.fail("Sensor content has changed.")

                        break

                if not found:
                    self.fail("Not able to find Sensor object corresponding to created sensors.")

            if len(self.sensors) != len(system_data.get_sensors_list()):
                self.fail("Number of stored Sensor objects differ from created ones.")
