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
import subprocess


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


# class that controls one watchdog of a challenge
class PingWatchdogSensor(_PollingSensor):

	def __init__(self):
		_PollingSensor.__init__(self)

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
		self.timeExecute = 0.0


	def getState(self):
		return self.state


	def updateState(self):

		# check if a process is executed
		# => if none no process is executed
		if self.process is None:

			# check if the interval in which the service should be checked
			# is exceeded
			if (int(time.time()) - self.timeExecute) > self.intervalToCheck:

				logging.debug("[%s]: Executing process " % self.fileName
							+ "'%s'." % self.description)
				self.process = subprocess.Popen([self.execute,
					"-c3", str(self.host)])
				self.timeExecute = int(time.time())

		# => process is still running
		else:

			# check if process is not finished yet
			if self.process.poll() is None:

				# check if process has timed out
				if (int(time.time()) - self.timeExecute) > self.timeout:

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