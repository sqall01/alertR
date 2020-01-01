#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import socket
import time
import ssl
import threading
import logging
import os
import random
import json
from .alert import AsynchronousAlertExecuter
from .localObjects import SensorAlert, SensorDataType
from .globalData import GlobalData
from .smtp import SMTPAlert
from typing import List, Dict, Any, Optional
BUFSIZE = 4096


# simple class of an ssl tcp client
class Client:

    def __init__(self, host: str, port: int, serverCAFile: str, clientCertFile: str, clientKeyFile: str):
        self.host = host
        self.port = port
        self.serverCAFile = serverCAFile
        self.clientCertFile = clientCertFile
        self.clientKeyFile = clientKeyFile
        self.socket = None
        self.sslSocket = None

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # check if a client certificate is required
        if (self.clientCertFile is None
           or self.clientKeyFile is None):
            self.sslSocket = ssl.wrap_socket(self.socket,
                                             ca_certs=self.serverCAFile,
                                             cert_reqs=ssl.CERT_REQUIRED)
        else:
            self.sslSocket = ssl.wrap_socket(self.socket,
                                             ca_certs=self.serverCAFile,
                                             cert_reqs=ssl.CERT_REQUIRED,
                                             certfile=self.clientCertFile,
                                             keyfile=self.clientKeyFile)

        self.sslSocket.connect((self.host, self.port))

    def send(self, data: str):
        self.sslSocket.send(data.encode('ascii'))

    def recv(self, buffsize: int, timeout=20.0) -> str:
        self.sslSocket.settimeout(timeout)
        data = self.sslSocket.recv(buffsize)
        self.sslSocket.settimeout(None)
        return data.decode("ascii")

    def close(self):
        # closing SSLSocket will also close the underlying socket
        self.sslSocket.close()


# this class handles the communication with the server
class ServerCommunication:

    def __init__(self, host: str, port: int, serverCAFile: str, username: str, password: str, clientCertFile: str,
                 clientKeyFile: str, globalData: GlobalData):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.serverCAFile = serverCAFile
        self.clientCertFile = clientCertFile
        self.clientKeyFile = clientKeyFile

        # instance of the used client class
        self.client = None

        # get global configured data
        self.globalData = globalData
        self.version = self.globalData.version
        self.rev = self.globalData.rev
        self.nodeType = self.globalData.nodeType
        self.instance = self.globalData.instance
        self.persistent = self.globalData.persistent

        # time the last message was received by the client
        self.lastRecv = 0.0

        # this lock is used to only allow one thread to use the communication
        self.connectionLock = threading.BoundedSemaphore(1)

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # list of all handled alerts
        self.alerts = self.globalData.alerts

        # flag that states if the client is connected
        self.isConnected = False

        # flag that states if the client is already trying to initiate a
        # transaction with the server
        self.transactionInitiation = False

    # internal function that acquires the lock
    def _acquireLock(self):
        logging.debug("[%s]: Acquire lock." % self.fileName)
        self.connectionLock.acquire()

    # internal function that releases the lock
    def _releaseLock(self):
        logging.debug("[%s]: Release lock." % self.fileName)
        self.connectionLock.release()

    # Internal function to check sanity of the alertLevels.
    def _checkMsgAlertLevels(self, alertLevels: List[int], messageType: str) -> bool:

        isCorrect = True
        if not isinstance(alertLevels, list):
            isCorrect = False
        elif not all(isinstance(item, int) for item in alertLevels):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "alertLevels not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the changeState.
    def _checkMsgChangeState(self, changeState: bool, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(changeState, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "changeState not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the description.
    def _checkMsgDescription(self, description: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(description, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "description not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the hasLatestData.
    def _checkMsgHasLatestData(self, hasLatestData: bool, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(hasLatestData, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "hasLatestData not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the hasOptionalData.
    def _checkMsgHasOptionalData(self, hasOptionalData: bool, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(hasOptionalData, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "hasOptionalData not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the optionalData.
    def _checkMsgOptionalData(self, optionalData: Dict[str, Any], messageType: str) -> bool:

        isCorrect = True
        if not isinstance(optionalData, dict):
            isCorrect = False
        if "message" in optionalData.keys():
            if not self._checkMsgOptionalDataMessage(optionalData["message"], messageType):
                isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "optionalData not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the optionalData message.
    def _checkMsgOptionalDataMessage(self, message: str, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(message, str):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "optionalData message not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the rulesActivated.
    def _checkMsgRulesActivated(self, rulesActivated: bool, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(rulesActivated, bool):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "rulesActivated not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the sensor data.
    def _checkMsgSensorData(self, data: Any, dataType: int, messageType: str) -> bool:

        isCorrect = True
        if dataType == SensorDataType.NONE and data is not None:
            isCorrect = False
        elif dataType == SensorDataType.INT and not isinstance(data, int):
            isCorrect = False
        elif dataType == SensorDataType.FLOAT and not isinstance(data, float):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "data not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the sensor data type.
    def _checkMsgSensorDataType(self, dataType: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(dataType, int):
            isCorrect = False
        elif not (SensorDataType.NONE == dataType
             or SensorDataType.INT == dataType
             or SensorDataType.FLOAT == dataType):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "dataType not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the sensorId.
    def _checkMsgSensorId(self, sensorId: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(sensorId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "sensorId not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the serverTime.
    def _checkMsgServerTime(self, serverTime: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(serverTime, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "serverTime not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to check sanity of the state.
    def _checkMsgState(self, state: int, messageType: str) -> bool:

        isCorrect = True
        if not isinstance(state, int):
            isCorrect = False
        elif state != 0 and state != 1:
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": messageType,
                           "error": "state not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # this internal function cleans up the session before releasing the
    # lock and exiting/closing the session
    def _cleanUpSessionForClosing(self):
        # set client as disconnected
        self.isConnected = False

        self.client.close()

    # this internal function that tries to initiate a transaction with
    # the server (and acquires a lock if it is told to do so)
    def _initiateTransaction(self, messageType: str, messageSize: int, acquireLock: bool=False) -> bool:

        # try to get the exclusive state to be allowed to initiate a
        # transaction with the server
        while True:

            # check if locks should be handled or not
            if acquireLock:
                self._acquireLock()

            # check if another thread is already trying to initiate a
            # transaction with the server
            if self.transactionInitiation:

                logging.warning("[%s]: Transaction initiation "
                                % self.fileName
                                + "already tried by another thread. Backing off.")

                # check if locks should be handled or not
                if acquireLock:
                    self._releaseLock()

                # wait 0.5 seconds before trying again to initiate a
                # transaction with the server
                time.sleep(0.5)

                continue

            # if transaction flag is not set
            # => start to initiate transaction with server
            else:

                logging.debug("[%s]: Got exclusive "
                              % self.fileName
                              + "transaction initiation state.")

                # set transaction initiation flag to true
                # to signal other threads that a transaction is already
                # tried to initiate
                self.transactionInitiation = True
                break

        # now we are in a exclusive state to initiate a transaction with
        # the server
        while True:

            # generate a random "unique" transaction id
            # for this transaction
            transactionId = random.randint(0, 0xffffffff)

            # send RTS (request to send) message
            logging.debug("[%s]: Sending RTS %d message."
                          % (self.fileName, transactionId))
            try:
                payload = {"type": "rts",
                           "id": transactionId}
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "size": messageSize,
                           "message": messageType,
                           "payload": payload}
                self.client.send(json.dumps(message))
            except Exception as e:
                logging.exception("[%s]: Sending RTS failed." % self.fileName)

                # set transaction initiation flag as false so other
                # threads can try to initiate a transaction with the server
                self.transactionInitiation = False

                # check if locks should be handled or not
                if acquireLock:
                    self._releaseLock()

                return False

            # get CTS (clear to send) message
            logging.debug("[%s]: Receiving CTS." % self.fileName)

            receivedTransactionId = -1
            receivedMessageType = ""
            receivedPayloadType = ""
            try:
                data = self.client.recv(BUFSIZE)
                message = json.loads(data)

                # check if an error was received
                # (only log error)
                if "error" in message.keys():
                    logging.error("[%s]: Error received: '%s'"
                                  % (self.fileName, message["error"]))
                # if no error => extract values from message
                else:
                    receivedTransactionId = int(message["payload"]["id"])
                    receivedMessageType = str(message["message"])
                    receivedPayloadType = str(message["payload"]["type"]).upper()

            except Exception as e:
                logging.exception("[%s]: Receiving CTS failed." % self.fileName)

                # set transaction initiation flag as false so other
                # threads can try to initiate a transaction with the server
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

                logging.debug("[%s]: Initiate transaction succeeded." % self.fileName)

                # set transaction initiation flag as false so other
                # threads can try to initiate a transaction with the server
                self.transactionInitiation = False
                break

            # if RTS was not acknowledged
            # => release lock and backoff for a random time then retry again
            else:

                logging.warning("[%s]: Initiate transaction "
                                % self.fileName
                                + "failed. Backing off.")

                # check if locks should be handled or not
                if acquireLock:
                    self._releaseLock()

                # backoff random time between 0 and 1 second
                backoffTime = float(random.randint(0, 100))/100
                time.sleep(backoffTime)

                # check if locks should be handled or not
                if acquireLock:
                    self._acquireLock()

        return True

    # Internal function that builds the client authentication message.
    def _buildAuthenticationMessage(self, regMessageSize: int) -> str:

        payload = {"type": "request",
                   "version": self.version,
                   "rev": self.rev,
                   "username": self.username,
                   "password": self.password}
        utcTimestamp = int(time.time())
        message = {"clientTime": utcTimestamp,
                   "size": regMessageSize,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)

    # Internal function that builds the ping message.
    def _buildPingMessage(self) -> str:

        payload = {"type": "request"}
        utcTimestamp = int(time.time())
        message = {"clientTime": utcTimestamp,
                   "message": "ping",
                   "payload": payload}
        return json.dumps(message)

    # Internal function that builds the client registration message.
    def _buildRegistrationMessage(self) -> str:

        # build alerts list for the message
        alerts = list()
        for alert in self.alerts:
            tempAlert = dict()
            tempAlert["clientAlertId"] = alert.id
            tempAlert["description"] = alert.description
            tempAlert["alertLevels"] = alert.alertLevels
            alerts.append(tempAlert)

        payload = {"type": "request",
                   "hostname": socket.gethostname(),
                   "nodeType": self.nodeType,
                   "instance": self.instance,
                   "persistent": self.persistent,
                   "alerts": alerts}
        utcTimestamp = int(time.time())
        message = {"clientTime": utcTimestamp,
                   "message": "initialization",
                   "payload": payload}
        return json.dumps(message)

    # internal function to verify the server/client version and authenticate
    def _verifyVersionAndAuthenticate(self, regMessageSize: int) -> bool:

        authMessage = self._buildAuthenticationMessage(regMessageSize)

        # send user credentials and version
        try:
            logging.debug("[%s]: Sending user credentials and version." % self.fileName)
            self.client.send(authMessage)

        except Exception as e:
            logging.exception("[%s]: Sending user credentials "
                              % self.fileName
                              + "and version failed.")
            return False

        # get authentication response from server
        try:
            data = self.client.recv(BUFSIZE)
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'."
                              % (self.fileName, message["error"]))
                return False

            if str(message["message"]).upper() != "initialization".upper():
                logging.error("[%s]: Wrong authentication message: '%s'."
                              % (self.fileName, message["message"]))

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "initialization message expected"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                logging.error("[%s]: response expected." % self.fileName)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "response expected"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).upper() != "OK":
                logging.error("[%s]: Result not ok: '%s'."
                              % (self.fileName, message["payload"]["result"]))
                return False

        except Exception as e:
            logging.exception("[%s]: Receiving authentication response failed." % self.fileName)
            return False

        # verify version
        try:
            version = float(message["payload"]["version"])
            rev = int(message["payload"]["rev"])

            logging.debug("[%s]: Received server version: '%.3f-%d'."
                          % (self.fileName, version, rev))

            # check if used protocol version is compatible
            if int(self.version * 10) != int(version * 10):

                logging.error("[%s]: Version not compatible. " % self.fileName
                              + "Client has version: '%.3f-%d' "
                              % (self.version, self.rev)
                              + "and server has '%.3f-%d"
                              % (version, rev))

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "version not compatible"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

        except Exception as e:

            logging.exception("[%s]: Version not valid." % self.fileName)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": message["message"],
                           "error": "version not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True

    # Internal function to register the node.
    def _registerNode(self, regMessage: str) -> bool:

        # Send registration message.
        try:
            logging.debug("[%s]: Sending registration message." % self.fileName)
            self.client.send(regMessage)

        except Exception as e:
            logging.exception("[%s]: Sending registration message." % self.fileName)
            return False

        # get registration response from server
        try:
            data = self.client.recv(BUFSIZE)
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'." % (self.fileName, message["error"]))
                return False

            if str(message["message"]).upper() != "initialization".upper():
                logging.error("[%s]: Wrong registration message: '%s'."
                              % (self.fileName, message["message"]))

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "initialization message expected"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                logging.error("[%s]: response expected." % self.fileName)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "response expected"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).upper() != "OK":
                logging.error("[%s]: Result not ok: '%s'." % (self.fileName, message["payload"]["result"]))
                return False

        except Exception as e:
            logging.exception("[%s]: Receiving registration response failed." % self.fileName)
            return False

        return True

    # internal function that handles received sensor alerts
    def _sensorAlertHandler(self, incomingMessage: Dict[str, Any]) -> bool:

        logging.info("[%s]: Received sensor alert." % self.fileName)

        # extract sensor alert values
        sensorAlert = SensorAlert()
        sensorAlert.timeReceived = int(time.time())
        try:
            if not self._checkMsgServerTime(incomingMessage["serverTime"], incomingMessage["message"]):
                logging.error("[%s]: Received serverTime invalid." % self.fileName)
                return False

            if not self._checkMsgAlertLevels(incomingMessage["payload"]["alertLevels"], incomingMessage["message"]):
                logging.error("[%s]: Received alertLevels invalid." % self.fileName)
                return False

            if not self._checkMsgDescription(incomingMessage["payload"]["description"], incomingMessage["message"]):
                logging.error("[%s]: Received description invalid." % self.fileName)
                return False

            if not self._checkMsgRulesActivated(incomingMessage["payload"]["rulesActivated"],
                                                incomingMessage["message"]):
                logging.error("[%s]: Received rulesActivated invalid." % self.fileName)
                return False

            if not self._checkMsgSensorId(incomingMessage["payload"]["sensorId"], incomingMessage["message"]):
                logging.error("[%s]: Received sensorId invalid." % self.fileName)
                return False

            if not self._checkMsgState(incomingMessage["payload"]["state"], incomingMessage["message"]):
                logging.error("[%s]: Received state invalid." % self.fileName)
                return False

            if not self._checkMsgHasOptionalData(incomingMessage["payload"]["hasOptionalData"],
                                                 incomingMessage["message"]):
                logging.error("[%s]: Received hasOptionalData invalid." % self.fileName)
                return False

            if incomingMessage["payload"]["hasOptionalData"]:
                if not self._checkMsgOptionalData(incomingMessage["payload"]["optionalData"],
                                                  incomingMessage["message"]):
                    logging.error("[%s]: Received optionalData invalid." % self.fileName)
                    return False

            if not self._checkMsgSensorDataType(incomingMessage["payload"]["dataType"],
                                                incomingMessage["message"]):
                logging.error("[%s]: Received dataType invalid." % self.fileName)
                return False

            if incomingMessage["payload"]["dataType"] != SensorDataType.NONE:
                if not self._checkMsgSensorData(incomingMessage["payload"]["data"],
                                                incomingMessage["payload"]["dataType"],
                                                incomingMessage["message"]):
                    logging.error("[%s]: Received data invalid." % self.fileName)
                    return False

            if not self._checkMsgHasLatestData(incomingMessage["payload"]["hasLatestData"],
                                               incomingMessage["message"]):
                logging.error("[%s]: Received hasLatestData invalid." % self.fileName)
                return False

            if not self._checkMsgChangeState(incomingMessage["payload"]["changeState"],
                                             incomingMessage["message"]):
                logging.error("[%s]: Received changeState invalid." % self.fileName)
                return False

            sensorAlert.sensorId = incomingMessage["payload"]["sensorId"]
            sensorAlert.alertLevels = incomingMessage["payload"]["alertLevels"]
            sensorAlert.state = incomingMessage["payload"]["state"]
            sensorAlert.description = incomingMessage["payload"]["description"]
            sensorAlert.changeState = incomingMessage["payload"]["changeState"]
            sensorAlert.rulesActivated = incomingMessage["payload"]["rulesActivated"]

            # parse received data (if data transfer is activated)
            sensorAlert.optionalData = None
            sensorAlert.hasOptionalData = incomingMessage["payload"]["hasOptionalData"]
            if sensorAlert.hasOptionalData:
                sensorAlert.optionalData = incomingMessage["payload"]["optionalData"]

            sensorAlert.changeState = incomingMessage["payload"]["changeState"]
            sensorAlert.hasLatestData = incomingMessage["payload"]["hasLatestData"]

            sensorAlert.dataType = incomingMessage["payload"]["dataType"]
            sensorAlert.sensorData = None
            if sensorAlert.dataType != SensorDataType.NONE:
                sensorAlert.sensorData = incomingMessage["payload"]["data"]

        except Exception as e:
            logging.exception("[%s]: Received sensor alert invalid." % self.fileName)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                           "message": incomingMessage["message"],
                           "error": "received sensor alert invalid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        # sending sensor alert response
        logging.debug("[%s]: Sending sensor alert response message." % self.fileName)
        try:
            payload = {"type": "response", "result": "ok"}
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": "sensoralert",
                       "payload": payload}
            self.client.send(json.dumps(message))

        except Exception as e:
            logging.exception("[%s]: Sending sensor alert response failed." % self.fileName)
            return False

        # trigger all alerts that have the same alert level
        atLeastOnceTriggered = False
        for alert in self.alerts:
            for alertLevel in sensorAlert.alertLevels:
                if alertLevel in alert.alertLevels:
                    atLeastOnceTriggered = True
                    # trigger alert in an own thread to not block this one
                    alertTriggerProcess = AsynchronousAlertExecuter(alert)
                    alertTriggerProcess.sensorAlert = sensorAlert
                    # set thread to daemon
                    # => threads terminates when main thread terminates
                    alertTriggerProcess.daemon = True
                    alertTriggerProcess.triggerAlert = True
                    alertTriggerProcess.start()
                    break

        # Write to log file if no alert was triggered for received sensorAlert.
        if not atLeastOnceTriggered:
            alertLevelsStr = ", ".join(map(str, sensorAlert.alertLevels))
            logging.info("[%s]: No alert triggered for alertLevels: %s."
                         % (self.fileName, alertLevelsStr))

        return True

    # internal function that handles received alerts off messages
    def _sensorAlertsOffHandler(self, incomingMessage: Dict[str, Any]) -> bool:

        logging.debug("[%s]: Received sensor alerts off." % self.fileName)

        # sending sensor alerts off response
        logging.debug("[%s]: Sending sensor alerts off response message." % self.fileName)
        try:
            payload = {"type": "response", "result": "ok"}
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                       "message": "sensoralertsoff",
                       "payload": payload}
            self.client.send(json.dumps(message))

        except Exception as e:
            logging.exception("[%s]: Sending sensor alerts "
                              % self.fileName
                              + "off response failed.")
            return False

        # stop all alerts
        for alert in self.alerts:
            # stop alert in an own thread to not block this one
            alertStopProcess = AsynchronousAlertExecuter(alert)
            # set thread to daemon
            # => threads terminates when main thread terminates
            alertStopProcess.daemon = True
            alertStopProcess.stopAlert = True
            alertStopProcess.start()

        return True

    # function that initializes the communication to the server
    # for example checks the version and authenticates the client
    def initializeCommunication(self) -> bool:

        self._acquireLock()

        # create client instance and connect to the server
        self.client = Client(self.host,
                             self.port,
                             self.serverCAFile,
                             self.clientCertFile,
                             self.clientKeyFile)
        try:
            self.client.connect()
        except Exception as e:
            logging.exception("[%s]: Connecting to server failed." % self.fileName)
            try:
                self.client.close()
            except:
                pass

            self._releaseLock()
            return False

        # Build registration message.
        regMessage = self._buildRegistrationMessage()

        # First check version and authenticate.
        if not self._verifyVersionAndAuthenticate(len(regMessage)):
            logging.error("[%s]: Version verification and "
                          % self.fileName
                          + "authentication failed.")
            self.client.close()

            self._releaseLock()
            return False

        # Second register node.
        if not self._registerNode(regMessage):
            logging.error("[%s]: Registration failed."
                          % self.fileName)
            self.client.close()

            self._releaseLock()
            return False

        # update the time the last data was received by the server
        self.lastRecv = int(time.time())

        # set client as connected
        self.isConnected = True

        self._releaseLock()

        return True

    # this function handles the incoming messages from the server
    def handleCommunication(self):

        self._acquireLock()

        # handle commands in an infinity loop
        while True:

            messageSize = 0

            try:
                # try to receive data for 0.5 seconds and then
                # timeout to give other threads the possibility
                # to send acquire the lock and send data to the server
                data = self.client.recv(BUFSIZE, timeout=0.5)
                if not data:

                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    return

                data = data.strip()
                message = json.loads(data)
                # check if an error was received
                if "error" in message.keys():
                    logging.error("[%s]: Error received: '%s'."
                                  % (self.fileName, message["error"],))

                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    return

                # check if RTS was received
                # => acknowledge it
                if str(message["payload"]["type"]).upper() == "RTS":
                    receivedTransactionId = int(message["payload"]["id"])
                    messageSize = int(message["size"])

                    # received RTS (request to send) message
                    logging.debug("[%s]: Received RTS %s message."
                                  % (self.fileName, receivedTransactionId))

                    logging.debug("[%s]: Sending CTS %s message."
                                  % (self.fileName, receivedTransactionId))

                    # send CTS (clear to send) message
                    payload = {"type": "cts", "id": receivedTransactionId}
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": str(message["message"]),
                               "payload": payload}
                    self.client.send(json.dumps(message))

                    # After initiating transaction receive actual command.
                    data = ""
                    lastSize = 0
                    while len(data) < messageSize:
                        data += self.client.recv(BUFSIZE)

                        # Check if the size of the received data has changed.
                        # If not we detected a possible dead lock.
                        if lastSize != len(data):
                            lastSize = len(data)
                        else:
                            logging.error("[%s]: Possible dead lock "
                                          % self.fileName
                                          + "detected while receiving data. Closing connection to server.")

                            # clean up session before exiting
                            self._cleanUpSessionForClosing()
                            self._releaseLock()
                            return

                # if no RTS was received
                # => server does not stick to protocol
                # => terminate session
                else:

                    logging.error("[%s]: Did not receive RTS. Server sent: '%s'."
                                  % (self.fileName, data))

                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    return

            except socket.timeout as e:
                # release lock and acquire to let other threads send
                # data to the server
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
                logging.exception("[%s]: Receiving failed." % self.fileName)

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return

            # extract message type
            try:
                message = json.loads(data)
                # check if an error was received
                if "error" in message.keys():
                    logging.error("[%s]: Error received: '%s'."
                                  % (self.fileName, message["error"]))

                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    return

                # check if the received type is the correct one
                if str(message["payload"]["type"]).upper() != "REQUEST":
                    logging.error("[%s]: request expected." % self.fileName)

                    # send error message back
                    try:
                        utcTimestamp = int(time.time())
                        message = {"clientTime": utcTimestamp,
                                   "message": message["message"],
                                   "error": "request expected"}
                        self.client.send(json.dumps(message))
                    except Exception as e:
                        pass

                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    return

                # extract the command/message type of the message
                command = str(message["message"]).upper()

            except Exception as e:

                logging.exception("[%s]: Received data not valid: '%s'." % (self.fileName, data))

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return

            # check if SENSORALERT was received
            # => trigger alerts
            if command == "SENSORALERT":

                    # handle sensor alert
                    if not self._sensorAlertHandler(message):

                        logging.error("[%s]: Receiving sensor alert failed."
                                      % self.fileName)

                        # clean up session before exiting
                        self._cleanUpSessionForClosing()
                        self._releaseLock()
                        return

            # check if SENSORALERTSOFF was received
            # => stop alerts
            elif command == "SENSORALERTSOFF":

                    # handle sensor alerts off message
                    if not self._sensorAlertsOffHandler(message):

                        logging.error("[%s]: Receiving sensor alerts off failed." % self.fileName)

                        # clean up session before exiting
                        self._cleanUpSessionForClosing()
                        self._releaseLock()
                        return

            # unknown command was received
            # => close connection
            else:
                logging.error("[%s]: Received unknown command. Server sent: '%s'." % (self.fileName, data))

                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "unknown command/message type"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return

            self.lastRecv = int(time.time())

    # this function reconnects the client to the server
    def reconnect(self) -> bool:

        logging.info("[%s] Reconnecting to server." % self.fileName)

        self._acquireLock()

        # clean up session before exiting
        self._cleanUpSessionForClosing()

        self._releaseLock()

        return self.initializeCommunication()

    # this function closes the connection to the server
    def close(self):

        self._acquireLock()

        # clean up session before exiting
        self._cleanUpSessionForClosing()
        self._releaseLock()
        return

    # this function sends a keep alive (PING request) to the server
    # to keep the connection alive and to check if the connection
    # is still alive
    def sendKeepalive(self) -> bool:

        pingMessage = self._buildPingMessage()

        # initiate transaction with server and acquire lock
        if not self._initiateTransaction("ping", len(pingMessage),
            acquireLock=True):

            # clean up session before exiting
            self._cleanUpSessionForClosing()
            return False

        # Send ping request.
        try:
            logging.debug("[%s]: Sending ping message." % self.fileName)
            self.client.send(pingMessage)

        except Exception as e:
            logging.exception("[%s]: Sending ping to server failed." % self.fileName)

            # clean up session before exiting
            self._cleanUpSessionForClosing()
            self._releaseLock()
            return False

        # get ping response from server
        try:
            data = self.client.recv(BUFSIZE)
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'." % (self.fileName, message["error"]))
                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return False

            if str(message["message"]).upper() != "PING":
                logging.error("[%s]: Wrong ping message: '%s'."
                              % (self.fileName, message["message"]))

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "ping message expected"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                logging.error("[%s]: response expected." % self.fileName)

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                               "message": message["message"],
                               "error": "response expected"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return False

            # check if status message was correctly received
            if str(message["payload"]["result"]).upper() != "OK":
                logging.error("[%s]: Result not ok: '%s'."
                              % (self.fileName, message["payload"]["result"]))
                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return False

        except Exception as e:
            logging.exception("[%s]: Receiving ping response failed." % self.fileName)
            # clean up session before exiting
            self._cleanUpSessionForClosing()
            self._releaseLock()
            return False

        logging.debug("[%s]: Received valid ping response." % self.fileName)
        self._releaseLock()

        # update time of the last received data
        self.lastRecv = int(time.time())

        return True


# this class checks if the connection to the server has broken down
# => reconnects it if necessary
class ConnectionWatchdog(threading.Thread):

    def __init__(self, connection: ServerCommunication, pingInterval: int, smtpAlert: Optional[SMTPAlert]):
        threading.Thread.__init__(self)

        # the object that handles the communication with the server
        self.connection = connection

        # the interval in which a ping should be send when no data
        # was received in this time
        self.pingInterval = pingInterval

        # the object to send a email alert via smtp
        self.smtpAlert = smtpAlert

        # the file name of this file for logging
        self.fileName = os.path.basename(__file__)

        # set exit flag as false
        self.exitFlag = False

        # internal counter to get the current count of connection retries
        self.connectionRetries = 1

    def run(self):

        # check every 5 seconds if the client is still connected
        # and the time of the last received data
        # from the server lies too far in the past
        while True:

            # wait 5 seconds before checking time of last received data
            for i in range(5):
                if self.exitFlag:
                    logging.info("[%s]: Exiting ConnectionWatchdog." % self.fileName)
                    return
                time.sleep(1)

            # check if the client is still connected to the server
            if not self.connection.isConnected:

                logging.error("[%s]: Connection to server has died." % self.fileName)

                # reconnect to the server
                while True:

                    # check if 5 unsuccessful attempts are made to connect
                    # to the server and if smtp alert is activated
                    # => send eMail alert
                    if (self.smtpAlert is not None
                       and (self.connectionRetries % 5) == 0):
                        self.smtpAlert.sendCommunicationAlert(
                            self.connectionRetries)

                    # try to connect to the server
                    if self.connection.reconnect():
                        # if smtp alert is activated
                        # => send email that communication problems are solved
                        if self.smtpAlert is not None:
                            self.smtpAlert.sendCommunicationAlertClear()

                        logging.info("[%s] Reconnecting successful after %d attempts."
                                     % (self.fileName, self.connectionRetries))

                        self.connectionRetries = 1
                        break
                    self.connectionRetries += 1

                    logging.error("[%s]: Reconnecting failed. Retrying in 5 seconds." % self.fileName)
                    time.sleep(5)

                continue

            # check if the time of the data last received lies too far in the
            # past => send ping to check connection
            utcTimestamp = int(time.time())
            if (utcTimestamp - self.connection.lastRecv) > self.pingInterval:
                logging.debug("[%s]: Ping interval exceeded." % self.fileName)

                # check if PING failed
                if not self.connection.sendKeepalive():
                    logging.error("[%s]: Connection to server has died. " % self.fileName)

                    # reconnect to the server
                    while True:

                        # check if 5 unsuccessful attempts are made to connect
                        # to the server and if smtp alert is activated
                        # => send eMail alert
                        if (self.smtpAlert is not None
                           and (self.connectionRetries % 5) == 0):
                            self.smtpAlert.sendCommunicationAlert(self.connectionRetries)

                        # try to connect to the server
                        if self.connection.reconnect():
                            # if smtp alert is activated
                            # => send email that communication
                            # problems are solved
                            if self.smtpAlert is not None:
                                self.smtpAlert.sendCommunicationAlertClear()

                            logging.info("[%s] Reconnecting successful after %d attempts."
                                         % (self.fileName, self.connectionRetries))

                            self.connectionRetries = 1
                            break
                        self.connectionRetries += 1

                        logging.error("[%s]: Reconnecting failed. Retrying in 5 seconds." % self.fileName)
                        time.sleep(5)

    # sets the exit flag to shut down the thread
    def exit(self):
        self.exitFlag = True


# this class handles the receive part of the client
class Receiver:

    def __init__(self, connection: ServerCommunication):
        self.connection = connection
        self.fileName = os.path.basename(__file__)

        # set exit flag as false
        self.exitFlag = False

    def run(self):

        while True:
            if self.exitFlag:
                return

            # only run the communication handler
            self.connection.handleCommunication()

            time.sleep(1)

    # sets the exit flag to shut down the thread
    def exit(self):
        self.exitFlag = True
