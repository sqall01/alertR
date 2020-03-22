#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import logging
import os
import json
import threading
from typing import Dict, Any, Optional
from .util import MsgChecker, MsgBuilder
from .communication import Communication
from .eventHandler import EventHandler
from ..localObjects import SensorDataType, Option, Node, Sensor, Manager, Alert, SensorAlert, AlertLevel
from ..globalData import GlobalData


# this class handles the communication with the server
class ServerCommunication:

    def __init__(self, host: str,
                 port: int,
                 server_ca_file: str,
                 username: str,
                 password: str,
                 client_cert_file: str,
                 client_key_file: str,
                 event_handler: EventHandler,
                 global_data: GlobalData):

        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._server_ca_file = server_ca_file
        self._client_cert_file = client_cert_file
        self._client_key_file = client_key_file

        # get global configured data
        self._global_data = global_data
        self._version = self._global_data.version
        self._rev = self._global_data.rev
        self._nodeType = self._global_data.nodeType.lower()
        self._instance = self._global_data.instance
        self._persistent = self._global_data.persistent

        # create the object that handles all incoming server events
        self._event_handler = event_handler

        # file nme of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        # Description of this manager.
        self._description = self._global_data.description

        # Communication object that handles sending and receiving.
        self._communication = Communication(self._host,
                                            self._port,
                                            self._server_ca_file,
                                            self._client_cert_file,
                                            self._client_key_file)

        # Utility class that checks the incoming messages.
        self._msg_checker = MsgChecker(self._communication)

        self._initialization_lock = threading.Lock()

    @property
    def last_communication(self) -> int:
        return self._communication.last_communication

    @property
    def is_connected(self) -> bool:
        return self._communication.is_connected

    def _verify_version_and_auth(self,
                                 regMessageSize: int) -> bool:
        """
        Internal function to verify the server/client version and authenticate.

        :param regMessageSize:
        :return:
        """
        authMessage = MsgBuilder.build_auth_msg(self._username,
                                                self._password,
                                                self._version,
                                                self._rev,
                                                regMessageSize)

        # send user credentials and version
        try:
            logging.debug("[%s]: Sending user credentials and version." % self._log_tag)
            self._communication.send(authMessage)

        except Exception as e:
            logging.exception("[%s]: Sending user credentials "
                              % self._log_tag
                              + "and version failed.")
            return False

        # get authentication response from server
        try:
            data = self._communication.recv()
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'."
                              % (self._log_tag, message["error"]))
                return False

            if str(message["message"]).upper() != "initialization".upper():
                logging.error("[%s]: Wrong authentication message: '%s'."
                              % (self._log_tag, message["message"]))

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "initialization message expected"}
                    self._communication.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                logging.error("[%s]: response expected." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "response expected"}
                    self._communication.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).upper() != "OK":
                logging.error("[%s]: Result not ok: '%s'."
                              % (self._log_tag, message["payload"]["result"]))
                return False

        except Exception:
            logging.exception("[%s]: Receiving authentication response failed." % self._log_tag)
            return False

        # verify version
        try:
            version = float(message["payload"]["version"])
            rev = int(message["payload"]["rev"])

            logging.debug("[%s]: Received server version: '%.3f-%d'."
                          % (self._log_tag, version, rev))

            # check if used protocol version is compatible
            if int(self._version * 10) != int(version * 10):

                logging.error("[%s]: Version not compatible. " % self._log_tag
                              + "Client has version: '%.3f-%d' "
                              % (self._version, self._rev)
                              + "and server has '%.3f-%d"
                              % (version, rev))

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "version not compatible"}
                    self._communication.send(json.dumps(message))
                except Exception:
                    pass

                return False

        except Exception:

            logging.exception("[%s]: Version not valid." % self._log_tag)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": message["message"],
                           "error": "version not valid"}
                self._communication.send(json.dumps(message))
            except Exception:
                pass

            return False

        return True

    # Internal function to register the node.
    def _register_node(self, regMessage: str) -> bool:

        # Send registration message.
        try:
            logging.debug("[%s]: Sending registration message." % self._log_tag)
            self._communication.send(regMessage)

        except Exception:
            logging.exception("[%s]: Sending registration message." % self._log_tag)
            return False

        # get registration response from server
        try:
            data = self._communication.recv()
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'." % (self._log_tag, message["error"]))
                return False

            if str(message["message"]).upper() != "initialization".upper():
                logging.error("[%s]: Wrong registration message: '%s'."
                              % (self._log_tag, message["message"]))

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "initialization message expected"}
                    self._communication.send(json.dumps(message))
                except Exception:
                    pass

                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                logging.error("[%s]: response expected." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "response expected"}
                    self._communication.send(json.dumps(message))
                except Exception:
                    pass

                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).upper() != "OK":
                logging.error("[%s]: Result not ok: '%s'." % (self._log_tag, message["payload"]["result"]))
                return False

        except Exception:
            logging.exception("[%s]: Receiving registration response failed." % self._log_tag)
            return False

        return True

    def _status_update_handler(self,
                               incomingMessage: Dict[str, Any]):
        """
        Internal function that handles received status updates.

        :param incomingMessage:
        :return: success or failure
        """
        options = list()
        nodes = list()
        sensors = list()
        managers = list()
        alerts = list()
        alertLevels = list()

        # extract status values
        try:

            if not self._msg_checker.check_server_time(incomingMessage["serverTime"], incomingMessage["message"]):
                logging.error("[%s]: Received serverTime invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_status_options_list(incomingMessage["payload"]["options"], incomingMessage["message"]):
                logging.error("[%s]: Received options invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_status_nodes_list(incomingMessage["payload"]["nodes"], incomingMessage["message"]):
                logging.error("[%s]: Received nodes invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_status_sensors_list(incomingMessage["payload"]["sensors"], incomingMessage["message"]):
                logging.error("[%s]: Received sensors invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_status_managers_list(incomingMessage["payload"]["managers"], incomingMessage["message"]):
                logging.error("[%s]: Received managers invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_status_alerts_list(incomingMessage["payload"]["alerts"], incomingMessage["message"]):
                logging.error("[%s]: Received alerts invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_status_alert_levels_list(incomingMessage["payload"]["alertLevels"],
                                                                    incomingMessage["message"]):
                logging.error("[%s]: Received alertLevels invalid." % self._log_tag)
                return False

            serverTime = incomingMessage["serverTime"]
            optionsRaw = incomingMessage["payload"]["options"]
            nodesRaw = incomingMessage["payload"]["nodes"]
            sensorsRaw = incomingMessage["payload"]["sensors"]
            managersRaw = incomingMessage["payload"]["managers"]
            alertsRaw = incomingMessage["payload"]["alerts"]
            alertLevelsRaw = incomingMessage["payload"]["alertLevels"]

        except Exception as e:
            logging.exception("[%s]: Received status invalid." % self._log_tag)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": incomingMessage["message"],
                           "error": "received status invalid"}
                self._communication.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        logging.debug("[%s]: Received option count: %d." % (self._log_tag, len(optionsRaw)))

        # process received options
        for i in range(len(optionsRaw)):

            try:
                optionType = optionsRaw[i]["type"]
                optionValue = optionsRaw[i]["value"]
            except Exception as e:
                logging.exception("[%s]: Received option invalid." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": incomingMessage["message"],
                               "error": "received option invalid"}
                    self._communication.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received option information: '%s':%d." % (self._log_tag, optionType, optionValue))

            option = Option()
            option.type = optionType
            option.value = optionValue
            options.append(option)

        logging.debug("[%s]: Received node count: %d." % (self._log_tag, len(nodesRaw)))

        # process received nodes
        for i in range(len(nodesRaw)):

            try:
                nodeId = nodesRaw[i]["nodeId"]
                hostname = nodesRaw[i]["hostname"]
                nodeType = nodesRaw[i]["nodeType"]
                instance = nodesRaw[i]["instance"]
                connected = nodesRaw[i]["connected"]
                version = nodesRaw[i]["version"]
                rev = nodesRaw[i]["rev"]
                username = nodesRaw[i]["username"]
                persistent = nodesRaw[i]["persistent"]

            except Exception as e:
                logging.exception("[%s]: Received node invalid." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": incomingMessage["message"],
                               "error": "received node invalid"}
                    self._communication.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received node information: %d:'%s':'%s':%d:%d."
                          % (self._log_tag, nodeId, hostname, nodeType, connected, persistent))

            node = Node()
            node.nodeId = nodeId
            node.hostname = hostname
            node.nodeType = nodeType
            node.instance = instance
            node.connected = connected
            node.version = version
            node.rev = rev
            node.username = username
            node.persistent = persistent
            nodes.append(node)

        logging.debug("[%s]: Received sensor count: %d." % (self._log_tag, len(sensorsRaw)))

        # process received sensors
        for i in range(len(sensorsRaw)):

            try:
                nodeId = sensorsRaw[i]["nodeId"]
                sensorId = sensorsRaw[i]["sensorId"]
                remoteSensorId = sensorsRaw[i]["remoteSensorId"]
                alertDelay = sensorsRaw[i]["alertDelay"]
                dataType = sensorsRaw[i]["dataType"]

                sensorData = None
                if dataType != SensorDataType.NONE:
                    sensorData = sensorsRaw[i]["data"]

                sensorAlertLevels = sensorsRaw[i]["alertLevels"]
                description = sensorsRaw[i]["description"]
                lastStateUpdated = sensorsRaw[i]["lastStateUpdated"]
                state = sensorsRaw[i]["state"]
            except Exception as e:
                logging.exception("[%s]: Received sensor invalid." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": incomingMessage["message"],
                               "error": "received sensor invalid"}
                    self._communication.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received sensor information: %d:%d:%d:'%s':%d:%d."
                          % (self._log_tag, nodeId, sensorId, alertDelay, description, lastStateUpdated, state))

            sensor = Sensor()
            sensor.nodeId = nodeId
            sensor.sensorId = sensorId
            sensor.remoteSensorId = remoteSensorId
            sensor.alertDelay = alertDelay
            sensor.alertLevels = sensorAlertLevels
            sensor.description = description
            sensor.lastStateUpdated = lastStateUpdated
            sensor.state = state
            sensor.dataType = dataType
            sensor.data = sensorData

            sensors.append(sensor)

        logging.debug("[%s]: Received manager count: %d." % (self._log_tag, len(managersRaw)))

        # process received managers
        for i in range(len(managersRaw)):

            try:
                nodeId = managersRaw[i]["nodeId"]
                managerId = managersRaw[i]["managerId"]
                description = managersRaw[i]["description"]
            except Exception as e:
                logging.exception("[%s]: Received manager invalid." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": incomingMessage["message"],
                               "error": "received manager invalid"}
                    self._communication.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received manager information: %d:%d:'%s'."
                          % (self._log_tag, nodeId, managerId, description))

            manager = Manager()
            manager.nodeId = nodeId
            manager.managerId = managerId
            manager.description = description
            managers.append(manager)

        logging.debug("[%s]: Received alert count: %d." % (self._log_tag, len(alertsRaw)))

        # process received alerts
        for i in range(len(alertsRaw)):

            try:
                nodeId = alertsRaw[i]["nodeId"]
                alertId = alertsRaw[i]["alertId"]
                remoteAlertId = alertsRaw[i]["remoteAlertId"]
                description = alertsRaw[i]["description"]
                alertAlertLevels = alertsRaw[i]["alertLevels"]

            except Exception as e:
                logging.exception("[%s]: Received alert invalid." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": incomingMessage["message"],
                               "error": "received alert invalid"}
                    self._communication.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received alert information: %d:%d:'%s'."
                          % (self._log_tag, nodeId, alertId, description))

            alert = Alert()
            alert.nodeId = nodeId
            alert.alertId = alertId
            alert.remoteAlertId = remoteAlertId
            alert.alertLevels = alertAlertLevels
            alert.description = description
            alerts.append(alert)

        logging.debug("[%s]: Received alertLevel count: %d." % (self._log_tag, len(alertLevelsRaw)))

        # process received alertLevels
        for i in range(len(alertLevelsRaw)):

            try:
                level = alertLevelsRaw[i]["alertLevel"]
                name = alertLevelsRaw[i]["name"]
                triggerAlways = alertLevelsRaw[i]["triggerAlways"]
                rulesActivated = alertLevelsRaw[i]["rulesActivated"]

            except Exception as e:
                logging.exception("[%s]: Received alertLevel invalid." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": incomingMessage["message"],
                               "error": "received alertLevel invalid"}
                    self._communication.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received alertLevel information: %d:'%s':%d."
                          % (self._log_tag, level, name, triggerAlways))

            alertLevel = AlertLevel()
            alertLevel.level = level
            alertLevel.name = name
            alertLevel.triggerAlways = triggerAlways
            alertLevel.rulesActivated = rulesActivated
            alertLevels.append(alertLevel)

        # handle received status update
        if not self._event_handler.status_update(serverTime,
                                                 options,
                                                 nodes,
                                                 sensors,
                                                 managers,
                                                 alerts,
                                                 alertLevels):

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": incomingMessage["message"],
                           "error": "handling received data failed"}
                self._communication.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        # sending sensor alert response
        logging.debug("[%s]: Sending status response message." % self._log_tag)
        try:
            payload = {"type": "response",
                       "result": "ok"}
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": "status",
                       "payload": payload}
            self._communication.send(json.dumps(message))

        except Exception as e:
            logging.exception("[%s]: Sending status response failed." % self._log_tag)
            return False

        return True

    def _sensorAlertHandler(self,
                            incomingMessage: Dict[str, Any]) -> bool:
        """
        Internal function that handles received sensor alerts.

        :param incomingMessage:
        :return: success or failure
        """
        logging.info("[%s]: Received sensor alert." % self._log_tag)

        # extract sensor alert values
        sensorAlert = SensorAlert()
        sensorAlert.timeReceived = int(time.time())
        try:
            if not self._msg_checker.check_server_time(incomingMessage["serverTime"], incomingMessage["message"]):
                logging.error("[%s]: Received serverTime invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_alert_levels(incomingMessage["payload"]["alertLevels"], incomingMessage["message"]):
                logging.error("[%s]: Received alertLevels invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_description(incomingMessage["payload"]["description"], incomingMessage["message"]):
                logging.error("[%s]: Received description invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_rules_activated(incomingMessage["payload"]["rulesActivated"],
                                                           incomingMessage["message"]):
                logging.error("[%s]: Received rulesActivated invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_sensor_id(incomingMessage["payload"]["sensorId"], incomingMessage["message"]):
                logging.error("[%s]: Received sensorId invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_state(incomingMessage["payload"]["state"], incomingMessage["message"]):
                logging.error("[%s]: Received state invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_has_optional_data(incomingMessage["payload"]["hasOptionalData"],
                                                             incomingMessage["message"]):
                logging.error("[%s]: Received hasOptionalData invalid." % self._log_tag)
                return False

            if incomingMessage["payload"]["hasOptionalData"]:
                if not self._msg_checker.check_optional_data(incomingMessage["payload"]["optionalData"],
                                                             incomingMessage["message"]):
                    logging.error("[%s]: Received optionalData invalid." % self._log_tag)
                    return False

            if not self._msg_checker.check_sensor_data_type(incomingMessage["payload"]["dataType"],
                                                            incomingMessage["message"]):
                logging.error("[%s]: Received dataType invalid." % self._log_tag)
                return False

            if incomingMessage["payload"]["dataType"] != SensorDataType.NONE:
                if not self._msg_checker.check_sensor_data(incomingMessage["payload"]["data"],
                                                           incomingMessage["payload"]["dataType"],
                                                           incomingMessage["message"]):
                    logging.error("[%s]: Received data invalid." % self._log_tag)
                    return False

            if not self._msg_checker.check_has_latest_data(incomingMessage["payload"]["hasLatestData"],
                                                           incomingMessage["message"]):
                logging.error("[%s]: Received hasLatestData invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_change_state(incomingMessage["payload"]["changeState"],
                                                        incomingMessage["message"]):
                logging.error("[%s]: Received changeState invalid." % self._log_tag)
                return False

            serverTime = incomingMessage["serverTime"]

            sensorAlert.rulesActivated = incomingMessage["payload"]["rulesActivated"]

            # always -1 when no sensor is responsible for sensor alert
            sensorAlert.sensorId = incomingMessage["payload"]["sensorId"]

            # state of rule sensor alerts is always set to 1
            sensorAlert.state = incomingMessage["payload"]["state"]

            sensorAlert.alertLevels = incomingMessage["payload"]["alertLevels"]

            sensorAlert.description = incomingMessage["payload"]["description"]

            # parse transfer data
            sensorAlert.hasOptionalData = incomingMessage["payload"]["hasOptionalData"]
            if sensorAlert.hasOptionalData:
                sensorAlert.optionalData = incomingMessage["payload"]["optionalData"]
            else:
                sensorAlert.optionalData = dict()

            sensorAlert.changeState = incomingMessage["payload"]["changeState"]
            sensorAlert.hasLatestData = incomingMessage["payload"]["hasLatestData"]
            sensorAlert.dataType = incomingMessage["payload"]["dataType"]

            sensorAlert.sensorData = None
            if sensorAlert.dataType == SensorDataType.INT:
                sensorAlert.sensorData = incomingMessage["payload"]["data"]
            elif sensorAlert.dataType == SensorDataType.FLOAT:
                sensorAlert.sensorData = incomingMessage["payload"]["data"]

        except Exception as e:
            logging.exception("[%s]: Received sensor alert invalid." % self._log_tag)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": incomingMessage["message"],
                           "error": "received sensor alert invalid"}
                self._communication.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        # sending sensor alert response
        logging.debug("[%s]: Sending sensor alert response message." % self._log_tag)
        try:
            payload = {"type": "response",
                       "result": "ok"}
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": "sensoralert",
                       "payload": payload}
            self._communication.send(json.dumps(message))

        except Exception as e:
            logging.exception("[%s]: Sending sensor alert response failed." % self._log_tag)
            return False

        # handle received sensor alert
        if self._event_handler.sensor_alert(serverTime, sensorAlert):
            return True

        return False

    def _state_change_handler(self,
                              incomingMessage: Dict[str, Any]) -> bool:
        """
        Internal function that handles received state changes of sensors.

        :param incomingMessage:
        :return: success or failure
        """
        logging.debug("[%s]: Received state change." % self._log_tag)

        # extract state change values
        try:
            if not self._msg_checker.check_server_time(incomingMessage["serverTime"], incomingMessage["message"]):
                logging.error("[%s]: Received serverTime invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_sensor_id(incomingMessage["payload"]["sensorId"], incomingMessage["message"]):
                logging.error("[%s]: Received sensorId invalid." % self._log_tag)
                return False
            if not self._msg_checker.check_state(incomingMessage["payload"]["state"], incomingMessage["message"]):
                logging.error("[%s]: Received state invalid." % self._log_tag)
                return False

            if not self._msg_checker.check_sensor_data_type(incomingMessage["payload"]["dataType"], incomingMessage["message"]):
                logging.error("[%s]: Received dataType invalid." % self._log_tag)
                return False

            if incomingMessage["payload"]["dataType"] != SensorDataType.NONE:
                if not self._msg_checker.check_sensor_data(incomingMessage["payload"]["data"],
                                                           incomingMessage["payload"]["dataType"],
                                                           incomingMessage["message"]):
                    logging.error("[%s]: Received data invalid." % self._log_tag)
                    return False

            serverTime = incomingMessage["serverTime"]

            sensorId = incomingMessage["payload"]["sensorId"]
            state = incomingMessage["payload"]["state"]
            dataType = incomingMessage["payload"]["dataType"]

            sensorData = None
            if dataType == SensorDataType.INT:
                sensorData = incomingMessage["payload"]["data"]
            elif dataType == SensorDataType.FLOAT:
                sensorData = incomingMessage["payload"]["data"]

        except Exception as e:
            logging.exception("[%s]: Received state change invalid." % self._log_tag)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": incomingMessage["message"],
                           "error": "received state change invalid"}
                self._communication.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        # sending state change response
        logging.debug("[%s]: Sending state change response message." % self._log_tag)
        try:
            payload = {"type": "response",
                       "result": "ok"}
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": "statechange",
                       "payload": payload}
            self._communication.send(json.dumps(message))

        except Exception as e:
            logging.exception("[%s]: Sending state change response failed." % self._log_tag)
            return False

        # handle received state change
        if self._event_handler.state_change(serverTime,
                                            sensorId,
                                            state,
                                            dataType,
                                            sensorData):
            return True

        return False

    def initialize(self) -> bool:
        """
        Function that initializes the communication channel to the server, for example,
        checks the version and authenticates the client.

        :return: success or failure
        """

        # Lock communication initialization to guarantee to only have one initialization at a time.
        with self._initialization_lock:

            # Do not initialize the communication anew if we have already a working communication channel.
            if self._communication.is_connected:
                return True

            if not self._communication.connect():
                self.close()
                return False

            # Build registration message.
            regMessage = MsgBuilder.build_reg_msg(self._description,
                                                  self._nodeType,
                                                  self._instance,
                                                  self._persistent)

            # First check version and authenticate.
            if not self._verify_version_and_auth(len(regMessage)):
                logging.error("[%s]: Version verification and authentication failed." % self._log_tag)
                self.close()
                return False

            # Second register node.
            if not self._register_node(regMessage):
                logging.error("[%s]: Registration failed." % self._log_tag)
                self.close()
                return False

            # get the initial status update from the server
            try:
                logging.debug("[%s]: Receiving initial status update." % self._log_tag)

                data = self._communication.recv()
                message = json.loads(data)
                # check if an error was received
                if "error" in message.keys():
                    logging.error("[%s]: Error received: '%s'." % (self._log_tag, message["error"],))
                    self.close()
                    return False

                # check if RTS was received
                # => acknowledge it
                if str(message["payload"]["type"]).upper() == "RTS":
                    receivedTransactionId = int(message["payload"]["id"])
                    messageSize = int(message["size"])

                    # received RTS (request to send) message
                    logging.debug("[%s]: Received RTS %s message." % (self._log_tag, receivedTransactionId))

                    logging.debug("[%s]: Sending CTS %s message." % (self._log_tag, receivedTransactionId))

                    # send CTS (clear to send) message
                    payload = {"type": "cts",
                               "id": receivedTransactionId}
                    utc_timestamp = int(time.time())
                    message = {"clientTime": utc_timestamp,
                               "message": str(message["message"]),
                               "payload": payload}
                    self._communication.send(json.dumps(message))

                    # After initiating transaction receive actual command.
                    data = ""
                    last_size = 0
                    while len(data) < messageSize:
                        data += self._communication.recv()

                        # Check if the size of the received data has changed.
                        # If not we detected a possible dead lock.
                        if last_size != len(data):
                            last_size = len(data)
                        else:
                            logging.error("[%s]: Possible dead lock "
                                          % self._log_tag
                                          + "detected while receiving data. Closing connection to server.")
                            self.close()
                            return False

                # if no RTS was received
                # => server does not stick to protocol
                # => terminate session
                else:
                    logging.error("[%s]: Did not receive RTS. Server sent: '%s'." % (self._log_tag, data))
                    self.close()
                    return False

            except Exception:
                logging.exception("[%s]: Receiving initial status update failed." % self._log_tag)
                self.close()
                return False

            # Extract message type
            try:
                message = json.loads(data)
                # check if an error was received
                if "error" in message.keys():
                    logging.error("[%s]: Error received: '%s'." % (self._log_tag, message["error"]))
                    self.close()
                    return False

                # check if the received type is the correct one
                if str(message["payload"]["type"]).upper() != "REQUEST":
                    logging.error("[%s]: request expected." % self._log_tag)

                    # send error message back
                    try:
                        utc_timestamp = int(time.time())
                        message = {"clientTime": utc_timestamp,
                                   "message": message["message"],
                                   "error": "request expected"}
                        self._communication.send(json.dumps(message))
                    except Exception as e:
                        pass

                    self.close()
                    return False

                # extract the command/message type of the message
                command = str(message["message"]).lower()

            except Exception:
                logging.exception("[%s]: Received data not valid: '%s'." % (self._log_tag, data))
                self.close()
                return False

            if command != "status":
                logging.error("[%s]: Receiving status update failed. Server sent: '%s'" % (self._log_tag, data))

                # send error message back
                try:
                    utc_timestamp = int(time.time())
                    message = {"clientTime": utc_timestamp,
                               "message": message["message"],
                               "error": "initial status update expected"}
                    self._communication.send(json.dumps(message))

                except Exception:
                    pass

                self.close()
                return False

            if not self._status_update_handler(message):
                logging.error("[%s]: Initial status update failed." % self._log_tag)
                self.close()
                return False

            # Set communication channel as established.
            self._communication.set_connected()

            # Handle connection initialized event.
            self._event_handler.new_connection()

            return True

    # This function handles the incoming messages from the server.
    def handle_requests(self):

        # Handle commands in an infinity loop.
        while True:

            data = self._communication.recv_request()
            if data is None:
                return

            # Extract request/message type.
            request = ""
            try:
                message = json.loads(data)
                # check if an error was received
                if "error" in message.keys():
                    logging.error("[%s]: Error received: '%s'."
                                  % (self._log_tag, message["error"]))

                    # clean up session before exiting
                    self.close()
                    return

                # check if the received type is the correct one
                if str(message["payload"]["type"]).lower() != "request":
                    logging.error("[%s]: Request expected." % self._log_tag)

                    # send error message back
                    try:
                        utc_timestamp = int(time.time())
                        message = {"clientTime": utc_timestamp,
                                   "message": message["message"],
                                   "error": "request expected"}
                        self._communication.send(json.dumps(message))
                    except Exception as e:
                        pass

                    # clean up session before exiting
                    self.close()
                    return

                # Extract the request/message type of the message.
                request = str(message["message"]).lower()

            except Exception as e:

                logging.exception("[%s]: Received data not valid: '%s'." % (self._log_tag, data))

                # clean up session before exiting
                self.close()
                return

            # Handle SENSORALERT request.
            if request == "sensoralert":
                if not self._sensorAlertHandler(message):
                    logging.error("[%s]: Receiving sensor alert failed."
                                  % self._log_tag)

                    # clean up session before exiting
                    self.close()
                    return

            # Handle STATUS request.
            elif request == "status":
                if not self._status_update_handler(message):
                    logging.error("[%s]: Receiving status update failed."
                                  % self._log_tag)

                    # clean up session before exiting
                    self.close()
                    return

            # Handle STATECHANGE request.
            elif request == "statechange":
                if not self._state_change_handler(message):
                    logging.error("[%s]: Receiving state change failed."
                                  % self._log_tag)

                    # clean up session before exiting
                    self.close()
                    return

            # Unkown request.
            else:
                logging.error("[%s]: Received unknown request. Server sent: %s" % (self._log_tag, data))

                try:
                    utc_timestamp = int(time.time())
                    message = {"clientTime": utc_timestamp,
                               "message": request,
                               "error": "unknown request/message type"}
                    self._communication.send(json.dumps(message))
                except Exception as e:
                    pass

                # clean up session before exiting
                self.close()
                return

    def reconnect(self) -> bool:
        """
        Closes the connection to the server and initializes a new connection.

        :return: success or failure
        """
        logging.info("[%s] Reconnecting to server." % self._log_tag)

        # clean up session before exiting
        self.close()

        return self.initialize()

    def exit(self):
        """
        Destroys the server communication object by setting the exit flag to shut down the thread and closes connection.
        NOTE: server communication object not usable afterwards.
        """
        # clean up session before exiting
        self.close()
        self._communication.exit()

    def close(self):
        """
        Closes the connection to the server.
        """
        # Closes communication channel to server.
        self._communication.close()

        # handle closing event
        self._event_handler.close_connection()

    def send_ping(self) -> bool:
        """
        Sends a keep alive (PING request) to the server to keep the connection alive and to check
        if the connection is still alive.

        :return: success or failure
        """
        pingMessage = MsgBuilder.build_ping_msg()

        promise = self._communication.send_request("ping", pingMessage)

        # TODO block at the moment when sending request until we checked the code works
        promise.is_finished(blocking=True)

        if not promise.was_successful():
            # clean up session before exiting
            self.close()
            return False

        return True

    def send_option(self,
                    optionType: str,
                    optionValue: float,
                    optionDelay: int = 0) -> bool:
        """
        This function sends an option change to the server for example
        to activate the alert system or deactivate it.

        :param optionType:
        :param optionValue:
        :param optionDelay:
        :return: success or failure
        """

        optionMessage = MsgBuilder.build_option_msg(optionType, optionValue, optionDelay)

        promise = self._communication.send_request("option", optionMessage)

        # TODO block at the moment when sending request until we checked the code works
        promise.is_finished(blocking=True)

        if not promise.was_successful():
            # clean up session before exiting
            self.close()
            return False

        return True
