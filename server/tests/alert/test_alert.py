import logging
import time
import os
import collections
import threading
import json
from unittest import TestCase
from typing import Tuple, List, Dict, Optional
from lib.localObjects import AlertLevel, SensorAlert, SensorDataType, SensorData, Option, Sensor
from lib.alert.alert import SensorAlertExecuter, SensorAlertState
from lib.alert.instrumentation import InstrumentationPromise, Instrumentation
from lib.globalData import GlobalData
from lib.storage.core import _Storage
from lib.internalSensors import AlertLevelInstrumentationErrorSensor


def _callback_trigger_sensor_alert(_, sensor_alert_state: SensorAlertState):
    """
    Callback to overwrite _trigger_sensor_alert() of SensorAlertExecuter.
    :param _: self of SensorAlertExecuter object
    :param sensor_alert_state:
    """
    TestAlert._callback_trigger_sensor_alert_arg.append(sensor_alert_state)


class MockStorage(_Storage):

    def __init__(self):
        self._profile = 0
        self._sensors = dict()  # type: Dict[int, Sensor]

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, profile: int):
        self._profile = profile

    @property
    def sensor_state_updates(self) -> Dict[int, List[Tuple[int, int]]]:
        raise NotImplementedError("TODO")

    def add_sensor(self, sensor: Sensor):
        self._sensors[sensor.sensorId] = Sensor().deepcopy(sensor)

    def getSensorById(self,
                      sensorId: int,
                      logger: logging.Logger = None) -> Optional[Sensor]:
        if sensorId in self._sensors.keys():
            return self._sensors[sensorId]
        return None

    def update_sensor_data(self, sensor_data: SensorData):  # TODO is this function still needed?
        if (sensor_data.sensorId in self._sensors.keys()
                and sensor_data.dataType == self._sensors[sensor_data.sensorId].dataType):
            self._sensors[sensor_data.sensorId].data = sensor_data.data

        else:
            raise ValueError("Sensor %d does not exist." % sensor_data.sensorId)

    def update_sensor_state(self, sensor_id: int, state: int):  # TODO is this function still needed?
        if sensor_id in self._sensors.keys():
            self._sensors[sensor_id].state = state

        else:
            raise ValueError("Sensor %d does not exist." % sensor_id)

    def get_option_by_type(self,
                           option_type: str,
                           logger: logging.Logger = None) -> Optional[Option]:
        if option_type == "profile":
            option = Option()
            option.type = option_type
            option.value = self._profile
            return option
        return None

    def getSensorData(self,
                      sensorId: int,
                      _: logging.Logger = None) -> Optional[SensorData]:
        if sensorId not in self._sensors.keys():
            return None

        sensor = self._sensors[sensorId]
        sensor_data = SensorData()
        sensor_data.sensorId = sensor.sensorId
        sensor_data.data = sensor.data
        sensor_data.dataType = sensor.dataType

        return sensor_data

    def getSensorState(self,
                       sensorId: int,
                       _: logging.Logger = None) -> Optional[int]:
        if sensorId not in self._sensors.keys():
            return None
        return self._sensors[sensorId].state

    def updateSensorState(self,
                          nodeId: int,
                          stateList: List[Tuple[int, int]],
                          logger: logging.Logger = None) -> bool:
        raise NotImplementedError("TODO")

        self._sensor_state_updates[nodeId] = stateList
        return True


class MockInstrumentationNotCallable(Instrumentation):

    def __init__(self, alert_level: AlertLevel, sensor_alert: SensorAlert, logger: logging.Logger):
        super().__init__(alert_level, sensor_alert, logger)

    def _execute(self):
        TestCase.fail(TestCase(), "Not callable.")

    def _process_output(self, output: str):
        TestCase.fail(TestCase(), "Not callable.")

    def execute(self):
        TestCase.fail(TestCase(), "Not callable.")


class MockManagerUpdateExecuter:

    def __init__(self):
        self._queue_state_change = collections.deque()
        self._manager_update_event = threading.Event()
        self._manager_update_event.clear()

    def queue_state_change(self,
                           sensor_id: int,
                           state: int,
                           sensor_data: Optional[SensorData]):
        self._queue_state_change.append((sensor_id, state, sensor_data))
        self._manager_update_event.set()


class MockInternalSensor(AlertLevelInstrumentationErrorSensor):

    def __init__(self, global_data: GlobalData):
        super().__init__(global_data)


class TestAlert(TestCase):

    _callback_trigger_sensor_alert_arg = list()

    def _create_sensor_alerts(self, num: int) -> Tuple[List[AlertLevel], List[SensorAlert]]:
        alert_levels = list()
        for i in range(num):
            alert_level = AlertLevel()
            alert_level.level = i
            alert_level.name = "AlertLevel_" + str(i)
            alert_level.triggerAlertTriggered = False
            alert_level.triggerAlertNormal = False
            alert_level.instrumentation_active = False
            alert_level.profiles = [0]
            alert_levels.append(alert_level)

        utc_now = int(time.time())
        sensor_alerts = list()
        for i in range(num):
            sensor_alert = SensorAlert()
            sensor_alert.sensorAlertId = i
            sensor_alert.nodeId = i
            sensor_alert.sensorId = i
            sensor_alert.description = "SensorAlert_" + str(i)
            sensor_alert.timeReceived = utc_now
            sensor_alert.alertDelay = 0
            sensor_alert.state = 1
            sensor_alert.hasOptionalData = False
            sensor_alert.changeState = False
            sensor_alert.alertLevels.append(i)
            sensor_alert.hasLatestData = False
            sensor_alert.dataType = SensorDataType.NONE
            sensor_alerts.append(sensor_alert)

        return alert_levels, sensor_alerts

    def test_filter_sensor_alerts_suitable_alert_levels(self):
        """
        Tests filtering of sensor alert states through suitable alert levels.
        """
        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(5)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_states.append(sensor_alert_state)

        for i in range(len(sensor_alert_states)):

            # Prepare sensor alert states to filter out.
            for j in range(i):
                sensor_alert_states[j]._suitable_alert_levels.clear()

            # Execute actual filter function.
            new_states, dropped_states = sensor_alert_executer._filter_sensor_alerts(sensor_alert_states)

            self.assertEqual(i, len(dropped_states))
            self.assertEqual(len(sensor_alert_states) - i, len(new_states))
            for j in range(i):
                self.assertEqual(j, dropped_states[j].sensorAlertId)
            for j in range(len(new_states)):
                self.assertEqual(j+i, new_states[j].sensor_alert.sensorAlertId)

    def test_filter_sensor_alerts_instrumentation_suppress(self):
        """
        Tests filtering of sensor alert states through instrumentation that suppress.
        """
        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(5)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state.uses_instrumentation = True
            instrumentation_promise = InstrumentationPromise(sensor_alert_state.suitable_alert_levels[0],
                                                             sensor_alert)
            instrumentation_promise.new_sensor_alert = None
            sensor_alert_state.instrumentation_promise = instrumentation_promise
            sensor_alert_states.append(sensor_alert_state)

        for i in range(len(sensor_alert_states)):

            # Prepare sensor alert states to filter out.
            for j in range(i):
                sensor_alert_states[j]._instrumentation_promise.set_success()

            # Execute actual filter function.
            new_states, dropped_states = sensor_alert_executer._filter_sensor_alerts(sensor_alert_states)

            self.assertEqual(i, len(dropped_states))
            self.assertEqual(len(sensor_alert_states) - i, len(new_states))
            for j in range(i):
                self.assertEqual(j, dropped_states[j].sensorAlertId)
            for j in range(len(new_states)):
                self.assertEqual(j+i, new_states[j].init_sensor_alert.sensorAlertId)

    def test_filter_sensor_alerts_instrumentation_fail(self):
        """
        Tests filtering of sensor alert states through instrumentation that failure.
        """
        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(5)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state.uses_instrumentation = True
            instrumentation_promise = InstrumentationPromise(sensor_alert_state.suitable_alert_levels[0],
                                                             sensor_alert)
            instrumentation_promise.new_sensor_alert = None
            sensor_alert_state.instrumentation_promise = instrumentation_promise
            sensor_alert_states.append(sensor_alert_state)

        for i in range(len(sensor_alert_states)):

            # Prepare sensor alert states to filter out.
            for j in range(i):
                sensor_alert_states[j]._instrumentation_promise.set_failed()

            # Execute actual filter function.
            new_states, dropped_states = sensor_alert_executer._filter_sensor_alerts(sensor_alert_states)

            self.assertEqual(i, len(dropped_states))
            self.assertEqual(len(sensor_alert_states) - i, len(new_states))
            for j in range(i):
                self.assertEqual(j, dropped_states[j].sensorAlertId)
            for j in range(len(new_states)):
                self.assertEqual(j+i, new_states[j].init_sensor_alert.sensorAlertId)

    def test_update_suitable_alert_levels_wrong_profile(self):
        """
        Tests update of suitable alert levels when the system profile does not match the one of the alert level.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.profile = 99

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlertTriggered = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(0, len(sensor_alert_state.suitable_alert_levels))
            self.assertTrue(sensor_alert_state.instrumentation_processed)

    def test_update_suitable_alert_levels_correct_profile(self):
        """
        Tests update of suitable alert levels when the system profile does match the one of the alert level.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlertTriggered = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

            # Check if the only suitable alert level is actually the alert level of the sensor alert.
            self.assertEqual(sensor_alert_state._init_sensor_alert.alertLevels[0],
                             sensor_alert_state.suitable_alert_levels[0].level)

            self.assertTrue(sensor_alert_state.instrumentation_processed)

    def test_update_suitable_alert_levels_multiple_profiles(self):
        """
        Tests update of suitable alert levels when the alert level has multiple system profiles.
        """
        num = 9

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.profile = 3

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        ctr = 0
        sensor_alert_states = list()
        sensor_alert_states_that_trigger = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_states.append(sensor_alert_state)

            if ctr % 2:
                sensor_alert_states_that_trigger.append(sensor_alert_state)
            ctr += 1

        ctr = 0
        alert_levels_that_trigger = list()
        for alert_level in alert_levels:
            alert_level.triggerAlertTriggered = True

            if ctr % 2:
                alert_level.profiles = [0, 1, 2, 3, 4]
                alert_levels_that_trigger.append(alert_level.level)

            else:
                alert_level.profiles = [0, 1, 2, 4]
            ctr += 1

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:

            # Distinguish checks between sensor alerts we know will trigger and the ones that will not.
            if sensor_alert_state in sensor_alert_states_that_trigger:
                self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

                # Check if the only suitable alert level is actually the alert level of the sensor alert.
                self.assertEqual(sensor_alert_state._init_sensor_alert.alertLevels[0],
                                 sensor_alert_state.suitable_alert_levels[0].level)

                # Check if the suitable alert level belongs to the alert levels that have the correct profile.
                self.assertTrue(sensor_alert_state.suitable_alert_levels[0].level in alert_levels_that_trigger)

            else:
                self.assertEqual(0, len(sensor_alert_state.suitable_alert_levels))

                # Check if the alert level of the sensor alert belongs _NOT_ to the alert levels that have
                # the correct profile.
                self.assertFalse(sensor_alert_state._init_sensor_alert.alertLevels[0] in alert_levels_that_trigger)

            self.assertTrue(sensor_alert_state.instrumentation_processed)

    def test_update_suitable_alert_levels_multiple_alert_levels(self):
        """
        Tests update of multiple suitable alert levels when the system profile does match.
        """

        # Use odd number to have different group sizes.
        num = 7

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        sensor_alert = sensor_alerts[0]
        sensor_alert.alertLevels.clear()
        num_suitable = 0
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.triggerAlertTriggered = (i % 2 == 0)
            sensor_alert.alertLevels.append(alert_level.level)
            if alert_level.triggerAlertTriggered:
                num_suitable += 1

        sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
        sensor_alert_state._init_sensor_alert.state = 1
        sensor_alert_states.append(sensor_alert_state)

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(num_suitable, len(sensor_alert_state.suitable_alert_levels))
            self.assertTrue(sensor_alert_state.instrumentation_processed)

            for suitable_alert_level in sensor_alert_state.suitable_alert_levels:
                # Check if each suitable alert level is actually an alert level of the sensor alert.
                self.assertTrue(any([al == suitable_alert_level.level
                                     for al in sensor_alert_state._init_sensor_alert.alertLevels]))

                # Check if the suitable alert level is the one that is set to trigger for state "triggered"
                self.assertTrue(suitable_alert_level.triggerAlertTriggered)

    def test_update_suitable_alert_levels_instrumentation_unfinished(self):
        """
        Tests update of suitable alert levels when the sensor alert is instrumented and not finished.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.profile = 99

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_state.uses_instrumentation = True
            for alert_level in alert_levels:
                if alert_level.level in sensor_alert.alertLevels:
                    sensor_alert_state.instrumentation_promise = InstrumentationPromise(
                        alert_level,
                        sensor_alert_state.init_sensor_alert)
                    break
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlertTriggered = True
            alert_level.instrumentation_active = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

            # Check if the only suitable alert level is actually the alert level of the sensor alert.
            self.assertEqual(sensor_alert_state._init_sensor_alert.alertLevels[0],
                             sensor_alert_state.suitable_alert_levels[0].level)

            self.assertFalse(sensor_alert_state.instrumentation_processed)

    def test_update_suitable_alert_levels_instrumentation_finished(self):
        """
        Tests update of suitable alert levels when the sensor alert is instrumented and finished.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_state.uses_instrumentation = True
            for alert_level in alert_levels:
                if alert_level.level in sensor_alert.alertLevels:
                    sensor_alert_state.instrumentation_promise = InstrumentationPromise(
                        alert_level,
                        sensor_alert_state.init_sensor_alert)
                    sensor_alert_state.instrumentation_promise.set_success()
                    sensor_alert_state.instrumentation_promise.new_sensor_alert = sensor_alert_state.init_sensor_alert
                    break
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlertTriggered = True
            alert_level.instrumentation_active = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

            # Check if the only suitable alert level is actually the alert level of the sensor alert.
            self.assertEqual(sensor_alert_state._init_sensor_alert.alertLevels[0],
                             sensor_alert_state.suitable_alert_levels[0].level)

            self.assertTrue(sensor_alert_state.instrumentation_processed)

    def test_update_suitable_alert_levels_instrumentation_finished_not_triggered(self):
        """
        Tests update of suitable alert levels when the sensor alert is instrumented, finished and does not
        satisfy trigger conditions.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.profile = 99

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_state.uses_instrumentation = True
            for alert_level in alert_levels:
                if alert_level.level in sensor_alert.alertLevels:
                    sensor_alert_state.instrumentation_promise = InstrumentationPromise(
                        alert_level,
                        sensor_alert_state.init_sensor_alert)
                    sensor_alert_state.instrumentation_promise.set_success()
                    sensor_alert_state.instrumentation_promise.new_sensor_alert = sensor_alert_state.init_sensor_alert
                    break
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlertTriggered = True
            alert_level.instrumentation_active = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(0, len(sensor_alert_state.suitable_alert_levels))
            self.assertTrue(sensor_alert_state.instrumentation_processed)

    def test_update_suitable_alert_levels_instrumentation_toggle_state_not_triggered(self):
        """
        Tests update of suitable alert levels when the sensor alert is instrumented, finishes by toggling the state
        and it does no longer satisfy the trigger conditions.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_state.uses_instrumentation = True
            for alert_level in alert_levels:
                if alert_level.level in sensor_alert.alertLevels:
                    sensor_alert_state.instrumentation_promise = InstrumentationPromise(
                        alert_level,
                        sensor_alert_state.init_sensor_alert)
                    sensor_alert_state.instrumentation_promise.set_success()
                    sensor_alert_state.instrumentation_promise.new_sensor_alert = \
                        SensorAlert().deepcopy(sensor_alert_state.init_sensor_alert)
                    sensor_alert_state.instrumentation_promise.new_sensor_alert.state = 0
                    break
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlertTriggered = True
            alert_level.triggerAlertNormal = False
            alert_level.instrumentation_active = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(0, len(sensor_alert_state.suitable_alert_levels))
            self.assertTrue(sensor_alert_state.instrumentation_processed)

    def test_update_suitable_alert_levels_instrumentation_toggle_state_triggered(self):
        """
        Tests update of suitable alert levels when the sensor alert is instrumented, finishes by toggling the state
        and now it satisfies the trigger conditions.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_state.uses_instrumentation = True
            for alert_level in alert_levels:
                if alert_level.level in sensor_alert.alertLevels:
                    sensor_alert_state.instrumentation_promise = InstrumentationPromise(
                        alert_level,
                        sensor_alert_state.init_sensor_alert)
                    sensor_alert_state.instrumentation_promise.set_success()
                    sensor_alert_state.instrumentation_promise.new_sensor_alert = \
                        SensorAlert().deepcopy(sensor_alert_state.init_sensor_alert)
                    sensor_alert_state.instrumentation_promise.new_sensor_alert.state = 0
                    break
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlertTriggered = False
            alert_level.triggerAlertNormal = True
            alert_level.instrumentation_active = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

            # Check if the only suitable alert level is actually the alert level of the sensor alert.
            self.assertEqual(sensor_alert_state._init_sensor_alert.alertLevels[0],
                             sensor_alert_state.suitable_alert_levels[0].level)

            self.assertTrue(sensor_alert_state.instrumentation_processed)

    def test_process_sensor_alert(self):
        """
        Tests processing of sensor alerts.
        """
        TestAlert._callback_trigger_sensor_alert_arg.clear()

        num = 1

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        sensor_alert_state = SensorAlertState(sensor_alerts[0], alert_levels)
        sensor_alert_states.append(sensor_alert_state)

        sensor_alert_executer._process_sensor_alert(sensor_alert_states)

        self.assertEqual(1, len(TestAlert._callback_trigger_sensor_alert_arg))
        self.assertEqual(sensor_alert_state, TestAlert._callback_trigger_sensor_alert_arg[0])

    def test_process_sensor_alert_alert_delay(self):
        """
        Tests processing of sensor alerts with an alert delay.
        """
        TestAlert._callback_trigger_sensor_alert_arg.clear()

        num = 1
        alert_delay = 2

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert = sensor_alerts[0]
        sensor_alert.alertDelay = alert_delay

        sensor_alert_states = list()
        sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
        sensor_alert_states.append(sensor_alert_state)

        sensor_alert_executer._process_sensor_alert(sensor_alert_states)

        self.assertEqual(0, len(TestAlert._callback_trigger_sensor_alert_arg))

        time.sleep(alert_delay)

        sensor_alert_executer._process_sensor_alert(sensor_alert_states)

        self.assertEqual(1, len(TestAlert._callback_trigger_sensor_alert_arg))
        self.assertEqual(sensor_alert_state, TestAlert._callback_trigger_sensor_alert_arg[0])

    def test_separate_instrumentation_alert_levels_one(self):
        """
        Tests split instrumented alert levels into separated sensor alert states with only one existing alert level
        which is instrumented.
        """
        num = 1

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        sensor_alert = sensor_alerts[0]
        sensor_alert.alertLevels.clear()

        alert_level = alert_levels[0]
        sensor_alert.alertLevels.append(alert_level.level)
        alert_level.instrumentation_active = True

        sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
        sensor_alert_states.append(sensor_alert_state)

        new_sensor_alert_states = sensor_alert_executer._separate_instrumentation_alert_levels(sensor_alert_states)

        self.assertEqual(1, len(new_sensor_alert_states))

        sensor_alert_state = new_sensor_alert_states[0]

        self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

        suitable_alert_level = sensor_alert_state.suitable_alert_levels[0]
        self.assertTrue(sensor_alert_state.suitable_alert_levels[0].instrumentation_active)
        self.assertTrue(sensor_alert_state.uses_instrumentation)

    def test_separate_instrumentation_alert_levels_one_not_instrumented(self):
        """
        Tests split instrumented alert levels into separated sensor alert states with only one existing alert level
        which is not instrumented.
        """
        num = 1

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        sensor_alert = sensor_alerts[0]
        sensor_alert.alertLevels.clear()

        alert_level = alert_levels[0]
        sensor_alert.alertLevels.append(alert_level.level)
        alert_level.instrumentation_active = False

        sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
        sensor_alert_states.append(sensor_alert_state)

        new_sensor_alert_states = sensor_alert_executer._separate_instrumentation_alert_levels(sensor_alert_states)

        self.assertEqual(1, len(new_sensor_alert_states))

        sensor_alert_state = new_sensor_alert_states[0]

        self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

        suitable_alert_level = sensor_alert_state.suitable_alert_levels[0]
        self.assertFalse(suitable_alert_level.instrumentation_active)
        self.assertFalse(sensor_alert_state.uses_instrumentation)

    def test_separate_instrumentation_alert_levels_half(self):
        """
        Tests split instrumented alert levels into separated sensor alert states (with remaining alert levels).
        """

        # Use odd number to have different group sizes.
        num = 11

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        sensor_alert = sensor_alerts[0]
        sensor_alert.alertLevels.clear()
        num_instrumentation = 0
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.instrumentation_active = (i % 2 == 0)
            sensor_alert.alertLevels.append(alert_level.level)
            if alert_level.instrumentation_active:
                num_instrumentation += 1

        sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
        sensor_alert_states.append(sensor_alert_state)

        new_sensor_alert_states = sensor_alert_executer._separate_instrumentation_alert_levels(sensor_alert_states)

        self.assertEqual(num_instrumentation + 1, len(new_sensor_alert_states))

        for sensor_alert_state in new_sensor_alert_states:

            # Sensor alert states with a single suitable alert level should only have instrumented alert levels.
            if len(sensor_alert_state.suitable_alert_levels) == 1:
                self.assertTrue(sensor_alert_state.suitable_alert_levels[0].instrumentation_active)
                self.assertTrue(sensor_alert_state.uses_instrumentation)

            # Sensor alert states with multiple alert levels should not have instrumented alert levels left.
            else:
                for suitable_alert_level in sensor_alert_state.suitable_alert_levels:
                    self.assertFalse(suitable_alert_level.instrumentation_active)
                    self.assertFalse(sensor_alert_state.uses_instrumentation)

    def test_separate_instrumentation_alert_levels_complete(self):
        """
        Tests split instrumented alert levels into separated sensor alert states (without remaining alert levels).
        """
        num = 11

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        sensor_alert = sensor_alerts[0]
        sensor_alert.alertLevels.clear()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.instrumentation_active = True
            sensor_alert.alertLevels.append(alert_level.level)

        sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
        sensor_alert_states.append(sensor_alert_state)

        new_sensor_alert_states = sensor_alert_executer._separate_instrumentation_alert_levels(sensor_alert_states)

        self.assertEqual(num, len(new_sensor_alert_states))

        for sensor_alert_state in new_sensor_alert_states:

            # Sensor alert states with a single suitable alert level should only have instrumented alert levels.
            if len(sensor_alert_state.suitable_alert_levels) == 1:
                self.assertTrue(sensor_alert_state.suitable_alert_levels[0].instrumentation_active)
                self.assertTrue(sensor_alert_state.uses_instrumentation)

            # Sensor alert states with multiple alert levels should not be left.
            else:
                self.fail("Sensor Alert state with not instrumented alert level remaining.")

    def test_separate_instrumentation_alert_levels_none(self):
        """
        Tests split instrumented alert levels into separated sensor alert states (only remaining alert levels).
        """
        num = 11

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        sensor_alert = sensor_alerts[0]
        sensor_alert.alertLevels.clear()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.instrumentation_active = False
            sensor_alert.alertLevels.append(alert_level.level)

        sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
        sensor_alert_states.append(sensor_alert_state)

        new_sensor_alert_states = sensor_alert_executer._separate_instrumentation_alert_levels(sensor_alert_states)

        self.assertEqual(1, len(new_sensor_alert_states))

        for sensor_alert_state in new_sensor_alert_states:

            # Sensor alert states with a single suitable alert level should not exist.
            if len(sensor_alert_state.suitable_alert_levels) == 1:
                self.fail("Sensor Alert state with not instrumented alert level remaining.")

            # Sensor alert states with multiple alert levels should not have instrumented alert levels left.
            else:
                for suitable_alert_level in sensor_alert_state.suitable_alert_levels:
                    self.assertFalse(sensor_alert_state.uses_instrumentation)
                    self.assertFalse(suitable_alert_level.instrumentation_active)

    def test_separate_instrumentation_alert_levels_single_none(self):
        """
        Tests split instrumented alert levels into separated sensor alert states (only remaining alert levels).
        """
        num = 11

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.instrumentation_active = False

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_states.append(sensor_alert_state)

        new_sensor_alert_states = sensor_alert_executer._separate_instrumentation_alert_levels(sensor_alert_states)

        self.assertEqual(num, len(new_sensor_alert_states))

        for sensor_alert_state in new_sensor_alert_states:

            # Sensor alert states with a single suitable alert level should not exist.
            if len(sensor_alert_state.suitable_alert_levels) == 1:
                self.assertFalse(sensor_alert_state.uses_instrumentation)
                self.assertFalse(sensor_alert_state.suitable_alert_levels[0].instrumentation_active)

            else:
                self.fail("Sensor Alert state with multiple suitable alert levels found.")

    def test_update_instrumentation_no_instrumentation(self):
        """
        Tests update of instrumentation when no instrumentation is used.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_states.append(sensor_alert_state)

        sensor_alert_executer._update_instrumentation(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertIsNone(sensor_alert_state.instrumentation)

    def test_update_instrumentation_no_suitable_alert_level(self):
        """
        Tests update of instrumentation when no suitable alert level in sensor alert state.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state.uses_instrumentation = True
            sensor_alert_state._suitable_alert_levels.clear()
            sensor_alert_states.append(sensor_alert_state)

        sensor_alert_executer._update_instrumentation(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertIsNone(sensor_alert_state.instrumentation)

    def test_update_instrumentation_already_executed(self):
        """
        Tests update of instrumentation when instrumentation was already executed.
        """

        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state.uses_instrumentation = True

            # Simulate an already running instrumentation by setting an instrumentation promise and using a mock
            # instrumentation that is not callable and crashes the test if it is called.
            alert_level = sensor_alert_state.suitable_alert_levels[0]
            sensor_alert_state.instrumentation_promise = InstrumentationPromise(alert_level, sensor_alert)
            sensor_alert_state.instrumentation = MockInstrumentationNotCallable(alert_level,
                                                                                sensor_alert,
                                                                                global_data.logger)
            sensor_alert_states.append(sensor_alert_state)

        # Asserts if the instrumentation object is used.
        sensor_alert_executer._update_instrumentation(sensor_alert_states)

    def test_update_instrumentation(self):
        """
        Tests update of instrumentation.
        """

        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        target_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "mirror_with_timestamp.py")

        for alert_level in alert_levels:
            alert_level.instrumentation_active = True
            alert_level.instrumentation_cmd = target_cmd
            alert_level.instrumentation_timeout = 10

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state.uses_instrumentation = True
            sensor_alert_states.append(sensor_alert_state)

        sensor_alert_executer._update_instrumentation(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertIsNotNone(sensor_alert_state.instrumentation)

            self.assertTrue(sensor_alert_state.instrumentation_promise.is_finished(blocking=False, timeout=5.0))
            self.assertTrue(sensor_alert_state.instrumentation_promise.was_success())

            init_sensor_alert = sensor_alert_state.init_sensor_alert
            self.assertIsNotNone(init_sensor_alert)
            self.assertFalse(init_sensor_alert.hasOptionalData)
            self.assertIsNone(init_sensor_alert.optionalData)

            sensor_alert = sensor_alert_state.sensor_alert
            self.assertNotEqual(init_sensor_alert, sensor_alert)
            self.assertIsNotNone(sensor_alert)
            self.assertTrue(sensor_alert.hasOptionalData)
            self.assertTrue("timestamp" in sensor_alert.optionalData.keys())

    def test_queue_manager_update_no_change(self):
        """
        Tests that sensor alerts without any data/state change are not queued for state change processing.
        """

        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        global_data.storage = MockStorage()
        global_data.storage.profile = 99

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        for sensor_alert in sensor_alerts:
            sensor_alert.hasLatestData = False
            sensor_alert.changeState = False

        sensor_alert_executer = SensorAlertExecuter(global_data)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        sensor_alert_executer._queue_manager_update(sensor_alerts)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        self.assertEqual(0, len(manager_update_executer._queue_state_change))

    def test_queue_manager_update_state_change(self):
        """
        Tests that sensor alerts with a state change are queued for state change processing.
        """

        # Use odd number to have different group sizes.
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        storage = MockStorage()
        global_data.storage = storage

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        for i in range(len(sensor_alerts)):
            sensor_alert = sensor_alerts[i]
            sensor_alert.hasLatestData = False
            sensor_alert.changeState = True
            sensor_alert.state = i % 2

            sensor_data = SensorData()
            sensor_data.sensorId = sensor_alert.sensorId
            if (i % 3) == 0:
                sensor_data.dataType = SensorDataType.NONE
            elif (i % 3) == 1:
                sensor_data.dataType = SensorDataType.INT
                sensor_data.data = i
            else:
                sensor_data.dataType = SensorDataType.FLOAT
                sensor_data.data = float(i)
            storage.add_sensor_data(sensor_data)

            storage.add_sensor_state(sensor_alert.sensorId, sensor_alert.state)

        sensor_alert_executer = SensorAlertExecuter(global_data)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        sensor_alert_executer._queue_manager_update(sensor_alerts)

        self.assertTrue(manager_update_executer._manager_update_event.is_set())

        self.assertEqual(num, len(manager_update_executer._queue_state_change))

        for sensor_id, state, sensor_data in manager_update_executer._queue_state_change:
            found = False
            for sensor_alert in sensor_alerts:
                if sensor_id == sensor_alert.sensorId:
                    found = True
                    self.assertEqual(sensor_alert.state, state)
                    self.assertEqual(sensor_alert.sensorId, sensor_data.sensorId)
                    gt_sensor_data = storage.getSensorData(sensor_id)
                    self.assertEqual(gt_sensor_data.sensorId, sensor_data.sensorId)
                    self.assertEqual(gt_sensor_data.dataType, sensor_data.dataType)
                    self.assertEqual(gt_sensor_data.data, sensor_data.data)
                    break
            self.assertTrue(found)

    def test_queue_manager_update_data_change(self):
        """
        Tests that sensor alerts with a data change are queued for state change processing.
        """

        # Use odd number to have different group sizes.
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        storage = MockStorage()
        global_data.storage = storage

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        for i in range(len(sensor_alerts)):
            sensor_alert = sensor_alerts[i]
            sensor_alert.hasLatestData = True
            sensor_alert.changeState = False
            sensor_alert.state = i % 2

            sensor_data = SensorData()
            sensor_data.sensorId = sensor_alert.sensorId
            if (i % 3) == 0:
                sensor_data.dataType = SensorDataType.NONE
            elif (i % 3) == 1:
                sensor_data.dataType = SensorDataType.INT
                sensor_data.data = i
            else:
                sensor_data.dataType = SensorDataType.FLOAT
                sensor_data.data = float(i)
            storage.add_sensor_data(sensor_data)

            storage.add_sensor_state(sensor_alert.sensorId, sensor_alert.state)

        sensor_alert_executer = SensorAlertExecuter(global_data)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        sensor_alert_executer._queue_manager_update(sensor_alerts)

        self.assertTrue(manager_update_executer._manager_update_event.is_set())

        self.assertEqual(num, len(manager_update_executer._queue_state_change))

        for sensor_id, state, sensor_data in manager_update_executer._queue_state_change:
            found = False
            for sensor_alert in sensor_alerts:
                if sensor_id == sensor_alert.sensorId:
                    found = True
                    self.assertEqual(sensor_alert.state, state)
                    self.assertEqual(sensor_alert.sensorId, sensor_data.sensorId)
                    gt_sensor_data = storage.getSensorData(sensor_id)
                    self.assertEqual(gt_sensor_data.sensorId, sensor_data.sensorId)
                    self.assertEqual(gt_sensor_data.dataType, sensor_data.dataType)
                    self.assertEqual(gt_sensor_data.data, sensor_data.data)
                    break
            self.assertTrue(found)

    def test_queue_manager_update_state_change_db_fail(self):
        """
        Tests that sensor alerts with a state change which a faulty database entry are
        not queued for state change processing.
        """

        # Use odd number to have different group sizes.
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        storage = MockStorage()
        global_data.storage = storage

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        for i in range(len(sensor_alerts)):
            sensor_alert = sensor_alerts[i]
            sensor_alert.hasLatestData = False
            sensor_alert.changeState = True
            sensor_alert.state = i % 2

            sensor_data = SensorData()
            sensor_data.sensorId = sensor_alert.sensorId
            if (i % 3) == 0:
                sensor_data.dataType = SensorDataType.NONE
            elif (i % 3) == 1:
                sensor_data.dataType = SensorDataType.INT
                sensor_data.data = i
            else:
                sensor_data.dataType = SensorDataType.FLOAT
                sensor_data.data = float(i)
            storage.add_sensor_data(sensor_data)

        sensor_alert_executer = SensorAlertExecuter(global_data)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        sensor_alert_executer._queue_manager_update(sensor_alerts)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        self.assertEqual(0, len(manager_update_executer._queue_state_change))

    def test_queue_manager_update_data_change_db_fail(self):
        """
        Tests that sensor alerts with a data change which a faulty database entry are
        not queued for state change processing.
        """

        # Use odd number to have different group sizes.
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        storage = MockStorage()
        global_data.storage = storage

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        for i in range(len(sensor_alerts)):
            sensor_alert = sensor_alerts[i]
            sensor_alert.hasLatestData = True
            sensor_alert.changeState = False
            sensor_alert.state = i % 2

            storage.add_sensor_state(sensor_alert.sensorId, sensor_alert.state)

        sensor_alert_executer = SensorAlertExecuter(global_data)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        sensor_alert_executer._queue_manager_update(sensor_alerts)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        self.assertEqual(0, len(manager_update_executer._queue_state_change))

    def test_run_trigger_correct_profile(self):  # TODO
        """
        Integration test that checks if sensor alerts that trigger when the system profile does match
        are processed correctly.
        """

        TestAlert._callback_trigger_sensor_alert_arg.clear()

        # Use odd number to have different group sizes.
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        gt_set = set()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.triggerAlertTriggered = False
            alert_level.triggerAlertNormal = (i % 2 == 0)
            if alert_level.triggerAlertNormal:
                gt_set.add(alert_level.level)

        sensor_alert_executer = SensorAlertExecuter(global_data)
        global_data.alertLevels = alert_levels
        for sensor_alert in sensor_alerts:
            sensor_alert.state = 0
            sensor_alert.changeState = True

            sensor = Sensor()
            sensor.sensorId = sensor_alert.sensorId
            sensor.nodeId = sensor_alert.nodeId
            sensor.description = sensor_alert.description
            sensor.alertDelay  = sensor_alert.alertDelay
            sensor.alertLevels = list(sensor_alert.alertLevels)
            global_data.storage.add_sensor(sensor)

            json_data = "" if sensor_alert.optionalData else json.dumps(sensor_alert.optionalData)
            sensor_alert_executer.add_sensor_alert(sensor_alert.nodeId,
                                                   sensor_alert.sensorId,
                                                   sensor_alert.state,
                                                   json_data,
                                                   sensor_alert.changeState,
                                                   sensor_alert.hasLatestData,
                                                   sensor_alert.dataType,
                                                   sensor_alert.sensorData)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        # Start executer thread.
        sensor_alert_executer.daemon = True
        sensor_alert_executer.start()

        time.sleep(1)

        sensor_alert_executer.exit()

        time.sleep(1)

        self.assertEqual(len(gt_set), len(TestAlert._callback_trigger_sensor_alert_arg))

        test_set = set([sas.sensor_alert.sensorAlertId for sas in TestAlert._callback_trigger_sensor_alert_arg])
        self.assertEqual(gt_set, test_set)

        # Check sensor alerts in database were removed after processing.
        self.assertEqual(0, len(global_data.storage.getSensorAlerts()))

        # Sensor alerts that did not trigger should lead to an manager state update.
        self.assertTrue(manager_update_executer._manager_update_event.is_set())
        self.assertEqual(num - len(gt_set), len(manager_update_executer._queue_state_change))

    def test_run_instrumentation(self):
        """
        Integration test that checks if sensor alerts with instrumentation (mirroring and suppression)
        are processed correctly.
        """
        TestAlert._callback_trigger_sensor_alert_arg.clear()

        # Use odd number to have different group sizes.
        num = 11

        trigger_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "instrumentation_scripts",
                                   "mirror_with_timestamp.py")

        suppress_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "instrumentation_scripts",
                                    "suppress.py")

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        # Only use one sensor alert with multiple alert levels.
        base_sensor_alert = sensor_alerts[0]
        base_sensor_alert.state = 1
        base_sensor_alert.alertLevels.clear()
        base_sensor_alert.changeState = True
        global_data.storage.add_sensor_alert(base_sensor_alert)

        base_sensor_data = SensorData()
        base_sensor_data.sensorId = base_sensor_alert.sensorId
        base_sensor_data.dataType = SensorDataType.NONE
        global_data.storage.add_sensor_data(base_sensor_data)
        global_data.storage.add_sensor_state(base_sensor_alert.sensorId, base_sensor_alert.state)

        gt_alert_level_set = set()
        alert_levels_suppressed = list()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            base_sensor_alert.alertLevels.append(alert_level.level)
            alert_level.triggerAlertTriggered = True
            alert_level.instrumentation_active = True
            alert_level.instrumentation_timeout = 10
            if (i % 2) == 0:
                alert_level.instrumentation_cmd = trigger_cmd
                gt_alert_level_set.add(alert_level.level)
            else:
                alert_level.instrumentation_cmd = suppress_cmd
                alert_levels_suppressed.append(alert_level)

        global_data.alertLevels = alert_levels

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        # Start executer thread.
        sensor_alert_executer.daemon = True
        sensor_alert_executer.start()

        time.sleep(1)

        sensor_alert_executer.exit()

        time.sleep(1)

        self.assertEqual(len(gt_alert_level_set), len(TestAlert._callback_trigger_sensor_alert_arg))

        test_alert_level_set = set()
        for sensor_alert_state in TestAlert._callback_trigger_sensor_alert_arg:
            self.assertIsNotNone(sensor_alert_state.sensor_alert)
            self.assertTrue(sensor_alert_state.uses_instrumentation)
            self.assertEqual(base_sensor_alert, sensor_alert_state.init_sensor_alert)
            self.assertNotEqual(base_sensor_alert, sensor_alert_state.sensor_alert)
            self.assertEqual(1, len(sensor_alert_state.sensor_alert.triggeredAlertLevels))
            test_alert_level_set.add(sensor_alert_state.sensor_alert.triggeredAlertLevels[0])
            self.assertEqual(num, len(sensor_alert_state.sensor_alert.alertLevels))
            self.assertTrue(sensor_alert_state.sensor_alert.hasOptionalData)
            self.assertTrue("timestamp" in sensor_alert_state.sensor_alert.optionalData.keys())

        # Check if each alert level was triggered.
        self.assertEqual(gt_alert_level_set, test_alert_level_set)

        # Check no suppressed alert level got triggered.
        for alert_level in alert_levels_suppressed:
            self.assertFalse(alert_level.level in test_alert_level_set)

        # Check sensor alerts in database were removed after processing.
        self.assertEqual(0, len(global_data.storage.getSensorAlerts()))

        # Sensor alerts that did not trigger should lead to an manager state update.
        self.assertTrue(manager_update_executer._manager_update_event.is_set())
        self.assertEqual(len(alert_levels_suppressed), len(manager_update_executer._queue_state_change))

    def test_run_instrumentation_toggle_state(self):
        """
        Integration test that checks if sensor alerts with instrumentation that
        change the state are correctly processed (no longer satisfies trigger condition after instrumentation
        and starts to satisfy trigger condition after instrumentation).
        """
        TestAlert._callback_trigger_sensor_alert_arg.clear()

        # Use odd number to have different group sizes.
        num = 11

        toggle_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "instrumentation_scripts",
                                  "toggle_state.py")

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        # Only use one sensor alert with multiple alert levels.
        base_sensor_alert = sensor_alerts[0]
        base_sensor_alert.state = 1
        base_sensor_alert.alertLevels.clear()
        base_sensor_alert.changeState = True
        global_data.storage.add_sensor_alert(base_sensor_alert)

        base_sensor_data = SensorData()
        base_sensor_data.sensorId = base_sensor_alert.sensorId
        base_sensor_data.dataType = SensorDataType.NONE
        global_data.storage.add_sensor_data(base_sensor_data)
        global_data.storage.add_sensor_state(base_sensor_alert.sensorId, base_sensor_alert.state)

        gt_alert_level_set = set()
        alert_levels_no_longer_triggered = list()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            base_sensor_alert.alertLevels.append(alert_level.level)
            if (i % 2) == 0:
                alert_level.triggerAlertTriggered = False
                alert_level.triggerAlertNormal = True
                gt_alert_level_set.add(alert_level.level)
            else:
                alert_level.triggerAlertTriggered = True
                alert_level.triggerAlertNormal = False
                alert_levels_no_longer_triggered.append(alert_level)

            alert_level.instrumentation_active = True
            alert_level.instrumentation_timeout = 10
            alert_level.instrumentation_cmd = toggle_cmd

        global_data.alertLevels = alert_levels

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        # Start executer thread.
        sensor_alert_executer.daemon = True
        sensor_alert_executer.start()

        time.sleep(3)

        sensor_alert_executer.exit()

        time.sleep(2)

        self.assertEqual(len(gt_alert_level_set), len(TestAlert._callback_trigger_sensor_alert_arg))

        test_alert_level_set = set()
        for sensor_alert_state in TestAlert._callback_trigger_sensor_alert_arg:
            self.assertIsNotNone(sensor_alert_state.sensor_alert)
            self.assertEqual(0, sensor_alert_state.sensor_alert.state)
            self.assertTrue(sensor_alert_state.uses_instrumentation)
            self.assertEqual(base_sensor_alert, sensor_alert_state.init_sensor_alert)
            self.assertNotEqual(base_sensor_alert, sensor_alert_state.sensor_alert)
            self.assertEqual(1, len(sensor_alert_state.sensor_alert.triggeredAlertLevels))
            test_alert_level_set.add(sensor_alert_state.sensor_alert.triggeredAlertLevels[0])
            self.assertEqual(num, len(sensor_alert_state.sensor_alert.alertLevels))

        # Check if each alert level was triggered.
        self.assertEqual(gt_alert_level_set, test_alert_level_set)

        # Check alert levels that no longer satisfy trigger conditions got triggered.
        for alert_level in alert_levels_no_longer_triggered:
            self.assertFalse(alert_level.level in test_alert_level_set)

        # Check sensor alerts in database were removed after processing.
        self.assertEqual(0, len(global_data.storage.getSensorAlerts()))

        # Sensor alerts that did not trigger should lead to an manager state update.
        self.assertTrue(manager_update_executer._manager_update_event.is_set())
        self.assertEqual(len(alert_levels_no_longer_triggered), len(manager_update_executer._queue_state_change))

    def test_run_instrumentation_timeout(self):
        """
        Integration test that checks if sensor alerts with instrumentation that times out is processed correctly
        """
        TestAlert._callback_trigger_sensor_alert_arg.clear()

        num = 3

        timeout_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "instrumentation_scripts",
                                   "timeout.py")

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        # Only use one sensor alert with multiple alert levels.
        base_sensor_alert = sensor_alerts[0]
        base_sensor_alert.state = 1
        base_sensor_alert.changeState = True
        base_sensor_alert.alertLevels.clear()
        global_data.storage.add_sensor_alert(base_sensor_alert)

        base_sensor_data = SensorData()
        base_sensor_data.sensorId = base_sensor_alert.sensorId
        base_sensor_data.dataType = SensorDataType.NONE
        global_data.storage.add_sensor_data(base_sensor_data)
        global_data.storage.add_sensor_state(base_sensor_alert.sensorId, base_sensor_alert.state)

        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            base_sensor_alert.alertLevels.append(alert_level.level)
            alert_level.triggerAlertTriggered = True
            alert_level.triggerAlertNormal = False
            alert_level.instrumentation_active = True
            alert_level.instrumentation_timeout = 2
            alert_level.instrumentation_cmd = timeout_cmd

        global_data.alertLevels = alert_levels

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        # Start executer thread.
        sensor_alert_executer.daemon = True
        sensor_alert_executer.start()

        time.sleep(5)

        sensor_alert_executer.exit()

        time.sleep(2)

        self.assertEqual(0, len(TestAlert._callback_trigger_sensor_alert_arg))

        # Check sensor alerts in database were removed after processing.
        self.assertEqual(0, len(global_data.storage.getSensorAlerts()))

        # Sensor alerts that did not trigger should lead to an manager state update.
        self.assertTrue(manager_update_executer._manager_update_event.is_set())
        self.assertEqual(num, len(manager_update_executer._queue_state_change))

    def test_run_instrumentation_failed(self):
        """
        Integration test that checks if sensor alerts with instrumentation that fails is processed correctly
        """
        TestAlert._callback_trigger_sensor_alert_arg.clear()

        num = 3

        timeout_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "instrumentation_scripts",
                                   "not_executable.py")

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        # Only use one sensor alert with multiple alert levels.
        base_sensor_alert = sensor_alerts[0]
        base_sensor_alert.state = 1
        base_sensor_alert.alertLevels.clear()
        base_sensor_alert.changeState = True
        global_data.storage.add_sensor_alert(base_sensor_alert)

        base_sensor_data = SensorData()
        base_sensor_data.sensorId = base_sensor_alert.sensorId
        base_sensor_data.dataType = SensorDataType.NONE
        global_data.storage.add_sensor_data(base_sensor_data)
        global_data.storage.add_sensor_state(base_sensor_alert.sensorId, base_sensor_alert.state)

        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            base_sensor_alert.alertLevels.append(alert_level.level)
            alert_level.triggerAlertTriggered = True
            alert_level.triggerAlertNormal = False
            alert_level.instrumentation_active = True
            alert_level.instrumentation_timeout = 2
            alert_level.instrumentation_cmd = timeout_cmd

        global_data.alertLevels = alert_levels

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        # Start executer thread.
        sensor_alert_executer.daemon = True
        sensor_alert_executer.start()

        time.sleep(5)

        sensor_alert_executer.exit()

        time.sleep(2)

        self.assertEqual(0, len(TestAlert._callback_trigger_sensor_alert_arg))

        # Check sensor alerts in database were removed after processing.
        self.assertEqual(0, len(global_data.storage.getSensorAlerts()))

        # Sensor alerts that did not trigger should lead to an manager state update.
        self.assertTrue(manager_update_executer._manager_update_event.is_set())
        self.assertEqual(num, len(manager_update_executer._queue_state_change))

    def test_run_alert_delay(self):
        """
        Integration test that checks if alert delay sensor alerts are processed correctly.
        """

        TestAlert._callback_trigger_sensor_alert_arg.clear()

        num = 5
        delay = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        gt_set = set()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.triggerAlertTriggered = True
            gt_set.add(alert_level.level)

        global_data.alertLevels = alert_levels
        for sensor_alert in sensor_alerts:
            sensor_alert.state = 1
            sensor_alert.alertDelay = delay
            sensor_alert.changeState = True
            global_data.storage.add_sensor_alert(sensor_alert)

            sensor_data = SensorData()
            sensor_data.sensorId = sensor_alert.sensorId
            sensor_data.dataType = SensorDataType.NONE
            global_data.storage.add_sensor_data(sensor_data)
            global_data.storage.add_sensor_state(sensor_alert.sensorId, sensor_alert.state)

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        # Start executer thread.
        sensor_alert_executer.daemon = True
        sensor_alert_executer.start()

        for i in range(delay-1):
            self.assertEqual(0, len(TestAlert._callback_trigger_sensor_alert_arg))
            time.sleep(1)

            # Check sensor alerts in database were removed while processing.
            self.assertEqual(0, len(global_data.storage.getSensorAlerts()))

            self.assertFalse(manager_update_executer._manager_update_event.is_set())

        time.sleep(2)

        sensor_alert_executer.exit()

        time.sleep(1)

        self.assertEqual(len(gt_set), len(TestAlert._callback_trigger_sensor_alert_arg))

        test_set = set([sas.sensor_alert.sensorAlertId for sas in TestAlert._callback_trigger_sensor_alert_arg])
        self.assertEqual(gt_set, test_set)

        # No sensor alert should was dropped that should trigger a state update.
        self.assertFalse(manager_update_executer._manager_update_event.is_set())
        self.assertEqual(0, len(manager_update_executer._queue_state_change))

    def test_run_alert_delay_canceled(self):
        """
        Integration test that checks if alert delay sensor alerts that satisfy all conditions in the beginning
        but this changes during the delay are processed correctly.
        """

        TestAlert._callback_trigger_sensor_alert_arg.clear()

        num = 5
        delay = 10

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        global_data.storage = MockStorage()
        global_data.storage.profile = 0

        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        gt_set = set()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.triggerAlertTriggered = True
            gt_set.add(alert_level.level)

        global_data.alertLevels = alert_levels
        for sensor_alert in sensor_alerts:
            sensor_alert.state = 1
            sensor_alert.alertDelay = delay
            sensor_alert.changeState = True
            global_data.storage.add_sensor_alert(sensor_alert)

            sensor_data = SensorData()
            sensor_data.sensorId = sensor_alert.sensorId
            sensor_data.dataType = SensorDataType.NONE
            global_data.storage.add_sensor_data(sensor_data)
            global_data.storage.add_sensor_state(sensor_alert.sensorId, sensor_alert.state)

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        self.assertFalse(manager_update_executer._manager_update_event.is_set())

        # Start executer thread.
        sensor_alert_executer.daemon = True
        sensor_alert_executer.start()

        for i in range(int(delay/2)):
            self.assertEqual(0, len(TestAlert._callback_trigger_sensor_alert_arg))
            time.sleep(1)

            # Check sensor alerts in database were removed while processing.
            self.assertEqual(0, len(global_data.storage.getSensorAlerts()))

            self.assertFalse(manager_update_executer._manager_update_event.is_set())
            self.assertEqual(0, len(manager_update_executer._queue_state_change))

        # Change system profile to change trigger condition.
        global_data.storage.profile = 99

        for i in range(int(delay/2) + 1):
            self.assertEqual(0, len(TestAlert._callback_trigger_sensor_alert_arg))
            time.sleep(1)

        sensor_alert_executer.exit()

        time.sleep(1)

        self.assertEqual(0, len(TestAlert._callback_trigger_sensor_alert_arg))

        # All sensor alerts should have been dropped.
        self.assertTrue(manager_update_executer._manager_update_event.is_set())
        self.assertEqual(num, len(manager_update_executer._queue_state_change))

    def test_run_internal_sensor_update_last_state_time_unnecessary(self):
        """
        Integration test that checks if the state of the internal sensor is not unnecessarily updated.
        """
        TestAlert._callback_trigger_sensor_alert_arg.clear()

        # Use odd number to have different group sizes.
        num = 1

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        storage = MockStorage()
        storage.profile = 0
        global_data.storage = storage

        internal_sensor = MockInternalSensor(global_data)
        internal_sensor.nodeId = 1
        internal_sensor.remoteSensorId = 2
        internal_sensor.state = 0
        global_data.internalSensors.append(internal_sensor)

        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.triggerAlertTriggered = True

        global_data.alertLevels = alert_levels
        for sensor_alert in sensor_alerts:
            sensor_alert.state = 1
            sensor_alert.changeState = True
            global_data.storage.add_sensor_alert(sensor_alert)

        gt_last_state_updated = int(time.time()) - 10
        internal_sensor.lastStateUpdated = gt_last_state_updated

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        self.assertEqual(0, len(TestAlert._callback_trigger_sensor_alert_arg))

        # Start executer thread.
        sensor_alert_executer.daemon = True
        sensor_alert_executer.start()

        time.sleep(1)

        sensor_alert_executer.exit()

        time.sleep(1)

        # Make sure a full processing run was executed.
        self.assertEqual(1, len(TestAlert._callback_trigger_sensor_alert_arg))

        self.assertEqual(gt_last_state_updated, internal_sensor.lastStateUpdated)

        self.assertEqual(0, len(storage.sensor_state_updates.keys()))

    def test_run_internal_sensor_update_last_state_time_necessary(self):
        """
        Integration test that checks if the state of the internal sensor is updated.
        """
        TestAlert._callback_trigger_sensor_alert_arg.clear()

        # Use odd number to have different group sizes.
        num = 1

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        storage = MockStorage()
        storage.profile = 0
        global_data.storage = storage

        internal_sensor = MockInternalSensor(global_data)
        internal_sensor.nodeId = 1
        internal_sensor.remoteSensorId = 2
        internal_sensor.state = 0
        global_data.internalSensors.append(internal_sensor)

        manager_update_executer = MockManagerUpdateExecuter()
        global_data.managerUpdateExecuter = manager_update_executer

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.triggerAlertTriggered = True

        global_data.alertLevels = alert_levels
        for sensor_alert in sensor_alerts:
            sensor_alert.state = 1
            sensor_alert.changeState = True
            global_data.storage.add_sensor_alert(sensor_alert)

        gt_last_state_updated = int(time.time()) - 31
        internal_sensor.lastStateUpdated = gt_last_state_updated

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

        self.assertEqual(0, len(TestAlert._callback_trigger_sensor_alert_arg))

        # Start executer thread.
        sensor_alert_executer.daemon = True
        sensor_alert_executer.start()

        time.sleep(1)

        sensor_alert_executer.exit()

        time.sleep(1)

        # Make sure a full processing run was executed.
        self.assertEqual(1, len(TestAlert._callback_trigger_sensor_alert_arg))

        self.assertNotEqual(gt_last_state_updated, internal_sensor.lastStateUpdated)

        self.assertEqual(1, len(storage.sensor_state_updates.keys()))
        self.assertEqual(internal_sensor.remoteSensorId, storage.sensor_state_updates[internal_sensor.nodeId][0][0])
        self.assertEqual(internal_sensor.state, storage.sensor_state_updates[internal_sensor.nodeId][0][1])
