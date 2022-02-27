import time
import logging
from unittest import TestCase
from typing import List, Optional, Dict, Any
from tests.util import config_logging
from lib.globalData.sensorObjects import SensorDataGPS, SensorObjSensorAlert, SensorDataType, SensorObjStateChange, \
    SensorObjErrorStateChange, SensorErrorState
from lib.sensor.gps import _GPSSensor

'''
Tool to get GPS coordinates on map and draw polygons: https://umap.openstreetmap.fr/en/map/new
'''


class MockSensor(_GPSSensor):

    def __init__(self):
        super().__init__()

        self._positions = []  # type: List[SensorDataGPS]

        self._last_position = None  # type: Optional[SensorDataGPS]

        self._raise_exception = False

    @property
    def raise_exception(self) -> bool:
        return self._raise_exception

    @raise_exception.setter
    def raise_exception(self, value: bool):
        self._raise_exception = value

    def add_data(self, data: SensorDataGPS):
        self._positions.append(data)

    def _get_data(self) -> SensorDataGPS:

        if self._raise_exception:
            raise ValueError("Test Exception")

        if not self._positions:
            return self._last_position

        self._last_position = self._positions.pop(0)
        return self._last_position

    def _get_optional_data(self) -> Optional[Dict[str, Any]]:
        return None


class TestGpsSensor(TestCase):

    def setUp(self) -> None:
        config_logging(logging.DEBUG)

    def test_process_position_within_trigger_within(self):
        """
        Tests position processing (triggers if position is within geofence, position is within).
        """
        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = True
        sensor.initialize()

        position = SensorDataGPS(52.51743522098097,
                                 13.390316963195803,
                                 1337)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjSensorAlert)
        self.assertEqual(events[0].state, 1)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_process_position_without_trigger_within(self):
        """
        Tests position processing (triggers if position is within geofence, position is without).
        """
        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = True
        sensor.initialize()

        position = SensorDataGPS(52.51253841478769,
                                 13.391990661621096,
                                 1337)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjStateChange)
        self.assertEqual(events[0].state, 0)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_process_position_without_trigger_without(self):
        """
        Tests position processing (triggers if position is without geofence, position is without).
        """
        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = False
        sensor.initialize()

        position = SensorDataGPS(52.51253841478769,
                                 13.391990661621096,
                                 1337)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjSensorAlert)
        self.assertEqual(events[0].state, 1)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_process_position_within_trigger_without(self):
        """
        Tests position processing (triggers if position is without geofence, position is within).
        """
        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = False
        sensor.initialize()

        position = SensorDataGPS(52.51743522098097,
                                 13.390316963195803,
                                 1337)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjStateChange)
        self.assertEqual(events[0].state, 0)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_process_position_within_trigger_within_triggered(self):
        """
        Tests position processing (triggers if position is within geofence, position is within, already triggered).
        """
        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = True
        sensor.initialize()

        sensor.state = sensor.triggerState

        position = SensorDataGPS(52.51743522098097,
                                 13.390316963195803,
                                 1337)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjStateChange)
        self.assertEqual(events[0].state, 1)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_process_position_without_trigger_without_triggered(self):
        """
        Tests position processing (triggers if position is without geofence, position is without, already triggered).
        """
        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = False
        sensor.initialize()

        sensor.state = sensor.triggerState

        position = SensorDataGPS(52.51253841478769,
                                 13.391990661621096,
                                 1337)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjStateChange)
        self.assertEqual(events[0].state, 1)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_process_position_without_trigger_within_triggered(self):
        """
        Tests position processing (triggers if position is within geofence, position is without, already triggered).
        """
        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = True
        sensor.initialize()

        sensor.state = sensor.triggerState

        position = SensorDataGPS(52.51253841478769,
                                 13.391990661621096,
                                 1337)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjSensorAlert)
        self.assertEqual(events[0].state, 0)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_process_position_within_trigger_without_triggered(self):
        """
        Tests position processing (triggers if position is without geofence, position is within, already triggered).
        """
        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = False
        sensor.initialize()

        sensor.state = sensor.triggerState

        position = SensorDataGPS(52.51743522098097,
                                 13.390316963195803,
                                 1337)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjSensorAlert)
        self.assertEqual(events[0].state, 0)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_process_multi_geofences(self):
        """
        Tests position processing with multiple geofences (moving in and out of geofences).
        """
        fence_coords1 = [(52.519850777692575, 13.383772373199465),
                         (52.52030775996867, 13.396904468536379),
                         (52.51468001850454, 13.397247791290285),
                         (52.51452331933269, 13.384673595428469)]
        fence_coords2 = [(55.519850777692575, 10.383772373199465),
                         (55.52030775996867, 10.396904468536379),
                         (55.51468001850454, 10.397247791290285),
                         (55.51452331933269, 10.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords1)
        sensor.polygons.append(fence_coords2)
        sensor.trigger_within = True
        sensor.initialize()

        # Move into first geofence.
        position = SensorDataGPS(52.51743522098097,
                                 13.390316963195803,
                                 1337)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjSensorAlert)
        self.assertEqual(events[0].state, 1)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

        # Move out of geofence.
        position = SensorDataGPS(42.51743522098097,
                                 42.390316963195803,
                                 1338)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjSensorAlert)
        self.assertEqual(events[0].state, 0)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

        # Move into second geofence.
        position = SensorDataGPS(55.51743522098097,
                                 10.390316963195803,
                                 1339)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjSensorAlert)
        self.assertEqual(events[0].state, 1)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

        # Move into first geofence again.
        position = SensorDataGPS(52.51743522098097,
                                 13.390316963195803,
                                 1340)
        sensor._process_position(position)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjStateChange)
        self.assertEqual(events[0].state, 1)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_integration_single_position(self):
        """
        Tests the GPS sensor execution with the processing of one position that resides inside the geofence.
        """

        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = True
        sensor.interval = 5
        sensor.initialize()

        position = SensorDataGPS(52.51743522098097,
                                 13.390316963195803,
                                 1337)
        sensor.add_data(position)

        sensor.start()

        time.sleep(2.0)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjSensorAlert)
        self.assertEqual(events[0].state, 1)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position.lat)
        self.assertEqual(events[0].data.lon, position.lon)
        self.assertEqual(events[0].data.utctime, position.utctime)

    def test_integration_multi_positions(self):
        """
        Tests the GPS sensor execution with the processing of two positions:
        one residing outside and one inside geofence.
        """

        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = True
        sensor.interval = 3
        sensor.initialize()

        position1 = SensorDataGPS(52.512669003368266,
                                  13.390574455261232,
                                  1336)
        sensor.add_data(position1)

        position2 = SensorDataGPS(52.51743522098097,
                                  13.390316963195803,
                                  1337)
        sensor.add_data(position2)

        sensor.start()

        time.sleep(2.0)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjStateChange)
        self.assertEqual(events[0].state, 0)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position1.lat)
        self.assertEqual(events[0].data.lon, position1.lon)
        self.assertEqual(events[0].data.utctime, position1.utctime)

        time.sleep(4.0)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjSensorAlert)
        self.assertEqual(events[0].state, 1)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position2.lat)
        self.assertEqual(events[0].data.lon, position2.lon)
        self.assertEqual(events[0].data.utctime, position2.utctime)

    def test_integration_one_position_only_changes(self):
        """
        Tests the GPS data processing if no new data is available.
        """

        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = True
        sensor.interval = 1
        sensor.initialize()

        position1 = SensorDataGPS(52.512669003368266,
                                  13.390574455261232,
                                  1336)
        sensor.add_data(position1)

        sensor.start()

        time.sleep(2.0)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjStateChange)
        self.assertEqual(events[0].state, 0)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position1.lat)
        self.assertEqual(events[0].data.lon, position1.lon)
        self.assertEqual(events[0].data.utctime, position1.utctime)

        time.sleep(4.0)

        events = sensor.get_events()

        self.assertEqual(len(events), 0)

    def test_integration_old_data(self):
        """
        Tests the GPS data processing if old data was delivered by provider.
        """

        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = True
        sensor.interval = 1
        sensor.initialize()

        position1 = SensorDataGPS(52.512669003368266,
                                  13.390574455261232,
                                  1337)
        sensor.add_data(position1)

        position2 = SensorDataGPS(52.51743522098097,
                                  13.390316963195803,
                                  1336)
        sensor.add_data(position2)

        sensor.start()

        time.sleep(2.0)

        events = sensor.get_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjStateChange)
        self.assertEqual(events[0].state, 0)
        self.assertEqual(events[0].dataType, SensorDataType.GPS)
        self.assertEqual(events[0].data.lat, position1.lat)
        self.assertEqual(events[0].data.lon, position1.lon)
        self.assertEqual(events[0].data.utctime, position1.utctime)

        time.sleep(4.0)

        events = sensor.get_events()

        self.assertEqual(len(events), 0)

    def test_integration_provider_exception(self):
        """
        Tests the GPS data processing if provider raises an exception and recovers after a while.
        """

        fence_coords = [(52.519850777692575, 13.383772373199465),
                        (52.52030775996867, 13.396904468536379),
                        (52.51468001850454, 13.397247791290285),
                        (52.51452331933269, 13.384673595428469)]

        sensor = MockSensor()
        sensor.id = 1
        sensor.triggerState = 1
        sensor.triggerAlert = True
        sensor.triggerAlertNormal = True
        sensor.polygons.append(fence_coords)
        sensor.trigger_within = True
        sensor.interval = 1
        sensor.initialize()

        position = SensorDataGPS(52.51743522098097,
                                 13.390316963195803,
                                 1337)
        sensor.add_data(position)
        sensor.raise_exception = True

        sensor.start()

        time.sleep(3.0)

        events = sensor.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(type(events[0]), SensorObjErrorStateChange)
        self.assertEqual(events[0].error_state.state, SensorErrorState.ProcessingError)
        self.assertTrue(events[0].error_state.msg.endswith("Test Exception"))

        sensor.raise_exception = False

        time.sleep(3.0)

        events = sensor.get_events()

        # We expect two events:
        # 1) sensor error state back to OK
        # 2) sensor alert with new data
        self.assertEqual(len(events), 2)
        self.assertEqual(type(events[0]), SensorObjErrorStateChange)
        self.assertEqual(events[0].error_state.state, SensorErrorState.OK)
        self.assertEqual(type(events[1]), SensorObjSensorAlert)
        self.assertEqual(events[1].state, 1)
        self.assertEqual(events[1].dataType, SensorDataType.GPS)
        self.assertEqual(events[1].data.lat, position.lat)
        self.assertEqual(events[1].data.lon, position.lon)
        self.assertEqual(events[1].data.utctime, position.utctime)
