#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

from serverObjects import Option, Node, Sensor, Manager, Alert, SensorAlert
import socket
import time
import ssl
import threading
import logging
import os
import base64
import ConfigParser
import random
BUFSIZE = 2048


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
		self.description = self.globalData.description
		self.screenUpdater = self.globalData.screenUpdater
		# list of alert system information
		self.options = self.globalData.options
		self.nodes = self.globalData.nodes
		self.sensors = self.globalData.sensors
		self.managers = self.globalData.managers
		self.alerts = self.globalData.alerts
		self.sensorAlerts = self.globalData.sensorAlerts		
		
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
	def _initiateTransaction(self, acquireLock=False):

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
			transactionId = os.urandom(12)

			# send RTS (request to send) message
			logging.debug("[%s]: Sending RTS %s message."
				% (self.fileName, base64.b64encode(transactionId)))
			try:
				message = "RTS %s\r\n" % base64.b64encode(transactionId)
				self.client.send(message)
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
				splittedData = data.split()
				receivedTransactionId = base64.b64decode(splittedData[1])
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
			if (splittedData[0] == "CTS"
				and receivedTransactionId == transactionId):

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


	# internal function to authenticate the client
	def _authenticate(self):

		# send username and verify response
		try:
			logging.debug("[%s]: Sending username '%s'." 
				% (self.fileName, self.username))
			self.client.send("USER %s\r\n" % self.username)
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Sending username failed." % self.fileName)
			return False

		if data != "OK":
			logging.error("[%s]: Authentication failed. " % self.fileName
				+ "Server responded with: '%s'" % data)
			return False

		# send password and verify response
		try:
			logging.debug("[%s]: Sending password." % self.fileName)
			self.client.send("PASS %s\r\n" % self.password)
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Sending password failed." % self.fileName)
			return False

		if data != "AUTHENTICATED":
			logging.error("[%s]: Authentication failed. " % self.fileName
				+ "Server responded with: '%s'" % data)
			return False		

		return True


	# internal function to verify the server/client version
	def _verifyVersion(self):

		# verify server version
		try:
			data = self.client.recv(BUFSIZE).strip()
			splittedData = data.split()
			if len(splittedData) != 2:
				logging.error("[%s]: Received malformed version message." 
					% self.fileName)
				return False
			command = splittedData[0].upper()
			version = float(splittedData[1])
		except Exception as e:
			logging.exception("[%s]: Receiving version failed." 
				% self.fileName)
			return False			

		if command != "VERSION":
			logging.error("[%s]: Receiving VERSION failed. Server sent: '%s'" 
				% (self.fileName, command))
			return False

		if version != self.version:
			logging.error("[%s]: Version not compatible. " % self.fileName
				+ "Client has version: '%.1f' and server has '%.1f" 
				% (self.version, version))
			return False

		logging.debug("[%s]: Received server version: '%.1f'." 
				% (self.fileName, version))
		
		# acknowledge server version
		try:
			self.client.send("OK\r\n")	
		except Exception as e:
			logging.exception("[%s]: Sending version acknowledgement failed." 
				% self.fileName)
			return False

		# sending client version
		try:
			logging.debug("[%s]: Sending client version: '%.1f'." 
				% (self.fileName, self.version))
			self.client.send("VERSION %.1f\r\n" % self.version)	
		except Exception as e:
			logging.exception("[%s]: Sending version failed." % self.fileName)
			return False

		# receive version acknowledgement and verify it
		try:
			data = self.client.recv(BUFSIZE).strip()		
		except Exception as e:
			logging.exception("[%s]: Receiving version " % self.fileName
				+ "acknowledgement failed.")
			return False

		if data.upper() != "OK":
			logging.error("[%s]: Expected version acknowledgement. " 
				% self.fileName + "Received: '%s'" % data)
			return False

		return True


	# internal function to register the node
	def _registerNode(self):

		# send registration start message
		try:
			logging.debug("[%s]: Sending registration start." % self.fileName)
			self.client.send("REGISTER START\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending registration start failed." 
				% self.fileName)
			return False

		# check if node is already registered at server with this
		# configuration
		if self.registered is True:
			message = "CONFIGURATION old\r\n"
		else:
			message = "CONFIGURATION new\r\n"

		# send configuration new/old message
		try:
			logging.debug("[%s]: Sending node configuration message." 
				% self.fileName)
			self.client.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending node " % self.fileName
				+ "configuration message failed.")
			return False		

		# send node registration message
		message = "NODE %s %s\r\n" \
			% (base64.b64encode(socket.gethostname()), self.nodeType)
		try:
			logging.debug("[%s]: Sending node registration message." 
				% self.fileName)
			self.client.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending node registration message failed."
				% self.fileName)
			return False

		# send manager information message
		message = "MANAGER %s\r\n" % base64.b64encode(self.description)
		try:
			logging.debug("[%s]: Sending manager information message." 
				% self.fileName)
			self.client.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending manager " % self.fileName
				+ "information message failed.")
			return False

		# send registration end message
		try:
			logging.debug("[%s]: Sending registration end." % self.fileName)
			self.client.send("REGISTER END\r\n")
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Sending registration end failed." 
				% self.fileName)
			return False

		if data != "REGISTERED":
			logging.error("[%s]: Registration failed. " % self.fileName
				+ "Server responded with: '%s'" % data)
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


	# internal function that handles received status updates
	def _statusUpdateHandler(self):

		# first mark all nodes as not checked
		self._markAlertSystemObjectsAsNotChecked()

		# receiving OPTION START from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving OPTION START failed." 
				% self.fileName)
			return False

		if (data != "OPTION START"):
			logging.error("[%s]: Receiving OPTION START " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received OPTION START message." % self.fileName)

		# receiving option count message
		try:
			data = self.client.recv(BUFSIZE).strip()
			splittedData = data.split()
			optionCount = int(splittedData[1])
		except Exception as e:
			logging.exception("[%s]: Receiving " % self.fileName
				+ "OPTIONCOUNT failed.")
			return False

		if (len(splittedData) != 2
			or splittedData[0].upper() != "OPTIONCOUNT"):
			logging.error("[%s]: Receiving " % self.fileName
				+ "OPTIONCOUNT failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received option count: %d." 
				% (self.fileName, optionCount))

		for i in range(optionCount):

			# receiving option information message
			try:
				data = self.client.recv(BUFSIZE).strip()
				splittedData = data.split()
				optionType = base64.b64decode(splittedData[1])
				optionValue = int(splittedData[2])
			except Exception as e:
				logging.exception("[%s]: Receiving " % self.fileName
					+ "OPTION failed.")
				return False

			if (len(splittedData) != 3
				or splittedData[0].upper() != "OPTION"):
				logging.error("[%s]: Receiving OPTION " % self.fileName
					+ "failed. Server sent: '%s'." % data)
				return False

			logging.debug("[%s]: Received option " % self.fileName
				+ "information message: '%s':%d." 
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
			return False

		# receiving OPTION END from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving OPTION END failed." 
				% self.fileName)
			return False

		if (data != "OPTION END"):
			logging.error("[%s]: Receiving OPTION END " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		# receiving NODE START from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving NODE START failed." 
				% self.fileName)
			return False

		if (data != "NODE START"):
			logging.error("[%s]: Receiving NODE START " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received NODE START message." % self.fileName)

		# receiving node count message
		try:
			data = self.client.recv(BUFSIZE).strip()
			splittedData = data.split()
			nodeCount = int(splittedData[1])
		except Exception as e:
			logging.exception("[%s]: Receiving " % self.fileName
				+ "NODECOUNT failed.")
			return False

		if (len(splittedData) != 2
			or splittedData[0].upper() != "NODECOUNT"):
			logging.error("[%s]: Receiving " % self.fileName
				+ "NODECOUNT failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received node count: %d." 
				% (self.fileName, nodeCount))

		for i in range(nodeCount):

			# receiving node information message
			try:
				data = self.client.recv(BUFSIZE).strip()
				splittedData = data.split()
				nodeId = int(splittedData[1])
				hostname = base64.b64decode(splittedData[2])
				nodeType = splittedData[3]
				connected = int(splittedData[4])
			except Exception as e:
				logging.exception("[%s]: Receiving " % self.fileName
					+ "NODE failed.")
				return False

			if (len(splittedData) != 5
				or splittedData[0].upper() != "NODE"):
				logging.error("[%s]: Receiving NODE " % self.fileName
					+ "failed. Server sent: '%s'." % data)
				return False

			logging.debug("[%s]: Received node " % self.fileName
				+ "information message: %d:'%s':'%s':%d." 
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

		# receiving NODE END from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving NODE END failed." 
				% self.fileName)
			return False

		if (data != "NODE END"):
			logging.error("[%s]: Receiving NODE END " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		# receiving SENSOR START from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving SENSOR START failed." 
				% self.fileName)
			return False

		if (data != "SENSOR START"):
			logging.error("[%s]: Receiving SENSOR START " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received SENSOR START message." % self.fileName)

		# receiving sensor count message
		try:
			data = self.client.recv(BUFSIZE).strip()
			splittedData = data.split()
			sensorCount = int(splittedData[1])
		except Exception as e:
			logging.exception("[%s]: Receiving " % self.fileName
				+ "SENSORCOUNT failed.")
			return False

		if (len(splittedData) != 2
			or splittedData[0].upper() != "SENSORCOUNT"):
			logging.error("[%s]: Receiving " % self.fileName
				+ "SENSORCOUNT failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received sensor count: %d." 
				% (self.fileName, sensorCount))

		for i in range(sensorCount):

			# receiving sensor information message
			try:
				data = self.client.recv(BUFSIZE).strip()
				splittedData = data.split()
				nodeId = int(splittedData[1])
				sensorId = int(splittedData[2])
				alertDelay = int(splittedData[3])
				alertLevel = int(splittedData[4])
				description = base64.b64decode(splittedData[5])
				lastStateUpdated = int(splittedData[6])
				state = int(splittedData[7])
			except Exception as e:
				logging.exception("[%s]: Receiving " % self.fileName
					+ "SENSOR failed.")
				return False

			if (len(splittedData) != 8
				or splittedData[0].upper() != "SENSOR"):
				logging.error("[%s]: Receiving SENSOR " % self.fileName
					+ "failed. Server sent: '%s'." % data)
				return False

			logging.debug("[%s]: Received sensor " % self.fileName
				+ "information message: %d:%d:%d:%d:'%s':%d:%d." 
				% (nodeId, sensorId, alertDelay, alertLevel, description,
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
						return False

					continue

				# when found => mark sensor as checked and update information
				if sensor.sensorId == sensorId:
					sensor.checked = True

					sensor.nodeId = nodeId
					sensor.alertDelay = alertDelay
					sensor.alertLevel = alertLevel
					sensor.description = description

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
				sensor.alertLevel = alertLevel
				sensor.description = description
				sensor.lastStateUpdated = lastStateUpdated
				sensor.state = state
				self.sensors.append(sensor)

		# receiving SENSOR END from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving SENSOR END failed." 
				% self.fileName)
			return False

		if (data != "SENSOR END"):
			logging.error("[%s]: Receiving SENSOR END " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		# receiving MANAGER START from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving MANAGER START failed." 
				% self.fileName)
			return False

		if (data != "MANAGER START"):
			logging.error("[%s]: Receiving MANAGER START " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received MANAGER START message." % self.fileName)

		# receiving manager count message
		try:
			data = self.client.recv(BUFSIZE).strip()
			splittedData = data.split()
			managerCount = int(splittedData[1])
		except Exception as e:
			logging.exception("[%s]: Receiving " % self.fileName
				+ "MANAGERCOUNT failed.")
			return False

		if (len(splittedData) != 2
			or splittedData[0].upper() != "MANAGERCOUNT"):
			logging.error("[%s]: Receiving " % self.fileName
				+ "MANAGERCOUNT failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received manager count: %d." 
				% (self.fileName, managerCount))

		for i in range(managerCount):

			# receiving manager information message
			try:
				data = self.client.recv(BUFSIZE).strip()
				splittedData = data.split()
				nodeId = int(splittedData[1])
				managerId = int(splittedData[2])
				description = base64.b64decode(splittedData[3])
			except Exception as e:
				logging.exception("[%s]: Receiving " % self.fileName
					+ "MANAGER failed.")
				return False

			if (len(splittedData) != 4
				or splittedData[0].upper() != "MANAGER"):
				logging.error("[%s]: Receiving MANAGER " % self.fileName
					+ "failed. Server sent: '%s'." % data)
				return False

			logging.debug("[%s]: Received manager " % self.fileName
				+ "information message: %d:%d:'%s'." 
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

		# receiving MANAGER END from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving MANAGER END failed." 
				% self.fileName)
			return False

		if (data != "MANAGER END"):
			logging.error("[%s]: Receiving MANAGER END " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		# receiving ALERT START from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving ALERT START failed." 
				% self.fileName)
			return False

		if (data != "ALERT START"):
			logging.error("[%s]: Receiving ALERT START " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received ALERT START message." % self.fileName)

		# receiving alert count message
		try:
			data = self.client.recv(BUFSIZE).strip()
			splittedData = data.split()
			alertCount = int(splittedData[1])
		except Exception as e:
			logging.exception("[%s]: Receiving " % self.fileName
				+ "ALERTCOUNT failed.")
			return False

		if (len(splittedData) != 2
			or splittedData[0].upper() != "ALERTCOUNT"):
			logging.error("[%s]: Receiving " % self.fileName
				+ "ALERTCOUNT failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received alert count: %d." 
				% (self.fileName, alertCount))

		for i in range(alertCount):

			# receiving alert information message
			try:
				data = self.client.recv(BUFSIZE).strip()
				splittedData = data.split()
				nodeId = int(splittedData[1])
				alertId =int(splittedData[2])
				description = base64.b64decode(splittedData[3])
			except Exception as e:
				logging.exception("[%s]: Receiving " % self.fileName
					+ "ALERT failed.")
				return False

			if (len(splittedData) != 4
				or splittedData[0].upper() != "ALERT"):
				logging.error("[%s]: Receiving ALERT " % self.fileName
					+ "failed. Server sent: '%s'." % data)
				return False

			logging.debug("[%s]: Received alert " % self.fileName
				+ "information message: %d:%d:'%s'" 
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
						return False

					continue

				# when found => mark alert as checked and update information
				if alert.alertId == alertId:
					alert.checked = True
					alert.nodeId = nodeId
					alert.description = description
					found = True
					break

			# when not found => add alert to list
			if not found:
				alert = Alert()
				alert.checked = True
				alert.alertId = alertId
				alert.nodeId = nodeId
				alert.description = description
				self.alerts.append(alert)

		# receiving ALERT END from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving ALERT END failed." 
				% self.fileName)
			return False

		if (data != "ALERT END"):
			logging.error("[%s]: Receiving ALERT END " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		# receiving STATUS END from the server
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving STATUS END failed." 
				% self.fileName)
			return False

		if (data != "STATUS END"):
			logging.error("[%s]: Receiving STATUS END " % self.fileName
				+ "failed. Server sent: '%s'." % data)
			return False

		logging.debug("[%s]: Received STATUS END message." % self.fileName)

		# acknowledge status update
		try:
			self.client.send("STATUS OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending status update " % self.fileName
				+ "acknowledgement failed.")

			return False

		# remove all nodes that are not checked
		self._removeNotCheckedNodes()

		# wake up the screen updater
		self.screenUpdater.screenUpdaterEvent.set()

		return True


	# internal function that handles received sensor alerts
	def _sensorAlertHandler(self, data):

		logging.debug("[%s]: Received sensor alert." % self.fileName)
		
		# extract data form sensor alert message
		try:
			splittedData = data.split()
			sensorId = int(splittedData[1])
			state = int(splittedData[2])
			alertLevel = int(splittedData[3])
		except Exception as e:
			logging.exception("[%s]: Receiving sensor alert " % self.fileName
				+ "failed.")

			return False

		# acknowledge sensor alert
		logging.debug("[%s]: Sending SENSORALERT OK message." % self.fileName)
		try:
			self.client.send("SENSORALERT OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending sensor alert " % self.fileName
				+ "acknowledgement failed.")

			return False

		# generate sensor alert object
		sensorAlert = SensorAlert()
		sensorAlert.sensorId = sensorId
		sensorAlert.state = state
		sensorAlert.timeReceived = int(time.time())
		self.sensorAlerts.append(sensorAlert)

		# update information in sensor which triggered the alert
		for sensor in self.sensors:
			if sensor.sensorId == sensorId:
				sensor.state = state
				sensor.lastStateUpdated = int(time.time())

		return True


	# internal function that handles received state changes of sensors
	def _stateChangeHandler(self, data):

		logging.debug("[%s]: Received state change." % self.fileName)
		
		# extract data form state change message
		try:
			splittedData = data.split()
			sensorId = int(splittedData[1])
			state = int(splittedData[2])
		except Exception as e:
			logging.exception("[%s]: Receiving state change " % self.fileName
				+ "failed.")

			return False

		# acknowledge state change
		logging.debug("[%s]: Sending STATECHANGE OK message." % self.fileName)
		try:
			self.client.send("STATECHANGE OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending state change " % self.fileName
				+ "acknowledgement failed.")

			return False

		# search sensor in list of known sensors
		# => if not known return failure
		found = False
		for sensor in self.sensors:

			# when found => mark sensor as checked and update information
			if sensor.sensorId == sensorId:
				sensor.state = state

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
		self.client = Client(self.host, self.port, self.caFile)
		try:
			self.client.connect()
		except Exception as e:
			self.client.close()
			logging.exception("[%s]: Connecting to server failed." 
				% self.fileName)

			self._releaseLock()

			return False
		
		# first check and send version 
		if not self._verifyVersion():
			self.client.close()
			logging.error("[%s]: Version verification failed." 
				% self.fileName)

			self._releaseLock()

			return False

		# second authenticate client
		if not self._authenticate():
			self.client.close()
			logging.error("[%s]: Authentication failed." 
				% self.fileName)			

			self._releaseLock()

			return False

		# third register node
		if not self._registerNode():
			self.client.close()
			logging.error("[%s]: Registration failed." 
				% self.fileName)			

			self._releaseLock()	

			return False

		# get the initial status update from the server
		try:
			logging.debug("[%s]: Receiving status update start."
				% self.fileName)
			data = self.client.recv(BUFSIZE).strip()

			# check if RTS was received
			# => acknowledge it
			splittedData = data.split()
			receivedTransactionId = splittedData[1]
			if splittedData[0] == "RTS":

				# received RTS (request to send) message
				logging.debug("[%s]: Received RTS %s message."
					% (self.fileName, receivedTransactionId))

				# send CTS (clear to send) message
				logging.debug("[%s]: Sending CTS %s message."
					% (self.fileName, receivedTransactionId))

				message = "CTS %s\r\n" % receivedTransactionId
				self.client.send(message)

			# if no RTS was received
			# => server does not stick to protocol 
			# => terminate session
			else:

				logging.error("[%s]: Did not receive " % self.fileName
					+ "RTS. Server sent: '%s'." % data)

				self._releaseLock()

				return False

			data = self.client.recv(BUFSIZE).strip()

		except Exception as e:
			logging.exception("[%s]: Receiving status update start failed." 
				% self.fileName)
			return False

		if data != "STATUS START":
			logging.error("[%s]: Receiving status update " % self.fileName
				+ "failed. Server sent: '%s'" % data)
			return False

		if not self._statusUpdateHandler():
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

				# check if RTS was received
				# => acknowledge it
				splittedData = data.split()
				receivedTransactionId = splittedData[1]
				if splittedData[0] == "RTS":

					# received RTS (request to send) message
					logging.debug("[%s]: Received RTS %s message."
						% (self.fileName, receivedTransactionId))

					# send CTS (clear to send) message
					logging.debug("[%s]: Sending CTS %s message."
						% (self.fileName, receivedTransactionId))

					message = "CTS %s\r\n" % receivedTransactionId
					self.client.send(message)

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

			splittedData = data.split()
			if len(splittedData) < 1:
				continue

			# extract command
			command = splittedData[0].upper()

			# check if SENSORALERT was received
			# => update screen
			if (command == "SENSORALERT"
				and len(splittedData) == 4):

					# handle sensor alert
					if not self._sensorAlertHandler(data):

						logging.error("[%s]: Receiving sensor alert failed." 
							% self.fileName)

						# clean up session before exiting
						self._cleanUpSessionForClosing()

						self._releaseLock()	

						return

			# check if STATUS START was received
			# => get status update
			elif (command == "STATUS"
				and splittedData[1].upper() == "START"):

					# get status update
					if not self._statusUpdateHandler():

						logging.error("[%s]: Receiving status update failed." 
							% self.fileName)

						# clean up session before exiting
						self._cleanUpSessionForClosing()

						self._releaseLock()	

						return

			# check if STATECHANGE was received
			# => update screen
			elif (command == "STATECHANGE"
				and len(splittedData) == 3):

					# handle sensor state change
					if not self._stateChangeHandler(data):

						logging.error("[%s]: Receiving state change failed." 
							% self.fileName)

						# clean up session before exiting
						self._cleanUpSessionForClosing()

						self._releaseLock()	

						return

			else:
				logging.error("[%s]: Received unknown " % self.fileName
					+ "command. Server sent: '%s'." % data)

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
		if not self._initiateTransaction(acquireLock=True):
			return False

		# send option message
		message = "OPTION %s %d %d\r\n" \
			% (base64.b64encode(optionType), optionValue, optionDelay)

		logging.critical(message)
		try:
			logging.debug("[%s]: Sending option message '%s':%d:%d." 
				% (self.fileName, optionType, optionValue, optionDelay))
			self.client.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending option message failed."
				% self.fileName)

			self._releaseLock()
			return False

		# receive acknowledge option message
		try:
			data = self.client.recv(BUFSIZE).strip()
		except Exception as e:
			logging.exception("[%s]: Receiving option message " % self.fileName
				+ "acknowledgement failed.")

			self._releaseLock()
			return False

		if data != "OPTION OK":
			logging.error("[%s]: Sending option failed. " % self.fileName
				+ "Server responded with: '%s'" % data)

			self._releaseLock()
			return False

		logging.debug("[%s]: Received option message acknowledgement." 
			% self.fileName)

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
		if not self._initiateTransaction(acquireLock=True):
			return False

		try:
			logging.debug("[%s]: Sending PING." % self.fileName)
			self.client.send("PING\r\n")
			data = self.client.recv(BUFSIZE).strip()
			if data.upper() != "PONG":

				self._releaseLock()

				return False
		except Exception as e:
			logging.exception("[%s]: Sending PING to server failed." 
				% self.fileName)			

			self._releaseLock()

			return False

		logging.debug("[%s]: Received PONG." % self.fileName)
		self._releaseLock()

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