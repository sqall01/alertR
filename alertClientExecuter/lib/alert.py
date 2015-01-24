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








class ExecuterAlert(_Alert):

	def __init__(self):
		_Alert.__init__(self)

		# gives the command/path that should be executed
		self.execute = None

		# gives the argument that is used for the command when the alert is
		# triggered
		self.triggerArgument = None # TODO better to use a list of arguments

		# gives the argument that is used for the command when the alert is
		# stopped
		self.stopArgument = None # TODO better to use a list of arguments


	# this function is called once when the alert client has connected itself
	# to the server (should be use to initialize everything that is needed
	# for the alert)
	def initializeAlert(self):
		pass


	# this function is called when this alert is triggered
	def triggerAlert(self, asyncAlertExecInstance):

		logging.debug("[%s]: Executing process " % self.fileName
			+ "'%s' with trigger arguments." % self.description)
		subprocess.Popen([self.execute, str(self.triggerArgument)],
			close_fds=True)
		

	# this function is called when the alert is stopped
	def stopAlert(self, asyncAlertExecInstance):

		logging.debug("[%s]: Executing process " % self.fileName
			+ "'%s' with stop arguments." % self.description)
		subprocess.Popen([self.execute, str(self.stopArgument)],
			close_fds=True)








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