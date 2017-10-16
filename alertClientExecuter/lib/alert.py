#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import random
import os
import logging
import threading
import subprocess


# internal class that holds the important attributes
# for a alert to work with (this class must be inherited from the
# used alert class)
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


# class that executes an command when an alert is triggered or all alerts
# are stopped
class ExecuterAlert(_Alert):

	def __init__(self):
		_Alert.__init__(self)

		# used for logging
		self.fileName = os.path.basename(__file__)

		# the command to execute and the arguments to pass when
		# an alert is triggered
		self.triggerExecute = list()

		# the command to execute and the arguments to pass when
		# an alert is stopped
		self.stopExecute = list()


	# this function is called once when the alert client has connected itself
	# to the server (should be use to initialize everything that is needed
	# for the alert)
	def initializeAlert(self):
		pass


	# this function is called when this alert is triggered
	def triggerAlert(self, sensorAlert):

		logging.debug("[%s]: Executing process " % self.fileName
			+ "'%s' with trigger arguments." % self.description)
		try:
			subprocess.Popen(self.triggerExecute, close_fds=True)
		except Exception as e:
			logging.exception("[%s]: Executing process " % self.fileName
				+ "'%s' with trigger arguments failed." % self.description)
		

	# this function is called when the alert is stopped
	def stopAlert(self, sensorAlert):

		logging.debug("[%s]: Executing process " % self.fileName
			+ "'%s' with stop arguments." % self.description)
		try:
			subprocess.Popen(self.stopExecute, close_fds=True)
		except Exception as e:
			logging.exception("[%s]: Executing process " % self.fileName
				+ "'%s' with stop arguments failed." % self.description)


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