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
import re
from client import AsynchronousSender
from localObjects import SensorDataType


# Internal class that holds the important attributes
# for a sensor to work (this class must be inherited from the
# used sensor class).
class _PollingSensor:

	def __init__(self):

		# Id of this sensor on this client. Will be handled as
		# "remoteSensorId" by the server.
		self.id = None

		# Description of this sensor.
		self.description = None

		# Delay in seconds this sensor has before a sensor alert is
		# issued by the server.
		self.alertDelay = None

		# Local state of the sensor (either 1 or 0). This state is translated
		# (with the help of "triggerState") into 1 = "triggered" / 0 = "normal"
		# when it is send to the server.
		self.state = None

		# State the sensor counts as triggered (either 1 or 0).
		self.triggerState = None

		# A list of alert levels this sensor belongs to.
		self.alertLevels = list()

		# Flag that indicates if this sensor should trigger a sensor alert
		# for the state "triggered" (true or false).
		self.triggerAlert = None

		# Flag that indicates if this sensor should trigger a sensor alert
		# for the state "normal" (true or false).
		self.triggerAlertNormal = None

		# The type of data the sensor holds (i.e., none at all, integer, ...).
		# Type is given by the enum class "SensorDataType".
		self.sensorDataType = None

		# The actual data the sensor holds.
		self.sensorData = None

		# Flag indicates if this sensor alert also holds
		# the data the sensor has. For example, the data send
		# with this alarm message could be the data that triggered
		# the alarm, but not necessarily the data the sensor
		# currently holds. Therefore, this flag indicates
		# if the data contained by this message is also the
		# current data of the sensor and can be used for example
		# to update the data the sensor has.
		self.hasLatestData = None

		# Flag that indicates if a sensor alert that is send to the server
		# should also change the state of the sensor accordingly. This flag
		# can be useful if the sensor watches multiple entities. For example,
		# a timeout sensor could watch multiple hosts and has the state
		# "triggered" when at least one host has timed out. When one host
		# connects back and still at least one host is timed out,
		# the sensor can still issue a sensor alert for the "normal"
		# state of the host that connected back, but the sensor
		# can still has the state "triggered".
		self.changeState = None

		# Optional data that can be transfered when a sensor alert is issued.
		self.hasOptionalData = False
		self.optionalData = None


	# this function returns the current state of the sensor
	def getState(self):
		raise NotImplementedError("Function not implemented yet.")


	# this function updates the state variable of the sensor
	def updateState(self):
		raise NotImplementedError("Function not implemented yet.")


	# This function initializes the sensor.
	#
	# Returns True or False depending on the success of the initialization.
	def initializeSensor(self):
		raise NotImplementedError("Function not implemented yet.")


	# This function decides if an update for this sensor should be sent
	# to the server. It is checked regularly and can be used to force an update
	# of the state and data of this sensor to be sent to the server.
	#
	# Returns True or False according on whether an update should be sent.
	def forceSendState(self):
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
		self.hasLatestData = False
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


	def forceSendState(self):
		return False


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
		self.hasLatestData = False
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


	def forceSendState(self):
		return False


# Class that reads one DS18b20 sensor connected to the Raspberry Pi.
class RaspberryPiDS18b20Sensor(_PollingSensor):

	def __init__(self):
		_PollingSensor.__init__(self)

		# Used for logging.
		self.fileName = os.path.basename(__file__)

		# Set sensor to hold float data.
		self.sensorDataType = SensorDataType.FLOAT

		# The file of the sensor that should be parsed.
		self.sensorFile = None

		# The name of the sensor that should be parsed.
		self.sensorName = None

		# The interval in seconds in which an update of the current held data
		# should be sent to the server.
		self.interval = None

		# The time the last update of the data was sent to the server.
		self.lastUpdate = None


	# Internal function that reads the data of the sensor and returns it
	# as a float number or None, if it fails.
	def _getData(self):

		try:
			with open(self.sensorFile, 'r') as fp:

				# File content looks like this:
				# 2d 00 4b 46 ff ff 04 10 b3 : crc=b3 YES
				# 2d 00 4b 46 ff ff 04 10 b3 t=22500
				fp.readline()
				line = fp.readline()

				reMatch = re.match("([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line)
				if reMatch:
					return float(reMatch.group(2)) / 1000

				else:
					logging.error("[%s]: Could not parse sensor file."
						% self.fileName)

		except Exception as e:
			logging.exception("[%s]: Could not read sensor file."
				% self.fileName)

		return None


	def initializeSensor(self):
		self.hasLatestData = True
		self.changeState = True

		self.state = 1 - self.triggerState

		self.sensorFile = "/sys/bus/w1/devices/" \
			+ self.sensorName \
			+ "/w1_slave"

		self.sensorData = self._getData()
		if not self.sensorData:
			return False

		self.lastUpdate = int(time.time())

		return True


	def getState(self):
		return self.state


	def updateState(self):

		# Update temperature data of sensor.
		temp = self._getData()
		if not temp:
			logging.error("[%s]: Could not get data from sensor file."
				% self.fileName)
		self.sensorData = temp

		logging.debug("[%s]: Current temperature of sensor '%s': %.3f."
			% (self.fileName, self.description, self.sensorData))


	def forceSendState(self):
		if (int(time.time()) - self.lastUpdate) > self.interval:
			self.lastUpdate = int(time.time())
			return True
		return False


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
			
			# Poll all sensors if they want to force an update that should
			# be send to the server.
			for sensor in self.sensors:

				if sensor.forceSendState():
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