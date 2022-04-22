import tempfile
import os
import logging
import shutil
from unittest import TestCase
from typing import Optional, List
from lib.localObjects import Option, Sensor, Node
from lib.storage.sqlite import Sqlite
from lib.globalData.globalData import GlobalData
from lib.globalData.sensorObjects import SensorErrorState, SensorDataNone, SensorDataInt, SensorDataFloat, \
    SensorDataGPS, SensorDataType


class TestStorageCore(TestCase):

    def _clean_up_storage(self):
        if self.temp_dir is not None:
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass

    def _init_storage(self) -> Sqlite:
        self.addCleanup(self._clean_up_storage)

        self.temp_dir = tempfile.mkdtemp()
        self.global_data = GlobalData()
        self.global_data.storageBackendSqliteFile = os.path.join(self.temp_dir, "database.db")
        self.global_data.logger = logging.getLogger("server")

        storage = Sqlite(self.global_data.storageBackendSqliteFile,
                         self.global_data)
        self.nodes = []  # type: List[Node]
        self.options = []  # type: List[Option]
        self.sensors = []  # type: List[Sensor]

        return storage


    def _create_nodes(self, storage: Optional[Sqlite] = None) -> Sqlite:

        if storage is None:
            storage = self._init_storage()

        node = Node()
        node.id = 1
        node.hostname = "host_1"
        node.username = "user_1"
        node.nodeType = "sensor"
        node.instance = "instance_1"
        node.connected = 1
        node.version = 1
        node.rev = 1
        node.persistent = 1
        self.nodes.append(node)
        storage.addNode(node.username,
                        node.hostname,
                        node.nodeType,
                        node.instance,
                        node.version,
                        node.rev,
                        node.persistent)

        return storage

    def _create_options(self, storage: Optional[Sqlite] = None) -> Sqlite:

        if storage is None:
            storage = self._init_storage()

        # Account for implicit option "profile" which is created on storage creation.
        option = storage.get_option_by_type("profile")
        self.options.append(option)

        option = Option()
        option.type = "type_1"
        option.value = 1
        self.options.append(option)
        storage.update_option_by_obj(option)

        option = Option()
        option.type = "type_2"
        option.value = 2
        self.options.append(option)
        storage.update_option_by_obj(option)

        option = Option()
        option.type = "type_3"
        option.value = 3
        self.options.append(option)
        storage.update_option_by_obj(option)

        return storage

    def _create_sensors(self, storage: Optional[Sqlite] = None) -> Sqlite:

        if storage is None:
            storage = self._init_storage()

        self._create_nodes(storage)

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.clientSensorId = 1
        sensor.description = "sensor_none"
        sensor.state = 0
        sensor.error_state = SensorErrorState()
        sensor.alertLevels.append(1)
        sensor.lastStateUpdated = 1
        sensor.alertDelay = 1
        sensor.dataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        storage.upsert_sensor(sensor)
        sensor.sensorId = storage.getSensorId(sensor.nodeId, sensor.clientSensorId)
        self.sensors.append(sensor)

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.clientSensorId = 2
        sensor.description = "sensor_int"
        sensor.state = 0
        sensor.error_state = SensorErrorState()
        sensor.alertLevels.append(1)
        sensor.lastStateUpdated = 2
        sensor.alertDelay = 2
        sensor.dataType = SensorDataType.INT
        sensor.data = SensorDataInt(2, "test unit")
        storage.upsert_sensor(sensor)
        sensor.sensorId = storage.getSensorId(sensor.nodeId, sensor.clientSensorId)
        self.sensors.append(sensor)

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.clientSensorId = 3
        sensor.description = "sensor_none"
        sensor.state = 0
        sensor.error_state = SensorErrorState()
        sensor.alertLevels.append(1)
        sensor.lastStateUpdated = 3
        sensor.alertDelay = 3
        sensor.dataType = SensorDataType.FLOAT
        sensor.data = SensorDataFloat(3.0, "test unit")
        storage.upsert_sensor(sensor)
        sensor.sensorId = storage.getSensorId(sensor.nodeId, sensor.clientSensorId)
        self.sensors.append(sensor)

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.clientSensorId = 4
        sensor.description = "sensor_none"
        sensor.state = 0
        sensor.error_state = SensorErrorState()
        sensor.alertLevels.append(1)
        sensor.lastStateUpdated = 4
        sensor.alertDelay = 4
        sensor.dataType = SensorDataType.GPS
        sensor.data = SensorDataGPS(4.0, 4.0, 4)
        storage.upsert_sensor(sensor)
        sensor.sensorId = storage.getSensorId(sensor.nodeId, sensor.clientSensorId)
        self.sensors.append(sensor)

        return storage
