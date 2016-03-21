#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import ssl
import socket
import threading
import SocketServer
import time
import logging
import os
import base64
import random
import json
from localObjects import SensorDataType, Sensor

BUFSIZE = 4096


# this class handles the communication with the incoming client connection
class ClientCommunication:

	def __init__(self, sslSocket, clientAddress, clientPort, globalData):
		self.sslSocket = sslSocket
		self.clientAddress = clientAddress
		self.clientPort = clientPort

		# get global configured data
		self.globalData = globalData
		self.logger = self.globalData.logger
		self.serverVersion = self.globalData.version
		self.serverRev = self.globalData.rev
		self.storage = self.globalData.storage
		self.userBackend = self.globalData.userBackend
		self.sensorAlertExecuter = self.globalData.sensorAlertExecuter
		self.managerUpdateExecuter = self.globalData.managerUpdateExecuter
		self.alertLevels = self.globalData.alertLevels
		self.asyncOptionExecuters = self.globalData.asyncOptionExecuters
		self.asyncOptionExecutersLock \
			= self.globalData.asyncOptionExecutersLock
		self.serverSessions = self.globalData.serverSessions
		self.connectionWatchdog = self.globalData.connectionWatchdog

		# time the last message was received by the server
		self.lastRecv = 0.0

		# username that is used by the client to authorize itself
		self.username = None

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


	# internal function that acquires the lock
	def _acquireLock(self):
		self.logger.debug("[%s]: Acquire lock (%s:%d)." % (self.fileName,
			self.clientAddress, self.clientPort))
		self.connectionLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		self.logger.debug("[%s]: Release lock (%s:%d)." % (self.fileName,
			self.clientAddress, self.clientPort))
		self.connectionLock.release()


	# Internal function to check sanity of the alertDelay.
	def _checkMsgAlertDelay(self, alertDelay):

		isCorrect = True
		if not isinstance(alertDelay, int):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "alertDelay not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the alertLevels.
	def _checkMsgAlertLevels(self, alertLevels):

		isCorrect = True
		if not isinstance(alertLevels, list):
			isCorrect = False
		elif not all(isinstance(item, int) for item in alertLevels):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "alertLevels not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the changeState.
	def _checkMsgChangeState(self, changeState):

		isCorrect = True
		if not isinstance(changeState, bool):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "changeState not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the clientAlertId.
	def _checkMsgClientAlertId(self, clientAlertId):

		isCorrect = True
		if not isinstance(clientAlertId, int):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "clientAlertId not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the clientSensorId.
	def _checkMsgClientSensorId(self, clientSensorId):

		isCorrect = True
		if not isinstance(clientSensorId, int):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "clientSensorId not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the description.
	def _checkMsgDescription(self, description):

		isCorrect = True
		if not (isinstance(description, str)
			or isinstance(description, unicode)):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "description not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the hostname.
	def _checkMsgHostname(self, hostname):

		isCorrect = True
		if not (isinstance(hostname, str)
			or isinstance(hostname, unicode)):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "hostname not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the instance.
	def _checkMsgInstance(self, instance):

		isCorrect = True
		if not (isinstance(instance, str)
			or isinstance(instance, unicode)):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "instance not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the nodeType.
	def _checkMsgNodeType(self, nodeType):

		isCorrect = True
		if not (isinstance(nodeType, str)
			or isinstance(nodeType, unicode)):
			isCorrect = False

		nodeTypes = set(["alert", "manager", "sensor"])
		if not nodeType in nodeTypes:
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "nodeType not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the optionType.
	def _checkMsgOptionType(self, optionType):

		isCorrect = True
		if not (isinstance(optionType, str)
			or isinstance(optionType, unicode)):
			isCorrect = False

		if optionType != "alertSystemActive":
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "optionType not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the option timeDelay.
	def _checkMsgOptionTimeDelay(self, timeDelay):

		isCorrect = True
		if not isinstance(timeDelay, int):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "timeDelay not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the option value.
	def _checkMsgOptionValue(self, value):

		isCorrect = True
		if not isinstance(value, float):
			isCorrect = False

		if not (value >= 0.0 and value <= 1.0):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "value not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the persistence.
	def _checkMsgPersistent(self, persistent):

		isCorrect = True
		if not isinstance(persistent, int):
			isCorrect = False

		if not (persistent == 0 or persistent == 1):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "persistent not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the registration alerts list.
	def _checkMsgRegAlertsList(self, alerts):

		isCorrect = True
		if not isinstance(alerts, list):
			isCorrect = False

		# Check each alert if correct.
		for alert in alerts:

			if not "alertLevels" in alert.keys():
				isCorrect = False
				break
			elif not self._checkMsgAlertLevels(alert["alertLevels"]):
				isCorrect = False
				break

			if not "clientAlertId" in alert.keys():
				isCorrect = False
				break
			elif not self._checkMsgClientAlertId(alert["clientAlertId"]):
				isCorrect = False
				break

			if not "description" in alert.keys():
				isCorrect = False
				break
			elif not self._checkMsgDescription(alert["description"]):
				isCorrect = False
				break

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "alerts list not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the registration manager dictionary.
	def _checkMsgRegManagerDict(self, manager):

		isCorrect = True
		if not isinstance(manager, dict):
			isCorrect = False
		else:

			if not "description" in manager.keys():
				isCorrect = False
			elif not self._checkMsgDescription(manager["description"]):
				isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "manager dictionary not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the registration sensors list.
	def _checkMsgRegSensorsList(self, sensors):

		isCorrect = True
		if not isinstance(sensors, list):
			isCorrect = False

		# Check each sensor if correct.
		for sensor in sensors:

			if not "alertDelay" in sensor.keys():
				isCorrect = False
				break
			elif not self._checkMsgAlertDelay(sensor["alertDelay"]):
				isCorrect = False
				break

			if not "alertLevels" in sensor.keys():
				isCorrect = False
				break
			elif not self._checkMsgAlertLevels(sensor["alertLevels"]):
				isCorrect = False
				break

			if not "clientSensorId" in sensor.keys():
				isCorrect = False
				break
			elif not self._checkMsgClientSensorId(sensor["clientSensorId"]):
				isCorrect = False
				break

			if not "dataType" in sensor.keys():
				isCorrect = False
				break
			elif not self._checkMsgSensorDataType(sensor["dataType"]):
				isCorrect = False
				break

			sensorDataType = sensor["dataType"]
			if sensorDataType != SensorDataType.NONE:
				if not "data" in sensor.keys():
					isCorrect = False
					break
				elif not self._checkMsgSensorData(sensor["data"],
					sensorDataType):
					isCorrect = False
					break

			if not "description" in sensor.keys():
				isCorrect = False
				break
			elif not self._checkMsgDescription(sensor["description"]):
				isCorrect = False
				break

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "sensors list not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the sensor data.
	def _checkMsgSensorData(self, data, dataType):

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
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "data not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the sensor data type.
	def _checkMsgSensorDataType(self, dataType):

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
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "dataType not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the status sensors list.
	def _checkMsgStatusSensorsList(self, sensors):

		isCorrect = True
		if not isinstance(sensors, list):
			isCorrect = False

		# Check each sensor if correct.
		for sensor in sensors:

			if not "clientSensorId" in sensor.keys():
				isCorrect = False
				break
			elif not self._checkMsgClientSensorId(sensor["clientSensorId"]):
				isCorrect = False
				break

			if not "dataType" in sensor.keys():
				isCorrect = False
				break
			elif not self._checkMsgSensorDataType(sensor["dataType"]):
				isCorrect = False
				break

			sensorDataType = sensor["dataType"]
			if sensorDataType != SensorDataType.NONE:
				if not "data" in sensor.keys():
					isCorrect = False
					break
				elif not self._checkMsgSensorData(sensor["data"],
					sensorDataType):
					isCorrect = False
					break

			if not "state" in sensor.keys():
				isCorrect = False
				break
			elif not self._checkMsgState(sensor["state"]):
				isCorrect = False
				break

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "sensors list not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# Internal function to check sanity of the state.
	def _checkMsgState(self, state):

		isCorrect = True
		if not isinstance(state, int):
			isCorrect = False
		elif (state != 0 and state != 1):
			isCorrect = False

		if not isCorrect:
			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "state not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# this internal function cleans up the session before releasing the
	# lock and exiting/closing the session
	def _cleanUpSessionForClosing(self):
		# set flag that the initialization process of
		# the client is finished as false
		self.clientInitialized = False

		# mark node as not connected
		self.storage.markNodeAsNotConnected(self.nodeId, logger=self.logger)

		# wake up manager update executer
		self.managerUpdateExecuter.forceStatusUpdate = True
		self.managerUpdateExecuter.managerUpdateEvent.set()


	# this internal function that tries to initiate a transaction with
	# the client (and acquires a lock if it is told to do so)
	def _initiateTransaction(self, messageType, messageSize,
		acquireLock=False):

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
					+ "already tried by another thread. Backing off (%s:%d)."
					% (self.clientAddress, self.clientPort))

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

				self.logger.debug("[%s]: Got exclusive " % self.fileName
					+ "transaction initiation state (%s:%d)."
					% (self.clientAddress, self.clientPort))

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
				% (self.fileName, transactionId,
				self.clientAddress, self.clientPort))
			try:

				payload = {"type": "rts",
					"id": transactionId}
				message = {"serverTime": int(time.time()),
					"size": messageSize,
					"message": messageType,
					"payload": payload}
				self.sslSocket.send(json.dumps(message))

			except Exception as e:
				self.logger.exception("[%s]: Sending RTS " % self.fileName
					+ "failed (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# set transaction initiation flag as false so other
				# threads can try to initiate a transaction with the client
				self.transactionInitiation = False

				# check if locks should be handled or not
				if acquireLock:
					self._releaseLock()

				return False

			# get CTS (clear to send) message
			self.logger.debug("[%s]: Receiving CTS (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			try:
				data = self.sslSocket.recv(BUFSIZE)
				message = json.loads(data)

				# check if an error was received
				# (only log error)
				if "error" in message.keys():
					self.logger.error("[%s]: Error received: '%s' (%s:%d)."
						% (self.fileName, message["error"],
						self.clientAddress, self.clientPort))
				# if no error => extract values from message
				else:
					receivedTransactionId = message["payload"]["id"]
					receivedMessageType = str(message["message"])
					receivedPayloadType = \
						str(message["payload"]["type"]).upper()

			except Exception as e:
				self.logger.exception("[%s]: Receiving CTS " % self.fileName
					+ "failed (%s:%d)."
					% (self.clientAddress, self.clientPort))

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

				self.logger.debug("[%s]: Initiate transaction " % self.fileName
					+ "succeeded (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# set transaction initiation flag as false so other
				# threads can try to initiate a transaction with the client
				self.transactionInitiation = False

				break

			# if RTS was not acknowledged
			# => release lock and backoff for a random time then retry again
			else:

				self.logger.warning("[%s]: Initiate transaction "
					% self.fileName
					+ "failed. Backing off (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# check if locks should be handled or not
				if acquireLock:
					self._releaseLock()

				# backoff random time between 0 and 0.5 second
				backoffTime = float(random.randint(0, 50))/100
				time.sleep(backoffTime)

				# check if locks should be handled or not
				if acquireLock:
					self._acquireLock()

		return True


	# Internal function that builds the sensor alert message.
	def _buildSensorAlertMessage(self, sensorAlert):

		# Differentiate payload of message when rules are activated or not.
		if sensorAlert.rulesActivated:
			payload = {"type": "request",
				"sensorId": sensorAlert.sensorId,
				"state": sensorAlert.state,
				"alertLevels": sensorAlert.alertLevels,
				"description": sensorAlert.description,
				"rulesActivated": True,
				"dataTransfer": sensorAlert.dataTransfer,
				"changeState": sensorAlert.changeState}
		else:

			# Differentiate payload of message when data transfer is
			# activated or not.
			if sensorAlert.dataTransfer:
				payload = {"type": "request",
					"sensorId": sensorAlert.sensorId,
					"state": sensorAlert.state,
					"alertLevels": sensorAlert.alertLevels,
					"description": sensorAlert.description,
					"rulesActivated": False,
					"dataTransfer": True,
					"data": sensorAlert.data,
					"changeState": sensorAlert.changeState}
			else:
				payload = {"type": "request",
					"sensorId": sensorAlert.sensorId,
					"state": sensorAlert.state,
					"alertLevels": sensorAlert.alertLevels,
					"description": sensorAlert.description,
					"rulesActivated": False,
					"dataTransfer": False,
					"changeState": sensorAlert.changeState}

		message = {"serverTime": int(time.time()),
			"message": "sensoralert",
			"payload": payload}
		return json.dumps(message)


	# Internal function that builds the sensor alerts off message.
	def _buildSensorAlertsOffMessage(self):

		payload = {"type": "request"}
		message = {"serverTime": int(time.time()),
			"message": "sensoralertsoff",
			"payload": payload}

		return json.dumps(message)


	# Internal function that builds the state change message.
	def _buildStateChangeMessage(self, sensorId, state):

		payload = {"type": "request",
			"sensorId": sensorId,
			"state": state}
		message = {"serverTime": int(time.time()),
			"message": "statechange",
			"payload": payload}
		return json.dumps(message)


	# Internal function that builds the alert system state message.
	def _buildAlertSystemStateMessage(self):

		# get a list from database of
		# list[0] = list(tuples of (type, value))
		# list[1] = list(tuples of (nodeId, hostname, username, nodeType,
		# instance, connected, version, rev, persistent))
		# list[2] = list(tuples of (sensorId, nodeId, remoteSensorId,
		# description, state, lastStateUpdated, alertDelay, dataType))
		# list[3] = list(tuples of (managerId, nodeId, description))
		# list[4] = list(tuples of (alertId, nodeId, remoteAlertId,
		# description))
		# or None
		alertSystemInformation = self.storage.getAlertSystemInformation(
			logger=self.logger)
		if alertSystemInformation is None:
			self.logger.error("[%s]: Getting alert system " % self.fileName
				+ "information from database failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": "status",
					"error": "not able to get alert system data from database"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return None
		optionsInformation = alertSystemInformation[0]
		nodesInformation = alertSystemInformation[1]
		sensorsInformation = alertSystemInformation[2]
		managersInformation = alertSystemInformation[3]
		alertsInformation = alertSystemInformation[4]

		# generating options list
		options = list()
		for i in range(len(optionsInformation)):
			tempDict = {"type": optionsInformation[i][0],
				"value": optionsInformation[i][1]}
			options.append(tempDict)

		# generating nodes list
		nodes = list()
		for i in range(len(nodesInformation)):
			tempDict = {"nodeId": nodesInformation[i][0],
				"hostname": nodesInformation[i][1],
				"username": nodesInformation[i][2],
				"nodeType": nodesInformation[i][3],
				"instance": nodesInformation[i][4],
				"connected": nodesInformation[i][5],
				"version": nodesInformation[i][6],
				"rev": nodesInformation[i][7],
				"persistent": nodesInformation[i][8]}
			nodes.append(tempDict)

		# generating sensors list
		sensors = list()
		for i in range(len(sensorsInformation)):

			sensorId = sensorsInformation[i][0]

			# create list of alert levels of this sensor
			alertLevels = self.storage.getSensorAlertLevels(sensorId,
				logger=self.logger)

			tempDict = {"sensorId": sensorId,
				"nodeId": sensorsInformation[i][1],
				"remoteSensorId": sensorsInformation[i][2],
				"description": sensorsInformation[i][3],
				"state": sensorsInformation[i][4],
				"lastStateUpdated": sensorsInformation[i][5],
				"alertDelay": sensorsInformation[i][6],
				"alertLevels": alertLevels}
			sensors.append(tempDict)

		# generating managers list
		managers = list()
		for i in range(len(managersInformation)):
			tempDict = {"managerId": managersInformation[i][0],
				"nodeId": managersInformation[i][1],
				"description": managersInformation[i][2]}
			managers.append(tempDict)

		# generating alerts list
		alerts = list()
		for i in range(len(alertsInformation)):

			alertId = alertsInformation[i][0]

			# create list of alert levels of this alert
			dbAlertLevels = self.storage.getAlertAlertLevels(alertId,
				logger=self.logger)
			alertLevels = list()
			for tempAlertLevel in dbAlertLevels:
				alertLevels.append(tempAlertLevel[0])

			tempDict = {"alertId": alertId,
				"nodeId": alertsInformation[i][1],
				"remoteAlertId": alertsInformation[i][2],
				"description": alertsInformation[i][3],
				"alertLevels": alertLevels}
			alerts.append(tempDict)

		# generating alertLevels list
		alertLevels = list()
		for i in range(len(self.alertLevels)):

			tempDict = {"alertLevel": self.alertLevels[i].level,
				"name": self.alertLevels[i].name,
				"triggerAlways": (1 if self.alertLevels[i].triggerAlways
				else 0),
				"rulesActivated": self.alertLevels[i].rulesActivated}
			alertLevels.append(tempDict)

		self.logger.debug("[%s]: Sending status message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))

		payload = {"type": "request",
			"options": options,
			"nodes": nodes,
			"sensors": sensors,
			"managers": managers,
			"alerts": alerts,
			"alertLevels": alertLevels}
		message = {"serverTime": int(time.time()),
			"message": "status",
			"payload": payload}
		return json.dumps(message)


	# Internal function to initialize communication with the client
	# (Authentication, Version verification, Registration).
	def _initializeCommunication(self):

		# First verify client/server version and authenticate client.
		result, messageSize = self._verifyVersionAndAuthenticate()
		if not result:
			self.logger.error("[%s]: Version verification and " % self.fileName
				+ "authentication failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		# Second register client.
		if not self._registerClient(messageSize):
			self.logger.error("[%s]: Client registration failed (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			return False

		return True


	# Internal function to initialize an own logger instance for this
	# connection.
	def _initializeLogger(self):

		self.logger = logging.getLogger("client_" + self.username)
		fh = logging.FileHandler(self.globalData.logdir
			+ "/client_"
			+ self.username
			+ ".log")
		fh.setLevel(self.globalData.loglevel)
		format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s',
			'%m/%d/%Y %H:%M:%S')
		fh.setFormatter(format)
		self.logger.addHandler(fh)

		# Set the logger instance also for the server session.
		for serverSession in self.serverSessions:
			if serverSession.clientComm == self:
				serverSession.setLogger(self.logger)
				break


	# Internal function to verify the server/client version
	# and authenticate the client.
	def _verifyVersionAndAuthenticate(self):

		# get version and credentials from client
		try:
			data = self.sslSocket.recv(BUFSIZE)
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				self.logger.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False, 0

		except Exception as e:
			self.logger.exception("[%s]: Receiving authentication "
				% self.fileName
				+ "failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False, 0

		# Extract message header of received message.
		try:
			messageSize = int(message["size"])

		except Exception as e:
			self.logger.exception("[%s]: Authentication message "
				% self.fileName
				+ "malformed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# Send error message back.
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "message header malformed"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False, 0

		# check if an authentication message was received
		try:
			if str(message["message"]).upper() != "initialization".upper():
				self.logger.error("[%s]: Wrong authentication message: "
					% self.fileName
					+ "'%s' (%s:%d)." % (message["message"],
					self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "initialization message expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False, 0

			# check if the received type is the correct one
			if str(message["payload"]["type"]).upper() != "REQUEST":
				self.logger.error("[%s]: request expected (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "request expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False, 0

		except Exception as e:

			self.logger.exception("[%s]: Message not valid (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "message not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False, 0

		# verify version
		try:
			self.clientVersion = float(message["payload"]["version"])
			self.clientRev = int(message["payload"]["rev"])

			# check if used protocol version is compatible
			if int(self.serverVersion * 10) != int(self.clientVersion * 10):

				self.logger.error("[%s]: Version not compatible. "
					% self.fileName
					+ "Client has version: '%.3f-%d' "
					% (self.clientVersion, self.clientRev)
					+ "and server has '%.3f-%d' (%s:%d)"
					% (self.serverVersion, self.serverRev, self.clientAddress,
					self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "version not compatible"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False, 0

		except Exception as e:

			self.logger.exception("[%s]: Version not valid (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "version not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False, 0

		self.logger.debug("[%s]: Received client version: '%.3f-%d' (%s:%d)."
			% (self.fileName, self.clientVersion, self.clientRev,
			self.clientAddress, self.clientPort))

		# get user credentials
		try:

			self.username = str(message["payload"]["username"])
			password = str(message["payload"]["password"])

		except Exception as e:

			self.logger.exception("[%s]: No user credentials (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "no user credentials"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False, 0

		self.logger.debug("[%s]: Received username and password for "
			% self.fileName
			+ "'%s' (%s:%d)."
			% (self.username, self.clientAddress, self.clientPort))

		# check if username is already in use
		# => terminate connection
		for serverSession in self.serverSessions:

			# ignore THIS server session and not existing once
			if (serverSession.clientComm is None
				or serverSession.clientComm == self):
				continue

			if serverSession.clientComm.username == self.username:

				self.logger.error("[%s]: Username already in use (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "username already in use"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False, 0

		# check if the given user credentials are valid
		if not self.userBackend.areUserCredentialsValid(self.username,
			password):

			self.logger.error("[%s]: Invalid user credentials " % self.fileName
				+ "(%s:%d)." % (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "invalid user credentials"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False, 0

		# send authentication response
		try:
			payload = {"type": "response",
				"result": "ok",
				"version": self.serverVersion,
				"rev" : self.serverRev}
			message = {"serverTime": int(time.time()),
				"message": "initialization",
				"payload": payload}
			self.sslSocket.send(json.dumps(message))

		except Exception as e:
			self.logger.exception("[%s]: Sending authentication response "
				% self.fileName
				+ "failed (%s:%d)." % (self.clientAddress, self.clientPort))
			return False, 0

		return True, messageSize


	# Internal function to register the client (add it to the database
	# or check if it is known).
	def _registerClient(self, messageSize):

		# get registration from client
		try:
			data = ""
			lastSize = 0
			while len(data) < messageSize:
				data += self.sslSocket.recv(BUFSIZE)

				# Check if the size of the received data has changed.
				# If not we detected a possible dead lock.
				if lastSize != len(data):
					lastSize = len(data)
				else:
					self.logger.error("[%s]: Possible dead lock "
						% self.fileName
						+ "detected while receiving data. Closing "
						+ "connection to client (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False

			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				self.logger.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False

		except Exception as e:
			self.logger.exception("[%s]: Receiving registration "
				% self.fileName
				+ "failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		try:
			# check if a registration message was received
			if str(message["message"]).upper() != "initialization".upper():
				self.logger.error("[%s]: Wrong registration message: "
					% self.fileName
					+ "'%s' (%s:%d)." % (message["message"],
					self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "initialization message expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# check if the received type is the correct one
			if str(message["payload"]["type"]).upper() != "REQUEST":
				self.logger.error("[%s]: request expected (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "request expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

		except Exception as e:

			self.logger.exception("[%s]: Message not valid (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "message not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# extract general client configuration from message
		try:
			if not self._checkMsgHostname(message["payload"]["hostname"]):
				self.logger.error("[%s]: Received hostname invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgNodeType(message["payload"]["nodeType"]):
				self.logger.error("[%s]: Received nodeType invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgInstance(message["payload"]["instance"]):
				self.logger.error("[%s]: Received instance invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgPersistent(message["payload"]["persistent"]):
				self.logger.error("[%s]: Received persistent invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False

			self.hostname = message["payload"]["hostname"]
			self.nodeType = message["payload"]["nodeType"]
			self.instance = message["payload"]["instance"]
			self.persistent = message["payload"]["persistent"]

		except Exception as e:

			self.logger.exception("[%s]: Registration message not "
				% self.fileName
				+ "valid (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "registration message not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# check if the given node type and instance are correct
		if not self.userBackend.checkNodeTypeAndInstance(self.username,
			self.nodeType, self.instance):

			self.logger.error("[%s]: Node type or instance " % self.fileName
				+ "for username '%s' is not correct (%s:%d)."
				% (self.username, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "invalid node type or instance"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		self.logger.debug("[%s]: Received node registration %s:%s (%s:%d)."
				% (self.fileName, self.hostname, self.nodeType,
					self.clientAddress, self.clientPort))

		# add node to database
		if not self.storage.addNode(self.username, self.hostname,
			self.nodeType, self.instance, self.clientVersion, self.clientRev,
			self.persistent, logger=self.logger):
			self.logger.error("[%s]: Unable to add node to database."
				% self.fileName)

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "unable to add node to database"}
				self.sslSocket.send(json.dumps(message))
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
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "unable to get node id from database"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# check if the type of the node got sensors
		# => add sensor data to the database
		if self.nodeType == "sensor":

			# extract sensors from message
			try:
				if not self._checkMsgRegSensorsList(
					message["payload"]["sensors"]):
					self.logger.error("[%s]: Received sensors invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
					return False

				sensors = message["payload"]["sensors"]

			except Exception as e:
				self.logger.exception("[%s]: No sensors in message (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "no sensors in message"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			sensorCount = len(sensors)

			self.logger.debug("[%s]: Sensor count: %d (%s:%d)."
					% (self.fileName, sensorCount, self.clientAddress,
					self.clientPort))

			for i in range(sensorCount):

				# extract sensor data
				try:
					sensorId = sensors[i]["clientSensorId"]
					alertDelay = sensors[i]["alertDelay"]
					sensorDataType = sensors[i]["dataType"]
					alertLevels = sensors[i]["alertLevels"]
					description = sensors[i]["description"]

					# Set data field if data type is "none".
					if sensorDataType == SensorDataType.NONE:
						sensors[i]["data"] = None

				except Exception as e:
					self.logger.exception("[%s]: Sensor data "
						% self.fileName
						+ "invalid (%s:%d)." % (self.clientAddress,
						self.clientPort))

					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "sensor data invalid"}
						self.sslSocket.send(json.dumps(message))
					except Exception as e:
						pass

					return False

				self.logger.debug("[%s]: Received sensor: " % self.fileName
					+ "%d:%d:'%s' (%s:%d)."
					% (sensorId, alertDelay, description,
					self.clientAddress, self.clientPort))

				for tempAlertLevel in alertLevels:
					self.logger.debug("[%s]: Sensor has alertLevel: "
						% self.fileName
						+ "%d (%s:%d)."
						% (tempAlertLevel,
						self.clientAddress, self.clientPort))

					# check if alert level is configured on server
					found = False
					for configuredAlertLevel in self.alertLevels:
						if tempAlertLevel == configuredAlertLevel.level:
							found = True
					if not found:
						self.logger.error("[%s]: Alert level does "
							% self.fileName
							+ "not exist in configuration (%s:%d)."
							% (self.clientAddress, self.clientPort))

						# send error message back
						try:
							message = {"serverTime": int(time.time()),
								"message": message["message"],
								"error": "alert level does not exist"}
							self.sslSocket.send(json.dumps(message))
						except Exception as e:
							pass

						return False

				# Create sensor object for the currently received sensor.
				# NOTE: sensor id is not known yet.
				tempSensor = Sensor()
				tempSensor.nodeId = self.nodeId
				tempSensor.remoteSensorId = sensorId
				tempSensor.description = description
				tempSensor.state = 0
				tempSensor.alertLevels = alertLevels
				tempSensor.lastStateUpdated = 0
				tempSensor.alertDelay = alertDelay
				tempSensor.dataType = sensorDataType
				tempSensor.data = sensors[i]["data"]
				self.sensors.append(tempSensor)

			# add sensors to database
			if not self.storage.addSensors(self.username, sensors,
				logger=self.logger):
				self.logger.error("[%s]: Unable to add "
					% self.fileName
					+ "sensors to database (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "unable to add sensors to database"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# Get sensor id for each registered sensor object.
			for sensor in self.sensors:

				sensor.sensorId = self.storage.getSensorId(self.nodeId,
					sensor.remoteSensorId, logger=self.logger)

				if sensor.sensorId is None:
					self.logger.error("[%s]: Unable to get "
						% self.fileName
						+ "sensor id for remote sensor %d (%s:%d)."
						% (sensor.remoteSensorId, self.clientAddress,
						self.clientPort))

					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "unable to get sensor id from database"}
						self.sslSocket.send(json.dumps(message))
					except Exception as e:
						pass

					return False

		# check if the type of the node is alert
		# => register alerts
		elif self.nodeType == "alert":

			# extract alerts from message
			try:
				if not self._checkMsgRegAlertsList(message["payload"]["alerts"]):
					self.logger.error("[%s]: Received alerts invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
					return False

				alerts = message["payload"]["alerts"]

			except Exception as e:
				self.logger.exception("[%s]: No alerts "
					% self.fileName
					+ "in message (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "no alerts in message"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			alertCount = len(alerts)

			self.logger.debug("[%s]: Received alerts count: %d (%s:%d)."
					% (self.fileName, alertCount, self.clientAddress,
					self.clientPort))

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
							self.logger.error("[%s]: Alert level %d does "
								% (self.fileName, recvAlertLevel)
								+ "not exist in configuration (%s:%d)."
								% (self.clientAddress, self.clientPort))

							# send error message back
							try:
								message = {"serverTime": int(time.time()),
									"message": message["message"],
									"error": "alert level does not exist"}
								self.sslSocket.send(json.dumps(message))
							except Exception as e:
								pass

							return False

				except Exception as e:
					self.logger.exception("[%s]: Alert data " % self.fileName
						+ "invalid (%s:%d)." % (self.clientAddress,
						self.clientPort))

					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "alert data invalid"}
						self.sslSocket.send(json.dumps(message))
					except Exception as e:
						pass

					return False

				self.logger.debug("[%s]: Received alert: " % self.fileName
					+ "%d:'%s' (%s:%d)."
					% (alertId, description,
					self.clientAddress, self.clientPort))

			# add alerts to database
			if not self.storage.addAlerts(self.username, alerts,
				logger=self.logger):
				self.logger.error("[%s]: Unable to add " % self.fileName
					+ "alerts to database (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "unable to add alerts to database"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

		# check if the type of the node is manager
		elif self.nodeType == "manager":

			# extract manager from message
			try:
				if not self._checkMsgRegManagerDict(
					message["payload"]["manager"]):
					self.logger.error("[%s]: Received manager invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
					return False

				manager = message["payload"]["manager"]

			except Exception as e:
				self.logger.exception("[%s]: No manager in message (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "no manager in message"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# extraction manager data
			try:
				description = manager["description"]
			except Exception as e:
				self.logger.exception("[%s]: Manager data " % self.fileName
					+ "invalid (%s:%d)." % (self.clientAddress,
					self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "manager data invalid"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			self.logger.debug("[%s]: Received manager information (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

			# add manager to database
			if not self.storage.addManager(self.username, manager,
				logger=self.logger):
				self.logger.error("[%s]: Unable to add " % self.fileName
					+ "manager to database (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "unable to add manager to database"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

		# if nodeType is not known
		else:
			self.logger.error("[%s]: Node type not known '%s'."
				% (self.fileName, self.nodeType))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "node type not known"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# send registration response
		try:

			payload = {"type": "response", "result": "ok"}
			message = {"serverTime": int(time.time()),
				"message": "initialization",
				"payload": payload}
			self.sslSocket.send(json.dumps(message))

		except Exception as e:
			self.logger.exception("[%s]: Sending registration response "
				% self.fileName
				+ "failed (%s:%d)." % (self.clientAddress, self.clientPort))
			return False

		return True


	# this internal function handles the sent option change from a manager
	# and updates it in the database
	def _optionHandler(self, incomingMessage):

		# extract option type and value from message
		try:
			if not self._checkMsgOptionType(
				incomingMessage["payload"]["optionType"]):
				self.logger.error("[%s]: Received optionType invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgOptionValue(
				incomingMessage["payload"]["value"]):
				self.logger.error("[%s]: Received value invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgOptionTimeDelay(
				incomingMessage["payload"]["timeDelay"]):
				self.logger.error("[%s]: Received timeDelay invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False

			optionType = incomingMessage["payload"]["optionType"]
			optionValue = incomingMessage["payload"]["value"]
			optionDelay = incomingMessage["payload"]["timeDelay"]
		except Exception as e:
			self.logger.exception("[%s]: Received option " % self.fileName
				+ "invalid (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "received option invalid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		self.logger.info("[%s]: Option change for type %s "
			% (self.fileName, optionType)
			+ "to value %.3f in %d seconds."
			% (optionValue, optionDelay))

		# check if this option should already be changed by another
		# thread => set flag to abort the change of this thread
		# (acquire and release lock to make the list operations thread safe)
		self.asyncOptionExecutersLock.acquire()
		for asyncOptionExecuter in self.asyncOptionExecuters:
			if asyncOptionExecuter.optionType == optionType:
				asyncOptionExecuter.abortOptionChange = True
		self.asyncOptionExecutersLock.release()

		# start a thread to change the option asynchronously
		asyncOptionExecuter = AsynchronousOptionExecuter(
			self.globalData, optionType, optionValue, optionDelay)
		# set thread to daemon
		# => threads terminates when main thread terminates
		asyncOptionExecuter.daemon = True
		self.asyncOptionExecuters.append(asyncOptionExecuter)
		asyncOptionExecuter.start()

		# send option response
		try:
			payload = {"type": "response", "result": "ok"}
			message = {"serverTime": int(time.time()),
				"message": "option", "payload": payload}
			self.sslSocket.send(json.dumps(message))
		except Exception as e:
			self.logger.exception("[%s]: Sending option " % self.fileName
				+ "response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		return True


	# this internal function handles the sent state of the sensors
	# from a node and updates it in the database
	def _statusHandler(self, incomingMessage):

		# extract sensors from message
		try:
			if not self._checkMsgStatusSensorsList(
				incomingMessage["payload"]["sensors"]):
				self.logger.error("[%s]: Received sensors invalid (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))
				return False

			sensors = incomingMessage["payload"]["sensors"]

		except Exception as e:
			self.logger.exception("[%s]: Received status " % self.fileName
				+ "invalid (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "received status invalid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		if len(sensors) != self.sensorCount:
			self.logger.error("[%s]: Received sensors count " % self.fileName
				+ "invalid. Received: %d; Needed: %d (%s:%d)."
				% (len(sensors), self.sensorCount, self.clientAddress,
				self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "count of sensors not correct"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# Extract sensor states.
		# Generate a list of tuples with (remoteSensorId, state).
		stateList = list()
		try:
			for i in range(self.sensorCount):
				remoteSensorId = sensors[i]["clientSensorId"]

				# Check if client sensor is known.
				sensor = None
				for currentSensor in self.sensors:
					if currentSensor.remoteSensorId == remoteSensorId:
						sensor = currentSensor
						break
				if sensor is None:

					self.logger.error("[%s]: Unknown client sensor id %d "
						% (self.fileName, remoteSensorId)
						+ "(%s:%d)."
						% (self.clientAddress, self.clientPort))

					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "unknown client sensor id"}
						self.sslSocket.send(json.dumps(message))
					except Exception as e:
						pass

					return False

				# Update sensor object.
				sensor.state = sensors[i]["state"]
				sensor.lastStateUpdated = int(time.time())

				stateList.append( (remoteSensorId, sensor.state) )

		except Exception as e:
			self.logger.exception("[%s]: Received sensor state "
				% self.fileName
				+ "invalid (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "received sensor state invalid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		self.logger.debug("[%s]: Received new sensor states (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))

		# update the sensor state in the database
		if not self.storage.updateSensorState(self.nodeId, stateList,
			logger=self.logger):
			self.logger.error("[%s]: Not able to update sensor state (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "not able to update sensor state in database"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# Extract sensor data.
		# Generate a list of tuples with (remoteSensorId, sensorData).
		dataList = list()
		try:
			for i in range(self.sensorCount):
				remoteSensorId = sensors[i]["clientSensorId"]

				# Check if client sensor is known.
				# NOTE: omit check if remote sensor id is valid because we
				# know it is, we checked it earlier.
				sensor = None
				for currentSensor in self.sensors:
					if currentSensor.remoteSensorId == remoteSensorId:
						sensor = currentSensor
						break

				sensorDataType = sensors[i]["dataType"]

				# Check if received message contains the correct data type.
				if sensor.dataType != sensorDataType:

					self.logger.error("[%s]: Received sensor data type for "
						% self.fileName
						+ "remote sensor %d invalid (%s:%d)."
						% (remoteSensorId, self.clientAddress,
						self.clientPort))

					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "received sensor data type wrong"}
						self.sslSocket.send(json.dumps(message))
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

				dataList.append( (remoteSensorId, sensor.data) )

		except Exception as e:
			self.logger.exception("[%s]: Received sensor data "
				% self.fileName
				+ "invalid (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "received sensor data invalid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# Update the sensor data in the database.
		if dataList:

			self.logger.debug("[%s]: Received new sensor data (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			if not self.storage.updateSensorData(self.nodeId, dataList,
				logger=self.logger):
				self.logger.error("[%s]: Not able to update sensor data "
					% self.fileName
					+ "(%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "not able to update sensor data in database"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

		# send status response
		try:
			payload = {"type": "response", "result": "ok"}
			message = {"serverTime": int(time.time()),
				"message": "status", "payload": payload}
			self.sslSocket.send(json.dumps(message))
		except Exception as e:
			self.logger.exception("[%s]: Sending status " % self.fileName
				+ "response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		return True


	# this internal function handles received sensor alerts
	# (adds them to the database and wakes up the sensor alert executer)
	def _sensorAlertHandler(self, incomingMessage):

		# extract sensor alert values
		try:
			if not self._checkMsgClientSensorId(
				incomingMessage["payload"]["clientSensorId"]):
				self.logger.error("[%s]: Received clientSensorId invalid "
						% self.fileName
						+ "(%s:%d)."
						% (self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgState(incomingMessage["payload"]["state"]):
				self.logger.error("[%s]: Received state invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgChangeState(
				incomingMessage["payload"]["changeState"]):
				self.logger.error("[%s]: Received changeState invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False

			remoteSensorId = incomingMessage["payload"]["clientSensorId"]
			state = incomingMessage["payload"]["state"]
			changeState = incomingMessage["payload"]["changeState"]

			# get data of sensor alert if data transfer is activated
			data = None
			dataTransfer = bool(incomingMessage["payload"]["dataTransfer"])
			if dataTransfer:
				data = incomingMessage["payload"]["data"]

				# check if data is of type dict
				if not isinstance(data, dict):
					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "data not of type dict"}
						self.sslSocket.send(json.dumps(message))
					except Exception as e:
						pass

					return False

			# convert received data to a json string
			if data is None:
				dataJson = ""
			else:
				dataJson = json.dumps(data)

		except Exception as e:
			self.logger.exception("[%s]: Received sensor alert "
				% self.fileName
				+ "invalid (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "received sensor alert invalid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		self.logger.info("[%s]: Sensor alert for remote sensor id %d "
			% (self.fileName, remoteSensorId)
			+ "and state %d."
			% state)

		# add sensor alert to database
		if not self.storage.addSensorAlert(self.nodeId, remoteSensorId,
			state, changeState, dataJson, logger=self.logger):
			self.logger.error("[%s]: Not able to add sensor alert (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "not able to add sensor alert to database"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# wake up sensor alert executer
		self.sensorAlertExecuter.sensorAlertEvent.set()

		# send sensor alert response
		try:
			payload = {"type": "response", "result": "ok"}
			message = {"serverTime": int(time.time()),
				"message": "sensoralert", "payload": payload}
			self.sslSocket.send(json.dumps(message))
		except Exception as e:
			self.logger.exception("[%s]: Sending sensor alert " % self.fileName
				+ "response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		return True


	# this internal function handles received state changes
	# (updates them in the database and wakes up the manager update executer)
	def _stateChangeHandler(self, incomingMessage):

		# Extract state change values.
		try:
			if not self._checkMsgClientSensorId(
				incomingMessage["payload"]["clientSensorId"]):
				self.logger.error("[%s]: Received clientSensorId invalid "
						% self.fileName
						+ "(%s:%d)."
						% (self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgState(incomingMessage["payload"]["state"]):
				self.logger.error("[%s]: Received state invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgSensorDataType(
				incomingMessage["payload"]["dataType"]):
				self.logger.error("[%s]: Received dataType invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False
			if not self._checkMsgSensorData(
				incomingMessage["payload"]["data"],
				incomingMessage["payload"]["dataType"]):
				self.logger.error("[%s]: Received data invalid (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))
				return False

			remoteSensorId = incomingMessage["payload"]["clientSensorId"]
			state = incomingMessage["payload"]["state"]
			sensorDataType = incomingMessage["payload"]["dataType"]
			sensorData = None
			if sensorDataType != SensorDataType.NONE:
				sensorData = incomingMessage["payload"]["data"]

			# Check if client sensor is known.
			sensor = None
			for currentSensor in self.sensors:
				if currentSensor.remoteSensorId == remoteSensorId:
					sensor = currentSensor
					break
			if sensor is None:

				self.logger.error("[%s]: Unknown client sensor id %d "
					% (self.fileName, remoteSensorId)
					+ "(%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "unknown client sensor id"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# Check if received message contains the correct data type.
			if sensorDataType != sensor.dataType:

				self.logger.error("[%s]: Received sensor data type for remote "
					% self.fileName
					+ "sensor %d invalid (%s:%d)."
					% (remoteSensorId, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "received sensor data type wrong"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# Update sensor object.
			sensor.state = state
			sensor.lastStateUpdated = int(time.time())
			sensor.data = sensorData

		except Exception as e:
			self.logger.exception("[%s]: Received state change "
				% self.fileName
				+ "invalid (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "received state change invalid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		if sensorDataType == SensorDataType.NONE:
			self.logger.info("[%s]: State change for remote sensor id %d "
				% (self.fileName, remoteSensorId)
				+ "and state %d."
				% state)
		elif sensorDataType == SensorDataType.INT:
			self.logger.info("[%s]: State change for remote sensor id %d "
				% (self.fileName, remoteSensorId)
				+ "and state %d and data %d."
				% (state, sensorData))
		elif sensorDataType == SensorDataType.FLOAT:
			self.logger.info("[%s]: State change for remote sensor id %d "
				% (self.fileName, remoteSensorId)
				+ "and state %d and data %.3f."
				% (state, sensorData))

		# update sensor state
		stateTuple = (remoteSensorId, state)
		stateList = [stateTuple]
		if not self.storage.updateSensorState(self.nodeId, stateList,
			logger=self.logger):
			self.logger.error("[%s]: Not able to change sensor state (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "not able to change sensor state in database"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# Update sensor data if it holds data.
		if sensorDataType != SensorDataType.NONE:
			dataTuple = (remoteSensorId, sensorData)
			dataList = [dataTuple]

			if not self.storage.updateSensorData(self.nodeId, dataList,
				logger=self.logger):
				self.logger.error("[%s]: Not able to change sensor data "
					% self.fileName
					+ "(%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "not able to change sensor data in database"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

		# get sensorId from database => append to state change queue
		# => wake up manager update executer
		sensorId = self.storage.getSensorId(self.nodeId, remoteSensorId,
			logger=self.logger)
		if sensorId is None:
			self.logger.error("[%s]: Not able to get sensorId (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "not able to get sensor id from database"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# send state change response
		try:
			payload = {"type": "response", "result": "ok"}
			message = {"serverTime": int(time.time()),
				"message": "statechange", "payload": payload}
			self.sslSocket.send(json.dumps(message))
		except Exception as e:
			self.logger.exception("[%s]: Sending state change " % self.fileName
				+ "response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		# add state change to queue and wake up manager update executer
		managerStateTuple = (sensorId, state)
		self.managerUpdateExecuter.queueStateChange.append(managerStateTuple)
		self.managerUpdateExecuter.managerUpdateEvent.set()

		return True


	# internal function to send the current state of the alert system
	# to a manager
	def _sendManagerAllInformation(self, alertSystemStateMessage):

		# Sending status message to client.
		try:
			self.logger.debug("[%s]: Sending status message (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			self.sslSocket.send(alertSystemStateMessage)

		except Exception as e:
			self.logger.exception("[%s]: Sending status " % self.fileName
				+ "message failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		# get status acknowledgement
		self.logger.debug("[%s]: Receiving status message response (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			data = self.sslSocket.recv(BUFSIZE)
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				self.logger.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False

			# check if the received message type is the correct one
			if str(message["message"]).upper() != "STATUS":
				self.logger.error("[%s]: status message expected (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "status message expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# check if the received type is the correct one
			if str(message["payload"]["type"]).upper() != "RESPONSE":
				self.logger.error("[%s]: response expected (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "response expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# check if status message was correctly received
			if str(message["payload"]["result"]).upper() != "OK":
				self.logger.error("[%s]: Result not ok: '%s' (%s:%d)."
					% (self.fileName, message["payload"]["result"],
					self.clientAddress, self.clientPort))
				return False

		except Exception as e:
			self.logger.exception("[%s]: Receiving status " % self.fileName
				+ "message response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		self.lastRecv = time.time()

		return True


	# internal function to send a state change to a manager
	def _sendManagerStateChange(self, stateChangeMessage):

		# Send state change message.
		try:
			self.logger.debug("[%s]: Sending state change message (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			self.sslSocket.send(stateChangeMessage)
		except Exception as e:
			self.logger.exception("[%s]: Sending state change " % self.fileName
				+ "failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		# receive state change response message
		try:
			data = self.sslSocket.recv(BUFSIZE)
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				self.logger.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False

			# check if the received message type is the correct one
			if str(message["message"]).upper() != "STATECHANGE":
				self.logger.error("[%s]: state change message "
					% self.fileName
					+ "expected (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "state change message expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# check if the received type is the correct one
			if str(message["payload"]["type"]).upper() != "RESPONSE":
				self.logger.error("[%s]: response expected (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "response expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# check if status message was correctly received
			if str(message["payload"]["result"]).upper() != "OK":
				self.logger.error("[%s]: Result not ok: '%s' (%s:%d)."
					% (self.fileName, message["payload"]["result"],
					self.clientAddress, self.clientPort))
				return False

		except Exception as e:
			self.logger.exception("[%s]: Receiving state change "
				% self.fileName
				+ "response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		self.lastRecv = time.time()

		return True


	# internal function to send a sensor alert off to a alert client
	def _sendAlertSensorAlertsOff(self, sensorAlertsOffMessage):

		# Send sensor alert off message.
		try:
			self.logger.debug("[%s]: Sending sensor alerts off "
				% self.fileName
				+ "message (%s:%d)."
				% (self.clientAddress, self.clientPort))
			self.sslSocket.send(sensorAlertsOffMessage)
		except Exception as e:
			self.logger.exception("[%s]: Sending sensor alerts "
				% self.fileName
				+ "off message failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		# get sensor alert off acknowledgement
		self.logger.debug("[%s]: Receiving sensor alerts off " % self.fileName
			+ "response (%s:%d)."
			% (self.clientAddress, self.clientPort))

		try:
			data = self.sslSocket.recv(BUFSIZE)
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				self.logger.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False

			# check if the received message type is the correct one
			if str(message["message"]).upper() != "SENSORALERTSOFF":
				self.logger.error("[%s]: sensor alerts off " % self.fileName
					+ "message expected (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "sensor alerts off message expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# check if the received type is the correct one
			if str(message["payload"]["type"]).upper() != "RESPONSE":
				self.logger.error("[%s]: response expected (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "response expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# check if status message was correctly received
			if str(message["payload"]["result"]).upper() != "OK":
				self.logger.error("[%s]: Result not ok: '%s' (%s:%d)."
					% (self.fileName, message["payload"]["result"],
					self.clientAddress, self.clientPort))
				return False

		except Exception as e:
			self.logger.exception("[%s]: Receiving " % self.fileName
				+ "sensor alerts off response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		self.lastRecv = time.time()

		return True


	# function that sends a state change to a manager client
	def sendManagerStateChange(self, sensorId, state):

		stateChangeMessage = self._buildStateChangeMessage(sensorId, state)

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction("statechange",
			len(stateChangeMessage), acquireLock=True):
			return False

		returnValue = self._sendManagerStateChange(stateChangeMessage)

		self._releaseLock()
		return returnValue


	# function that sends a sensor alert of to a alert client
	def sendAlertSensorAlertsOff(self):

		sensorAlertsOffMessage = self._buildSensorAlertsOffMessage()

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction("sensoralertsoff",
			len(sensorAlertsOffMessage), acquireLock=True):
			return False

		returnValue = self._sendAlertSensorAlertsOff(sensorAlertsOffMessage)

		self._releaseLock()
		return returnValue


	# function that sends a full information update to a manager client
	def sendManagerUpdate(self):

		alertSystemStateMessage = self._buildAlertSystemStateMessage()
		if not alertSystemStateMessage:
			return False

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction("status",
			len(alertSystemStateMessage), acquireLock=True):
			return False

		returnValue = self._sendManagerAllInformation(alertSystemStateMessage)

		self._releaseLock()
		return returnValue


	# function that sends a sensor alert to an alert/manager client
	def sendSensorAlert(self, sensorAlert):

		sensorAlertMessage = self._buildSensorAlertMessage(sensorAlert)

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction("sensoralert",
			len(sensorAlertMessage), acquireLock=True):
			return False

		# Send sensor alert message.
		try:
			self.logger.debug("[%s]: Sending sensor alert message (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			self.sslSocket.send(sensorAlertMessage)
		except Exception as e:
			self.logger.exception("[%s]: Sending sensor alert " % self.fileName
				+ "message failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			self._releaseLock()
			return False

		# get sensor alert message response
		try:
			data = self.sslSocket.recv(BUFSIZE)
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				self.logger.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))

				self._releaseLock()
				return False

			# check if the received message type is the correct one
			if str(message["message"]).upper() != "SENSORALERT":
				self.logger.error("[%s]: sensor alert message "
					% self.fileName
					+ "expected (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "sensor alert message expected"}
					self.sslSocket.send(json.dumps(message))
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
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "response expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				self._releaseLock()
				return False

			# check if status message was correctly received
			if str(message["payload"]["result"]).upper() != "OK":
				self.logger.error("[%s]: Result not ok: '%s' (%s:%d)."
					% (self.fileName, message["payload"]["result"],
					self.clientAddress, self.clientPort))

				self._releaseLock()
				return False

		except Exception as e:
			self.logger.exception("[%s]: Receiving sensor alert "
				% self.fileName
				+ "response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			self._releaseLock()
			return False

		self.lastRecv = time.time()

		self._releaseLock()
		return True


	# this function handles the communication with the client
	# and receives the commands
	def handleCommunication(self):

		self._acquireLock()

		# set timeout of the socket to configured seconds
		self.sslSocket.settimeout(self.serverReceiveTimeout)

		# Initialize communication with the client
		# (Authentication, Version verification, Registration).
		if not self._initializeCommunication():
			self.logger.error("[%s]: Communication initialization "
				% self.fileName
				+ "failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			self._releaseLock()
			return

		# Now that the communication is initialized, we can switch to our
		# own logger instance for the client.
		self._initializeLogger()
		self.logger.info("[%s]: Communication initialized (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))

		# change the time of the last received message
		# (for the watchdog so it can see that the connection is still alive)
		self.lastRecv = time.time()

		# get the sensor count from the database for this connection
		# if the nodeType is "sensor"
		if self.nodeType == "sensor":
			self.sensorCount = self.storage.getSensorCount(self.nodeId,
				logger=self.logger)
			if self.sensorCount == 0:
				self.logger.error("[%s]: Getting sensor count failed (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))

				self._releaseLock()
				return

		# mark node as connected in the database
		if not self.storage.markNodeAsConnected(self.nodeId,
			logger=self.logger):
			self.logger.error("[%s]: Not able to mark node as "
				% self.fileName
				+ "connected (%s:%d)."
				% (self.clientAddress, self.clientPort))

			self._releaseLock()
			return

		# check if the type of the node is manager
		# => send all current node information to the manager
		if self.nodeType == "manager":

			alertSystemStateMessage = self._buildAlertSystemStateMessage()
			if not alertSystemStateMessage:
				self.logger.error("[%s]: Not able to build "
					% self.fileName
					+ "status update message (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			if (not self._initiateTransaction("status",
				len(alertSystemStateMessage), acquireLock=False)):
				self.logger.error("[%s]: Not able initiate "
					% self.fileName
					+ "status update message (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			if (not self._sendManagerAllInformation(alertSystemStateMessage)):
				self.logger.error("[%s]: Not able send status "
					% self.fileName
					+ "update message (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

		# if node is no manager
		# => send full status update to all manager clients
		else:
			# wake up manager update executer
			self.managerUpdateExecuter.forceStatusUpdate = True
			self.managerUpdateExecuter.managerUpdateEvent.set()

		# If client has registered itself,
		# notify the connection watchdog about the reconnect.
		# NOTE: We do not care if the client is set as "persistent"
		# because it could changed its configuration since the last time seen.
		self.connectionWatchdog.removeNodeTimeout(self.nodeId)

		# Set flag that the initialization process of the client is finished.
		self.clientInitialized = True

		# handle commands
		while True:

			messageSize = 0

			try:
				# set timeout of the socket to 0.5 seconds
				self.sslSocket.settimeout(0.5)

				data = self.sslSocket.recv(BUFSIZE)
				if not data:

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

				# change timeout of the socket back to configured seconds
				self.sslSocket.settimeout(self.serverReceiveTimeout)

				data = data.strip()
				message = json.loads(data)
				# check if an error was received
				if "error" in message.keys():
					self.logger.error("[%s]: Error received: '%s' (%s:%d)."
						% (self.fileName, message["error"],
						self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

				# check if RTS was received
				# => acknowledge it
				if str(message["payload"]["type"]).upper() == "rts".upper():
					receivedTransactionId = int(message["payload"]["id"])
					messageSize = int(message["size"])

					# received RTS (request to send) message
					self.logger.debug("[%s]: Received RTS %d message (%s:%d)."
						% (self.fileName, receivedTransactionId,
						self.clientAddress, self.clientPort))

					self.logger.debug("[%s]: Sending CTS %d message (%s:%d)."
						% (self.fileName, receivedTransactionId,
						self.clientAddress, self.clientPort))

					# send CTS (clear to send) message
					payload = {"type": "cts",
						"id": receivedTransactionId}
					message = {"serverTime": int(time.time()),
						"message": str(message["message"]),
						"payload": payload}
					self.sslSocket.send(json.dumps(message))

					# After initiating transaction receive actual command.
					data = ""
					lastSize = 0
					while len(data) < messageSize:
						data += self.sslSocket.recv(BUFSIZE)

						# Check if the size of the received data has changed.
						# If not we detected a possible dead lock.
						if lastSize != len(data):
							lastSize = len(data)
						else:
							self.logger.error("[%s]: Possible dead lock "
								% self.fileName
								+ "detected while receiving data. Closing "
								+ "connection to client (%s:%d)."
								% (self.clientAddress, self.clientPort))

							# clean up session before exiting
							self._cleanUpSessionForClosing()
							self._releaseLock()
							return

				# if no RTS was received
				# => client does not stick to protocol
				# => terminate session
				else:

					self.logger.error("[%s]: Did not receive " % self.fileName
						+ "RTS. Client sent: '%s' (%s:%d)."
						% (data, self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

			except ssl.SSLError as e:

				# catch receive timeouts
				err = e.args[0]
				if err == "The read operation timed out":

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

				self.logger.exception("[%s]: Receiving failed " % self.fileName
					+ "(%s:%d)." % (self.clientAddress, self.clientPort))

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			except Exception as e:
				self.logger.exception("[%s]: Receiving failed " % self.fileName
					+ "(%s:%d)." % (self.clientAddress, self.clientPort))

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			# extract message type
			try:
				message = json.loads(data)
				# check if an error was received
				if "error" in message.keys():
					self.logger.error("[%s]: Error received: '%s' (%s:%d)."
						% (self.fileName, message["error"],
						self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

				# check if the received type is the correct one
				if str(message["payload"]["type"]).upper() != "REQUEST":
					self.logger.error("[%s]: request expected (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))

					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "request expected"}
						self.sslSocket.send(json.dumps(message))
					except Exception as e:
						pass

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

				# extract the command/message type of the message
				command = str(message["message"]).upper()

			except Exception as e:

				self.logger.exception("[%s]: Received data " % self.fileName
					+ "not valid: '%s' (%s:%d)." % (data, self.clientAddress,
					self.clientPort))

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			# check if PING was received => send PONG back
			if command == "PING":

				self.logger.debug("[%s]: Received ping request (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))
				self.logger.debug("[%s]: Sending ping response (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				try:
					payload = {"type": "response", "result": "ok"}
					message = {"serverTime": int(time.time()),
						"message": "ping", "payload": payload}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					self.logger.exception("[%s]: Sending ping " % self.fileName
						+ "response to client failed (%s:%d)."
						% (self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

			# check if SENSORALERT was received
			# => add to database and wake up alertExecuter
			elif (command == "SENSORALERT"
				and self.nodeType == "sensor"):

				self.logger.info("[%s]: Received sensor alert "
					% self.fileName
					+ "message (%s:%d)."
					% (self.clientAddress, self.clientPort))

				if not self._sensorAlertHandler(message):

					self.logger.error("[%s]: Handling sensor alert "
						% self.fileName
						+ "failed (%s:%d)."
						% (self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

			# check if STATECHANGE was received
			# => change state of sensor in database
			elif (command == "STATECHANGE"
				and self.nodeType == "sensor"):

				self.logger.info("[%s]: Received state change "
					% self.fileName
					+ "message (%s:%d)."
					% (self.clientAddress, self.clientPort))

				if not self._stateChangeHandler(message):

					self.logger.error("[%s]: Handling sensor " % self.fileName
						+ "state change failed (%s:%d)."
						% (self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

			# check if STATUS was received
			# => add new state to the database
			elif (command == "STATUS"
				and self.nodeType == "sensor"):

				self.logger.debug("[%s]: Received status message (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				if not self._statusHandler(message):

					self.logger.error("[%s]: Handling status failed (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

			# check if OPTION was received (for manager only)
			# => change option in the database
			elif (command == "OPTION"
				and self.nodeType == "manager"):

				self.logger.info("[%s]: Received option message (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

				if not self._optionHandler(message):

					self.logger.error("[%s]: Handling option failed (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

			# command is unknown => close connection
			else:
				self.logger.error("[%s]: Received unknown " % self.fileName
					+ "command. Client sent: '%s' (%s:%d)."
					% (data, self.clientAddress, self.clientPort))

				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "unknown command/message type"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			self.lastRecv = time.time()


# this class is used for the threaded tcp server and extends the constructor
# to pass the global configured data to all threads
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

	def __init__(self, globalData, serverAddress, RequestHandlerClass):

		# get reference to global data object
		self.globalData = globalData

		SocketServer.TCPServer.__init__(self, serverAddress,
			RequestHandlerClass)


# this class is used for incoming client connections
class ServerSession(SocketServer.BaseRequestHandler):

	def __init__(self, request, clientAddress, server):

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# ssl socket wrapper
		self.sslSocket = None

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

		# add own server session to the global list of server sessions
		self.globalData.serverSessions.append(self)

		# Get reference to the connection watchdog object
		# to inform it about disconnects.
		self.connectionWatchdog = self.globalData.connectionWatchdog

		SocketServer.BaseRequestHandler.__init__(self, request,
			clientAddress, server)


	def handle(self):

		self.logger.info("[%s]: Client connected (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))

		# try to initiate ssl with client
		try:

			# check if the clients should also be forced to authenticate
			# themselves via a certificate
			if self.useClientCertificates is True:
				self.sslSocket = ssl.wrap_socket(self.request,
					server_side=True, certfile=self.serverCertFile,
					keyfile=self.serverKeyFile, ssl_version=ssl.PROTOCOL_TLSv1,
					cert_reqs=ssl.CERT_REQUIRED, ca_certs=self.clientCAFile)
			else:
				self.sslSocket = ssl.wrap_socket(self.request,
					server_side=True, certfile=self.serverCertFile,
					keyfile=self.serverKeyFile, ssl_version=ssl.PROTOCOL_TLSv1)

		except Exception as e:
			self.logger.exception("[%s]: Unable to initialize SSL "
				% self.fileName
				+ "connection (%s:%d)."
			% (self.clientAddress, self.clientPort))

			# remove own server session from the global list of server sessions
			# before closing server session
			try:
				self.globalData.serverSessions.remove(self)
			except:
				pass

			return

		# give incoming connection to client communication handler
		self.clientComm = ClientCommunication(self.sslSocket,
			self.clientAddress, self.clientPort, self.globalData)
		self.clientComm.handleCommunication()

		# close ssl connection gracefully
		try:
			#self.sslSocket.shutdown(socket.SHUT_RDWR)
			self.sslSocket.close()
		except Exception as e:
			self.logger.exception("[%s]: Unable to close SSL " % self.fileName
				+ "connection gracefully with %s:%d."
			% (self.clientAddress, self.clientPort))

		# remove own server session from the global list of server sessions
		# before closing server session
		try:
			self.globalData.serverSessions.remove(self)
		except:
			pass

		self.logger.info("[%s]: Client disconnected (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))

		# If client was registered and set as "persistent",
		# notify the connection watchdog about the disconnect.
		if (not self.clientComm.nodeId is None
			and self.clientComm.persistent == 1):
			self.connectionWatchdog.addNodePreTimeout(self.clientComm.nodeId)


	def closeConnection(self):
		self.logger.info("[%s]: Closing connection to client (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.shutdown(socket.SHUT_RDWR)
		except:
			pass
		try:
			self.sslSocket.close()
		except:
			pass
		try:
			self.globalData.serverSessions.remove(self)
		except:
			pass


	# Overwrites the used logger instance.
	def setLogger(self, logger):
		self.logger = logger


# this class is used to send messages to the client
# in an asynchronous way to avoid blockings
class AsynchronousSender(threading.Thread):

	def __init__(self, globalData, clientComm):
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

		# this option is used when the thread should
		# send a sensor alert off to the client
		self.sendAlertSensorAlertsOff = False


	def run(self):

		# check if a status update to a manager should be send
		if self.sendManagerUpdate:
			if self.clientComm.nodeType != "manager":
				self.logger.error("[%s]: Sending status " % self.fileName
						+ "update to manager failed. Client is not a "
						+ "'manager' node (%s:%d)."
						% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

			# sending status update to manager
			if not self.clientComm.sendManagerUpdate():
				self.logger.error("[%s]: Sending status " % self.fileName
					+ "update to manager failed (%s:%d)."
					% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

		# check if a sensor alert to a manager/alert should be send
		elif self.sendSensorAlert:
			if (self.clientComm.nodeType != "manager"
				and self.clientComm.nodeType != "alert"):
				self.logger.error("[%s]: Sending sensor " % self.fileName
						+ "alert failed. Client is not a "
						+ "'manager'/'alert' node (%s:%d)."
						% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

			if not self.clientComm.sendSensorAlert(self.sensorAlert):
				self.logger.error("[%s]: Sending sensor " % self.fileName
					+ "alert to manager/alert failed (%s:%d)."
					% (self.clientComm.clientAddress,
					self.clientComm.clientPort))

		# check if a state change to a manager should be send
		elif self.sendManagerStateChange:
			if self.clientComm.nodeType != "manager":
				self.logger.error("[%s]: Sending state " % self.fileName
						+ "change to manager failed. Client is not a "
						+ "'manager' node (%s:%d)."
						% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

			# sending state change to manager
			if not self.clientComm.sendManagerStateChange(
				self.sendManagerStateChangeSensorId,
				self.sendManagerStateChangeState):
				self.logger.error("[%s]: Sending state " % self.fileName
					+ "change to manager failed (%s:%d)."
					% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

		# check if a sensor alert off to an alert client should be send
		elif self.sendAlertSensorAlertsOff:
			if self.clientComm.nodeType != "alert":
				self.logger.error("[%s]: Sending sensor " % self.fileName
						+ "alert off to alert failed. Client is not a "
						+ "'alert' node (%s:%d)."
						% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

			# sending sensor alert off to alert client
			if not self.clientComm.sendAlertSensorAlertsOff():
				self.logger.error("[%s]: Sending sensor " % self.fileName
					+ "alert off to alert client failed (%s:%d)."
					% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return


# this class is used to change an option
# in an asynchronous way to avoid blockings
class AsynchronousOptionExecuter(threading.Thread):

	def __init__(self, globalData, optionType, optionValue, optionDelay):
		threading.Thread.__init__(self)

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# get global configured data
		self.globalData = globalData
		self.logger = self.globalData.logger
		self.storage = self.globalData.storage
		self.serverSessions = self.globalData.serverSessions
		self.asyncOptionExecuters = self.globalData.asyncOptionExecuters
		self.asyncOptionExecutersLock \
			= self.globalData.asyncOptionExecutersLock
		self.managerUpdateExecuter = self.globalData.managerUpdateExecuter

		# get option data to change
		self.optionType = optionType
		self.optionValue = optionValue
		self.optionDelay = optionDelay

		# this flag tells the asynchronous option executer
		# if the option should still be changed or the change be aborted
		# (for example if the option was changed in the time
		# this thread was waiting the given delay time before
		# it changes the option)
		self.abortOptionChange = False


	def run(self):
		self.logger.debug("[%s]: Changing option '%s' to %d in %d seconds."
			% (self.fileName, self.optionType, self.optionValue,
			self.optionDelay))

		# wait time before changing option
		time.sleep(self.optionDelay)

		# remove this thread from the list of active async option executers
		# (acquire and release lock to make the list operations thread safe)
		self.asyncOptionExecutersLock.acquire()
		self.asyncOptionExecuters.remove(self)
		self.asyncOptionExecutersLock.release()

		# check if the option change should be aborted
		if self.abortOptionChange:
			self.logger.debug("[%s]: Changing option '%s' to %d was aborted."
				% (self.fileName, self.optionType, self.optionValue))
			return

		self.logger.debug("[%s]: Changing option '%s' to %d now."
			% (self.fileName, self.optionType, self.optionValue))

		# change option in the database
		if not self.storage.changeOption(self.optionType, self.optionValue):
			self.logger.error("[%s]: Not able to change option (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

		# check if the alert system was deactivated
		# => send sensor alerts off to alert clients
		if (self.optionType == "alertSystemActive"
			and self.optionValue == 0):
			for serverSession in self.serverSessions:
				# ignore sessions which do not exist yet
				# and that are not managers
				if serverSession.clientComm == None:
					continue
				if serverSession.clientComm.nodeType != "alert":
					continue
				if not serverSession.clientComm.clientInitialized:
					continue

				# sending sensor alerts off to alert client
				# via a thread to not block this one
				sensorAlertsOffProcess = AsynchronousSender(
					self.globalData, serverSession.clientComm)
				# set thread to daemon
				# => threads terminates when main thread terminates
				sensorAlertsOffProcess.daemon = True
				sensorAlertsOffProcess.sendAlertSensorAlertsOff = True
				self.logger.debug("[%s]: Sending sensor " % self.fileName
					+ "alerts off to alert client (%s:%d)."
					% (serverSession.clientComm.clientAddress,
					serverSession.clientComm.clientPort))
				sensorAlertsOffProcess.start()

		# wake up manager update executer
		self.managerUpdateExecuter.forceStatusUpdate = True
		self.managerUpdateExecuter.managerUpdateEvent.set()