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


# internal class that holds the important attributes
# for a sensor to work with (this class must be inherited from the
# used sensor class)
class _PollingSensor:

	def __init__(self):
		self.id = None
		self.description = None
		self.alertDelay = None
		self.state = None
		self.alertLevel = None
		self.triggerAlert = None
		self.triggerAlways = None
		self.triggerState = None


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

		# the gpio pin number (NOTE: python uses the actual
		# pin number and not the gpio number)
		self.gpioPin = None


	def initializeSensor(self):
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

		# used as internal state set by the interrupt callback
		self._internalState = None


	def _interruptCallback(self, gpioPin):

		logging.debug("[%s]: Interrupt " % self.fileName
							+ "for sensor '%s' triggered." % self.description)

		# check if the last time the sensor was triggered is longer ago
		# than the configured delay between two triggers
		# => trigger internal state
		if (time.time() - self.lastTimeTriggered) > self.delayBetweenTriggers:
			self.lastTimeTriggered = time.time()
			self._internalState = self.triggerState


	def initializeSensor(self):
		# configure gpio pin and get initial state
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.gpioPin, GPIO.IN)

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

	def __init__(self, connection, globalData):
		self.fileName = os.path.basename(__file__)
		self.connection = connection
		self.sensors = globalData.sensors
		self.globalData = globalData


	def execute(self):

		# initialize all sensors
		for sensor in self.sensors:
			sensor.initializeSensor()

		# time on which the last full sensor states were sent
		# to the server
		lastFullStateSent = 0

		while(1):

			# check if the client is connected to the server
			# => wait and continue loop until client is connected
			if not self.connection.isConnected:
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