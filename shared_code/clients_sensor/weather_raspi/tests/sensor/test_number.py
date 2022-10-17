import time
from unittest import TestCase
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange, SensorDataType, SensorOrdering, \
    SensorDataInt, SensorErrorState, SensorObjErrorStateChange
from lib.sensor.number import _NumberSensor


class MockNumberSensor(_NumberSensor):

    def __init__(self):
        super().__init__()
        self._next_data = SensorDataInt(0, "test unit")
        self._log_desc = "Mock Sensor"

    def _get_data(self) -> SensorDataInt:
        return self._next_data

    @property
    def next_data(self) -> SensorDataInt:
        return self._next_data

    @next_data.setter
    def next_data(self, data: SensorDataInt):
        self._next_data = data

    def initialize(self) -> bool:
        pass


class TestNumberSensor(TestCase):

    def _create_base_sensor(self) -> MockNumberSensor:
        sensor = MockNumberSensor()
        sensor.id = 1
        sensor.description = "Test Number"
        sensor.alertDelay = 0
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.triggerState = 1
        sensor.alertLevels = [1]
        sensor.sensorDataType = SensorDataType.INT
        self._sensors.append(sensor)
        return sensor

    def setUp(self):
        self._sensors = []

    def tearDown(self):
        for sensor in self._sensors:
            sensor.exit()

    def test_threshold_trigger_equal(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (equal, triggered).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.EQ
        sensor.state = 0
        sensor.data = SensorDataInt(0, "test unit")

        sensor.initialize()
        sensor.start()

        self.assertEqual(SensorDataInt(0, "test unit"), sensor.data)

        sensor.next_data = SensorDataInt(1, "test unit")
        time.sleep(1.0)

        self.assertEqual(SensorDataInt(1, "test unit"), sensor.data)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(SensorDataInt(1, "test unit"), events[0].data)

    def test_threshold_trigger_lower_than(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (lower than, triggered).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.LT
        sensor.state = 0
        sensor.data = SensorDataInt(2, "test unit")

        sensor.initialize()
        sensor.start()

        self.assertEqual(SensorDataInt(2, "test unit"), sensor.data)

        sensor.next_data = SensorDataInt(0, "test unit")
        time.sleep(1.0)

        self.assertEqual(SensorDataInt(0, "test unit"), sensor.data)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(SensorDataInt(0, "test unit"), events[0].data)

    def test_threshold_trigger_greater_than(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (greater than, triggered).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.GT
        sensor.state = 0
        sensor.data = SensorDataInt(0, "test unit")

        sensor.initialize()
        sensor.start()

        self.assertEqual(SensorDataInt(0, "test unit"), sensor.data)

        sensor.next_data = SensorDataInt(2, "test unit")
        time.sleep(1.0)

        self.assertEqual(SensorDataInt(2, "test unit"), sensor.data)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(SensorDataInt(2, "test unit"), events[0].data)

    def test_threshold_normal_equal(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (equal, normal).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 0
        sensor.ordering = SensorOrdering.EQ
        sensor.state = 1
        sensor.data = SensorDataInt(0, "test unit")

        sensor.initialize()
        sensor.start()

        self.assertEqual(SensorDataInt(0, "test unit"), sensor.data)

        sensor.next_data = SensorDataInt(1, "test unit")
        time.sleep(1.0)

        self.assertEqual(SensorDataInt(1, "test unit"), sensor.data)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(SensorDataInt(1, "test unit"), events[0].data)

    def test_threshold_normal_lower_than(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (lower than, normal).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.LT
        sensor.state = 1
        sensor.data = SensorDataInt(0, "test unit")

        sensor.initialize()
        sensor.start()

        self.assertEqual(SensorDataInt(0, "test unit"), sensor.data)

        sensor.next_data = SensorDataInt(2, "test unit")
        time.sleep(1.0)

        self.assertEqual(SensorDataInt(2, "test unit"), sensor.data)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(SensorDataInt(2, "test unit"), events[0].data)

    def test_threshold_normal_greater_than(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (greater than, normal).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.GT
        sensor.state = 1
        sensor.data = SensorDataInt(2, "test unit")

        sensor.initialize()
        sensor.start()

        self.assertEqual(SensorDataInt(2, "test unit"), sensor.data)

        sensor.next_data = SensorDataInt(0, "test unit")
        time.sleep(1.0)

        self.assertEqual(SensorDataInt(0, "test unit"), sensor.data)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(SensorDataInt(0, "test unit"), events[0].data)

    def test_no_threshold(self):
        """
        Tests state change if no threshold is set.
        """

        sensor = self._create_base_sensor()

        sensor.hasThreshold = False
        sensor.state = 0
        sensor.data = SensorDataInt(0, "test unit")

        sensor.initialize()
        sensor.start()

        self.assertEqual(SensorDataInt(0, "test unit"), sensor.data)

        sensor.next_data = SensorDataInt(2, "test unit")
        time.sleep(1.0)

        self.assertEqual(SensorDataInt(2, "test unit"), sensor.data)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertEqual(SensorDataInt(2, "test unit"), events[0].data)

    def test_threshold_not_satisfied(self):
        """
        Tests state change if threshold is not satisfied.
        """

        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.EQ
        sensor.state = 0
        sensor.data = SensorDataInt(0, "test unit")

        sensor.initialize()
        sensor.start()

        self.assertEqual(SensorDataInt(0, "test unit"), sensor.data)

        sensor.next_data = SensorDataInt(2, "test unit")
        time.sleep(1.0)

        self.assertEqual(SensorDataInt(2, "test unit"), sensor.data)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertEqual(SensorDataInt(2, "test unit"), events[0].data)

    def test_same_data(self):
        """
        Tests that no change in data does not generate an event.
        """

        sensor = self._create_base_sensor()

        sensor.hasThreshold = False
        sensor.state = 0
        sensor.data = SensorDataInt(1337, "test unit")

        sensor.initialize()
        sensor.start()

        self.assertEqual(SensorDataInt(1337, "test unit"), sensor.data)

        sensor.next_data = SensorDataInt(1337, "test unit")
        time.sleep(1.0)

        self.assertEqual(SensorDataInt(1337, "test unit"), sensor.data)

        events = sensor.get_events()
        self.assertEqual(0, len(events))

    def test_error_state_change_without_new_data(self):
        """
        Tests if error state is changed back to normal if sensor processing works correctly again and no
        new data occurred while a not-OK error state existed.
        """

        sensor = self._create_base_sensor()

        sensor.hasThreshold = False
        sensor.state = 0
        sensor.data = sensor.next_data

        sensor.initialize()

        # Set error state.
        sensor.error_state = SensorErrorState(SensorErrorState.GenericError, "test error")

        sensor.start()

        time.sleep(1)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjErrorStateChange, type(events[0]))
        self.assertEqual(SensorErrorState.OK, events[0].error_state.state)

        # Make sure sensor state has not changed.
        self.assertEqual(0, sensor.state)
