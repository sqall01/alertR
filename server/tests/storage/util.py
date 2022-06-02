from unittest import TestCase
from typing import List
from lib.localObjects import Option, Sensor


def compare_options_content(context: TestCase, gt_options: List[Option], new_options: List[Option]):
    """
    Compares two lists of Option objects.
    :param context:
    :param gt_options:
    :param new_options:
    """
    if len(new_options) != len(gt_options):
        context.fail("Wrong number of objects.")

    already_processed = []
    for new_option in new_options:
        found = False
        for gt_option in gt_options:
            if new_option.type == gt_option.type:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_option in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_option)

                # Only the content of the object should have changed, not the object itself.
                if new_option == gt_option:
                    context.fail("Changed ground truth object, not content of existing object.")

                if new_option.value != gt_option.value:
                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find object.")


def compare_sensors_content(context: TestCase, gt_sensors: List[Sensor], new_sensors: List[Sensor]):
    """
    Compares two lists of Sensor objects.
    :param context:
    :param gt_sensors:
    :param new_sensors:
    """
    if len(new_sensors) != len(gt_sensors):
        context.fail("Wrong number of objects.")

    already_processed = []
    for new_sensor in new_sensors:
        found = False
        for gt_sensor in gt_sensors:
            if new_sensor.sensorId == gt_sensor.sensorId:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_sensor in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_sensor)

                # Only the content of the object should have changed, not the object itself.
                if new_sensor == gt_sensor:
                    context.fail("Changed ground truth object, not content of existing object.")

                if (new_sensor.nodeId != gt_sensor.nodeId
                        or new_sensor.clientSensorId != gt_sensor.clientSensorId
                        or new_sensor.description != gt_sensor.description
                        or new_sensor.state != gt_sensor.state
                        or new_sensor.error_state != gt_sensor.error_state
                        or new_sensor.alertDelay != gt_sensor.alertDelay
                        or new_sensor.dataType != gt_sensor.dataType
                        or new_sensor.data != gt_sensor.data
                        or not any(x in gt_sensor.alertLevels for x in new_sensor.alertLevels)
                        or not any(x in new_sensor.alertLevels for x in gt_sensor.alertLevels)):
                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find object.")
