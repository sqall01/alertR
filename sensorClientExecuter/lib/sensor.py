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
from client import AsynchronousSender
from localObjects import SensorDataType, SensorAlert, StateChange
import subprocess


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

		# Flag indicates if the sensor changes its state directly
		# by using forceSendAlert() and forceSendState() and the SensorExecuter
		# should ignore state changes and thereby not generate sensor alerts.
		self.handlesStateMsgs = False


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


# class that controls one watchdog of a challenge
class ExecuterSensor(_PollingSensor):

	def __init__(self):
		_PollingSensor.__init__(self)

		# Set sensor to not hold any data.
		# NOTE: Can be changed if "parseOutput" is set to true in the
		# configuration file.
		self.sensorDataType = SensorDataType.NONE

		# used for logging
		self.fileName = os.path.basename(__file__)

		# gives the time that the process has to execute
		self.timeout = None

		# gives the interval in seconds in which the process
		# should be checked
		self.intervalToCheck = None

		# the command to execute and the arguments to pass
		self.execute = list()

		# This flag indicates if we should only use the exit code to
		# determine the state of the sensor or if we should parse the output.
		self.parseOutput = None

		# time when the process was executed
		self.timeExecute = None

		# the process itself
		self.process = None

		# Used to force a state change to be sent to the server.
		self.shouldForceSendState = False
		self.stateChange = None

		# Used to force a sensor alert to be sent to the server.
		self.shouldForceSendAlert = False
		self.sensorAlert = None


	def _checkDataType(self, dataType):
		if not isinstance(dataType, int):
			return False
		if dataType != self.sensorDataType:
			return False
		return True


	def _checkChangeState(self, changeState):
		if not isinstance(changeState, bool):
			return False
		return True


	def _checkHasLatestData(self, hasLatestData):
		if not isinstance(hasLatestData, bool):
			return False
		return True


	def _checkHasOptionalData(self, hasOptionalData):
		if not isinstance(hasOptionalData, bool):
			return False
		return True


	def _checkState(self, state):
		if not isinstance(state, int):
			return False
		if state != 0 and state != 1:
			return False
		return True


	def _parseOutput(self, data):

		# Parse output data
		try:

			logging.debug("[%s] Received output from sensor with id '%d': %s"
				% (self.fileName, self.id, data))

			message = json.loads(data)

			# Parse message depending on type.
			# Type: statechange
			if str(message["message"]).upper() == "STATECHANGE":

				# Check if state is valid.
				tempInputState = message["payload"]["state"]
				if not self._checkState(tempInputState):
					logging.error("[%s]: Received state "
						% self.fileName
						+ "from output of sensor with id '%d' "
						% self.id
						+ "invalid. Ignoring output.")
					return False

				# Check if data type is valid.
				tempDataType = message["payload"]["dataType"]
				if not self._checkDataType(tempDataType):
					logging.error("[%s]: Received data type "
						% self.fileName
						+ "from output of sensor with id '%d' "
						% self.id
						+ "invalid. Ignoring output.")
					return False

				# Set new data.
				if self.sensorDataType == SensorDataType.NONE:
					self.sensorData = None
				elif self.sensorDataType == SensorDataType.INT:
					self.sensorData = int(message["payload"]["data"])
				elif self.sensorDataType == SensorDataType.FLOAT:
					self.sensorData = float(message["payload"]["data"])

				# Force state change sending if the data could be changed
				# or the state has changed.
				if (self.sensorDataType != SensorDataType.NONE
					or self.state != tempInputState):

					# Create state change object that is
					# send to the server.
					self.stateChange = StateChange()
					self.stateChange.clientSensorId = self.id
					if tempInputState == self.triggerState:
						self.stateChange.state = 1
					else:
						self.stateChange.state = 0
					self.stateChange.dataType = tempDataType
					self.stateChange.sensorData = self.sensorData
					self.shouldForceSendState = True

				# Set state.
				self.state = tempInputState

			# Type: sensoralert
			elif str(message["message"]).upper() == "SENSORALERT":

				# Check if state is valid.
				tempInputState = message["payload"]["state"]
				if not self._checkState(tempInputState):
					logging.error("[%s]: Received state "
						% self.fileName
						+ "from output of sensor with id '%d' "
						% self.id
						+ "invalid. Ignoring output.")
					return False

				# Check if hasOptionalData field is valid.
				tempHasOptionalData = message[
					"payload"]["hasOptionalData"]
				if not self._checkHasOptionalData(tempHasOptionalData):
					logging.error("[%s]: Received hasOptionalData field "
						% self.fileName
						+ "from output of sensor with id '%d' "
						% self.id
						+ "invalid. Ignoring output.")
					return False

				# Check if data type is valid.
				tempDataType = message["payload"]["dataType"]
				if not self._checkDataType(tempDataType):
					logging.error("[%s]: Received data type "
						% self.fileName
						+ "from output of sensor with id '%d' "
						% self.id
						+ "invalid. Ignoring output.")
					return False

				if self.sensorDataType == SensorDataType.NONE:
					tempSensorData = None
				elif self.sensorDataType == SensorDataType.INT:
					tempSensorData = int(message["payload"]["data"])
				elif self.sensorDataType == SensorDataType.FLOAT:
					tempSensorData = float(message["payload"]["data"])

				# Check if hasLatestData field is valid.
				tempHasLatestData = message[
					"payload"]["hasLatestData"]
				if not self._checkHasLatestData(tempHasLatestData):
					logging.error("[%s]: Received hasLatestData field "
						% self.fileName
						+ "from output of sensor with id '%d' "
						% self.id
						+ "invalid. Ignoring output.")
					return False

				# Check if changeState field is valid.
				tempChangeState = message[
					"payload"]["changeState"]
				if not self._checkChangeState(tempChangeState):
					logging.error("[%s]: Received changeState field "
						% self.fileName
						+ "from output of sensor with id '%d' "
						% self.id
						+ "invalid. Ignoring output.")
					return False

				# Check if data should be transfered with the sensor alert
				# => if it should parse it
				tempOptionalData = None
				if tempHasOptionalData:

					tempOptionalData = message["payload"]["optionalData"]

					# check if data is of type dict
					if not isinstance(tempOptionalData, dict):
						logging.warning("[%s]: Received optional data "
							% self.fileName
							+ "from output of sensor with id '%d' "
							% self.id
							+ "invalid. Ignoring output.")
						return False

				# Set optional data.
				self.hasOptionalData = tempHasOptionalData
				self.optionalData = tempOptionalData

				# Set new data.
				if tempHasLatestData:
					self.sensorData = tempSensorData

				# Set state.
				if tempChangeState:
					self.state = tempInputState

				# Create sensor alert object that is send to the server.
				self.sensorAlert = SensorAlert()
				self.sensorAlert.clientSensorId = self.id
				if tempInputState == self.triggerState:
					self.sensorAlert.state = 1
				else:
					self.sensorAlert.state = 0
				self.sensorAlert.hasOptionalData = tempHasOptionalData
				self.sensorAlert.optionalData = tempOptionalData
				self.sensorAlert.changeState = tempChangeState
				self.sensorAlert.hasLatestData = tempHasLatestData
				self.sensorAlert.dataType = tempDataType
				self.sensorAlert.sensorData = tempSensorData
				self.shouldForceSendAlert = True

			# Type: invalid
			else:
				raise ValueError("Received invalid message type.")

		except Exception as e:
			logging.exception("[%s]: Could not parse received data from "
				% self.fileName
				+ "output of sensor with id '%d'."
				% self.id)
			return False

		return True


	def initializeSensor(self):
		self.changeState = True
		self.hasLatestData = False
		self.timeExecute = 0.0
		self.state = 1 - self.triggerState

		# If the sensor parses the output it handles the state changes itself.
		if self.parseOutput:
			self.handlesStateMsgs = True

		if self.sensorDataType == SensorDataType.INT:
			self.sensorData = 0
		elif self.sensorDataType == SensorDataType.FLOAT:
			self.sensorData = 0.0

		return True


	def getState(self):
		return self.state


	def updateState(self):

		# check if a process is executed
		# => if none no process is executed
		if self.process is None:

			# check if the interval in which the service should be checked
			# is exceeded
			utcTimestamp = int(time.time())
			if (utcTimestamp - self.timeExecute) > self.intervalToCheck:

				logging.debug("[%s]: Executing process " % self.fileName
							+ "'%s'." % self.description)

				# Distinguish if we should parse the output or not.
				if self.parseOutput:
					self.process = subprocess.Popen(self.execute,
						stdout=subprocess.PIPE)
				else:
					self.process = subprocess.Popen(self.execute)

				self.timeExecute = utcTimestamp

		# => process is still running
		else:

			# check if process is not finished yet
			if self.process.poll() is None:

				# check if process has timed out
				utcTimestamp = int(time.time())
				if (utcTimestamp - self.timeExecute) > self.timeout:

					self.state = 1
					self.hasOptionalData = True
					self.optionalData = {"message": "Timeout"}

					logging.error("[%s]: Process " % self.fileName
							+ "'%s' has timed out." % self.description)

					# terminate process
					self.process.terminate()

					# give the process one second to terminate
					time.sleep(1)

					# check if the process has terminated
					# => if not kill it
					if self.process.poll() != -15:
						try:
							logging.error("[%s]: Could not " % self.fileName
							+ "terminate '%s'. Killing it." % self.description)

							self.process.kill()
						except:
							pass

					# set process to none so it can be newly started
					# in the next state update
					self.process = None

			# process has finished
			else:

				# Distinguish if we should parse the output or not.
				if self.parseOutput:

					# Parse output.
					output, _ = self.process.communicate()
					if not self._parseOutput(output):

						logging.error("[%s] Not able to parse output "
							% self.fileName
							+ "of sensor with id '%d': %s"
							% (self.id, output))

						self.state = 1

						# Generate sensor alert object.
						self.sensorAlert = SensorAlert()
						self.sensorAlert.clientSensorId = self.id
						self.sensorAlert.state = 1
						self.sensorAlert.hasOptionalData = True
						self.sensorAlert.optionalData = \
							{"message": "Illegal output"}
						self.sensorAlert.changeState = True
						self.sensorAlert.hasLatestData = False
						self.sensorAlert.dataType = self.sensorDataType
						if self.sensorDataType == SensorDataType.NONE:
							self.sensorAlert.sensorData = None
						elif self.sensorDataType == SensorDataType.INT:
							self.sensorAlert.sensorData = 0
						elif self.sensorDataType == SensorDataType.FLOAT:
							self.sensorAlert.sensorData = 0.0
						self.shouldForceSendAlert = True

				else:
					self.hasOptionalData = False
					self.optionalData = None

					# check if the process has exited with code 0
					# => everything works fine
					if self.process.poll() == 0:
						self.state = 0
					# process did not exited correctly
					# => something is wrong with the service
					else:
						self.state = 1

				# set process to none so it can be newly started
				# in the next state update
				self.process = None


	def forceSendAlert(self):
		returnValue = None
		if self.shouldForceSendAlert:
			returnValue = self.sensorAlert
			self.sensorAlert = None
			self.shouldForceSendAlert = False
		return returnValue


	def forceSendState(self):
		returnValue = None
		if self.shouldForceSendState:
			returnValue = self.stateChange
			self.stateChange = None
			self.shouldForceSendState = False
		return returnValue


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

				# Check if we should ignore state changes and just let
				# the sensor handle sensor alerts by using forceSendAlert()
				# and forceSendState().
				elif sensor.handlesStateMsgs:
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
			utcTimestamp = int(time.time())
			if (utcTimestamp - lastFullStateSent) > 60:

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
				lastFullStateSent = utcTimestamp
				
			time.sleep(0.5)