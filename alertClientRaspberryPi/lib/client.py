#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import socket
import time
import ssl
import threading
import logging
import os
import base64
import ConfigParser
import random
import json
from alert import AsynchronousAlertExecuter
BUFSIZE = 8192


# simple class of an ssl tcp client 
class Client:

	def __init__(self, host, port, caFile):
		self.host = host
		self.port = port
		self.caFile = caFile
		self.socket = None
		self.sslSocket = None


	def connect(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.sslSocket = ssl.wrap_socket(self.socket, 
			ca_certs=self.caFile, cert_reqs=ssl.CERT_REQUIRED, 
			ssl_version=ssl.PROTOCOL_TLSv1)

		self.sslSocket.connect((self.host, self.port))


	def send(self, data):
		count = self.sslSocket.send(data)


	def recv(self, buffsize, timeout=3.0):
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

	def __init__(self, host, port, caFile, username, password, globalData):
		self.host = host
		self.port = port
		self.username = username
		self.password = password
		self.caFile = caFile

		# instance of the used client class
		self.client = None

		# get global configured data
		self.globalData = globalData
		self.version = self.globalData.version
		self.nodeType = self.globalData.nodeType
		self.registeredFile = self.globalData.registeredFile
		self.registered = self.globalData.registered

		# time the last message was received by the client
		self.lastRecv = 0.0

		# this lock is used to only allow one thread to use the communication
		self.connectionLock = threading.BoundedSemaphore(1)

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# list of all unique alert levels that are configured on this client
		self.alertLevels = self.globalData.alertLevels

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


	# this internal function cleans up the session before releasing the
	# lock and exiting/closing the session
	def _cleanUpSessionForClosing(self):
		# set client as disconnected
		self.isConnected = False

		self.client.close()


	# this internal function that tries to initiate a transaction with 
	# the server (and acquires a lock if it is told to do so)
	def _initiateTransaction(self, messageType, acquireLock=False):

		# try to get the exclusive state to be allowed to iniate a transaction
		# with the server
		while True:

			# check if locks should be handled or not
			if acquireLock:
				self._acquireLock()

			# check if another thread is already trying to initiate a
			# transaction with the server
			if self.transactionInitiation:

				logging.debug("[%s]: Transaction initiation " % self.fileName
					+ "already tried by another thread. Backing off.")

				# check if locks should be handled or not
				if acquireLock:
					self._releaseLock()

				# wait 0.5 seconds before trying again to initiate a
				# transaction with the server
				time.sleep(0.5)

				continue

			# if transaction flag is not set
			# => start to initate transaction with server
			else:

				logging.debug("[%s]: Got exclusive " % self.fileName
					+ "transaction initiation state.")

				# set transaction initiation flag to true
				# to signal other threads that a transaction is already
				# tried to initate
				self.transactionInitiation = True
				break

		# now we are in a exclusive state to iniate a transaction with
		# the server
		while True:

			# generate a random "unique" transaction id
			# for this transaction
			transactionId = random.randint(0, 0xffffffff)

			# send RTS (request to send) message
			logging.debug("[%s]: Sending RTS %d message."
				% (self.fileName, transactionId))
			try:
				payload = {"type": "rts", "id": transactionId}
				message = {"message": messageType, "payload": payload}
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

				data = self.client.recv(BUFSIZE).strip()
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

				logging.debug("[%s]: Initiate transaction " % self.fileName
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


	# internal function to verify the server/client version and authenticate
	def _verifyVersionAndAuthenticate(self):

		logging.debug("[%s]: Sending user credentials and version." 
			% self.fileName)

		# send user credentials and version
		try:

			payload = {"type": "request",
				"version": self.version,
				"username": self.username,
				"password": self.password}
			message = {"message": "authentication", "payload": payload}
			self.client.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending user credentials " % self.fileName
				+ "and version failed.")
			return False

		# get authentication response from server
		try:

			data = self.client.recv(BUFSIZE).strip()
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				logging.error("[%s]: Error received: '%s'."
					% (self.fileName, message["error"]))
				return False

			if str(message["message"]).upper() != "AUTHENTICATION":
				logging.error("[%s]: Wrong authentication message: "
					% self.fileName
					+ "'%s'." % message["message"])

				# send error message back
				try:
					message = {"message": message["message"],
						"error": "authentication message expected"}
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
					message = {"message": message["message"],
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

			logging.debug("[%s]: Received server version: '%.1f'." 
				% (self.fileName, version))

			if self.version != version:

				logging.error("[%s]: Version not compatible. " % self.fileName
					+ "Client has version: '%.1f' " % self.version
					+ "and server has '%.1f" % version)

				# send error message back
				try:
					message = {"message": message["message"],
						"error": "version not compatible"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

		except Exception as e:

			logging.exception("[%s]: Version not valid." % self.fileName)

			# send error message back
			try:
				message = {"message": message["message"],
					"error": "version not valid"}
				self.client.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		return True


	# internal function to register the node
	def _registerNode(self):

		# check if node is already registered at server with this
		# configuration
		if self.registered is True:
			configuration = "old"
		else:
			configuration = "new"

		# build alerts list for the message
		alerts = list()
		for alert in self.alerts:
			tempAlert = dict()

			tempAlert["clientAlertId"] = alert.id
			tempAlert["description"] = alert.description
			alerts.append(tempAlert)

		# build alert levels list for the message
		alertLevels = list()
		for alertLevel in self.alertLevels:
			tempAlertLevel = dict()

			tempAlertLevel["alertLevel"] = alertLevel
			alertLevels.append(tempAlertLevel)

		# send registration message
		try:

			payload = {"type": "request",
				"configuration": configuration,
				"hostname": socket.gethostname(),
				"nodeType": self.nodeType,
				"alerts": alerts,
				"alertLevels": alertLevels}
			message = {"message": "registration", "payload": payload}
			self.client.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending registration " % self.fileName
				+ "message.")
			return False

		# get registration response from server
		try:

			data = self.client.recv(BUFSIZE).strip()
			message = json.loads(data)
			# check if an error was received
			if "error" in message.keys():
				logging.error("[%s]: Error received: '%s'."
					% (self.fileName, message["error"]))
				return False

			if str(message["message"]).upper() != "REGISTRATION":
				logging.error("[%s]: Wrong registration message: "
					% self.fileName
					+ "'%s'." % message["message"])

				# send error message back
				try:
					message = {"message": message["message"],
						"error": "registration message expected"}
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
					message = {"message": message["message"],
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

		# check if client was registered before
		# if not => create registered config file
		if self.registered is False:

			# create config from the values that were transmitted to server
			registeredConfig = ConfigParser.RawConfigParser()
			registeredConfig.add_section('general')
			registeredConfig.set('general', 'hostname', socket.gethostname())
			registeredConfig.set('general', 'alertcount', len(self.alerts))

			for i in range(len(self.alerts)):
				registeredConfig.add_section('alert%d' % i)
				registeredConfig.set('alert%d' % i, 'id', self.alerts[i].id)
				registeredConfig.set('alert%d' % i, 'description',
					self.alerts[i].description)

				# generate a string of the alert levels
				alertLevelString = ""
				firstAlertLevel = True
				for alertLevel in self.alerts[i].alertLevels:
					if not firstAlertLevel:
						alertLevelString += ", "
					else:
						firstAlertLevel = False
					alertLevelString += "%d" % alertLevel
				registeredConfig.set('alert%d' % i, 'alertLevels',
					alertLevelString)

			# write config
			try:
				with open(self.registeredFile, 'w') as f:
					registeredConfig.write(f)
			# if there was an exception in creating the file
			# log it but do not abort
			except Exception as e:
				logging.exception("[%s]: Not able to create registered file." 
				% self.fileName)

		return True


	# internal function that handles received sensor alerts
	def _sensorAlertHandler(self, incomingMessage):

		logging.debug("[%s]: Received sensor alert." % self.fileName)
		
		# extract sensor alert values
		try:
			sensorId = int(incomingMessage["payload"]["sensorId"])
			state = int(incomingMessage["payload"]["state"])
			alertLevel = int(incomingMessage["payload"]["alertLevel"])
			description = str(incomingMessage["payload"]["description"])
		except Exception as e:
			logging.exception("[%s]: Received sensor alert " % self.fileName
				+ "invalid.")

			# send error message back
			try:
				message = {"message": incomingMessage["message"],
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
			message = {"message": "sensoralert", "payload": payload}
			self.client.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending sensor alert " % self.fileName
				+ "response failed.")

			return False

		# trigger all alerts that have the same alert level
		for alert in self.alerts:
			if alertLevel in alert.alertLevels:

				# trigger alert in an own thread to not block this one
				alertTriggerProcess = AsynchronousAlertExecuter(alert)
				alertTriggerProcess.sensorDescription = description
				# set thread to daemon
				# => threads terminates when main thread terminates	
				alertTriggerProcess.daemon = True
				alertTriggerProcess.triggerAlert = True
				alertTriggerProcess.start()

		return True


	# internal function that handles received alerts off messages
	def _sensorAlertsOffHandler(self, incomingMessage):

		logging.debug("[%s]: Received sensor alerts off." % self.fileName)
		
		# sending sensor alerts off response
		logging.debug("[%s]: Sending sensor alerts off " % self.fileName
			+ "response message.")
		try:

			payload = {"type": "response", "result": "ok"}
			message = {"message": "sensoralertsoff", "payload": payload}
			self.client.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending sensor alerts " % self.fileName
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
	def initializeCommunication(self):
		
		self._acquireLock()

		# create client instance and connect to the server
		self.client = Client(self.host, self.port, self.caFile)
		try:
			self.client.connect()
		except Exception as e:
			self.client.close()
			logging.exception("[%s]: Connecting to server failed." 
				% self.fileName)

			self._releaseLock()

			return False
		
		# first check version and authenticate
		if not self._verifyVersionAndAuthenticate():
			self.client.close()
			logging.error("[%s]: Version verification and " % self.fileName
				+ "authentication failed.")

			self._releaseLock()

			return False

		# second register node
		if not self._registerNode():
			self.client.close()
			logging.error("[%s]: Registration failed." 
				% self.fileName)			

			self._releaseLock()	

			return False

		# update the time the last data was received by the server
		self.lastRecv = time.time()

		# set client as connected
		self.isConnected = True	

		self._releaseLock()

		return True


	# this function handles the incoming messages from the server
	def handleCommunication(self):

		self._acquireLock()

		# handle commands in an infinity loop
		while 1:

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

					# received RTS (request to send) message
					logging.debug("[%s]: Received RTS %s message."
						% (self.fileName, receivedTransactionId))

					logging.debug("[%s]: Sending CTS %s message."
						% (self.fileName, receivedTransactionId))

					# send CTS (clear to send) message
					payload = {"type": "cts", "id": receivedTransactionId}
					message = {"message": str(message["message"]),
						"payload": payload}
					self.client.send(json.dumps(message))

					# after initiating transaction receive
					# actual command 
					data = self.client.recv(BUFSIZE)
					data = data.strip()


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
						message = {"message": message["message"],
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
			# => trigger alerts
			if (command == "SENSORALERT"):

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
			elif (command == "SENSORALERTSOFF"):

					# handle sensor alerts off message
					if not self._sensorAlertsOffHandler(message):

						logging.error("[%s]: Receiving sensor " % self.fileName
							+ "alerts off failed.")

						# clean up session before exiting
						self._cleanUpSessionForClosing()
						self._releaseLock()	
						return

			# unknown command was received
			# => close connection
			else:
				logging.error("[%s]: Received unknown " % self.fileName
					+ "command. Server sent: '%s'." % data)

				try:
					message = {"message": message["message"],
						"error": "unknown command/message type"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			self.lastRecv = time.time()


	# this function reconnects the client to the server
	def reconnect(self):

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
	def sendKeepalive(self):

		# initiate transaction with server and acquire lock
		if not self._initiateTransaction("ping", acquireLock=True):

			# clean up session before exiting
			self._cleanUpSessionForClosing()

			return False

		# send ping request
		try:
			logging.debug("[%s]: Sending ping message." % self.fileName)

			payload = {"type": "request"}
			message = {"message": "ping", "payload": payload}
			self.client.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending ping to server failed." 
				% self.fileName)			

			# clean up session before exiting
			self._cleanUpSessionForClosing()
			self._releaseLock()
			return False

		# get ping response from server
		try:

			data = self.client.recv(BUFSIZE).strip()
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
					message = {"message": message["message"],
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
					message = {"message": message["message"],
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
		self.lastRecv = time.time()

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

		# check every 5 seconds if the client is still connected
		# and the time of the last received data 
		# from the server lies too far in the past
		while 1:

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
				while 1:

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

						self.connectionRetries = 1
						break
					self.connectionRetries +=1

					logging.error("[%s]: Reconnecting failed. " 
						% self.fileName + "Retrying in 5 seconds.")
					time.sleep(5)

				continue

			# check if the time of the data last received lies too far in the 
			# past => send ping to check connection
			if (time.time() - self.connection.lastRecv) > self.pingInterval:
				logging.debug("[%s]: Ping interval exceeded." 
						% self.fileName)

				# check if PING failed
				if not self.connection.sendKeepalive():
					logging.error("[%s]: Connection to server has died. " 
						% self.fileName)

					# reconnect to the server
					while 1:

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
class Receiver:

	def __init__(self, connection):
		self.connection = connection
		self.fileName = os.path.basename(__file__)

		# set exit flag as false
		self.exitFlag = False


	def run(self):

		while 1:
			if self.exitFlag:
				return			

			# only run the communication handler
			self.connection.handleCommunication()

			time.sleep(1)


	# sets the exit flag to shut down the thread
	def exit(self):
		self.exitFlag = True
		return