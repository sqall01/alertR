#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import os
import logging
import smtplib
import threading
import re
from lightweightpush import LightweightPush, ErrorCodes
from localObjects import SensorDataType


# Internal class that holds the important attributes
# for a alert to work with (this class must be inherited from the
# used alert class).
class _Alert(object):

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
		self.pushRetryTimeout = self.globalData.pushRetryTimeout
		self.pushRetries = self.globalData.pushRetries

		# These are the message settings.
		self._channel = None
		self.encSecret = None
		self.subject = None
		self.templateFile = None
		self.msgText = None
		self.username = None
		self.password = None
		self.push_service = None

		# Error codes to determine if we can retry to send the message or not.
		self.retryCodes = [
			ErrorCodes.DATABASE_ERROR,
			ErrorCodes.GOOGLE_CONNECTION,
			ErrorCodes.GOOGLE_UNKNOWN,
			ErrorCodes.GOOGLE_AUTH,
			ErrorCodes.CLIENT_CONNECTION_ERROR
			]


	@property
	def channel(self):
		return self._channel


	@channel.setter
	def channel(self, value):
		if bool(re.match(r'^[a-zA-Z0-9-_.~%]+$', value)):
			self._channel = value
		else:
			raise ValueError("Channel '%s' contains illegal characters."
				% value)


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
	def _sendMessage(self, subject, msg, sensorAlert):

		# Send message to push server.
		ctr = 0
		errorCode = ErrorCodes.NO_ERROR
		while True:

			ctr += 1

			logging.info("[%s] Sending message for sensorAlert to server."
				% self.fileName)

			errorCode = self.push_service.send_msg(subject,
				msg,
				self.channel,
				state=sensorAlert.state,
				time_triggered=sensorAlert.timeReceived,
				max_retries=1)

			if errorCode == ErrorCodes.NO_ERROR:
				logging.debug("[%s] Sending message successful."
					% self.fileName)
				break

			else:
				if errorCode == ErrorCodes.AUTH_ERROR:
					logging.error("[%s] Unable to authenticate at server. "
						% self.fileName
						+ " Please check your credentials.")

				elif errorCode == ErrorCodes.ILLEGAL_MSG_ERROR:
					logging.error("[%s] Server replies that message is "
						% self.fileName
						+ "malformed.")

				elif errorCode == ErrorCodes.VERSION_MISSMATCH:
					logging.error("[%s] Used version is no longer used. "
						% self.fileName
						+ "Please update your AlertR instance.")

				else:
					logging.error("[%s] Server responded with error '%d'."
						% (self.fileName, errorCode))

			# Only retry sending message if we can recover from error.
			if errorCode not in self.retryCodes:
				logging.error("[%s]: Do not retry to send message."
					% self.fileName)
				break

			if ctr > self.pushRetries:
				logging.error("[%s]: Tried to send message for %d times. "
					% (self.fileName, ctr)
					+ "Giving up.")
				break
			
			logging.info("[%s] Retrying to send notification to "
				% self.fileName
				+ "channel '%s' in %d seconds."
				% (self.channel, self.pushRetryTimeout))

			time.sleep(self.pushRetryTimeout)

		# Return last error code (used by the testPushConfiguration.py script).
		return errorCode


	# this function is called once when the alert client has connected itself
	# to the server (should be use to initialize everything that is needed
	# for the alert)
	def initializeAlert(self):

		# set the state of the alert to "not triggered"
		self.triggered = False

		with open(self.templateFile, 'r') as fp:
			self.msgText = fp.read()

		self.push_service = LightweightPush(self.username,
			self.password, self.encSecret)


	def triggerAlert(self, sensorAlert):

		tempMsg = self._replaceWildcards(sensorAlert, self.msgText)
		tempSbj = self._replaceWildcards(sensorAlert, self.subject)

		threading.Thread(target=self._sendMessage,
			args=(tempSbj, tempMsg, sensorAlert))


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