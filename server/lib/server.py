#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import ssl
import socket
import threading
import socketserver
import time
import logging
import os
import random
import json
from .localObjects import SensorDataType, Sensor, SensorData, SensorAlert, Option, Alert, Manager, Node, AlertLevel, \
    Profile, SensorDataGPS
from .globalData import GlobalData
from typing import Optional, Dict, Tuple, Any, List, Type

BUFSIZE = 4096


# this class handles the communication with the incoming client connection
class ClientCommunication:

    def __init__(self,
                 sslSocket: ssl.SSLSocket,
                 clientAddress: str,
                 clientPort: int,
                 globalData: GlobalData):
        self.sslSocket = sslSocket
        self.clientAddress = clientAddress
        self.clientPort = clientPort

        # get global configured data
        self.globalData = globalData
        self.serverVersion = self.globalData.version
        self.serverRev = self.globalData.rev
        self.storage = self.globalData.storage
        self.userBackend = self.globalData.userBackend
        self.sensorAlertExecuter = self.globalData.sensorAlertExecuter
        self.managerUpdateExecuter = self.globalData.managerUpdateExecuter
        self.alertLevels = self.globalData.alertLevels  # type: List[AlertLevel]
        self.profiles = self.globalData.profiles  # type: List[Profile]
        self.connectionWatchdog = self.globalData.connectionWatchdog
        self.serverSessions = self.globalData.serverSessions
        self._option_executer = self.globalData.option_executer

        # Time the last message was received by the server. Since the 
        # connection counts as a message, set it to the current time
        # (otherwise the connectionWatchdog might close the connection).
        self.lastRecv = int(time.time())

        # username that is used by the client to authorize itself
        self.username = None

        # Set of alert levels (integer) the client responds to
        # (in case of a sensor client, all alert levels the client triggers,
        # in case of an alert client, all alert levels the client handles,
        # in case of a manager client, all alert levels).
        self.clientAlertLevels = set()

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # type of the client (sensor/alert/manager)
        self.nodeType = None

        # instance of the client (i.e. sensorClientPing)
        self.instance = None

        # hostname of the client
        self.hostname = None

        # Flag that indicates if this node is registered as persistent.
        self.persistent = 0

        # version and revision of client
        self.clientVersion = None
        self.clientRev = None

        # the id of the client
        self.nodeId = None

        # count of all sensors that are managed by the client
        # (only set if the client is of the type "sensor")
        self.sensorCount = 0

        # this lock is used to only allow one thread to use the communication
        self.connectionLock = threading.BoundedSemaphore(1)

        # a flag that signals that the initialization process
        # of the client is finished
        self.clientInitialized = False

        # time the server is waiting on receives until a time out occurs
        self.serverReceiveTimeout = self.globalData.serverReceiveTimeout

        # Flag that states if the server is already trying to initiate a
        # transaction with the client.
        self.transactionInitiation = False

        # List of all sensors this client manages (is only used if the client
        # is of type "sensor").
        self.sensors = list()

        # Needed for logging.
        self.logger = self.globalData.logger
        self.loggerFileHandler = None

    def _acquireLock(self):
        """
        internal function that acquires the lock
        """
        self.connectionLock.acquire()

    def _releaseLock(self):
        """
        internal function that releases the lock
        """
        self.connectionLock.release()

    def _send(self, data: str):
        """
        Wrapper around socket send to handle bytes/string encoding.

        :param data:
        """
        self.sslSocket.send(data.encode("ascii"))

    def _recv(self, bufsize: int = BUFSIZE) -> str:
        """
        Wrapper around socket recv to handle bytes/string encoding.

        :return:
        """
        return self.sslSocket.recv(bufsize).decode("ascii")

    def _checkMsgAlertDelay(self,
                            alertDelay: int,
                            messageType: str) -> bool:
        """
        Internal function to check sanity of the alertDelay.

        :param alertDelay:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(alertDelay, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "alertDelay not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgAlertLevels(self,
                             alertLevels: List[int],
                             messageType: str) -> bool:
        """
        Internal function to check sanity of the alertLevels.

        :param alertLevels:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(alertLevels, list):
            isCorrect = False

        elif not all(isinstance(item, int) for item in alertLevels):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "alertLevels not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgChangeState(self,
                             changeState: bool,
                             messageType: str) -> bool:
        """
        Internal function to check sanity of the changeState.

        :param changeState:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(changeState, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "changeState not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgClientAlertId(self,
                               clientAlertId: int,
                               messageType: str) -> bool:
        """
        Internal function to check sanity of the clientAlertId.

        :param clientAlertId:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(clientAlertId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "clientAlertId not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgClientSensorId(self,
                                clientSensorId: int,
                                messageType: str) -> bool:
        """
        Internal function to check sanity of the clientSensorId.

        :param clientSensorId:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(clientSensorId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "clientSensorId not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgDescription(self,
                             description: str,
                             messageType: str) -> bool:
        """
        Internal function to check sanity of the description.

        :param description:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(description, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "description not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgHasLatestData(self,
                               hasLatestData: bool,
                               messageType: str) -> bool:
        """
        Internal function to check sanity of the hasLatestData.

        :param hasLatestData:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(hasLatestData, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "hasLatestData not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgHostname(self,
                          hostname: str,
                          messageType: str) -> bool:
        """
        Internal function to check sanity of the hostname.

        :param hostname:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(hostname, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "hostname not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgInstance(self,
                          instance: str,
                          messageType: str) -> bool:
        """
        Internal function to check sanity of the instance.

        :param instance:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(instance, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "instance not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgNodeType(self,
                          nodeType: str,
                          messageType: str) -> bool:
        """
        Internal function to check sanity of the nodeType.

        :param nodeType:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(nodeType, str):
            isCorrect = False

        nodeTypes = {"alert", "manager", "sensor"}
        if nodeType not in nodeTypes:
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "nodeType not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgOptionType(self,
                            optionType: str,
                            messageType: str) -> bool:
        """
        Internal function to check sanity of the optionType.

        :param optionType:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(optionType, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "optionType not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgOptionTimeDelay(self,
                                 timeDelay: int,
                                 messageType: str) -> bool:
        """
        Internal function to check sanity of the option timeDelay.

        :param timeDelay:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(timeDelay, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "timeDelay not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgOptionValue(self,
                             value: int,
                             messageType: str) -> bool:
        """
        Internal function to check sanity of the option value.

        :param value:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(value, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "value not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgPersistent(self,
                            persistent: int,
                            messageType: str) -> bool:
        """
        Internal function to check sanity of the persistence.

        :param persistent:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(persistent, int):
            isCorrect = False

        if not (persistent == 0 or persistent == 1):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "persistent not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgRegAlertsList(self,
                               alerts: Dict[str, Any],
                               messageType: str) -> bool:
        """
        Internal function to check sanity of the registration alerts list.

        :param alerts:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(alerts, list):
            isCorrect = False

        # Check each alert if correct.
        for alert in alerts:

            if not isinstance(alert, dict):
                isCorrect = False
                break

            if"alertLevels" not in alert.keys():
                isCorrect = False
                break

            elif not self._checkMsgAlertLevels(alert["alertLevels"],
                                               messageType):
                isCorrect = False
                break

            if "clientAlertId" not in alert.keys():
                isCorrect = False
                break

            elif not self._checkMsgClientAlertId(alert["clientAlertId"],
                                                 messageType):
                isCorrect = False
                break

            if "description" not in alert.keys():
                isCorrect = False
                break

            elif not self._checkMsgDescription(alert["description"],
                                               messageType):
                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "alerts list not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgRegManagerDict(self,
                                manager: Dict[str, Any],
                                messageType: str) -> bool:
        """
        Internal function to check sanity of the registration manager dictionary.

        :param manager:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(manager, dict):
            isCorrect = False

        else:

            if "description" not in manager.keys():
                isCorrect = False

            elif not self._checkMsgDescription(manager["description"],
                                               messageType):
                isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "manager dictionary not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgRegSensorsList(self,
                                sensors: Dict[str, Any],
                                messageType: str) -> bool:
        """
        Internal function to check sanity of the registration sensors list.

        :param sensors:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(sensors, list):
            isCorrect = False

        # Check each sensor if correct.
        for sensor in sensors:

            if not isinstance(sensor, dict):
                isCorrect = False
                break

            if "alertDelay" not in sensor.keys():
                isCorrect = False
                break

            elif not self._checkMsgAlertDelay(sensor["alertDelay"],
                                              messageType):
                isCorrect = False
                break

            if "alertLevels" not in sensor.keys():
                isCorrect = False
                break

            elif not self._checkMsgAlertLevels(sensor["alertLevels"],
                                               messageType):
                isCorrect = False
                break

            if "clientSensorId" not in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgClientSensorId(sensor["clientSensorId"],
                                                  messageType):
                isCorrect = False
                break

            if "dataType" not in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgSensorDataType(sensor["dataType"],
                                                  messageType):
                isCorrect = False
                break

            sensorDataType = sensor["dataType"]
            if sensorDataType != SensorDataType.NONE:
                if "data" not in sensor.keys():
                    isCorrect = False
                    break

                elif not self._checkMsgSensorData(sensor["data"],
                                                  sensorDataType,
                                                  messageType):
                    isCorrect = False
                    break

            if "description" not in sensor.keys():
                isCorrect = False
                break

            elif not self._checkMsgDescription(sensor["description"],
                                               messageType):
                isCorrect = False
                break

            if "state" not in sensor.keys():
                isCorrect = False
                break

            elif not self._checkMsgState(sensor["state"],
                                         messageType):
                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "sensors list not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgSensorData(self,
                            data: Any,
                            dataType: int,
                            messageType: str) -> bool:
        """
        Internal function to check sanity of the sensor data.

        :param data:
        :param dataType:
        :param messageType:
        :return:
        """
        isCorrect = True
        if dataType == SensorDataType.NONE and data is not None:
            isCorrect = False

        elif dataType == SensorDataType.INT and not isinstance(data, int):
            isCorrect = False

        elif dataType == SensorDataType.FLOAT and not isinstance(data, float):
            isCorrect = False

        elif (dataType == SensorDataType.GPS
              and not (isinstance(data, dict)
                       and all([x in data.keys() for x in ["lat", "lon", "utctime"]])
                       and isinstance(data["lat"], float)
                       and isinstance(data["lon"], float)
                       and isinstance(data["utctime"], int))):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "data not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgSensorDataType(self,
                                dataType: int,
                                messageType: str) -> bool:
        """
        Internal function to check sanity of the sensor data type.

        :param dataType:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(dataType, int):
            isCorrect = False

        elif not (SensorDataType.NONE == dataType
                  or SensorDataType.INT == dataType
                  or SensorDataType.FLOAT == dataType
                  or SensorDataType.GPS == dataType):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "dataType not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgStatusSensorsList(self,
                                   sensors: Dict[str, Any],
                                   messageType: str) -> bool:
        """
        Internal function to check sanity of the status sensors list.

        :param sensors:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(sensors, list):
            isCorrect = False

        # Check each sensor if correct.
        for sensor in sensors:

            if not isinstance(sensor, dict):
                isCorrect = False
                break

            if "clientSensorId" not in sensor.keys():
                isCorrect = False
                break

            elif not self._checkMsgClientSensorId(sensor["clientSensorId"],
                                                  messageType):
                isCorrect = False
                break

            if "dataType" not in sensor.keys():
                isCorrect = False
                break

            elif not self._checkMsgSensorDataType(sensor["dataType"],
                                                  messageType):
                isCorrect = False
                break

            sensorDataType = sensor["dataType"]
            if sensorDataType != SensorDataType.NONE:
                if "data" not in sensor.keys():
                    isCorrect = False
                    break

                elif not self._checkMsgSensorData(sensor["data"],
                                                  sensorDataType,
                                                  messageType):
                    isCorrect = False
                    break

            if "state" not in sensor.keys():
                isCorrect = False
                break

            elif not self._checkMsgState(sensor["state"],
                                         messageType):
                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "sensors list not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _checkMsgState(self,
                       state: int,
                       messageType: str) -> bool:
        """
        Internal function to check sanity of the state.

        :param state:
        :param messageType:
        :return:
        """
        isCorrect = True
        if not isinstance(state, int):
            isCorrect = False

        elif state != 0 and state != 1:
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                message = {"message": messageType,
                           "error": "state not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        return True

    def _cleanUpSessionForClosing(self):
        """
        this internal function cleans up the session before releasing the lock and exiting/closing the session
        """
        # mark node as not connected
        self.storage.markNodeAsNotConnected(self.nodeId, logger=self.logger)

        # set flag that the initialization process of
        # the client is finished as false
        self.clientInitialized = False

        # wake up manager update executer
        self.managerUpdateExecuter.force_status_update()

    def _initiateTransaction(self,
                             messageType: str,
                             messageSize: int,
                             acquireLock: bool = False) -> bool:
        """
        this internal function that tries to initiate a transaction with the client
        (and acquires a lock if it is told to do so)

        :param messageType:
        :param messageSize:
        :param acquireLock:
        :return:
        """
        # try to get the exclusive state to be allowed to initiate a
        # transaction with the client
        while True:

            # check if locks should be handled or not
            if acquireLock:
                self._acquireLock()

            # check if another thread is already trying to initiate a
            # transaction with the client
            if self.transactionInitiation:

                self.logger.warning("[%s]: Transaction initiation "
                                    % self.fileName
                                    + "already tried by another thread. Backing off.")

                # check if locks should be handled or not
                if acquireLock:
                    self._releaseLock()

                # wait 0.5 seconds before trying again to initiate a
                # transaction with the client
                time.sleep(0.5)
                continue

            # if transaction flag is not set
            # => start to initiate transaction with client
            else:
                self.logger.debug("[%s]: Got exclusive transaction initiation state (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # set transaction initiation flag to true
                # to signal other threads that a transaction is already
                # tried to initiate
                self.transactionInitiation = True
                break

        # now we are in a exclusive state to initiate a transaction with
        # the client
        while True:

            # generate a random "unique" transaction id
            # for this transaction
            transactionId = random.randint(0, 0xffffffff)

            # send RTS (request to send) message
            self.logger.debug("[%s]: Sending RTS %d message (%s:%d)."
                              % (self.fileName, transactionId, self.clientAddress, self.clientPort))
            try:
                payload = {"type": "rts",
                           "id": transactionId}
                message = {"size": messageSize,
                           "message": messageType,
                           "payload": payload}
                self._send(json.dumps(message))

            except Exception as e:
                self.logger.exception("[%s]: Sending RTS failed (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))

                # set transaction initiation flag as false so other
                # threads can try to initiate a transaction with the client
                self.transactionInitiation = False

                # check if locks should be handled or not
                if acquireLock:
                    self._releaseLock()

                return False

            # get CTS (clear to send) message
            self.logger.debug("[%s]: Receiving CTS (%s:%d)." % (self.fileName, self.clientAddress, self.clientPort))

            receivedTransactionId = -1
            receivedMessageType = ""
            receivedPayloadType = ""
            try:
                data = self._recv()
                message = json.loads(data)

                # check if an error was received
                # (only log error)
                if "error" in message.keys():
                    self.logger.error("[%s]: Error received: '%s' (%s:%d)."
                                      % (self.fileName, message["error"], self.clientAddress, self.clientPort))

                # if no error => extract values from message
                else:
                    receivedTransactionId = int(message["payload"]["id"])
                    receivedMessageType = str(message["message"])
                    receivedPayloadType = str(message["payload"]["type"]).upper()

            except Exception as e:
                self.logger.exception("[%s]: Receiving CTS failed (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))

                # set transaction initiation flag as false so other
                # threads can try to initiate a transaction with the client
                self.transactionInitiation = False

                # check if locks should be handled or not
                if acquireLock:
                    self._releaseLock()

                return False

            # check if RTS is acknowledged by a CTS
            # => exit transaction initiation loop
            if (receivedTransactionId == transactionId
                    and receivedMessageType == messageType
                    and receivedPayloadType == "CTS"):

                self.logger.debug("[%s]: Initiate transaction succeeded (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # set transaction initiation flag as false so other
                # threads can try to initiate a transaction with the client
                self.transactionInitiation = False
                break

            # if RTS was not acknowledged
            # => release lock and backoff for a random time then retry again
            else:

                self.logger.warning("[%s]: Initiate transaction failed. Backing off (%s:%d)."
                                    % (self.fileName, self.clientAddress, self.clientPort))

                # check if locks should be handled or not
                if acquireLock:
                    self._releaseLock()

                # backoff random time between 0 and 0.5 second
                backoffTime = float(random.randint(0, 50)) / 100
                time.sleep(backoffTime)

                # check if locks should be handled or not
                if acquireLock:
                    self._acquireLock()

        return True

    def _buildSensorAlertMessage(self,
                                 sensorAlert: SensorAlert) -> str:
        """
        Internal function that builds the sensor alert message.

        :param sensorAlert:
        :return:
        """
        # Differentiate payload of message when data transfer is
        # activated or not.
        if sensorAlert.hasOptionalData:
            payload = {"type": "request",
                       "sensorId": sensorAlert.sensorId,
                       "state": sensorAlert.state,
                       "alertLevels": sensorAlert.triggeredAlertLevels,
                       "description": sensorAlert.description,
                       "hasOptionalData": True,
                       "optionalData": sensorAlert.optionalData,
                       "changeState": sensorAlert.changeState,
                       "hasLatestData": sensorAlert.hasLatestData,
                       "dataType": sensorAlert.dataType
                       }

            if sensorAlert.dataType == SensorDataType.GPS:
                payload["data"] = sensorAlert.sensorData.convert_to_dict()

            else:
                payload["data"] = sensorAlert.sensorData
        else:
            payload = {"type": "request",
                       "sensorId": sensorAlert.sensorId,
                       "state": sensorAlert.state,
                       "alertLevels": sensorAlert.triggeredAlertLevels,
                       "description": sensorAlert.description,
                       "hasOptionalData": False,
                       "changeState": sensorAlert.changeState,
                       "hasLatestData": sensorAlert.hasLatestData,
                       "dataType": sensorAlert.dataType
                       }

            if sensorAlert.dataType == SensorDataType.GPS:
                payload["data"] = sensorAlert.sensorData.convert_to_dict()

            else:
                payload["data"] = sensorAlert.sensorData

        utc_time = int(time.time())
        message = {"msgTime": utc_time,
                   "message": "sensoralert",
                   "payload": payload}
        return json.dumps(message)

    def _build_profile_change_message(self, profile: Profile) -> str:
        """
        Internal function that builds the profile change message.

        :return:
        """
        payload = {"type": "request",
                   "profileId": profile.profileId,
                   "name": profile.name}
        utc_time = int(time.time())
        message = {"msgTime": utc_time,
                   "message": "profilechange",
                   "payload": payload}

        return json.dumps(message)

    def _buildStateChangeMessage(self,
                                 sensorId: int,
                                 state: int,
                                 dataType: int,
                                 data: Any) -> str:
        """
        Internal function that builds the state change message.

        :param sensorId:
        :param state:
        :param dataType:
        :param data:
        :return:
        """
        payload = {"type": "request",
                   "sensorId": sensorId,
                   "state": state,
                   "dataType": dataType}

        if dataType == SensorDataType.GPS:
            payload["data"] = data.convert_to_dict()

        elif dataType != SensorDataType.NONE:
            payload["data"] = data

        utc_time = int(time.time())
        message = {"msgTime": utc_time,
                   "message": "statechange",
                   "payload": payload}

        return json.dumps(message)

    def _buildAlertSystemStateMessage(self) -> Optional[str]:
        """
        Internal function that builds the alert system state message.

        :return:
        """
        # Get a list from database of
        # list[0] = list(option objects)
        # list[1] = list(node objects)
        # list[2] = list(sensor objects)
        # list[3] = list(manager objects)
        # list[4] = list(alert objects)
        # or None
        alertSystemInformation = self.storage.getAlertSystemInformation(logger=self.logger)
        if alertSystemInformation is None:
            self.logger.error("[%s]: Getting alert system information from database failed (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": "status",
                           "error": "not able to get alert system data from database"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return None
        optionList = alertSystemInformation[0]  # type: List[Option]
        nodesList = alertSystemInformation[1]  # type: List[Node]
        sensorList = alertSystemInformation[2]  # type: List[Sensor]
        managerList = alertSystemInformation[3]  # type: List[Manager]
        alertList = alertSystemInformation[4]  # type: List[Alert]

        # Generating options list.
        options = list()
        for optionObj in optionList:
            tempDict = {"type": optionObj.type,
                        "value": optionObj.value}
            options.append(tempDict)

        # Generating nodes list.
        nodes = list()
        for nodeObj in nodesList:
            tempDict = {"nodeId": nodeObj.id,
                        "hostname": nodeObj.hostname,
                        "username": nodeObj.username,
                        "nodeType": nodeObj.nodeType,
                        "instance": nodeObj.instance,
                        "connected": nodeObj.connected,
                        "version": nodeObj.version,
                        "rev": nodeObj.rev,
                        "persistent": nodeObj.persistent}

            nodes.append(tempDict)

        # Generating sensors list.
        sensors = list()
        for sensorObj in sensorList:
            tempDict = {"sensorId": sensorObj.sensorId,
                        "nodeId": sensorObj.nodeId,
                        "clientSensorId": sensorObj.clientSensorId,
                        "description": sensorObj.description,
                        "state": sensorObj.state,
                        "lastStateUpdated": sensorObj.lastStateUpdated,
                        "alertDelay": sensorObj.alertDelay,
                        "alertLevels": sensorObj.alertLevels,
                        "dataType": sensorObj.dataType}

            if sensorObj.dataType == SensorDataType.GPS:
                tempDict["data"] = sensorObj.data.convert_to_dict()

            else:
                tempDict["data"] = sensorObj.data

            sensors.append(tempDict)

        # Generating managers list.
        managers = list()
        for managerObj in managerList:
            tempDict = {"managerId": managerObj.managerId,
                        "nodeId": managerObj.nodeId,
                        "description": managerObj.description}
            managers.append(tempDict)

        # Generating alerts list.
        alerts = list()
        for alertObj in alertList:
            tempDict = {"alertId": alertObj.alertId,
                        "nodeId": alertObj.nodeId,
                        "clientAlertId": alertObj.clientAlertId,
                        "description": alertObj.description,
                        "alertLevels": alertObj.alertLevels}
            alerts.append(tempDict)

        # Generating profiles list
        profiles = list()
        for profile_obj in self.profiles:
            temp_dict = {"profileId": profile_obj.profileId,
                         "name": profile_obj.name}
            profiles.append(temp_dict)

        # Generating alertLevels list.
        alertLevels = list()
        for i in range(len(self.alertLevels)):
            tempDict = {"alertLevel": self.alertLevels[i].level,
                        "name": self.alertLevels[i].name,
                        "profiles": self.alertLevels[i].profiles,
                        "instrumentation_active": self.alertLevels[i].instrumentation_active,
                        "instrumentation_cmd": self.alertLevels[i].instrumentation_cmd,
                        "instrumentation_timeout": self.alertLevels[i].instrumentation_timeout}
            alertLevels.append(tempDict)

        self.logger.debug("[%s]: Sending status message (%s:%d)." % (self.fileName, self.clientAddress, self.clientPort))

        payload = {"type": "request",
                   "options": options,
                   "profiles": profiles,
                   "nodes": nodes,
                   "sensors": sensors,
                   "managers": managers,
                   "alerts": alerts,
                   "alertLevels": alertLevels}
        utc_time = int(time.time())
        message = {"msgTime": utc_time,
                   "message": "status",
                   "payload": payload}

        return json.dumps(message)

    def _initializeCommunication(self) -> bool:
        """
        Internal function to initialize communication with the client
        (Authentication, Version verification, Registration).

        :return:
        """
        # First verify client/server version and authenticate client.
        result, messageSize = self._verifyVersionAndAuthenticate()
        if not result:
            self.logger.error("[%s]: Version verification and authentication failed (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))
            return False

        # Second register client.
        if not self._registerClient(messageSize):
            self.logger.error("[%s]: Client registration failed (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))
            return False

        return True

    def _initializeLogger(self):
        """
        Internal function to initialize an own logger instance for this connection.
        """
        self.logger = logging.getLogger("client_" + self.username)
        fh = logging.FileHandler(self.globalData.logdir + "/client_" + self.username + ".log")
        fh.setLevel(self.globalData.loglevel)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', '%m/%d/%Y %H:%M:%S')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.loggerFileHandler = fh

        # Set the logger instance also for the server session.
        for serverSession in self.serverSessions:
            if serverSession.clientComm == self:
                serverSession.setLogger(self.logger)
                break

    def _finalizeLogger(self):
        """
        Internal function to finalize an own logger instance for this connection.
        """
        if self.loggerFileHandler is not None:
            self.logger.debug("[%s]: Closing log file (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))
            self.logger.removeHandler(self.loggerFileHandler)
            self.loggerFileHandler.close()
            self.loggerFileHandler = None
        self.logger = self.globalData.logger

    def _verifyVersionAndAuthenticate(self) -> Tuple[bool, int]:
        """
        Internal function to verify the server/client version and authenticate the client.

        :return:
        """
        # get version and credentials from client
        try:
            data = self._recv()
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                self.logger.error("[%s]: Error received: '%s' (%s:%d)."
                                  % (self.fileName, message["error"], self.clientAddress, self.clientPort))
                return False, 0

        except Exception as e:
            self.logger.exception("[%s]: Receiving authentication failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False, 0

        # Extract message header of received message.
        try:
            messageSize = int(message["size"])

        except Exception as e:
            self.logger.exception("[%s]: Authentication message malformed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # Send error message back.
            try:
                message = {"message": message["message"],
                           "error": "message header malformed"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False, 0

        # check if an authentication message was received
        try:
            if str(message["message"]).upper() != "initialization".upper():
                self.logger.error("[%s]: Wrong authentication message: '%s' (%s:%d)."
                                  % (self.fileName, message["message"], self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "initialization message expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False, 0

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "REQUEST":
                self.logger.error("[%s]: request expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "request expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False, 0

        except Exception as e:

            self.logger.exception("[%s]: Message not valid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "message not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False, 0

        # verify version
        try:
            self.clientVersion = float(message["payload"]["version"])
            self.clientRev = int(message["payload"]["rev"])

            # check if used protocol version is compatible
            if int(self.serverVersion * 10) != int(self.clientVersion * 10):

                self.logger.error("[%s]: Version not compatible. Client has version: '%.3f-%d' "
                                  % (self.fileName, self.clientVersion, self.clientRev)
                                  + "and server has '%.3f-%d' (%s:%d)"
                                  % (self.serverVersion, self.serverRev, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "version not compatible"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False, 0

        except Exception as e:
            self.logger.exception("[%s]: Version not valid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "version not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False, 0

        self.logger.debug("[%s]: Received client version: '%.3f-%d' (%s:%d)."
                          % (self.fileName, self.clientVersion, self.clientRev, self.clientAddress, self.clientPort))

        # get user credentials
        try:
            self.username = str(message["payload"]["username"])
            password = str(message["payload"]["password"])

        except Exception as e:
            self.logger.exception("[%s]: No user credentials (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "no user credentials"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False, 0

        self.logger.debug("[%s]: Received username and password for '%s' (%s:%d)."
                          % (self.fileName, self.username, self.clientAddress, self.clientPort))

        # check if username is already in use
        # => terminate connection
        for serverSession in self.serverSessions:

            # ignore THIS server session and not existing once
            if serverSession.clientComm is None or serverSession.clientComm == self:
                continue

            if serverSession.clientComm.username == self.username:

                self.logger.error("[%s]: Username '%s' already in use (%s:%d)."
                                  % (self.fileName, self.username, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "username already in use"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False, 0

        # check if the given user credentials are valid
        if not self.userBackend.areUserCredentialsValid(self.username, password):
            self.logger.error("[%s]: Invalid user credentials (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "invalid user credentials"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False, 0

        # send authentication response
        try:
            payload = {"type": "response",
                       "result": "ok",
                       "version": self.serverVersion,
                       "rev": self.serverRev}
            message = {"message": "initialization",
                       "payload": payload}
            self._send(json.dumps(message))

        except Exception as e:
            self.logger.exception("[%s]: Sending authentication response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False, 0

        return True, messageSize

    def _registerClient(self,
                        messageSize: int) -> bool:
        """
        Internal function to register the client (add it to the database or check if it is known).

        :param messageSize:
        :return:
        """
        # get registration from client
        try:
            data = ""
            lastSize = 0
            while len(data) < messageSize:
                # NOTE: Receiving should use bytearray as in client implementation. Change during refactor.
                data += self._recv()

                # Check if the size of the received data has changed.
                # If not we detected a possible dead lock.
                if lastSize != len(data):
                    lastSize = len(data)

                else:
                    self.logger.error("[%s]: Possible dead lock detected while receiving data. Closing "
                                      % self.fileName
                                      + "connection to client (%s:%d)."
                                      % (self.clientAddress, self.clientPort))
                    return False

            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                self.logger.error("[%s]: Error received: '%s' (%s:%d)."
                                  % (self.fileName, message["error"], self.clientAddress, self.clientPort))
                return False

        except Exception as e:
            self.logger.exception("[%s]: Receiving registration failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        try:
            # check if a registration message was received
            if str(message["message"]).upper() != "initialization".upper():
                self.logger.error("[%s]: Wrong registration message: '%s' (%s:%d)."
                                  % (self.fileName, message["message"], self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "initialization message expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "REQUEST":
                self.logger.error("[%s]: request expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "request expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

        except Exception as e:
            self.logger.exception("[%s]: Message not valid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "message not valid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # extract general client configuration from message
        try:
            if not self._checkMsgHostname(message["payload"]["hostname"],
                                          message["message"]):
                self.logger.error("[%s]: Received hostname invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgNodeType(message["payload"]["nodeType"],
                                          message["message"]):
                self.logger.error("[%s]: Received nodeType invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgInstance(message["payload"]["instance"],
                                          message["message"]):
                self.logger.error("[%s]: Received instance invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgPersistent(message["payload"]["persistent"],
                                            message["message"]):
                self.logger.error("[%s]: Received persistent invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            self.hostname = message["payload"]["hostname"]
            self.nodeType = message["payload"]["nodeType"]
            self.instance = message["payload"]["instance"]
            self.persistent = message["payload"]["persistent"]

        except Exception as e:
            self.logger.exception("[%s]: Registration message not valid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "registration message not valid"}
                self._send(json.dumps(message))
            except Exception as e:
                pass

            return False

        # check if the given node type and instance are correct
        if not self.userBackend.checkNodeTypeAndInstance(self.username,
                                                         self.nodeType,
                                                         self.instance):
            self.logger.error("[%s]: Node type or instance for username '%s' is not correct (%s:%d)."
                              % (self.fileName, self.username, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "invalid node type or instance"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        self.logger.debug("[%s]: Received node registration %s:%s (%s:%d)."
                          % (self.fileName, self.hostname, self.nodeType, self.clientAddress, self.clientPort))

        # add node to database
        if not self.storage.addNode(self.username,
                                    self.hostname,
                                    self.nodeType,
                                    self.instance,
                                    self.clientVersion,
                                    self.clientRev,
                                    self.persistent,
                                    logger=self.logger):
            self.logger.error("[%s]: Unable to add node to database." % self.fileName)

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "unable to add node to database"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # Get the node id from the database for this client.
        self.nodeId = self.storage.getNodeId(self.username,
                                             logger=self.logger)
        if self.nodeId is None:
            self.logger.error("[%s]: Getting node id failed (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "unable to get node id from database"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # check if the type of the node got sensors
        # => add sensor data to the database
        if self.nodeType == "sensor":

            # extract sensors from message
            try:
                if not self._checkMsgRegSensorsList(message["payload"]["sensors"],
                                                    message["message"]):
                    self.logger.error("[%s]: Received sensors invalid (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))
                    return False

                sensors = message["payload"]["sensors"]

            except Exception as e:
                self.logger.exception("[%s]: No sensors in message (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "no sensors in message"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            sensorCount = len(sensors)

            self.logger.debug("[%s]: Sensor count: %d (%s:%d)."
                              % (self.fileName, sensorCount, self.clientAddress, self.clientPort))

            for i in range(sensorCount):

                # extract sensor data
                try:
                    sensorId = sensors[i]["clientSensorId"]
                    alertDelay = sensors[i]["alertDelay"]
                    sensorDataType = sensors[i]["dataType"]
                    alertLevels = sensors[i]["alertLevels"]
                    description = sensors[i]["description"]
                    state = sensors[i]["state"]

                    # Get data of sensor according to data type.
                    sensorData = None
                    if sensorDataType == SensorDataType.GPS:
                        sensorData = SensorDataGPS(sensors[i]["data"]["lat"],
                                                   sensors[i]["data"]["lon"],
                                                   sensors[i]["data"]["utctime"])

                    elif sensorDataType != SensorDataType.NONE:
                        sensorData = sensors[i]["data"]

                except Exception as e:
                    self.logger.exception("[%s]: Sensor data invalid (%s:%d)."
                                          % (self.fileName, self.clientAddress, self.clientPort))

                    # send error message back
                    try:
                        message = {"message": message["message"],
                                   "error": "sensor data invalid"}
                        self._send(json.dumps(message))

                    except Exception as e:
                        pass

                    return False

                self.logger.debug("[%s]: Received sensor: %d:%d:'%s' (%s:%d)."
                                  % (self.fileName, sensorId, alertDelay, description, self.clientAddress,
                                     self.clientPort))

                for tempAlertLevel in alertLevels:
                    self.logger.debug("[%s]: Sensor has alertLevel: %d (%s:%d)."
                                      % (self.fileName, tempAlertLevel, self.clientAddress, self.clientPort))

                    # check if alert level is configured on server
                    found = False
                    for configuredAlertLevel in self.alertLevels:
                        if tempAlertLevel == configuredAlertLevel.level:
                            found = True
                    if not found:
                        self.logger.error("[%s]: Alert level does not exist in configuration (%s:%d)."
                                          % (self.fileName, self.clientAddress, self.clientPort))

                        # send error message back
                        try:
                            message = {"message": message["message"],
                                       "error": "alert level does not exist"}
                            self._send(json.dumps(message))

                        except Exception as e:
                            pass

                        return False

                # Create sensor object for the currently received sensor.
                # NOTE: sensor id is not known yet.
                utcTimestamp = int(time.time())
                tempSensor = Sensor()
                tempSensor.nodeId = self.nodeId
                tempSensor.clientSensorId = sensorId
                tempSensor.description = description
                tempSensor.state = state
                tempSensor.alertLevels = alertLevels
                tempSensor.lastStateUpdated = utcTimestamp
                tempSensor.alertDelay = alertDelay
                tempSensor.dataType = sensorDataType
                tempSensor.data = sensorData
                self.sensors.append(tempSensor)

            # add sensors to database
            if not self.storage.addSensors(self.username,
                                           sensors,
                                           logger=self.logger):
                self.logger.error("[%s]: Unable to add sensors to database (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "unable to add sensors to database"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # Update alert levels the client handles
            # (sensor clients handle only alert levels the sensors trigger).
            for sensorDict in sensors:
                for alertLevelInt in sensorDict["alertLevels"]:
                    self.clientAlertLevels.add(alertLevelInt)

            # Get sensor id for each registered sensor object.
            for sensor in self.sensors:
                sensor.sensorId = self.storage.getSensorId(self.nodeId,
                                                           sensor.clientSensorId,
                                                           logger=self.logger)

                if sensor.sensorId is None:
                    self.logger.error("[%s]: Unable to get sensor id for client sensor %d (%s:%d)."
                                      % (self.fileName, sensor.clientSensorId, self.clientAddress, self.clientPort))

                    # send error message back
                    try:
                        message = {"message": message["message"],
                                   "error": "unable to get sensor id from database"}
                        self._send(json.dumps(message))

                    except Exception as e:
                        pass

                    return False

        # check if the type of the node is alert
        # => register alerts
        elif self.nodeType == "alert":

            # extract alerts from message
            try:
                if not self._checkMsgRegAlertsList(message["payload"]["alerts"],
                                                   message["message"]):

                    self.logger.error("[%s]: Received alerts invalid (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))
                    return False

                alerts = message["payload"]["alerts"]

            except Exception as e:
                self.logger.exception("[%s]: No alerts in message (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "no alerts in message"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            alertCount = len(alerts)

            self.logger.debug("[%s]: Received alerts count: %d (%s:%d)."
                              % (self.fileName, alertCount, self.clientAddress, self.clientPort))

            for i in range(alertCount):

                # extract sensor data
                try:
                    alertId = alerts[i]["clientAlertId"]
                    description = alerts[i]["description"]
                    alertLevels = alerts[i]["alertLevels"]

                    # check if alert level is configured on server
                    found = False
                    for recvAlertLevel in alertLevels:
                        for confAlertLevel in self.alertLevels:
                            if recvAlertLevel == confAlertLevel.level:
                                found = True
                                break

                        if not found:
                            self.logger.error("[%s]: Alert level %d does not exist in configuration (%s:%d)."
                                              % (self.fileName, recvAlertLevel, self.clientAddress, self.clientPort))

                            # send error message back
                            try:
                                message = {"message": message["message"],
                                           "error": "alert level does not exist"}
                                self._send(json.dumps(message))

                            except Exception as e:
                                pass

                            return False

                except Exception as e:
                    self.logger.exception("[%s]: Alert data invalid (%s:%d)."
                                          % (self.fileName, self.clientAddress, self.clientPort))

                    # send error message back
                    try:
                        message = {"message": message["message"],
                                   "error": "alert data invalid"}
                        self._send(json.dumps(message))

                    except Exception as e:
                        pass

                    return False

                self.logger.debug("[%s]: Received alert: %d:'%s' (%s:%d)."
                                  % (self.fileName, alertId, description, self.clientAddress, self.clientPort))

            # add alerts to database
            if not self.storage.addAlerts(self.username,
                                          alerts,
                                          logger=self.logger):
                self.logger.error("[%s]: Unable to add alerts to database (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "unable to add alerts to database"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # Update alert levels the client handles
            # (alert clients handle only alert levels the alerts respond to).
            for alertDict in alerts:
                for alertLevelInt in alertDict["alertLevels"]:
                    self.clientAlertLevels.add(alertLevelInt)

        # check if the type of the node is manager
        elif self.nodeType == "manager":

            # extract manager from message
            try:
                if not self._checkMsgRegManagerDict(message["payload"]["manager"],
                                                    message["message"]):
                    self.logger.error("[%s]: Received manager invalid (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))
                    return False

                manager = message["payload"]["manager"]

            except Exception as e:
                self.logger.exception("[%s]: No manager in message (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "no manager in message"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # extraction manager data
            try:
                description = manager["description"]

            except Exception as e:
                self.logger.exception("[%s]: Manager data invalid (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "manager data invalid"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            self.logger.debug("[%s]: Received manager information (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))

            # add manager to database
            if not self.storage.addManager(self.username,
                                           manager,
                                           logger=self.logger):
                self.logger.error("[%s]: Unable to add manager to database (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "unable to add manager to database"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # Update alert levels the client handles
            # (manager clients handle all alert levels).
            for alertLevel in self.alertLevels:
                self.clientAlertLevels.add(alertLevel.level)

        # if nodeType is not known
        else:
            self.logger.error("[%s]: Node type not known '%s'." % (self.fileName, self.nodeType))

            # send error message back
            try:
                message = {"message": message["message"],
                           "error": "node type not known"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # send registration response
        try:
            payload = {"type": "response",
                       "result": "ok"}
            message = {"message": "initialization",
                       "payload": payload}
            self._send(json.dumps(message))

        except Exception as e:
            self.logger.exception("[%s]: Sending registration response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        return True

    def _optionHandler(self,
                       incomingMessage: Dict[str, Any]) -> bool:
        """
        this internal function handles the sent option change from a manager and updates it in the database

        :param incomingMessage:
        :return:
        """
        # extract option type and value from message
        try:
            if not self._checkMsgOptionType(incomingMessage["payload"]["optionType"],
                                            incomingMessage["message"]):
                self.logger.error("[%s]: Received optionType invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgOptionValue(incomingMessage["payload"]["value"], incomingMessage["message"]):
                self.logger.error("[%s]: Received value invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgOptionTimeDelay(incomingMessage["payload"]["timeDelay"],
                                                 incomingMessage["message"]):
                self.logger.error("[%s]: Received timeDelay invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            optionType = incomingMessage["payload"]["optionType"]
            optionValue = incomingMessage["payload"]["value"]
            optionDelay = incomingMessage["payload"]["timeDelay"]

        except Exception as e:
            self.logger.exception("[%s]: Received option invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "received option invalid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        self.logger.debug("[%s]: Option change for type '%s' to value %d in %d seconds."
                          % (self.fileName, optionType, optionValue, optionDelay))

        self._option_executer.add_option(optionType,
                                         optionValue,
                                         optionDelay)

        # send option response
        try:
            payload = {"type": "response",
                       "result": "ok"}
            message = {"message": "option",
                       "payload": payload}
            self._send(json.dumps(message))

        except Exception as e:
            self.logger.exception("[%s]: Sending option response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        return True

    def _statusHandler(self,
                       incomingMessage: Dict[str, Any]) -> bool:
        """
        this internal function handles the sent state of the sensors from a node and updates it in the database

        :param incomingMessage:
        :return:
        """
        # extract sensors from message
        try:
            if not self._checkMsgStatusSensorsList(incomingMessage["payload"]["sensors"],
                                                   incomingMessage["message"]):
                self.logger.error("[%s]: Received sensors invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            sensors = incomingMessage["payload"]["sensors"]

        except Exception as e:
            self.logger.exception("[%s]: Received status invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "received status invalid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        if len(sensors) != self.sensorCount:
            self.logger.error("[%s]: Received sensors count invalid. Received: %d; Needed: %d (%s:%d)."
                              % (self.fileName, len(sensors), self.sensorCount, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "count of sensors not correct"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # Extract sensor states.
        # Generate a list of tuples with (clientSensorId, state).
        stateList = list()
        try:
            for i in range(self.sensorCount):
                clientSensorId = sensors[i]["clientSensorId"]

                # Check if client sensor is known.
                sensor = None
                for currentSensor in self.sensors:
                    if currentSensor.clientSensorId == clientSensorId:
                        sensor = currentSensor
                        break

                if sensor is None:

                    self.logger.error("[%s]: Unknown client sensor id %d (%s:%d)."
                                      % (self.fileName, clientSensorId, self.clientAddress, self.clientPort))

                    # send error message back
                    try:
                        message = {"message": incomingMessage["message"],
                                   "error": "unknown client sensor id"}
                        self._send(json.dumps(message))

                    except Exception as e:
                        pass

                    return False

                # Update sensor object.
                sensor.state = sensors[i]["state"]
                sensor.lastStateUpdated = int(time.time())

                stateList.append((clientSensorId, sensor.state))

        except Exception as e:
            self.logger.exception("[%s]: Received sensor state invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "received sensor state invalid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        self.logger.debug("[%s]: Received new sensor states (%s:%d)."
                          % (self.fileName, self.clientAddress, self.clientPort))

        # update the sensor state in the database
        if not self.storage.updateSensorState(self.nodeId,
                                              stateList,
                                              logger=self.logger):
            self.logger.error("[%s]: Not able to update sensor state (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "not able to update sensor state in database"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # Extract sensor data.
        # Generate a list of tuples with (clientSensorId, sensorData).
        dataList = list()
        try:
            for i in range(self.sensorCount):
                clientSensorId = sensors[i]["clientSensorId"]

                # Check if client sensor is known.
                # NOTE: omit check if client sensor id is valid because we
                # know it is, we checked it earlier.
                sensor = None
                for currentSensor in self.sensors:
                    if currentSensor.clientSensorId == clientSensorId:
                        sensor = currentSensor
                        break

                sensorDataType = sensors[i]["dataType"]

                # Check if received message contains the correct data type.
                if sensor.dataType != sensorDataType:

                    self.logger.error("[%s]: Received sensor data type for client sensor %d invalid (%s:%d)."
                                      % (self.fileName, clientSensorId, self.clientAddress, self.clientPort))

                    # send error message back
                    try:
                        message = {"message": incomingMessage["message"],
                                   "error": "received sensor data type wrong"}
                        self._send(json.dumps(message))

                    except Exception as e:
                        pass

                    return False

                # Extract received data.
                if sensorDataType == SensorDataType.NONE:
                    continue

                elif sensorDataType == SensorDataType.INT:
                    sensor.data = sensors[i]["data"]

                elif sensorDataType == SensorDataType.FLOAT:
                    sensor.data = sensors[i]["data"]

                dataList.append((clientSensorId, sensor.data))

        except Exception as e:
            self.logger.exception("[%s]: Received sensor data invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "received sensor data invalid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # Update the sensor data in the database.
        if dataList:
            self.logger.debug("[%s]: Received new sensor data (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))

            if not self.storage.updateSensorData(self.nodeId,
                                                 dataList,
                                                 logger=self.logger):
                self.logger.error("[%s]: Not able to update sensor data (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": incomingMessage["message"],
                               "error": "not able to update sensor data in database"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

        # send status response
        try:
            payload = {"type": "response",
                       "result": "ok"}
            message = {"message": "status",
                       "payload": payload}
            self._send(json.dumps(message))

        except Exception as e:
            self.logger.exception("[%s]: Sending status response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        return True

    def _sensorAlertHandler(self,
                            incomingMessage: Dict[str, Any]) -> bool:
        """
        this internal function handles received sensor alerts
        (adds them to the database and wakes up the sensor alert executer)

        :param incomingMessage:
        :return:
        """
        # extract sensor alert values
        sensor = None
        try:
            if not self._checkMsgClientSensorId(incomingMessage["payload"]["clientSensorId"],
                                                incomingMessage["message"]):
                self.logger.error("[%s]: Received clientSensorId invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgState(incomingMessage["payload"]["state"],
                                       incomingMessage["message"]):
                self.logger.error("[%s]: Received state invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgChangeState(incomingMessage["payload"]["changeState"],
                                             incomingMessage["message"]):
                self.logger.error("[%s]: Received changeState invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgHasLatestData(incomingMessage["payload"]["hasLatestData"],
                                               incomingMessage["message"]):
                self.logger.error("[%s]: Received hasLatestData invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgSensorDataType(incomingMessage["payload"]["dataType"],
                                                incomingMessage["message"]):
                self.logger.error("[%s]: Received dataType invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if incomingMessage["payload"]["dataType"] != SensorDataType.NONE:
                if not self._checkMsgSensorData(incomingMessage["payload"]["data"],
                                                incomingMessage["payload"]["dataType"],
                                                incomingMessage["message"]):
                    self.logger.error("[%s]: Received data invalid (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))
                    return False

            clientSensorId = incomingMessage["payload"]["clientSensorId"]
            state = incomingMessage["payload"]["state"]
            changeState = incomingMessage["payload"]["changeState"]
            hasLatestData = incomingMessage["payload"]["hasLatestData"]

            sensorDataType = incomingMessage["payload"]["dataType"]
            sensorData = None
            if sensorDataType != SensorDataType.NONE:
                sensorData = incomingMessage["payload"]["data"]

            # Check if client sensor is known.
            for currentSensor in self.sensors:
                if currentSensor.clientSensorId == clientSensorId:
                    sensor = currentSensor
                    break
            if sensor is None:
                self.logger.error("[%s]: Unknown client sensor id %d (%s:%d)."
                                  % (self.fileName, clientSensorId, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": incomingMessage["message"],
                               "error": "unknown client sensor id"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # Check if received message contains the correct data type.
            if sensorDataType != sensor.dataType:
                self.logger.error("[%s]: Received sensor data type for client sensor %d invalid (%s:%d)."
                                  % (self.fileName, clientSensorId, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": incomingMessage["message"],
                               "error": "received sensor data type wrong"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # Get optional data of sensor alert if it is activated.
            optionalData = None
            hasOptionalData = bool(incomingMessage["payload"]["hasOptionalData"])
            if hasOptionalData:
                optionalData = incomingMessage["payload"]["optionalData"]

                # check if data is of type dict
                if not isinstance(optionalData, dict):
                    # send error message back
                    try:
                        message = {"message": incomingMessage["message"],
                                   "error": "optionalData not of type dict"}
                        self._send(json.dumps(message))

                    except Exception as e:
                        pass

                    return False

        except Exception as e:
            self.logger.exception("[%s]: Received sensor alert invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "received sensor alert invalid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        self.logger.info("[%s]: Sensor alert for client sensor id %d and state %d."
                         % (self.fileName, clientSensorId, state))

        # Update state of the sensor if sensor alert updates the state.
        if changeState:
            sensor.state = state

            if not self.storage.updateSensorState(self.nodeId,
                                                  [(clientSensorId, state)],
                                                  logger=self.logger):

                self.logger.error("[%s]: Not able to update sensor state (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": incomingMessage["message"],
                               "error": "not able to update sensor state in database"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

        # Update data of the sensor if sensor alert carries latest
        # sensor data.
        if hasLatestData:
            sensor.data = sensorData

            if not self.storage.updateSensorData(self.nodeId,
                                                 [(clientSensorId, sensorData)],
                                                 logger=self.logger):
                self.logger.error("[%s]: Not able to update sensor data (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": incomingMessage["message"],
                               "error": "not able to update sensor data in database"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

        if not self.storage.updateSensorTime(sensor.sensorId,
                                             logger=self.logger):
            self.logger.error("[%s]: Not able to update sensor time (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "not able to update sensor time in database"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        if not self.sensorAlertExecuter.add_sensor_alert(self.nodeId,
                                                         sensor.sensorId,
                                                         state,
                                                         optionalData,
                                                         changeState,
                                                         hasLatestData,
                                                         sensorDataType,
                                                         sensorData,
                                                         self.logger):

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "not able to add sensor alert for processing"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # send sensor alert response
        try:
            payload = {"type": "response",
                       "result": "ok"}
            message = {"message": "sensoralert",
                       "payload": payload}
            self._send(json.dumps(message))

        except Exception as e:
            self.logger.exception("[%s]: Sending sensor alert response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        return True

    def _stateChangeHandler(self,
                            incomingMessage: Dict[str, Any]) -> bool:
        """
        this internal function handles received state changes
        (updates them in the database and wakes up the manager update executer)

        :param incomingMessage:
        :return:
        """
        # Extract state change values.
        sensor = None
        try:
            if not self._checkMsgClientSensorId(incomingMessage["payload"]["clientSensorId"],
                                                incomingMessage["message"]):
                self.logger.error("[%s]: Received clientSensorId invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgState(incomingMessage["payload"]["state"],
                                       incomingMessage["message"]):
                self.logger.error("[%s]: Received state invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if not self._checkMsgSensorDataType(incomingMessage["payload"]["dataType"],
                                                incomingMessage["message"]):
                self.logger.error("[%s]: Received dataType invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                return False

            if incomingMessage["payload"]["dataType"] != SensorDataType.NONE:
                if not self._checkMsgSensorData(incomingMessage["payload"]["data"],
                                                incomingMessage["payload"]["dataType"],
                                                incomingMessage["message"]):
                    self.logger.error("[%s]: Received data invalid (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))
                    return False

            clientSensorId = incomingMessage["payload"]["clientSensorId"]
            state = incomingMessage["payload"]["state"]
            sensorDataType = incomingMessage["payload"]["dataType"]
            sensorData = None
            if sensorDataType != SensorDataType.NONE:
                sensorData = incomingMessage["payload"]["data"]

            # Check if client sensor is known.
            for currentSensor in self.sensors:
                if currentSensor.clientSensorId == clientSensorId:
                    sensor = currentSensor
                    break
            if sensor is None:
                self.logger.error("[%s]: Unknown client sensor id %d (%s:%d)."
                                  % (self.fileName, clientSensorId, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": incomingMessage["message"],
                               "error": "unknown client sensor id"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # Check if received message contains the correct data type.
            if sensorDataType != sensor.dataType:
                self.logger.error("[%s]: Received sensor data type for client sensor %d invalid (%s:%d)."
                                  % (self.fileName, clientSensorId, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": incomingMessage["message"],
                               "error": "received sensor data type wrong"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # Update sensor object.
            sensor.state = state
            sensor.lastStateUpdated = int(time.time())
            sensor.data = sensorData

        except Exception as e:
            self.logger.exception("[%s]: Received state change invalid (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "received state change invalid"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        if sensorDataType == SensorDataType.NONE:
            self.logger.debug("[%s]: State change for client sensor id %d and state %d (%s:%d)."
                              % (self.fileName, clientSensorId, state, self.clientAddress, self.clientPort))

        elif sensorDataType == SensorDataType.INT:
            self.logger.debug("[%s]: State change for client sensor id %d and state %d and data %d (%s:%d)."
                              % (self.fileName, clientSensorId, state, sensorData, self.clientAddress, self.clientPort))

        elif sensorDataType == SensorDataType.FLOAT:
            self.logger.debug("[%s]: State change for client sensor id %d and state %d and data %.3f (%s:%d)."
                              % (self.fileName, clientSensorId, state, sensorData, self.clientAddress, self.clientPort))

        # update sensor state
        stateTuple = (clientSensorId, state)
        stateList = [stateTuple]
        if not self.storage.updateSensorState(self.nodeId,
                                              stateList,
                                              logger=self.logger):
            self.logger.error("[%s]: Not able to change sensor state (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "not able to change sensor state in database"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # Update sensor data if it holds data.
        if sensorDataType != SensorDataType.NONE:
            dataTuple = (clientSensorId, sensorData)
            dataList = [dataTuple]

            if not self.storage.updateSensorData(self.nodeId,
                                                 dataList,
                                                 logger=self.logger):
                self.logger.error("[%s]: Not able to change sensor data (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": incomingMessage["message"],
                               "error": "not able to change sensor data in database"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

        # get sensorId from database => append to state change queue
        # => wake up manager update executer
        sensorId = self.storage.getSensorId(self.nodeId,
                                            clientSensorId,
                                            logger=self.logger)
        if sensorId is None:
            self.logger.error("[%s]: Not able to get sensorId (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "not able to get sensor id from database"}
                self._send(json.dumps(message))

            except Exception as e:
                pass

            return False

        # send state change response
        try:
            payload = {"type": "response",
                       "result": "ok"}
            message = {"message": "statechange",
                       "payload": payload}
            self._send(json.dumps(message))

        except Exception as e:
            self.logger.exception("[%s]: Sending state change response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        sensorDataObj = SensorData()
        sensorDataObj.dataType = sensor.dataType
        sensorDataObj.data = sensor.data

        # add state change to queue and wake up manager update executer
        self.managerUpdateExecuter.queue_state_change(sensor.sensorId, sensor.state, sensorDataObj)

        return True

    def _sendManagerAllInformation(self,
                                   alertSystemStateMessage: str) -> bool:
        """
        internal function to send the current state of the alert system to a manager

        :param alertSystemStateMessage:
        :return:
        """
        # Sending status message to client.
        try:
            self.logger.debug("[%s]: Sending status message (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))
            self._send(alertSystemStateMessage)

        except Exception as e:
            self.logger.exception("[%s]: Sending status message failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        # get status acknowledgement
        self.logger.debug("[%s]: Receiving status message response (%s:%d)."
                          % (self.fileName, self.clientAddress, self.clientPort))
        try:
            data = self._recv()
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                self.logger.error("[%s]: Error received: '%s' (%s:%d)."
                                  % (self.fileName, message["error"], self.clientAddress, self.clientPort))
                return False

            # check if the received message type is the correct one
            if str(message["message"]).upper() != "STATUS":
                self.logger.error("[%s]: status message expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "status message expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                self.logger.error("[%s]: response expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "response expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).upper() == "EXPIRED":
                self.logger.warning("[%s]: Client reported 'status' messages as expired." % self.fileName)

            elif str(message["payload"]["result"]).upper() != "OK":
                self.logger.error("[%s]: Result not ok: '%s' (%s:%d)."
                                  % (self.fileName, message["payload"]["result"], self.clientAddress, self.clientPort))
                return False

        except Exception as e:
            self.logger.exception("[%s]: Receiving status message response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        self.lastRecv = int(time.time())

        return True

    def _sendManagerStateChange(self,
                                stateChangeMessage: str) -> bool:
        """
        internal function to send a state change to a manager

        :param stateChangeMessage:
        :return:
        """
        # Send state change message.
        try:
            self.logger.debug("[%s]: Sending state change message (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))
            self._send(stateChangeMessage)

        except Exception as e:
            self.logger.exception("[%s]: Sending state change failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        # receive state change response message
        try:
            data = self._recv()
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                self.logger.error("[%s]: Error received: '%s' (%s:%d)."
                                  % (self.fileName, message["error"], self.clientAddress, self.clientPort))
                return False

            # check if the received message type is the correct one
            if str(message["message"]).upper() != "STATECHANGE":
                self.logger.error("[%s]: state change message expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "state change message expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                self.logger.error("[%s]: response expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "response expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).upper() == "EXPIRED":
                self.logger.warning("[%s]: Client reported 'statechange' messages as expired." % self.fileName)

            elif str(message["payload"]["result"]).upper() != "OK":
                self.logger.error("[%s]: Result not ok: '%s' (%s:%d)."
                                  % (self.fileName, message["payload"]["result"], self.clientAddress, self.clientPort))
                return False

        except Exception as e:
            self.logger.exception("[%s]: Receiving state change response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        self.lastRecv = int(time.time())

        return True

    def _send_profile_change(self,
                             profile_change_message: str) -> bool:
        """
        internal function to send a profile change to an alert client

        :param profile_change_message:
        :return:
        """
        # Send profile change message.
        try:
            self.logger.debug("[%s]: Sending profile change message (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))
            self._send(profile_change_message)

        except Exception as e:
            self.logger.exception("[%s]: Sending profile change message failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        # get profile change acknowledgement
        self.logger.debug("[%s]: Receiving profile change response (%s:%d)."
                          % (self.fileName, self.clientAddress, self.clientPort))

        try:
            data = self._recv()
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                self.logger.error("[%s]: Error received: '%s' (%s:%d)."
                                  % (self.fileName, message["error"], self.clientAddress, self.clientPort))
                return False

            # check if the received message type is the correct one
            if str(message["message"]).upper() != "PROFILECHANGE":
                self.logger.error("[%s]: profile change message expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "profile change message expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                self.logger.error("[%s]: response expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "response expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).upper() == "EXPIRED":
                self.logger.warning("[%s]: Client reported 'profilechange' messages as expired." % self.fileName)

            elif str(message["payload"]["result"]).upper() != "OK":
                self.logger.error("[%s]: Result not ok: '%s' (%s:%d)."
                                  % (self.fileName, message["payload"]["result"], self.clientAddress, self.clientPort))
                return False

        except Exception as e:
            self.logger.exception("[%s]: Receiving profile change response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            return False

        self.lastRecv = int(time.time())

        return True

    def sendManagerStateChange(self,
                               sensorId: int,
                               state: int,
                               dataType: int,
                               data: Any) -> bool:
        """
        function that sends a state change to a manager client

        :param sensorId:
        :param state:
        :param dataType:
        :param data:
        :return:
        """
        stateChangeMessage = self._buildStateChangeMessage(sensorId,
                                                           state,
                                                           dataType,
                                                           data)

        # initiate transaction with client and acquire lock
        if not self._initiateTransaction("statechange",
                                         len(stateChangeMessage),
                                         acquireLock=True):
            return False

        returnValue = self._sendManagerStateChange(stateChangeMessage)

        self._releaseLock()
        return returnValue

    def send_profile_change(self, profile: Profile) -> bool:
        """
        Function that sends a profile change to an alert client

        :return:
        """
        profile_change_msg = self._build_profile_change_message(profile)

        # initiate transaction with client and acquire lock
        if not self._initiateTransaction("profilechange",
                                         len(profile_change_msg),
                                         acquireLock=True):
            return False

        returnValue = self._send_profile_change(profile_change_msg)

        self._releaseLock()
        return returnValue

    def sendManagerUpdate(self) -> bool:
        """
        function that sends a full information update to a manager client

        :return:
        """
        alertSystemStateMessage = self._buildAlertSystemStateMessage()
        if not alertSystemStateMessage:
            return False

        # initiate transaction with client and acquire lock
        if not self._initiateTransaction("status",
                                         len(alertSystemStateMessage),
                                         acquireLock=True):
            return False

        returnValue = self._sendManagerAllInformation(alertSystemStateMessage)

        self._releaseLock()
        return returnValue

    def sendSensorAlert(self,
                        sensorAlert: SensorAlert) -> bool:
        """
        function that sends a sensor alert to an alert/manager client

        :param sensorAlert:
        :return:
        """
        sensorAlertMessage = self._buildSensorAlertMessage(sensorAlert)

        # initiate transaction with client and acquire lock
        if not self._initiateTransaction("sensoralert",
                                         len(sensorAlertMessage),
                                         acquireLock=True):
            return False

        # Send sensor alert message.
        try:
            self.logger.debug("[%s]: Sending sensor alert message (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))
            self._send(sensorAlertMessage)

        except Exception as e:
            self.logger.exception("[%s]: Sending sensor alert message failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            self._releaseLock()
            return False

        # get sensor alert message response
        try:
            data = self._recv()
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                self.logger.error("[%s]: Error received: '%s' (%s:%d)."
                                  % (self.fileName, message["error"], self.clientAddress, self.clientPort))
                self._releaseLock()
                return False

            # check if the received message type is the correct one
            if str(message["message"]).upper() != "SENSORALERT":
                self.logger.error("[%s]: sensor alert message expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "sensor alert message expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                self._releaseLock()
                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                self.logger.error("[%s]: response expected (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                # send error message back
                try:
                    message = {"message": message["message"],
                               "error": "response expected"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                self._releaseLock()
                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).upper() == "EXPIRED":
                self.logger.warning("[%s]: Client reported 'sensoralert' messages as expired." % self.fileName)

            elif str(message["payload"]["result"]).upper() != "OK":
                self.logger.error("[%s]: Result not ok: '%s' (%s:%d)."
                                  % (self.fileName, message["payload"]["result"], self.clientAddress, self.clientPort))
                self._releaseLock()
                return False

        except Exception as e:
            self.logger.exception("[%s]: Receiving sensor alert response failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
            self._releaseLock()
            return False

        self.lastRecv = int(time.time())

        self._releaseLock()
        return True

    def handleCommunication(self):
        """
        this function handles the communication with the client and receives the commands

        :return:
        """
        self._acquireLock()

        # set timeout of the socket to configured seconds
        self.sslSocket.settimeout(self.serverReceiveTimeout)

        # Initialize communication with the client
        # (Authentication, Version verification, Registration).
        if not self._initializeCommunication():
            self.logger.error("[%s]: Communication initialization failed (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))
            self._releaseLock()
            return

        # Now that the communication is initialized, we can switch to our
        # own logger instance for the client.
        self._initializeLogger()
        self.logger.info("[%s]: Communication initialized (%s:%d)."
                         % (self.fileName, self.clientAddress, self.clientPort))

        # change the time of the last received message
        # (for the watchdog so it can see that the connection is still alive)
        self.lastRecv = int(time.time())

        # get the sensor count from the database for this connection
        # if the nodeType is "sensor"
        if self.nodeType == "sensor":
            self.sensorCount = self.storage.getSensorCount(self.nodeId,
                                                           logger=self.logger)
            # Since a user can be deleted during runtime, check if
            # the node still existed in the database.
            if self.sensorCount is None:
                self.logger.error("[%s]: Could not get node with id %d from database."
                                  % (self.fileName, self.nodeId))
                self._releaseLock()
                self._finalizeLogger()
                return

            if self.sensorCount == 0:
                self.logger.error("[%s]: Getting sensor count failed (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                self._releaseLock()
                self._finalizeLogger()
                return

        # mark node as connected in the database
        if not self.storage.markNodeAsConnected(self.nodeId,
                                                logger=self.logger):
            self.logger.error("[%s]: Not able to mark node as connected (%s:%d)."
                              % (self.fileName, self.clientAddress, self.clientPort))
            self._releaseLock()
            self._finalizeLogger()
            return

        # check if the type of the node is manager
        # => send all current node information to the manager
        if self.nodeType == "manager":
            alertSystemStateMessage = self._buildAlertSystemStateMessage()
            if not alertSystemStateMessage:
                self.logger.error("[%s]: Not able to build status update message (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                self._finalizeLogger()
                return

            if not self._initiateTransaction("status",
                                             len(alertSystemStateMessage),
                                             acquireLock=False):
                self.logger.error("[%s]: Not able initiate status update message (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                self._finalizeLogger()
                return

            if not self._sendManagerAllInformation(alertSystemStateMessage):
                self.logger.error("[%s]: Not able send status update message (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                self._finalizeLogger()
                return

        # if node is no manager
        # => send full status update to all manager clients
        else:
            # wake up manager update executer
            self.managerUpdateExecuter.force_status_update()

        # Set flag that the initialization process of the client is finished.
        self.clientInitialized = True

        # If client has registered itself,
        # notify the connection watchdog about the reconnect.
        # NOTE: We do not care if the client is set as "persistent"
        # because it could changed its configuration since the last time seen.
        self.connectionWatchdog.removeNodeTimeout(self.nodeId)

        # handle commands
        while True:
            messageSize = 0
            try:
                # set timeout of the socket to 0.5 seconds
                self.sslSocket.settimeout(0.5)

                data = self._recv()
                if not data:

                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

                # change timeout of the socket back to configured seconds
                self.sslSocket.settimeout(self.serverReceiveTimeout)

                data = data.strip()
                message = json.loads(data)
                # check if an error was received
                if "error" in message.keys():
                    self.logger.error("[%s]: Error received: '%s' (%s:%d)."
                                      % (self.fileName, message["error"], self.clientAddress, self.clientPort))
                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

                # check if RTS was received
                # => acknowledge it
                if str(message["payload"]["type"]).upper() == "rts".upper():
                    receivedTransactionId = int(message["payload"]["id"])
                    messageSize = int(message["size"])

                    # received RTS (request to send) message
                    self.logger.debug("[%s]: Received RTS %d message (%s:%d)."
                                      % (self.fileName, receivedTransactionId, self.clientAddress, self.clientPort))
                    self.logger.debug("[%s]: Sending CTS %d message (%s:%d)."
                                      % (self.fileName, receivedTransactionId, self.clientAddress, self.clientPort))

                    # send CTS (clear to send) message
                    payload = {"type": "cts",
                               "id": receivedTransactionId}
                    message = {"message": str(message["message"]),
                               "payload": payload}
                    self._send(json.dumps(message))

                    # After initiating transaction receive actual command.
                    data = ""
                    lastSize = 0
                    while len(data) < messageSize:
                        # NOTE: Receiving should use bytearray as in client implementation. Change during refactor.
                        data += self._recv(messageSize - len(data))

                        # Check if the size of the received data has changed.
                        # If not we detected a possible dead lock.
                        if lastSize != len(data):
                            lastSize = len(data)

                        else:
                            self.logger.error("[%s]: Possible dead lock detected while receiving data. Closing "
                                              % self.fileName
                                              + "connection to client (%s:%d)."
                                              % (self.clientAddress, self.clientPort))
                            # clean up session before exiting
                            self._cleanUpSessionForClosing()
                            self._releaseLock()
                            self._finalizeLogger()
                            return

                # if no RTS was received
                # => client does not stick to protocol
                # => terminate session
                else:
                    self.logger.error("[%s]: Did not receive RTS. Client sent: '%s' (%s:%d)."
                                      % (self.fileName, data, self.clientAddress, self.clientPort))
                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

            except socket.timeout as e:
                # change timeout of the socket back to configured seconds
                # before releasing the lock
                self.sslSocket.settimeout(self.serverReceiveTimeout)

                # release lock and acquire to let other threads send
                # data to the client
                # (wait 0.5 seconds in between, because semaphore
                # are released in random order => other threads could be
                # unlucky and not be chosen => this has happened when
                # loglevel was not debug => hdd I/O has slowed this process
                # down)
                self._releaseLock()
                time.sleep(0.5)
                self._acquireLock()

                # continue receiving
                continue

            except Exception as e:
                self.logger.exception("[%s]: Receiving failed (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                self._finalizeLogger()
                return

            # extract message type
            try:
                message = json.loads(data)
                # check if an error was received
                if "error" in message.keys():
                    self.logger.error("[%s]: Error received: '%s' (%s:%d)."
                                      % (self.fileName, message["error"], self.clientAddress, self.clientPort))

                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

                # check if the received type is the correct one
                if str(message["payload"]["type"]).upper() != "REQUEST":
                    self.logger.error("[%s]: request expected (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))

                    # send error message back
                    try:
                        message = {"message": message["message"],
                                   "error": "request expected"}
                        self._send(json.dumps(message))

                    except Exception as e:
                        pass

                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

                # extract the command/message type of the message
                command = str(message["message"]).upper()

            except Exception as e:
                self.logger.exception("[%s]: Received data not valid: '%s' (%s:%d)."
                                      % (self.fileName, data, self.clientAddress, self.clientPort))
                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                self._finalizeLogger()
                return

            # check if PING was received => send PONG back
            if command == "PING":
                self.logger.debug("[%s]: Received ping request (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))
                self.logger.debug("[%s]: Sending ping response (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                try:
                    payload = {"type": "response",
                               "result": "ok"}
                    message = {"message": "ping",
                               "payload": payload}
                    self._send(json.dumps(message))

                except Exception as e:
                    self.logger.exception("[%s]: Sending ping response to client failed (%s:%d)."
                                          % (self.fileName, self.clientAddress, self.clientPort))
                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

            # check if SENSORALERT was received
            # => add to database and wake up alertExecuter
            elif command == "SENSORALERT" and self.nodeType == "sensor":
                self.logger.debug("[%s]: Received sensor alert message (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                if not self._sensorAlertHandler(message):
                    self.logger.error("[%s]: Handling sensor alert failed (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))
                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

            # check if STATECHANGE was received
            # => change state of sensor in database
            elif command == "STATECHANGE" and self.nodeType == "sensor":
                self.logger.debug("[%s]: Received state change message (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                if not self._stateChangeHandler(message):
                    self.logger.error("[%s]: Handling sensor state change failed (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))
                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

            # check if STATUS was received
            # => add new state to the database
            elif command == "STATUS" and self.nodeType == "sensor":
                self.logger.debug("[%s]: Received status message (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                if not self._statusHandler(message):
                    self.logger.error("[%s]: Handling status failed (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))
                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

            # check if OPTION was received (for manager only)
            # => change option in the database
            elif command == "OPTION" and self.nodeType == "manager":
                self.logger.debug("[%s]: Received option message (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

                if not self._optionHandler(message):
                    self.logger.error("[%s]: Handling option failed (%s:%d)."
                                      % (self.fileName, self.clientAddress, self.clientPort))
                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    self._finalizeLogger()
                    return

            # command is unknown => close connection
            else:
                self.logger.error("[%s]: Received unknown command. Client sent: '%s' (%s:%d)."
                                  % (self.fileName, data, self.clientAddress, self.clientPort))

                try:
                    message = {"message": message["message"],
                               "error": "unknown command/message type"}
                    self._send(json.dumps(message))

                except Exception as e:
                    pass

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                self._finalizeLogger()
                return

            self.lastRecv = int(time.time())


# this class is used for the threaded tcp server and extends the constructor
# to pass the global configured data to all threads
class ThreadedTCPServer(socketserver.ThreadingMixIn,
                        socketserver.TCPServer):

    def __init__(self,
                 globalData: GlobalData,
                 serverAddress: Tuple[str, int],
                 RequestHandlerClass: Type[socketserver.BaseRequestHandler]):

        # get reference to global data object
        self.globalData = globalData

        socketserver.TCPServer.__init__(self,
                                        serverAddress,
                                        RequestHandlerClass)


# this class is used for incoming client connections
class ServerSession(socketserver.BaseRequestHandler):

    def __init__(self,
                 request: socket,
                 clientAddress: Tuple[str, int],
                 server: ThreadedTCPServer):

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # ssl socket
        self.sslSocket = None
        self.sslContext = None

        # instance of the client communication object
        self.clientComm = None

        # get client ip address and port
        self.clientAddress = clientAddress[0]
        self.clientPort = clientAddress[1]

        # Get reference to global data object.
        self.globalData = server.globalData
        self.logger = self.globalData.logger

        # get server certificate/key file
        self.serverCertFile = self.globalData.serverCertFile
        self.serverKeyFile = self.globalData.serverKeyFile

        # get client certificate settings
        self.useClientCertificates = self.globalData.useClientCertificates
        self.clientCAFile = self.globalData.clientCAFile

        # Get TLS/SSL setting.
        self.sslProtocol = self.globalData.sslProtocol
        self.sslCiphers = self.globalData.sslCiphers
        self.sslOptions = self.globalData.sslOptions

        # add own server session to the global list of server sessions
        self.serverSessions = self.globalData.serverSessions
        self.serverSessions.append(self)

        # Get reference to the connection watchdog object
        # to inform it about disconnects.
        self.connectionWatchdog = self.globalData.connectionWatchdog

        socketserver.BaseRequestHandler.__init__(self,
                                                 request,
                                                 clientAddress,
                                                 server)

    def handle(self):

        self.logger.info("[%s]: Client connected (%s:%d)." % (self.fileName, self.clientAddress, self.clientPort))

        # Set SSL context.
        self.sslContext = ssl.SSLContext(self.sslProtocol)
        self.sslContext.load_cert_chain(certfile=self.serverCertFile,
                                        keyfile=self.serverKeyFile)
        self.sslContext.set_ciphers(self.sslCiphers)
        self.sslContext.options = self.sslOptions

        # If activated, require a client certificate.
        if self.useClientCertificates:
            self.sslContext.verify_mode = ssl.CERT_REQUIRED
            self.sslContext.load_verify_locations(cafile=self.clientCAFile)

        # try to initiate ssl with client
        try:
            self.sslSocket = self.sslContext.wrap_socket(self.request,
                                                         server_side=True)

        except Exception as e:
            self.logger.exception("[%s]: Unable to initialize SSL connection (%s:%d)."
                                  % (self.fileName, self.clientAddress, self.clientPort))

            # remove own server session from the global list of server sessions
            # before closing server session
            try:
                self.serverSessions.remove(self)

            except Exception as e:
                pass

            return

        # give incoming connection to client communication handler
        self.clientComm = ClientCommunication(self.sslSocket,
                                              self.clientAddress,
                                              self.clientPort,
                                              self.globalData)
        self.clientComm.handleCommunication()

        # close ssl connection gracefully
        try:
            # self.sslSocket.shutdown(socket.SHUT_RDWR)
            self.sslSocket.close()

        except Exception as e:
            self.logger.exception("[%s]: Unable to close SSL connection gracefully with %s:%d."
                                  % (self.fileName, self.clientAddress, self.clientPort))

        # remove own server session from the global list of server sessions
        # before closing server session
        try:
            self.serverSessions.remove(self)

        except Exception as e:
            pass

        self.logger.info("[%s]: Client disconnected (%s:%d)." % (self.fileName, self.clientAddress, self.clientPort))

        # If client was registered and set as "persistent",
        # notify the connection watchdog about the disconnect.
        if self.clientComm.nodeId is not None and self.clientComm.persistent == 1:
            self.connectionWatchdog.addNodePreTimeout(self.clientComm.nodeId)

    def closeConnection(self):
        self.logger.info("[%s]: Closing connection to client (%s:%d)."
                         % (self.fileName, self.clientAddress, self.clientPort))
        try:
            self.sslSocket.shutdown(socket.SHUT_RDWR)

        except Exception as e:
            pass

        try:
            self.sslSocket.close()
        except Exception as e:
            pass

        try:
            self.serverSessions.remove(self)
        except Exception as e:
            pass

    def setLogger(self, logger):
        """
        Overwrites the used logger instance.

        :param logger:
        """
        self.logger = logger


# this class is used to send messages to the client
# in an asynchronous way to avoid blockings
class AsynchronousSender(threading.Thread):

    def __init__(self,
                 globalData: GlobalData,
                 clientComm: ClientCommunication):
        threading.Thread.__init__(self)

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # get global configured data
        self.globalData = globalData
        self.logger = self.globalData.logger

        # the communication instance to the client
        self.clientComm = clientComm

        # this option is used when the thread should
        # send a manager update
        self.sendManagerUpdate = False

        # this options are used when the thread should
        # send a sensor alert to the client
        self.sendSensorAlert = False
        self.sensorAlert = None

        # this options are used when the thread should
        # send a state change to a manager client
        self.sendManagerStateChange = False
        self.sendManagerStateChangeSensorId = None
        self.sendManagerStateChangeState = None
        self.sendManagerStateChangeDataType = None
        self.sendManagerStateChangeData = None

        # This option is used when the thread should
        # send a change profile to the client
        self.send_profile_change = False
        self.profile = None

    def run(self):

        # check if a status update to a manager should be send
        if self.sendManagerUpdate:
            if self.clientComm.nodeType != "manager":
                self.logger.error("[%s]: Sending status update to manager failed. Client is not a "
                                  % self.fileName
                                  + "'manager' node (%s:%d)."
                                  % (self.clientComm.clientAddress, self.clientComm.clientPort))
                return

            # sending status update to manager
            if not self.clientComm.sendManagerUpdate():
                self.logger.error("[%s]: Sending status update to manager failed (%s:%d)."
                                  % (self.fileName, self.clientComm.clientAddress, self.clientComm.clientPort))
                return

        # check if a sensor alert to a manager/alert should be send
        elif self.sendSensorAlert:
            if self.clientComm.nodeType != "manager" and self.clientComm.nodeType != "alert":
                self.logger.error("[%s]: Sending sensor alert failed. Client is not a 'manager'/'alert' node (%s:%d)."
                                  % (self.fileName, self.clientComm.clientAddress, self.clientComm.clientPort))
                return

            if not self.clientComm.sendSensorAlert(self.sensorAlert):
                self.logger.error("[%s]: Sending sensor alert to manager/alert failed (%s:%d)."
                                  % (self.fileName, self.clientComm.clientAddress, self.clientComm.clientPort))

        # check if a state change to a manager should be send
        elif self.sendManagerStateChange:
            if self.clientComm.nodeType != "manager":
                self.logger.error("[%s]: Sending state change to manager failed. Client is not a "
                                  % self.fileName
                                  + "'manager' node (%s:%d)."
                                  % (self.clientComm.clientAddress, self.clientComm.clientPort))
                return

            # sending state change to manager
            if not self.clientComm.sendManagerStateChange(self.sendManagerStateChangeSensorId,
                                                          self.sendManagerStateChangeState,
                                                          self.sendManagerStateChangeDataType,
                                                          self.sendManagerStateChangeData):
                self.logger.error("[%s]: Sending state change to manager failed (%s:%d)."
                                  % (self.fileName, self.clientComm.clientAddress, self.clientComm.clientPort))
                return

        # check if a profile change to an alert client should be send
        elif self.send_profile_change:
            if self.clientComm.nodeType != "alert":
                self.logger.error("[%s]: Sending profile change to alert failed. Client is not a "
                                  % self.fileName
                                  + "'alert' node (%s:%d)."
                                  % (self.clientComm.clientAddress, self.clientComm.clientPort))
                return

            # sending profile change to alert client
            if not self.clientComm.send_profile_change(self.profile):
                self.logger.error("[%s]: Sending profile change to alert client failed (%s:%d)."
                                  % (self.fileName, self.clientComm.clientAddress, self.clientComm.clientPort))
                return
