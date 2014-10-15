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
import dbus


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


# this class represents an alert that sends notifications via dbus
# to the freedesktop notification system
class DbusAlert(_Alert):

	def __init__(self):
		_Alert.__init__(self)

		self.fileName = os.path.basename(__file__)

		# these values are used to check when the alert was triggered
		# the last time and if it should trigger again
		self.triggered = None
		self.triggerDelay = None

		# message notification
		self.displayTime = None


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

			icon = "dialog-information"
			title = "alertR"
			appName = "alertR alertClientDbus"
			replacesId = 0 # not needed, every notification stands for its own
			tempMessage = "\"" \
						+ asyncAlertExecInstance.sensorDescription \
						+ "\" just triggered."

			# send notification via dbus to notification system
			try:
				busName = 'org.freedesktop.Notifications'
				objectPath = '/org/freedesktop/Notifications'
				sessionBus = dbus.SessionBus()
				dbusObject = sessionBus.get_object(busName, objectPath)
				interface = dbus.Interface(dbusObject, busName)
				interface.Notify(appName, replacesId, icon,
					title, tempMessage, [], [], self.displayTime)
			except Exception as e:
				logging.exception("[%s]: Could not send notification via dbus."
					% self.fileName)

				return


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


	def run(self):

		# check if an alert should be triggered
		if self.triggerAlert:
			self.alert.triggerAlert(self)

		# check if an alert should be stopped
		elif self.stopAlert:
			self.alert.stopAlert(self)