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
from typing import List, Dict, Any
from .communication import Communication
from ..localObjects import SensorDataType


class MsgChecker:

    def __init__(self, communication: Communication):
        self._communication = communication

    # Internal function to check sanity of the alertDelay.
    def check_alert_delay(self, alertDelay: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(alertDelay, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "alertDelay not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the alertId.
    def check_alert_id(self, alertId: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(alertId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "alertId not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the alertLevel.
    def check_alert_level(self, alertLevel: int, messageType: str):

        isCorrect = True
        if not isinstance(alertLevel, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "alertLevel not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the alertLevels.
    def check_alert_levels(self, alertLevels: List[int], messageType: str) -> bool:

        isCorrect = True
        if not isinstance(alertLevels, list):
            isCorrect = False
        elif not all(isinstance(item, int) for item in alertLevels):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "alertLevels not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the changeState.
    def check_change_state(self, changeState: bool, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(changeState, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "changeState not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the connected.
    def check_connected(self, connected, messageType):

        isCorrect = True
        if not isinstance(connected, int):
            isCorrect = False
        elif connected != 0 and connected != 1:
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "connected not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the description.
    def check_description(self, description: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(description, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "description not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the hasLatestData.
    def check_has_latest_data(self, hasLatestData: bool, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(hasLatestData, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "hasLatestData not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the hasOptionalData.
    def check_has_optional_data(self, hasOptionalData: bool, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(hasOptionalData, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "hasOptionalData not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the hostname.
    def check_hostname(self, hostname: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(hostname, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "hostname not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the instance.
    def check_instance(self, instance: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(instance, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "instance not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the lastStateUpdated.
    def check_last_state_updated(self, lastStateUpdated: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(lastStateUpdated, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "lastStateUpdated not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the managerId.
    def check_manager_id(self, managerId: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(managerId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "managerId not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the name.
    def check_name(self, name: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(name, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "name not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the nodeId.
    def check_node_id(self, nodeId: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(nodeId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "nodeId not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the nodeType.
    def check_node_type(self, nodeType: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(nodeType, str):
            isCorrect = False

        nodeTypes = {"alert", "manager", "sensor", "server"}
        if nodeType not in nodeTypes:
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "nodeType not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the optionalData.
    def check_optional_data(self, optionalData: Dict[str, Any], messageType: str) -> bool:

        isCorrect = True
        if not isinstance(optionalData, dict):
            isCorrect = False
        if "message" in optionalData.keys():
            if not self.check_optional_data_message(optionalData["message"], messageType):
                isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "optionalData not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the optionalData message.
    def check_optional_data_message(self, message: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(message, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "optionalData message not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the optionType.
    def check_option_type(self, optionType: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(optionType, str):
            isCorrect = False

        if optionType != "alertSystemActive":
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "optionType not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the option value.
    def check_option_value(self, value: float, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(value, float):
            isCorrect = False

        if not 0.0 <= value <= 1.0:
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "value not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the persistent.
    def check_persistent(self, persistent: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(persistent, int):
            isCorrect = False
        elif persistent != 0 and persistent != 1:
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "persistent not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the remoteAlertId.
    def check_remote_alert_id(self, remoteAlertId: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(remoteAlertId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "remoteAlertId not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the remoteSensorId.
    def check_remote_sensor_id(self, remoteSensorId: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(remoteSensorId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "remoteSensorId not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the rev.
    def check_rev(self, rev: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(rev, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "rev not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the rulesActivated.
    def check_rules_activated(self, rulesActivated: bool, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(rulesActivated, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "rulesActivated not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the sensor data.
    def check_sensor_data(self, data: Any, dataType: int, messageType: str) -> bool:

        isCorrect = True
        if dataType == SensorDataType.NONE and data is not None:
            isCorrect = False
        elif dataType == SensorDataType.INT and not isinstance(data, int):
            isCorrect = False
        elif dataType == SensorDataType.FLOAT and not isinstance(data, float):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "data not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the sensor data type.
    def check_sensor_data_type(self, dataType: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(dataType, int):
            isCorrect = False
        elif not (SensorDataType.NONE == dataType
                  or SensorDataType.INT == dataType
                  or SensorDataType.FLOAT == dataType):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "dataType not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the sensorId.
    def check_sensor_id(self, sensorId: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(sensorId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "sensorId not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the serverTime.
    def check_server_time(self, serverTime: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(serverTime, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "serverTime not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the state.
    def check_state(self, state: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(state, int):
            isCorrect = False
        elif state != 0 and state != 1:
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "state not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the status alertLevels list.
    def check_status_alert_levels_list(self, alertLevels: List[Dict[str, Any]], messageType: str) -> bool:

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

            elif not self.check_alert_level(alertLevel["alertLevel"], messageType):
                isCorrect = False
                break

            if "name" not in alertLevel.keys():
                isCorrect = False
                break

            elif not self.check_name(alertLevel["name"], messageType):
                isCorrect = False
                break

            if "triggerAlways" not in alertLevel.keys():
                isCorrect = False
                break

            elif not self.check_trigger_always(alertLevel["triggerAlways"], messageType):
                isCorrect = False
                break

            if "rulesActivated" not in alertLevel.keys():
                isCorrect = False
                break

            elif not self.check_rules_activated(alertLevel["rulesActivated"], messageType):
                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "alertLevels list not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the status alerts list.
    def check_status_alerts_list(self, alerts: List[Dict[str, Any]], messageType: str) -> bool:

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

            elif not self.check_node_id(alert["nodeId"], messageType):
                isCorrect = False
                break

            if "alertId" not in alert.keys():
                isCorrect = False
                break

            elif not self.check_alert_id(alert["alertId"], messageType):
                isCorrect = False
                break

            if "description" not in alert.keys():
                isCorrect = False
                break

            elif not self.check_description(alert["description"], messageType):
                isCorrect = False
                break

            if "alertLevels" not in alert.keys():
                isCorrect = False
                break

            elif not self.check_alert_levels(alert["alertLevels"], messageType):
                isCorrect = False
                break

            if "remoteAlertId" not in alert.keys():
                isCorrect = False
                break

            elif not self.check_remote_alert_id(alert["remoteAlertId"], messageType):
                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "alerts list not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the status managers list.
    def check_status_managers_list(self, managers: List[Dict[str, Any]], messageType: str) -> bool:

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

            elif not self.check_node_id(manager["nodeId"], messageType):
                isCorrect = False
                break

            if "managerId" not in manager.keys():
                isCorrect = False
                break

            elif not self.check_manager_id(manager["managerId"], messageType):
                isCorrect = False
                break

            if "description" not in manager.keys():
                isCorrect = False
                break

            elif not self.check_description(manager["description"], messageType):
                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "managers list not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the status nodes list.
    def check_status_nodes_list(self, nodes: List[Dict[str, Any]], messageType: str) -> bool:

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

            elif not self.check_node_id(node["nodeId"], messageType):
                isCorrect = False
                break

            if "hostname" not in node.keys():
                isCorrect = False
                break

            elif not self.check_hostname(node["hostname"], messageType):
                isCorrect = False
                break

            if "nodeType" not in node.keys():
                isCorrect = False
                break

            elif not self.check_node_type(node["nodeType"], messageType):
                isCorrect = False
                break

            if "instance" not in node.keys():
                isCorrect = False
                break

            elif not self.check_instance(node["instance"], messageType):
                isCorrect = False
                break

            if "connected" not in node.keys():
                isCorrect = False
                break

            elif not self.check_connected(node["connected"], messageType):
                isCorrect = False
                break

            if "version" not in node.keys():
                isCorrect = False
                break

            elif not self.check_version(node["version"], messageType):
                isCorrect = False
                break

            if "rev" not in node.keys():
                isCorrect = False
                break

            elif not self.check_rev(node["rev"], messageType):
                isCorrect = False
                break

            if "username" not in node.keys():
                isCorrect = False
                break

            elif not self.check_username(node["username"], messageType):
                isCorrect = False
                break

            if "persistent" not in node.keys():
                isCorrect = False
                break

            elif not self.check_persistent(node["persistent"], messageType):
                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "nodes list not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the status options list.
    def check_status_options_list(self, options: List[Dict[str, Any]], messageType: str) -> bool:

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

            elif not self.check_option_type(option["type"], messageType):
                isCorrect = False
                break

            if "value" not in option.keys():
                isCorrect = False
                break

            elif not self.check_option_value(option["value"], messageType):
                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "options list not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the status sensors list.
    def check_status_sensors_list(self, sensors: List[Dict[str, Any]], messageType: str) -> bool:

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

            elif not self.check_node_id(sensor["nodeId"], messageType):
                isCorrect = False
                break

            if "sensorId" not in sensor.keys():
                isCorrect = False
                break

            elif not self.check_sensor_id(sensor["sensorId"], messageType):
                isCorrect = False
                break

            if "alertDelay" not in sensor.keys():
                isCorrect = False
                break

            elif not self.check_alert_delay(sensor["alertDelay"], messageType):
                isCorrect = False
                break

            if "alertLevels" not in sensor.keys():
                isCorrect = False
                break

            elif not self.check_alert_levels(sensor["alertLevels"], messageType):
                isCorrect = False
                break

            if "description" not in sensor.keys():
                isCorrect = False
                break

            elif not self.check_description(sensor["description"], messageType):
                isCorrect = False
                break

            if "lastStateUpdated" not in sensor.keys():
                isCorrect = False
                break

            elif not self.check_last_state_updated(sensor["lastStateUpdated"], messageType):
                isCorrect = False
                break

            if "state" not in sensor.keys():
                isCorrect = False
                break

            elif not self.check_state(sensor["state"], messageType):
                isCorrect = False
                break

            if "remoteSensorId" not in sensor.keys():
                isCorrect = False
                break

            elif not self.check_remote_sensor_id(sensor["remoteSensorId"], messageType):
                isCorrect = False
                break

            if "dataType" not in sensor.keys():
                isCorrect = False
                break

            elif not self.check_sensor_data_type(sensor["dataType"], messageType):
                isCorrect = False
                break

            if sensor["dataType"] != SensorDataType.NONE:
                if "data" not in sensor.keys():
                    isCorrect = False
                    break

                elif not self.check_sensor_data(sensor["data"], sensor["dataType"], messageType):
                    isCorrect = False
                    break

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "sensors list not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the triggerAlways.
    def check_trigger_always(self, triggerAlways: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(triggerAlways, int):
            isCorrect = False
        elif triggerAlways != 0 and triggerAlways != 1:
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "triggerAlways not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the username.
    def check_username(self, username: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(username, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "username not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True

    # Internal function to check sanity of the version.
    def check_version(self, version: float, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(version, float):
            isCorrect = False

        if not isCorrect:
            # send error message back
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": messageType,
                       "error": "version not valid"}
            self._communication.send(json.dumps(message))

            return False

        return True


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
