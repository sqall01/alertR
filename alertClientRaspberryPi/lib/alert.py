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

		# File nme of this file (used for logging).
		self.fileName = os.path.basename(__file__)

		# this flag is used to signalize if the alert is triggered or not
		self.triggered = None

		# the gpio pin number (NOTE: python uses the actual
		# pin number and not the gpio number)
		self.gpioPin = None
		self.gpioPinLock = threading.Lock()

		# the state the gpio pin is set to when no alert is triggered
		self.gpioPinStateNormal = None

		# the state the gpio pin is set to when the alert is triggered
		self.gpioPinStateTriggered = None

		# Time in seconds the gpio pin is reseted to the normal state
		# after it was triggered (if set to 0 this feature is deactivated).
		self.gpioResetStateTime = 0
		self.gpioResetStateThread = None
		self.gpioResetStateThreadStop = False
		self.gpioResetStateThreadLock = threading.Lock()


	# Internal function that sets alert state.
	def _setState(self, state):

		self.gpioPinLock.acquire()

		if state and not self.triggered:
			self.triggered = True
			GPIO.output(self.gpioPin, self.gpioPinStateTriggered)
		elif not state and self.triggered:
			self.triggered = False
			GPIO.output(self.gpioPin, self.gpioPinStateNormal)

		self.gpioPinLock.release()


	# Internal function that resets the state after wating the reset time.
	def _resetPin(self):

		# Wait until the reset time was reached.
		endTime = int(time.time()) + self.gpioResetStateTime
		while int(time.time()) < endTime:
			time.sleep(1)

			self.gpioPinLock.acquire()
			state = self.triggered
			self.gpioPinLock.release()

			self.gpioResetStateThreadLock.acquire()
			stopThread = self.gpioResetStateThreadStop
			self.gpioResetStateThreadLock.release()

			# Stop thread if the alert is not triggered anymore or
			# if we were asked to stop.
			if not state or stopThread:
				self.gpioResetStateThreadLock.acquire()
				self.gpioResetStateThread = None
				self.gpioResetStateThreadStop = False
				self.gpioResetStateThreadLock.release()
				return

		logging.info("[%s]: Resetting alert with id %d to normal state "
			% (self.fileName, self.id)
			+ "after %d seconds."
			% self.gpioResetStateTime)

		self._setState(False)

		self.gpioResetStateThreadLock.acquire()
		self.gpioResetStateThread = None
		self.gpioResetStateThreadStop = False
		self.gpioResetStateThreadLock.release()


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

		self.gpioPinLock.acquire()
		state = self.triggered
		self.gpioPinLock.release()

		# only execute if not triggered
		if not state:
			self._setState(True)

			# Start thread to reset gpio pin.
			if self.gpioResetStateTime > 0:
				self.gpioResetStateThreadLock.acquire()

				# Ask already running thread to stop (if exists).
				if self.gpioResetStateThread is not None:
					self.gpioResetStateThreadStop = True

				# Start new thread to reset pin after given time.
				self.gpioResetStateThread = threading.Thread(
					target=self._resetPin)
				self.gpioResetStateThread.start()

				self.gpioResetStateThreadLock.release()


	# this function is called when the alert is stopped
	def stopAlert(self, sensorAlert):

		self.gpioPinLock.acquire()
		state = self.triggered
		self.gpioPinLock.release()

		# only execute if the alert was triggered
		if state:
			self._setState(False)


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