import logging
import time
from unittest import TestCase
from lib.localObjects import AlertLevel, SensorAlert
from lib.alert.alert import SensorAlertExecuter, SensorAlertState
from lib.globalData import GlobalData


class TestAlert(TestCase):

    def test_filter_sensor_alerts(self):
        """
        Tests filtering of sensor alert states.
        """
        global_data = GlobalData()
        global_data.logger = logging.getLogger("Alert Test Case")

        sensor_alert_executer = SensorAlertExecuter(global_data)

        alert_levels = list()
        for i in range(5):
            alert_level = AlertLevel()
            alert_level.level = i
            alert_level.name = "AlertLevel_" + str(i)
            alert_levels.append(alert_level)

        utc_now = int(time.time())
        sensor_alerts = list()
        for i in range(5):
            sensor_alert = SensorAlert()
            sensor_alert.sensorAlertId = i
            sensor_alert.description = "SensorAlert_" + str(i)
            sensor_alert.alertLevels.append(i)
            sensor_alert.timeReceived = utc_now
            sensor_alert.alertDelay = 0
            sensor_alerts.append(sensor_alert)

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
                self.assertEqual(j, dropped_states[j].sensor_alert.sensorAlertId)
            for j in range(len(new_states)):
                self.assertEqual(j+i, new_states[j].sensor_alert.sensorAlertId)
