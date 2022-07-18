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
from ..globalData.sensorObjects import SensorDataType, SensorObjSensorAlert, SensorObjStateChange, \
    SensorObjErrorStateChange, SensorErrorState


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
            if "msgTime" in message.keys():
                error_msg = MsgChecker.check_msg_time(message["msgTime"])
                if error_msg is not None:
                    logging.error("[%s]: Received msgTime invalid." % MsgChecker._log_tag)
                    return error_msg
            else:
                return "msgTime expected"

        # Check "SENSORERRORSTATECHANGE" message.
        elif request == "sensorerrorstatechange":
            if "msgTime" not in message.keys():
                logging.error("[%s]: msgTime missing." % MsgChecker._log_tag)
                return "msgTime expected"

            error_msg = MsgChecker.check_msg_time(message["msgTime"])
            if error_msg is not None:
                logging.error("[%s]: Received msgTime invalid." % MsgChecker._log_tag)
                return error_msg

            if "sensorId" not in message["payload"].keys():
                logging.error("[%s]: sensorId missing." % MsgChecker._log_tag)
                return "sensorId expected"

            error_msg = MsgChecker.check_sensor_id(message["payload"]["sensorId"])
            if error_msg is not None:
                logging.error("[%s]: Received sensorId invalid." % MsgChecker._log_tag)
                return error_msg

            if "error_state" not in message["payload"].keys():
                logging.error("[%s]: error_state missing." % MsgChecker._log_tag)
                return "state expected"

            error_msg = MsgChecker.check_error_state(message["payload"]["error_state"])
            if error_msg is not None:
                logging.error("[%s]: Received error_state invalid." % MsgChecker._log_tag)
                return error_msg

        # Check "SENSORALERT" message.
        elif request == "sensoralert":
            if "msgTime" not in message.keys():
                logging.error("[%s]: msgTime missing." % MsgChecker._log_tag)
                return "msgTime expected"

            error_msg = MsgChecker.check_msg_time(message["msgTime"])
            if error_msg is not None:
                logging.error("[%s]: Received msgTime invalid." % MsgChecker._log_tag)
                return error_msg

            if "alertLevels" not in message["payload"].keys():
                logging.error("[%s]: alertLevels missing." % MsgChecker._log_tag)
                return "alertLevels expected"

            error_msg = MsgChecker.check_alert_levels(message["payload"]["alertLevels"])
            if error_msg is not None:
                logging.error("[%s]: Received alertLevels invalid." % MsgChecker._log_tag)
                return error_msg

            if "description" not in message["payload"].keys():
                logging.error("[%s]: description missing." % MsgChecker._log_tag)
                return "description expected"

            error_msg = MsgChecker.check_description(message["payload"]["description"])
            if error_msg is not None:
                logging.error("[%s]: Received description invalid." % MsgChecker._log_tag)
                return error_msg

            if "sensorId" not in message["payload"].keys():
                logging.error("[%s]: sensorId missing." % MsgChecker._log_tag)
                return "sensorId expected"

            error_msg = MsgChecker.check_sensor_id(message["payload"]["sensorId"])
            if error_msg is not None:
                logging.error("[%s]: Received sensorId invalid." % MsgChecker._log_tag)
                return error_msg

            if "state" not in message["payload"].keys():
                logging.error("[%s]: state missing." % MsgChecker._log_tag)
                return "state expected"

            error_msg = MsgChecker.check_state(message["payload"]["state"])
            if error_msg is not None:
                logging.error("[%s]: Received state invalid." % MsgChecker._log_tag)
                return error_msg

            if "hasOptionalData" not in message["payload"].keys():
                logging.error("[%s]: hasOptionalData missing." % MsgChecker._log_tag)
                return "hasOptionalData expected"

            error_msg = MsgChecker.check_has_optional_data(message["payload"]["hasOptionalData"])
            if error_msg is not None:
                logging.error("[%s]: Received hasOptionalData invalid." % MsgChecker._log_tag)
                return error_msg

            if message["payload"]["hasOptionalData"]:
                error_msg = MsgChecker.check_optional_data(message["payload"]["optionalData"])
                if error_msg is not None:
                    logging.error("[%s]: Received optionalData invalid." % MsgChecker._log_tag)
                    return error_msg

            if "dataType" not in message["payload"].keys():
                logging.error("[%s]: dataType missing." % MsgChecker._log_tag)
                return "dataType expected"

            error_msg = MsgChecker.check_sensor_data_type(message["payload"]["dataType"])
            if error_msg is not None:
                logging.error("[%s]: Received dataType invalid." % MsgChecker._log_tag)
                return error_msg

            if "data" not in message["payload"].keys():
                logging.error("[%s]: data missing." % MsgChecker._log_tag)
                return "data expected"

            error_msg = MsgChecker.check_sensor_data(message["payload"]["data"],
                                                     message["payload"]["dataType"])
            if error_msg is not None:
                logging.error("[%s]: Received data invalid." % MsgChecker._log_tag)
                return error_msg

            if "hasLatestData" not in message["payload"].keys():
                logging.error("[%s]: hasLatestData missing." % MsgChecker._log_tag)
                return "hasLatestData expected"

            error_msg = MsgChecker.check_has_latest_data(message["payload"]["hasLatestData"])
            if error_msg is not None:
                logging.error("[%s]: Received hasLatestData invalid." % MsgChecker._log_tag)
                return error_msg

            if "changeState" not in message["payload"].keys():
                logging.error("[%s]: changeState missing." % MsgChecker._log_tag)
                return "changeState expected"

            error_msg = MsgChecker.check_change_state(message["payload"]["changeState"])
            if error_msg is not None:
                logging.error("[%s]: Received changeState invalid." % MsgChecker._log_tag)
                return error_msg

        # Check "PROFILECHANGE" message.
        elif request == "profilechange":
            if "msgTime" not in message.keys():
                logging.error("[%s]: msgTime missing." % MsgChecker._log_tag)
                return "msgTime expected"

            error_msg = MsgChecker.check_msg_time(message["msgTime"])
            if error_msg is not None:
                logging.error("[%s]: Received msgTime invalid." % MsgChecker._log_tag)
                return error_msg

            if "profileId" not in message["payload"].keys():
                logging.error("[%s]: profileId missing." % MsgChecker._log_tag)
                return "profileId expected"

            error_msg = MsgChecker.check_profile_id(message["payload"]["profileId"])
            if error_msg is not None:
                logging.error("[%s]: Received profileId invalid." % MsgChecker._log_tag)
                return error_msg

            if "name" not in message["payload"].keys():
                logging.error("[%s]: name missing." % MsgChecker._log_tag)
                return "profileId expected"

            error_msg = MsgChecker.check_profile_name(message["payload"]["name"])
            if error_msg is not None:
                logging.error("[%s]: Received name invalid." % MsgChecker._log_tag)
                return error_msg

        # Check "STATECHANGE" message.
        elif request == "statechange":
            if "msgTime" not in message.keys():
                logging.error("[%s]: msgTime missing." % MsgChecker._log_tag)
                return "msgTime expected"

            error_msg = MsgChecker.check_msg_time(message["msgTime"])
            if error_msg is not None:
                logging.error("[%s]: Received msgTime invalid." % MsgChecker._log_tag)
                return error_msg

            if "sensorId" not in message["payload"].keys():
                logging.error("[%s]: sensorId missing." % MsgChecker._log_tag)
                return "sensorId expected"

            error_msg = MsgChecker.check_sensor_id(message["payload"]["sensorId"])
            if error_msg is not None:
                logging.error("[%s]: Received sensorId invalid." % MsgChecker._log_tag)
                return error_msg

            if "state" not in message["payload"].keys():
                logging.error("[%s]: state missing." % MsgChecker._log_tag)
                return "state expected"

            error_msg = MsgChecker.check_state(message["payload"]["state"])
            if error_msg is not None:
                logging.error("[%s]: Received state invalid." % MsgChecker._log_tag)
                return error_msg

            if "dataType" not in message["payload"].keys():
                logging.error("[%s]: dataType missing." % MsgChecker._log_tag)
                return "dataType expected"

            error_msg = MsgChecker.check_sensor_data_type(message["payload"]["dataType"])
            if error_msg is not None:
                logging.error("[%s]: Received dataType invalid." % MsgChecker._log_tag)
                return error_msg

            if "data" not in message["payload"].keys():
                logging.error("[%s]: data missing." % MsgChecker._log_tag)
                return "data expected"

            error_msg = MsgChecker.check_sensor_data(message["payload"]["data"],
                                                     message["payload"]["dataType"])
            if error_msg is not None:
                logging.error("[%s]: Received data invalid." % MsgChecker._log_tag)
                return error_msg

        # Check "STATUS" message.
        elif request == "status":
            if "msgTime" not in message.keys():
                logging.error("[%s]: msgTime missing." % MsgChecker._log_tag)
                return "msgTime expected"

            error_msg = MsgChecker.check_msg_time(message["msgTime"])
            if error_msg is not None:
                logging.error("[%s]: Received msgTime invalid." % MsgChecker._log_tag)
                return error_msg

            if "options" not in message["payload"].keys():
                logging.error("[%s]: options missing." % MsgChecker._log_tag)
                return "options expected"

            error_msg = MsgChecker.check_status_options_list(message["payload"]["options"])
            if error_msg is not None:
                logging.error("[%s]: Received options invalid." % MsgChecker._log_tag)
                return error_msg

            if "profiles" not in message["payload"].keys():
                logging.error("[%s]: profiles missing." % MsgChecker._log_tag)
                return "profiles expected"

            error_msg = MsgChecker.check_status_profiles_list(message["payload"]["profiles"])
            if error_msg is not None:
                logging.error("[%s]: Received profiles invalid." % MsgChecker._log_tag)
                return error_msg

            if "nodes" not in message["payload"].keys():
                logging.error("[%s]: nodes missing." % MsgChecker._log_tag)
                return "nodes expected"

            error_msg = MsgChecker.check_status_nodes_list(message["payload"]["nodes"])
            if error_msg is not None:
                logging.error("[%s]: Received nodes invalid." % MsgChecker._log_tag)
                return error_msg

            if "sensors" not in message["payload"].keys():
                logging.error("[%s]: sensors missing." % MsgChecker._log_tag)
                return "sensors expected"

            error_msg = MsgChecker.check_status_sensors_list(message["payload"]["sensors"])
            if error_msg is not None:
                logging.error("[%s]: Received sensors invalid." % MsgChecker._log_tag)
                return error_msg

            if "managers" not in message["payload"].keys():
                logging.error("[%s]: managers missing." % MsgChecker._log_tag)
                return "managers expected"

            error_msg = MsgChecker.check_status_managers_list(message["payload"]["managers"])
            if error_msg is not None:
                logging.error("[%s]: Received managers invalid." % MsgChecker._log_tag)
                return error_msg

            if "alerts" not in message["payload"].keys():
                logging.error("[%s]: alerts missing." % MsgChecker._log_tag)
                return "alerts expected"

            error_msg = MsgChecker.check_status_alerts_list(message["payload"]["alerts"])
            if error_msg is not None:
                logging.error("[%s]: Received alerts invalid." % MsgChecker._log_tag)
                return error_msg

            if "alertLevels" not in message["payload"].keys():
                logging.error("[%s]: alertLevels missing." % MsgChecker._log_tag)
                return "alertLevels expected"

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
    def check_alert_delay(alert_delay: int) -> Optional[str]:

        is_correct = True
        if not isinstance(alert_delay, int):
            is_correct = False

        if not is_correct:
            return "alertDelay not valid"

        return None

    # Internal function to check sanity of the alertId.
    @staticmethod
    def check_alert_id(alert_id: int) -> Optional[str]:

        is_correct = True
        if not isinstance(alert_id, int):
            is_correct = False

        if not is_correct:
            return "alertId not valid"

        return None

    # Internal function to check sanity of the alertLevel.
    @staticmethod
    def check_alert_level(alert_level: int):

        is_correct = True
        if not isinstance(alert_level, int):
            is_correct = False

        if not is_correct:
            return "alertLevel not valid"

        return None

    # Internal function to check sanity of the alertLevels.
    @staticmethod
    def check_alert_levels(alert_levels: List[int]) -> Optional[str]:

        is_correct = True
        if not isinstance(alert_levels, list):
            is_correct = False
        elif not all(isinstance(item, int) for item in alert_levels):
            is_correct = False

        if not is_correct:
            return "alertLevels not valid"

        return None

    # Internal function to check sanity of the changeState.
    @staticmethod
    def check_change_state(change_state: bool) -> Optional[str]:

        is_correct = True
        if not isinstance(change_state, bool):
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
    def check_has_latest_data(has_latest_data: bool) -> Optional[str]:

        is_correct = True
        if not isinstance(has_latest_data, bool):
            is_correct = False

        if not is_correct:
            return "hasLatestData not valid"

        return None

    # Internal function to check sanity of the hasOptionalData.
    @staticmethod
    def check_has_optional_data(has_optional_data: bool) -> Optional[str]:

        is_correct = True
        if not isinstance(has_optional_data, bool):
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

    # Internal function to check sanity of the managerId.
    @staticmethod
    def check_manager_id(manager_id: int) -> Optional[str]:

        is_correct = True
        if not isinstance(manager_id, int):
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
    def check_node_id(node_id: int) -> Optional[str]:

        is_correct = True
        if not isinstance(node_id, int):
            is_correct = False

        if not is_correct:
            return "nodeId not valid"

        return None

    # Internal function to check sanity of the nodeType.
    @staticmethod
    def check_node_type(node_type: str) -> Optional[str]:

        is_correct = True
        if not isinstance(node_type, str):
            is_correct = False

        node_types = {"alert", "manager", "sensor", "server"}
        if node_type not in node_types:
            is_correct = False

        if not is_correct:
            return "nodeType not valid"

        return None

    # Internal function to check sanity of the optionalData.
    @staticmethod
    def check_optional_data(optional_data: Dict[str, Any]) -> Optional[str]:

        is_correct = True
        if not isinstance(optional_data, dict):
            is_correct = False
        if "message" in optional_data.keys():
            if MsgChecker.check_optional_data_message(optional_data["message"]) is not None:
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
    def check_option_type(option_type: str) -> Optional[str]:

        is_correct = True
        if not isinstance(option_type, str):
            is_correct = False

        if not is_correct:
            return "optionType not valid"

        return None

    # Internal function to check sanity of the option value.
    @staticmethod
    def check_option_value(value: int) -> Optional[str]:

        is_correct = True
        if not isinstance(value, int):
            is_correct = False

        if not is_correct:
            return "value not valid"

        return None

    @staticmethod
    def check_profile_id(profile_id: int) -> Optional[str]:
        """
        Internal function to check sanity of the profile id.
        :param profile_id:
        :return:
        """
        is_correct = True
        if not isinstance(profile_id, int):
            is_correct = False

        if not is_correct:
            return "profileId not valid"

        return None

    @staticmethod
    def check_profile_name(profile_name: str) -> Optional[str]:
        """
        Internal function to check sanity of the profile name.
        :param profile_name:
        :return:
        """
        is_correct = True
        if not isinstance(profile_name, str):
            is_correct = False

        if not is_correct:
            return "profile name not valid"

        return None

    @staticmethod
    def check_profiles(profiles: List[int]) -> Optional[str]:
        """
        Internal function to check sanity of the profiles integer list.
        :param profiles:
        :return:
        """
        is_correct = True
        if not isinstance(profiles, list):
            is_correct = False
        elif not all(isinstance(item, int) for item in profiles):
            is_correct = False

        if not is_correct:
            return "profiles not valid"

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

    # Internal function to check sanity of the clientAlertId.
    @staticmethod
    def check_client_alert_id(client_alert_id: int) -> Optional[str]:

        is_correct = True
        if not isinstance(client_alert_id, int):
            is_correct = False

        if not is_correct:
            return "clientAlertId not valid"

        return None

    # Internal function to check sanity of the clientSensorId.
    @staticmethod
    def check_client_sensor_id(client_sensor_id: int) -> Optional[str]:

        is_correct = True
        if not isinstance(client_sensor_id, int):
            is_correct = False

        if not is_correct:
            return "clientSensorId not valid"

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
    def check_sensor_data(data: Dict[str, Any], data_type: int) -> Optional[str]:

        is_correct = False
        sensor_data_class = SensorDataType.get_sensor_data_class(data_type)
        if sensor_data_class.verify_dict(data):
            is_correct = True

        if not is_correct:
            return "data not valid"

        return None

    # Internal function to check sanity of the sensor data type.
    @staticmethod
    def check_sensor_data_type(data_type: int) -> Optional[str]:

        is_correct = True
        if not isinstance(data_type, int):
            is_correct = False
        elif not SensorDataType.has_value(data_type):
            is_correct = False

        if not is_correct:
            return "dataType not valid"

        return None

    # Internal function to check sanity of the sensorId.
    @staticmethod
    def check_sensor_id(sensor_id: int) -> Optional[str]:

        is_correct = True
        if not isinstance(sensor_id, int):
            is_correct = False

        if not is_correct:
            return "sensorId not valid"

        return None

    # Internal function to check sanity of the msgTime.
    @staticmethod
    def check_msg_time(msg_time: int) -> Optional[str]:

        is_correct = True
        if not isinstance(msg_time, int):
            is_correct = False

        if not is_correct:
            return "msg_time not valid"

        return None

    @staticmethod
    def check_error_state(data: Dict[str, Any]) -> Optional[str]:
        """
        Internal function to check sanity of the error state.
        """

        is_correct = True
        if not SensorErrorState.verify_dict(data):
            is_correct = False

        if not is_correct:
            return "error_state not valid"

        return None

    @staticmethod
    def check_state(state: int) -> Optional[str]:
        """
        Internal function to check sanity of the state.
        """

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
    def check_status_alert_levels_list(alert_levels: List[Dict[str, Any]]) -> Optional[str]:

        is_correct = True
        if not isinstance(alert_levels, list):
            is_correct = False

        alert_level_ids = set()

        # Check each alertLevel if correct.
        for alertLevel in alert_levels:

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

            if "profiles" not in alertLevel.keys():
                is_correct = False
                break

            elif MsgChecker.check_profiles(alertLevel["profiles"]) is not None:
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

            if "clientAlertId" not in alert.keys():
                is_correct = False
                break

            elif MsgChecker.check_client_alert_id(alert["clientAlertId"]) is not None:
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

    @staticmethod
    def check_status_profiles_list(profiles: List[Dict[str, Any]]) -> Optional[str]:
        """
        # Internal function to check sanity of the status profiles list.
        :param profiles:
        :return:
        """
        is_correct = True
        if not isinstance(profiles, list):
            is_correct = False

        # Check each profile if correct.
        for profile in profiles:

            if not isinstance(profile, dict):
                is_correct = False
                break

            if "profileId" not in profile.keys():
                is_correct = False
                break

            elif MsgChecker.check_profile_id(profile["profileId"]) is not None:
                is_correct = False
                break

            if "name" not in profile.keys():
                is_correct = False
                break

            elif MsgChecker.check_profile_name(profile["name"]) is not None:
                is_correct = False
                break

        if not is_correct:
            return "profiles list not valid"

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

            if "state" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_state(sensor["state"]):
                is_correct = False
                break

            if "clientSensorId" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_client_sensor_id(sensor["clientSensorId"]) is not None:
                is_correct = False
                break

            if "dataType" not in sensor.keys():
                is_correct = False
                break

            elif MsgChecker.check_sensor_data_type(sensor["dataType"]) is not None:
                is_correct = False
                break

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
                       reg_message_size: int) -> str:
        """
        Internal function that builds the client authentication message.

        :param username:
        :param password:
        :param version:
        :param rev:
        :param reg_message_size:
        :return:
        """
        payload = {"type": "request",
                   "version": version,
                   "rev": rev,
                   "username": username,
                   "password": password}
        utc_timestamp = int(time.time())
        message = {"msgTime": utc_timestamp,
                   "size": reg_message_size,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_option_msg_manager(option_type: str,
                                 option_value: int,
                                 option_delay: int) -> str:
        """
        Internal function that builds the option message for manager nodes.

        :param option_type:
        :param option_value:
        :param option_delay:
        :return:
        """
        payload = {"type": "request",
                   "optionType": option_type,
                   "value": option_value,
                   "timeDelay": option_delay}
        utc_timestamp = int(time.time())
        message = {"msgTime": utc_timestamp,
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
        message = {"msgTime": utc_timestamp,
                   "message": "ping",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_reg_msg_alert(local_alerts,
                            node_type: str,
                            instance: str,
                            persistent: int) -> str:
        """
        Internal function that builds the client registration message for alert nodes.

        :param local_alerts: the objects representing the local alerts.
        :param node_type:
        :param instance:
        :param persistent:
        :return:
        """
        # build alerts list for the message
        alerts = list()
        for alert in local_alerts:
            temp_alert = dict()
            temp_alert["clientAlertId"] = alert.id
            temp_alert["description"] = alert.description
            temp_alert["alertLevels"] = alert.alertLevels
            alerts.append(temp_alert)

        payload = {"type": "request",
                   "hostname": socket.gethostname(),
                   "nodeType": node_type,
                   "instance": instance,
                   "persistent": persistent,
                   "alerts": alerts}

        utc_timestamp = int(time.time())
        message = {"msgTime": utc_timestamp,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_reg_msg_manager(description: str,
                              node_type: str,
                              instance: str,
                              persistent: int) -> str:
        """
        Internal function that builds the client registration message for manager nodes.

        :param description: the description of the manager.
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
        message = {"msgTime": utc_timestamp,
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

        :param polling_sensors: the objects representing the local sensors.
        :param node_type:
        :param instance:
        :param persistent:
        :return:
        """
        # build sensors list for the message
        msg_sensors = list()
        for sensor in polling_sensors:
            temp_sensor = dict()
            temp_sensor["clientSensorId"] = sensor.id
            temp_sensor["error_state"] = sensor.error_state.copy_to_dict()
            temp_sensor["alertDelay"] = sensor.alertDelay
            temp_sensor["alertLevels"] = sensor.alertLevels
            temp_sensor["description"] = sensor.description
            temp_sensor["state"] = sensor.state
            temp_sensor["dataType"] = sensor.sensorDataType
            temp_sensor["data"] = sensor.data.copy_to_dict()

            msg_sensors.append(temp_sensor)

        payload = {"type": "request",
                   "hostname": socket.gethostname(),
                   "nodeType": node_type,
                   "instance": instance,
                   "persistent": persistent,
                   "sensors": msg_sensors}

        utc_timestamp = int(time.time())
        message = {"msgTime": utc_timestamp,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)

    @staticmethod
    def build_error_state_change_msg_sensor(error_state_change: SensorObjErrorStateChange) -> str:
        """
        Internal function that builds an error state change message for sensor nodes.

        :param error_state_change:
        """
        payload = {"type": "request",
                   "clientSensorId": error_state_change.clientSensorId,
                   "error_state": error_state_change.error_state.copy_to_dict()}

        utc_timestamp = int(time.time())
        message = {"msgTime": utc_timestamp,
                   "message": "sensorerrorstatechange",
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
                   "dataType": sensor_alert.dataType,
                   "data": sensor_alert.data.copy_to_dict()}

        # Only add optional data field if it should be transfered.
        if sensor_alert.hasOptionalData:
            payload["optionalData"] = sensor_alert.optionalData

        utc_timestamp = int(time.time())
        message = {"msgTime": utc_timestamp,
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
                   "dataType": state_change.dataType,
                   "data": state_change.data.copy_to_dict()}

        utc_timestamp = int(time.time())
        message = {"msgTime": utc_timestamp,
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
            temp_sensor["error_state"] = sensor.error_state.copy_to_dict()
            temp_sensor["dataType"] = sensor.sensorDataType
            temp_sensor["data"] = sensor.data.copy_to_dict()

            # convert the internal trigger state to the state
            # convention of the alert system (1 = trigger, 0 = normal)
            if sensor.triggerState == sensor.state:
                temp_sensor["state"] = 1
            else:
                temp_sensor["state"] = 0

            sensors.append(temp_sensor)

        payload = {"type": "request", "sensors": sensors}
        utc_timestamp = int(time.time())
        message = {"msgTime": utc_timestamp,
                   "message": "status",
                   "payload": payload}
        return json.dumps(message)
