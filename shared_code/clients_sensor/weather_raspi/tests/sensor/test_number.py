import time
from unittest import TestCase
from typing import Optional, Union
from lib.globalData.sensorObjects import SensorObjSensorAlert, SensorObjStateChange, SensorDataType, SensorOrdering
from lib.sensor.number import _NumberSensor


class MockNumberSensor(_NumberSensor):

    def __init__(self):
        self._next_data = 0
        super().__init__()

    def _get_data(self) -> Optional[Union[float, int]]:
        return self._next_data

    @property
    def next_data(self) -> int:
        return self._next_data

    @next_data.setter
    def next_data(self, data: int):
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
        sensor._sane_lowest_value = -1337
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
        sensor.sensorData = 0

        sensor.initialize()
        sensor.start()

        self.assertEqual(0, sensor.sensorData)

        sensor.next_data = 1
        time.sleep(1.0)

        self.assertEqual(1, sensor.sensorData)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(1, events[0].sensorData)

    def test_threshold_trigger_lower_than(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (lower than, triggered).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.LT
        sensor.state = 0
        sensor.sensorData = 2

        sensor.initialize()
        sensor.start()

        self.assertEqual(2, sensor.sensorData)

        sensor.next_data = 0
        time.sleep(1.0)

        self.assertEqual(0, sensor.sensorData)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(0, events[0].sensorData)

    def test_threshold_trigger_greater_than(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (greater than, triggered).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.GT
        sensor.state = 0
        sensor.sensorData = 0

        sensor.initialize()
        sensor.start()

        self.assertEqual(0, sensor.sensorData)

        sensor.next_data = 2
        time.sleep(1.0)

        self.assertEqual(2, sensor.sensorData)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(1, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(2, events[0].sensorData)

    def test_threshold_normal_equal(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (equal, normal).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 0
        sensor.ordering = SensorOrdering.EQ
        sensor.state = 1
        sensor.sensorData = 0

        sensor.initialize()
        sensor.start()

        self.assertEqual(0, sensor.sensorData)

        sensor.next_data = 1
        time.sleep(1.0)

        self.assertEqual(1, sensor.sensorData)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(1, events[0].sensorData)

    def test_threshold_normal_lower_than(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (lower than, normal).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.LT
        sensor.state = 1
        sensor.sensorData = 0

        sensor.initialize()
        sensor.start()

        self.assertEqual(0, sensor.sensorData)

        sensor.next_data = 2
        time.sleep(1.0)

        self.assertEqual(2, sensor.sensorData)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(2, events[0].sensorData)

    def test_threshold_normal_greater_than(self):
        """
        Tests Sensor Alert generation if threshold is satisfied (greater than, normal).
        """
        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.GT
        sensor.state = 1
        sensor.sensorData = 2

        sensor.initialize()
        sensor.start()

        self.assertEqual(2, sensor.sensorData)

        sensor.next_data = 0
        time.sleep(1.0)

        self.assertEqual(0, sensor.sensorData)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjSensorAlert, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertTrue(events[0].changeState)
        self.assertTrue(events[0].hasLatestData)
        self.assertFalse(events[0].hasOptionalData)
        self.assertIsNone(events[0].optionalData)
        self.assertEqual(0, events[0].sensorData)

    def test_no_threshold(self):
        """
        Tests state change if no threshold is set.
        """

        sensor = self._create_base_sensor()

        sensor.hasThreshold = False
        sensor.state = 0
        sensor.sensorData = 0

        sensor.initialize()
        sensor.start()

        self.assertEqual(0, sensor.sensorData)

        sensor.next_data = 2
        time.sleep(1.0)

        self.assertEqual(2, sensor.sensorData)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertEqual(2, events[0].sensorData)

    def test_threshold_not_satisfied(self):
        """
        Tests state change if threshold is not satisfied.
        """

        sensor = self._create_base_sensor()

        sensor.hasThreshold = True
        sensor.threshold = 1
        sensor.ordering = SensorOrdering.EQ
        sensor.state = 0
        sensor.sensorData = 0

        sensor.initialize()
        sensor.start()

        self.assertEqual(0, sensor.sensorData)

        sensor.next_data = 2
        time.sleep(1.0)

        self.assertEqual(2, sensor.sensorData)

        events = sensor.get_events()
        self.assertEqual(1, len(events))
        self.assertEqual(SensorObjStateChange, type(events[0]))
        self.assertEqual(0, events[0].state)
        self.assertEqual(2, events[0].sensorData)

    def test_same_data(self):
        """
        Tests that no change in data does not generate an event.
        """

        sensor = self._create_base_sensor()

        sensor.hasThreshold = False
        sensor.state = 0
        sensor.sensorData = 1337

        sensor.initialize()
        sensor.start()

        self.assertEqual(1337, sensor.sensorData)

        sensor.next_data = 1337
        time.sleep(1.0)

        self.assertEqual(1337, sensor.sensorData)

        events = sensor.get_events()
        self.assertEqual(0, len(events))
