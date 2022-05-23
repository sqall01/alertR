import logging
import time
from typing import List, Tuple, Optional, Dict
from unittest import TestCase
from lib.localObjects import Node, Sensor
from lib.globalData.globalData import GlobalData
from lib.globalData.sensorObjects import SensorErrorState, SensorDataType, SensorDataNone, SensorDataInt, \
    SensorDataFloat, SensorDataGPS
from lib.errorState.errorState import ErrorStateExecuter
# noinspection PyProtectedMember
from lib.storage.core import _Storage
from lib.internalSensors.sensorErrorState import SensorErrorStateSensor


class MockSensorErrorStateSensor(SensorErrorStateSensor):

    def __init__(self,
                 global_data: GlobalData):
        super().__init__(global_data)
        self._sensor_error_states = []  # type: List[Tuple[str, int, int, SensorErrorState]]

    @property
    def sensor_error_states(self):
        return self._sensor_error_states

    def initialize(self):
        pass

    def process_error_state(self, username: str, client_sensor_id: int, sensor_id: int, error_state: SensorErrorState):
        self._sensor_error_states.append((username, client_sensor_id, sensor_id, error_state))


# noinspection PyAbstractClass
class MockStorage(_Storage):

    def __init__(self):
        self.is_working = True

        self._node = None  # type: Optional[Node]
        self._sensors = dict()  # type: Dict[int, Sensor]

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, value: Node):
        self._node = value

    @property
    def sensors(self) -> List[Sensor]:
        return list(self._sensors.values())

    def get_sensor_error_state(self,
                               sensor_id: int,
                               logger: logging.Logger = None) -> Optional[SensorErrorState]:
        if not self.is_working:
            return None

        return self._sensors[sensor_id].error_state

    def get_sensor_ids_in_error_state(self,
                                      logger: logging.Logger = None) -> List[int]:

        if not self.is_working:
            return []

        return [x.sensorId for x in filter(lambda x: x.error_state.state != SensorErrorState.OK,
                                           self._sensors.values())]

    def getNodeById(self,
                    nodeId: int,
                    logger: logging.Logger = None) -> Optional[Node]:
        if not self.is_working:
            return None

        if self.node.id != nodeId:
            raise ValueError("Wrong node id.")

        return self.node

    def getSensorById(self,
                      sensorId: int,
                      logger: logging.Logger = None) -> Optional[Sensor]:
        if not self.is_working:
            return None

        for sensor in self.sensors:
            if sensor.sensorId == sensorId:
                return sensor

        raise ValueError("Sensor id unknown.")

    def getSensorId(self,
                    nodeId: int,
                    clientSensorId: int,
                    logger: logging.Logger = None) -> Optional[int]:
        if not self.is_working:
            return None

        if self.node.id != nodeId:
            raise ValueError("Wrong node id.")

        for sensor in self.sensors:
            if sensor.clientSensorId == clientSensorId:
                return sensor.sensorId

        raise ValueError("Client sensor id unknown.")

    def update_sensor_error_state(self,
                                  node_id: int,
                                  client_sensor_id: int,
                                  error_state: SensorErrorState,
                                  logger: logging.Logger = None) -> bool:
        if not self.is_working:
            return False

        if self.node.id != node_id:
            raise ValueError("Wrong node id.")

        for sensor in self.sensors:
            if sensor.clientSensorId == client_sensor_id:
                sensor.error_state = error_state
                return True

        raise ValueError("Client sensor id unknown.")

    def upsert_sensor(self,
                      sensor: Sensor,
                      logger: logging.Logger = None) -> bool:
        self._sensors[sensor.sensorId] = sensor
        return True


class TestErrorState(TestCase):

    def _create_error_state_executer(self) -> Tuple[ErrorStateExecuter, GlobalData]:

        self.node = None  # type: Optional[Node]
        self.sensors = []  # type: List[Sensor]

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Error State Test Case")

        global_data.storage = MockStorage()

        self.internal_sensor = MockSensorErrorStateSensor(global_data)
        global_data.internalSensors.append(self.internal_sensor)

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
        self.node = node
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

        sensor = Sensor()
        sensor.nodeId = 1
        sensor.sensorId = 4
        sensor.clientSensorId = 4
        sensor.description = "sensor_gps"
        sensor.state = 0
        sensor.error_state = SensorErrorState()
        sensor.alertLevels.append(1)
        sensor.lastStateUpdated = 4
        sensor.alertDelay = 4
        sensor.dataType = SensorDataType.FLOAT
        sensor.data = SensorDataGPS(0, 1, 2)
        global_data.storage.upsert_sensor(sensor)
        self.sensors.append(sensor)

        executer = ErrorStateExecuter(global_data)
        return executer, global_data

    def test_process_error_state_changes_empty_queue(self):
        """
        Tests error state change processing with an empty queue.
        """

        executer, global_data = self._create_error_state_executer()

        executer._process_error_state_changes()

        for sensor in global_data.storage.sensors:
            self.assertEqual(sensor.error_state.state, SensorErrorState.OK)

    def test_process_error_state_changes_one_queue(self):
        """
        Tests error state change processing with one element in queue.
        """

        executer, global_data = self._create_error_state_executer()

        executer.add_error_state(self.node.id,
                                 self.sensors[0].sensorId,
                                 SensorErrorState(SensorErrorState.GenericError, "Test Error"))

        executer._process_error_state_changes()

        one_error = False
        for sensor in global_data.storage.sensors:
            if sensor.sensorId == self.sensors[0].sensorId:
                self.assertEqual(sensor.error_state.state, SensorErrorState.GenericError)
                self.assertEqual(sensor.error_state.msg, "Test Error")
                one_error = True

            else:
                self.assertEqual(sensor.error_state.state, SensorErrorState.OK)

        self.assertTrue(one_error)

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 1)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.GenericError)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].msg, "Test Error")

    def test_process_error_state_changes_two_queue(self):
        """
        Tests error state change processing with two elements in queue.
        """

        executer, global_data = self._create_error_state_executer()

        executer.add_error_state(self.node.id,
                                 self.sensors[0].sensorId,
                                 SensorErrorState(SensorErrorState.GenericError, "Test Error"))

        executer.add_error_state(self.node.id,
                                 self.sensors[-1].sensorId,
                                 SensorErrorState(SensorErrorState.ProcessingError, "Test Error 2"))

        executer._process_error_state_changes()

        one_error = False
        two_error = False
        for sensor in global_data.storage.sensors:
            if sensor.sensorId == self.sensors[0].sensorId:
                self.assertEqual(sensor.error_state.state, SensorErrorState.GenericError)
                self.assertEqual(sensor.error_state.msg, "Test Error")
                one_error = True

            elif sensor.sensorId == self.sensors[-1].sensorId:
                self.assertEqual(sensor.error_state.state, SensorErrorState.ProcessingError)
                self.assertEqual(sensor.error_state.msg, "Test Error 2")
                two_error = True

            else:
                self.assertEqual(sensor.error_state.state, SensorErrorState.OK)

        self.assertTrue(one_error)
        self.assertTrue(two_error)

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 2)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.GenericError)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].msg, "Test Error")
        self.assertEqual(self.internal_sensor.sensor_error_states[1][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[1][1], self.sensors[-1].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[1][2], self.sensors[-1].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[1][3].state, SensorErrorState.ProcessingError)
        self.assertEqual(self.internal_sensor.sensor_error_states[1][3].msg, "Test Error 2")

    def test_update_sensor_error_state_sensor_by_sensor_id_no_sensor(self):
        """
        Tests behavior of function when no internal sensor exists.
        """

        executer, global_data = self._create_error_state_executer()

        # Remove internal sensor reference.
        executer._internal_sensor = None

        executer._update_sensor_error_state_sensor_by_sensor_id(self.sensors[0].sensorId,
                                                                SensorErrorState(SensorErrorState.GenericError,
                                                                                 "Test Error"))

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

    def test_update_sensor_error_state_sensor_by_sensor_id(self):
        """
        Tests passing of sensor error state to internal sensor.
        """

        executer, global_data = self._create_error_state_executer()

        executer._update_sensor_error_state_sensor_by_sensor_id(self.sensors[0].sensorId,
                                                                SensorErrorState(SensorErrorState.GenericError,
                                                                                 "Test Error"))

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 1)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.GenericError)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].msg, "Test Error")

    def test_update_sensor_error_state_sensor_no_sensor(self):
        """
        Tests behavior of function when no internal sensor exists.
        """

        executer, global_data = self._create_error_state_executer()

        # Remove internal sensor reference.
        executer._internal_sensor = None

        executer._update_sensor_error_state_sensor(self.node.id,
                                                   self.sensors[0].clientSensorId,
                                                   SensorErrorState(SensorErrorState.GenericError, "Test Error"))

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

    def test_update_sensor_error_state_sensor(self):
        """
        Tests passing of sensor error state to internal sensor.
        """

        executer, global_data = self._create_error_state_executer()

        executer._update_sensor_error_state_sensor(self.node.id,
                                                   self.sensors[0].clientSensorId,
                                                   SensorErrorState(SensorErrorState.GenericError, "Test Error"))

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 1)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.GenericError)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].msg, "Test Error")

    def test_process_sensor_error_states_one_error(self):
        """
        Tests sensor error state processing to recover from missed error state events (one missed error state).
        """

        executer, global_data = self._create_error_state_executer()

        global_data.storage.update_sensor_error_state(self.node.id,
                                                      self.sensors[0].clientSensorId,
                                                      SensorErrorState(SensorErrorState.GenericError, "Test Error"))

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

        executer._process_sensor_error_states()

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 1)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.GenericError)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].msg, "Test Error")

    def test_process_sensor_error_states_two_error(self):
        """
        Tests sensor error state processing to recover from missed error state events (two missed error state).
        """

        executer, global_data = self._create_error_state_executer()

        global_data.storage.update_sensor_error_state(self.node.id,
                                                      self.sensors[0].clientSensorId,
                                                      SensorErrorState(SensorErrorState.GenericError, "Test Error"))

        global_data.storage.update_sensor_error_state(self.node.id,
                                                      self.sensors[-1].clientSensorId,
                                                      SensorErrorState(SensorErrorState.TimeoutError, "Test Error 2"))

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

        executer._process_sensor_error_states()

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 2)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.GenericError)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].msg, "Test Error")
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][1], self.sensors[-1].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][2], self.sensors[-1].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][3].state, SensorErrorState.TimeoutError)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][3].msg, "Test Error 2")

    def test_process_sensor_error_states_one_ok(self):
        """
        Tests sensor error state processing to recover from missed error state events (one missed ok state).
        """

        executer, global_data = self._create_error_state_executer()

        # Add sensors that executer things are in an error state.
        executer._sensor_ids_in_error.add(self.sensors[0].sensorId)

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

        executer._process_sensor_error_states()

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 1)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.OK)

    def test_process_sensor_error_states_two_ok(self):
        """
        Tests sensor error state processing to recover from missed error state events (two missed ok state).
        """

        executer, global_data = self._create_error_state_executer()

        # Add sensors that executer things are in an error state.
        executer._sensor_ids_in_error.add(self.sensors[0].sensorId)
        executer._sensor_ids_in_error.add(self.sensors[-1].sensorId)

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

        executer._process_sensor_error_states()

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 2)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.OK)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][1], self.sensors[-1].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][2], self.sensors[-1].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][3].state, SensorErrorState.OK)

    def test_process_sensor_error_states_one_error_one_ok(self):
        """
        Tests sensor error state processing to recover from missed error state events
        (one missed error state and ok state).
        """

        executer, global_data = self._create_error_state_executer()

        # Add sensors that executer things are in an error state.
        executer._sensor_ids_in_error.add(self.sensors[0].sensorId)

        global_data.storage.update_sensor_error_state(self.node.id,
                                                      self.sensors[-1].clientSensorId,
                                                      SensorErrorState(SensorErrorState.TimeoutError, "Test Error 2"))

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

        executer._process_sensor_error_states()

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 2)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.OK)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][1], self.sensors[-1].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][2], self.sensors[-1].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][3].state, SensorErrorState.TimeoutError)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][3].msg, "Test Error 2")

    def test_process_sensor_error_states_no_misses(self):
        """
        Tests sensor error state processing to recover from missed error state events (no misses).
        """

        executer, global_data = self._create_error_state_executer()

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

        executer._process_sensor_error_states()

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

    def test_integration_sensor_error_state_changes(self):
        """
        Tests handling of sensor error state changes.
        """

        executer, global_data = self._create_error_state_executer()
        executer.daemon = True
        executer.start()

        time.sleep(1)

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

        self.assertEqual(self.sensors[0].error_state.state, SensorErrorState.OK)
        self.assertEqual(self.sensors[-1].error_state.state, SensorErrorState.OK)

        executer.add_error_state(self.node.id,
                                 self.sensors[0].clientSensorId,
                                 SensorErrorState(SensorErrorState.GenericError, "Test Error"))

        executer.add_error_state(self.node.id,
                                 self.sensors[-1].clientSensorId,
                                 SensorErrorState(SensorErrorState.TimeoutError, "Test Error 2"))

        time.sleep(1)

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 2)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.GenericError)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].msg, "Test Error")
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][1], self.sensors[-1].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][2], self.sensors[-1].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][3].state, SensorErrorState.TimeoutError)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][3].msg, "Test Error 2")

        self.assertEqual(self.sensors[0].error_state.state, SensorErrorState.GenericError)
        self.assertEqual(self.sensors[0].error_state.msg, "Test Error")
        self.assertEqual(self.sensors[-1].error_state.state, SensorErrorState.TimeoutError)
        self.assertEqual(self.sensors[-1].error_state.msg, "Test Error 2")

    def test_integration_event_misses(self):
        """
        Tests handling of missed sensor error events.
        """

        executer, global_data = self._create_error_state_executer()
        executer.daemon = True
        executer.start()

        time.sleep(1)

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 0)

        self.assertEqual(self.sensors[0].error_state.state, SensorErrorState.OK)
        self.assertEqual(self.sensors[-1].error_state.state, SensorErrorState.OK)

        # Change two error states in the database.
        self.sensors[0].error_state = SensorErrorState(SensorErrorState.GenericError, "Test Error")
        self.sensors[-1].error_state = SensorErrorState(SensorErrorState.TimeoutError, "Test Error 2")

        # Force processing round of error state executer.
        executer.start_processing_round()

        time.sleep(1)

        self.assertEqual(len(self.internal_sensor.sensor_error_states), 2)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][1], self.sensors[0].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][2], self.sensors[0].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].state, SensorErrorState.GenericError)
        self.assertEqual(self.internal_sensor.sensor_error_states[0][3].msg, "Test Error")
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][0], self.node.username)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][1], self.sensors[-1].clientSensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][2], self.sensors[-1].sensorId)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][3].state, SensorErrorState.TimeoutError)
        self.assertEqual(self.internal_sensor.sensor_error_states[-1][3].msg, "Test Error 2")
