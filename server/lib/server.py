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
BUFSIZE = 2048


# this class handles the communication with the incoming client connection
class ClientCommunication:

	def __init__(self, sslSocket, clientAddress, clientPort, globalData):
		self.sslSocket = sslSocket
		self.clientAddress = clientAddress
		self.clientPort = clientPort

		# get global configured data
		self.globalData = globalData
		self.version = self.globalData.version
		self.storage = self.globalData.storage
		self.userBackend = self.globalData.userBackend
		self.sensorAlertExecuter = self.globalData.sensorAlertExecuter
		self.managerUpdateExecuter = self.globalData.managerUpdateExecuter
		self.alertLevels = self.globalData.alertLevels
		self.asyncOptionExecuters = self.globalData.asyncOptionExecuters
		self.asyncOptionExecutersLock \
			= self.globalData.asyncOptionExecutersLock

		# time the last message was received by the server
		self.lastRecv = 0.0

		# username that is used by the client to authorize itself
		self.username = None

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# type of the client (sensor/alert/manager)
		self.nodeType = None

		# hostname of the client
		self.hostname = None

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
	def _initiateTransaction(self, acquireLock=False):

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
			transactionId = os.urandom(12)

			# send RTS (request to send) message
			logging.debug("[%s]: Sending RTS %s message (%s:%d)."
				% (self.fileName, base64.b64encode(transactionId),
				self.clientAddress, self.clientPort))
			try:
				message = "RTS %s\r\n" % base64.b64encode(transactionId)
				self.sslSocket.send(message)
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
				data = self.sslSocket.recv().strip()
				splittedData = data.split()
				receivedTransactionId = base64.b64decode(splittedData[1])
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
			if (splittedData[0] == "CTS"
				and receivedTransactionId == transactionId):

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


	# internal function that authenticates the client
	def _clientAuthentication(self):

		# get username from client
		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving username failed (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))
			return False

		splittedData = data.split()
		if (len(splittedData) != 2 
			or splittedData[0].upper() != "USER"):
			logging.error("[%s]: Authentication failed. " % self.fileName
				+ "Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))

			try:
				self.sslSocket.send("AUTHENTICATION REQUIRED\r\n")
			except Exception as e:
				logging.exception("[%s]: Sending " % self.fileName
					+ "authentication abort failed (%s:%d)." 
					% (self.clientAddress, self.clientPort))

			return False
		self.username = splittedData[1]

		logging.debug("[%s]: Received username: '%s' (%s:%d)." 
				% (self.fileName, self.username, self.clientAddress, 
				self.clientPort))

		try:
			self.sslSocket.send("OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending username " % self.fileName
				+ "acknowledgement failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

		# get password from client
		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving password failed (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))
			return False

		splittedData = data.split()
		if (len(splittedData) != 2 
			or splittedData[0].upper() != "PASS"):
			logging.error("[%s]: Authentication failed. " % self.fileNames
				+ "Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))

			try:
				self.sslSocket.send("AUTHENTICATION REQUIRED\r\n")
			except Exception as e:
				logging.exception("[%s]: Sending " % self.fileName
					+ "authentication abort failed (%s:%d)." 
					% (self.clientAddress, self.clientPort))

			return False
		password = splittedData[1]
		
		logging.debug("[%s]: Received password (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))

		# check if the given user credentials are valid
		if not self.userBackend.areUserCredentialsValid(self.username,
			password):

			try:
				self.sslSocket.send("INCORRECT CREDENTIALS\r\n")
			except Exception as e:
				logging.exception("[%s]: Sending incorrect " % self.fileName
					+ "credentials failed (%s:%d)."
					% (self.clientAddress, self.clientPort))				

			return False

		try:
			self.sslSocket.send("AUTHENTICATED\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending authentication " % self.fileName
				+ "acknowledgement failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		return True


	# internal function to verify the server/client version
	def _verifyVersion(self):

		# sending server version to client
		try:
			logging.debug("[%s]: Sending server version: '%.1f' (%s:%d)." 
				% (self.fileName, self.version, self.clientAddress, 
				self.clientPort))
			self.sslSocket.send("VERSION %.1f\r\n" % self.version)
		except Exception as e:
			logging.exception("[%s]: Sending version failed (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))
			return False

		# receiving version acknowledgement
		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving version " % self.fileName
				+ "acknowledgement failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		if data.upper() != "OK":
			logging.error("[%s]: Expected version acknowledgement. " 
				% self.fileName + "Received: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))
			return False

		# receiving client version and verify it
		try:
			data = self.sslSocket.recv().strip()
			splittedData = data.split()
			version = float(splittedData[1])
		except Exception as e:
			logging.exception("[%s]: Receiving version failed (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))
			return False

		if (len(splittedData) != 2 
			or splittedData[0].upper() != "VERSION"):
			logging.error("[%s]: Receiving VERSION " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))
			
			try:
				self.sslSocket.send("VERSION VERIFICATION REQUIRED\r\n")
			except Exception as e:
				logging.exception("[%s]: Sending version " % self.fileName
					+ "verification abort failed (%s:%d)."
					% (self.clientAddress, self.clientPort))

			return False

		if self.version != version:

			logging.error("[%s]: Version not compatible. " % self.fileName
				+ "Client has version: '%.1f' and server has '%.1f (%s:%d)" 
				% (version, self.version, self.clientAddress, self.clientPort))

			try:
				self.sslSocket.send("VERSION VERIFICATION FAILED\r\n")
			except Exception as e:
				logging.exception("[%s]: Sending version " % self.fileName
					+ "verification abort failed (%s:%d)."
					% (self.clientAddress, self.clientPort))

			return False

		logging.debug("[%s]: Received client version: '%.1f' (%s:%d)." 
				% (self.fileName, version, self.clientAddress, 
				self.clientPort))

		# acknowledge client version
		try:
			self.sslSocket.send("OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending version " % self.fileName
				+ "acknowledgement failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		return True


	# internal function to register the client (add it to the database
	# or check if it is known)
	def _registerClient(self):

		# get registration start message from client
		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving REGISTER " % self.fileName
				+ " START failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		if data != "REGISTER START":
			logging.error("[%s]: Receiving REGISTER START " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))
			return False

		logging.debug("[%s]: Received register start message (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))

		# receiving client configuration new/old message
		try:
			data = self.sslSocket.recv().strip()
			splittedData = data.split()
			configuration = splittedData[1]
		except Exception as e:
			logging.exception("[%s]: Receiving CONFIGURATION failed (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))
			return False

		if (len(splittedData) != 2
			or splittedData[0].upper() != "CONFIGURATION"):
			logging.error("[%s]: Receiving CONFIGURATION " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))
			return False

		# check if the received parameter was "new" or "old"
		if not (configuration == "new"
			or configuration == "old"):
			logging.error("[%s]: Receiving CONFIGURATION " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))			
			return False

		# receiving node registration
		try:
			data = self.sslSocket.recv().strip()
			splittedData = data.split()
			self.hostname = base64.b64decode(splittedData[1])
			self.nodeType = splittedData[2]
		except Exception as e:
			logging.exception("[%s]: Receiving NODE failed (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))
			return False

		if (len(splittedData) != 3
			or splittedData[0].upper() != "NODE"):
			logging.error("[%s]: Receiving NODE " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))
			return False

		logging.debug("[%s]: Received node registration '%s': %s:%s (%s:%d)." 
				% (self.fileName, configuration, self.hostname, self.nodeType,
					self.clientAddress, self.clientPort))

		# check if the client configuration is new and has to be changed
		# in the database
		if configuration == "new":
			# add node to database
			if not self.storage.addNode(self.username, self.hostname,
				self.nodeType):
				logging.error("[%s]: Unable to add node to database." 
					% self.fileName)
				return False

		# check if the client configuration is old and is the same as
		# in the database
		elif configuration == "old":
			# check received node configuration with database
			if not self.storage.checkNode(self.username, self.hostname,
				self.nodeType):
				logging.error("[%s]: Node check in database failed." 
					% self.fileName)
				return False

		# only new/old are allowed => abort if other value
		else:
			return False

		# check if the type of the node got sensors
		# => await sensor registration message
		if self.nodeType == "sensor":

			# receiving sensor count message
			try:
				data = self.sslSocket.recv().strip()
				splittedData = data.split()
				sensorCount = int(splittedData[1])
			except Exception as e:
				logging.exception("[%s]: Receiving " % self.fileName
					+ "SENSORCOUNT failed (%s:%d)."
					% (self.clientAddress, self.clientPort))
				return False

			if (len(splittedData) != 2
				or splittedData[0].upper() != "SENSORCOUNT"):
				logging.error("[%s]: Receiving " % self.fileName
					+ "SENSORCOUNT failed. Client sent: '%s' (%s:%d)." 
					% (data, self.clientAddress, self.clientPort))
				return False

			logging.debug("[%s]: Received sensor count: %d (%s:%d)." 
					% (self.fileName, sensorCount, self.clientAddress,
					self.clientPort))

			# check if the client configuration is old and is the same as
			# in the database
			if configuration == "old":
				# check received sensor count matches with the database
				if not self.storage.checkSensorCount(self.username,
					sensorCount):
					logging.error("[%s]: Sensor count check " % self.fileName
						+ "in database failed.")
					return False			

			for i in range(sensorCount):

				# receiving sensor registration message
				try:
					data = self.sslSocket.recv().strip()
					splittedData = data.split()
					sensorId = int(splittedData[1])
					alertDelay = int(splittedData[2])
					alertLevel = int(splittedData[3])
					description = base64.b64decode(splittedData[4])
					triggerAlways = int(splittedData[5])
				except Exception as e:
					logging.exception("[%s]: Receiving " % self.fileName
						+ "SENSOR failed (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False

				if (len(splittedData) != 6
					or splittedData[0].upper() != "SENSOR"):
					logging.error("[%s]: Receiving SENSOR " % self.fileName
						+ "failed. Client sent: '%s' (%s:%d)." 
						% (data, self.clientAddress, self.clientPort))
					return False

				logging.debug("[%s]: Received sensor " % self.fileName
					+ "registration: %d:%d:%d:'%s':%d (%s:%d)." 
					% (sensorId, alertDelay, alertLevel, description,
					triggerAlways, self.clientAddress, self.clientPort))

				found = False
				for tempAlertLevel in self.alertLevels:
					if tempAlertLevel.level == alertLevel:
						found = True
						break
				if not found:
					logging.error("[%s]: Alert level does " % self.fileName
						+ "not exist in configuration (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False					

				# check if the client configuration is new and has to 
				# be changed in the data59base
				if configuration == "new":
					# add sensor to database
					if not self.storage.addSensor(self.username, sensorId,
						alertDelay, alertLevel, description, triggerAlways):
						logging.error("[%s]: Unable to add " % self.fileName
							+ "sensor to database (%s:%d)."
							% (self.clientAddress, self.clientPort))
						return False

				# check if the client configuration is old and is the same as
				# in the database
				elif configuration == "old":
					# check received sensor configuration with database
					if not self.storage.checkSensor(self.username, sensorId,
						alertDelay, alertLevel, description, triggerAlways):
						logging.error("[%s]: Sensor check in " % self.fileName
							+ "database failed (%s:%d)."
							% (self.clientAddress, self.clientPort))
						return False

				# only new/old are allowed => abort if other value
				else:
					return False

		# check if the type of the node is alert
		# => register alerts
		elif self.nodeType == "alert":

			# receiving alert count message
			try:
				data = self.sslSocket.recv().strip()
				splittedData = data.split()
				alertCount = int(splittedData[1])
			except Exception as e:
				logging.exception("[%s]: Receiving " % self.fileName
					+ "ALERTCOUNT failed (%s:%d)."
					% (self.clientAddress, self.clientPort))
				return False

			if (len(splittedData) != 2
				or splittedData[0].upper() != "ALERTCOUNT"):
				logging.error("[%s]: Receiving " % self.fileName
					+ "ALERTCOUNT failed. Client sent: '%s' (%s:%d)." 
					% (data, self.clientAddress, self.clientPort))
				return False

			logging.debug("[%s]: Received alert count: %d (%s:%d)." 
					% (self.fileName, alertCount, self.clientAddress,
					self.clientPort))

			# check if the client configuration is old and is the same as
			# in the database
			if configuration == "old":
				# check received alert count matches with the database
				if not self.storage.checkAlertCount(self.username,
					alertCount):
					logging.error("[%s]: Alert count check " % self.fileName
						+ "in database failed.")
					return False			

			for i in range(alertCount):

				# receiving alert registration message
				try:
					data = self.sslSocket.recv().strip()
					splittedData = data.split()
					alertId = int(splittedData[1])
					description = base64.b64decode(splittedData[2])

				except Exception as e:
					logging.exception("[%s]: Receiving " % self.fileName
						+ "ALERT failed (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False

				if (len(splittedData) != 3
					or splittedData[0].upper() != "ALERT"):
					logging.error("[%s]: Receiving ALERT " % self.fileName
						+ "failed. Client sent: '%s' (%s:%d)." 
						% (data, self.clientAddress, self.clientPort))
					return False

				logging.debug("[%s]: Received alert " % self.fileName
					+ "registration: %d:'%s' (%s:%d)." 
					% (alertId, description,
					self.clientAddress, self.clientPort))

				# check if the client configuration is new and has to 
				# be changed in the database
				if configuration == "new":
					# add alert to database
					if not self.storage.addAlert(self.username, alertId,
						description):
						logging.error("[%s]: Unable to add " % self.fileName
							+ "alert to database (%s:%d)."
							% (self.clientAddress, self.clientPort))
						return False

				# check if the client configuration is old and is the same as
				# in the database
				elif configuration == "old":
					# check received alert configuration with database
					if not self.storage.checkAlert(self.username, alertId,
						description):
						logging.error("[%s]: Alert check in " % self.fileName
							+ "database failed (%s:%d)."
							% (self.clientAddress, self.clientPort))
						return False

			# receiving alert level count message
			try:
				data = self.sslSocket.recv().strip()
				splittedData = data.split()
				alertLevelCount = int(splittedData[1])
			except Exception as e:
				logging.exception("[%s]: Receiving " % self.fileName
					+ "ALERTLEVELCOUNT failed (%s:%d)."
					% (self.clientAddress, self.clientPort))
				return False

			if (len(splittedData) != 2
				or splittedData[0].upper() != "ALERTLEVELCOUNT"):
				logging.error("[%s]: Receiving " % self.fileName
					+ "ALERTLEVELCOUNT failed. Client sent: '%s' (%s:%d)." 
					% (data, self.clientAddress, self.clientPort))
				return False

			logging.debug("[%s]: Received alert level count: %d (%s:%d)." 
					% (self.fileName, alertLevelCount, self.clientAddress,
					self.clientPort))

			# check if the client configuration is old and is the same as
			# in the database
			if configuration == "old":
				# check received alert level count matches with the database
				if not self.storage.checkAlertLevelCount(self.username,
					alertLevelCount):
					logging.error("[%s]: Alert level count " % self.fileName
						+ "check in database failed.")
					return False

			receivedAlertLevels = list()

			for i in range(alertLevelCount):

				# receiving alert level registration message
				try:
					data = self.sslSocket.recv().strip()
					splittedData = data.split()
					alertLevel = int(splittedData[1])

				except Exception as e:
					logging.exception("[%s]: Receiving " % self.fileName
						+ "ALERTLEVEL failed (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False

				if (len(splittedData) != 2
					or splittedData[0].upper() != "ALERTLEVEL"):
					logging.error("[%s]: Receiving ALERTLEVEL " % self.fileName
						+ "failed. Client sent: '%s' (%s:%d)." 
						% (data, self.clientAddress, self.clientPort))
					return False

				# check if alert level is configured on server
				found = False
				for tempAlertLevel in self.alertLevels:
					if tempAlertLevel.level == alertLevel:
						found = True
						break
				if not found:
					logging.error("[%s]: Alert level does " % self.fileName
						+ "not exist in configuration (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False

				# check if alert level is unique on this client
				if not alertLevel in receivedAlertLevels:
					logging.debug("[%s]: Received alert level" % self.fileName
						+ "registration: %d (%s:%d)." 
						% (alertLevel, self.clientAddress, self.clientPort))
					receivedAlertLevels.append(alertLevel)
				else:
					logging.error("[%s]: Received duplicated " % self.fileName
						+ "alert level: %d (%s:%d)." 
						% (alertLevel, self.clientAddress, self.clientPort))
					return False

			# check if the client configuration is new and has to 
			# be changed in the database
			if configuration == "new":
				# add alert levels to database
				if not self.storage.addAlertLevels(self.username,
					receivedAlertLevels):
					logging.error("[%s]: Unable to add " % self.fileName
						+ "alert levels to database (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False

			# check if the client configuration is old and is the same as
			# in the database
			elif configuration == "old":
				# check received alert configuration with database
				if not self.storage.checkAlertLevels(self.username,
					receivedAlertLevels):
					logging.error("[%s]: Alert levels check " % self.fileName
						+ "in database failed (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False

			# only new/old are allowed => abort if other value
			else:
				return False

		# check if the type of the node is manager
		elif self.nodeType == "manager":
			
			# receiving manager information message
			try:
				data = self.sslSocket.recv().strip()
				splittedData = data.split()
				description = base64.b64decode(splittedData[1])
			except Exception as e:
				logging.exception("[%s]: Receiving " % self.fileName
					+ "MANAGER failed (%s:%d)."
					% (self.clientAddress, self.clientPort))
				return False

			if (len(splittedData) != 2
				or splittedData[0].upper() != "MANAGER"):
				logging.error("[%s]: Receiving " % self.fileName
					+ "MANAGER failed. Client sent: '%s' (%s:%d)." 
					% (data, self.clientAddress, self.clientPort))
				return False

			logging.debug("[%s]: Received manager information (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

			# check if the client configuration is new and has to 
			# be changed in the database
			if configuration == "new":
				# add manager to database
				if not self.storage.addManager(self.username, description):
					logging.error("[%s]: Unable to add " % self.fileName
						+ "manager to database (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False

			# check if the client configuration is old and is the same as
			# in the database
			elif configuration == "old":
				# check received manager configuration with database
				if not self.storage.checkManager(self.username, description):
					logging.error("[%s]: Manager check " % self.fileName
						+ "in database failed (%s:%d)."
						% (self.clientAddress, self.clientPort))
					return False

			# only new/old are allowed => abort if other value
			else:
				return False

		# if nodetype is not sensor, alert or manager => not known
		else:
			logging.error("[%s]: Node type not known '%s'."
				% (self.fileName, self.nodeType))		
			return False

		# get registration end message from client
		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving REGISTER " % self.fileName
				+ " END failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		if data != "REGISTER END":
			logging.error("[%s]: Receiving REGISTER END " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))
			return False

		logging.debug("[%s]: Received register end message (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))

		# acknowledge registration
		try:
			self.sslSocket.send("REGISTERED\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending REGISTERED " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		return True


	# this internal function handles the sent option change from a manager
	# and updates it in the database
	def _optionHandler(self, data):
		# extract option type and value from received data
		try:
			splittedData = data.split()
			optionType = base64.b64decode(splittedData[1])
			optionValue = int(splittedData[2])
			optionDelay = int(splittedData[3])
		except Exception as e:
			logging.exception("[%s]: Receiving option " % self.fileName
				+ "failed. Received: '%s' (%s:%d)."
				% (data, self.clientAddress, self.clientPort))
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

		# acknowledge option
		try:
			self.sslSocket.send("OPTION OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending option " % self.fileName
				+ "acknowledgement failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))
			return False

		return True


	# this internal function handles the sent state of the sensors 
	# from a node and updates it in the database
	def _statusHandler(self):

		# get all sensor states from the client and
		# generate a list of tuples with (remoteSensorId, state)
		stateList = list()
		for i in range(self.sensorCount):

			# get sensor message from client
			try:
				data = self.sslSocket.recv().strip()
				splittedData = data.split()
				command = splittedData[0].upper()
				remoteSensorId = int(splittedData[1])
				state = int(splittedData[2])
			except Exception as e:
				logging.exception("[%s]: Receiving sensor " % self.fileName
					+ "state failed. Received: '%s' (%s:%d)."
					% (data, self.clientAddress, self.clientPort))
				return False

			logging.debug("[%s]: Received new sensor state %d:%d (%s:%d)." 
				% (self.fileName, remoteSensorId, state,
				self.clientAddress, self.clientPort))

			stateList.append((remoteSensorId, state))

		# update the sensor state in the database
		if not self.storage.updateSensorState(self.nodeId, stateList):
			logging.error("[%s]: Not able to update sensor state (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			return False			

		# get status end message from client
		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving STATUS " % self.fileName
				+ " END failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		if data != "STATUS END":
			logging.error("[%s]: Receiving STATUS END " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))
			return False

		logging.debug("[%s]: Received status end message (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))

		# acknowledge status
		try:
			self.sslSocket.send("OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending status " % self.fileName
				+ "acknowledgement failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		return True


	# this internal function handles received sensor alerts
	# (adds them to the database and wakes up the sensor alert executer)
	def _sensorAlertHandler(self, data):

		# extract remoteSensorId and state from received message
		try:
			splittedData = data.split()
			remoteSensorId = int(splittedData[1])
			state = int(splittedData[2])
		except Exception as e:
			logging.exception("[%s]: Receiving sensor alert " % self.fileName
				+ "failed. Received: '%s' (%s:%d)."
				% (data, self.clientAddress, self.clientPort))
			return False

		# add sensor alert to database
		if not self.storage.addSensorAlert(self.nodeId, remoteSensorId, state):
			logging.error("[%s]: Not able to add sensor alert (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			return False

		# wake up sensor alert executer
		self.sensorAlertExecuter.sensorAlertEvent.set()

		# acknowledge sensor alert
		try:
			self.sslSocket.send("OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending sensor alert " % self.fileName
				+ "acknowledgement failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		return True


	# this internal function handles received state changes
	# (updates them in the database and wakes up the manager update executer)
	def _stateChangeHandler(self, data):

		# extract remoteSensorId and state from received message
		try:
			splittedData = data.split()
			remoteSensorId = int(splittedData[1])
			state = int(splittedData[2])
		except Exception as e:
			logging.exception("[%s]: Receiving sensor state " % self.fileName
				+ "change failed. Received: '%s' (%s:%d)."
				% (data, self.clientAddress, self.clientPort))
			return False

		# update sensor state
		stateTuple = (remoteSensorId, state)
		stateList = list()
		stateList.append(stateTuple)
		if not self.storage.updateSensorState(self.nodeId, stateList):
			logging.error("[%s]: Not able to change sensor state (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			return False

		# acknowledge sensor state change
		try:
			self.sslSocket.send("OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending sensor state " % self.fileName
				+ "change acknowledgement failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# get sensorId from database => append to state change queue
		# => wake up manager update executer
		sensorId = self.storage.getSensorId(self.nodeId, remoteSensorId)
		if sensorId is None:
			logging.error("[%s]: Not able to get sensorId (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))

			return False

		# add state change to queue and wake up manager update executer
		self.managerUpdateExecuter.queueStateChange.append(sensorId)
		self.managerUpdateExecuter.managerUpdateEvent.set()

		return True


	# internal function to send the current state of the alert system
	# to a manager
	def _sendManagerAllInformation(self):

		# send status start message
		logging.debug("[%s]: Sending STATUS START message (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("STATUS START\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending STATUS START " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# get a list from database of 
		# list[0] = optionCount
		# list[1] = list(tuples of (type, value))
		# list[2] = nodeCount
		# list[3] = list(tuples of (nodeId, hostname, nodeType, connected))
		# list[4] = sensorCount
		# list[5] = list(tuples of (nodeId, sensorId, alertDelay,
		# alertLevel, description, lastStateUpdated, state))
		# list[6] = managerCount
		# list[7] = list(tuples of (nodeId, managerId, description))
		# list[8] = alertCount
		# list[9] = list(tuples of (nodeId, alertId, description))	
		alertSystemInformation = self.storage.getAlertSystemInformation()
		if alertSystemInformation == None:
			logging.error("[%s]: Getting alert system " % self.fileName
				+ "information from database failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

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

		# send option start message
		logging.debug("[%s]: Sending OPTION START message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("OPTION START\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending OPTION START " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send option count message
		logging.debug("[%s]: Sending OPTIONCOUNT message (%s:%d)." 
			% (self.fileName, self.clientAddress, self.clientPort))	
		message = "OPTIONCOUNT %d\r\n" % optionCount
		try:
			self.sslSocket.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending OPTIONCOUNT " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# sending all options information
		for i in range(optionCount):

			# send option message
			logging.debug("[%s]: Sending OPTION message (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			message = "OPTION %s %d\r\n" \
				% (base64.b64encode(optionsInformation[i][0]),
				optionsInformation[i][1])
			try:
				self.sslSocket.send(message)
			except Exception as e:
				logging.exception("[%s]: Sending OPTION " % self.fileName
					+ "failed (%s:%d)." 
					% (self.clientAddress, self.clientPort))

				return False

		# send option end message
		logging.debug("[%s]: Sending OPTION END message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("OPTION END\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending OPTION END " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send node start message
		logging.debug("[%s]: Sending NODE START message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("NODE START\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending NODE START " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send node count message
		logging.debug("[%s]: Sending NODECOUNT message (%s:%d)." 
			% (self.fileName, self.clientAddress, self.clientPort))	
		message = "NODECOUNT %d\r\n" % nodeCount
		try:
			self.sslSocket.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending NODECOUNT " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# sending all nodes information
		for i in range(nodeCount):

			# send node message
			logging.debug("[%s]: Sending NODE message (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			message = "NODE %d %s %s %d\r\n" % (nodesInformation[i][0],
				base64.b64encode(nodesInformation[i][1]),
				nodesInformation[i][2], nodesInformation[i][3])
			try:
				self.sslSocket.send(message)
			except Exception as e:
				logging.exception("[%s]: Sending NODE " % self.fileName
					+ "failed (%s:%d)." 
					% (self.clientAddress, self.clientPort))

				return False

		# send node end message
		logging.debug("[%s]: Sending NODE END message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("NODE END\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending NODE END " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send sensor start message
		logging.debug("[%s]: Sending SENSOR START message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("SENSOR START\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending SENSOR START " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send sensor count message
		logging.debug("[%s]: Sending SENSORCOUNT message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		message = "SENSORCOUNT %d\r\n" % sensorCount
		try:
			self.sslSocket.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending SENSORCOUNT " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# sending all sensors information
		for i in range(sensorCount):

			# send sensor message
			logging.debug("[%s]: Sending SENSOR message (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			message = "SENSOR %d %d %d %d %s %d %d\r\n" \
				% (sensorsInformation[i][0], sensorsInformation[i][1],
				sensorsInformation[i][2], sensorsInformation[i][3],
				base64.b64encode(sensorsInformation[i][4]),
				sensorsInformation[i][5], sensorsInformation[i][6])
			try:
				self.sslSocket.send(message)
			except Exception as e:
				logging.exception("[%s]: Sending SENSOR " % self.fileName
					+ "failed (%s:%d)." 
					% (self.clientAddress, self.clientPort))

				return False

		# send sensor end message
		logging.debug("[%s]: Sending SENSOR END message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("SENSOR END\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending SENSOR END " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send manager start message
		logging.debug("[%s]: Sending MANAGER START message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("MANAGER START\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending MANAGER START " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send manager count message
		logging.debug("[%s]: Sending MANAGERCOUNT message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		message = "MANAGERCOUNT %d\r\n" % managerCount
		try:
			self.sslSocket.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending MANAGERCOUNT " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# sending all managers information
		for i in range(managerCount):

			# send manager message
			logging.debug("[%s]: Sending MANAGER message (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			message = "MANAGER %d %d %s\r\n" % (managersInformation[i][0],
				managersInformation[i][1],
				base64.b64encode(managersInformation[i][2]))
			try:
				self.sslSocket.send(message)
			except Exception as e:
				logging.exception("[%s]: Sending MANAGER " % self.fileName
					+ "failed (%s:%d)." 
					% (self.clientAddress, self.clientPort))

				return False

		# send manager end message
		logging.debug("[%s]: Sending MANAGER END message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("MANAGER END\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending MANAGER END " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send alert start message
		logging.debug("[%s]: Sending ALERT START message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("ALERT START\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending ALERT START " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send alert count message
		logging.debug("[%s]: Sending ALERTCOUNT message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		message = "ALERTCOUNT %d\r\n" % alertCount
		try:
			self.sslSocket.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending ALERTCOUNT " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# sending all alerts information
		for i in range(alertCount):

			# send alert message
			logging.debug("[%s]: Sending ALERT message (%s:%d)."
				% (self.fileName, self.clientAddress, self.clientPort))
			message = "ALERT %d %d %s\r\n" % (alertsInformation[i][0],
				alertsInformation[i][1],
				base64.b64encode(alertsInformation[i][2]))
			try:
				self.sslSocket.send(message)
			except Exception as e:
				logging.exception("[%s]: Sending ALERT " % self.fileName
					+ "failed (%s:%d)." 
					% (self.clientAddress, self.clientPort))

				return False

		# send alert end message
		logging.debug("[%s]: Sending ALERT END message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			self.sslSocket.send("ALERT END\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending ALERT END " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send status end message
		logging.debug("[%s]: Sending STATUS END message (%s:%d)." 
				% (self.fileName, self.clientAddress, self.clientPort))		
		try:
			self.sslSocket.send("STATUS END\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending STATUS END " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# get status acknowledgement
		logging.debug("[%s]: Receiving STATUS acknowledgement (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving STATUS " % self.fileName
				+ "OK failed (%s:%d)."
				% (self.clientAddress, self.clientPort))
			return False

		if data != "STATUS OK":
			logging.error("[%s]: Receiving STATUS OK " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))
			return False

		self.lastRecv = time.time()

		return True


	# internal function to send a state change to a manager
	def _sendManagerStateChange(self, sensorId):

		state = self.storage.getSensorState(sensorId)
		if state is None:
			logging.error("[%s]: Getting sensor state " % self.fileName
				+ "from database failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# send state change message
		logging.debug("[%s]: Sending STATECHANGE message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		message = "STATECHANGE %d %d\r\n" % (sensorId, state)
		try:
			self.sslSocket.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending OPTION " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# get state change acknowledgement
		logging.debug("[%s]: Receiving STATECHANGE acknowledgement (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))

		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving STATECHANGE " % self.fileName
				+ "OK failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		if data != "STATECHANGE OK":
			logging.error("[%s]: Receiving STATECHANGE OK " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))

			return False

		self.lastRecv = time.time()

		return True


	# internal function to send a sensor alert off to a alert client
	def _sendAlertSensorAlertsOff(self):

		# send sensor alert off message
		logging.debug("[%s]: Sending SENSORALERTSOFF message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		message = "SENSORALERTSOFF\r\n"
		try:
			self.sslSocket.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending SENSORALERTSOFF " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			return False

		# get sensor alert off acknowledgement
		logging.debug("[%s]: Receiving SENSORALERTSOFF " % self.fileName
			+ "acknowledgement (%s:%d)."
			% (self.clientAddress, self.clientPort))

		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving " % self.fileName
				+ "SENSORALERTSOFF OK failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			return False

		if data != "SENSORALERTSOFF OK":
			logging.error("[%s]: Receiving SENSORALERTSOFF OK " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))

			return False

		self.lastRecv = time.time()

		return True


	# function that sends a state change to a manager client
	def sendManagerStateChange(self, sensorId):

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction(acquireLock=True):
			return False

		returnValue = self._sendManagerStateChange(sensorId)

		self._releaseLock()
		return returnValue


	# function that sends a sensor alert of to a alert client
	def sendAlertSensorAlertsOff(self):

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction(acquireLock=True):
			return False

		returnValue = self._sendAlertSensorAlertsOff()

		self._releaseLock()
		return returnValue


	# function that sends a full information update to a manager client
	def sendManagerUpdate(self):

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction(acquireLock=True):
			return False

		returnValue = self._sendManagerAllInformation()

		self._releaseLock()
		return returnValue


	# function that sends a sensor alert to an alert/manager client
	def sendSensorAlert(self, sensorId, state, alertLevel):

		# initiate transaction with client and acquire lock
		if not self._initiateTransaction(acquireLock=True):
			return False

		# send sensor alert message
		logging.debug("[%s]: Sending SENSORALERT message (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))
		try:
			message = "SENSORALERT %d %d %d\r\n" \
				% (sensorId, state, alertLevel)
			self.sslSocket.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending SENSORALERT " % self.fileName
				+ "failed (%s:%d)." 
				% (self.clientAddress, self.clientPort))

			self._releaseLock()
			return False

		# get sensor alert acknowledgement
		logging.debug("[%s]: Receiving SENSORALERT acknowledgement (%s:%d)."
			% (self.fileName, self.clientAddress, self.clientPort))

		try:
			data = self.sslSocket.recv().strip()
		except Exception as e:
			logging.exception("[%s]: Receiving SENSORALERT " % self.fileName
				+ "OK failed (%s:%d)."
				% (self.clientAddress, self.clientPort))

			self._releaseLock()
			return False

		if data != "SENSORALERT OK":

			logging.error("[%s]: Receiving SENSORALERT OK " % self.fileName
				+ "failed. Client sent: '%s' (%s:%d)." 
				% (data, self.clientAddress, self.clientPort))

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
		if not self._verifyVersion():
			logging.error("[%s]: Version verification failed (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

			self._releaseLock()
			return

		# second authenticate client
		if not self._clientAuthentication():
			logging.error("[%s]: Authentication failed (%s:%d)."
					% (self.fileName, self.clientAddress, self.clientPort))

			self._releaseLock()
			return

		# third register client
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

			if (not self._initiateTransaction(acquireLock=False)
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

				data = self.sslSocket.recv()
				if not data:

					# clean up session before exiting
					self._cleanUpSessionForClosing()

					self._releaseLock()
					return
				data = data.strip()

				# change timeout of the socket back to configured seconds
				self.sslSocket.settimeout(self.serverReceiveTimeout)

				# check if RTS was received
				# => acknowledge it
				splittedData = data.split()
				receivedTransactionId = splittedData[1]
				if splittedData[0] == "RTS":

					# received RTS (request to send) message
					logging.debug("[%s]: Received RTS %s message (%s:%d)."
						% (self.fileName, receivedTransactionId,
						self.clientAddress, self.clientPort))

					# send CTS (clear to send) message
					logging.debug("[%s]: Sending CTS %s message (%s:%d)."
						% (self.fileName, receivedTransactionId,
						self.clientAddress, self.clientPort))

					message = "CTS %s\r\n" % receivedTransactionId
					self.sslSocket.send(message)

					# after initiating transaction receive
					# actual command 
					data = self.sslSocket.recv()
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

			splittedData = data.split()
			if len(splittedData) < 1:
				continue

			# extract command
			command = splittedData[0].upper()

			# check if PING was received => send PONG back
			if command == "PING":

				logging.debug("[%s]: Received PING (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))
				logging.debug("[%s]: Sending PONG (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

				try:
					self.sslSocket.send("PONG\r\n")
				except Exception as e:
					logging.exception("[%s]: Sending PONG " % self.fileName
						+ "to client failed (%s:%d)." 
						% (self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()

					self._releaseLock()
					return

			# check if SENSORALERT was received
			# => add to database and wake up alertExecuter
			elif (command == "SENSORALERT"
				and self.nodeType == "sensor"):

				logging.debug("[%s]: Received SENSORALERT (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

				if not self._sensorAlertHandler(data):

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

				logging.debug("[%s]: Received STATECHANGE (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

				if not self._stateChangeHandler(data):

					logging.error("[%s]: Handling sensor " % self.fileName
						+ "state change failed (%s:%d)."
						% (self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()

					self._releaseLock()
					return

			# check if STATUS START was received
			# => add new state to the database
			elif (command == "STATUS"
				and splittedData[1].upper() == "START"
				and self.nodeType == "sensor"):

				logging.debug("[%s]: Received status start message (%s:%d)." 
					% (self.fileName, self.clientAddress, self.clientPort))

				if not self._statusHandler():

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

				if not self._optionHandler(data):

					logging.error("[%s]: Handling option failed (%s:%d)." 
						% (self.fileName, self.clientAddress, self.clientPort))

					# clean up session before exiting
					self._cleanUpSessionForClosing()

					self._releaseLock()
					return

				# wake up manager update executer
				self.managerUpdateExecuter.forceStatusUpdate = True
				self.managerUpdateExecuter.managerUpdateEvent.set()

			# command is unknown => close connection
			else:
				logging.error("[%s]: Received unknown " % self.fileName
					+ "command. Client sent: '%s' (%s:%d)."
					% (data, self.clientAddress, self.clientPort))

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

		# add own server session to the global list of server sessions
		self.globalData.serverSessions.append(self)

		SocketServer.BaseRequestHandler.__init__(self, request, 
			clientAddress, server)
		

	def handle(self):

		logging.info("[%s]: Client connected (%s:%d)." 
			% (self.fileName, self.clientAddress, self.clientPort))

		# try to initiate ssl with client
		try:
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
			self.sslSocket.close()
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
					# lastStateUpdated, alertDelay,
					# alertLevel, triggerAlways)
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
		self.sensorAlertSensorId = None
		self.sensorAlertState = None
		self.sensorAlertAlertLevel = None

		# this options are used when the thread should
		# send a state change to a manager client
		self.sendManagerStateChange = False
		self.sendManagerStateChangeSensorId = None

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
				self.sensorAlertState, self.sensorAlertAlertLevel):
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
				self.sendManagerStateChangeSensorId):
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