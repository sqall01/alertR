#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from serverObjects import Option, Node, Sensor, Manager, Alert, SensorAlert, \
    AlertLevel, ServerEventHandler
import socket
import time
import ssl
import threading
import logging
import os
import base64
import random
import json
from localObjects import SensorDataType
BUFSIZE = 4096


# simple class of an ssl tcp client
class Client:

    def __init__(self, host, port, serverCAFile, clientCertFile,
        clientKeyFile):
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
                ca_certs=self.serverCAFile, cert_reqs=ssl.CERT_REQUIRED)
        else:
            self.sslSocket = ssl.wrap_socket(self.socket,
                ca_certs=self.serverCAFile, cert_reqs=ssl.CERT_REQUIRED,
                certfile=self.clientCertFile, keyfile=self.clientKeyFile)

        self.sslSocket.connect((self.host, self.port))


    def send(self, data):
        count = self.sslSocket.send(data)


    def recv(self, buffsize, timeout=20.0):
        data = None
        self.sslSocket.settimeout(timeout)
        data = self.sslSocket.recv(buffsize)
        self.sslSocket.settimeout(None)
        return data


    def close(self):
        # closing SSLSocket will also close the underlying socket
        self.sslSocket.close()


# this class handles the communication with the server
class ServerCommunication:

    def __init__(self, host, port, serverCAFile, username, password,
        clientCertFile, clientKeyFile, globalData):
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
        self.description = self.globalData.description
        self.persistent = self.globalData.persistent

        # create the object that handles all incoming server events
        self.serverEventHandler = ServerEventHandler(self.globalData)

        # time the last message was received by the client
        self.lastRecv = 0.0

        # this lock is used to only allow one thread to use the communication
        self.connectionLock = threading.BoundedSemaphore(1)

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

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


    # Internal function to check sanity of the alertDelay.
    def _checkMsgAlertDelay(self, alertDelay, messageType):

        isCorrect = True
        if not isinstance(alertDelay, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "alertDelay not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the alertId.
    def _checkMsgAlertId(self, alertId, messageType):

        isCorrect = True
        if not isinstance(alertId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "alertId not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the alertLevel.
    def _checkMsgAlertLevel(self, alertLevel, messageType):

        isCorrect = True
        if not isinstance(alertLevel, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "alertLevel not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the alertLevels.
    def _checkMsgAlertLevels(self, alertLevels, messageType):

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
    def _checkMsgChangeState(self, changeState, messageType):

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


    # Internal function to check sanity of the connected.
    def _checkMsgConnected(self, connected, messageType):

        isCorrect = True
        if not isinstance(connected, int):
            isCorrect = False
        elif (connected != 0 and connected != 1):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "connected not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the description.
    def _checkMsgDescription(self, description, messageType):

        isCorrect = True
        if not (isinstance(description, str)
            or isinstance(description, unicode)):
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
    def _checkMsgHasLatestData(self, hasLatestData, messageType):

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
    def _checkMsgHasOptionalData(self, hasOptionalData, messageType):

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


    # Internal function to check sanity of the hostname.
    def _checkMsgHostname(self, hostname, messageType):

        isCorrect = True
        if not (isinstance(hostname, str)
            or isinstance(hostname, unicode)):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "hostname not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the instance.
    def _checkMsgInstance(self, instance, messageType):

        isCorrect = True
        if not (isinstance(instance, str)
            or isinstance(instance, unicode)):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "instance not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the lastStateUpdated.
    def _checkMsgLastStateUpdated(self, lastStateUpdated, messageType):

        isCorrect = True
        if not isinstance(lastStateUpdated, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "lastStateUpdated not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the managerId.
    def _checkMsgManagerId(self, managerId, messageType):

        isCorrect = True
        if not isinstance(managerId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "managerId not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the name.
    def _checkMsgName(self, name, messageType):

        isCorrect = True
        if not (isinstance(name, str)
            or isinstance(name, unicode)):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "name not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the nodeId.
    def _checkMsgNodeId(self, nodeId, messageType):

        isCorrect = True
        if not isinstance(nodeId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "nodeId not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the nodeType.
    def _checkMsgNodeType(self, nodeType, messageType):

        isCorrect = True
        if not (isinstance(nodeType, str)
            or isinstance(nodeType, unicode)):
            isCorrect = False

        nodeTypes = set(["alert", "manager", "sensor", "server"])
        if not nodeType in nodeTypes:
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "nodeType not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the optionalData.
    def _checkMsgOptionalData(self, optionalData, messageType):

        isCorrect = True
        if not isinstance(optionalData, dict):
            isCorrect = False
        if "message" in optionalData.keys():
            if not self._checkMsgOptionalDataMessage(
                optionalData["message"],
                messageType):

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
    def _checkMsgOptionalDataMessage(self, message, messageType):

        isCorrect = True
        if not (isinstance(message, str)
            or isinstance(message, unicode)):
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


    # Internal function to check sanity of the optionType.
    def _checkMsgOptionType(self, optionType, messageType):

        isCorrect = True
        if not (isinstance(optionType, str)
            or isinstance(optionType, unicode)):
            isCorrect = False

        if optionType != "alertSystemActive":
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "optionType not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the option value.
    def _checkMsgOptionValue(self, value, messageType):

        isCorrect = True
        if not isinstance(value, float):
            isCorrect = False

        if not (value >= 0.0 and value <= 1.0):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "value not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the persistent.
    def _checkMsgPersistent(self, persistent, messageType):

        isCorrect = True
        if not isinstance(persistent, int):
            isCorrect = False
        elif (persistent != 0 and persistent != 1):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "persistent not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the remoteAlertId.
    def _checkMsgRemoteAlertId(self, remoteAlertId, messageType):

        isCorrect = True
        if not isinstance(remoteAlertId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "remoteAlertId not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the remoteSensorId.
    def _checkMsgRemoteSensorId(self, remoteSensorId, messageType):

        isCorrect = True
        if not isinstance(remoteSensorId, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "remoteSensorId not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the rev.
    def _checkMsgRev(self, rev, messageType):

        isCorrect = True
        if not isinstance(rev, int):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "rev not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the rulesActivated.
    def _checkMsgRulesActivated(self, rulesActivated, messageType):

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
    def _checkMsgSensorData(self, data, dataType, messageType):

        isCorrect = True
        if (dataType == SensorDataType.NONE
            and not data is None):
            isCorrect = False
        elif (dataType == SensorDataType.INT
            and not isinstance(data, int)):
            isCorrect = False
        elif (dataType == SensorDataType.FLOAT
            and not isinstance(data, float)):
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
    def _checkMsgSensorDataType(self, dataType, messageType):

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
    def _checkMsgSensorId(self, sensorId, messageType):

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
    def _checkMsgServerTime(self, serverTime, messageType):

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
    def _checkMsgState(self, state, messageType):

        isCorrect = True
        if not isinstance(state, int):
            isCorrect = False
        elif (state != 0 and state != 1):
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


    # Internal function to check sanity of the status alertLevels list.
    def _checkMsgStatusAlertLevelsList(self, alertLevels, messageType):

        isCorrect = True
        if not isinstance(alertLevels, list):
            isCorrect = False

        # Check each alertLevel if correct.
        for alertLevel in alertLevels:

            if not isinstance(alertLevel, dict):
                isCorrect = False
                break

            if not "alertLevel" in alertLevel.keys():
                isCorrect = False
                break
            elif not self._checkMsgAlertLevel(
                alertLevel["alertLevel"],
                messageType):

                isCorrect = False
                break

            if not "name" in alertLevel.keys():
                isCorrect = False
                break
            elif not self._checkMsgName(
                alertLevel["name"],
                messageType):

                isCorrect = False
                break

            if not "triggerAlways" in alertLevel.keys():
                isCorrect = False
                break
            elif not self._checkMsgTriggerAlways(
                alertLevel["triggerAlways"],
                messageType):

                isCorrect = False
                break

            if not "rulesActivated" in alertLevel.keys():
                isCorrect = False
                break
            elif not self._checkMsgRulesActivated(
                alertLevel["rulesActivated"],
                messageType):

                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "alertLevels list not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the status alerts list.
    def _checkMsgStatusAlertsList(self, alerts, messageType):

        isCorrect = True
        if not isinstance(alerts, list):
            isCorrect = False

        # Check each alert if correct.
        for alert in alerts:

            if not isinstance(alert, dict):
                isCorrect = False
                break

            if not "nodeId" in alert.keys():
                isCorrect = False
                break
            elif not self._checkMsgNodeId(
                alert["nodeId"],
                messageType):

                isCorrect = False
                break

            if not "alertId" in alert.keys():
                isCorrect = False
                break
            elif not self._checkMsgAlertId(
                alert["alertId"],
                messageType):

                isCorrect = False
                break

            if not "description" in alert.keys():
                isCorrect = False
                break
            elif not self._checkMsgDescription(
                alert["description"],
                messageType):

                isCorrect = False
                break

            if not "alertLevels" in alert.keys():
                isCorrect = False
                break
            elif not self._checkMsgAlertLevels(
                alert["alertLevels"],
                messageType):

                isCorrect = False
                break

            if not "remoteAlertId" in alert.keys():
                isCorrect = False
                break
            elif not self._checkMsgRemoteAlertId(
                alert["remoteAlertId"],
                messageType):

                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "alerts list not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the status managers list.
    def _checkMsgStatusManagersList(self, managers, messageType):

        isCorrect = True
        if not isinstance(managers, list):
            isCorrect = False

        # Check each manager if correct.
        for manager in managers:

            if not isinstance(manager, dict):
                isCorrect = False
                break

            if not "nodeId" in manager.keys():
                isCorrect = False
                break
            elif not self._checkMsgNodeId(
                manager["nodeId"],
                messageType):

                isCorrect = False
                break

            if not "managerId" in manager.keys():
                isCorrect = False
                break
            elif not self._checkMsgManagerId(
                manager["managerId"],
                messageType):

                isCorrect = False
                break

            if not "description" in manager.keys():
                isCorrect = False
                break
            elif not self._checkMsgDescription(
                manager["description"],
                messageType):

                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "managers list not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the status nodes list.
    def _checkMsgStatusNodesList(self, nodes, messageType):

        isCorrect = True
        if not isinstance(nodes, list):
            isCorrect = False

        # Check each option if correct.
        for node in nodes:

            if not isinstance(node, dict):
                isCorrect = False
                break

            if not "nodeId" in node.keys():
                isCorrect = False
                break
            elif not self._checkMsgNodeId(
                node["nodeId"],
                messageType):

                isCorrect = False
                break

            if not "hostname" in node.keys():
                isCorrect = False
                break
            elif not self._checkMsgHostname(
                node["hostname"],
                messageType):

                isCorrect = False
                break

            if not "nodeType" in node.keys():
                isCorrect = False
                break
            elif not self._checkMsgNodeType(
                node["nodeType"],
                messageType):

                isCorrect = False
                break

            if not "instance" in node.keys():
                isCorrect = False
                break
            elif not self._checkMsgInstance(
                node["instance"],
                messageType):

                isCorrect = False
                break

            if not "connected" in node.keys():
                isCorrect = False
                break
            elif not self._checkMsgConnected(
                node["connected"],
                messageType):

                isCorrect = False
                break

            if not "version" in node.keys():
                isCorrect = False
                break
            elif not self._checkMsgVersion(
                node["version"],
                messageType):

                isCorrect = False
                break

            if not "rev" in node.keys():
                isCorrect = False
                break
            elif not self._checkMsgRev(
                node["rev"],
                messageType):

                isCorrect = False
                break

            if not "username" in node.keys():
                isCorrect = False
                break
            elif not self._checkMsgUsername(
                node["username"],
                messageType):

                isCorrect = False
                break

            if not "persistent" in node.keys():
                isCorrect = False
                break
            elif not self._checkMsgPersistent(
                node["persistent"],
                messageType):

                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "nodes list not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the status options list.
    def _checkMsgStatusOptionsList(self, options, messageType):

        isCorrect = True
        if not isinstance(options, list):
            isCorrect = False

        # Check each option if correct.
        for option in options:

            if not isinstance(option, dict):
                isCorrect = False
                break

            if not "type" in option.keys():
                isCorrect = False
                break
            elif not self._checkMsgOptionType(
                option["type"],
                messageType):

                isCorrect = False
                break

            if not "value" in option.keys():
                isCorrect = False
                break
            elif not self._checkMsgOptionValue(
                option["value"],
                messageType):

                isCorrect = False
                break

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "options list not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the status sensors list.
    def _checkMsgStatusSensorsList(self, sensors, messageType):

        isCorrect = True
        if not isinstance(sensors, list):
            isCorrect = False

        # Check each sensor if correct.
        for sensor in sensors:

            if not isinstance(sensor, dict):
                isCorrect = False
                break

            if not "nodeId" in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgNodeId(
                sensor["nodeId"],
                messageType):

                isCorrect = False
                break

            if not "sensorId" in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgSensorId(
                sensor["sensorId"],
                messageType):

                isCorrect = False
                break

            if not "alertDelay" in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgAlertDelay(
                sensor["alertDelay"],
                messageType):

                isCorrect = False
                break

            if not "alertLevels" in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgAlertLevels(
                sensor["alertLevels"],
                messageType):

                isCorrect = False
                break

            if not "description" in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgDescription(
                sensor["description"],
                messageType):

                isCorrect = False
                break

            if not "lastStateUpdated" in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgLastStateUpdated(
                sensor["lastStateUpdated"],
                messageType):

                isCorrect = False
                break

            if not "state" in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgState(
                sensor["state"],
                messageType):
                isCorrect = False
                break

            if not "remoteSensorId" in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgRemoteSensorId(
                sensor["remoteSensorId"],
                messageType):

                isCorrect = False
                break

            if not "dataType" in sensor.keys():
                isCorrect = False
                break
            elif not self._checkMsgSensorDataType(
                sensor["dataType"],
                messageType):

                isCorrect = False
                break

            if sensor["dataType"] != SensorDataType.NONE:
                if not "data" in sensor.keys():
                    isCorrect = False
                    break
                elif not self._checkMsgSensorData(
                    sensor["data"],
                    sensor["dataType"],
                    messageType):

                    isCorrect = False
                    break

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "sensors list not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the triggerAlways.
    def _checkMsgTriggerAlways(self, triggerAlways, messageType):

        isCorrect = True
        if not isinstance(triggerAlways, int):
            isCorrect = False
        elif (triggerAlways != 0 and triggerAlways != 1):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "triggerAlways not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the username.
    def _checkMsgUsername(self, username, messageType):

        isCorrect = True
        if not (isinstance(username, str)
            or isinstance(username, unicode)):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "username not valid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        return True


    # Internal function to check sanity of the version.
    def _checkMsgVersion(self, version, messageType):

        isCorrect = True
        if not isinstance(version, float):
            isCorrect = False

        if not isCorrect:
            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": messageType,
                    "error": "version not valid"}
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

        # handle closing event
        self.serverEventHandler.handleEvent()

        self.client.close()


    # this internal function that tries to initiate a transaction with
    # the server (and acquires a lock if it is told to do so)
    def _initiateTransaction(self, messageType, messageSize,
        acquireLock=False):

        # try to get the exclusive state to be allowed to initiate a
        # transaction with the server
        while True:

            # check if locks should be handled or not
            if acquireLock:
                self._acquireLock()

            # check if another thread is already trying to initiate a
            # transaction with the server
            if self.transactionInitiation:

                logging.warning("[%s]: Transaction initiation " % self.fileName
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

                logging.debug("[%s]: Got exclusive " % self.fileName
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
                logging.exception("[%s]: Sending RTS " % self.fileName
                    + "failed.")

                # set transaction initiation flag as false so other
                # threads can try to initiate a transaction with the server
                self.transactionInitiation = False

                # check if locks should be handled or not
                if acquireLock:
                    self._releaseLock()

                return False

            # get CTS (clear to send) message
            logging.debug("[%s]: Receiving CTS." % self.fileName)

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
                    receivedTransactionId = message["payload"]["id"]
                    receivedMessageType = str(message["message"])
                    receivedPayloadType = \
                        str(message["payload"]["type"]).upper()

            except Exception as e:
                logging.exception("[%s]: Receiving CTS " % self.fileName
                    + "failed.")

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

                logging.debug("[%s]: Initiate transaction " % self.fileName
                    + "succeeded.")

                # set transaction initiation flag as false so other
                # threads can try to initiate a transaction with the server
                self.transactionInitiation = False

                break

            # if RTS was not acknowledged
            # => release lock and backoff for a random time then retry again
            else:

                logging.warning("[%s]: Initiate transaction " % self.fileName
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
    def _buildAuthenticationMessage(self, regMessageSize):

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

    # Internal function that builds the option message.
    def _buildOptionMessage(self, optionType, optionValue, optionDelay):

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
    def _buildPingMessage(self):

        payload = {"type": "request"}
        utcTimestamp = int(time.time())
        message = {"clientTime": utcTimestamp,
            "message": "ping",
            "payload": payload}
        return json.dumps(message)


    # Internal function that builds the client registration message.
    def _buildRegistrationMessage(self):

        # build manager dict for the message
        manager = dict()
        manager["description"] = self.description

        payload = {"type": "request",
            "hostname": socket.gethostname(),
            "nodeType": self.nodeType,
            "instance": self.instance,
            "persistent": self.persistent,
            "manager": manager}
        utcTimestamp = int(time.time())
        message = {"clientTime": utcTimestamp,
            "message": "initialization",
            "payload": payload}
        return json.dumps(message)


    # internal function to verify the server/client version and authenticate
    def _verifyVersionAndAuthenticate(self, regMessageSize):

        authMessage = self._buildAuthenticationMessage(regMessageSize)

        # send user credentials and version
        try:
            logging.debug("[%s]: Sending user credentials and version."
                % self.fileName)
            self.client.send(authMessage)

        except Exception as e:
            logging.exception("[%s]: Sending user credentials " % self.fileName
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
                logging.error("[%s]: Wrong authentication message: "
                    % self.fileName
                    + "'%s'." % message["message"])

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
                logging.error("[%s]: response expected."
                    % self.fileName)

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
            logging.exception("[%s]: Receiving authentication response failed."
                % self.fileName)
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


    # internal function to register the node
    def _registerNode(self, regMessage):

        # Send registration message.
        try:
            logging.debug("[%s]: Sending registration message."
                % self.fileName)
            self.client.send(regMessage)

        except Exception as e:
            logging.exception("[%s]: Sending registration " % self.fileName
                + "message.")
            return False

        # get registration response from server
        try:
            data = self.client.recv(BUFSIZE)
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'."
                    % (self.fileName, message["error"]))
                return False

            if str(message["message"]).upper() != "initialization".upper():
                logging.error("[%s]: Wrong registration message: "
                    % self.fileName
                    + "'%s'." % message["message"])

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
                logging.error("[%s]: response expected."
                    % self.fileName)

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
            logging.exception("[%s]: Receiving registration response failed."
                % self.fileName)
            return False

        return True


    # internal function that handles received status updates
    def _statusUpdateHandler(self, incomingMessage):

        options = list()
        nodes = list()
        sensors = list()
        managers = list()
        alerts = list()
        alertLevels = list()

        # extract status values
        try:

            if not self._checkMsgServerTime(
                incomingMessage["serverTime"],
                incomingMessage["message"]):

                logging.error("[%s]: Received serverTime invalid."
                    % self.fileName)
                return False
            if not self._checkMsgStatusOptionsList(
                incomingMessage["payload"]["options"],
                incomingMessage["message"]):

                logging.error("[%s]: Received options invalid."
                    % self.fileName)
                return False
            if not self._checkMsgStatusNodesList(
                incomingMessage["payload"]["nodes"],
                incomingMessage["message"]):

                logging.error("[%s]: Received nodes invalid."
                    % self.fileName)
                return False
            if not self._checkMsgStatusSensorsList(
                incomingMessage["payload"]["sensors"],
                incomingMessage["message"]):

                logging.error("[%s]: Received sensors invalid."
                    % self.fileName)
                return False
            if not self._checkMsgStatusManagersList(
                incomingMessage["payload"]["managers"],
                incomingMessage["message"]):

                logging.error("[%s]: Received managers invalid."
                    % self.fileName)
                return False
            if not self._checkMsgStatusAlertsList(
                incomingMessage["payload"]["alerts"],
                incomingMessage["message"]):

                logging.error("[%s]: Received alerts invalid."
                    % self.fileName)
                return False
            if not self._checkMsgStatusAlertLevelsList(
                incomingMessage["payload"]["alertLevels"],
                incomingMessage["message"]):

                logging.error("[%s]: Received alertLevels invalid."
                    % self.fileName)
                return False

            serverTime = incomingMessage["serverTime"]
            optionsRaw = incomingMessage["payload"]["options"]
            nodesRaw = incomingMessage["payload"]["nodes"]
            sensorsRaw = incomingMessage["payload"]["sensors"]
            managersRaw = incomingMessage["payload"]["managers"]
            alertsRaw = incomingMessage["payload"]["alerts"]
            alertLevelsRaw = incomingMessage["payload"]["alertLevels"]

        except Exception as e:
            logging.exception("[%s]: Received status " % self.fileName
                + "invalid.")

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": incomingMessage["message"],
                    "error": "received status invalid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        logging.debug("[%s]: Received option count: %d."
                % (self.fileName, len(optionsRaw)))

        # process received options
        for i in range(len(optionsRaw)):

            try:
                optionType = optionsRaw[i]["type"]
                optionValue = optionsRaw[i]["value"]
            except Exception as e:
                logging.exception("[%s]: Received option " % self.fileName
                + "invalid.")

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                        "message": incomingMessage["message"],
                        "error": "received option invalid"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received option " % self.fileName
                + "information: '%s':%d."
                % (optionType, optionValue))

            option = Option()
            option.type = optionType
            option.value = optionValue
            options.append(option)

        logging.debug("[%s]: Received node count: %d."
                % (self.fileName, len(nodesRaw)))

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
                logging.exception("[%s]: Received node " % self.fileName
                + "invalid.")

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                        "message": incomingMessage["message"],
                        "error": "received node invalid"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received node " % self.fileName
                + "information: %d:'%s':'%s':%d:%d."
                % (nodeId, hostname, nodeType, connected, persistent))

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

        logging.debug("[%s]: Received sensor count: %d."
                % (self.fileName, len(sensorsRaw)))

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
                logging.exception("[%s]: Received sensor " % self.fileName
                + "invalid.")

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                        "message": incomingMessage["message"],
                        "error": "received sensor invalid"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received sensor " % self.fileName
                + "information: %d:%d:%d:'%s':%d:%d."
                % (nodeId, sensorId, alertDelay, description,
                lastStateUpdated, state))

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

        logging.debug("[%s]: Received manager count: %d."
                % (self.fileName, len(managersRaw)))

        # process received managers
        for i in range(len(managersRaw)):

            try:
                nodeId = managersRaw[i]["nodeId"]
                managerId = managersRaw[i]["managerId"]
                description = managersRaw[i]["description"]
            except Exception as e:
                logging.exception("[%s]: Received manager " % self.fileName
                + "invalid.")

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                        "message": incomingMessage["message"],
                        "error": "received manager invalid"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received manager " % self.fileName
                + "information: %d:%d:'%s'."
                % (nodeId, managerId, description))

            manager = Manager()
            manager.nodeId = nodeId
            manager.managerId = managerId
            manager.description = description
            managers.append(manager)

        logging.debug("[%s]: Received alert count: %d."
                % (self.fileName, len(alertsRaw)))

        # process received alerts
        for i in range(len(alertsRaw)):

            try:
                nodeId = alertsRaw[i]["nodeId"]
                alertId = alertsRaw[i]["alertId"]
                remoteAlertId = alertsRaw[i]["remoteAlertId"]
                description = alertsRaw[i]["description"]
                alertAlertLevels = alertsRaw[i]["alertLevels"]

            except Exception as e:
                logging.exception("[%s]: Received alert " % self.fileName
                + "invalid.")

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                        "message": incomingMessage["message"],
                        "error": "received alert invalid"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received alert " % self.fileName
                + "information: %d:%d:'%s'"
                % (nodeId, alertId, description))

            alert = Alert()
            alert.nodeId = nodeId
            alert.alertId = alertId
            alert.remoteAlertId = remoteAlertId
            alert.alertLevels = alertAlertLevels
            alert.description = description
            alerts.append(alert)

        logging.debug("[%s]: Received alertLevel count: %d."
                % (self.fileName, len(alertLevelsRaw)))

        # process received alertLevels
        for i in range(len(alertLevelsRaw)):

            try:
                level = alertLevelsRaw[i]["alertLevel"]
                name = alertLevelsRaw[i]["name"]
                triggerAlways = alertLevelsRaw[i]["triggerAlways"]
                rulesActivated = alertLevelsRaw[i]["rulesActivated"]

            except Exception as e:
                logging.exception("[%s]: Received alertLevel " % self.fileName
                + "invalid.")

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                        "message": incomingMessage["message"],
                        "error": "received alertLevel invalid"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                return False

            logging.debug("[%s]: Received alertLevel " % self.fileName
                + "information: %d:'%s':%d:"
                % (level, name, triggerAlways))

            alertLevel = AlertLevel()
            alertLevel.level = level
            alertLevel.name = name
            alertLevel.triggerAlways = triggerAlways
            alertLevel.rulesActivated = rulesActivated
            alertLevels.append(alertLevel)


        # handle received status update
        if not self.serverEventHandler.receivedStatusUpdate(serverTime,
            options, nodes, sensors, managers, alerts, alertLevels):

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": incomingMessage["message"],
                    "error": "handling received data failed"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        # sending sensor alert response
        logging.debug("[%s]: Sending status " % self.fileName
            + "response message.")
        try:
            payload = {"type": "response", "result": "ok"}
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                "message": "status", "payload": payload}
            self.client.send(json.dumps(message))

        except Exception as e:
            logging.exception("[%s]: Sending status " % self.fileName
                + "response failed.")

            return False

        # handle status update event
        self.serverEventHandler.handleEvent()

        return True


    # internal function that handles received sensor alerts
    def _sensorAlertHandler(self, incomingMessage):

        logging.info("[%s]: Received sensor alert." % self.fileName)

        # extract sensor alert values
        sensorAlert = SensorAlert()
        sensorAlert.timeReceived = int(time.time())
        try:
            if not self._checkMsgServerTime(
                incomingMessage["serverTime"],
                incomingMessage["message"]):

                logging.error("[%s]: Received serverTime invalid."
                    % self.fileName)
                return False
            if not self._checkMsgAlertLevels(
                incomingMessage["payload"]["alertLevels"],
                incomingMessage["message"]):

                logging.error("[%s]: Received alertLevels invalid."
                    % self.fileName)
                return False
            if not self._checkMsgDescription(
                incomingMessage["payload"]["description"],
                incomingMessage["message"]):

                logging.error("[%s]: Received description invalid."
                    % self.fileName)
                return False
            if not self._checkMsgRulesActivated(
                incomingMessage["payload"]["rulesActivated"],
                incomingMessage["message"]):

                logging.error("[%s]: Received rulesActivated invalid."
                    % self.fileName)
                return False
            if not self._checkMsgSensorId(
                incomingMessage["payload"]["sensorId"],
                incomingMessage["message"]):

                logging.error("[%s]: Received sensorId invalid."
                    % self.fileName)
                return False
            if not self._checkMsgState(
                incomingMessage["payload"]["state"],
                incomingMessage["message"]):

                logging.error("[%s]: Received state invalid."
                    % self.fileName)
                return False
            if not self._checkMsgHasOptionalData(
                incomingMessage["payload"]["hasOptionalData"],
                incomingMessage["message"]):

                logging.error("[%s]: Received hasOptionalData invalid."
                    % self.fileName)
                return False
            if incomingMessage["payload"]["hasOptionalData"]:
                if not self._checkMsgOptionalData(
                    incomingMessage["payload"]["optionalData"],
                    incomingMessage["message"]):

                    logging.error("[%s]: Received optionalData invalid."
                        % self.fileName)
                    return False
            if not self._checkMsgSensorDataType(
                incomingMessage["payload"]["dataType"],
                incomingMessage["message"]):

                logging.error("[%s]: Received dataType invalid."
                    % self.fileName)
                return False
            if incomingMessage["payload"]["dataType"] != SensorDataType.NONE:
                if not self._checkMsgSensorData(
                    incomingMessage["payload"]["data"],
                    incomingMessage["payload"]["dataType"],
                    incomingMessage["message"]):

                    logging.error("[%s]: Received data invalid."
                        % self.fileName)
                    return False
            if not self._checkMsgHasLatestData(
                incomingMessage["payload"]["hasLatestData"],
                incomingMessage["message"]):

                logging.error("[%s]: Received hasLatestData invalid."
                    % self.fileName)
                return False
            if not self._checkMsgChangeState(
                incomingMessage["payload"]["changeState"],
                incomingMessage["message"]):

                logging.error("[%s]: Received changeState invalid."
                    % self.fileName)
                return False

            serverTime = incomingMessage["serverTime"]

            sensorAlert.rulesActivated = \
                incomingMessage["payload"]["rulesActivated"]

            # always -1 when no sensor is responsible for sensor alert
            sensorAlert.sensorId = incomingMessage["payload"]["sensorId"]

            # state of rule sensor alerts is always set to 1
            sensorAlert.state = incomingMessage["payload"]["state"]

            sensorAlert.alertLevels = incomingMessage["payload"]["alertLevels"]

            sensorAlert.description = \
                incomingMessage["payload"]["description"]

            # parse transfer data
            sensorAlert.hasOptionalData = \
                incomingMessage["payload"]["hasOptionalData"]
            if sensorAlert.hasOptionalData:
                sensorAlert.optionalData = incomingMessage[
                    "payload"]["optionalData"]
            else:
                sensorAlert.optionalData = dict()

            sensorAlert.changeState = incomingMessage["payload"]["changeState"]
            sensorAlert.hasLatestData = \
                incomingMessage["payload"]["hasLatestData"]
            sensorAlert.dataType = incomingMessage["payload"]["dataType"]

            sensorAlert.sensorData = None
            if sensorAlert.dataType == SensorDataType.INT:
                sensorAlert.sensorData = incomingMessage["payload"]["data"]
            elif sensorAlert.dataType == SensorDataType.FLOAT:
                sensorAlert.sensorData = incomingMessage["payload"]["data"]

        except Exception as e:
            logging.exception("[%s]: Received sensor alert " % self.fileName
                + "invalid.")

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
        logging.debug("[%s]: Sending sensor alert " % self.fileName
            + "response message.")
        try:
            payload = {"type": "response", "result": "ok"}
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                "message": "sensoralert", "payload": payload}
            self.client.send(json.dumps(message))

        except Exception as e:
            logging.exception("[%s]: Sending sensor alert " % self.fileName
                + "response failed.")

            return False

        # handle received sensor alert
        if self.serverEventHandler.receivedSensorAlert(serverTime,
            sensorAlert):

            return True

        return False


    # internal function that handles received state changes of sensors
    def _stateChangeHandler(self, incomingMessage):

        logging.debug("[%s]: Received state change." % self.fileName)

        # extract state change values
        try:
            if not self._checkMsgServerTime(
                incomingMessage["serverTime"],
                incomingMessage["message"]):

                logging.error("[%s]: Received serverTime invalid."
                    % self.fileName)
                return False
            if not self._checkMsgSensorId(
                incomingMessage["payload"]["sensorId"],
                incomingMessage["message"]):

                logging.error("[%s]: Received sensorId invalid."
                    % self.fileName)
                return False
            if not self._checkMsgState(
                incomingMessage["payload"]["state"],
                incomingMessage["message"]):

                logging.error("[%s]: Received state invalid."
                    % self.fileName)
                return False
            if not self._checkMsgSensorDataType(
                incomingMessage["payload"]["dataType"],
                incomingMessage["message"]):

                logging.error("[%s]: Received dataType invalid."
                    % self.fileName)
                return False
            if incomingMessage["payload"]["dataType"] != SensorDataType.NONE:
                if not self._checkMsgSensorData(
                    incomingMessage["payload"]["data"],
                    incomingMessage["payload"]["dataType"],
                    incomingMessage["message"]):

                    logging.error("[%s]: Received data invalid."
                        % self.fileName)
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
            logging.exception("[%s]: Received state change " % self.fileName
                + "invalid.")

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": incomingMessage["message"],
                    "error": "received state change invalid"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            return False

        # sending state change response
        logging.debug("[%s]: Sending state change " % self.fileName
            + "response message.")
        try:
            payload = {"type": "response", "result": "ok"}
            utcTimestamp = int(time.time())
            message = {"clientTime": utcTimestamp,
                "message": "statechange", "payload": payload}
            self.client.send(json.dumps(message))

        except Exception as e:
            logging.exception("[%s]: Sending state change " % self.fileName
                + "response failed.")

            return False

        # handle received state change
        if self.serverEventHandler.receivedStateChange(serverTime, sensorId,
            state, dataType, sensorData):

            return True

        return False


    # function that initializes the communication to the server
    # for example checks the version and authenticates the client
    def initializeCommunication(self):

        self._acquireLock()

        # create client instance and connect to the server
        self.client = Client(self.host, self.port, self.serverCAFile,
            self.clientCertFile, self.clientKeyFile)
        try:
            self.client.connect()
        except Exception as e:
            logging.exception("[%s]: Connecting to server failed."
                % self.fileName)
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
            logging.error("[%s]: Version verification and " % self.fileName
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

        # get the initial status update from the server
        try:
            logging.debug("[%s]: Receiving initial status update."
                % self.fileName)

            data = self.client.recv(BUFSIZE)
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'."
                    % (self.fileName, message["error"],))

                self._releaseLock()
                return False

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
                            + "detected while receiving data. Closing "
                            + "connection to server.")

                        self._releaseLock()
                        return False

            # if no RTS was received
            # => server does not stick to protocol
            # => terminate session
            else:

                logging.error("[%s]: Did not receive " % self.fileName
                    + "RTS. Server sent: '%s'." % data)

                self._releaseLock()
                return False

        except Exception as e:
            logging.exception("[%s]: Receiving initial " % self.fileName
                + "status update failed.")

            self._releaseLock()
            return False

        # extract message type
        try:
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'."
                    % (self.fileName, message["error"]))

                self._releaseLock()
                return False

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

                self._releaseLock()
                return False

            # extract the command/message type of the message
            command = str(message["message"]).upper()

        except Exception as e:

            logging.exception("[%s]: Received data " % self.fileName
                + "not valid: '%s'." % data)

            self._releaseLock()
            return False

        if command != "STATUS":
            logging.error("[%s]: Receiving status update " % self.fileName
                + "failed. Server sent: '%s'" % data)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"clientTime": utcTimestamp,
                    "message": message["message"],
                    "error": "initial status update expected"}
                self.client.send(json.dumps(message))
            except Exception as e:
                pass

            self._releaseLock()
            return False

        if not self._statusUpdateHandler(message):
            logging.error("[%s]: Initial status update failed."
                % self.fileName)
            self.client.close()

            self._releaseLock()
            return False

        self.lastRecv = int(time.time())

        # set client as connected
        self.isConnected = True

        self._releaseLock()

        # handle connection initialized event
        self.serverEventHandler.handleEvent()

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

                    # After initiating transaction receive actual command
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
                                + "detected while receiving data. Closing "
                                + "connection to server.")

                            # clean up session before exiting
                            self._cleanUpSessionForClosing()
                            self._releaseLock()
                            return

                # if no RTS was received
                # => server does not stick to protocol
                # => terminate session
                else:

                    logging.error("[%s]: Did not receive " % self.fileName
                        + "RTS. Server sent: '%s'." % data)

                    # clean up session before exiting
                    self._cleanUpSessionForClosing()
                    self._releaseLock()
                    return

            except ssl.SSLError as e:

                # catch receive timeouts
                err = e.args[0]
                if err == "The read operation timed out":

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

                logging.exception("[%s]: Receiving failed." % self.fileName)

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return

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

                logging.exception("[%s]: Received data " % self.fileName
                    + "not valid: '%s'." % data)

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return

            # check if SENSORALERT was received
            # => update screen
            if (command == "SENSORALERT"):

                    # handle sensor alert
                    if not self._sensorAlertHandler(message):

                        logging.error("[%s]: Receiving sensor alert failed."
                            % self.fileName)

                        # clean up session before exiting
                        self._cleanUpSessionForClosing()
                        self._releaseLock()
                        return

            # check if STATUS was received
            # => get status update
            elif (command == "STATUS"):

                    # get status update
                    if not self._statusUpdateHandler(message):

                        logging.error("[%s]: Receiving status update failed."
                            % self.fileName)

                        # clean up session before exiting
                        self._cleanUpSessionForClosing()
                        self._releaseLock()
                        return

            # check if STATECHANGE was received
            # => update screen
            elif (command == "STATECHANGE"):

                    # handle sensor state change
                    if not self._stateChangeHandler(message):

                        logging.error("[%s]: Receiving state change failed."
                            % self.fileName)

                        # clean up session before exiting
                        self._cleanUpSessionForClosing()
                        self._releaseLock()
                        return

            else:
                logging.error("[%s]: Received unknown " % self.fileName
                    + "command. Server sent: '%s'." % data)

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

            # handle incoming message event
            self.serverEventHandler.handleEvent()

            self.lastRecv = int(time.time())


    # this function sends an option change to the server for example
    # to activate the alert system or deactivate it
    def sendOption(self, optionType, optionValue, optionDelay=0):

        optionMessage = self._buildOptionMessage(optionType,
            optionValue, optionDelay)

        # initiate transaction with server and acquire lock
        if not self._initiateTransaction("option",
            len(optionMessage), acquireLock=True):
            return False

        # Send option request.
        try:
            logging.debug("[%s]: Sending option message." % self.fileName)
            self.client.send(optionMessage)

        except Exception as e:
            logging.exception("[%s]: Sending option message failed."
                % self.fileName)

            # clean up session before exiting
            self._cleanUpSessionForClosing()
            self._releaseLock()
            return False

        # get option response from server
        try:
            data = self.client.recv(BUFSIZE)
            message = json.loads(data)
            # check if an error was received
            if "error" in message.keys():
                logging.error("[%s]: Error received: '%s'."
                    % (self.fileName, message["error"]))
                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return False

            if str(message["message"]).upper() != "OPTION":
                logging.error("[%s]: Wrong option message: "
                    % self.fileName
                    + "'%s'." % message["message"])

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"clientTime": utcTimestamp,
                        "message": message["message"],
                        "error": "option message expected"}
                    self.client.send(json.dumps(message))
                except Exception as e:
                    pass

                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return False

            # check if the received type is the correct one
            if str(message["payload"]["type"]).upper() != "RESPONSE":
                logging.error("[%s]: response expected."
                    % self.fileName)

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
            logging.exception("[%s]: Receiving option response failed."
                % self.fileName)
            # clean up session before exiting
            self._cleanUpSessionForClosing()
            self._releaseLock()
            return False

        logging.debug("[%s]: Received valid option response." % self.fileName)

        self.lastRecv = int(time.time())
        self._releaseLock()

        return True


    # this function reconnects the client to the server
    def reconnect(self):

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


    # this function sends a keep alive (PING request) to the server
    # to keep the connection alive and to check if the connection
    # is still alive
    def sendKeepalive(self):

        pingMessage = self._buildPingMessage()

        # initiate transaction with server and acquire lock
        if not self._initiateTransaction("ping",
            len(pingMessage), acquireLock=True):

            # clean up session before exiting
            self._cleanUpSessionForClosing()
            return False

        # Send ping request.
        try:
            logging.debug("[%s]: Sending ping message." % self.fileName)
            self.client.send(pingMessage)

        except Exception as e:
            logging.exception("[%s]: Sending ping to server failed."
                % self.fileName)

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
                logging.error("[%s]: Error received: '%s'."
                    % (self.fileName, message["error"]))
                # clean up session before exiting
                self._cleanUpSessionForClosing()
                self._releaseLock()
                return False

            if str(message["message"]).upper() != "PING":
                logging.error("[%s]: Wrong ping message: "
                    % self.fileName
                    + "'%s'." % message["message"])

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
                logging.error("[%s]: response expected."
                    % self.fileName)

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
            logging.exception("[%s]: Receiving ping response failed."
                % self.fileName)
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

    def __init__(self, connection, pingInterval, smtpAlert):
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

        # check every 5 seconds if the time of the last received data
        # from the server lies too far in the past
        while True:

            # wait 5 seconds before checking time of last received data
            for i in range(5):
                if self.exitFlag:
                    logging.info("[%s]: Exiting ConnectionWatchdog."
                        % self.fileName)
                    return
                time.sleep(1)

            # check if the client is still connected to the server
            if not self.connection.isConnected:

                logging.error("[%s]: Connection to server has died. "
                    % self.fileName)

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
                        if not self.smtpAlert is None:
                            self.smtpAlert.sendCommunicationAlertClear()

                        logging.info("[%s] Reconnecting successful "
                            % self.fileName
                            + "after %d attempts."
                            % self.connectionRetries)

                        self.connectionRetries = 1
                        break
                    self.connectionRetries +=1

                    logging.error("[%s]: Reconnecting failed. "
                        % self.fileName + "Retrying in 5 seconds.")
                    time.sleep(5)

                continue

            # check if the time of the data last received lies too far in the
            # past => send ping to check connection
            utcTimestamp = int(time.time())
            if (utcTimestamp - self.connection.lastRecv) > self.pingInterval:
                logging.debug("[%s]: Ping interval exceeded."
                        % self.fileName)

                # check if PING failed
                if not self.connection.sendKeepalive():
                    logging.error("[%s]: Connection to server has died. "
                        % self.fileName)

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
                            # => send email that communication
                            # problems are solved
                            if not self.smtpAlert is None:
                                self.smtpAlert.sendCommunicationAlertClear()

                            logging.info("[%s] Reconnecting successful "
                                % self.fileName
                                + "after %d attempts."
                                % self.connectionRetries)

                            self.connectionRetries = 1
                            break
                        self.connectionRetries +=1

                        logging.error("[%s]: Reconnecting failed. "
                            % self.fileName + "Retrying in 5 seconds.")
                        time.sleep(5)


    # sets the exit flag to shut down the thread
    def exit(self):
        self.exitFlag = True
        return


# this class handles the receive part of the client
class Receiver(threading.Thread):

    def __init__(self, connection):
        threading.Thread.__init__(self)
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
        return