#!/usr/bin/python3

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
from ..localObjects import SensorDataType


class MsgChecker:

    _log_tag = os.path.basename(__file__)

    @staticmethod
    def check_received_message(message: Dict[str, Any]) -> Optional[str]:

        if "message" not in message.keys() and type(message["message"]) != str:
            return "message not valid"

        if "payload" not in message.keys() and type(message["payload"]) != dict:
            return "payload not valid"

        if "type" not in message["payload"].keys() and str(message["payload"]["type"]).lower() != "request":
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
            if "serverTime" in message.keys():
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

            error_msg = MsgChecker.check_rules_activated(message["payload"]["rulesActivated"])
            if error_msg is not None:
                logging.error("[%s]: Received rulesActivated invalid." % MsgChecker._log_tag)
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
            if "serverTime" in message.keys():
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
            if "serverTime" in message.keys():
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
            return "unknown request/message type"

        return None

    # Internal function to check sanity of the alertDelay.
    @staticmethod
    def check_alert_delay(alertDelay: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(alertDelay, int):
            isCorrect = False

        if not isCorrect:
            return "alertDelay not valid"

        return None

    # Internal function to check sanity of the alertId.
    @staticmethod
    def check_alert_id(alertId: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(alertId, int):
            isCorrect = False

        if not isCorrect:
            return "alertId not valid"

        return None

    # Internal function to check sanity of the alertLevel.
    @staticmethod
    def check_alert_level(alertLevel: int):

        isCorrect = True
        if not isinstance(alertLevel, int):
            isCorrect = False

        if not isCorrect:
            return "alertLevel not valid"

        return None

    # Internal function to check sanity of the alertLevels.
    @staticmethod
    def check_alert_levels(alertLevels: List[int]) -> Optional[str]:

        isCorrect = True
        if not isinstance(alertLevels, list):
            isCorrect = False
        elif not all(isinstance(item, int) for item in alertLevels):
            isCorrect = False

        if not isCorrect:
            return "alertLevels not valid"

        return None

    # Internal function to check sanity of the changeState.
    @staticmethod
    def check_change_state(changeState: bool) -> Optional[str]:

        isCorrect = True
        if not isinstance(changeState, bool):
            isCorrect = False

        if not isCorrect:
            return "changeState not valid"

        return None

    # Internal function to check sanity of the connected.
    @staticmethod
    def check_connected(connected: int):

        isCorrect = True
        if not isinstance(connected, int):
            isCorrect = False
        elif connected != 0 and connected != 1:
            isCorrect = False

        if not isCorrect:
            return "connected not valid"

        return None

    # Internal function to check sanity of the description.
    @staticmethod
    def check_description(description: str) -> Optional[str]:

        isCorrect = True
        if not isinstance(description, str):
            isCorrect = False

        if not isCorrect:
            return "description not valid"

        return None

    # Internal function to check sanity of the hasLatestData.
    @staticmethod
    def check_has_latest_data(hasLatestData: bool) -> Optional[str]:

        isCorrect = True
        if not isinstance(hasLatestData, bool):
            isCorrect = False

        if not isCorrect:
            return "hasLatestData not valid"

        return None

    # Internal function to check sanity of the hasOptionalData.
    @staticmethod
    def check_has_optional_data(hasOptionalData: bool) -> Optional[str]:

        isCorrect = True
        if not isinstance(hasOptionalData, bool):
            isCorrect = False

        if not isCorrect:
            return "hasOptionalData not valid"

        return None

    # Internal function to check sanity of the hostname.
    @staticmethod
    def check_hostname(hostname: str) -> Optional[str]:

        isCorrect = True
        if not isinstance(hostname, str):
            isCorrect = False

        if not isCorrect:
            return "hostname not valid"

        return None

    # Internal function to check sanity of the instance.
    @staticmethod
    def check_instance(instance: str) -> Optional[str]:

        isCorrect = True
        if not isinstance(instance, str):
            isCorrect = False

        if not isCorrect:
            return "instance not valid"

        return None

    # Internal function to check sanity of the lastStateUpdated.
    @staticmethod
    def check_last_state_updated(lastStateUpdated: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(lastStateUpdated, int):
            isCorrect = False

        if not isCorrect:
            return "lastStateUpdated not valid"

        return None

    # Internal function to check sanity of the managerId.
    @staticmethod
    def check_manager_id(managerId: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(managerId, int):
            isCorrect = False

        if not isCorrect:
            return "managerId not valid"

        return None

    # Internal function to check sanity of the name.
    @staticmethod
    def check_name(name: str) -> Optional[str]:

        isCorrect = True
        if not isinstance(name, str):
            isCorrect = False

        if not isCorrect:
            return "name not valid"

        return None

    # Internal function to check sanity of the nodeId.
    @staticmethod
    def check_node_id(nodeId: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(nodeId, int):
            isCorrect = False

        if not isCorrect:
            return "nodeId not valid"

        return None

    # Internal function to check sanity of the nodeType.
    @staticmethod
    def check_node_type(nodeType: str) -> Optional[str]:

        isCorrect = True
        if not isinstance(nodeType, str):
            isCorrect = False

        nodeTypes = {"alert", "manager", "sensor", "server"}
        if nodeType not in nodeTypes:
            isCorrect = False

        if not isCorrect:
            return "nodeType not valid"

        return None

    # Internal function to check sanity of the optionalData.
    @staticmethod
    def check_optional_data(optionalData: Dict[str, Any]) -> Optional[str]:

        isCorrect = True
        if not isinstance(optionalData, dict):
            isCorrect = False
        if "message" in optionalData.keys():
            if MsgChecker.check_optional_data_message(optionalData["message"]) is not None:
                isCorrect = False

        if not isCorrect:
            return "optionalData not valid"

        return None

    # Internal function to check sanity of the optionalData message.
    @staticmethod
    def check_optional_data_message(message: str) -> Optional[str]:

        isCorrect = True
        if not isinstance(message, str):
            isCorrect = False

        if not isCorrect:
            return "optionalData message not valid"

        return None

    # Internal function to check sanity of the optionType.
    @staticmethod
    def check_option_type(optionType: str) -> Optional[str]:

        isCorrect = True
        if not isinstance(optionType, str):
            isCorrect = False

        if optionType != "alertSystemActive":
            isCorrect = False

        if not isCorrect:
            return "optionType not valid"

        return None

    # Internal function to check sanity of the option value.
    @staticmethod
    def check_option_value(value: float) -> Optional[str]:

        isCorrect = True
        if not isinstance(value, float):
            isCorrect = False

        if not 0.0 <= value <= 1.0:
            isCorrect = False

        if not isCorrect:
            return "value not valid"

        return None

    # Internal function to check sanity of the persistent.
    @staticmethod
    def check_persistent(persistent: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(persistent, int):
            isCorrect = False
        elif persistent != 0 and persistent != 1:
            isCorrect = False

        if not isCorrect:
            return "persistent not valid"

        return None

    # Internal function to check sanity of the remoteAlertId.
    @staticmethod
    def check_remote_alert_id(remoteAlertId: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(remoteAlertId, int):
            isCorrect = False

        if not isCorrect:
            return "remoteAlertId not valid"

        return None

    # Internal function to check sanity of the remoteSensorId.
    @staticmethod
    def check_remote_sensor_id(remoteSensorId: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(remoteSensorId, int):
            isCorrect = False

        if not isCorrect:
            return "remoteSensorId not valid"

        return None

    # Internal function to check sanity of the rev.
    @staticmethod
    def check_rev(rev: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(rev, int):
            isCorrect = False

        if not isCorrect:
            return "rev not valid"

        return None

    # Internal function to check sanity of the rulesActivated.
    @staticmethod
    def check_rules_activated(rulesActivated: bool) -> Optional[str]:

        isCorrect = True
        if not isinstance(rulesActivated, bool):
            isCorrect = False

        if not isCorrect:
            return "rulesActivated not valid"

        return None

    # Internal function to check sanity of the sensor data.
    @staticmethod
    def check_sensor_data(data: Any, dataType: int) -> Optional[str]:

        isCorrect = True
        if dataType == SensorDataType.NONE and data is not None:
            isCorrect = False
        elif dataType == SensorDataType.INT and not isinstance(data, int):
            isCorrect = False
        elif dataType == SensorDataType.FLOAT and not isinstance(data, float):
            isCorrect = False

        if not isCorrect:
            return "data not valid"

        return None

    # Internal function to check sanity of the sensor data type.
    @staticmethod
    def check_sensor_data_type(dataType: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(dataType, int):
            isCorrect = False
        elif not (SensorDataType.NONE == dataType
                  or SensorDataType.INT == dataType
                  or SensorDataType.FLOAT == dataType):
            isCorrect = False

        if not isCorrect:
            return "dataType not valid"

        return None

    # Internal function to check sanity of the sensorId.
    @staticmethod
    def check_sensor_id(sensorId: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(sensorId, int):
            isCorrect = False

        if not isCorrect:
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

        isCorrect = True
        if not isinstance(state, int):
            isCorrect = False
        elif state != 0 and state != 1:
            isCorrect = False

        if not isCorrect:
            return "state not valid"

        return None

    # Internal function to check sanity of the status alertLevels list.
    @staticmethod
    def check_status_alert_levels_list(alertLevels: List[Dict[str, Any]]) -> Optional[str]:

        isCorrect = True
        if not isinstance(alertLevels, list):
            isCorrect = False

        # Check each alertLevel if correct.
        for alertLevel in alertLevels:

            if not isinstance(alertLevel, dict):
                isCorrect = False
                break

            if "alertLevel" not in alertLevel.keys():
                isCorrect = False
                break

            elif MsgChecker.check_alert_level(alertLevel["alertLevel"]) is not None:
                isCorrect = False
                break

            if "name" not in alertLevel.keys():
                isCorrect = False
                break

            elif MsgChecker.check_name(alertLevel["name"]) is not None:
                isCorrect = False
                break

            if "triggerAlways" not in alertLevel.keys():
                isCorrect = False
                break

            elif MsgChecker.check_trigger_always(alertLevel["triggerAlways"]) is not None:
                isCorrect = False
                break

            if "rulesActivated" not in alertLevel.keys():
                isCorrect = False
                break

            elif MsgChecker.check_rules_activated(alertLevel["rulesActivated"]) is not None:
                isCorrect = False
                break

        if not isCorrect:
            return "alertLevels list not valid"

        return None

    # Internal function to check sanity of the status alerts list.
    @staticmethod
    def check_status_alerts_list(alerts: List[Dict[str, Any]]) -> Optional[str]:

        isCorrect = True
        if not isinstance(alerts, list):
            isCorrect = False

        # Check each alert if correct.
        for alert in alerts:

            if not isinstance(alert, dict):
                isCorrect = False
                break

            if "nodeId" not in alert.keys():
                isCorrect = False
                break

            elif MsgChecker.check_node_id(alert["nodeId"]) is not None:
                isCorrect = False
                break

            if "alertId" not in alert.keys():
                isCorrect = False
                break

            elif MsgChecker.check_alert_id(alert["alertId"]) is not None:
                isCorrect = False
                break

            if "description" not in alert.keys():
                isCorrect = False
                break

            elif MsgChecker.check_description(alert["description"]) is not None:
                isCorrect = False
                break

            if "alertLevels" not in alert.keys():
                isCorrect = False
                break

            elif MsgChecker.check_alert_levels(alert["alertLevels"]) is not None:
                isCorrect = False
                break

            if "remoteAlertId" not in alert.keys():
                isCorrect = False
                break

            elif MsgChecker.check_remote_alert_id(alert["remoteAlertId"]) is not None:
                isCorrect = False
                break

        if not isCorrect:
            return "alerts list not valid"

        return None

    # Internal function to check sanity of the status managers list.
    @staticmethod
    def check_status_managers_list(managers: List[Dict[str, Any]]) -> Optional[str]:

        isCorrect = True
        if not isinstance(managers, list):
            isCorrect = False

        # Check each manager if correct.
        for manager in managers:

            if not isinstance(manager, dict):
                isCorrect = False
                break

            if "nodeId" not in manager.keys():
                isCorrect = False
                break

            elif MsgChecker.check_node_id(manager["nodeId"]) is not None:
                isCorrect = False
                break

            if "managerId" not in manager.keys():
                isCorrect = False
                break

            elif MsgChecker.check_manager_id(manager["managerId"]) is not None:
                isCorrect = False
                break

            if "description" not in manager.keys():
                isCorrect = False
                break

            elif MsgChecker.check_description(manager["description"]) is not None:
                isCorrect = False
                break

        if not isCorrect:
            return "managers list not valid"

        return None

    # Internal function to check sanity of the status nodes list.
    @staticmethod
    def check_status_nodes_list(nodes: List[Dict[str, Any]]) -> Optional[str]:

        isCorrect = True
        if not isinstance(nodes, list):
            isCorrect = False

        # Check each option if correct.
        for node in nodes:

            if not isinstance(node, dict):
                isCorrect = False
                break

            if "nodeId" not in node.keys():
                isCorrect = False
                break

            elif MsgChecker.check_node_id(node["nodeId"]) is not None:
                isCorrect = False
                break

            if "hostname" not in node.keys():
                isCorrect = False
                break

            elif MsgChecker.check_hostname(node["hostname"]) is not None:
                isCorrect = False
                break

            if "nodeType" not in node.keys():
                isCorrect = False
                break

            elif MsgChecker.check_node_type(node["nodeType"]) is not None:
                isCorrect = False
                break

            if "instance" not in node.keys():
                isCorrect = False
                break

            elif MsgChecker.check_instance(node["instance"]) is not None:
                isCorrect = False
                break

            if "connected" not in node.keys():
                isCorrect = False
                break

            elif MsgChecker.check_connected(node["connected"]) is not None:
                isCorrect = False
                break

            if "version" not in node.keys():
                isCorrect = False
                break

            elif MsgChecker.check_version(node["version"]) is not None:
                isCorrect = False
                break

            if "rev" not in node.keys():
                isCorrect = False
                break

            elif MsgChecker.check_rev(node["rev"]) is not None:
                isCorrect = False
                break

            if "username" not in node.keys():
                isCorrect = False
                break

            elif MsgChecker.check_username(node["username"]) is not None:
                isCorrect = False
                break

            if "persistent" not in node.keys():
                isCorrect = False
                break

            elif MsgChecker.check_persistent(node["persistent"]) is not None:
                isCorrect = False
                break

        if not isCorrect:
            return "nodes list not valid"

        return None

    # Internal function to check sanity of the status options list.
    @staticmethod
    def check_status_options_list(options: List[Dict[str, Any]]) -> Optional[str]:

        isCorrect = True
        if not isinstance(options, list):
            isCorrect = False

        # Check each option if correct.
        for option in options:

            if not isinstance(option, dict):
                isCorrect = False
                break

            if "type" not in option.keys():
                isCorrect = False
                break

            elif MsgChecker.check_option_type(option["type"]) is not None:
                isCorrect = False
                break

            if "value" not in option.keys():
                isCorrect = False
                break

            elif MsgChecker.check_option_value(option["value"]) is not None:
                isCorrect = False
                break

        if not isCorrect:
            return "options list not valid"

        return None

    # Internal function to check sanity of the status sensors list.
    @staticmethod
    def check_status_sensors_list(sensors: List[Dict[str, Any]]) -> Optional[str]:

        isCorrect = True
        if not isinstance(sensors, list):
            isCorrect = False

        # Check each sensor if correct.
        for sensor in sensors:

            if not isinstance(sensor, dict):
                isCorrect = False
                break

            if "nodeId" not in sensor.keys():
                isCorrect = False
                break

            elif MsgChecker.check_node_id(sensor["nodeId"]) is not None:
                isCorrect = False
                break

            if "sensorId" not in sensor.keys():
                isCorrect = False
                break

            elif MsgChecker.check_sensor_id(sensor["sensorId"]) is not None:
                isCorrect = False
                break

            if "alertDelay" not in sensor.keys():
                isCorrect = False
                break

            elif MsgChecker.check_alert_delay(sensor["alertDelay"]) is not None:
                isCorrect = False
                break

            if "alertLevels" not in sensor.keys():
                isCorrect = False
                break

            elif MsgChecker.check_alert_levels(sensor["alertLevels"]) is not None:
                isCorrect = False
                break

            if "description" not in sensor.keys():
                isCorrect = False
                break

            elif MsgChecker.check_description(sensor["description"]) is not None:
                isCorrect = False
                break

            if "lastStateUpdated" not in sensor.keys():
                isCorrect = False
                break

            elif MsgChecker.check_last_state_updated(sensor["lastStateUpdated"]) is not None:
                isCorrect = False
                break

            if "state" not in sensor.keys():
                isCorrect = False
                break

            elif MsgChecker.check_state(sensor["state"]):
                isCorrect = False
                break

            if "remoteSensorId" not in sensor.keys():
                isCorrect = False
                break

            elif MsgChecker.check_remote_sensor_id(sensor["remoteSensorId"]) is not None:
                isCorrect = False
                break

            if "dataType" not in sensor.keys():
                isCorrect = False
                break

            elif MsgChecker.check_sensor_data_type(sensor["dataType"]) is not None:
                isCorrect = False
                break

            if sensor["dataType"] != SensorDataType.NONE:
                if "data" not in sensor.keys():
                    isCorrect = False
                    break

                elif MsgChecker.check_sensor_data(sensor["data"], sensor["dataType"]) is not None:
                    isCorrect = False
                    break

        if not isCorrect:
            return "sensors list not valid"

        return None

    # Internal function to check sanity of the triggerAlways.
    @staticmethod
    def check_trigger_always(triggerAlways: int) -> Optional[str]:

        isCorrect = True
        if not isinstance(triggerAlways, int):
            isCorrect = False
        elif triggerAlways != 0 and triggerAlways != 1:
            isCorrect = False

        if not isCorrect:
            return "triggerAlways not valid"

        return None

    # Internal function to check sanity of the username.
    @staticmethod
    def check_username(username: str) -> Optional[str]:

        isCorrect = True
        if not isinstance(username, str):
            isCorrect = False

        if not isCorrect:
            return "username not valid"

        return None

    # Internal function to check sanity of the version.
    @staticmethod
    def check_version(version: float) -> Optional[str]:

        isCorrect = True
        if not isinstance(version, float):
            isCorrect = False

        if not isCorrect:
            return "version not valid"

        return None


class MsgBuilder:

    # Internal function that builds the client authentication message.
    @staticmethod
    def build_auth_msg(username: str,
                       password: str,
                       version: float,
                       rev: int,
                       regMessageSize: int) -> str:

        payload = {"type": "request",
                   "version": version,
                   "rev": rev,
                   "username": username,
                   "password": password}
        utcTimestamp = int(time.time())
        message = {"clientTime": utcTimestamp,
                   "size": regMessageSize,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)

    # Internal function that builds the option message.
    @staticmethod
    def build_option_msg(optionType: str,
                         optionValue: float,
                         optionDelay: int) -> str:

        payload = {"type": "request",
                   "optionType": optionType,
                   "value": float(optionValue),
                   "timeDelay": optionDelay}
        utcTimestamp = int(time.time())
        message = {"clientTime": utcTimestamp,
                   "message": "option",
                   "payload": payload}
        return json.dumps(message)

    # Internal function that builds the ping message.
    @staticmethod
    def build_ping_msg() -> str:

        payload = {"type": "request"}
        utcTimestamp = int(time.time())
        message = {"clientTime": utcTimestamp,
                   "message": "ping",
                   "payload": payload}
        return json.dumps(message)

    # Internal function that builds the client registration message.
    @staticmethod
    def build_reg_msg(description: str,
                      node_type: str,
                      instance: str,
                      persistent: int) -> str:

        # build manager dict for the message
        manager = dict()
        manager["description"] = description

        payload = {"type": "request",
                   "hostname": socket.gethostname(),
                   "nodeType": node_type,
                   "instance": instance,
                   "persistent": persistent,
                   "manager": manager}
        utcTimestamp = int(time.time())
        message = {"clientTime": utcTimestamp,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)
