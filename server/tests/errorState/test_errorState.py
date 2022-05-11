import logging
from typing import List, Tuple, Optional, Dict
from collections import defaultdict
from unittest import TestCase
from lib.localObjects import Node, Sensor
from lib.globalData.globalData import GlobalData
from lib.globalData.sensorObjects import SensorErrorState, SensorDataType, SensorDataNone, SensorDataInt, \
    SensorDataFloat
from lib.errorState.errorState import ErrorStateExecuter
# noinspection PyProtectedMember
from lib.storage.core import _Storage


# noinspection PyAbstractClass
class MockStorage(_Storage):

    def __init__(self):
        self.is_working = True

        self._sensor_data = defaultdict(list)
        self._sensor_state = defaultdict(list)

        self._sensors_in_error = []  # type: List[int]

        self._node = None  # type: Optional[Node]
        self._sensors = dict()  # type: Dict[int, Sensor]

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, value: Node):
        self._node = value

    @property
    def sensor_data(self):
        return self._sensor_data

    @property
    def sensor_state(self):
        return self._sensor_state

    @property
    def sensors_in_error(self):
        return self._sensors_in_error

    @sensors_in_error.setter
    def sensors_in_error(self, value: List[int]):
        self._sensors_in_error = value

    def get_sensor_error_state(self,
                               sensor_id: int,
                               logger: logging.Logger = None) -> Optional[SensorErrorState]:
        raise NotImplementedError("TODO")

    def get_sensor_ids_in_error_state(self,
                                      logger: logging.Logger = None) -> List[int]:

        if not self.is_working:
            return []

        return self._sensors_in_error

    def getNodeById(self,
                    nodeId: int,
                    logger: logging.Logger = None) -> Optional[Node]:
        raise NotImplementedError("TODO")

    def getSensorId(self,
                    nodeId: int,
                    clientSensorId: int,
                    logger: logging.Logger = None) -> Optional[int]:
        raise NotImplementedError("TODO")

    def update_sensor_error_state(self,
                                  node_id: int,
                                  client_sensor_id: int,
                                  error_state: SensorErrorState,
                                  logger: logging.Logger = None) -> bool:
        raise NotImplementedError("TODO")

    def upsert_sensor(self,
                      sensor: Sensor,
                      logger: logging.Logger = None) -> bool:
        self._sensors[sensor.sensorId] = sensor
        return True


class TestErrorState(TestCase):

    def _create_error_state_executer(self) -> Tuple[ErrorStateExecuter, GlobalData]:

        self.nodes = []  # type: List[Node]
        self.sensors = []  # type: List[Sensor]

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Error State Test Case")

        global_data.storage = MockStorage()

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
        global_data.storage.node = node

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.sensorId = 1
        sensor.clientSensorId = 1
        sensor.description = "sensor_none"
        sensor.state = 0
        sensor.error_state = SensorErrorState()
        sensor.alertLevels.append(1)
        sensor.lastStateUpdated = 1
        sensor.alertDelay = 1
        sensor.dataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        global_data.storage.upsert_sensor(sensor)
        self.sensors.append(sensor)

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.sensorId = 2
        sensor.clientSensorId = 2
        sensor.description = "sensor_int"
        sensor.state = 0
        sensor.error_state = SensorErrorState()
        sensor.alertLevels.append(1)
        sensor.lastStateUpdated = 2
        sensor.alertDelay = 2
        sensor.dataType = SensorDataType.INT
        sensor.data = SensorDataInt(2, "test unit")
        global_data.storage.upsert_sensor(sensor)
        self.sensors.append(sensor)

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.sensorId = 3
        sensor.clientSensorId = 3
        sensor.description = "sensor_float"
        sensor.state = 0
        sensor.error_state = SensorErrorState()
        sensor.alertLevels.append(1)
        sensor.lastStateUpdated = 3
        sensor.alertDelay = 3
        sensor.dataType = SensorDataType.FLOAT
        sensor.data = SensorDataFloat(3.0, "test unit")
        global_data.storage.upsert_sensor(sensor)
        self.sensors.append(sensor)

        executer = ErrorStateExecuter(global_data)
        return executer, global_data

    def test_update_sensor_error_state_sensor_by_sensor_id(self):

        executer, global_data = self._create_error_state_executer()

        raise NotImplementedError("TODO")

