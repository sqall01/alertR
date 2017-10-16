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
import RPi.GPIO as GPIO


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


# this function represents an alert that sets the Raspberry Pi GPIO to high
# or low if triggered
class RaspberryPiGPIOAlert(_Alert):

	def __init__(self):
		_Alert.__init__(self)

		# this flag is used to signalize if the alert is triggered or not
		self.triggered = None

		# the gpio pin number (NOTE: python uses the actual
		# pin number and not the gpio number)
		self.gpioPin = None

		# the state the gpio pin is set to when no alert is triggered
		self.gpioPinStateNormal = None

		# the state the gpio pin is set to when the alert is triggered
		self.gpioPinStateTriggered = None


	# this function is called once when the alert client has connected itself
	# to the server
	def initializeAlert(self):

		# set the state of the alert to "not triggered"
		self.triggered = False

		# configure gpio pin and set initial state
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.gpioPin, GPIO.OUT)
		GPIO.output(self.gpioPin, self.gpioPinStateNormal)


	# this function is called when this alert is triggered
	def triggerAlert(self, sensorAlert):

		# only execute if not triggered
		if not self.triggered:

			# set state of alert to "triggered"
			self.triggered = True

			# set gpio pin to state when an alert is triggered
			GPIO.output(self.gpioPin, self.gpioPinStateTriggered)


	# this function is called when the alert is stopped
	def stopAlert(self, sensorAlert):

		# only execute if the alert was triggered
		if self.triggered:

			# set state of alert to "not triggered"
			self.triggered = False

			# set gpio pin to state when no alert is triggered
			GPIO.output(self.gpioPin, self.gpioPinStateNormal)


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