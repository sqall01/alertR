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


# class that represents one FIFO sensor
class SensorFIFO(_PollingSensor, threading.Thread):

	def __init__(self):
		threading.Thread.__init__(self)
		_PollingSensor.__init__(self)

		# used for logging
		self.fileName = os.path.basename(__file__)

		self.fifoFile = None

		self.umask = None

		self.temporaryState = None


	def initializeSensor(self):
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

					self.dataTransfer = bool(
						message["payload"]["dataTransfer"])

					# check if data should be transfered with the sensor alert
					# => if it should parse it
					if self.dataTransfer:

						self.data = message["payload"]["data"]

						# check if data is of type dict
						if not isinstance(self.data, dict):
							logging.warning("[%s]: Received data "
								% self.fileName
								+ "from FIFO file of sensor with id '%d' "
								% self.id
								+ "invalid. Ignoring data to transfer.")
							
							self.dataTransfer = False
							self.data = None

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