#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

from serverObjects import Option, Node, Sensor, Manager, Alert, SensorAlert, \
	AlertLevel
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
BUFSIZE = 16384


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
				ca_certs=self.serverCAFile, cert_reqs=ssl.CERT_REQUIRED, 
				ssl_version=ssl.PROTOCOL_TLSv1)
		else:
			self.sslSocket = ssl.wrap_socket(self.socket, 
				ca_certs=self.serverCAFile, cert_reqs=ssl.CERT_REQUIRED, 
				ssl_version=ssl.PROTOCOL_TLSv1,
				certfile=self.clientCertFile, keyfile=self.clientKeyFile)

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
		self.nodeType = self.globalData.nodeType
		self.registeredFile = self.globalData.registeredFile
		self.registered = self.globalData.registered
		self.description = self.globalData.description
		self.screenUpdater = self.globalData.screenUpdater
		# list of alert system information
		self.options = self.globalData.options
		self.nodes = self.globalData.nodes
		self.sensors = self.globalData.sensors
		self.managers = self.globalData.managers
		self.alerts = self.globalData.alerts		
		self.sensorAlerts = self.globalData.sensorAlerts
		self.alertLevels = self.globalData.alertLevels		
		
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


	# this internal function cleans up the session before releasing the
	# lock and exiting/closing the session
	def _cleanUpSessionForClosing(self):
		# set client as disconnected
		self.isConnected = False

		# wake up the screen updater
		self.screenUpdater.screenUpdaterEvent.set()	

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
				message = {"clientTime": int(time.time()),
					"message": messageType, "payload": payload}
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
			message = {"clientTime": int(time.time()),
				"message": "authentication", "payload": payload}
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
					message = {"clientTime": int(time.time()),
						"message": message["message"],
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
					message = {"clientTime": int(time.time()),
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

			logging.debug("[%s]: Received server version: '%.3f'." 
				% (self.fileName, version))

			if self.version != version:

				logging.error("[%s]: Version not compatible. " % self.fileName
					+ "Client has version: '%.3f' " % self.version
					+ "and server has '%.3f" % version)

				# send error message back
				try:
					message = {"clientTime": int(time.time()),
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
				message = {"clientTime": int(time.time()),
					"message": message["message"],
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

		# build manager dict for the message
		manager = dict()
		manager["description"] = self.description

		# send registration message
		try:

			payload = {"type": "request",
				"configuration": configuration,
				"hostname": socket.gethostname(),
				"nodeType": self.nodeType,
				"manager": manager}
			message = {"clientTime": int(time.time()),
				"message": "registration", "payload": payload}
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
					message = {"clientTime": int(time.time()),
						"message": message["message"],
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
					message = {"clientTime": int(time.time()),
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

		# check if client was registered before
		# if not => create registered config file
		if self.registered is False:

			# create config from the values that were transmitted to server
			registeredConfig = ConfigParser.RawConfigParser()
			registeredConfig.add_section('general')
			registeredConfig.set('general', 'hostname', socket.gethostname())
			registeredConfig.set('general', 'description',
				self.description)

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


	# internal function that marks all nodes as not checked
	def _markAlertSystemObjectsAsNotChecked(self):
		for option in self.options:
			option.checked = False

		for node in self.nodes:
			node.checked = False

		for sensor in self.sensors:
			sensor.checked = False		

		for manager in self.managers:
			manager.checked = False

		for alert in self.alerts:
			alert.checked = False

		for alertLevel in self.alertLevels:
			alertLevel.checked = False


	# internal function that checks if all options are checked
	def _checkAllOptionsAreChecked(self):
		for option in self.options:
			if option.checked is False:
				return False
		return True


	# internal function that removes all nodes that are not checked
	def _removeNotCheckedNodes(self):
		for node in self.nodes:
			if node.checked is False:

				# check if node object has a link to the sensor urwid object
				if not node.sensorUrwid is None:
					# check if sensor urwid object is linked to node object
					if not node.sensorUrwid.node is None:
						# used for urwid only:
						# remove reference from urwid object to node object
						# (the objects are double linked)
						node.sensorUrwid.node = None

				# check if node object has a link to the alert urwid object
				elif not node.alertUrwid is None:
					# check if sensor urwid object is linked to node object
					if not node.alertUrwid.node is None:
						# used for urwid only:
						# remove reference from urwid object to node object
						# (the objects are double linked)
						node.alertUrwid.node = None

				# remove sensor from list of sensors
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.nodes.remove(node)

		for sensor in self.sensors:
			if sensor.checked is False:

				# check if sensor object has a link to the sensor urwid object
				if not sensor.sensorUrwid is None:
					# check if sensor urwid object is linked to sensor object
					if not sensor.sensorUrwid.sensor is None:
						# used for urwid only:
						# remove reference from urwid object to sensor object
						# (the objects are double linked)
						sensor.sensorUrwid.sensor = None

				# remove sensor from list of sensors
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.sensors.remove(sensor)

		for manager in self.managers:
			if manager.checked is False:

				# check if manager object has a link to the 
				# manager urwid object
				if not manager.managerUrwid is None:
					# check if manager urwid object is linked to manager object
					if not manager.managerUrwid.manager is None:
						# used for urwid only:
						# remove reference from urwid object to manager object
						# (the objects are double linked)
						manager.managerUrwid.manager = None

				# remove manager from list of managers
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.managers.remove(manager)

		for alert in self.alerts:
			if alert.checked is False:

				# check if alert object has a link to the alert urwid object
				if not alert.alertUrwid is None:
					# check if alert urwid object is linked to alert object
					if not alert.alertUrwid.alert is None:
						# used for urwid only:
						# remove reference from urwid object to alert object
						# (the objects are double linked)
						alert.alertUrwid.alert = None

				# remove alert from list of alerts
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.alerts.remove(alert)

		for alertLevel in self.alertLevels:
			if alertLevel.checked is False:

				# check if alert level object has a link to 
				# the alert level urwid object
				if not alertLevel.alertLevelUrwid is None:
					# check if alert level urwid object is 
					# linked to alert level object
					if not alertLevel.alertLevelUrwid.alertLevel is None:
						# used for urwid only:
						# remove reference from urwid object to 
						# alert level object
						# (the objects are double linked)
						alertLevel.alertLevelUrwid.alertLevel = None

				# remove alert level from list of alert levels
				# to delete all references to object
				# => object will be deleted by garbage collector
				self.alertLevels.remove(alertLevel)


	# internal function that handles received status updates
	def _statusUpdateHandler(self, incomingMessage):

		# first mark all nodes as not checked
		self._markAlertSystemObjectsAsNotChecked()

		# extract status values
		try:

			serverTime = int(incomingMessage["serverTime"])

			options = incomingMessage["payload"]["options"]
			# check if options is of type list
			if not isinstance(options, list):
				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "options not of type list"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			nodes = incomingMessage["payload"]["nodes"]
			# check if nodes is of type list
			if not isinstance(nodes, list):
				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "nodes not of type list"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			sensors = incomingMessage["payload"]["sensors"]
			# check if sensors is of type list
			if not isinstance(sensors, list):
				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "sensors not of type list"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			managers = incomingMessage["payload"]["managers"]
			# check if managers is of type list
			if not isinstance(managers, list):
				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "managers not of type list"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			alerts = incomingMessage["payload"]["alerts"]
			# check if alerts is of type list
			if not isinstance(alerts, list):
				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "alerts not of type list"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			alertLevels = incomingMessage["payload"]["alertLevels"]
			# check if alerts is of type list
			if not isinstance(alertLevels, list):
				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "alertLevels not of type list"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

		except Exception as e:
			logging.exception("[%s]: Received status " % self.fileName
				+ "invalid.")

			# send error message back
			try:
				message = {"clientTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "received status invalid"}
				self.client.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		logging.debug("[%s]: Received option count: %d." 
				% (self.fileName, len(options)))

		# process received options
		for i in range(len(options)):

			try:
				optionType = str(options[i]["type"])
				optionValue = float(options[i]["value"])
			except Exception as e:
				logging.exception("[%s]: Received option " % self.fileName
				+ "invalid.")

				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "received option invalid"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			logging.debug("[%s]: Received option " % self.fileName
				+ "information: '%s':%d."
				% (optionType, optionValue))

			# search option in list of known options
			# => if not known add it
			found = False
			for option in self.options:
				# ignore options that are already checked
				if option.checked:

					# check if the type is unique
					if option.type == optionType:
						logging.error("[%s]: Received optionType "
							% self.fileName
							+ "'%s' is not unique." % optionType)

						# send error message back
						try:
							message = {"clientTime": int(time.time()),
								"message": incomingMessage["message"],
								"error": "received option type not unique"}
							self.client.send(json.dumps(message))
						except Exception as e:
							pass

						return False

					continue

				# when found => mark option as checked and update information
				if option.type == optionType:
					option.checked = True
					option.value = optionValue
					found = True
					break
			# when not found => add option to list
			if not found:
				option = Option()
				option.checked = True
				option.type = optionType
				option.value = optionValue
				self.options.append(option)

		# check if all options are checked
		# => if not, one was removed on the server
		if not self._checkAllOptionsAreChecked():
			logging.exception("[%s]: Options are inconsistent."
				% self.fileName)

			# send error message back
			try:
				message = {"clientTime": int(time.time()),
					"message": incomingMessage["message"],
					"error": "options are inconsistent"}
				self.client.send(json.dumps(message))
			except Exception as e:
				pass

			return False

		logging.debug("[%s]: Received node count: %d." 
				% (self.fileName, len(nodes)))

		# process received nodes
		for i in range(len(nodes)):

			try:
				nodeId = int(nodes[i]["nodeId"])
				hostname = str(nodes[i]["hostname"])
				nodeType = str(nodes[i]["nodeType"])
				connected = int(nodes[i]["connected"])
			except Exception as e:
				logging.exception("[%s]: Received node " % self.fileName
				+ "invalid.")

				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "received node invalid"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			logging.debug("[%s]: Received node " % self.fileName
				+ "information: %d:'%s':'%s':%d." 
				% (nodeId, hostname, nodeType, connected))

			# search node in list of known nodes
			# => if not known add it
			found = False
			for node in self.nodes:
				# ignore nodes that are already checked
				if node.checked:

					# check if the nodeId is unique
					if node.nodeId == nodeId:
						logging.error("[%s]: Received nodeId " % self.fileName
							+ "'%d' is not unique." % nodeId)

						# send error message back
						try:
							message = {"clientTime": int(time.time()),
								"message": incomingMessage["message"],
								"error": "received node id not unique"}
							self.client.send(json.dumps(message))
						except Exception as e:
							pass

						return False

					continue

				# when found => mark node as checked and update information
				if node.nodeId == nodeId:
					node.checked = True
					node.hostname = hostname
					node.nodeType = nodeType
					node.connected = connected
					found = True
					break
			# when not found => add node to list
			if not found:
				node = Node()
				node.checked = True
				node.nodeId = nodeId
				node.hostname = hostname
				node.nodeType = nodeType
				node.connected = connected
				self.nodes.append(node)

		logging.debug("[%s]: Received sensor count: %d." 
				% (self.fileName, len(sensors)))

		# process received sensors
		for i in range(len(sensors)):

			try:
				nodeId = int(sensors[i]["nodeId"])
				sensorId = int(sensors[i]["sensorId"])
				alertDelay = int(sensors[i]["alertDelay"])

				sensorAlertLevels = sensors[i]["alertLevels"]
				# check if alertLevels is a list
				if not isinstance(sensorAlertLevels, list):
					# send error message back
					try:
						message = {"clientTime": int(time.time()),
							"message": message["message"],
							"error": "alertLevels not of type list"}
						self.client.send(json.dumps(message))
					except Exception as e:
						pass

					return False
				# check if all elements of the alertLevels list 
				# are of type int
				if not all(isinstance(item, int) for item in
					sensorAlertLevels):
					# send error message back
					try:
						message = {"clientTime": int(time.time()),
							"message": message["message"],
							"error": "alertLevels items not of type int"}
						self.client.send(json.dumps(message))
					except Exception as e:
						pass

					return False

				description = str(sensors[i]["description"])
				lastStateUpdated = int(sensors[i]["lastStateUpdated"])
				state = int(sensors[i]["state"])
			except Exception as e:
				logging.exception("[%s]: Received sensor " % self.fileName
				+ "invalid.")

				# send error message back
				try:
					message = {"clientTime": int(time.time()),
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

			# search sensor in list of known sensors
			# => if not known add it
			found = False
			for sensor in self.sensors:
				# ignore sensors that are already checked
				if sensor.checked:

					# check if the sensorId is unique
					if sensor.sensorId == sensorId:
						logging.error("[%s]: Received sensorId "
							% self.fileName
							+ "'%d' is not unique." % sensorId)

						# send error message back
						try:
							message = {"clientTime": int(time.time()),
								"message": incomingMessage["message"],
								"error": "received sensor id not unique"}
							self.client.send(json.dumps(message))
						except Exception as e:
							pass

						return False

					continue

				# when found => mark sensor as checked and update information
				if sensor.sensorId == sensorId:
					sensor.checked = True

					sensor.nodeId = nodeId
					sensor.alertDelay = alertDelay
					sensor.alertLevels = sensorAlertLevels				
					sensor.description = description
					sensor.serverTime = serverTime

					# only update state if it is older than received one
					if lastStateUpdated > sensor.lastStateUpdated:
						sensor.lastStateUpdated = lastStateUpdated
						sensor.state = state

					found = True
					break
			# when not found => add sensor to list
			if not found:
				sensor = Sensor()
				sensor.checked = True
				sensor.sensorId = sensorId
				sensor.nodeId = nodeId
				sensor.alertDelay = alertDelay
				sensor.alertLevels = sensorAlertLevels
				sensor.description = description
				sensor.lastStateUpdated = lastStateUpdated
				sensor.state = state
				sensor.serverTime = serverTime
				self.sensors.append(sensor)

		logging.debug("[%s]: Received manager count: %d." 
				% (self.fileName, len(managers)))

		# process received managers
		for i in range(len(managers)):

			try:
				nodeId = int(managers[i]["nodeId"])
				managerId = int(managers[i]["managerId"])
				description = str(managers[i]["description"])
			except Exception as e:
				logging.exception("[%s]: Received manager " % self.fileName
				+ "invalid.")

				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "received manager invalid"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			logging.debug("[%s]: Received manager " % self.fileName
				+ "information: %d:%d:'%s'." 
				% (nodeId, managerId, description))

			# search manager in list of known managers
			# => if not known add it
			found = False
			for manager in self.managers:
				# ignore managers that are already checked
				if manager.checked:

					# check if the managerId is unique
					if manager.managerId == managerId:
						logging.error("[%s]: Received managerId "
							% self.fileName
							+ "'%d' is not unique." % managerId)

						# send error message back
						try:
							message = {"clientTime": int(time.time()),
								"message": incomingMessage["message"],
								"error": "received manager id not unique"}
							self.client.send(json.dumps(message))
						except Exception as e:
							pass

						return False

					continue

				# when found => mark manager as checked and update information
				if manager.managerId == managerId:
					manager.checked = True
					manager.nodeId = nodeId
					manager.description = description
					found = True
					break
			# when not found => add manager to list
			if not found:
				manager = Manager()
				manager.checked = True
				manager.managerId = managerId
				manager.nodeId = nodeId
				manager.description = description
				self.managers.append(manager)

		logging.debug("[%s]: Received alert count: %d." 
				% (self.fileName, len(alerts)))

		# process received alerts
		for i in range(len(alerts)):

			try:
				nodeId = int(alerts[i]["nodeId"])
				alertId =int(alerts[i]["alertId"])
				description = str(alerts[i]["description"])

				alertAlertLevels = alerts[i]["alertLevels"]
				# check if alertLevels is a list
				if not isinstance(alertAlertLevels, list):
					# send error message back
					try:
						message = {"clientTime": int(time.time()),
							"message": message["message"],
							"error": "alertLevels not of type list"}
						self.client.send(json.dumps(message))
					except Exception as e:
						pass

					return False
				# check if all elements of the alertLevels list 
				# are of type int
				if not all(isinstance(item, int) for item in alertAlertLevels):
					# send error message back
					try:
						message = {"clientTime": int(time.time()),
							"message": message["message"],
							"error": "alertLevels items not of type int"}
						self.client.send(json.dumps(message))
					except Exception as e:
						pass

					return False

			except Exception as e:
				logging.exception("[%s]: Received alert " % self.fileName
				+ "invalid.")

				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "received alert invalid"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			logging.debug("[%s]: Received alert " % self.fileName
				+ "information: %d:%d:'%s'" 
				% (nodeId, alertId, description))

			# search alert in list of known alerts
			# => if not known add it
			found = False
			for alert in self.alerts:
				# ignore alerts that are already checked
				if alert.checked:

					# check if the alertId is unique
					if alert.alertId == alertId:
						logging.error("[%s]: Received alertId " % self.fileName
							+ "'%d' is not unique." % alertId)

						# send error message back
						try:
							message = {"clientTime": int(time.time()),
								"message": incomingMessage["message"],
								"error": "received alert id not unique"}
							self.client.send(json.dumps(message))
						except Exception as e:
							pass

						return False

					continue

				# when found => mark alert as checked and update information
				if alert.alertId == alertId:
					alert.checked = True
					alert.nodeId = nodeId
					alert.alertLevels = alertAlertLevels
					alert.description = description
					found = True
					break

			# when not found => add alert to list
			if not found:
				alert = Alert()
				alert.checked = True
				alert.alertId = alertId
				alert.nodeId = nodeId
				alert.alertLevels = alertAlertLevels
				alert.description = description
				self.alerts.append(alert)

		logging.debug("[%s]: Received alertLevel count: %d." 
				% (self.fileName, len(alertLevels)))

		# process received alertLevels
		for i in range(len(alertLevels)):

			try:
				level = int(alertLevels[i]["alertLevel"])
				name = str(alertLevels[i]["name"])
				triggerAlways = int(alertLevels[i]["triggerAlways"])
				smtpActivated = int(alertLevels[i]["smtpActivated"])
				toAddr = str(alertLevels[i]["toAddr"])

			except Exception as e:
				logging.exception("[%s]: Received alertLevel " % self.fileName
				+ "invalid.")

				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": incomingMessage["message"],
						"error": "received alertLevel invalid"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			logging.debug("[%s]: Received alertLevel " % self.fileName
				+ "information: %d:'%s':%d:%d:'%s'" 
				% (level, name, triggerAlways, smtpActivated, toAddr))

			# search alertLevel in list of known alertLevels
			# => if not known add it
			found = False
			for alertLevel in self.alertLevels:
				# ignore alertLevels that are already checked
				if alertLevel.checked:

					# check if the level is unique
					if alertLevel.level == level:
						logging.error("[%s]: Received alertLevel "
							% self.fileName
							+ "'%d' is not unique." % level)

						# send error message back
						try:
							message = {"clientTime": int(time.time()),
								"message": incomingMessage["message"],
								"error": "received alertLevel not unique"}
							self.client.send(json.dumps(message))
						except Exception as e:
							pass

						return False

					continue

				# when found => mark alertLevel as checked
				# and update information
				if alertLevel.level == level:
					alertLevel.checked = True
					alertLevel.smtpActivated = smtpActivated
					alertLevel.toAddr = toAddr
					alertLevel.name = name
					alertLevel.triggerAlways = triggerAlways

					found = True
					break
			# when not found => add alertLevel to list
			if not found:
				alertLevel = AlertLevel()
				alertLevel.checked = True
				alertLevel.level = level
				alertLevel.smtpActivated = smtpActivated
				alertLevel.toAddr = toAddr
				alertLevel.name = name
				alertLevel.triggerAlways = triggerAlways
				self.alertLevels.append(alertLevel)

		# sending sensor alert response
		logging.debug("[%s]: Sending status " % self.fileName
			+ "response message.")
		try:

			payload = {"type": "response", "result": "ok"}
			message = {"clientTime": int(time.time()),
				"message": "status", "payload": payload}
			self.client.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending status " % self.fileName
				+ "response failed.")

			return False

		# remove all nodes that are not checked
		self._removeNotCheckedNodes()

		# wake up the screen updater
		self.screenUpdater.screenUpdaterEvent.set()

		return True


	# internal function that handles received sensor alerts
	def _sensorAlertHandler(self, incomingMessage):

		logging.debug("[%s]: Received sensor alert." % self.fileName)

		# extract sensor alert values
		try:
			serverTime = int(incomingMessage["serverTime"])
			sensorId = int(incomingMessage["payload"]["sensorId"])
			state = int(incomingMessage["payload"]["state"])

			alertLevels = incomingMessage["payload"]["alertLevels"]
			# check if alertLevels is a list
			if not isinstance(alertLevels, list):
				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": message["message"],
						"error": "alertLevels not of type list"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False
			# check if all elements of the alertLevels list 
			# are of type int
			if not all(isinstance(item, int) for item in alertLevels):
				# send error message back
				try:
					message = {"clientTime": int(time.time()),
						"message": message["message"],
						"error": "alertLevels items not of type int"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				return False

			description = str(incomingMessage["payload"]["description"])
		except Exception as e:
			logging.exception("[%s]: Received sensor alert " % self.fileName
				+ "invalid.")

			# send error message back
			try:
				message = {"clientTime": int(time.time()),
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
			message = {"clientTime": int(time.time()),
				"message": "sensoralert", "payload": payload}
			self.client.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending sensor alert " % self.fileName
				+ "response failed.")

			return False

		# generate sensor alert object
		sensorAlert = SensorAlert()
		sensorAlert.sensorId = sensorId
		sensorAlert.state = state
		sensorAlert.timeReceived = int(time.time())
		sensorAlert.alertLevels = alertLevels
		self.sensorAlerts.append(sensorAlert)

		# update information in sensor which triggered the alert
		for sensor in self.sensors:
			if sensor.sensorId == sensorId:
				sensor.state = state
				sensor.lastStateUpdated = serverTime
				sensor.serverTime = serverTime

		return True


	# internal function that handles received state changes of sensors
	def _stateChangeHandler(self, incomingMessage):

		logging.debug("[%s]: Received state change." % self.fileName)
		
		# extract state change values
		try:
			serverTime = int(incomingMessage["serverTime"])
			sensorId = int(incomingMessage["payload"]["sensorId"])
			state = int(incomingMessage["payload"]["state"])
		except Exception as e:
			logging.exception("[%s]: Received state change " % self.fileName
				+ "invalid.")

			# send error message back
			try:
				message = {"clientTime": int(time.time()),
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
			message = {"clientTime": int(time.time()),
				"message": "statechange", "payload": payload}
			self.client.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending state change " % self.fileName
				+ "response failed.")

			return False

		# search sensor in list of known sensors
		# => if not known return failure
		found = False
		for sensor in self.sensors:

			# when found => mark sensor as checked and update information
			if sensor.sensorId == sensorId:
				sensor.state = state
				sensor.lastStateUpdated = serverTime
				sensor.serverTime = serverTime

				found = True
				break
		if not found:
			logging.error("[%s]: Sensor for state change " % self.fileName
				+ "not known.")

			return False

		return True


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

		# get the initial status update from the server
		try:
			logging.debug("[%s]: Receiving initial status update."
				% self.fileName)

			data = self.client.recv(BUFSIZE).strip()
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

				# received RTS (request to send) message
				logging.debug("[%s]: Received RTS %s message."
					% (self.fileName, receivedTransactionId))
					
				logging.debug("[%s]: Sending CTS %s message."
					% (self.fileName, receivedTransactionId))

				# send CTS (clear to send) message
				payload = {"type": "cts", "id": receivedTransactionId}
				message = {"clientTime": int(time.time()),
					"message": str(message["message"]),
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
					message = {"clientTime": int(time.time()),
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
				message = {"clientTime": int(time.time()),
					"message": message["message"],
					"error": "initial status update expected"}
				self.client.send(json.dumps(message))
			except Exception as e:
				pass

			self._releaseLock()
			return False

		if not self._statusUpdateHandler(message):
			self.client.close()
			logging.error("[%s]: Initial status update failed." 
				% self.fileName)			

			self._releaseLock()
			return False

		self._releaseLock()

		self.lastRecv = time.time()

		# set client as connected
		self.isConnected = True
		# wake up the screen updater
		self.screenUpdater.screenUpdaterEvent.set()		

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
					message = {"clientTime": int(time.time()),
						"message": str(message["message"]),
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
						message = {"clientTime": int(time.time()),
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
					message = {"clientTime": int(time.time()),
						"message": message["message"],
						"error": "unknown command/message type"}
					self.client.send(json.dumps(message))
				except Exception as e:
					pass

				# clean up session before exiting
				self._cleanUpSessionForClosing()
				self._releaseLock()
				return

			# wake up the screen updater
			self.screenUpdater.screenUpdaterEvent.set()

			self.lastRecv = time.time()


	# this function sends an option change to the server for example
	# to activate the alert system or deactivate it
	def sendOption(self, optionType, optionValue, optionDelay=0):

		# initiate transaction with server and acquire lock
		if not self._initiateTransaction("option", acquireLock=True):
			return False

		# send option request
		try:
			logging.debug("[%s]: Sending option message." % self.fileName)

			payload = {"type": "request",
				"optionType": optionType,
				"value": float(optionValue),
				"timeDelay": optionDelay}
			message = {"clientTime": int(time.time()),
				"message": "option", "payload": payload}
			self.client.send(json.dumps(message))

		except Exception as e:
			logging.exception("[%s]: Sending option message failed." 
				% self.fileName)			

			# clean up session before exiting
			self._cleanUpSessionForClosing()
			self._releaseLock()
			return False

		# get option response from server
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

			if str(message["message"]).upper() != "OPTION":
				logging.error("[%s]: Wrong option message: "
					% self.fileName
					+ "'%s'." % message["message"])

				# send error message back
				try:
					message = {"clientTime": int(time.time()),
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
					message = {"clientTime": int(time.time()),
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

		self.lastRecv = time.time()
		self._releaseLock()

		return True


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
			message = {"clientTime": int(time.time()),
				"message": "ping", "payload": payload}
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
					message = {"clientTime": int(time.time()),
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
					message = {"clientTime": int(time.time()),
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

		# check every 5 seconds if the time of the last received data 
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
class Receiver(threading.Thread):

	def __init__(self, connection):
		threading.Thread.__init__(self)
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