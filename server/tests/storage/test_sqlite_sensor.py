import logging
from tests.util import config_logging
from tests.storage.sqlite_core import TestStorageCore
from tests.storage.util import compare_sensors_content
from lib.localObjects import Sensor


class TestStorageSensor(TestStorageCore):

    def test_delete_sensor(self):
        """
        Test Sensor object deleting.
        """
        config_logging(logging.INFO)
        storage = self._create_sensors()

        node_id = self.sensors[0].nodeId
        init_db_sensors = storage.get_sensors(node_id)

        self.assertEqual(len(init_db_sensors), len(self.sensors))

        compare_sensors_content(self, self.sensors, init_db_sensors)

        removed_sensors = []
        for i in range(len(self.sensors)):
            sensor = self.sensors[i]
            storage.delete_sensor(sensor.sensorId)
            removed_sensors.append(sensor)

            curr_db_sensors = storage.get_sensors(node_id)

            self.assertEqual(len(self.sensors) - i - 1, len(curr_db_sensors))

            for curr_db_sensor in curr_db_sensors:
                # Check removed sensors are no longer stored in database.
                self.assertFalse(any([obj.sensorId == curr_db_sensor.sensorId for obj in removed_sensors]))

                # TODO check sensor object contents with compare_sensors_content



