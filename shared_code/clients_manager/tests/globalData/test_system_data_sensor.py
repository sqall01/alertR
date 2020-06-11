from tests.globalData.core import TestSystemDataCore
from lib.globalData.systemData import SystemData
from lib.globalData.localObjects import Node, Sensor, SensorDataType, SensorAlert


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
            temp_sensor = Sensor().deepcopy(self.sensors[i])
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

    def test_delete_sensor(self):
        """
        Test Sensor object deleting.
        """
        system_data = self._create_sensors()
        number_sensor_alerts = 3

        for i in range(len(self.sensors)):
            for j in range(number_sensor_alerts):
                temp_sensor_alert = SensorAlert()
                temp_sensor_alert.rulesActivated = False
                temp_sensor_alert.sensorId = self.sensors[i % len(self.sensors)].sensorId
                temp_sensor_alert.state = j % 2
                temp_sensor_alert.alertLevels = list(self.sensors[i % len(self.sensors)].alertLevels)
                temp_sensor_alert.hasOptionalData = False
                temp_sensor_alert.optionalData = None
                temp_sensor_alert.changeState = (j % 2) == 0
                temp_sensor_alert.hasLatestData = False
                temp_sensor_alert.dataType = SensorDataType.NONE
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

            if (stored_sensor.remoteSensorId != curr_sensor.remoteSensorId
                    or stored_sensor.description != curr_sensor.description
                    or stored_sensor.alertDelay != curr_sensor.alertDelay
                    or stored_sensor.lastStateUpdated != curr_sensor.lastStateUpdated
                    or stored_sensor.state != curr_sensor.state
                    or stored_sensor.dataType != curr_sensor.dataType
                    or stored_sensor.data != curr_sensor.data
                    or any(map(lambda x: x not in curr_sensor.alertLevels, stored_sensor.alertLevels))
                    or any(map(lambda x: x not in stored_sensor.alertLevels, curr_sensor.alertLevels))):
                self.fail("Stored object does not have initially correct content.")

            sensor_alert = SensorAlert()
            sensor_alert.rulesActivated = False
            sensor_alert.sensorId = curr_sensor.sensorId
            sensor_alert.state = 1 - curr_sensor.state
            sensor_alert.alertLevels = curr_sensor.alertLevels
            sensor_alert.hasOptionalData = False
            sensor_alert.optionalData = None
            sensor_alert.changeState = True
            sensor_alert.hasLatestData = False
            sensor_alert.dataType = SensorDataType.NONE
            sensor_alert.timeReceived = 0
            system_data.add_sensor_alert(sensor_alert)

            if (stored_sensor.remoteSensorId != curr_sensor.remoteSensorId
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
                        if (stored_sensor.remoteSensorId != gt_sensor.remoteSensorId
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

            if (stored_sensor.remoteSensorId != curr_sensor.remoteSensorId
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

            if (stored_sensor.remoteSensorId != curr_sensor.remoteSensorId
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
                        if (stored_sensor.remoteSensorId != gt_sensor.remoteSensorId
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
