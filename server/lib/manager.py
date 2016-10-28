#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import threading
import os
import time
import logging
import collections
from server import AsynchronousSender


# this class is woken up if a sensor alert or state change is received
# and sends updates to all manager clients
class ManagerUpdateExecuter(threading.Thread):

	def __init__(self, globalData):
		threading.Thread.__init__(self)

		# get global configured data
		self.globalData = globalData
		self.logger = self.globalData.logger
		self.serverSessions = self.globalData.serverSessions
		self.managerUpdateInterval = self.globalData.managerUpdateInterval
		self.storage = self.globalData.storage

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# create an event that is used to wake this thread up
		# and reacte on state changes/sensor alerts
		self.managerUpdateEvent = threading.Event()
		self.managerUpdateEvent.clear()

		# set exit flag as false
		self.exitFlag = False

		# this is used to know when the last status update was send to the
		# manager clients
		self.lastStatusUpdateSend = 0

		# this is used to know if a full status update has to be sent to
		# the manager clients (ignoring the time interval)
		self.forceStatusUpdate = False

		# this is a queue that is used to signalize the state changes
		# that should be sent to the manager clients
		self.queueStateChange = collections.deque()


	def run(self):

		while True:

			# check if thread should terminate
			if self.exitFlag:
				return

			# check if state change queue is empty before waiting
			# for event (or timeout)
			if len(self.queueStateChange) == 0:
				# wait 10 seconds before checking if a
				# status update to all manager nodes has to be sent
				# or check it when the event is triggered
				self.managerUpdateEvent.wait(10)
				self.managerUpdateEvent.clear()

			# check if last status update has timed out
			# or a status update is forced
			# => send status update to all manager
			utcTimestamp = int(time.time())
			if (((utcTimestamp - self.managerUpdateInterval)
				> self.lastStatusUpdateSend)
				or self.forceStatusUpdate):

				# update time when last status update was sent
				self.lastStatusUpdateSend = utcTimestamp

				# reset new client variable
				self.forceStatusUpdate = False

				# empty current state queue
				# (because the state changes are also transmitted
				# during the full state update)
				self.queueStateChange.clear()

				for serverSession in self.serverSessions:
					# ignore sessions which do not exist yet
					# and that are not managers
					if serverSession.clientComm == None:
						continue
					if serverSession.clientComm.nodeType != "manager":
						continue
					if not serverSession.clientComm.clientInitialized:
						continue

					# sending status update to manager via a thread
					# to not block the manager update executer
					statusUpdateProcess = AsynchronousSender(self.globalData,
						serverSession.clientComm)
					# set thread to daemon
					# => threads terminates when main thread terminates
					statusUpdateProcess.daemon = True
					statusUpdateProcess.sendManagerUpdate = True
					statusUpdateProcess.start()

				# if status update was sent to manager clients
				# => ignore state changes (because they are also covered
				# by a status update)
				continue

			# if status change queue is not empty
			# => send status changes to manager clients
			while len(self.queueStateChange) != 0:
				managerStateTuple = self.queueStateChange.popleft()
				sensorId = managerStateTuple[0]
				state = managerStateTuple[1]
				dataType = managerStateTuple[2]
				sensorData = managerStateTuple[3]

				for serverSession in self.serverSessions:
					# ignore sessions which do not exist yet
					# and that are not managers
					if serverSession.clientComm == None:
						continue
					if serverSession.clientComm.nodeType != "manager":
						continue
					if not serverSession.clientComm.clientInitialized:
						continue

					# sending status update to manager via a thread
					# to not block the manager update executer
					stateChangeProcess = AsynchronousSender(self.globalData,
						serverSession.clientComm)
					# set thread to daemon
					# => threads terminates when main thread terminates
					stateChangeProcess.daemon = True
					stateChangeProcess.sendManagerStateChange = True
					stateChangeProcess.sendManagerStateChangeSensorId \
						= sensorId
					stateChangeProcess.sendManagerStateChangeState \
						= state
					stateChangeProcess.sendManagerStateChangeDataType \
						= dataType
					stateChangeProcess.sendManagerStateChangeData \
						= sensorData
					stateChangeProcess.start()


	# sets the exit flag to shut down the thread
	def exit(self):
		self.exitFlag = True
		return