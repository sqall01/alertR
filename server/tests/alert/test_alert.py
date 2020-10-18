import logging
import time
from unittest import TestCase
from typing import Tuple, List
from lib.localObjects import AlertLevel, SensorAlert, SensorDataType
from lib.alert.alert import SensorAlertExecuter, SensorAlertState
from lib.alert.instrumentation import InstrumentationPromise
from lib.globalData import GlobalData
from lib.storage.core import _Storage


def _callback_trigger_sensor_alert(_, sensor_alert_state: SensorAlertState):
    """
    Callback to overwrite _trigger_sensor_alert() of SensorAlertExecuter.
    :param _: self of SensorAlertExecuter object
    :param sensor_alert_state:
    """
    TestAlert._callback_trigger_sensor_alert_arg = sensor_alert_state


class MockStorage(_Storage):

    def __init__(self):
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value

    def isAlertSystemActive(self, _: logging.Logger = None):
        return self._is_active


class TestAlert(TestCase):

    _callback_trigger_sensor_alert_arg = None

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
        TestAlert._callback_trigger_sensor_alert_arg = None

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

        self.assertEqual(sensor_alert_state, TestAlert._callback_trigger_sensor_alert_arg)

    def test_process_sensor_alert_alert_delay(self):
        """
        Tests processing of sensor alerts with an alert delay.
        """
        TestAlert._callback_trigger_sensor_alert_arg = None

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

        self.assertEqual(None, TestAlert._callback_trigger_sensor_alert_arg)

        time.sleep(alert_delay)

        sensor_alert_executer._process_sensor_alert(sensor_alert_states)

        self.assertEqual(sensor_alert_state, TestAlert._callback_trigger_sensor_alert_arg)

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
