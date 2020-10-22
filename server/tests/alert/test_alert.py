import logging
import time
import os
from unittest import TestCase
from typing import Tuple, List, Dict, Optional
from lib.localObjects import AlertLevel, SensorAlert, SensorDataType
from lib.alert.alert import SensorAlertExecuter, SensorAlertState
from lib.alert.instrumentation import InstrumentationPromise, Instrumentation
from lib.globalData import GlobalData
from lib.storage.core import _Storage


def _callback_trigger_sensor_alert(_, sensor_alert_state: SensorAlertState):
    """
    Callback to overwrite _trigger_sensor_alert() of SensorAlertExecuter.
    :param _: self of SensorAlertExecuter object
    :param sensor_alert_state:
    """
    TestAlert._callback_trigger_sensor_alert_arg.append(sensor_alert_state)


class MockStorage(_Storage):

    def __init__(self):
        self._is_active = False
        self._sensor_alerts = dict()  # type: Dict[int, SensorAlert]

    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value

    def add_sensor_alert(self, sensor_alert: SensorAlert):
        self._sensor_alerts[sensor_alert.sensorAlertId] = sensor_alert

    def isAlertSystemActive(self, _: logging.Logger = None):
        return self._is_active

    def deleteSensorAlert(self,
                          sensorAlertId: int,
                          logger: logging.Logger = None) -> bool:
        if sensorAlertId in self._sensor_alerts.keys():
            del self._sensor_alerts[sensorAlertId]
            return True
        return False

    def getSensorAlerts(self,
                        _: logging.Logger = None)  -> Optional[List[SensorAlert]]:
        return list(self._sensor_alerts.values())


class MockInstrumentationNotCallable(Instrumentation):

    def __init__(self, alert_level: AlertLevel, sensor_alert: SensorAlert, logger: logging.Logger):
        super().__init__(alert_level, sensor_alert, logger)

    def _execute(self):
        TestCase.fail(TestCase(), "Not callable.")

    def _process_output(self, output: str):
        TestCase.fail(TestCase(), "Not callable.")

    def execute(self):
        TestCase.fail(TestCase(), "Not callable.")


class TestAlert(TestCase):

    _callback_trigger_sensor_alert_arg = list()

    def _create_sensor_alerts(self, num: int) -> Tuple[List[AlertLevel], List[SensorAlert]]:
        alert_levels = list()
        for i in range(num):
            alert_level = AlertLevel()
            alert_level.level = i
            alert_level.name = "AlertLevel_" + str(i)
            alert_level.triggerAlways = False
            alert_level.triggerAlertTriggered = False
            alert_level.triggerAlertNormal = False
            alert_level.instrumentation_active = False
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

    def test_update_suitable_alert_levels_deactivated(self):
        """
        Tests update of suitable alert levels when the alert system is deactivated.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.is_active = False

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlways = False
            alert_level.triggerAlertTriggered = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(0, len(sensor_alert_state.suitable_alert_levels))

    def test_update_suitable_alert_levels_activated(self):
        """
        Tests update of suitable alert levels when the alert system is activated.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.is_active = True

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlways = False
            alert_level.triggerAlertTriggered = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

            # Check if the only suitable alert level is actually the alert level of the sensor alert.
            self.assertEqual(sensor_alert_state._init_sensor_alert.alertLevels[0],
                             sensor_alert_state.suitable_alert_levels[0].level)

    def test_update_suitable_alert_levels_trigger_always_wrong_trigger_state(self):
        """
        Tests update of suitable alert levels when the alert system is deactivated,
        trigger always is set in alert level and the state is wrong.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.is_active = False

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlways = True
            alert_level.triggerAlertTriggered = False

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(0, len(sensor_alert_state.suitable_alert_levels))

    def test_update_suitable_alert_levels_trigger_always_correct_trigger_state(self):
        """
        Tests update of suitable alert levels when the alert system is deactivated,
        trigger always is set in alert level and the state is correct.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.is_active = False

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 1
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlways = True
            alert_level.triggerAlertTriggered = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

            # Check if the only suitable alert level is actually the alert level of the sensor alert.
            self.assertEqual(sensor_alert_state._init_sensor_alert.alertLevels[0],
                             sensor_alert_state.suitable_alert_levels[0].level)

    def test_update_suitable_alert_levels_trigger_always_wrong_normal_state(self):
        """
        Tests update of suitable alert levels when the alert system is deactivated,
        trigger always is set in alert level and the state is wrong.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.is_active = False

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 0
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlways = True
            alert_level.triggerAlertNormal = False

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(0, len(sensor_alert_state.suitable_alert_levels))

    def test_update_suitable_alert_levels_trigger_always_correct_normal_state(self):
        """
        Tests update of suitable alert levels when the alert system is deactivated,
        trigger always is set in alert level and the state is correct.
        """
        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.is_active = False

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        for sensor_alert in sensor_alerts:
            sensor_alert_state = SensorAlertState(sensor_alert, alert_levels)
            sensor_alert_state._init_sensor_alert.state = 0
            sensor_alert_states.append(sensor_alert_state)

        for alert_level in alert_levels:
            alert_level.triggerAlways = True
            alert_level.triggerAlertNormal = True

        sensor_alert_executer._update_suitable_alert_levels(sensor_alert_states)

        for sensor_alert_state in sensor_alert_states:
            self.assertEqual(1, len(sensor_alert_state.suitable_alert_levels))

            # Check if the only suitable alert level is actually the alert level of the sensor alert.
            self.assertEqual(sensor_alert_state._init_sensor_alert.alertLevels[0],
                             sensor_alert_state.suitable_alert_levels[0].level)

    def test_update_suitable_alert_levels_multiple_alert_levels(self):
        """
        Tests update of multiple suitable alert levels when the alert system is activated.
        """
        num = 6

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.storage = MockStorage()
        global_data.storage.is_active = True

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        sensor_alert_states = list()
        sensor_alert = sensor_alerts[0]
        sensor_alert.alertLevels.clear()
        num_suitable = 0
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.triggerAlways = False
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

            for suitable_alert_level in sensor_alert_state.suitable_alert_levels:
                # Check if each suitable alert level is actually an alert level of the sensor alert.
                self.assertTrue(any([al == suitable_alert_level.level
                                     for al in sensor_alert_state._init_sensor_alert.alertLevels]))

                # Check if the suitable alert level is the one that is set to trigger for state "triggered"
                self.assertTrue(suitable_alert_level.triggerAlertTriggered)

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

    def test_separate_instrumentation_alert_levels_half(self):
        """
        Tests split instrumented alert levels into separated sensor alert states (with remaining alert levels).
        """
        num = 10

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
        num = 10

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
        num = 10

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
        num = 10

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

    def test_run_trigger_always(self):
        """
        Integration test that checks if trigger always sensor alerts are processed correctly.
        """

        TestAlert._callback_trigger_sensor_alert_arg.clear()

        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        global_data.storage = MockStorage()
        global_data.storage.is_active = False

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        gt_set = set()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.triggerAlways = True
            alert_level.triggerAlertTriggered = (i % 2 == 0)
            if alert_level.triggerAlertTriggered:
                gt_set.add(alert_level.level)

        global_data.alertLevels = alert_levels
        for sensor_alert in sensor_alerts:
            sensor_alert.state = 1
            global_data.storage.add_sensor_alert(sensor_alert)

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

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

    def test_run_trigger_active(self):
        """
        Integration test that checks if sensor alerts that trigger when alarm system is activated
        are processed correctly.
        """

        TestAlert._callback_trigger_sensor_alert_arg.clear()

        num = 5

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")
        global_data.managerUpdateExecuter = None

        global_data.storage = MockStorage()
        global_data.storage.is_active = True

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        gt_set = set()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            alert_level.triggerAlertTriggered = False
            alert_level.triggerAlertNormal = (i % 2 == 0)
            if alert_level.triggerAlertNormal:
                gt_set.add(alert_level.level)

        global_data.alertLevels = alert_levels
        for sensor_alert in sensor_alerts:
            sensor_alert.state = 0
            global_data.storage.add_sensor_alert(sensor_alert)

        sensor_alert_executer = SensorAlertExecuter(global_data)

        # Overwrite _trigger_sensor_alert() function of SensorAlertExecuter object since it will be called
        # if a sensor alert is triggered.
        func_type = type(sensor_alert_executer._trigger_sensor_alert)
        sensor_alert_executer._trigger_sensor_alert = func_type(_callback_trigger_sensor_alert,
                                                                sensor_alert_executer)

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

    def test_run_instrumentation(self):
        """
        Integration test that checks if sensor alerts with instrumentation are processed correctly.
        """
        TestAlert._callback_trigger_sensor_alert_arg.clear()

        num = 10

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
        global_data.storage.is_active = False

        alert_levels, sensor_alerts = self._create_sensor_alerts(num)

        # Only use one sensor alert with multiple alert levels.
        base_sensor_alert = sensor_alerts[0]
        base_sensor_alert.state = 1
        base_sensor_alert.alertLevels.clear()
        global_data.storage.add_sensor_alert(base_sensor_alert)

        gt_alert_level_set = set()
        alert_levels_suppressed = list()
        for i in range(len(alert_levels)):
            alert_level = alert_levels[i]
            base_sensor_alert.alertLevels.append(alert_level.level)
            alert_level.triggerAlways = True
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

    def test_run_manager_updater(self):
        """
        Integration test that checks if sensor alerts that are dropped are send to the manager updater queue.
        """
        self.fail("TODO")
