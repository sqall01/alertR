from unittest import TestCase
from typing import List
from lib.globalData.managerObjects import ManagerObjOption, ManagerObjAlert, ManagerObjManager, ManagerObjSensor, \
    ManagerObjNode, ManagerObjAlertLevel, ManagerObjSensorAlert, ManagerObjProfile


def compare_alert_levels_content(context: TestCase, gt_alert_levels: List[ManagerObjAlertLevel], new_alert_levels: List[ManagerObjAlertLevel]):
    """
    Compares two lists of AlertLevel objects.
    :param context:
    :param gt_alert_levels:
    :param new_alert_levels:
    """
    if len(new_alert_levels) != len(gt_alert_levels):
        context.fail("Wrong number of objects.")

    already_processed = []
    for stored_alert_level in new_alert_levels:
        found = False
        for gt_alert_level in gt_alert_levels:
            if stored_alert_level.level == gt_alert_level.level:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_alert_level in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_alert_level)

                # Only the content of the object should have changed, not the object itself.
                if stored_alert_level == gt_alert_level:
                    context.fail("Changed ground truth object, not content of existing object.")

                if (stored_alert_level.name != gt_alert_level.name
                        or any(map(lambda x: x not in gt_alert_level.profiles, stored_alert_level.profiles))
                        or any(map(lambda x: x not in stored_alert_level.profiles, gt_alert_level.profiles))
                        or stored_alert_level.instrumentation_active != gt_alert_level.instrumentation_active
                        or stored_alert_level.instrumentation_cmd != gt_alert_level.instrumentation_cmd
                        or stored_alert_level.instrumentation_timeout != gt_alert_level.instrumentation_timeout):
                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Alert Level object.")


def compare_alerts_content(context: TestCase, gt_alerts: List[ManagerObjAlert], new_alerts: List[ManagerObjAlert]):
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

                if (stored_alert.clientAlertId != gt_alert.clientAlertId
                        or stored_alert.description != gt_alert.description
                        or any(map(lambda x: x not in gt_alert.alertLevels, stored_alert.alertLevels))
                        or any(map(lambda x: x not in stored_alert.alertLevels, gt_alert.alertLevels))):

                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Alert object.")


def compare_managers_content(context: TestCase, gt_managers: List[ManagerObjManager], new_managers: List[ManagerObjManager]):
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


def compare_nodes_content(context: TestCase, gt_nodes: List[ManagerObjNode], new_nodes: List[ManagerObjNode]):
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


def compare_options_content(context: TestCase, gt_options: List[ManagerObjOption], new_options: List[ManagerObjOption]):
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


def compare_profiles_content(context: TestCase, gt_profiles: List[ManagerObjProfile], new_profiles: List[ManagerObjProfile]):
    """
    Compares two lists of Profile objects.
    :param context:
    :param gt_profiles:
    :param new_profiles:
    """
    if len(new_profiles) != len(gt_profiles):
        context.fail("Wrong number of objects.")

    already_processed = []
    for stored_profile in new_profiles:
        found = False
        for gt_profile in gt_profiles:
            if stored_profile.profileId == gt_profile.profileId:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_profile in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_profile)

                # Only the content of the object should have changed, not the object itself.
                if stored_profile == gt_profile:
                    context.fail("Changed ground truth object, not content of existing object.")

                if stored_profile.name != gt_profile.name:
                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Profile object.")


def compare_sensor_alerts_content(context: TestCase,
                                  gt_sensor_alerts: List[ManagerObjSensorAlert],
                                  new_sensor_alerts: List[ManagerObjSensorAlert]):
    """
    Compares two lists of Sensor Alert objects.
    :param context:
    :param gt_sensor_alerts:
    :param new_sensor_alerts:
    """
    if len(gt_sensor_alerts) != len(new_sensor_alerts):
        context.fail("Wrong number of objects.")

    for new_sensor_alert in new_sensor_alerts:
        found = False
        for gt_sensor_alert in gt_sensor_alerts:

            if (new_sensor_alert.sensorId == gt_sensor_alert.sensorId
                    and new_sensor_alert.state == gt_sensor_alert.state
                    and new_sensor_alert.description == gt_sensor_alert.description
                    and new_sensor_alert.timeReceived == gt_sensor_alert.timeReceived
                    and new_sensor_alert.hasOptionalData == gt_sensor_alert.hasOptionalData
                    and new_sensor_alert.changeState == gt_sensor_alert.changeState
                    and new_sensor_alert.hasLatestData == gt_sensor_alert.hasLatestData
                    and new_sensor_alert.dataType == gt_sensor_alert.dataType
                    and new_sensor_alert.data == gt_sensor_alert.data
                    and any(map(lambda x: x in gt_sensor_alert.alertLevels, new_sensor_alert.alertLevels))
                    and any(map(lambda x: x in new_sensor_alert.alertLevels, gt_sensor_alert.alertLevels))):

                found = True
                break

        if not found:
            context.fail("Lists of Sensor Alert objects do not have the same content.")


def compare_sensors_content(context: TestCase, gt_sensors: List[ManagerObjSensor], new_sensors: List[ManagerObjSensor]):
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

                if (stored_sensor.clientSensorId != gt_sensor.clientSensorId
                        or stored_sensor.description != gt_sensor.description
                        or stored_sensor.alertDelay != gt_sensor.alertDelay
                        or stored_sensor.lastStateUpdated != gt_sensor.lastStateUpdated
                        or stored_sensor.state != gt_sensor.state
                        or stored_sensor.dataType != gt_sensor.dataType
                        or stored_sensor.data != gt_sensor.data
                        or stored_sensor.error_state != gt_sensor.error_state
                        or any(map(lambda x: x not in gt_sensor.alertLevels, stored_sensor.alertLevels))
                        or any(map(lambda x: x not in stored_sensor.alertLevels, gt_sensor.alertLevels))):

                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Sensor object.")
