#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import time
import socket
import ssl
import os
import logging
import smtplib
import threading
import base64
import json
import hashlib
from Crypto.Cipher import AES
from localObjects import SensorDataType
BUFSIZE = 4096


# Push server error codes.
class ErrorCodes:
    NO_ERROR = 0
    DATABASE_ERROR = 1
    AUTH_ERROR = 2
    ILLEGAL_MSG_ERROR = 3
    GOOGLE_MSG_TOO_LARGE = 4
    GOOGLE_CONNECTION = 5
    GOOGLE_UNKNOWN = 6
    GOOGLE_AUTH = 7
    VERSION_MISSMATCH = 8
    NO_NOTIFICATION_PERMISSION = 9


# Simple class of an ssl tcp client.
class Client:

	def __init__(self, host, port, serverCAFile):
		self.host = host
		self.port = port
		self.serverCAFile = serverCAFile
		self.socket = None
		self.sslSocket = None


	def connect(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.sslSocket = ssl.wrap_socket(self.socket,
			ca_certs=self.serverCAFile, cert_reqs=ssl.CERT_REQUIRED,
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


# Internal class that holds the important attributes
# for a alert to work with (this class must be inherited from the
# used alert class).
class _Alert:

	def __init__(self):
		self.id = None
		self.description = None
		self.alertLevels = list()


	def triggerAlert(self, sensorAlert):
		raise NotImplementedError("Function not implemented yet.")


	def stopAlert(self, sensorAlert):
		raise NotImplementedError("Function not implemented yet.")


	def initializeAlert(self):
		raise NotImplementedError("Function not implemented yet.")


# This class represents an alert that sends a notification to the push service
# on the configured channel.
class PushAlert(_Alert):

	def __init__(self, globalData):
		_Alert.__init__(self)

		self.fileName = os.path.basename(__file__)

		# this flag is used to signalize if the alert is triggered or not
		self.triggered = None

		self.globalData = globalData
		self.pushServerAddress = self.globalData.pushServerAddress
		self.pushServerPort = self.globalData.pushServerPort
		self.pushServerCert = self.globalData.pushServerCert
		self.pushRetryTimeout = self.globalData.pushRetryTimeout

		# These are the message settings.
		self.channel = None
		self.encSecret = None
		self.subject = None
		self.templateFile = None
		self.msgText = None
		self.key = None
		self.protocolVersion = 0.1
		self.username = None
		self.password = None
		self.sbjMsgSize = 1400

		# Error codes to determine if we can retry to send the message or not.
		self.retryCodes = [
			ErrorCodes.DATABASE_ERROR,
			ErrorCodes.GOOGLE_CONNECTION,
			ErrorCodes.GOOGLE_UNKNOWN,
			ErrorCodes.GOOGLE_AUTH, 
			ErrorCodes.GOOGLE_AUTH
			]
		self.notRetryCodes = [
			ErrorCodes.AUTH_ERROR,
			ErrorCodes.ILLEGAL_MSG_ERROR,
			ErrorCodes.GOOGLE_MSG_TOO_LARGE,
			ErrorCodes.VERSION_MISSMATCH,
			ErrorCodes.NO_NOTIFICATION_PERMISSION
			]


	# Create the channel name linked to the username.
	# NOTE: This function is not collision free but will improve collision
	# resistance if multiple parties choose the same channel.
	def _generatePrefixedChannel(self, username, channel):
		# Create a encryption key from the secret.
		sha256 = hashlib.sha256()
		sha256.update(username)
		prefix = sha256.hexdigest()[0:8]
		return prefix.lower() + "_" + channel


	# Internal function that prepares the data
	# (which is a json string) that is send to the devices.
	def _prepareMessage(self, payload):

		logging.debug("[%s] Preparing sensorAlert message."
				% self.fileName)

		# Add random bytes in the beginning of the message to
		# increase randomness.
		iv = os.urandom(16)
		internalIv = os.urandom(4)
		paddedPayload = internalIv + payload

		padding = len(paddedPayload) % 16
		if padding != 0:
			for i in range(16 - padding):
				# Use whitespaces as padding since they are ignored by json.
				paddedPayload += " "

		cipher = AES.new(self.key, AES.MODE_CBC, iv)
		encryptedPayload = cipher.encrypt(paddedPayload)

		temp = iv + encryptedPayload
		return base64.b64encode(temp)


	# Internal function that replaces the wildcards in the message
	# with the corresponding values.
	def _replaceWildcards(self, sensorAlert, message):

		# Create a received message text.
		if (sensorAlert.hasOptionalData
			and "message" in sensorAlert.optionalData):
			receivedMessage = sensorAlert.optionalData["message"]
		else:
			receivedMessage = "None"

		sensorDescription = sensorAlert.description

		# convert state to a text
		if sensorAlert.state == 0:
			stateMessage = "Normal"
		elif sensorAlert.state == 1:
			stateMessage = "Triggered"
		else:
			stateMessage = "Undefined"

		# Convert data to a string.
		if sensorAlert.dataType == SensorDataType.NONE:
			dataMessage = "None"
		elif (sensorAlert.dataType == SensorDataType.INT
			or sensorAlert.dataType == SensorDataType.FLOAT):
			dataMessage = str(sensorAlert.sensorData)
		else:
			dataMessage = "Unknown"

		# Replace wildcards in the message with the actual values.
		tempMsg = message.replace("$MESSAGE$", receivedMessage)
		tempMsg = tempMsg.replace("$STATE$", stateMessage)
		tempMsg = tempMsg.replace("$SENSORDESC$", sensorDescription)
		tempMsg = tempMsg.replace("$TIMERECEIVED$",
			time.strftime("%d %b %Y %H:%M:%S",
			time.localtime(sensorAlert.timeReceived)))
		tempMsg = tempMsg.replace("$SENSORDATA$", dataMessage)

		return tempMsg


	# Internal function that sends the message to the push server.
	# Returns True for not retrying and False for retrying to send the message.
	def _sendMessage(self, data):

		logging.debug("[%s] Sending sensorAlert message."
				% self.fileName)

		prefixedChannel = self._generatePrefixedChannel(self.username,
			self.channel)

		finalData = {"username": self.username,
			"password": self.password,
			"channel": prefixedChannel,
			"data": data,
			"version": self.protocolVersion}

		# Send message to push server.
		responseStr = None
		try:

			logging.info("[%s] Sending message for sensorAlert to server '%s'."
				% (self.fileName, self.pushServerAddress))

			client = Client(self.pushServerAddress,
				self.pushServerPort, self.pushServerCert)
			client.connect()
			client.send(json.dumps(finalData))
			responseStr = client.recv(BUFSIZE)

		except Exception as e:
			logging.exception("[%s]: Unable to send message for "
				% self.fileName
				+ "sensorAlert to server '%s'."
				% self.pushServerAddress)

			# Return False in order to retry again to send the message.
			return False

		logging.debug("[%s] Received response: '%s'."
				% (self.fileName, responseStr))

		response = None
		try:
			response = json.loads(responseStr)
			if not "Code" in response.keys():
				raise ValueError("Response does not have key 'Code'")

		except Exception as e:
			logging.exception("[%s]: Received illegal message from server "
				% self.fileName
				+ "'%s' with content: '%s'."
				% self.pushServerAddress, responseStr)

			# Return True in order to NOT retry to send the message.
			return True

		if response["Code"] == ErrorCodes.NO_ERROR:

			logging.info("[%s]: Message for sensorAlert successfully "
				% self.fileName
				+ "transmitted.")
			return True

		elif response["Code"] in self.retryCodes:

			logging.error("[%s]: Received error code %d. "
				% (self.fileName, response["Code"])
				+ "We retry to send the message.")
			return False

		elif response["Code"] in self.notRetryCodes:

			logging.error("[%s]: Received error code %d. "
				% (self.fileName, response["Code"])
				+ "We do not retry to send the message.")
			return True

		logging.error("[%s]: Received unknown error code %d. "
			% (self.fileName, response["Code"])
			+ "We do not retry to send the message.")

		# If we reach this point, we have an unknown case and we do not attempt
		# to resend the message.
		return True


	# Truncates the message and subject to fit in a notification message.
	def _truncToSize(self, subject, message):
		lenJsonSbj = len(json.dumps(subject))
		lenSbj = len(subject)
		lenJsonMsg = len(json.dumps(message))
		lenMsg = len(message)

		# Consider json encoding (characters like \n need two characters).
		if (lenJsonSbj + lenJsonMsg) > self.sbjMsgSize:
			numberToRemove = (lenJsonSbj + lenJsonMsg + 7) - self.sbjMsgSize
			if lenMsg > numberToRemove:
				message = message[0:(lenMsg-numberToRemove)]
				message += "*TRUNC*"
			elif lenSbj > numberToRemove:
				subject = subject[0:(lenSbj-numberToRemove)]
				subject += "*TRUNC*"
			else:
				message = "*TRUNC*"
				numberToRemove = numberToRemove - lenMsg + 7
				subject = subject[0:(lenSbj-numberToRemove)]
				subject += "*TRUNC*"

		return subject, message


	# this function is called once when the alert client has connected itself
	# to the server (should be use to initialize everything that is needed
	# for the alert)
	def initializeAlert(self):

		# set the state of the alert to "not triggered"
		self.triggered = False

		# Create an encryption key from the secret.
		sha256 = hashlib.sha256()
		sha256.update(self.encSecret)
		self.key = sha256.digest()

		with open(self.templateFile, 'r') as fp:
			self.msgText = fp.read()


	def triggerAlert(self, sensorAlert):

		tempMsg = self._replaceWildcards(sensorAlert, self.msgText)
		tempSbj = self._replaceWildcards(sensorAlert, self.subject)
		oldSize = len(tempMsg) + len(tempSbj)
		tempSbj, tempMsg = self._truncToSize(tempSbj, tempMsg)
		newSize = len(tempMsg) + len(tempSbj)

		if oldSize != newSize:
			logging.info("[%s] Truncated message size from %d to %d."
				% (self.fileName, oldSize, newSize))

		# Send message to push server.
		while True:

			# Create payload for the message.
			payload = json.dumps( {
				"sbj": tempSbj, # Subject
				"msg": tempMsg, # Message
				"tt": sensorAlert.timeReceived, # Time Triggered
				"ts": int(time.time()), # Time Sent
				"is_sa": True, # Is SensorAlert
				"st": sensorAlert.state # State
				} )

			preparedPayload = self._prepareMessage(payload)

			if self._sendMessage(preparedPayload):
				break

			logging.info("[%s] Retrying to send notification to channel '%s' "
					% (self.fileName, self.channel)
					+ "in %d seconds."
					% self.pushRetryTimeout)

			time.sleep(self.pushRetryTimeout)


	def stopAlert(self, sensorAlert):
		pass


# this class is used to trigger or stop an alert
# in an own thread to not block the initiating thread
class AsynchronousAlertExecuter(threading.Thread):

	def __init__(self, alert):
		threading.Thread.__init__(self)

		self.fileName = os.path.basename(__file__)
		self.alert = alert

		# this option is used when the thread should
		# trigger an alert
		self.triggerAlert = False

		# this option is used when the thread should
		# stop an alert
		self.stopAlert = False

		# this options are used to transfer data from the received
		# sensor alert to the alert that is triggered
		self.sensorAlert = None


	def run(self):

		# check if an alert should be triggered
		if self.triggerAlert:
			self.alert.triggerAlert(self.sensorAlert)

		# check if an alert should be stopped
		elif self.stopAlert:
			self.alert.stopAlert(self.sensorAlert)