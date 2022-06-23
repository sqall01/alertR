import json
from unittest import TestCase
from lib.sensor.protocoldata import _ProtocolDataSensor
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange, SensorDataType, SensorDataNone, \
    SensorDataInt, SensorObjErrorStateChange, SensorErrorState


class MockProtocolDataSensor(_ProtocolDataSensor):

    def __init__(self):
        super().__init__()

    def _execute(self):
        pass

    def initialize(self) -> bool:
        pass


class TestProtocolDataSensor(TestCase):

    def _create_base_sensor(self) -> MockProtocolDataSensor:
        sensor = MockProtocolDataSensor()
        sensor.id = 1
        sensor.description = "Test Protocol Data"
        sensor.alertDelay = 0
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.triggerState = 1
        sensor.alertLevels = [1]
        sensor.state = 0
        self._sensors.append(sensor)
        return sensor

    def setUp(self):
        self._sensors = []

    def tearDown(self):
        for sensor in self._sensors:
            sensor.exit()

    def test_illegal_data(self):
        """
        Tests if illegal data is handled correctly.
        """
        payload = "no json at all"

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(payload))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_wrong_type(self):
        """
        Tests if wrong message type is handled correctly.
        """
        payload = {
            "message": "doesnotexist",
            "payload": {
                "state": 1,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_state_change_illegal_state(self):
        """
        Tests if an illegal state for a state change is handled correctly.
        """
        payload = {
            "message": "statechange",
            "payload": {
                "state": 1337,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_state_change_illegal_data_type(self):
        """
        Tests if an illegal data type for a state change is handled correctly.
        """
        payload = {
            "message": "statechange",
            "payload": {
                "state": 1,
                "dataType": SensorDataType.INT,
                "data": SensorDataInt(1338, "test unit").copy_to_dict(),
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertEqual(sensor.data, SensorDataNone())

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_illegal_state(self):
        """
        Tests if an illegal state for a Sensor Alert is handled correctly.
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1337,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_illegal_data_type(self):
        """
        Tests if an illegal data type for a Sensor Alert is handled correctly.
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.INT,
                "data": SensorDataInt(1338, "test unit").copy_to_dict(),
                "hasLatestData": True,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertEqual(sensor.data, SensorDataNone())

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_illegal_has_optional_data(self):
        """
        Tests if an illegal has optional data flag for a Sensor Alert is handled correctly.
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": 1,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertEqual(sensor.data, SensorDataNone())

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_illegal_has_latest_data(self):
        """
        Tests if an illegal has latest data flag for a Sensor Alert is handled correctly.
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": 1,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertEqual(sensor.data, SensorDataNone())

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_illegal_change_state(self):
        """
        Tests if an illegal change state flag for a Sensor Alert is handled correctly.
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": False,
                "changeState": 1
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertEqual(sensor.data, SensorDataNone())

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_illegal_optional_data(self):
        """
        Tests if an illegal optional data for a Sensor Alert is handled correctly.
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": True,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has not changed.
        self.assertEqual(sensor.data, SensorDataNone())

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_error_state_change_illegal_error_state(self):
        """
        Tests if an illegal error state for an error state change is handled correctly.
        """
        payload = {
            "message": "sensorerrorstatechange",
            "payload": {
                "error_state": "wrong data"
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_error_state_change_illegal_state(self):
        """
        Tests if an illegal state for an error state change is handled correctly.
        """
        payload = {
            "message": "sensorerrorstatechange",
            "payload": {
                "error_state": {
                    "state": -1337,
                    "msg": "some msg"
                }
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_error_state_change_illegal_msg(self):
        """
        Tests if an illegal msg for an error state change is handled correctly.
        """
        payload = {
            "message": "sensorerrorstatechange",
            "payload": {
                "error_state": {
                    "state": SensorErrorState.OK,
                    "msg": "Some msg"
                }
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertFalse(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_triggered_state_change(self):
        """
        Tests if a Sensor Alert is triggered (with state change).
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": False,
                "changeState": True
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_triggered_no_state_change(self):
        """
        Tests if a Sensor Alert is triggered (with no state change).
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_normal_state_change(self):
        """
        Tests if a Sensor Alert is triggered (with state change).
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 0,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": False,
                "changeState": True
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_normal_no_state_change(self):
        """
        Tests if a Sensor Alert is triggered (with no state change).
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 0,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.state = 1
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(1, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has not changed.
        self.assertEqual(1, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_data_change(self):
        """
        Tests if a Sensor Alert is triggered (with data change).
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.INT,
                "data": SensorDataInt(1337, "test unit").copy_to_dict(),
                "hasLatestData": True,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data has changed.
        self.assertEqual(SensorDataInt.copy_from_dict(payload["payload"]["data"]), sensor.data)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_sensor_alert_no_data_change(self):
        """
        Tests if a Sensor Alert is triggered (with no data change).
        """
        payload = {
            "message": "sensoralert",
            "payload": {
                "state": 1,
                "hasOptionalData": False,
                "optionalData": None,
                "dataType": SensorDataType.INT,
                "data": SensorDataInt(1337, "test unit").copy_to_dict(),
                "hasLatestData": False,
                "changeState": False
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(0, "test unit")
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["hasOptionalData"], events[0].hasOptionalData)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(payload["payload"]["hasLatestData"], events[0].hasLatestData)
        self.assertEqual(payload["payload"]["changeState"], events[0].changeState)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure data hasnot  changed.
        self.assertNotEqual(SensorDataInt.copy_from_dict(payload["payload"]["data"]), sensor.data)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_state_change_triggered(self):
        """
        Tests if state change is processed correctly (state is changed to triggered).
        """
        payload = {
            "message": "statechange",
            "payload": {
                "state": 1,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(SensorDataNone.copy_from_dict(payload["payload"]["data"]), events[0].data)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_state_change_normal(self):
        """
        Tests if state change is processed correctly (state is changed to normal).
        """
        payload = {
            "message": "statechange",
            "payload": {
                "state": 0,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.state = 1
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(1, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(SensorDataNone.copy_from_dict(payload["payload"]["data"]), events[0].data)

        # Make sure sensor state has changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_state_change_data_change(self):
        """
        Tests if state change is processed correctly (data is changed).
        """
        payload = {
            "message": "statechange",
            "payload": {
                "state": 1,
                "dataType": SensorDataType.INT,
                "data": SensorDataInt(1337, "test unit").copy_to_dict(),
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(0, "test unit")
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["state"], events[0].state)
        self.assertEqual(payload["payload"]["dataType"], events[0].dataType)
        self.assertEqual(SensorDataInt.copy_from_dict(payload["payload"]["data"]), events[0].data)

        # Make sure sensor state has changed.
        self.assertEqual(1, sensor.state)

        # Make sure sensor data has changed.
        self.assertEqual(SensorDataInt.copy_from_dict(payload["payload"]["data"]), sensor.data)

        # Make sure error state has not changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_error_state_change(self):
        """
        Tests if error state change is processed correctly.
        """
        payload = {
            "message": "sensorerrorstatechange",
            "payload": {
                "error_state": {
                    "state": SensorErrorState.GenericError,
                    "msg": "Some error"
                }
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(payload["payload"]["error_state"]["state"], events[0].error_state.state)
        self.assertEqual(payload["payload"]["error_state"]["msg"], events[0].error_state.msg)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has changed.
        self.assertEqual(SensorErrorState.GenericError, sensor.error_state.state)
        self.assertEqual("Some error", sensor.error_state.msg)

    def test_error_state_change_through_state_change_event(self):
        """
        Tests if error state is changed back to normal if a state change event occurs with no new data during while
        an not-OK error state exists.
        """
        payload = {
            "message": "statechange",
            "payload": {
                "state": 0,
                "dataType": SensorDataType.NONE,
                "data": SensorDataNone().copy_to_dict(),
            }
        }

        sensor = self._create_base_sensor()

        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.state = 0
        sensor.error_state = SensorErrorState(SensorErrorState.GenericError, "test error")
        sensor.initialize()

        # Make sure sensor is in correct initial state.
        self.assertEqual(0, sensor.state)
        self.assertEqual(SensorErrorState.GenericError, sensor.error_state.state)
        self.assertEqual("test error", sensor.error_state.msg)

        self.assertTrue(sensor._process_protocol_data(json.dumps(payload)))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(SensorErrorState.OK, events[0].error_state.state)
        self.assertEqual("", events[0].error_state.msg)

        # Make sure sensor state has changed.
        self.assertEqual(0, sensor.state)

        # Make sure error state has changed.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)
