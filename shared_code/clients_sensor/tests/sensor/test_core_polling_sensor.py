from unittest import TestCase
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange, SensorDataType, SensorDataNone, \
    SensorDataInt, SensorErrorState, SensorObjErrorStateChange
# noinspection PyProtectedMember
from lib.sensor.core import _PollingSensor


class EmptySensor(_PollingSensor):
    """
    Class used to test methods of _PollingSensor.
    """

    def _execute(self):
        pass

    def initialize(self) -> bool:
        pass


class TestPollingSensor(TestCase):

    def _create_base_sensor(self) -> EmptySensor:
        sensor = EmptySensor()
        sensor.id = 1
        sensor.description = "Test Polling"
        sensor.sensorDataType = SensorDataType.NONE
        sensor.data = SensorDataNone()
        sensor.alertDelay = 0
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.triggerState = 1
        sensor.alertLevels = [1]
        return sensor

    def test_add_sensor_alert_triggered_no_state_change(self):
        """
        Tests if adding a Sensor Alert is correctly processed (triggered, no state change).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=False)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertFalse(events[0].changeState)
        self.assertFalse(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertTrue(type(events[0].data) == SensorDataNone)
        self.assertEqual(SensorDataType.NONE, events[0].dataType)

        # Make sure sensor state did not change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

    def test_add_sensor_alert_triggered_state_change(self):
        """
        Tests if adding a Sensor Alert is correctly processed (triggered, state change).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=True)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertFalse(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertTrue(type(events[0].data) == SensorDataNone)
        self.assertEqual(SensorDataType.NONE, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(sensor.triggerState, sensor.state)

    def test_add_sensor_alert_normal_no_state_change(self):
        """
        Tests if adding a Sensor Alert is correctly processed (normal, no state change).
        """

        sensor = self._create_base_sensor()
        sensor.state = sensor.triggerState
        sensor._add_sensor_alert(1 - sensor.triggerState,
                                 change_state=False)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(0, events[0].state)
        self.assertFalse(events[0].changeState)
        self.assertFalse(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertTrue(type(events[0].data) == SensorDataNone)
        self.assertEqual(SensorDataType.NONE, events[0].dataType)

        # Make sure sensor state did not change.
        self.assertEqual(sensor.triggerState, sensor.state)

    def test_add_sensor_alert_normal_state_change(self):
        """
        Tests if adding a Sensor Alert is correctly processed (normal, state change).
        """

        sensor = self._create_base_sensor()
        sensor.state = sensor.triggerState
        sensor._add_sensor_alert(1 - sensor.triggerState,
                                 change_state=True)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(0, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertFalse(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertTrue(type(events[0].data) == SensorDataNone)
        self.assertEqual(SensorDataType.NONE, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

    def test_add_sensor_alert_no_data_change(self):
        """
        Tests if adding a Sensor Alert is correctly processed (triggered, no data change).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=False,
                                 sensor_data=SensorDataInt(1337, "test unit"),
                                 has_latest_data=False)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertFalse(events[0].changeState)
        self.assertFalse(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(SensorDataInt(1337, "test unit"), events[0].data)
        self.assertEqual(SensorDataType.INT, events[0].dataType)

        # Make sure sensor state did not change.
        self.assertEqual(SensorDataInt(1, "test unit"), sensor.data)

    def test_add_sensor_alert_data_change(self):
        """
        Tests if adding a Sensor Alert is correctly processed (triggered, data change).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=False,
                                 sensor_data=SensorDataInt(1337, "test unit"),
                                 has_latest_data=True)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertFalse(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(SensorDataInt(1337, "test unit"), events[0].data)
        self.assertEqual(SensorDataType.INT, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(SensorDataInt(1337, "test unit"), sensor.data)

    def test_add_sensor_alert_optional_data(self):
        """
        Tests if adding a Sensor Alert is correctly processed (triggered, optional data).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        optional_data = {"msg": "test msg"}
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=False,
                                 optional_data=optional_data)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertFalse(events[0].changeState)
        self.assertFalse(events[0].hasLatestData)
        self.assertTrue(events[0].hasOptionalData)
        self.assertEqual(optional_data["msg"], events[0].optionalData["msg"])
        self.assertTrue(type(events[0].data) == SensorDataNone)
        self.assertEqual(SensorDataType.NONE, events[0].dataType)

        # Make sure sensor state did not change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

    def test_add_sensor_alert_triggered_no_state_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (triggered, no state change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.triggerAlert = False
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=False)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state did not change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

    def test_add_sensor_alert_normal_no_state_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (normal, no state change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = sensor.triggerState
        sensor.triggerAlertNormal = False
        sensor._add_sensor_alert(1 - sensor.triggerState,
                                 change_state=False)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state did not change.
        self.assertEqual(sensor.triggerState, sensor.state)

    def test_add_sensor_alert_triggered_state_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (triggered, state change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.triggerAlert = False
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=True)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertTrue(type(events[0].data) == SensorDataNone)
        self.assertEqual(SensorDataType.NONE, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(sensor.triggerState, sensor.state)

    def test_add_sensor_alert_normal_state_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (normal, state change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = sensor.triggerState
        sensor.triggerAlertNormal = False
        sensor._add_sensor_alert(1 - sensor.triggerState,
                                 change_state=True)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(0, events[0].state)
        self.assertTrue(type(events[0].data) == SensorDataNone)
        self.assertEqual(SensorDataType.NONE, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

    def test_add_sensor_alert_triggered_data_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (triggered, state change, data change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.triggerAlert = False
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=True,
                                 sensor_data=SensorDataInt(1337, "test unit"),
                                 has_latest_data=True)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertEqual(SensorDataInt(1337, "test unit"), events[0].data)
        self.assertEqual(SensorDataType.INT, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(sensor.triggerState, sensor.state)

        # Make sure sensor data did change.
        self.assertEqual(SensorDataInt(1337, "test unit"), sensor.data)

    def test_add_sensor_alert_normal_data_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (normal, state change, data change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = sensor.triggerState
        sensor.triggerAlertNormal = False
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")
        sensor._add_sensor_alert(1 - sensor.triggerState,
                                 change_state=True,
                                 sensor_data=SensorDataInt(1337, "test unit"),
                                 has_latest_data=True)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(0, events[0].state)
        self.assertEqual(SensorDataInt(1337, "test unit"), events[0].data)
        self.assertEqual(SensorDataType.INT, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

        # Make sure sensor data did change.
        self.assertEqual(SensorDataInt(1337, "test unit"), sensor.data)

    def test_add_sensor_alert_triggered_no_data_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (triggered, state change, no data change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.triggerAlert = False
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=True,
                                 sensor_data=SensorDataInt(1337, "test unit"),
                                 has_latest_data=False)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertEqual(SensorDataInt(1, "test unit"), events[0].data)
        self.assertEqual(SensorDataType.INT, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(sensor.triggerState, sensor.state)

        # Make sure sensor data did not change.
        self.assertEqual(SensorDataInt(1, "test unit"), sensor.data)

    def test_add_sensor_alert_normal_no_data_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (normal, state change, no data change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = sensor.triggerState
        sensor.triggerAlertNormal = False
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")
        sensor._add_sensor_alert(1 - sensor.triggerState,
                                 change_state=True,
                                 sensor_data=SensorDataInt(1337, "test unit"),
                                 has_latest_data=False)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(0, events[0].state)
        self.assertEqual(SensorDataInt(1, "test unit"), events[0].data)
        self.assertEqual(SensorDataType.INT, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

        # Make sure sensor data did not change.
        self.assertEqual(SensorDataInt(1, "test unit"), sensor.data)

    def test_add_sensor_alert_triggered_only_data_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (triggered, no state change, data change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.triggerAlert = False
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")
        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=False,
                                 sensor_data=SensorDataInt(1337, "test unit"),
                                 has_latest_data=True)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(0, events[0].state)  # Old sensor state was "normal"
        self.assertEqual(SensorDataInt(1337, "test unit"), events[0].data)
        self.assertEqual(SensorDataType.INT, events[0].dataType)

        # Make sure sensor state did not change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

        # Make sure sensor data did change.
        self.assertEqual(SensorDataInt(1337, "test unit"), sensor.data)

    def test_add_sensor_alert_normal_only_data_change_disabled(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (normal, no state change, data change, configuration disables sensor alert).
        """

        sensor = self._create_base_sensor()
        sensor.state = sensor.triggerState
        sensor.triggerAlertNormal = False
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")
        sensor._add_sensor_alert(1 - sensor.triggerState,
                                 change_state=False,
                                 sensor_data=SensorDataInt(1337, "test unit"),
                                 has_latest_data=True)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)  # Old sensor state was "triggered"
        self.assertEqual(SensorDataInt(1337, "test unit"), events[0].data)
        self.assertEqual(SensorDataType.INT, events[0].dataType)

        # Make sure sensor state did not change.
        self.assertEqual(sensor.triggerState, sensor.state)

        # Make sure sensor data did change.
        self.assertEqual(SensorDataInt(1337, "test unit"), sensor.data)

    def test_add_sensor_alert_data_expected(self):
        """
        Tests if adding a Sensor Alert is correctly processed
        (triggered, no data but it was expected).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")

        exception = False
        try:
            sensor._add_sensor_alert(sensor.triggerState,
                                     change_state=True)

        except ValueError as e:
            exception = True

        if not exception:
            self.fail("Expected ValueError exception")

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state did not change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

        # Make sure sensor data did not change.
        self.assertEqual(SensorDataInt(1, "test unit"), sensor.data)

    def test_add_sensor_alert_clears_error_state(self):
        """
        Tests if adding a sensor alert is correctly processed
        (clears error state).
        """

        sensor = self._create_base_sensor()

        sensor.error_state.set_error(SensorErrorState.GenericError, "Some Error")

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        sensor._add_sensor_alert(sensor.triggerState,
                                 change_state=True)

        events = sensor.get_events()
        self.assertEqual(2, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(SensorObjSensorAlert, type(events[1]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(SensorErrorState.OK, events[0].error_state.state)
        self.assertEqual("", events[0].error_state.msg)

        # Make sure error state did change.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_get_events(self):
        """
        Tests if getting events clears the event list.
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor._add_sensor_alert(sensor.triggerState,
                                 False)

        self.assertEqual(1, len(sensor.get_events()))

        # Make sure first call clears events.
        self.assertEqual(0, len(sensor.get_events()))

    def test_add_state_change_triggered(self):
        """
        Tests if adding a state change is correctly processed
        (triggered).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState

        sensor._add_state_change(sensor.triggerState)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertTrue(type(events[0].data) == SensorDataNone)
        self.assertEqual(SensorDataType.NONE, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(sensor.triggerState, sensor.state)

        # Make sure sensor data did not change.
        self.assertTrue(type(sensor.data) == SensorDataNone)

    def test_add_state_change_normal(self):
        """
        Tests if adding a state change is correctly processed
        (normal).
        """

        sensor = self._create_base_sensor()
        sensor.state = sensor.triggerState

        sensor._add_state_change(1 - sensor.triggerState)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(0, events[0].state)
        self.assertTrue(type(events[0].data) == SensorDataNone)
        self.assertEqual(SensorDataType.NONE, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

        # Make sure sensor data did not change.
        self.assertTrue(type(sensor.data) == SensorDataNone)

    def test_add_state_change_data(self):
        """
        Tests if adding a state change is correctly processed
        (triggered, data change).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")

        sensor._add_state_change(sensor.triggerState,
                                 SensorDataInt(1337, "test unit"))

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(1, events[0].state)
        self.assertEqual(SensorDataInt(1337, "test unit"), events[0].data)
        self.assertEqual(SensorDataType.INT, events[0].dataType)

        # Make sure sensor state did change.
        self.assertEqual(sensor.triggerState, sensor.state)

        # Make sure sensor data did change.
        self.assertEqual(SensorDataInt(1337, "test unit"), sensor.data)

    def test_add_state_change_data_expected(self):
        """
        Tests if adding a state change is correctly processed
        (triggered, no data but it was expected).
        """

        sensor = self._create_base_sensor()
        sensor.state = 1 - sensor.triggerState
        sensor.sensorDataType = SensorDataType.INT
        sensor.data = SensorDataInt(1, "test unit")

        exception = False
        try:
            sensor._add_state_change(sensor.triggerState)

        except ValueError as e:
            exception = True

        if not exception:
            self.fail("Expected ValueError exception")

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure sensor state did not change.
        self.assertEqual(1 - sensor.triggerState, sensor.state)

        # Make sure sensor data did not change.
        self.assertEqual(SensorDataInt(1, "test unit"), sensor.data)

    def test_add_state_change_clears_error_state(self):
        """
        Tests if adding a state change is correctly processed
        (clears error state).
        """

        sensor = self._create_base_sensor()

        sensor.error_state.set_error(SensorErrorState.GenericError, "Some Error")

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        sensor._add_state_change(sensor.triggerState)

        events = sensor.get_events()
        self.assertEqual(2, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(SensorObjStateChange, type(events[1]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(SensorErrorState.OK, events[0].error_state.state)
        self.assertEqual("", events[0].error_state.msg)

        # Make sure error state did change.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_clear_error_state(self):
        """
        Tests if clearing error state is correctly processed (clears error state).
        """

        sensor = self._create_base_sensor()
        sensor.error_state.set_error(SensorErrorState.GenericError, "Some Error")

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        sensor._clear_error_state()

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(sensor.error_state, events[0].error_state)
        self.assertFalse(sensor.error_state is events[0].error_state)

        # Make sure error state did change.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_clear_error_state_no_change(self):
        """
        Tests if clearing error state is correctly processed (does not clear error state if already cleared).
        """

        sensor = self._create_base_sensor()

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        sensor._clear_error_state()

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure error state did not change.
        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)
        self.assertEqual("", sensor.error_state.msg)

    def test_set_error_state(self):
        """
        Tests if setting error state is correctly processed (error state is set).
        """

        sensor = self._create_base_sensor()

        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)

        sensor._set_error_state(SensorErrorState.GenericError, "Some Error")

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(sensor.error_state, events[0].error_state)
        self.assertFalse(sensor.error_state is events[0].error_state)

        # Make sure error state did change.
        self.assertEqual(SensorErrorState.GenericError, sensor.error_state.state)
        self.assertEqual("Some Error", sensor.error_state.msg)

    def test_set_error_state_no_change(self):
        """
        Tests if setting error state is correctly processed (error state is not set if already in error state).
        """

        sensor = self._create_base_sensor()

        self.assertEqual(SensorErrorState.OK, sensor.error_state.state)

        sensor._set_error_state(SensorErrorState.GenericError, "Some Error")

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(sensor.id, events[0].clientSensorId)
        self.assertEqual(sensor.error_state, events[0].error_state)
        self.assertFalse(sensor.error_state is events[0].error_state)

        # Make sure error state did change.
        self.assertEqual(SensorErrorState.GenericError, sensor.error_state.state)
        self.assertEqual("Some Error", sensor.error_state.msg)

        sensor._set_error_state(SensorErrorState.TimeoutError, "Timeout Error")

        events = sensor.get_events()
        self.assertEqual(0, len(events))

        # Make sure error state did not change.
        self.assertEqual(SensorErrorState.GenericError, sensor.error_state.state)
        self.assertEqual("Some Error", sensor.error_state.msg)
