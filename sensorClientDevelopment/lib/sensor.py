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
from client import AsynchronousSender
import threading


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


	# this function returns the current state of the sensor
	def getState(self):
		raise NotImplementedError("Function not implemented yet.")


	# this function updates the state variable of the sensor
	def updateState(self):
		raise NotImplementedError("Function not implemented yet.")


	# this function initializes the sensor
	def initializeSensor(self):
		raise NotImplementedError("Function not implemented yet.")


# class that represents one emulated sensor that can be triggered via keyboard
class SensorDev(_PollingSensor):

	def __init__(self):
		_PollingSensor.__init__(self)

		# used for logging
		self.fileName = os.path.basename(__file__)

		self.consoleInputState = 1

	def initializeSensor(self):
		self.state = self.consoleInputState


	def getState(self):
		return self.state


	def updateState(self):
		self.state = self.consoleInputState


	def toggleConsoleState(self):
		if self.consoleInputState == 0:
			self.consoleInputState = 1
		else:
			self.consoleInputState = 0


# this class polls the sensor states and triggers alerts and state changes
class SensorExecuter(threading.Thread):

	def __init__(self, connection, globalData):
		threading.Thread.__init__(self)
		self.fileName = os.path.basename(__file__)
		self.connection = connection
		self.sensors = globalData.sensors
		self.globalData = globalData


	def run(self):

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