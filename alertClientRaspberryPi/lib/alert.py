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
import RPi.GPIO as GPIO


# internal class that holds the important attributes
# for a alert to work with (this class must be inherited from the
# used alert class)
class _Alert:

	def __init__(self):
		self.id = None
		self.description = None
		self.alertLevels = list()


	def triggerAlert(self):
		raise NotImplementedError("Function not implemented yet.")


	def stopAlert(self):
		raise NotImplementedError("Function not implemented yet.")


	def initializeAlert(self):
		raise NotImplementedError("Function not implemented yet.")


# this function represents an example alert
# (for example a GPIO on a Raspberry Pi which should be set to high 
# or code that executes an external command)
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
	# to the server (should be use to initialize everything that is needed
	# for the alert)
	def initializeAlert(self):

		# set the state of the alert to "not triggered"
		self.triggered = False

		# configure gpio pin and set initial state
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.gpioPin, GPIO.OUT)
		GPIO.output(self.gpioPin, self.gpioPinStateNormal)

	def triggerAlert(self):

		# only execute if not triggered
		if not self.triggered:

			# set state of alert to "triggered"
			self.triggered = True

			# set gpio pin to state when an alert is triggered
			GPIO.output(self.gpioPin, self.gpioPinStateTriggered)


	def stopAlert(self):

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


	def run(self):

		# check if an alert should be triggered
		if self.triggerAlert:
			self.alert.triggerAlert()

		# check if an alert should be stopped
		elif self.stopAlert:
			self.alert.stopAlert()