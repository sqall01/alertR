#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import time
import random
import os
import logging
import threading
from thirdparty import xbmcjson


# internal class that holds the important attributes
# for a alert to work with (this class must be inherited from the
# used alert class)
class _Alert:

	def __init__(self):
		self.id = None
		self.description = None
		self.alertLevels = list()


	def triggerAlert(self, asyncAlertExecInstance):
		raise NotImplementedError("Function not implemented yet.")


	def stopAlert(self, asyncAlertExecInstance):
		raise NotImplementedError("Function not implemented yet.")


	def initializeAlert(self):
		raise NotImplementedError("Function not implemented yet.")


# this function class an alert that controls a xbmc instance
# (for example shows a notification and pauses the player)
class XbmcAlert(_Alert):

	def __init__(self):
		_Alert.__init__(self)

		self.fileName = os.path.basename(__file__)

		# these values are used to check when the alert was triggered
		# the last time and if it should trigger again
		self.triggered = None
		self.triggerDelay = None

		# host and port of the xbmc instance
		self.host = None
		self.port = None
		
		# message notification
		self.showMessage = None
		self.displayTime = None

		# display a received message (if any was received)
		self.displayReceivedMessage = None

		# should the player be paused
		self.pausePlayer = None


	# this function is called once when the alert client has connected itself
	# to the server
	def initializeAlert(self):

		# set the time of the trigger
		self.triggered = 0.0


	# this function is called when this alert is triggered
	def triggerAlert(self, asyncAlertExecInstance):

		# only execute if the last triggered alert was more than
		# the configured trigger delay ago
		if (time.time() - self.triggered) > self.triggerDelay:

			# set the time the alert was triggered
			self.triggered = time.time()

			# extract the received message if it was received and should be
			# displayed
			receivedMessage = None
			if (self.displayReceivedMessage
				and asyncAlertExecInstance.dataTransfer):

				if ("message" in asyncAlertExecInstance.data):
					receivedMessage = asyncAlertExecInstance.data["message"]

			# connect to the xbmc json rpc service
			try:
				xbmcInstance = xbmcjson.XBMC("http://" + self.host
					+ ":" + str(self.port) + "/jsonrpc")
			except Exception as e:
				logging.exception("[%s]: Not able to connect to XBMC instance."
					% self.fileName)

				return

			# ping the xbmc instance
			try:
				response = xbmcInstance.JSONRPC.Ping()
			except Exception as e:
				logging.exception("[%s]: Not able to ping XBMC instance."
					% self.fileName)

				return

			# check if xbmc instance respond
			if (not response is None 
				and response["result"] == "pong"):

				# get player id of the player instance that plays audio/video
				playerId = None
				response = xbmcInstance.Player.GetActivePlayers()
				for i in range(len(response["result"])):
					if (response["result"][i]["type"] == "audio"
						or response["result"][i]["type"] == "video"):
						playerId = response["result"][i]["playerid"]

				# if audio/video is played => pause it if configured
				if (not playerId is None
					and self.pausePlayer is True):
					xbmcInstance.Player.PlayPause(playerid=playerId,
						play=False)

				# show a message on the display if configured
				if self.showMessage is True:

					# differentiate between a generic displayed notification
					# and a notification which also shows the received message
					if receivedMessage is None:
						tempMessage = "\"" \
							+ asyncAlertExecInstance.sensorDescription \
							+ "\" just triggered."
					else:
						tempMessage = "\"" \
							+ asyncAlertExecInstance.sensorDescription \
							+ "\" just triggered. Received message: \"" \
							+ receivedMessage \
							+ "\""

					xbmcInstance.GUI.ShowNotification(title="alertR",
						message=tempMessage, displaytime=self.displayTime)

			else:
				logging.error("[%s]: XBMC does not respond."
					% self.fileName)


	# this function is called when the alert is stopped
	def stopAlert(self, asyncAlertExecInstance):
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
		self.sensorDescription = None
		self.dataTransfer = False # true or false
		self.data = None # only evaluated if data transfer is true


	def run(self):

		# check if an alert should be triggered
		if self.triggerAlert:
			self.alert.triggerAlert(self)

		# check if an alert should be stopped
		elif self.stopAlert:
			self.alert.stopAlert(self)