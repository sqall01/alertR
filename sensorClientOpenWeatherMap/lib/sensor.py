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
import httplib
from client import AsynchronousSender
from localObjects import SensorDataType, SensorAlert, StateChange


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


	# This function decides if a sensor alert for this sensor should be sent
	# to the server. It is checked regularly and can be used to force
	# a sensor alert despite the state of the sensor has not changed.
	#
	# Returns an object of class SensorAlert if a sensor alert should be sent
	# or None.
	def forceSendAlert(self):
		raise NotImplementedError("Function not implemented yet.")


	# This function decides if an update for this sensor should be sent
	# to the server. It is checked regularly and can be used to force an update
	# of the state and data of this sensor to be sent to the server.
	#
	# Returns an object of class StateChange if a sensor alert should be sent
	# or None.
	def forceSendState(self):
		raise NotImplementedError("Function not implemented yet.")


# Class that controls one sensor for OpenWeatherMap
class OpenWeatherMapTempPollingSensor(_PollingSensor):

	def __init__(self):
		_PollingSensor.__init__(self)

		# Used for logging.
		self.fileName = os.path.basename(__file__)

		# Set sensor to hold float data.
		self.sensorDataType = SensorDataType.FLOAT

		self.lastUpdate = 0
		self.interval = 60
		self.host = "api.openweathermap.org"
		self.port = 80

		self._forceSendState = False


	def initializeSensor(self):
		self.hasLatestData = False
		self.changeState = False
		self.state = 1 - self.triggerState

		# Update data directly for the first time.
		self.updateState()

		return True


	def getState(self):
		return self.state


	def updateState(self):

		if (int(time.time()) - self.lastUpdate) > self.interval:

			logging.debug("[%s]: Getting data from OpenWeatherMap."
				% self.fileName)

			try:
				# Get weather data from OpenWeatherMap
				conn = httplib.HTTPConnection(self.host, self.port)
				location = "/data/2.5/weather?q=" + self.zipCode \
					+ "," + self.countryCode \
					+ "&appid=" + self.apiKey
				conn.request("GET", location)
				response = conn.getresponse()

				# Extract data.
				if response.status == 200:
					jsonData =  json.loads(response.read())

					temp = float(int(jsonData["main"]["temp"])) / 10

					if temp != self.sensorData:

						logging.info("[%s]: Received new temperature data "
							% self.fileName
							+ "from OpenWeatherMap: %.1f degrees Celsius."
							% temp)

						self.sensorData = temp
						self._forceSendState = True
					self.lastUpdate = int(time.time())
				else:
					self.sensorData = -998

			except Exception as e:
				logging.exception("[%s]: Could not get weather data."
					% self.fileName)
				self.sensorData = -999


	def forceSendAlert(self):
		return None


	def forceSendState(self):
		if self._forceSendState:
			self._forceSendState = False

			stateChange = StateChange()
			stateChange.clientSensorId = self.id
			if self.state == self.triggerState:
				stateChange.state = 1
			else:
				stateChange.state = 0
			stateChange.dataType = self.sensorDataType
			stateChange.sensorData = self.sensorData

			return stateChange
		return None


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

				# Check if a sensor alert is forced to send to the server.
				# => update already known state and continue
				sensorAlert = sensor.forceSendAlert()
				if sensorAlert:
					oldState = currentState

					asyncSenderProcess = AsynchronousSender(
						self.connection, self.globalData)
					# set thread to daemon
					# => threads terminates when main thread terminates	
					asyncSenderProcess.daemon = True
					asyncSenderProcess.sendSensorAlert = True
					asyncSenderProcess.sendSensorAlertSensorAlert = sensorAlert
					asyncSenderProcess.start()

					continue

				# check if the current state is the same
				# than the already known state => continue
				elif oldState == currentState:
					continue

				# check if the current state is an alert triggering state
				elif currentState == sensor.triggerState:

					# check if the sensor triggers a sensor alert
					# => send sensor alert to server
					if sensor.triggerAlert:

						logging.info("[%s]: Sensor alert " % self.fileName
							+ "triggered by '%s'." % sensor.description)

						# Create sensor alert object to send to the server.
						sensorAlert = SensorAlert()
						sensorAlert.clientSensorId = sensor.id
						sensorAlert.state = 1
						sensorAlert.hasOptionalData = sensor.hasOptionalData
						sensorAlert.optionalData = sensor.optionalData
						sensorAlert.changeState = sensor.changeState
						sensorAlert.hasLatestData = sensor.hasLatestData
						sensorAlert.dataType = sensor.sensorDataType
						sensorAlert.sensorData = sensor.sensorData

						asyncSenderProcess = AsynchronousSender(
							self.connection, self.globalData)
						# set thread to daemon
						# => threads terminates when main thread terminates	
						asyncSenderProcess.daemon = True
						asyncSenderProcess.sendSensorAlert = True
						asyncSenderProcess.sendSensorAlertSensorAlert = \
							sensorAlert
						asyncSenderProcess.start()

					# if sensor does not trigger sensor alert
					# => just send changed state to server
					else:

						logging.debug("[%s]: State " % self.fileName
							+ "changed by '%s'." % sensor.description)

						# Create state change object to send to the server.
						stateChange = StateChange()
						stateChange.clientSensorId = sensor.id
						stateChange.state = 1
						stateChange.dataType = sensor.sensorDataType
						stateChange.sensorData = sensor.sensorData

						asyncSenderProcess = AsynchronousSender(
							self.connection, self.globalData)
						# set thread to daemon
						# => threads terminates when main thread terminates	
						asyncSenderProcess.daemon = True
						asyncSenderProcess.sendStateChange = True
						asyncSenderProcess.sendStateChangeStateChange = \
							stateChange
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

						# Create sensor alert object to send to the server.
						sensorAlert = SensorAlert()
						sensorAlert.clientSensorId = sensor.id
						sensorAlert.state = 0
						sensorAlert.hasOptionalData = sensor.hasOptionalData
						sensorAlert.optionalData = sensor.optionalData
						sensorAlert.changeState = sensor.changeState
						sensorAlert.hasLatestData = sensor.hasLatestData
						sensorAlert.dataType = sensor.sensorDataType
						sensorAlert.sensorData = sensor.sensorData

						asyncSenderProcess = AsynchronousSender(
							self.connection, self.globalData)
						# set thread to daemon
						# => threads terminates when main thread terminates	
						asyncSenderProcess.daemon = True
						asyncSenderProcess.sendSensorAlert = True
						asyncSenderProcess.sendSensorAlertSensorAlert = \
							sensorAlert
						asyncSenderProcess.start()

					# if sensor does not trigger sensor alert when
					# state is back to normal
					# => just send changed state to server
					else:

						logging.debug("[%s]: State " % self.fileName
							+ "changed by '%s'." % sensor.description)

						# Create state change object to send to the server.
						stateChange = StateChange()
						stateChange.clientSensorId = sensor.id
						stateChange.state = 0
						stateChange.dataType = sensor.sensorDataType
						stateChange.sensorData = sensor.sensorData

						asyncSenderProcess = AsynchronousSender(
							self.connection, self.globalData)
						# set thread to daemon
						# => threads terminates when main thread terminates	
						asyncSenderProcess.daemon = True
						asyncSenderProcess.sendStateChange = True
						asyncSenderProcess.sendStateChangeStateChange = \
							stateChange
						asyncSenderProcess.start()

			# Poll all sensors if they want to force an update that should
			# be send to the server.
			for sensor in self.sensors:

				stateChange = sensor.forceSendState()
				if stateChange:
					asyncSenderProcess = AsynchronousSender(
						self.connection, self.globalData)
					# set thread to daemon
					# => threads terminates when main thread terminates	
					asyncSenderProcess.daemon = True
					asyncSenderProcess.sendStateChange = True
					asyncSenderProcess.sendStateChangeStateChange = stateChange
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