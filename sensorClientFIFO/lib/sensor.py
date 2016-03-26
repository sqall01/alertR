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
import json
import threading
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


	# this function initializes the sensor
	def initializeSensor(self):
		raise NotImplementedError("Function not implemented yet.")


# class that represents one FIFO sensor
class SensorFIFO(_PollingSensor, threading.Thread):

	def __init__(self):
		threading.Thread.__init__(self)
		_PollingSensor.__init__(self)

		# Set sensor to not hold any data.
		self.sensorDataType = SensorDataType.NONE

		# used for logging
		self.fileName = os.path.basename(__file__)

		self.fifoFile = None

		self.umask = None

		self.temporaryState = None


	def initializeSensor(self):
		self.changeState = True
		self.hasLatestData = False
		self.state = 1 - self.triggerState
		self.temporaryState = 1 - self.triggerState


	def getState(self):
		return self.state


	def updateState(self):
		self.state = self.temporaryState


	def run(self):

		while True:

			# check if FIFO file exists
			# => remove it if it does
			if os.path.exists(self.fifoFile):
				try:
					os.remove(self.fifoFile)
				except Exception as e:
					logging.exception("[%s]: Could not delete "
						% self.fileName
						+ "FIFO file of sensor with id '%d'."
						% self.id)
					time.sleep(10)
					continue

			# create a new FIFO file
			try:
				os.umask(self.umask)
				os.mkfifo(self.fifoFile)
			except Exception as e:
				logging.exception("[%s]: Could not create "
					% self.fileName
					+ "FIFO file of sensor with id '%d'."
					% self.id)
				time.sleep(10)
				continue

			# read FIFO for data
			data = ""
			try:
				fifo = open(self.fifoFile, "r")
				data = fifo.read()
				fifo.close()
			except Exception as e:
				logging.exception("[%s]: Could not read data from "
					% self.fileName
					+ "FIFO file of sensor with id '%d'."
					% self.id)
				time.sleep(10)
				continue

			logging.debug("[%s]: Received data '%s' from "
				% (self.fileName, data)
				+ "FIFO file of sensor with id '%d'."
				% self.id)

			# parse received data
			try:

				message = json.loads(data)

				# check if the received message is valid
				# => if it is parse it
				if str(message["message"]).upper() == "STATECHANGE":

					self.hasOptionalData = bool(
						message["payload"]["hasOptionalData"])

					# check if data should be transfered with the sensor alert
					# => if it should parse it
					if self.hasOptionalData:

						self.optionalData = message["payload"]["optionalData"]

						# check if data is of type dict
						if not isinstance(self.optionalData, dict):
							logging.warning("[%s]: Received optional data "
								% self.fileName
								+ "from FIFO file of sensor with id '%d' "
								% self.id
								+ "invalid. Ignoring data to transfer.")
							
							self.hasOptionalData = False
							self.optionalData = None

					# set the new state as temporary
					tempInputState = int(message["payload"]["state"])
					if (tempInputState != 0
						and tempInputState != 1):
						logging.warning("[%s]: Received state "
							% self.fileName
							+ "from FIFO file of sensor with id '%d' "
							% self.id
							+ "invalid. Ignoring state change.")
					else:
						self.temporaryState = tempInputState

				else:
					raise ValueError("Received unvalid message type.")

			except Exception as e:
				logging.exception("[%s]: Could not parse received data from "
					% self.fileName
					+ "FIFO file of sensor with id '%d'."
					% self.id)
				continue


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

		# initialize all sensors
		for sensor in self.sensors:
			sensor.initializeSensor()

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