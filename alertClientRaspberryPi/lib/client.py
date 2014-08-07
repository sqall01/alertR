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
from alert import AsynchronousAlertExecuter
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

		# send alert count message
		message = "ALERTCOUNT %d\r\n" % len(self.alerts)
		try:
			logging.debug("[%s]: Sending alert count message." 
				% self.fileName)
			self.client.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending alert count message failed."
				% self.fileName)
			return False

		# register all alerts
		for alert in self.alerts:

			# send alert information message
			message = "ALERT %d %s\r\n" \
				% (alert.id, base64.b64encode(alert.description))
			try:
				logging.debug("[%s]: Sending alert information message." 
					% self.fileName)
				self.client.send(message)
			except Exception as e:
				logging.exception("[%s]: Sending alert " % self.fileName
					+ "information message failed.")
				return False

		# send alert level count message
		message = "ALERTLEVELCOUNT %d\r\n" % len(self.alertLevels)
		try:
			logging.debug("[%s]: Sending alert level count message." 
				% self.fileName)
			self.client.send(message)
		except Exception as e:
			logging.exception("[%s]: Sending alert level count message failed."
				% self.fileName)
			return False

		# register all alert levels
		for alertLevel in self.alertLevels:

			# send alert information message
			message = "ALERTLEVEL %d\r\n" % alertLevel
			try:
				logging.debug("[%s]: Sending alert level information message." 
					% self.fileName)
				self.client.send(message)
			except Exception as e:
				logging.exception("[%s]: Sending alert level " % self.fileName
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
	def _sensorAlertHandler(self, data):

		logging.debug("[%s]: Received sensor alert." % self.fileName)
		
		# extract data from sensor alert message
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

		# trigger all alerts that have the same alert level
		for alert in self.alerts:
			if alertLevel in alert.alertLevels:

				# trigger alert in an own thread to not block this one
				alertTriggerProcess = AsynchronousAlertExecuter(alert)
				# set thread to daemon
				# => threads terminates when main thread terminates	
				alertTriggerProcess.daemon = True
				alertTriggerProcess.triggerAlert = True
				alertTriggerProcess.start()

		return True


	# internal function that handles received alerts off messages
	def _sensorAlertsOffHandler(self):

		logging.debug("[%s]: Received sensor alerts off." % self.fileName)
		
		# acknowledge sensor alerts off
		logging.debug("[%s]: Sending SENSORALERTSOFF OK message."
			% self.fileName)
		try:
			self.client.send("SENSORALERTSOFF OK\r\n")
		except Exception as e:
			logging.exception("[%s]: Sending sensor alerts " % self.fileName
				+ "off acknowledgement failed.")

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
			# => trigger alerts
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

			# check if SENSORALERTSOFF was received
			# => stop alerts
			elif (command == "SENSORALERTSOFF"
				and len(splittedData) == 1):

					# handle sensor alerts off message
					if not self._sensorAlertsOffHandler():

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


	# this function sends a keep alive (PING request) to the server
	# to keep the connection alive and to check if the connection
	# is still alive
	def sendKeepalive(self):

		# initiate transaction with server and acquire lock
		if not self._initiateTransaction(acquireLock=True):

			# clean up session before exiting
			self._cleanUpSessionForClosing()

			return False

		try:
			logging.debug("[%s]: Sending PING." % self.fileName)
			self.client.send("PING\r\n")
			data = self.client.recv(BUFSIZE).strip()
			if data.upper() != "PONG":

				# clean up session before exiting
				self._cleanUpSessionForClosing()

				self._releaseLock()

				return False
		except Exception as e:
			logging.exception("[%s]: Sending PING to server failed." 
				% self.fileName)			

			# clean up session before exiting
			self._cleanUpSessionForClosing()

			self._releaseLock()

			return False

		logging.debug("[%s]: Received PONG." % self.fileName)
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