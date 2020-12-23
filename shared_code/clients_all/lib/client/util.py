#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


import time
import json
import socket
import os
import logging
from typing import List, Dict, Any, Optional
from ..globalData import SensorDataType, SensorObjSensorAlert, SensorObjStateChange


class MsgChecker:

    _log_tag = os.path.basename(__file__)

    @staticmethod
    def check_received_message(message: Dict[str, Any]) -> Optional[str]:

        if "message" not in message.keys() and type(message["message"]) != str:
            logging.error("[%s]: Message not invalid." % MsgChecker._log_tag)
            return "message not valid"

        if "payload" not in message.keys() and type(message["payload"]) != dict:
            logging.error("[%s]: Payload not invalid." % MsgChecker._log_tag)
            return "payload not valid"

        if "type" not in message["payload"].keys() and str(message["payload"]["type"]).lower() != "request":
            logging.error("[%s]: Request expected." % MsgChecker._log_tag)
            return "request expected"

        # Extract the request/message type of the message and check message accordingly.
        request = str(message["message"]).lower()

        # check "PING" message.
        if request == "ping":
            error_msg = None
            if "serverTime" in message.keys():
                error_msg = MsgChecker.check_client_server_time(message["serverTime"])
                if error_msg is not None:
                    logging.error("[%s]: Received serverTime invalid." % MsgChecker._log_tag)
                    return error_msg
            elif "clientTime" in message.keys():
                error_msg = MsgChecker.check_client_server_time(message["clientTime"])
                if error_msg is not None:
                    logging.error("[%s]: Received clientTime invalid." % MsgChecker._log_tag)
                    return error_msg
            else:
                return "clientTime/serverTime expected"

        # Check "SENSORALERT" message.
        elif request == "sensoralert":
            if "serverTime" not in message.keys():
                logging.error("[%s]: serverTime missing." % MsgChecker._log_tag)
                return "serverTime expected"

            error_msg = MsgChecker.check_client_server_time(message["serverTime"])
            if error_msg is not None:
                logging.error("[%s]: Received serverTime invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_alert_levels(message["payload"]["alertLevels"])
            if error_msg is not None:
                logging.error("[%s]: Received alertLevels invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_description(message["payload"]["description"])
            if error_msg is not None:
                logging.error("[%s]: Received description invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_sensor_id(message["payload"]["sensorId"])
            if error_msg is not None:
                logging.error("[%s]: Received sensorId invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_state(message["payload"]["state"])
            if error_msg is not None:
                logging.error("[%s]: Received state invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_has_optional_data(message["payload"]["hasOptionalData"])
            if error_msg is not None:
                logging.error("[%s]: Received hasOptionalData invalid." % MsgChecker._log_tag)
                return error_msg

            if message["payload"]["hasOptionalData"]:
                error_msg = MsgChecker.check_optional_data(message["payload"]["optionalData"])
                if error_msg is not None:
                    logging.error("[%s]: Received optionalData invalid." % MsgChecker._log_tag)
                    return error_msg

            error_msg = MsgChecker.check_sensor_data_type(message["payload"]["dataType"])
            if error_msg is not None:
                logging.error("[%s]: Received dataType invalid." % MsgChecker._log_tag)
                return error_msg

            if message["payload"]["dataType"] != SensorDataType.NONE:
                error_msg = MsgChecker.check_sensor_data(message["payload"]["data"],
                                                         message["payload"]["dataType"])
                if error_msg is not None:
                    logging.error("[%s]: Received data invalid." % MsgChecker._log_tag)
                    return error_msg

            error_msg = MsgChecker.check_has_latest_data(message["payload"]["hasLatestData"])
            if error_msg is not None:
                logging.error("[%s]: Received hasLatestData invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_change_state(message["payload"]["changeState"])
            if error_msg is not None:
                logging.error("[%s]: Received changeState invalid." % MsgChecker._log_tag)
                return error_msg

        # Check "STATECHANGE" message.
        elif request == "statechange":
            if "serverTime" not in message.keys():
                logging.error("[%s]: serverTime missing." % MsgChecker._log_tag)
                return "serverTime expected"

            error_msg = MsgChecker.check_client_server_time(message["serverTime"])
            if error_msg is not None:
                logging.error("[%s]: Received serverTime invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_sensor_id(message["payload"]["sensorId"])
            if error_msg is not None:
                logging.error("[%s]: Received sensorId invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_state(message["payload"]["state"])
            if error_msg is not None:
                logging.error("[%s]: Received state invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_sensor_data_type(message["payload"]["dataType"])
            if error_msg is not None:
                logging.error("[%s]: Received dataType invalid." % MsgChecker._log_tag)
                return error_msg

            if message["payload"]["dataType"] != SensorDataType.NONE:
                error_msg = MsgChecker.check_sensor_data(message["payload"]["data"],
                                                         message["payload"]["dataType"])
                if error_msg is not None:
                    logging.error("[%s]: Received data invalid." % MsgChecker._log_tag)
                    return error_msg

        # Check "STATUS" message.
        elif request == "status":
            if "serverTime" not in message.keys():
                logging.error("[%s]: serverTime missing." % MsgChecker._log_tag)
                return "serverTime expected"

            error_msg = MsgChecker.check_client_server_time(message["serverTime"])
            if error_msg is not None:
                logging.error("[%s]: Received serverTime invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_status_options_list(message["payload"]["options"])
            if error_msg is not None:
                logging.error("[%s]: Received options invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_status_nodes_list(message["payload"]["nodes"])
            if error_msg is not None:
                logging.error("[%s]: Received nodes invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_status_sensors_list(message["payload"]["sensors"])
            if error_msg is not None:
                logging.error("[%s]: Received sensors invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_status_managers_list(message["payload"]["managers"])
            if error_msg is not None:
                logging.error("[%s]: Received managers invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_status_alerts_list(message["payload"]["alerts"])
            if error_msg is not None:
                logging.error("[%s]: Received alerts invalid." % MsgChecker._log_tag)
                return error_msg

            error_msg = MsgChecker.check_status_alert_levels_list(message["payload"]["alertLevels"])
            if error_msg is not None:
                logging.error("[%s]: Received alertLevels invalid." % MsgChecker._log_tag)
                return error_msg

        else:
            logging.error("[%s]: Unknown request/message type." % MsgChecker._log_tag)
            return "unknown request/message type"

        return None

    # Internal function to check sanity of the alertDelay.
    @staticmethod
    def check_alert_delay(alertDelay: int) -> Optional[str]:

        is_correct = True
        if not isinstance(alertDelay, int):
            is_correct = False

        if not is_correct:
            return "alertDelay not valid"

        return None

    # Internal function to check sanity of the alertId.
    @staticmethod
    def check_alert_id(alertId: int) -> Optional[str]:

        is_correct = True
        if not isinstance(alertId, int):
            is_correct = False

        if not is_correct:
            return "alertId not valid"

        return None

    # Internal function to check sanity of the alertLevel.
    @staticmethod
    def check_alert_level(alertLevel: int):

        is_correct = True
        if not isinstance(alertLevel, int):
            is_correct = False

        if not is_correct:
            return "alertLevel not valid"

        return None

    # Internal function to check sanity of the alertLevels.
    @staticmethod
    def check_alert_levels(alertLevels: List[int]) -> Optional[str]:

        is_correct = True
        if not isinstance(alertLevels, list):
            is_correct = False
        elif not all(isinstance(item, int) for item in alertLevels):
            is_correct = False

        if not is_correct:
            return "alertLevels not valid"

        return None

    # Internal function to check sanity of the changeState.
    @staticmethod
    def check_change_state(changeState: bool) -> Optional[str]:

        is_correct = True
        if not isinstance(changeState, bool):
            is_correct = False

        if not is_correct:
            return "changeState not valid"

        return None

    # Internal function to check sanity of the connected.
    @staticmethod
    def check_connected(connected: int):

        is_correct = True
        if not isinstance(connected, int):
            is_correct = False
        elif connected != 0 and connected != 1:
            is_correct = False

        if not is_correct:
            return "connected not valid"

        return None

    # Internal function to check sanity of the description.
    @staticmethod
    def check_description(description: str) -> Optional[str]:

        is_correct = True
        if not isinstance(description, str):
            is_correct = False

        if not is_correct:
            return "description not valid"

        return None

    # Internal function to check sanity of the hasLatestData.
    @staticmethod
    def check_has_latest_data(hasLatestData: bool) -> Optional[str]:

        is_correct = True
        if not isinstance(hasLatestData, bool):
            is_correct = False

        if not is_correct:
            return "hasLatestData not valid"

        return None

    # Internal function to check sanity of the hasOptionalData.
    @staticmethod
    def check_has_optional_data(hasOptionalData: bool) -> Optional[str]:

        is_correct = True
        if not isinstance(hasOptionalData, bool):
            is_correct = False

        if not is_correct:
            return "hasOptionalData not valid"

        return None

    # Internal function to check sanity of the hostname.
    @staticmethod
    def check_hostname(hostname: str) -> Optional[str]:

        is_correct = True
        if not isinstance(hostname, str):
            is_correct = False

        if not is_correct:
            return "hostname not valid"

        return None

    # Internal function to check sanity of the instance.
    @staticmethod
    def check_instance(instance: str) -> Optional[str]:

        is_correct = True
        if not isinstance(instance, str):
            is_correct = False

        if not is_correct:
            return "instance not valid"

        return None

    # Internal function to check sanity of the instrumentation_active.
    @staticmethod
    def check_instrumentation_active(instrumentation_active: bool) -> Optional[str]:

        is_correct = True
        if not isinstance(instrumentation_active, bool):
            is_correct = False

        if not is_correct:
            return "instrumentation_active not valid"

        return None

    # Internal function to check sanity of the instrumentation_cmd.
    @staticmethod
    def check_instrumentation_cmd(instrumentation_cmd: str) -> Optional[str]:

        is_correct = True
        if not isinstance(instrumentation_cmd, str):
            is_correct = False

        if not is_correct:
            return "instrumentation_cmd not valid"

        return None

    # Internal function to check sanity of the instrumentation_timeout.
    @staticmethod
    def check_instrumentation_timeout(instrumentation_timeout: int) -> Optional[str]:

        is_correct = True
        if not isinstance(instrumentation_timeout, int):
            is_correct = False

        if not is_correct:
            return "instrumentation_timeout not valid"

        return None

    # Internal function to check sanity of the lastStateUpdated.
    @staticmethod
    def check_last_state_updated(lastStateUpdated: int) -> Optional[str]:

        is_correct = True
        if not isinstance(lastStateUpdated, int):
            is_correct = False

        if not is_correct:
            return "lastStateUpdated not valid"

        return None

    # Internal function to check sanity of the managerId.
    @staticmethod
    def check_manager_id(managerId: int) -> Optional[str]:

        is_correct = True
        if not isinstance(managerId, int):
            is_correct = False

        if not is_correct:
            return "managerId not valid"

        return None

    # Internal function to check sanity of the name.
    @staticmethod
    def check_name(name: str) -> Optional[str]:

        is_correct = True
        if not isinstance(name, str):
            is_correct = False

        if not is_correct:
            return "name not valid"

        return None

    # Internal function to check sanity of the nodeId.
    @staticmethod
    def check_node_id(nodeId: int) -> Optional[str]:

        is_correct = True
        if not isinstance(nodeId, int):
            is_correct = False

        if not is_correct:
            return "nodeId not valid"

        return None

    # Internal function to check sanity of the nodeType.
    @staticmethod
    def check_node_type(nodeType: str) -> Optional[str]:

        is_correct = True
        if not isinstance(nodeType, str):
            is_correct = False

        nodeTypes = {"alert", "manager", "sensor", "server"}
        if nodeType not in nodeTypes:
            is_correct = False

        if not is_correct:
            return "nodeType not valid"

        return None

    # Internal function to check sanity of the optionalData.
    @staticmethod
    def check_optional_data(optionalData: Dict[str, Any]) -> Optional[str]:

        is_correct = True
        if not isinstance(optionalData, dict):
            is_correct = False
        if "message" in optionalData.keys():
            if MsgChecker.check_optional_data_message(optionalData["message"]) is not None:
                is_correct = False

        if not is_correct:
            return "optionalData not valid"

        return None

    # Internal function to check sanity of the optionalData message.
    @staticmethod
    def check_optional_data_message(message: str) -> Optional[str]:

        is_correct = True
        if not isinstance(message, str):
            is_correct = False

        if not is_correct:
            return "optionalData message not valid"

        return None

    # Internal function to check sanity of the optionType.
    @staticmethod
    def check_option_type(optionType: str) -> Optional[str]:

        is_correct = True
        if not isinstance(optionType, str):
            is_correct = False

        if optionType != "alertSystemActive":
            is_correct = False

        if not is_correct:
            return "optionType not valid"

        return None

    # Internal function to check sanity of the option value.
    @staticmethod
    def check_option_value(value: float) -> Optional[str]:

        is_correct = True
        if not isinstance(value, float):
            is_correct = False

        if not 0.0 <= value <= 1.0:
            is_correct = False

        if not is_correct:
            return "value not valid"

        return None

    # Internal function to check sanity of the persistent.
    @staticmethod
    def check_persistent(persistent: int) -> Optional[str]:

        is_correct = True
        if not isinstance(persistent, int):
            is_correct = False
        elif persistent != 0 and persistent != 1:
            is_correct = False

        if not is_correct:
            return "persistent not valid"

        return None

    # Internal function to check sanity of the remoteAlertId.
    @staticmethod
    def check_remote_alert_id(remoteAlertId: int) -> Optional[str]:

        is_correct = True
        if not isinstance(remoteAlertId, int):
            is_correct = False

        if not is_correct:
            return "remoteAlertId not valid"

        return None

    # Internal function to check sanity of the remoteSensorId.
    @staticmethod
    def check_remote_sensor_id(remoteSensorId: int) -> Optional[str]:

        is_correct = True
        if not isinstance(remoteSensorId, int):
            is_correct = False

        if not is_correct:
            return "remoteSensorId not valid"

        return None

    # Internal function to check sanity of the rev.
    @staticmethod
    def check_rev(rev: int) -> Optional[str]:

        is_correct = True
        if not isinstance(rev, int):
            is_correct = False

        if not is_correct:
            return "rev not valid"

        return None

    # Internal function to check sanity of the sensor data.
    @staticmethod
    def check_sensor_data(data: Any, dataType: int) -> Optional[str]:

        is_correct = True
        if dataType == SensorDataType.NONE and data is not None:
            is_correct = False
        elif dataType == SensorDataType.INT and not isinstance(data, int):
            is_correct = False
        elif dataType == SensorDataType.FLOAT and not isinstance(data, float):
            is_correct = False

        if not is_correct:
            return "data not valid"

        return None

    # Internal function to check sanity of the sensor data type.
    @staticmethod
    def check_sensor_data_type(dataType: int) -> Optional[str]:

        is_correct = True
        if not isinstance(dataType, int):
            is_correct = False
        elif not (SensorDataType.NONE == dataType
                  or SensorDataType.INT == dataType
                  or SensorDataType.FLOAT == dataType):
            is_correct = False

        if not is_correct:
            return "dataType not valid"

        return None

    # Internal function to check sanity of the sensorId.
    @staticmethod
    def check_sensor_id(sensorId: int) -> Optional[str]:

        is_correct = True
        if not isinstance(sensorId, int):
            is_correct = False

        if not is_correct:
            return "sensorId not valid"

        return None

    # Internal function to check sanity of the serverTime.
    @staticmethod
    def check_client_server_time(client_server_time: int) -> Optional[str]:

        is_correct = True
        if not isinstance(client_server_time, int):
            is_correct = False

        if not is_correct:
            return "clientTime/serverTime not valid"

        return None

    # Internal function to check sanity of the state.
    @staticmethod
    def check_state(state: int) -> Optional[str]:

        is_correct = True
        if not isinstance(state, int):
            is_correct = False
        elif state != 0 and state != 1:
            is_correct = False

        if not is_correct:
            return "state not valid"

        return None

    # Internal function to check sanity of the status alertLevels list.
    @staticmethod
    def check_status_alert_levels_list(alertLevels: List[Dict[str, Any]]) -> Optional[str]:

        is_correct = True
        if not isinstance(alertLevels, list):
            is_correct = False

        alert_level_ids = set()

        # Check each alertLevel if correct.
        for alertLevel in alertLevels:

            if not isinstance(alertLevel, dict):
                is_correct = False
                break

            if "alertLevel" not in alertLevel.keys():
                is_correct = False
                break

            elif MsgChecker.check_alert_level(alertLevel["alertLevel"]) is not None:
                is_correct = False
                break

            if "name" not in alertLevel.keys():
                is_correct = False
                break

            elif MsgChecker.check_name(alertLevel["name"]) is not None:
                is_correct = False
                break

            if "triggerAlways" not in alertLevel.keys():
                is_correct = False
                break

            elif MsgChecker.check_trigger_always(alertLevel["triggerAlways"]) is not None:
                is_correct = False
                break

            if "instrumentation_active" not in alertLevel.keys():
                is_correct = False
                break

            elif MsgChecker.check_instrumentation_active(alertLevel["instrumentation_active"]) is not None:
                is_correct = False
                break

            if alertLevel["instrumentation_active"]:
                if "instrumentation_cmd" not in alertLevel.keys():
                    is_correct = False
                    break

                elif MsgChecker.check_instrumentation_cmd(alertLevel["instrumentation_cmd"]) is not None:
                    is_correct = False
                    break

                if "instrumentation_timeout" not in alertLevel.keys():
                    is_correct = False
                    break

                elif MsgChecker.check_instrumentation_timeout(alertLevel["instrumentation_timeout"]) is not None:
                    is_correct = False
                    break

            if alertLevel["alertLevel"] in alert_level_ids:
                is_correct = False
                break
            alert_level_ids.add(alertLevel["alertLevel"])

        if not is_correct:
            return "alertLevels list not valid"

        return None

    # Internal function to check sanity of the status alerts list.
    @staticmethod
    def check_status_alerts_list(alerts: List[Dict[str, Any]]) -> Optional[str]:

        is_correct = True
        if not isinstance(alerts, list):
            is_correct = False

        alert_ids = set()

        # Check each alert if correct.
        for alert in alerts:

            if not isinstance(alert, dict):
                is_correct = False
                break

            if "nodeId" not in alert.keys():
                is_correct = False
                break

            elif MsgChecker.check_node_id(alert["nodeId"]) is not None:
                is_correct = False
                break

            if "alertId" not in alert.keys():
                is_correct = False
                break

            elif MsgChecker.check_alert_id(alert["alertId"]) is not None:
                is_correct = False
                break

            if "description" not in alert.keys():
                is_correct = False
                break

            elif MsgChecker.check_description(alert["description"]) is not None:
                is_correct = False
                break

            if "alertLevels" not in alert.keys():
                is_correct = False
                break

            elif MsgChecker.check_alert_levels(alert["alertLevels"]) is not None:
                is_correct = False
                break

            if "remoteAlertId" not in alert.keys():
                is_correct = False
                break

            elif MsgChecker.check_remote_alert_id(alert["remoteAlertId"]) is not None:
                is_correct = False
                break

            if alert["alertId"] in alert_ids:
                is_correct = False
                break
            alert_ids.add(alert["alertId"])

        if not is_correct:
            return "alerts list not valid"

        return None

    # Internal function to check sanity of the status managers list.
    @staticmethod
    def check_status_managers_list(managers: List[Dict[str, Any]]) -> Optional[str]:

        is_correct = True
        if not isinstance(managers, list):
            is_correct = False

        manager_ids = set()

        # Check each manager if correct.
        for manager in managers:

            if not isinstance(manager, dict):
                is_correct = False
                break

            if "nodeId" not in manager.keys():
                is_correct = False
                break

            elif MsgChecker.check_node_id(manager["nodeId"]) is not None:
                is_correct = False
                break

            if "managerId" not in manager.keys():
                is_correct = False
                break

            elif MsgChecker.check_manager_id(manager["managerId"]) is not None:
                is_correct = False
                break

            if "description" not in manager.keys():
                is_correct = False
                break

            elif MsgChecker.check_description(manager["description"]) is not None:
                is_correct = False
                break

            if manager["managerId"] in manager_ids:
                is_correct = False
                break
            manager_ids.add(manager["managerId"])

        if not is_correct:
            return "managers list not valid"

        return None

    # Internal function to check sanity of the status nodes list.
    @staticmethod
    def check_status_nodes_list(nodes: List[Dict[str, Any]]) -> Optional[str]:

        is_correct = True
        if not isinstance(nodes, list):
            is_correct = False

        node_ids = set()

        # Check each option if correct.
        for node in nodes:

            if not isinstance(node, dict):
                is_correct = False
                break

            if "nodeId" not in node.keys():
                is_correct = False
                break

            elif MsgChecker.check_node_id(node["nodeId"]) is not None:
                is_correct = False
                break

            if "hostname" not in node.keys():
                is_correct = False
                break

            elif MsgChecker.check_hostname(node["hostname"]) is not None:
                is_correct = False
                break

            if "nodeType" not in node.keys():
                is_correct = False
                break

            elif MsgChecker.check_node_type(node["nodeType"]) is not None:
                is_correct = False
                break

            if "instance" not in node.keys():
                is_correct = False
                break

            elif MsgChecker.check_instance(node["instance"]) is not None:
                is_correct = False
                break

            if "connected" not in node.keys():
                is_correct = False
                break

            elif MsgChecker.check_connected(node["connected"]) is not None:
                is_correct = False
                break

            if "version" not in node.keys():
                is_correct = False
                break

            elif MsgChecker.check_version(node["version"]) is not None:
                is_correct = False
                break

            if "rev" not in node.keys():
                is_correct = False
                break

            elif MsgChecker.check_rev(node["rev"]) is not None:
                is_correct = False
                break

            if "username" not in node.keys():
                is_correct = False
                break

            elif MsgChecker.check_username(node["username"]) is not None:
                is_correct = False
                break

            if "persistent" not in node.keys():
                is_correct = False
                break

            elif MsgChecker.check_persistent(node["persistent"]) is not None:
                is_correct = False
                break

            if node["nodeId"] in node_ids:
                is_correct = False
                break
            node_ids.add(node["nodeId"])

        if not is_correct:
            return "nodes list not valid"

        return None

    # Internal function to check sanity of the status options list.
    @staticmethod
    def check_status_options_list(options: List[Dict[str, Any]]) -> Optional[str]:

        is_correct = True
        if not isinstance(options, list):
            is_correct = False

        # Check each option if correct.
        for option in options:

            if not isinstance(option, dict):
                is_correct = False
                break

            if "type" not in option.keys():
                is_correct = False
                break

            elif MsgChecker.check_option_type(option["type"]) is not None:
                is_correct = False
                break

            if "value" not in option.keys():
                is_correct = False
                break

            elif MsgChecker.check_option_value(option["value"]) is not None:
                is_correct = False
                break

        if not is_correct:
            return "options list not valid"

        return None

    # Internal function to check sanity of the status sensors list.
    @staticmethod
    def check_status_sensors_list(sensors: List[Dict[str, Any]]) -> Optional[str]:

        is_correct = True
        if not isinstance(sensors, list):
            is_correct = False

        sensor_ids = set()

        # Check each sensor if correct.
        for sensor in sensors:

            if not isinstance(sensor, dict):
                is_correct = False
                break

            if "nodeId" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_node_id(sensor["nodeId"]) is not None:
                is_correct = False
                break

            if "sensorId" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_sensor_id(sensor["sensorId"]) is not None:
                is_correct = False
                break

            if "alertDelay" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_alert_delay(sensor["alertDelay"]) is not None:
                is_correct = False
                break

            if "alertLevels" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_alert_levels(sensor["alertLevels"]) is not None:
                is_correct = False
                break

            if "description" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_description(sensor["description"]) is not None:
                is_correct = False
                break

            if "lastStateUpdated" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_last_state_updated(sensor["lastStateUpdated"]) is not None:
                is_correct = False
                break

            if "state" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_state(sensor["state"]):
                is_correct = False
                break

            if "remoteSensorId" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_remote_sensor_id(sensor["remoteSensorId"]) is not None:
                is_correct = False
                break

            if "dataType" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_sensor_data_type(sensor["dataType"]) is not None:
                is_correct = False
                break

            if sensor["dataType"] != SensorDataType.NONE:
                if "data" not in sensor.keys():
                    is_correct = False
                    break

                elif MsgChecker.check_sensor_data(sensor["data"], sensor["dataType"]) is not None:
                    is_correct = False
                    break

            if sensor["sensorId"] in sensor_ids:
                is_correct = False
                break
            sensor_ids.add(sensor["sensorId"])

        if not is_correct:
            return "sensors list not valid"

        return None

    # Internal function to check sanity of the triggerAlways.
    @staticmethod
    def check_trigger_always(triggerAlways: int) -> Optional[str]:

        is_correct = True
        if not isinstance(triggerAlways, int):
            is_correct = False
        elif triggerAlways != 0 and triggerAlways != 1:
            is_correct = False

        if not is_correct:
            return "triggerAlways not valid"

        return None

    # Internal function to check sanity of the username.
    @staticmethod
    def check_username(username: str) -> Optional[str]:

        is_correct = True
        if not isinstance(username, str):
            is_correct = False

        if not is_correct:
            return "username not valid"

        return None

    # Internal function to check sanity of the version.
    @staticmethod
    def check_version(version: float) -> Optional[str]:

        is_correct = True
        if not isinstance(version, float):
            is_correct = False

        if not is_correct:
            return "version not valid"

        return None


class MsgBuilder:

    @staticmethod
    def build_auth_msg(username: str,
                       password: str,
                       version: float,
                       rev: int,
                       regMessageSize: int) -> str:
        """
        Internal function that builds the client authentication message.

        :param username:
        :param password:
        :param version:
        :param rev:
        :param regMessageSize:
        :return:
        """
        payload = {"type": "request",
                   "version": version,
                   "rev": rev,
                   "username": username,
                   "password": password}
        utc_timestamp = int(time.time())
        message = {"clientTime": utc_timestamp,
                   "size": regMessageSize,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_option_msg_manager(optionType: str,
                                 optionValue: float,
                                 optionDelay: int) -> str:
        """
        Internal function that builds the option message for manager nodes.

        :param optionType:
        :param optionValue:
        :param optionDelay:
        :return:
        """
        payload = {"type": "request",
                   "optionType": optionType,
                   "value": float(optionValue),
                   "timeDelay": optionDelay}
        utc_timestamp = int(time.time())
        message = {"clientTime": utc_timestamp,
                   "message": "option",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_ping_msg() -> str:
        """
        Internal function that builds the ping message.

        :return:
        """
        payload = {"type": "request"}
        utc_timestamp = int(time.time())
        message = {"clientTime": utc_timestamp,
                   "message": "ping",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_reg_msg_manager(description: str,
                              node_type: str,
                              instance: str,
                              persistent: int) -> str:
        """
        Internal function that builds the client registration message for manager nodes.

        :param description:
        :param node_type:
        :param instance:
        :param persistent:
        :return:
        """
        # build manager dict for the message
        manager = dict()
        manager["description"] = description

        payload = {"type": "request",
                   "hostname": socket.gethostname(),
                   "nodeType": node_type,
                   "instance": instance,
                   "persistent": persistent,
                   "manager": manager}

        utc_timestamp = int(time.time())
        message = {"clientTime": utc_timestamp,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_reg_msg_sensor(polling_sensors,
                             node_type: str,
                             instance: str,
                             persistent: int) -> str:
        """
        Internal function that builds the client registration message for sensor nodes.

        :param polling_sensors:
        :param node_type:
        :param instance:
        :param persistent:
        :return:
        """
        # build sensors list for the message
        msg_sensors = list()
        for sensor in polling_sensors:
            tempSensor = dict()
            tempSensor["clientSensorId"] = sensor.id
            tempSensor["alertDelay"] = sensor.alertDelay
            tempSensor["alertLevels"] = sensor.alertLevels
            tempSensor["description"] = sensor.description
            tempSensor["state"] = sensor.state

            # Only add data field if sensor data type is not "none".
            tempSensor["dataType"] = sensor.sensorDataType
            if sensor.sensorDataType != SensorDataType.NONE:
                tempSensor["data"] = sensor.sensorData

            msg_sensors.append(tempSensor)

        payload = {"type": "request",
                   "hostname": socket.gethostname(),
                   "nodeType": node_type,
                   "instance": instance,
                   "persistent": persistent,
                   "sensors": msg_sensors}

        utc_timestamp = int(time.time())
        message = {"clientTime": utc_timestamp,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_sensor_alert_msg_sensor(sensor_alert: SensorObjSensorAlert) -> str:
        """
        Internal function that builds a sensor alert message for sensor nodes.

        :param sensor_alert:
        """

        payload = {"type": "request",
                   "clientSensorId": sensor_alert.clientSensorId,
                   "state": sensor_alert.state,
                   "hasOptionalData": sensor_alert.hasOptionalData,
                   "changeState": sensor_alert.changeState,
                   "hasLatestData": sensor_alert.hasLatestData,
                   "dataType": sensor_alert.dataType}

        # Only add optional data field if it should be transfered.
        if sensor_alert.hasOptionalData:
            payload["optionalData"] = sensor_alert.optionalData

        # Only add data field if sensor data type is not "none".
        if sensor_alert.dataType != SensorDataType.NONE:
            payload["data"] = sensor_alert.sensorData

        utc_timestamp = int(time.time())
        message = {"clientTime": utc_timestamp,
                   "message": "sensoralert",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_state_change_msg_sensor(state_change: SensorObjStateChange) -> str:
        """
        Internal function that builds a state change message for sensor nodes.

        :param state_change:
        """

        payload = {"type": "request",
                   "clientSensorId": state_change.clientSensorId,
                   "state": state_change.state,
                   "dataType": state_change.dataType}

        # Only add data field if sensor data type is not "none".
        if state_change.dataType != SensorDataType.NONE:
            payload["data"] = state_change.sensorData

        utc_timestamp = int(time.time())
        message = {"clientTime": utc_timestamp,
                   "message": "statechange",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_status_update_msg_sensor(polling_sensors) -> str:
        """
        Internal function that builds a sensor alert message for sensor nodes.

        :param polling_sensors:
        """
        # build sensors list for the message
        sensors = list()
        for sensor in polling_sensors:
            temp_sensor = dict()
            temp_sensor["clientSensorId"] = sensor.id

            # convert the internal trigger state to the state
            # convention of the alert system (1 = trigger, 0 = normal)
            if sensor.triggerState == sensor.state:
                temp_sensor["state"] = 1
            else:
                temp_sensor["state"] = 0

            # Only add data field if sensor data type is not "none".
            temp_sensor["dataType"] = sensor.sensorDataType
            if sensor.sensorDataType != SensorDataType.NONE:
                temp_sensor["data"] = sensor.sensorData

            sensors.append(temp_sensor)

        payload = {"type": "request", "sensors": sensors}
        utc_timestamp = int(time.time())
        message = {"clientTime": utc_timestamp,
                   "message": "status",
                   "payload": payload}
        return json.dumps(message)
