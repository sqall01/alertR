from unittest import TestCase
from typing import List
from lib.globalData.localObjects import Option, Alert, Manager, Sensor, Node


def compare_alerts_content(context: TestCase, gt_alerts: List[Alert], new_alerts: List[Alert]):
    """
    Compares two lists of Alert objects.
    :param context:
    :param gt_alerts:
    :param new_alerts:
    """
    if len(new_alerts) != len(gt_alerts):
        context.fail("Wrong number of objects.")

    already_processed = []
    for stored_alert in new_alerts:
        found = False
        for gt_alert in gt_alerts:
            if stored_alert.nodeId == gt_alert.nodeId and stored_alert.alertId == gt_alert.alertId:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_alert in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_alert)

                # Only the content of the object should have changed, not the object itself.
                if stored_alert == gt_alert:
                    context.fail("Changed ground truth object, not content of existing object.")

                if (stored_alert.remoteAlertId != gt_alert.remoteAlertId
                        or stored_alert.description != gt_alert.description
                        or any(map(lambda x: x not in gt_alert.alertLevels, stored_alert.alertLevels))
                        or any(map(lambda x: x not in stored_alert.alertLevels, gt_alert.alertLevels))):

                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Alert object.")


def compare_managers_content(context: TestCase, gt_managers: List[Manager], new_managers: List[Manager]):
    """
    Compares two lists of Manager objects.
    :param context:
    :param gt_managers:
    :param new_managers:
    """
    if len(new_managers) != len(gt_managers):
        context.fail("Wrong number of objects.")

    already_processed = []
    for stored_manager in new_managers:
        found = False
        for gt_manager in gt_managers:
            if stored_manager.nodeId == gt_manager.nodeId and stored_manager.managerId == gt_manager.managerId:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_manager in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_manager)

                # Only the content of the object should have changed, not the object itself.
                if stored_manager == gt_manager:
                    context.fail("Changed ground truth object, not content of existing object.")

                if stored_manager.description != gt_manager.description:
                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Manager object.")


def compare_nodes_content(context: TestCase, gt_nodes: List[Node], new_nodes: List[Node]):
    """
    Compares two lists of Node objects.
    :param context:
    :param gt_nodes:
    :param new_nodes:
    """
    if len(new_nodes) != len(gt_nodes):
        context.fail("Wrong number of objects.")

    already_processed = []
    for stored_node in new_nodes:
        found = False
        for gt_node in gt_nodes:
            if stored_node.nodeId == gt_node.nodeId:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_node in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_node)

                # Only the content of the object should have changed, not the object itself.
                if stored_node == gt_node:
                    context.fail("Changed ground truth object, not content of existing object.")

                if (stored_node.hostname != gt_node.hostname
                        or stored_node.nodeType != gt_node.nodeType
                        or stored_node.instance != gt_node.instance
                        or stored_node.connected != gt_node.connected
                        or stored_node.version != gt_node.version
                        or stored_node.rev != gt_node.rev
                        or stored_node.username != gt_node.username
                        or stored_node.persistent != gt_node.persistent):

                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Node object.")


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
    for stored_option in new_options:
        found = False
        for gt_option in gt_options:
            if stored_option.type == gt_option.type:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_option in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_option)

                # Only the content of the object should have changed, not the object itself.
                if stored_option == gt_option:
                    context.fail("Changed ground truth object, not content of existing object.")

                if stored_option.value != gt_option.value:
                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Option object.")


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
    for stored_sensor in new_sensors:
        found = False
        for gt_sensor in gt_sensors:
            if stored_sensor.nodeId == gt_sensor.nodeId and stored_sensor.sensorId == gt_sensor.sensorId:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_sensor in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_sensor)

                # Only the content of the object should have changed, not the object itself.
                if stored_sensor == gt_sensor:
                    context.fail("Changed ground truth object, not content of existing object.")

                if (stored_sensor.remoteSensorId != gt_sensor.remoteSensorId
                        or stored_sensor.description != gt_sensor.description
                        or stored_sensor.alertDelay != gt_sensor.alertDelay
                        or stored_sensor.lastStateUpdated != gt_sensor.lastStateUpdated
                        or stored_sensor.state != gt_sensor.state
                        or stored_sensor.dataType != gt_sensor.dataType
                        or stored_sensor.data != gt_sensor.data
                        or any(map(lambda x: x not in gt_sensor.alertLevels, stored_sensor.alertLevels))
                        or any(map(lambda x: x not in stored_sensor.alertLevels, gt_sensor.alertLevels))):

                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Sensor object.")
