#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import RPi.GPIO as GPIO
import time
import random
import os
import logging
from client import AsynchronousSender
from localObjects import SensorDataType


# internal class that holds the important attributes
# for a sensor to work with (this class must be inherited from the
# used sensor class)
class _PollingSensor:

	def __init__(self):
		self.id = None
		self.description = None
		self.alertDelay = None
		self.state = None
		self.alertLevels = list()
		self.triggerAlert = None
		self.triggerAlertNormal = None
		self.triggerState = None
		self.dataTransfer = False
		self.data = None
		self.sensorDataType = None
		self.sensorData = None
		self.changeState = None


	# this function returns the current state of the sensor
	def getState(self):
		raise NotImplementedError("Function not implemented yet.")


	# this function updates the state variable of the sensor
	def updateState(self):
		raise NotImplementedError("Function not implemented yet.")


	# this function initializes the sensor
	def initializeSensor(self):
		raise NotImplementedError("Function not implemented yet.")


# class that controls one sensor at a gpio pin of the raspberry pi
class RaspberryPiGPIOPollingSensor(_PollingSensor):

	def __init__(self):
		_PollingSensor.__init__(self)

		# Set sensor to not hold any data.
		self.sensorDataType = SensorDataType.NONE

		# the gpio pin number (NOTE: python uses the actual
		# pin number and not the gpio number)
		self.gpioPin = None


	def initializeSensor(self):
		self.changeState = True

		# configure gpio pin and get initial state
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.gpioPin, GPIO.IN)
		self.state = GPIO.input(self.gpioPin)


	def getState(self):
		return self.state


	def updateState(self):
		# read current state of the gpio
		self.state = GPIO.input(self.gpioPin)


# class that uses edge detection to check a gpio pin of the raspberry pi
class RaspberryPiGPIOInterruptSensor(_PollingSensor):

	def __init__(self):
		_PollingSensor.__init__(self)
		self.fileName = os.path.basename(__file__)

		# Set sensor to not hold any data.
		self.sensorDataType = SensorDataType.NONE

		# the gpio pin number (NOTE: python uses the actual
		# pin number and not the gpio number)
		self.gpioPin = None

		# time that has to go by between two triggers
		self.delayBetweenTriggers = None

		# time a sensor is seen as triggered
		self.timeSensorTriggered = None

		# the last time the sensor was triggered
		self.lastTimeTriggered = 0.0

		# the configured edge detection
		self.edge = None

		# the count of interrupts that has to occur before
		# an alert is triggered
		# this is used to relax the edge detection a little bit
		# for example an interrupt is triggered when an falling/rising 
		# edge is detected, if your wiring is not good enough isolated
		# it can happen that electro magnetic radiation (because of
		# a starting vacuum cleaner for example) causes a falling/rising edge
		# this option abuses the bouncing of the wiring, this means
		# that the radiation for example only triggers one rising/falling
		# edge and your normal wiring could cause like four detected edges
		# when it is triggered because of the signal bouncing
		# so you could use this circumstance to determine correct triggers
		# from false triggers by setting a threshold of edges that have
		# to be reached before an alert is executed
		self.edgeCountBeforeTrigger = 0
		self.edgeCounter = 0

		# configures if the gpio input is pulled up or down
		self.pulledUpOrDown = None

		# used as internal state set by the interrupt callback
		self._internalState = None


	def _interruptCallback(self, gpioPin):

		# check if the last time the sensor was triggered is longer ago
		# than the configured delay between two triggers
		# => set time and reset edge counter
		if (time.time() - self.lastTimeTriggered) > self.delayBetweenTriggers:

			self.edgeCounter = 1
			self.lastTimeTriggered = time.time()

		else:

			# increment edge counter
			self.edgeCounter += 1

			# if edge counter reaches threshold
			# => trigger state
			if self.edgeCounter >= self.edgeCountBeforeTrigger:
				self._internalState = self.triggerState

				logging.debug("[%s]: " % self.fileName
							+ "Sensor '%s' triggered." % self.description)

		logging.debug("[%s]: %d Interrupt " % (self.fileName, self.edgeCounter)
							+ "for sensor '%s' triggered." % self.description)


	def initializeSensor(self):
		self.changeState = True

		# get the value for the setting if the gpio is pulled up or down
		if self.pulledUpOrDown == 0:
			pulledUpOrDown = GPIO.PUD_DOWN
		elif self.pulledUpOrDown == 1:
			pulledUpOrDown = GPIO.PUD_UP
		else:
			raise ValueError("Value for pulled up or down setting not known.")

		# configure gpio pin and get initial state
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.gpioPin, GPIO.IN, pull_up_down=pulledUpOrDown)

		# set initial state to not triggered
		self.state = 1 - self.triggerState
		self._internalState = 1 - self.triggerState

		# set edge detection
		if self.edge == 0:
			GPIO.add_event_detect(self.gpioPin, GPIO.FALLING,
			callback=self._interruptCallback)
		elif self.edge == 1:
			GPIO.add_event_detect(self.gpioPin, GPIO.RISING,
			callback=self._interruptCallback)
		else:
			raise ValueError("Value for edge detection not known.")


	def getState(self):
		return self.state


	def updateState(self):
		# check if the sensor is triggered and if it is longer
		# triggered than configured => set internal state to normal
		if (self.state == self.triggerState
			and ((time.time() - self.lastTimeTriggered)
			> self.timeSensorTriggered)):
			self._internalState = 1 - self.triggerState

		# update state to internal state
		self.state = self._internalState


# this class polls the sensor states and triggers alerts and state changes
class SensorExecuter:

	def __init__(self, globalData):
		self.fileName = os.path.basename(__file__)
		self.globalData = globalData
		self.connection = self.globalData.serverComm
		self.sensors = self.globalData.sensors

		# Flag indicates if the thread is initialized.
		self._isInitialized = False


	def isInitialized(self):
		return self._isInitialized


	def execute(self):

		# time on which the last full sensor states were sent
		# to the server
		lastFullStateSent = 0

		# Get reference to server communication object.
		while self.connection is None:
			time.sleep(0.5)
			self.connection = self.globalData.serverComm

		self._isInitialized = True

		while True:

			# check if the client is connected to the server
			# => wait and continue loop until client is connected
			if not self.connection.isConnected():
				time.sleep(0.5)
				continue

			# poll all sensors and check their states
			for sensor in self.sensors:

				oldState = sensor.getState()
				sensor.updateState()
				currentState = sensor.getState()

				# check if the current state is the same
				# than the already known state => continue
				if oldState == currentState:
					continue

				# check if the current state is an alert triggering state
				elif currentState == sensor.triggerState:

					# check if the sensor triggers a sensor alert
					# => send sensor alert to server
					if sensor.triggerAlert:

						logging.info("[%s]: Sensor alert " % self.fileName
							+ "triggered by '%s'." % sensor.description)

						asyncSenderProcess = AsynchronousSender(
							self.connection, self.globalData)
						# set thread to daemon
						# => threads terminates when main thread terminates	
						asyncSenderProcess.daemon = True
						asyncSenderProcess.sendSensorAlert = True
						asyncSenderProcess.sendSensorAlertSensor = sensor
						asyncSenderProcess.start()

					# if sensor does not trigger sensor alert
					# => just send changed state to server
					else:

						logging.debug("[%s]: State " % self.fileName
							+ "changed by '%s'." % sensor.description)

						asyncSenderProcess = AsynchronousSender(
							self.connection, self.globalData)
						# set thread to daemon
						# => threads terminates when main thread terminates	
						asyncSenderProcess.daemon = True
						asyncSenderProcess.sendStateChange = True
						asyncSenderProcess.sendStateChangeSensor = sensor
						asyncSenderProcess.start()

				# only possible situation left => sensor changed
				# back from triggering state to a normal state
				else:

					# check if the sensor triggers a sensor alert when
					# state is back to normal
					# => send sensor alert to server
					if sensor.triggerAlertNormal:

						logging.info("[%s]: Sensor alert " % self.fileName
							+ "for back to normal state "
							+ "triggered by '%s'." % sensor.description)

						asyncSenderProcess = AsynchronousSender(
							self.connection, self.globalData)
						# set thread to daemon
						# => threads terminates when main thread terminates	
						asyncSenderProcess.daemon = True
						asyncSenderProcess.sendSensorAlert = True
						asyncSenderProcess.sendSensorAlertSensor = sensor
						asyncSenderProcess.start()

					# if sensor does not trigger sensor alert when
					# state is back to normal
					# => just send changed state to server
					else:

						logging.debug("[%s]: State " % self.fileName
							+ "changed by '%s'." % sensor.description)

						asyncSenderProcess = AsynchronousSender(
							self.connection, self.globalData)
						# set thread to daemon
						# => threads terminates when main thread terminates	
						asyncSenderProcess.daemon = True
						asyncSenderProcess.sendStateChange = True
						asyncSenderProcess.sendStateChangeSensor = sensor
						asyncSenderProcess.start()
				
			# check if the last state that was sent to the server
			# is older than 60 seconds => send state update
			if (time.time() - lastFullStateSent) > 60:

				logging.debug("[%s]: Last state " % self.fileName
					+ "timed out.")

				asyncSenderProcess = AsynchronousSender(
					self.connection, self.globalData)
				# set thread to daemon
				# => threads terminates when main thread terminates	
				asyncSenderProcess.daemon = True
				asyncSenderProcess.sendSensorsState = True
				asyncSenderProcess.start()

				# update time on which the full state update was sent
				lastFullStateSent = time.time()
				
			time.sleep(0.5)