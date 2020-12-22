#!/usr/bin/env python3

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
from typing import Dict, Any
from .core import Client
from .util import MsgBuilder
from .communication import Communication, Promise
from .eventHandler import EventHandler
from ..globalData import ManagerObjOption, ManagerObjNode, ManagerObjSensor, ManagerObjManager, ManagerObjAlert, \
    ManagerObjAlertLevel, ManagerObjSensorAlert
from ..globalData import SensorDataType, SensorObjSensorAlert, SensorObjStateChange
from ..globalData import GlobalData


# this class handles the communication with the server
class ServerCommunication(Communication):

    def __init__(self,
                 host: str,
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

        client = Client(self._host,
                        self._port,
                        self._server_ca_file,
                        self._client_cert_file,
                        self._client_key_file)
        super().__init__(client)

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

        # Set node type specific data.
        if self._nodeType.lower() == "manager": # TODO: Manager
            # Description of this manager.
            self._description = self._global_data.description

        elif self._nodeType.lower() == "sensor": # TODO: Sensor
            self._polling_sensors = self._global_data.sensors

        self._initialization_lock = threading.Lock()

    @property
    def event_handler(self) -> EventHandler:
        return self._event_handler

    @property
    def is_connected(self) -> bool:
        return self.has_channel

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
            self.send_raw(authMessage)

        except Exception:
            logging.exception("[%s]: Sending user credentials "
                              % self._log_tag
                              + "and version failed.")
            return False

        # get authentication response from server
        try:
            data = self.recv_raw()
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'."
                              % (self._log_tag, message["error"]))
                return False

            if str(message["message"]).lower() != "initialization":
                logging.error("[%s]: Wrong authentication message: '%s'."
                              % (self._log_tag, message["message"]))

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "initialization message expected"}
                    self.send_raw(json.dumps(message))
                except Exception:
                    pass

                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).lower() != "response":
                logging.error("[%s]: response expected." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "response expected"}
                    self.send_raw(json.dumps(message))
                except Exception:
                    pass

                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).lower() != "ok":
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
                    self.send_raw(json.dumps(message))
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
                self.send_raw(json.dumps(message))
            except Exception:
                pass

            return False

        return True

    def _register_node(self,
                       regMessage: str) -> bool:
        """
        Internal function to register the node.

        :param regMessage:
        :return: success or failure
        """
        # Send registration message.
        try:
            logging.debug("[%s]: Sending registration message." % self._log_tag)
            self.send_raw(regMessage)

        except Exception:
            logging.exception("[%s]: Sending registration message." % self._log_tag)
            return False

        # get registration response from server
        try:
            data = self.recv_raw()
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'." % (self._log_tag, message["error"]))
                return False

            if str(message["message"]).lower() != "initialization":
                logging.error("[%s]: Wrong registration message: '%s'."
                              % (self._log_tag, message["message"]))

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "initialization message expected"}
                    self.send_raw(json.dumps(message))
                except Exception:
                    pass

                return False

            # Check if the received type is the correct one.
            if str(message["payload"]["type"]).lower() != "response":
                logging.error("[%s]: response expected." % self._log_tag)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "response expected"}
                    self.send_raw(json.dumps(message))
                except Exception:
                    pass

                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).lower() != "ok":
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
            serverTime = incomingMessage["serverTime"]
            optionsRaw = incomingMessage["payload"]["options"]
            nodesRaw = incomingMessage["payload"]["nodes"]
            sensorsRaw = incomingMessage["payload"]["sensors"]
            managersRaw = incomingMessage["payload"]["managers"]
            alertsRaw = incomingMessage["payload"]["alerts"]
            alertLevelsRaw = incomingMessage["payload"]["alertLevels"]

        except Exception:
            logging.exception("[%s]: Received status invalid." % self._log_tag)
            return False

        logging.debug("[%s]: Received option count: %d." % (self._log_tag, len(optionsRaw)))

        # process received options
        for i in range(len(optionsRaw)):

            try:
                optionType = optionsRaw[i]["type"]
                optionValue = optionsRaw[i]["value"]

            except Exception:
                logging.exception("[%s]: Received option invalid." % self._log_tag)
                return False

            logging.debug("[%s]: Received option information: '%s':%d." % (self._log_tag, optionType, optionValue))

            option = ManagerObjOption()
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

            except Exception:
                logging.exception("[%s]: Received node invalid." % self._log_tag)
                return False

            logging.debug("[%s]: Received node information: %d:'%s':'%s':%d:%d."
                          % (self._log_tag, nodeId, hostname, nodeType, connected, persistent))

            node = ManagerObjNode()
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

            except Exception:
                logging.exception("[%s]: Received sensor invalid." % self._log_tag)
                return False

            logging.debug("[%s]: Received sensor information: %d:%d:%d:'%s':%d:%d."
                          % (self._log_tag, nodeId, sensorId, alertDelay, description, lastStateUpdated, state))

            sensor = ManagerObjSensor()
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

            except Exception:
                logging.exception("[%s]: Received manager invalid." % self._log_tag)
                return False

            logging.debug("[%s]: Received manager information: %d:%d:'%s'."
                          % (self._log_tag, nodeId, managerId, description))

            manager = ManagerObjManager()
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

            except Exception:
                logging.exception("[%s]: Received alert invalid." % self._log_tag)
                return False

            logging.debug("[%s]: Received alert information: %d:%d:'%s'."
                          % (self._log_tag, nodeId, alertId, description))

            alert = ManagerObjAlert()
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
                instrumentation_active = alertLevelsRaw[i]["instrumentation_active"]

                if instrumentation_active:
                    instrumentation_cmd = alertLevelsRaw[i]["instrumentation_cmd"]
                    instrumentation_timeout = alertLevelsRaw[i]["instrumentation_timeout"]

                else:
                    instrumentation_cmd = None
                    instrumentation_timeout = None

            except Exception:
                logging.exception("[%s]: Received alertLevel invalid." % self._log_tag)
                return False

            logging.debug("[%s]: Received alertLevel information: %d:'%s':%d."
                          % (self._log_tag, level, name, triggerAlways))

            alertLevel = ManagerObjAlertLevel()
            alertLevel.level = level
            alertLevel.name = name
            alertLevel.triggerAlways = triggerAlways
            alertLevel.instrumentation_active = instrumentation_active
            alertLevel.instrumentation_cmd = instrumentation_cmd
            alertLevel.instrumentation_timeout = instrumentation_timeout
            alertLevels.append(alertLevel)

        # handle received status update
        if not self._event_handler.status_update(serverTime,
                                                 options,
                                                 nodes,
                                                 sensors,
                                                 managers,
                                                 alerts,
                                                 alertLevels):
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
        sensorAlert = ManagerObjSensorAlert()
        sensorAlert.timeReceived = int(time.time())
        try:
            serverTime = incomingMessage["serverTime"]

            # always -1 when no sensor is responsible for sensor alert
            sensorAlert.sensorId = incomingMessage["payload"]["sensorId"]

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

        except Exception:
            logging.exception("[%s]: Received sensor alert invalid." % self._log_tag)
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
            serverTime = incomingMessage["serverTime"]

            sensorId = incomingMessage["payload"]["sensorId"]
            state = incomingMessage["payload"]["state"]
            dataType = incomingMessage["payload"]["dataType"]

            sensorData = None
            if dataType == SensorDataType.INT:
                sensorData = incomingMessage["payload"]["data"]
            elif dataType == SensorDataType.FLOAT:
                sensorData = incomingMessage["payload"]["data"]

        except Exception:
            logging.exception("[%s]: Received state change invalid." % self._log_tag)
            return False

        # handle received state change
        if self._event_handler.state_change(serverTime,
                                            sensorId,
                                            state,
                                            dataType,
                                            sensorData):
            return True

        return False

    def close(self):
        """
        Closes the connection to the server.
        """
        # Closes communication channel to server.
        super().close()

        # handle closing event
        self._event_handler.close_connection()

    def exit(self):
        """
        Destroys the server communication object by setting the exit flag to shut down the thread and closes connection.
        NOTE: server communication object not usable afterwards.
        """
        # clean up session before exiting
        self.close()
        super().exit()

    def handle_requests(self):
        """
        Handles received requests by server in a loop. Returns if an error is encountered.

        :return:
        """

        # Handle commands in an infinity loop.
        while True:

            if not self.has_channel:
                return

            # Exit if we are requested to.
            if self._exit_flag:
                if self.has_channel:
                    self.close()
                return

            message = self.recv_request()
            if message is None:
                self.close()
                return
            request = message["message"]

            # Handle SENSORALERT request.
            if request.lower() == "sensoralert":
                if not self._sensorAlertHandler(message):
                    logging.error("[%s]: Receiving sensor alert failed."
                                  % self._log_tag)

                    # clean up session before exiting
                    self.close()
                    return

            # Handle STATUS request.
            elif request.lower() == "status":
                if not self._status_update_handler(message):
                    logging.error("[%s]: Receiving status update failed."
                                  % self._log_tag)

                    # clean up session before exiting
                    self.close()
                    return

            # Handle STATECHANGE request.
            elif request.lower() == "statechange":
                if not self._state_change_handler(message):
                    logging.error("[%s]: Receiving state change failed."
                                  % self._log_tag)

                    # clean up session before exiting
                    self.close()
                    return

            # Unkown request.
            else:
                logging.error("[%s]: Received unknown request. Server sent: %s" % (self._log_tag, str(message)))

                # clean up session before exiting
                self.close()
                return

    def initialize(self) -> bool:
        """
        Function that initializes the communication channel to the server, for example,
        checks the version and authenticates the client.

        :return: success or failure
        """

        # Lock communication initialization to guarantee to only have one initialization at a time.
        with self._initialization_lock:

            # Do not initialize the communication anew if we have already a working communication channel.
            if self.has_channel:
                return True

            if not self.connect():
                # Do not close the connection since it was not established yet.
                return False

            # Build registration message.
            reg_message = ""
            if self._nodeType.lower() == "manager":
                reg_message = MsgBuilder.build_reg_msg_manager(self._description,
                                                              self._nodeType,
                                                              self._instance,
                                                              self._persistent)

            elif self._nodeType.lower() == "sensor":
                reg_message = MsgBuilder.build_reg_msg_sensor(self._polling_sensors,
                                                             self._nodeType,
                                                             self._instance,
                                                             self._persistent)

            # First check version and authenticate.
            if not self._verify_version_and_auth(len(reg_message)):
                logging.error("[%s]: Version verification and authentication failed." % self._log_tag)
                self.close()
                return False

            # Second register node.
            if not self._register_node(reg_message):
                logging.error("[%s]: Registration failed." % self._log_tag)
                self.close()
                return False

            # Set communication channel as established.
            self.set_connected()

            # Nodes of type "manager" receive an initial status update when connecting to the server.
            if self._nodeType == "manager":

                logging.debug("[%s]: Receiving initial status update." % self._log_tag)

                message = self.recv_request()
                message_type = message["message"]
                if message_type != "status":
                    logging.error("[%s]: Receiving status update failed. Server sent: '%s'" % (self._log_tag, str(message)))

                    # send error message back
                    try:
                        utc_timestamp = int(time.time())
                        message = {"clientTime": utc_timestamp,
                                   "message": message_type,
                                   "error": "initial status update expected"}
                        self.send_raw(json.dumps(message))

                    except Exception:
                        pass

                    self.close()
                    return False

                if not self._status_update_handler(message):
                    logging.error("[%s]: Initial status update failed." % self._log_tag)
                    self.close()
                    return False

            # Handle connection initialized event.
            self._event_handler.new_connection()

            return True

    def reconnect(self) -> bool:
        """
        Closes the connection to the server and initializes a new connection.

        :return: success or failure
        """
        logging.info("[%s] Reconnecting to server." % self._log_tag)

        # Clean up session before reconnecting if it exists.
        if self.has_channel:
            self.close()

        return self.initialize()

    # TODO: Manager
    def send_option(self,
                    optionType: str,
                    optionValue: float,
                    optionDelay: int = 0) -> Promise:
        """
        This function sends an option change to the server for example
        to activate the alert system or deactivate it.

        :param optionType:
        :param optionValue:
        :param optionDelay:
        :return: Promise that the request will be sent and that contains the state of the send request
        """

        option_message = MsgBuilder.build_option_msg(optionType, optionValue, optionDelay)

        return self.send_request("option", option_message)

    def send_ping(self) -> Promise:
        """
        Sends a keep alive (PING request) to the server to keep the connection alive and to check
        if the connection is still alive.

        :return: Promise that the request will be sent and that contains the state of the send request
        """
        ping_message = MsgBuilder.build_ping_msg()

        return self.send_request("ping", ping_message)

    # TODO: Sensor
    def send_sensor_alert(self,
                          sensor_alert: SensorObjSensorAlert) -> Promise:
        """
        This function sends a sensor alert to the server.

        :param sensor_alert:
        :return: Promise that the request will be sent and that contains the state of the send request
        """

        sensor_alert_message = MsgBuilder.build_sensor_alert_msg_sensor(sensor_alert)

        return self.send_request("sensoralert", sensor_alert_message)

    # TODO: Sensor
    def send_state_change(self,
                          state_change: SensorObjStateChange) -> Promise:
        """
        This function sends a state change to the server for example to update the sensor state or data.

        :param state_change:
        :return: Promise that the request will be sent and that contains the state of the send request
        """

        state_change_message = MsgBuilder.build_state_change_msg_sensor(state_change)

        return self.send_request("statechange", state_change_message)

    # TODO: Sensor
    def send_sensors_status_update(self) -> Promise:
        """
        This function sends a status update of all sensors to the server.

        :return: Promise that the request will be sent and that contains the state of the send request
        """

        status_update_message = MsgBuilder.build_status_update_msg_sensor(self._polling_sensors)

        return self.send_request("status", status_update_message)
