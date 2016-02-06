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
BUFSIZE = 16384


# this class handles the communication with the incoming client connection
class ClientCommunication:

	def __init__(self, sslSocket, clientAddress, clientPort, globalData):
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
		self.alertLevels = self.globalData.alertLevels
		self.asyncOptionExecuters = self.globalData.asyncOptionExecuters
		self.asyncOptionExecutersLock \
			= self.globalData.asyncOptionExecutersLock
		self.serverSessions = self.globalData.serverSessions

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

		# version and revision of client
		self.clientVersion = None
		self.clientRev = None

		# the id of the client
		self.nodeId = 0

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

		# flag that states if the server is already trying to initiate a
		# transaction with the client
		self.transactionInitiation = False


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock (%s:%d)." % (self.fileName,
			self.clientAddress, self.clientPort))
		self.connectionLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock (%s:%d)." % (self.fileName,
			self.clientAddress, self.clientPort))
		self.connectionLock.release()


	# this internal function cleans up the session before releasing the
	# lock and exiting/closing the session
	def _cleanUpSessionForClosing(self):
		# set flag that the initialization process of 
		# the client is finished as false
		self.clientInitialized = False

		# mark node as not connected
		self.storage.markNodeAsNotConnected(self.nodeId)

		# wake up manager update executer
		self.managerUpdateExecuter.forceStatusUpdate = True
		self.managerUpdateExecuter.managerUpdateEvent.set()


	# this internal function that tries to initiate a transaction with
	# the client (and acquires a lock if it is told to do so)
	def _initiateTransaction(self, messageType, acquireLock=False):

		# try to get the exclusive state to be allowed to iniate a transaction
		# with the client
		while True:

			# check if locks should be handled or not
			if acquireLock:
				self._acquireLock()

			# check if another thread is already trying to initiate a
			# transaction with the client
			if self.transactionInitiation:

				logging.debug("[%s]: Transaction initiation " % self.fileName
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
			# => start to initate transaction with client
			else:

				logging.debug("[%s]: Got exclusive " % self.fileName
					+ "transaction initiation state (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# set transaction initiation flag to true
				# to signal other threads that a transaction is already
				# tried to initate
				self.transactionInitiation = True
				break

		# now we are in a exclusive state to iniate a transaction with
		# the client
		while True:

			# generate a random "unique" transaction id
			# for this transaction
			transactionId = random.randint(0, 0xffffffff)

			# send RTS (request to send) message
			logging.debug("[%s]: Sending RTS %d message (%s:%d)."
				% (self.fileName, transactionId,
				self.clientAddress, self.clientPort))
			try:

				payload = {"type": "rts", "id": transactionId}
				message = {"serverTime": int(time.time()),
					"message": messageType, "payload": payload}
				self.sslSocket.send(json.dumps(message))

			except Exception as e:
				logging.exception("[%s]: Sending RTS " % self.fileName
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
			logging.debug("[%s]: Receiving CTS (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			try:

				data = self.sslSocket.recv(BUFSIZE).strip()
				message = json.loads(data)

				# check if an error was received
				# (only log error)
				if "error" in message.keys():
					logging.error("[%s]: Error received: '%s' (%s:%d)."
						% (self.fileName, message["error"],
						self.clientAddress, self.clientPort))
				# if no error => extract values from message
				else:
					receivedTransactionId = message["payload"]["id"]
					receivedMessageType = str(message["message"])
					receivedPayloadType = \
						str(message["payload"]["type"]).upper()

			except Exception as e:
				logging.exception("[%s]: Receiving CTS " % self.fileName
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

				logging.debug("[%s]: Initiate transaction " % self.fileName
					+ "succeeded (%s:%d)."
					% (self.clientAddress, self.clientPort))

				# set transaction initiation flag as false so other
				# threads can try to initiate a transaction with the client
				self.transactionInitiation = False

				break

			# if RTS was not acknowledged
			# => release lock and backoff for a random time then retry again
			else:

				logging.debug("[%s]: Initiate transaction " % self.fileName
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


	# internal function to verify the server/client version
	# and authenticate the client
	def _verifyVersionAndAuthenticate(self):

		# get version and credentials from client
		try:

			data = self.sslSocket.recv(BUFSIZE).strip()
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				logging.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False

		except Exception as e:
			logging.exception("[%s]: Receiving authentication failed (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))
			return False

		# check if an authentication message was received
		try:
			if str(message["message"]).upper() != "AUTHENTICATION":
				logging.error("[%s]: Wrong authentication message: "
					% self.fileName
					+ "'%s' (%s:%d)." % (message["message"],
					self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()), 
						"message": message["message"],
						"error": "authentication message expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# check if the received type is the correct one
			if str(message["payload"]["type"]).upper() != "REQUEST":
				logging.error("[%s]: request expected (%s:%d)." 
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

			logging.exception("[%s]: Message not valid (%s:%d)." 
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

		# verify version
		try:
			self.clientVersion = float(message["payload"]["version"])
			self.clientRev = int(message["payload"]["rev"])

			# check if used protocol version is compatible
			if int(self.serverVersion * 10) != int(self.clientVersion * 10):

				logging.error("[%s]: Version not compatible. " % self.fileName
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

				return False

		except Exception as e:

			logging.exception("[%s]: Version not valid (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "version not valid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		logging.debug("[%s]: Received client version: '%.3f-%d' (%s:%d)." 
			% (self.fileName, self.clientVersion, self.clientRev,
			self.clientAddress, self.clientPort))

		# get user credentials
		try:

			self.username = str(message["payload"]["username"])
			password = str(message["payload"]["password"])			

		except Exception as e:

			logging.exception("[%s]: No user credentials (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "no user credentials"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		logging.debug("[%s]: Received username and password for '%s' (%s:%d)." 
			% (self.fileName, self.username, self.clientAddress, 
			self.clientPort))

		# check if username is already in use
		# => terminate connection
		for serverSession in self.serverSessions:

			# ignore THIS server session and not existing once
			if (serverSession.clientComm is None
				or serverSession.clientComm == self):
				continue

			if serverSession.clientComm.username == self.username:

				logging.error("[%s]: Username already in use (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "username already in use"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

		# check if the given user credentials are valid
		if not self.userBackend.areUserCredentialsValid(self.username,
			password):

			logging.error("[%s]: Invalid user credentials " % self.fileName
				+ "(%s:%d)." % (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": message["message"],
					"error": "invalid user credentials"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		# send authentication response
		try:

			payload = {"type": "response",
				"result": "ok",
				"version": self.serverVersion,
				"rev" : self.serverRev}
			message = {"serverTime": int(time.time()),
				"message": "authentication", "payload": payload}
			self.sslSocket.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending authentication response "
				% self.fileName
				+ "failed (%s:%d)." % (self.clientAddress, self.clientPort))
			return False

		return True


	# internal function to register the client (add it to the database
	# or check if it is known)
	def _registerClient(self):

		# get registration from client
		try:

			data = self.sslSocket.recv(BUFSIZE).strip()
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				logging.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False
			
		except Exception as e:
			logging.exception("[%s]: Receiving registration failed (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))
			return False

		try:
			# check if a registration message was received
			if str(message["message"]).upper() != "REGISTRATION":
				logging.error("[%s]: Wrong registration message: "
					% self.fileName
					+ "'%s' (%s:%d)." % (message["message"],
					self.clientAddress, self.clientPort))

				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "registration message expected"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			# check if the received type is the correct one
			if str(message["payload"]["type"]).upper() != "REQUEST":
				logging.error("[%s]: request expected (%s:%d)." 
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

			logging.exception("[%s]: Message not valid (%s:%d)." 
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
			self.hostname = str(message["payload"]["hostname"])
			self.nodeType = str(message["payload"]["nodeType"])
			self.instance = str(message["payload"]["instance"])

		except Exception as e:

			logging.exception("[%s]: Registration message not valid (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))

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

			logging.error("[%s]: Node type or instance " % self.fileName
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

		logging.debug("[%s]: Received node registration %s:%s (%s:%d)." 
				% (self.fileName, self.hostname, self.nodeType,
					self.clientAddress, self.clientPort))

		# add node to database
		if not self.storage.addNode(self.username, self.hostname,
			self.nodeType, self.instance, self.clientVersion, self.clientRev):
			logging.error("[%s]: Unable to add node to database." 
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

		# check if the type of the node got sensors
		# => add sensor data to the database
		if self.nodeType == "sensor":

			# extract sensors from message
			try:
				sensors = message["payload"]["sensors"]

				# check if sensors is of type list
				if not isinstance(sensors, list):
					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "sensors not of type list"}
						self.sslSocket.send(json.dumps(message))
					except Exception as e:
						pass

					return False

			except Exception as e:
				logging.exception("[%s]: No sensors in message (%s:%d)." 
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

			logging.debug("[%s]: Sensor count: %d (%s:%d)." 
					% (self.fileName, sensorCount, self.clientAddress,
					self.clientPort))

			for i in range(sensorCount):

				# extract sensor data
				try:
					sensorId = int(sensors[i]["clientSensorId"])
					alertDelay = int(sensors[i]["alertDelay"])

					alertLevels = sensors[i]["alertLevels"]
					# check if alertLevels is a list
					if not isinstance(alertLevels, list):
						# send error message back
						try:
							message = {"serverTime": int(time.time()),
								"message": message["message"],
								"error": "alertLevels not of type list"}
							self.sslSocket.send(json.dumps(message))
						except Exception as e:
							pass

						return False
					# check if all elements of the alertLevels list 
					# are of type int
					if not all(isinstance(item, int) for item in alertLevels):
						# send error message back
						try:
							message = {"serverTime": int(time.time()),
								"message": message["message"],
								"error": "alertLevels items not of type int"}
							self.sslSocket.send(json.dumps(message))
						except Exception as e:
							pass

						return False						

					description = str(sensors[i]["description"])
				except Exception as e:
					logging.exception("[%s]: Sensor data " % self.fileName
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

				logging.debug("[%s]: Received sensor: " % self.fileName
					+ "%d:%d:'%s' (%s:%d)." 
					% (sensorId, alertDelay, description,
					self.clientAddress, self.clientPort))

				for tempAlertLevel in alertLevels:
					logging.debug("[%s]: Sensor has alertLevel: %d (%s:%d)."
						% (self.fileName, tempAlertLevel, 
						self.clientAddress, self.clientPort))

					# check if alert level is configured on server
					found = False
					for configuredAlertLevel in self.alertLevels:
						if tempAlertLevel == configuredAlertLevel.level:
							found = True
					if not found:
						logging.error("[%s]: Alert level does " % self.fileName
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

			# add sensors to database
			if not self.storage.addSensors(self.username, sensors):
				logging.error("[%s]: Unable to add " % self.fileName
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

		# check if the type of the node is alert
		# => register alerts
		elif self.nodeType == "alert":

			# extract alerts from message
			try:
				alerts = message["payload"]["alerts"]

				# check if alerts is of type list
				if not isinstance(alerts, list):
					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "alerts not of type list"}
						self.sslSocket.send(json.dumps(message))
					except Exception as e:
						pass

					return False

			except Exception as e:
				logging.exception("[%s]: No alerts "
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

			logging.debug("[%s]: Received alerts count: %d (%s:%d)." 
					% (self.fileName, alertCount, self.clientAddress,
					self.clientPort))

			for i in range(alertCount):

				# extract sensor data
				try:
					alertId = int(alerts[i]["clientAlertId"])
					description = str(alerts[i]["description"])
					alertLevels = alerts[i]["alertLevels"]

					# check if alertLevels is a list
					if not isinstance(alertLevels, list):
						# send error message back
						try:
							message = {"serverTime": int(time.time()),
								"message": message["message"],
								"error": "alertLevels not of type list"}
							self.sslSocket.send(json.dumps(message))
						except Exception as e:
							pass

						return False
					# check if all elements of the alertLevels list 
					# are of type int
					if not all(isinstance(item, int) for item in alertLevels):
						# send error message back
						try:
							message = {"serverTime": int(time.time()),
								"message": message["message"],
								"error": "alertLevels items not of type int"}
							self.sslSocket.send(json.dumps(message))
						except Exception as e:
							pass

						return False

					# check if alert level is configured on server
					found = False
					for recvAlertLevel in alertLevels:
						for confAlertLevel in self.alertLevels:
							if recvAlertLevel == confAlertLevel.level:
								found = True
								break

						if not found:
							logging.error("[%s]: Alert level %d does " 
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
					logging.exception("[%s]: Alert data " % self.fileName
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

				logging.debug("[%s]: Received alert: " % self.fileName
					+ "%d:'%s' (%s:%d)." 
					% (alertId, description,
					self.clientAddress, self.clientPort))

			# add alerts to database
			if not self.storage.addAlerts(self.username, alerts):
				logging.error("[%s]: Unable to add " % self.fileName
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
				manager = message["payload"]["manager"]

				# check if manager is of type dict
				if not isinstance(manager, dict):
					# send error message back
					try:
						message = {"serverTime": int(time.time()),
							"message": message["message"],
							"error": "manager not of type dict"}
						self.sslSocket.send(json.dumps(message))
					except Exception as e:
						pass

					return False

			except Exception as e:
				logging.exception("[%s]: No manager in message (%s:%d)." 
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
				description = str(manager["description"])
			except Exception as e:
				logging.exception("[%s]: Manager data " % self.fileName
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

			logging.debug("[%s]: Received manager information (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

			# add manager to database
			if not self.storage.addManager(self.username, manager):
				logging.error("[%s]: Unable to add " % self.fileName
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

		# if nodetype is not sensor, alert or manager => not known
		else:
			logging.error("[%s]: Node type not known '%s'."
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
				"message": "registration", "payload": payload}
			self.sslSocket.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending registration response "
				% self.fileName
				+ "failed (%s:%d)." % (self.clientAddress, self.clientPort))
			return False

		return True


	# this internal function handles the sent option change from a manager
	# and updates it in the database
	def _optionHandler(self, incomingMessage):

		# extract option type and value from message
		try:
			optionType = str(incomingMessage["payload"]["optionType"])
			optionValue = float(incomingMessage["payload"]["value"])
			optionDelay = int(incomingMessage["payload"]["timeDelay"])
		except Exception as e:
			logging.exception("[%s]: Received option " % self.fileName
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
			logging.exception("[%s]: Sending option " % self.fileName
				+ "response failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))
			return False

		return True


	# this internal function handles the sent state of the sensors 
	# from a node and updates it in the database
	def _statusHandler(self, incomingMessage):

		# extract sensors from message
		try:
			sensors = incomingMessage["payload"]["sensors"]

			# check if sensors are of type list
			if not isinstance(sensors, list):
				# send error message back
				try:
					message = {"serverTime": int(time.time()),
						"message": message["message"],
						"error": "sensors not of type list"}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					pass

				return False

		except Exception as e:
			logging.exception("[%s]: Received status " % self.fileName
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
			logging.error("[%s]: Received sensors count " % self.fileName
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

		# extract sensor data
		# generate a list of tuples with (remoteSensorId, state)
		stateList = list()
		try:
			for i in range(self.sensorCount):			
				stateList.append((int(sensors[i]["clientSensorId"]),
					int(sensors[i]["state"])))
		except Exception as e:
			logging.exception("[%s]: Received sensor " % self.fileName
				+ "invalid (%s:%d)."
				% (self.clientAddress, self.clientPort))

			# send error message back
			try:
				message = {"serverTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "received sensor invalid"}
				self.sslSocket.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		logging.debug("[%s]: Received new sensor states (%s:%d)." 
			% (self.fileName, self.clientAddress, self.clientPort))

		# update the sensor state in the database
		if not self.storage.updateSensorState(self.nodeId, stateList):
			logging.error("[%s]: Not able to update sensor state (%s:%d)."
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

		# send status response
		try:
			payload = {"type": "response", "result": "ok"}
			message = {"serverTime": int(time.time()),
				"message": "status", "payload": payload}
			self.sslSocket.send(json.dumps(message))
		except Exception as e:
			logging.exception("[%s]: Sending status " % self.fileName
				+ "response failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))
			return False

		return True


	# this internal function handles received sensor alerts
	# (adds them to the database and wakes up the sensor alert executer)
	def _sensorAlertHandler(self, incomingMessage):

		# extract sensor alert values
		try:
			remoteSensorId = int(incomingMessage["payload"]["clientSensorId"])
			state = int(incomingMessage["payload"]["state"])
			changeState = bool(incomingMessage["payload"]["changeState"])

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
			logging.exception("[%s]: Received sensor alert " % self.fileName
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

		# add sensor alert to database
		if not self.storage.addSensorAlert(self.nodeId, remoteSensorId,
			state, changeState, dataJson):
			logging.error("[%s]: Not able to add sensor alert (%s:%d)."
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
			logging.exception("[%s]: Sending sensor alert " % self.fileName
				+ "response failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))
			return False

		return True


	# this internal function handles received state changes
	# (updates them in the database and wakes up the manager update executer)
	def _stateChangeHandler(self, incomingMessage):

		# extract state change values
		try:
			remoteSensorId = int(incomingMessage["payload"]["clientSensorId"])
			state = int(incomingMessage["payload"]["state"])
		except Exception as e:
			logging.exception("[%s]: Received state change " % self.fileName
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

		# update sensor state
		stateTuple = (remoteSensorId, state)
		stateList = list()
		stateList.append(stateTuple)
		if not self.storage.updateSensorState(self.nodeId, stateList):
			logging.error("[%s]: Not able to change sensor state (%s:%d)."
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

		# get sensorId from database => append to state change queue
		# => wake up manager update executer
		sensorId = self.storage.getSensorId(self.nodeId, remoteSensorId)
		if sensorId is None:
			logging.error("[%s]: Not able to get sensorId (%s:%d)."
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
			logging.exception("[%s]: Sending state change " % self.fileName
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
	def _sendManagerAllInformation(self):

		# get a list from database of 
		# list[0] = optionCount
		# list[1] = list(tuples of (type, value))
		# list[2] = nodeCount
		# list[3] = list(tuples of (nodeId, hostname, nodeType, instance,
		# connected, version, rev, username))
		# list[4] = sensorCount
		# list[5] = list(tuples of (nodeId, sensorId, alertDelay,
		# description, lastStateUpdated, state, remoteSensorId))
		# list[6] = managerCount
		# list[7] = list(tuples of (nodeId, managerId, description))
		# list[8] = alertCount
		# list[9] = list(tuples of (nodeId, alertId, description,
		# remoteAlertId))	
		alertSystemInformation = self.storage.getAlertSystemInformation()
		if alertSystemInformation == None:
			logging.error("[%s]: Getting alert system " % self.fileName
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

			return False
		optionCount = alertSystemInformation[0]
		optionsInformation = alertSystemInformation[1]
		nodeCount = alertSystemInformation[2]
		nodesInformation = alertSystemInformation[3]
		sensorCount = alertSystemInformation[4]
		sensorsInformation = alertSystemInformation[5]
		managerCount = alertSystemInformation[6]
		managersInformation = alertSystemInformation[7]
		alertCount = alertSystemInformation[8]
		alertsInformation = alertSystemInformation[9]

		# generating options list
		options = list()
		for i in range(optionCount):
			tempDict = {"type": optionsInformation[i][0],
				"value": optionsInformation[i][1]}
			options.append(tempDict)

		# generating nodes list
		nodes = list()
		for i in range(nodeCount):
			tempDict = {"nodeId": nodesInformation[i][0],
				"hostname": nodesInformation[i][1],
				"nodeType": nodesInformation[i][2],
				"instance": nodesInformation[i][3],
				"connected": nodesInformation[i][4],
				"version": nodesInformation[i][5],
				"rev": nodesInformation[i][6],
				"username": nodesInformation[i][7]}
			nodes.append(tempDict)

		# generating sensors list
		sensors = list()
		for i in range(sensorCount):

			sensorId = sensorsInformation[i][1]

			# create list of alert levels of this sensor
			dbAlertLevels = self.storage.getSensorAlertLevels(sensorId)
			alertLevels = list()
			for tempAlertLevel in dbAlertLevels:
				alertLevels.append(tempAlertLevel[0])

			tempDict = {"nodeId": sensorsInformation[i][0],
				"sensorId": sensorId,
				"alertDelay": sensorsInformation[i][2],
				"alertLevels": alertLevels,
				"description": sensorsInformation[i][3],
				"lastStateUpdated": sensorsInformation[i][4],
				"state": sensorsInformation[i][5],
				"remoteSensorId": sensorsInformation[i][6]}
			sensors.append(tempDict)

		# generating managers list
		managers = list()
		for i in range(managerCount):
			tempDict = {"nodeId": managersInformation[i][0],
				"managerId": managersInformation[i][1],
				"description": managersInformation[i][2]}
			managers.append(tempDict)

		# generating alerts list
		alerts = list()
		for i in range(alertCount):

			alertId = alertsInformation[i][1]

			# create list of alert levels of this alert
			dbAlertLevels = self.storage.getAlertAlertLevels(alertId)
			alertLevels = list()
			for tempAlertLevel in dbAlertLevels:
				alertLevels.append(tempAlertLevel[0])

			tempDict = {"nodeId": alertsInformation[i][0],
				"alertId": alertId,
				"alertLevels": alertLevels,
				"description": alertsInformation[i][2],
				"remoteAlertId": alertsInformation[i][3]}
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

		logging.debug("[%s]: Sending status message (%s:%d)." 
			% (self.fileName, self.clientAddress, self.clientPort))

		# sending status message to client
		try:

			payload = {"type": "request",
				"options": options,
				"nodes": nodes,
				"sensors": sensors,
				"managers": managers,
				"alerts": alerts,
				"alertLevels": alertLevels}
			message = {"serverTime": int(time.time()),
				"message": "status", "payload": payload}
			self.sslSocket.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending status " % self.fileName
				+ "message failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		# get status acknowledgement
		logging.debug("[%s]: Receiving status message response (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			data = self.sslSocket.recv(BUFSIZE).strip()
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				logging.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False

			# check if the received message type is the correct one
			if str(message["message"]).upper() != "STATUS":
				logging.error("[%s]: status message expected (%s:%d)." 
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
				logging.error("[%s]: response expected (%s:%d)." 
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
				logging.error("[%s]: Result not ok: '%s' (%s:%d)."
					% (self.fileName, message["payload"]["result"],
					self.clientAddress, self.clientPort))
				return False

		except Exception as e:
			logging.exception("[%s]: Receiving status " % self.fileName
				+ "message response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		self.lastRecv = time.time()

		return True


	# internal function to send a state change to a manager
	def _sendManagerStateChange(self, sensorId, state):

		# send state change message
		logging.debug("[%s]: Sending state change message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			payload = {"type": "request",
				"sensorId": sensorId,
				"state": state}
			message = {"serverTime": int(time.time()),
				"message": "statechange", "payload": payload}
			self.sslSocket.send(json.dumps(message))
		except Exception as e:
			logging.exception("[%s]: Sending state change " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# receive state change response message
		try:
			data = self.sslSocket.recv(BUFSIZE).strip()
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				logging.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False

			# check if the received message type is the correct one
			if str(message["message"]).upper() != "STATECHANGE":
				logging.error("[%s]: state change message expected (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

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
				logging.error("[%s]: response expected (%s:%d)." 
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
				logging.error("[%s]: Result not ok: '%s' (%s:%d)."
					% (self.fileName, message["payload"]["result"],
					self.clientAddress, self.clientPort))
				return False

		except Exception as e:
			logging.exception("[%s]: Receiving state change " % self.fileName
				+ "response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		self.lastRecv = time.time()

		return True


	# internal function to send a sensor alert off to a alert client
	def _sendAlertSensorAlertsOff(self):

		# send sensor alert off message
		logging.debug("[%s]: Sending sensor alerts off message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			payload = {"type": "request"}
			message = {"serverTime": int(time.time()),
				"message": "sensoralertsoff", "payload": payload}
			self.sslSocket.send(json.dumps(message))
		except Exception as e:
			logging.exception("[%s]: Sending sensor alerts " % self.fileName
				+ "off message failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# get sensor alert off acknowledgement
		logging.debug("[%s]: Receiving sensor alerts off " % self.fileName
			+ "response (%s:%d)."
			% (self.clientAddress, self.clientPort))

		try:
			data = self.sslSocket.recv(BUFSIZE).strip()
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				logging.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))
				return False

			# check if the received message type is the correct one
			if str(message["message"]).upper() != "SENSORALERTSOFF":
				logging.error("[%s]: sensor alerts off " % self.fileName
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
				logging.error("[%s]: response expected (%s:%d)." 
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
				logging.error("[%s]: Result not ok: '%s' (%s:%d)."
					% (self.fileName, message["payload"]["result"],
					self.clientAddress, self.clientPort))
				return False

		except Exception as e:
			logging.exception("[%s]: Receiving " % self.fileName
				+ "sensor alerts off response failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		self.lastRecv = time.time()

		return True


	# function that sends a state change to a manager client
	def sendManagerStateChange(self, sensorId, state):

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction("statechange", acquireLock=True):
			return False

		returnValue = self._sendManagerStateChange(sensorId, state)

		self._releaseLock()
		return returnValue


	# function that sends a sensor alert of to a alert client
	def sendAlertSensorAlertsOff(self):

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction("sensoralertsoff", acquireLock=True):
			return False

		returnValue = self._sendAlertSensorAlertsOff()

		self._releaseLock()
		return returnValue


	# function that sends a full information update to a manager client
	def sendManagerUpdate(self):

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction("status", acquireLock=True):
			return False

		returnValue = self._sendManagerAllInformation()

		self._releaseLock()
		return returnValue


	# function that sends a sensor alert to an alert/manager client
	def sendSensorAlert(self, sensorId, state, alertLevels, description,
		rulesActivated, dataTransfer, data):

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction("sensoralert", acquireLock=True):
			return False

		# send sensor alert message
		logging.debug("[%s]: Sending sensor alert message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:

			# differentiate payload of message when rules are activated or not
			if rulesActivated:
				payload = {"type": "request",
					"sensorId": -1,
					"state": 1,
					"alertLevels": alertLevels,
					"description": description,
					"rulesActivated": True,
					"dataTransfer": False}
			else:

				# differentiate payload of message when data transfer is
				# activated or not
				if dataTransfer:
					payload = {"type": "request",
						"sensorId": sensorId,
						"state": state,
						"alertLevels": alertLevels,
						"description": description,
						"rulesActivated": False,
						"dataTransfer": True,
						"data": data}
				else:
					payload = {"type": "request",
						"sensorId": sensorId,
						"state": state,
						"alertLevels": alertLevels,
						"description": description,
						"rulesActivated": False,
						"dataTransfer": False}

			message = {"serverTime": int(time.time()),
				"message": "sensoralert", "payload": payload}
			self.sslSocket.send(json.dumps(message))
		except Exception as e:
			logging.exception("[%s]: Sending sensor alert " % self.fileName
				+ "message failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			self._releaseLock()
			return False

		# get sensor alert message response
		try:
			data = self.sslSocket.recv(BUFSIZE).strip()
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				logging.error("[%s]: Error received: '%s' (%s:%d)."
					% (self.fileName, message["error"],
					self.clientAddress, self.clientPort))

				self._releaseLock()
				return False

			# check if the received message type is the correct one
			if str(message["message"]).upper() != "SENSORALERT":
				logging.error("[%s]: sensor alert message expected (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

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
				logging.error("[%s]: response expected (%s:%d)." 
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
				logging.error("[%s]: Result not ok: '%s' (%s:%d)."
					% (self.fileName, message["payload"]["result"],
					self.clientAddress, self.clientPort))

				self._releaseLock()
				return False

		except Exception as e:
			logging.exception("[%s]: Receiving sensor alert " % self.fileName
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

		# first verify client/server version
		if not self._verifyVersionAndAuthenticate():
			logging.error("[%s]: Version verification and " % self.fileName
				+ "authentication failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			self._releaseLock()
			return

		# second register client
		if not self._registerClient():
			logging.error("[%s]: Registration failed (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

			self._releaseLock()
			return

		# change the time of the last received message
		# (for the watchdog so it can see that the connection is still alive)
		self.lastRecv = time.time()

		# get the node id from the database for this connection
		self.nodeId = self.storage.getNodeId(self.username)
		if self.nodeId == None:
			logging.error("[%s]: Getting node id failed (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

			self._releaseLock()
			return

		# get the sensor count from the database for this connection
		# if the nodeType is "sensor"
		if self.nodeType == "sensor":
			self.sensorCount = self.storage.getSensorCount(self.nodeId)
			if self.sensorCount == 0:
				logging.error("[%s]: Getting sensor count failed (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))

				self._releaseLock()
				return		

		# mark node as connected in the database
		if not self.storage.markNodeAsConnected(self.nodeId):
			logging.error("[%s]: Not able to mark node as connected (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			self._releaseLock()
			return				

		# check if the type of the node is manager
		# => send all current node information to the manager
		if self.nodeType == "manager":

			if (not self._initiateTransaction("status", acquireLock=False)
				or not self._sendManagerAllInformation()):
				logging.error("[%s]: Not able send status " % self.fileName
					+ "update to client (%s:%d)."
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

		# set flag that the initialization process of the client is finished
		self.clientInitialized = True

		# handle commands
		while 1:

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
					logging.error("[%s]: Error received: '%s' (%s:%d)."
						% (self.fileName, message["error"],
						self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

				# check if RTS was received
				# => acknowledge it
				if str(message["payload"]["type"]).upper() == "RTS":
					receivedTransactionId = int(message["payload"]["id"])

					# received RTS (request to send) message
					logging.debug("[%s]: Received RTS %d message (%s:%d)."
						% (self.fileName, receivedTransactionId,
						self.clientAddress, self.clientPort))

					logging.debug("[%s]: Sending CTS %d message (%s:%d)."
						% (self.fileName, receivedTransactionId,
						self.clientAddress, self.clientPort))

					# send CTS (clear to send) message
					payload = {"type": "cts", "id": receivedTransactionId}
					message = {"serverTime": int(time.time()),
						"message": str(message["message"]),
						"payload": payload}
					self.sslSocket.send(json.dumps(message))

					# after initiating transaction receive
					# actual command 
					data = self.sslSocket.recv(BUFSIZE)
					data = data.strip()

				# if no RTS was received
				# => client does not stick to protocol 
				# => terminate session
				else:

					logging.error("[%s]: Did not receive " % self.fileName
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

				logging.exception("[%s]: Receiving failed " % self.fileName
					+ "(%s:%d)." % (self.clientAddress, self.clientPort))

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			except Exception as e:
				logging.exception("[%s]: Receiving failed " % self.fileName
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
					logging.error("[%s]: Error received: '%s' (%s:%d)."
						% (self.fileName, message["error"],
						self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

				# check if the received type is the correct one
				if str(message["payload"]["type"]).upper() != "REQUEST":
					logging.error("[%s]: request expected (%s:%d)." 
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

				logging.exception("[%s]: Received data " % self.fileName
					+ "not valid: '%s' (%s:%d)." % (data, self.clientAddress,
					self.clientPort))

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			# check if PING was received => send PONG back
			if command == "PING":

				logging.debug("[%s]: Received ping request (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))
				logging.debug("[%s]: Sending ping response (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

				try:
					payload = {"type": "response", "result": "ok"}
					message = {"serverTime": int(time.time()),
						"message": "ping", "payload": payload}
					self.sslSocket.send(json.dumps(message))
				except Exception as e:
					logging.exception("[%s]: Sending ping " % self.fileName
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

				logging.debug("[%s]: Received sensor alert message (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

				if not self._sensorAlertHandler(message):

					logging.error("[%s]: Handling sensor alert failed (%s:%d)."
						% (self.fileName, self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

			# check if STATECHANGE was received
			# => change state of sensor in database
			elif (command == "STATECHANGE"
				and self.nodeType == "sensor"):

				logging.debug("[%s]: Received state change message (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

				if not self._stateChangeHandler(message):

					logging.error("[%s]: Handling sensor " % self.fileName
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

				logging.debug("[%s]: Received status message (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

				if not self._statusHandler(message):

					logging.error("[%s]: Handling status failed (%s:%d)." 
						% (self.fileName, self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

			# check if OPTION was received (for manager only)
			# => change option in the database
			elif (command == "OPTION"
				and self.nodeType == "manager"):

				logging.debug("[%s]: Received option message (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

				if not self._optionHandler(message):

					logging.error("[%s]: Handling option failed (%s:%d)." 
						% (self.fileName, self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()
					self._releaseLock()
					return

			# command is unknown => close connection
			else:
				logging.error("[%s]: Received unknown " % self.fileName
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

		# get reference to global data object
		self.globalData = server.globalData

		# get server certificate/key file
		self.serverCertFile = self.globalData.serverCertFile
		self.serverKeyFile = self.globalData.serverKeyFile

		# get client certificate settings
		self.useClientCertificates = self.globalData.useClientCertificates
		self.clientCAFile = self.globalData.clientCAFile

		# add own server session to the global list of server sessions
		self.globalData.serverSessions.append(self)

		SocketServer.BaseRequestHandler.__init__(self, request, 
			clientAddress, server)
		

	def handle(self):

		logging.info("[%s]: Client connected (%s:%d)." 
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
			logging.exception("[%s]: Unable to initialize SSL " % self.fileName
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
			logging.exception("[%s]: Unable to close SSL " % self.fileName
				+ "connection gracefully with %s:%d." 
			% (self.clientAddress, self.clientPort))

		# remove own server session from the global list of server sessions
		# before closing server session
		try:
			self.globalData.serverSessions.remove(self)
		except:
			pass

		logging.info("[%s]: Client disconnected (%s:%d)." 
			% (self.fileName, self.clientAddress, self.clientPort))


	def closeConnection(self):
		logging.info("[%s]: Closing connection to client (%s:%d)." 
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


# this class checks if the connections to the clients timed out
class ConnectionWatchdog(threading.Thread):

	def __init__(self, globalData, connectionTimeout):
		threading.Thread.__init__(self)

		# get global configured data
		self.globalData = globalData
		self.serverSessions = self.globalData.serverSessions
		self.storage = self.globalData.storage
		self.smtpAlert = self.globalData.smtpAlert
		self.managerUpdateExecuter = self.globalData.managerUpdateExecuter

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# get value for the configured timeout of a session
		self.connectionTimeout = connectionTimeout

		# set exit flag as false
		self.exitFlag = False

		# list of all timed out sensors
		self.timedOutSensors = list()


	def run(self):

		while 1:
			# wait 5 seconds before checking time of last received data
			for i in range(5):
				if self.exitFlag:
					logging.info("[%s]: Exiting ConnectionWatchdog." 
						% self.fileName)
					return
				time.sleep(1)

			# check all server sessions if the connection timed out
			for serverSession in self.serverSessions:

				# check if client communication object exists
				if serverSession.clientComm == None:
					continue

				# check if the time of the data last received lies 
				# too far in the past => kill connection
				if ((time.time() - serverSession.clientComm.lastRecv) 
					>= self.connectionTimeout):
					
					logging.error("[%s]: Connection to " % self.fileName
						+ "client timed out. Closing connection (%s:%d)." 
						% (serverSession.clientAddress,
						serverSession.clientPort))
					
					serverSession.closeConnection()

			# get all node ids from database
			# return value is a list of tuples of (nodeId)
			nodeIds = self.storage.getAllConnectedNodeIds()
			if nodeIds == None:
				logging.error("[%s]: Could not get node " % self.fileName
					+ "ids from database.")
			else:

				# get node id for this server instance
				uniqueID = self.storage.getUniqueID()
				serverNodeId = self.storage.getNodeId(uniqueID)

				# check if node marked as connected got a connection
				# to the server
				for nodeIdTuple in nodeIds:
					nodeId = nodeIdTuple[0]
					found = False

					for serverSession in self.serverSessions:

						# check if client communication object exists
						if serverSession.clientComm == None:
							continue

						if serverSession.clientComm.nodeId == nodeId:
							found = True
							break

					# ignore node id of this server instance
					if nodeId == serverNodeId:
						found = True

					# if no server session was found with the node id
					# => node is not connected to the server
					if not found:
						logging.debug("[%s]: Marking node " % self.fileName
							+ "'%d' as not connected." % nodeId)
						if not self.storage.markNodeAsNotConnected(nodeId):
							logging.error("[%s]: Could not " % self.fileName
								+ "mark node as not connected in database.")
						# wake up manager update executer
						self.managerUpdateExecuter.forceStatusUpdate = True
						self.managerUpdateExecuter.managerUpdateEvent.set()

			# get all sensors that have timed out
			# list of tuples of (sensorId, nodeId,
			# lastStateUpdated, description)
			sensorsTimeoutList = self.storage.getSensorsUpdatedOlderThan(
				int(time.time()) - (2 * self.connectionTimeout))





			# TODO here timeout sensor trigger
			# trigger sensor alert for each NEW sensor that has timed out
			# (check with self.timeoutSensorIds if it is new)
			# Put this in a separate function





			# generate an alert for every timed out sensor
			# (logging + email)
			for sensorTimeoutTuple in sensorsTimeoutList:
				sensorId = sensorTimeoutTuple[0]
				nodeId = sensorTimeoutTuple[1]
				hostname = self.storage.getNodeHostnameById(nodeId)
				lastStateUpdated = sensorTimeoutTuple[2]
				description = sensorTimeoutTuple[3]
				if hostname == None:
					logging.error("[%s]: Could not " % self.fileName
						+ "get hostname for node from database.")
					continue

				logging.critical("[%s]: Sensor " % self.fileName
						+ "with description '%s' from host '%s' timed out. "
						% (description, hostname)
						+ "Last state received at %s"
						% time.strftime("%D %H:%M:%S",
						time.localtime(lastStateUpdated)))

				# send email alert for timed out sensor if activated
				# and sensor is not in list of timed out sensors
				if ((not self.smtpAlert is None)
					and (not sensorId in self.timedOutSensors)):
					if not self.smtpAlert.sendSensorTimeoutAlert(hostname,
						description, lastStateUpdated):
						logging.error("[%s]: Could not send " % self.fileName
							+ "email alert for sensor timeout.")

				# if sensor is not in list of timed out sensors
				# => add it
				if not sensorId in self.timedOutSensors:
					self.timedOutSensors.append(sensorId)






			# TODO here timeout sensor normal
			# check here if in the current list of sensor timeouts
			# is one missing that is still in the self.timeoutSensorIds
			# => set sensor to normal if it is empty
			# => trigger sensor alert with normal state for each sensor
			# that is not timed out anymore (but let timeout sensor
			# still be triggered) <--- can get problems with client site 
			# processing with this method, have to check
			# Put this in a separate function







			# check if a timed out sensor has reconnected and
			# updated its state and generate a notification
			for oldTimedOutSensorId in self.timedOutSensors:
				found = False
				for sensorTimeoutTuple in sensorsTimeoutList:
					currentTimedOutSensorId = sensorTimeoutTuple[0]
					if oldTimedOutSensorId == currentTimedOutSensorId:
						found = True
						break
				if not found:
					self.timedOutSensors.remove(oldTimedOutSensorId)

					# get a tuple of (sensorId, nodeId,
					# remoteSensorId, description, state,
					# lastStateUpdated, alertDelay)
					timedOutSensor = self.storage.getSensorInformation(
						oldTimedOutSensorId)

					# check if the sensor could be found in the database
					if timedOutSensor is None:
						logging.error("[%s]: Could not get " % self.fileName
							+ "sensor with id %d from database."
							% oldTimedOutSensorId)
						continue

					nodeId = timedOutSensor[1]
					hostname = self.storage.getNodeHostnameById(nodeId)
					lastStateUpdated = timedOutSensor[5]
					description = timedOutSensor[3]

					logging.info("[%s]: Sensor " % self.fileName
						+ "with description '%s' from host '%s' has "
						% (description, hostname)
						+ "reconnected. Last state received at %s"
						% time.strftime("%D %H:%M:%S",
						time.localtime(lastStateUpdated)))

					# send email notification that sensor
					# has reconnected if activated
					if not self.smtpAlert is None:
						if not self.smtpAlert.sendSensorTimeoutAlertClear(
							hostname, description, lastStateUpdated):
							logging.error("[%s]: Could not send " 
								% self.fileName
								+ "email notification for reconnected sensor.")
















	# sets the exit flag to shut down the thread
	def exit(self):
		self.exitFlag = True
		return


# this class is used to send messages to the client
# in an asynchronous way to avoid blockings
class AsynchronousSender(threading.Thread):

	def __init__(self, globalData, clientComm):
		threading.Thread.__init__(self)

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# get global configured data
		self.globalData = globalData

		# the communication instance to the client
		self.clientComm = clientComm

		# this option is used when the thread should
		# send a manager update
		self.sendManagerUpdate = False

		# this options are used when the thread should
		# send a sensor alert to the client
		self.sendSensorAlert = False
		self.sensorAlertRulesActivated = None
		self.sensorAlertSensorId = None
		self.sensorAlertState = None
		self.sensorAlertAlertLevels = None
		self.sensorAlertSensorDescription = None
		self.sensorAlertDataTransfer = False
		self.sensorAlertData = None

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
				logging.error("[%s]: Sending status " % self.fileName
						+ "update to manager failed. Client is not a "
						+ "'manager' node (%s:%d)."
						% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

			# sending status update to manager
			if not self.clientComm.sendManagerUpdate():
				logging.error("[%s]: Sending status " % self.fileName
					+ "update to manager failed (%s:%d)."
					% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

		# check if a sensor alert to a manager/alert should be send
		elif self.sendSensorAlert:
			if (self.clientComm.nodeType != "manager"
				and self.clientComm.nodeType != "alert"):
				logging.error("[%s]: Sending sensor " % self.fileName
						+ "alert failed. Client is not a "
						+ "'manager'/'alert' node (%s:%d)."
						% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

			if not self.clientComm.sendSensorAlert(self.sensorAlertSensorId,
				self.sensorAlertState, self.sensorAlertAlertLevels,
				self.sensorAlertSensorDescription,
				self.sensorAlertRulesActivated,
				self.sensorAlertDataTransfer,
				self.sensorAlertData):
				logging.error("[%s]: Sending sensor " % self.fileName
					+ "alert to manager/alert failed (%s:%d)."
					% (self.clientComm.clientAddress,
					self.clientComm.clientPort))

		# check if a state change to a manager should be send
		elif self.sendManagerStateChange:
			if self.clientComm.nodeType != "manager":
				logging.error("[%s]: Sending state " % self.fileName
						+ "change to manager failed. Client is not a "
						+ "'manager' node (%s:%d)."
						% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

			# sending state change to manager
			if not self.clientComm.sendManagerStateChange(
				self.sendManagerStateChangeSensorId,
				self.sendManagerStateChangeState):
				logging.error("[%s]: Sending state " % self.fileName
					+ "change to manager failed (%s:%d)."
					% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

		# check if a sensor alert off to an alert client should be send
		elif self.sendAlertSensorAlertsOff:
			if self.clientComm.nodeType != "alert":
				logging.error("[%s]: Sending sensor " % self.fileName
						+ "alert off to alert failed. Client is not a "
						+ "'alert' node (%s:%d)."
						% (self.clientComm.clientAddress,
					self.clientComm.clientPort))
				return

			# sending sensor alert off to alert client
			if not self.clientComm.sendAlertSensorAlertsOff():
				logging.error("[%s]: Sending sensor " % self.fileName
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
		logging.debug("[%s]: Changing option '%s' to %d in %d seconds."
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
			logging.debug("[%s]: Changing option '%s' to %d was aborted."
				% (self.fileName, self.optionType, self.optionValue))
			return

		logging.debug("[%s]: Changing option '%s' to %d now."
			% (self.fileName, self.optionType, self.optionValue))

		# change option in the database
		if not self.storage.changeOption(self.optionType, self.optionValue):
			logging.error("[%s]: Not able to change option (%s:%d)."
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
				logging.debug("[%s]: Sending sensor " % self.fileName
					+ "alerts off to alert client (%s:%d)."
					% (serverSession.clientComm.clientAddress,
					serverSession.clientComm.clientPort))
				sensorAlertsOffProcess.start()

		# wake up manager update executer
		self.managerUpdateExecuter.forceStatusUpdate = True
		self.managerUpdateExecuter.managerUpdateEvent.set()