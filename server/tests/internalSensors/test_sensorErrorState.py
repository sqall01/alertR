import logging
from typing import Any, List, Tuple, Optional, Dict
from collections import defaultdict
from unittest import TestCase
from lib.localObjects import SensorAlert, Sensor
from lib.internalSensors.sensorErrorState import SensorErrorStateSensor
from lib.globalData.globalData import GlobalData
from lib.globalData.sensorObjects import SensorErrorState, SensorDataType
# noinspection PyProtectedMember
from lib.storage.core import _Storage


class MockSensorAlertExecuter:

    def __init__(self):
        self._sensor_alerts = list()  # type: List[SensorAlert]
        self.is_working = True

    @property
    def sensor_alerts(self) -> List[SensorAlert]:
        return self._sensor_alerts

    def add_sensor_alert(self,
                         node_id: int,
                         sensor_id: int,
                         state: int,
                         optional_data: Optional[Dict[str, Any]],
                         change_state: bool,
                         has_latest_data: bool,
                         data_type: int,
                         sensor_data: Any,
                         logger: logging.Logger = None) -> bool:

        if not self.is_working:
            return False

        sensor_alert = SensorAlert()
        sensor_alert.nodeId = node_id
        sensor_alert.sensorId = sensor_id
        sensor_alert.state = state
        sensor_alert.changeState = change_state
        sensor_alert.hasLatestData = has_latest_data
        sensor_alert.dataType = data_type
        sensor_alert.data = sensor_data

        sensor_alert.hasOptionalData = False
        sensor_alert.optionalData = optional_data
        if optional_data:
            sensor_alert.hasOptionalData = True

        self._sensor_alerts.append(sensor_alert)
        return True


# noinspection PyAbstractClass
class MockStorage(_Storage):

    def __init__(self):
        self.is_working = True

        self._sensor_data = defaultdict(list)
        self._sensor_state = defaultdict(list)

        self._sensors_in_error = []  # type: List[int]

        self._sensors = dict()  # type: Dict[int, Sensor]

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

    def get_sensor_ids_in_error_state(self,
                                      logger: logging.Logger = None) -> List[int]:

        if not self.is_working:
            return []

        return self._sensors_in_error

    def getSensorById(self,
                      sensorId: int,
                      logger: logging.Logger = None) -> Optional[Sensor]:
        return self._sensors[sensorId] if sensorId in self._sensors else None

    def register_sensor(self,
                        node_id: int,
                        sensor_id: int,
                        client_sensor_id: int,
                        description: str):
        sensor = Sensor()
        sensor.nodeId = node_id
        sensor.sensorId = sensor_id
        sensor.clientSensorId = client_sensor_id
        sensor.description = description
        sensor.state = 0
        sensor.error_state = SensorErrorState()
        sensor.dataType = SensorDataType.NONE
        sensor.alertDelay = 0
        self._sensors[sensor_id] = sensor

    def updateSensorData(self,
                         node_id: int,
                         data_list: List[Tuple[int, Any]],
                         logger: logging.Logger = None) -> bool:

        if not self.is_working:
            return False

        for data_tuple in data_list:
            self._sensor_data[node_id].append(data_tuple)

        return True

    def updateSensorState(self,
                          node_id: int,
                          state_list: List[Tuple[int, int]],
                          logger: logging.Logger = None) -> bool:

        if not self.is_working:
            return False

        for state_tuple in state_list:
            self._sensor_state[node_id].append(state_tuple)

        return True


class TestSensorErrorState(TestCase):

    def _create_internal_sensor(self) -> Tuple[SensorErrorStateSensor, GlobalData]:
        global_data = GlobalData()
        global_data.logger = logging.getLogger("Sensor Error State Test Case")
        global_data.sensorAlertExecuter = MockSensorAlertExecuter()

        global_data.storage = MockStorage()

        sensor = SensorErrorStateSensor(global_data)
        sensor.nodeId = 1
        sensor.sensorId = 1
        return sensor, global_data

    def test_initialize_without_sensor_in_error(self):
        """
        Tests initialization of sensor considers sensors having an error state and updates its state accordingly.
        """

        # Create clean sensor and global data.
        sensor, global_data = self._create_internal_sensor()

        # Initialize without sensors in error.
        sensor.initialize()

        self.assertEqual(0, sensor.state)
        self.assertEqual(0, sensor.data.value)

        states = global_data.storage.sensor_state
        self.assertEqual(len(states[sensor.nodeId]), 1)
        self.assertEqual(states[sensor.nodeId][-1], (sensor.clientSensorId, sensor.state))

        data = global_data.storage.sensor_data
        self.assertEqual(len(data[sensor.nodeId]), 1)
        self.assertEqual(data[sensor.nodeId][-1], (sensor.clientSensorId, sensor.data))

        sensor_alerts = global_data.sensorAlertExecuter.sensor_alerts
        self.assertEqual(len(sensor_alerts), 0)

    def test_initialize_with_sensor_in_error(self):
        """
        Tests initialization of sensor considers sensors having an error state and updates its state accordingly.
        """

        # Create clean sensor and global data.
        sensor, global_data = self._create_internal_sensor()

        global_data.storage.sensors_in_error = [5, 6, 7, 8]

        # Initialize with sensors in error.
        sensor.initialize()

        self.assertEqual(1, sensor.state)
        self.assertEqual(len(global_data.storage.sensors_in_error), sensor.data.value)

        states = global_data.storage.sensor_state
        self.assertEqual(len(states[sensor.nodeId]), 1)
        self.assertEqual(states[sensor.nodeId][-1], (sensor.clientSensorId, sensor.state))

        data = global_data.storage.sensor_data
        self.assertEqual(len(data[sensor.nodeId]), 1)
        self.assertEqual(data[sensor.nodeId][-1], (sensor.clientSensorId, sensor.data))

    def test_process_error_state_add_new_error_state(self):
        """
        Tests processing of error state change message (no prior error state, add error state).
        """

        # Create clean sensor and global data.
        sensor, global_data = self._create_internal_sensor()
        client_sensor_id = 1
        sensor_id = 2
        global_data.storage.register_sensor(1, sensor_id, client_sensor_id, "Some description")
        sensor.initialize()

        self.assertEqual(0, sensor.state)
        self.assertEqual(0, sensor.data.value)

        sensor.process_error_state("username",
                                   client_sensor_id,
                                   sensor_id,
                                   SensorErrorState(SensorErrorState.GenericError, "error"))

        self.assertEqual(1, sensor.state)
        self.assertEqual(1, sensor.data.value)

        states = global_data.storage.sensor_state
        self.assertEqual(len(states[sensor.nodeId]), 2)
        self.assertEqual(states[sensor.nodeId][-1], (sensor.clientSensorId, sensor.state))

        data = global_data.storage.sensor_data
        self.assertEqual(len(data[sensor.nodeId]), 2)
        self.assertEqual(data[sensor.nodeId][-1], (sensor.clientSensorId, sensor.data))

        sensor_alerts = global_data.sensorAlertExecuter.sensor_alerts
        self.assertEqual(len(sensor_alerts), 1)
        self.assertEqual(sensor_alerts[-1].nodeId, sensor.nodeId)
        self.assertEqual(sensor_alerts[-1].sensorId, sensor.sensorId)
        self.assertEqual(sensor_alerts[-1].state, sensor.state)
        self.assertEqual(sensor_alerts[-1].dataType, sensor.dataType)
        self.assertEqual(sensor_alerts[-1].data, sensor.data)
        self.assertTrue(sensor_alerts[-1].hasLatestData)
        self.assertTrue(sensor_alerts[-1].changeState)

    def test_process_error_state_add_old_error_state(self):
        """
        Tests processing of error state change message (with prior error state, add error state).
        """



        # Create clean sensor and global data.
        sensor, global_data = self._create_internal_sensor()
        sensor_id_error = 2
        client_sensor_id = 1
        global_data.storage.register_sensor(1, sensor_id_error, client_sensor_id, "Some description")
        global_data.storage.sensors_in_error = [sensor_id_error]
        sensor.initialize()

        self.assertEqual(1, sensor.state)
        self.assertEqual(1, sensor.data.value)

        sensor.process_error_state("username",
                                   client_sensor_id,
                                   sensor_id_error,
                                   SensorErrorState(SensorErrorState.GenericError, "error"))

        self.assertEqual(1, sensor.state)
        self.assertEqual(1, sensor.data.value)

        states = global_data.storage.sensor_state
        self.assertEqual(len(states[sensor.nodeId]), 2)
        self.assertEqual(states[sensor.nodeId][-1], (sensor.clientSensorId, sensor.state))

        data = global_data.storage.sensor_data
        self.assertEqual(len(data[sensor.nodeId]), 2)
        self.assertEqual(data[sensor.nodeId][-1], (sensor.clientSensorId, sensor.data))

        sensor_alerts = global_data.sensorAlertExecuter.sensor_alerts
        self.assertEqual(len(sensor_alerts), 1)
        self.assertEqual(sensor_alerts[-1].nodeId, sensor.nodeId)
        self.assertEqual(sensor_alerts[-1].sensorId, sensor.sensorId)
        self.assertEqual(sensor_alerts[-1].state, sensor.state)
        self.assertEqual(sensor_alerts[-1].dataType, sensor.dataType)
        self.assertEqual(sensor_alerts[-1].data, sensor.data)
        self.assertTrue(sensor_alerts[-1].hasLatestData)
        self.assertTrue(sensor_alerts[-1].changeState)

    def test_process_error_state_remove_error_state(self):
        """
        Tests processing of error state change message (with prior error state, remove error state).
        """

        # Create clean sensor and global data.
        sensor, global_data = self._create_internal_sensor()
        sensor_id_error = 2
        client_sensor_id = 1
        global_data.storage.register_sensor(1, sensor_id_error, client_sensor_id, "Some description")
        global_data.storage.sensors_in_error = [sensor_id_error]
        sensor.initialize()

        self.assertEqual(1, sensor.state)
        self.assertEqual(1, sensor.data.value)

        sensor.process_error_state("username",
                                   client_sensor_id,
                                   sensor_id_error,
                                   SensorErrorState(SensorErrorState.OK, ""))

        self.assertEqual(0, sensor.state)
        self.assertEqual(0, sensor.data.value)

        states = global_data.storage.sensor_state
        self.assertEqual(len(states[sensor.nodeId]), 2)
        self.assertEqual(states[sensor.nodeId][-1], (sensor.clientSensorId, sensor.state))

        data = global_data.storage.sensor_data
        self.assertEqual(len(data[sensor.nodeId]), 2)
        self.assertEqual(data[sensor.nodeId][-1], (sensor.clientSensorId, sensor.data))

        sensor_alerts = global_data.sensorAlertExecuter.sensor_alerts
        self.assertEqual(len(sensor_alerts), 1)
        self.assertEqual(sensor_alerts[-1].nodeId, sensor.nodeId)
        self.assertEqual(sensor_alerts[-1].sensorId, sensor.sensorId)
        self.assertEqual(sensor_alerts[-1].state, sensor.state)
        self.assertEqual(sensor_alerts[-1].dataType, sensor.dataType)
        self.assertEqual(sensor_alerts[-1].data, sensor.data)
        self.assertTrue(sensor_alerts[-1].hasLatestData)
        self.assertTrue(sensor_alerts[-1].changeState)

    def test_process_error_state_remove_no_error_state(self):
        """
        Tests processing of error state change message (no prior error state, remove error state).
        """

        # Create clean sensor and global data.
        sensor, global_data = self._create_internal_sensor()
        sensor_id = 2
        client_sensor_id = 1
        global_data.storage.register_sensor(1, sensor_id, client_sensor_id, "Some description")
        sensor.initialize()

        self.assertEqual(0, sensor.state)
        self.assertEqual(0, sensor.data.value)

        sensor.process_error_state("username",
                                   client_sensor_id,
                                   sensor_id,
                                   SensorErrorState(SensorErrorState.OK, ""))

        self.assertEqual(0, sensor.state)
        self.assertEqual(0, sensor.data.value)

        states = global_data.storage.sensor_state
        self.assertEqual(len(states[sensor.nodeId]), 2)
        self.assertEqual(states[sensor.nodeId][-1], (sensor.clientSensorId, sensor.state))

        data = global_data.storage.sensor_data
        self.assertEqual(len(data[sensor.nodeId]), 2)
        self.assertEqual(data[sensor.nodeId][-1], (sensor.clientSensorId, sensor.data))

        sensor_alerts = global_data.sensorAlertExecuter.sensor_alerts
        self.assertEqual(len(sensor_alerts), 1)
        self.assertEqual(sensor_alerts[-1].nodeId, sensor.nodeId)
        self.assertEqual(sensor_alerts[-1].sensorId, sensor.sensorId)
        self.assertEqual(sensor_alerts[-1].state, sensor.state)
        self.assertEqual(sensor_alerts[-1].dataType, sensor.dataType)
        self.assertEqual(sensor_alerts[-1].data, sensor.data)
        self.assertTrue(sensor_alerts[-1].hasLatestData)
        self.assertTrue(sensor_alerts[-1].changeState)

    def test_process_error_state_database_error(self):
        """
        Tests processing of error state change message with a faulty database (send out sensor alert).
        """

        # Create clean sensor and global data.
        sensor, global_data = self._create_internal_sensor()
        sensor_id = 2
        client_sensor_id = 1
        global_data.storage.register_sensor(1, sensor_id, client_sensor_id, "Some description")
        sensor.initialize()

        self.assertEqual(0, sensor.state)
        self.assertEqual(0, sensor.data.value)

        global_data.storage.is_working = False

        sensor.process_error_state("username",
                                   client_sensor_id,
                                   sensor_id,
                                   SensorErrorState(SensorErrorState.GenericError, "error"))

        self.assertEqual(1, sensor.state)
        self.assertEqual(1, sensor.data.value)

        sensor_alerts = global_data.sensorAlertExecuter.sensor_alerts
        self.assertEqual(len(sensor_alerts), 1)
        self.assertEqual(sensor_alerts[-1].nodeId, sensor.nodeId)
        self.assertEqual(sensor_alerts[-1].sensorId, sensor.sensorId)
        self.assertEqual(sensor_alerts[-1].state, sensor.state)
        self.assertEqual(sensor_alerts[-1].dataType, sensor.dataType)
        self.assertEqual(sensor_alerts[-1].data, sensor.data)
        self.assertTrue(sensor_alerts[-1].hasLatestData)
        self.assertTrue(sensor_alerts[-1].changeState)

    def test_process_error_state_sensor_alert_executer_error(self):
        """
        Tests processing of error state change message with a faulty sensor alert executer (change data in database).
        """

        # Create clean sensor and global data.
        sensor, global_data = self._create_internal_sensor()
        sensor_id = 2
        client_sensor_id = 1
        global_data.storage.register_sensor(1, sensor_id, client_sensor_id, "Some description")
        sensor.initialize()

        self.assertEqual(0, sensor.state)
        self.assertEqual(0, sensor.data.value)

        global_data.sensorAlertExecuter.is_working = False

        sensor.process_error_state("username",
                                   client_sensor_id,
                                   sensor_id,
                                   SensorErrorState(SensorErrorState.GenericError, "error"))

        self.assertEqual(1, sensor.state)
        self.assertEqual(1, sensor.data.value)

        states = global_data.storage.sensor_state
        self.assertEqual(len(states[sensor.nodeId]), 2)
        self.assertEqual(states[sensor.nodeId][-1], (sensor.clientSensorId, sensor.state))

        data = global_data.storage.sensor_data
        self.assertEqual(len(data[sensor.nodeId]), 2)
        self.assertEqual(data[sensor.nodeId][-1], (sensor.clientSensorId, sensor.data))

        sensor_alerts = global_data.sensorAlertExecuter.sensor_alerts
        self.assertEqual(len(sensor_alerts), 0)
