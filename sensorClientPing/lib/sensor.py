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
import subprocess
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


# class that controls one watchdog of a challenge
class PingWatchdogSensor(_PollingSensor):

	def __init__(self):
		_PollingSensor.__init__(self)

		# Set sensor to not hold any data.
		self.sensorDataType = SensorDataType.NONE

		# used for logging
		self.fileName = os.path.basename(__file__)

		# gives the time that the process has to execute
		self.timeout = None

		# gives the interval in seconds in which the process
		# should be checked
		self.intervalToCheck = None

		# gives the command/path that should be executed
		self.execute = None

		# gives the host of the service
		self.host = None

		# time when the process was executed
		self.timeExecute = None

		# the process itself
		self.process = None


	def initializeSensor(self):
		self.changeState = True
		self.hasLatestData = False
		self.timeExecute = 0.0
		self.state = 1 - self.triggerState

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
				self.process = subprocess.Popen([self.execute,
					"-c3", str(self.host)])
				self.timeExecute = utcTimestamp

		# => process is still running
		else:

			# check if process is not finished yet
			if self.process.poll() is None:

				# check if process has timed out
				utcTimestamp = int(time.time())
				if (utcTimestamp - self.timeExecute) > self.timeout:

					self.state = 1

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

				# check if the process has exited with code 0
				# => everything works fine
				if self.process.poll() == 0:
					self.state = 0
				# process did not exited correctly
				# => something is wrong with the ctf service
				else:
					self.state = 1

				# set process to none so it can be newly started
				# in the next state update
				self.process = None


	def forceSendAlert(self):
		return None


	def forceSendState(self):
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