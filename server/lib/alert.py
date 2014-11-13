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
from server import AsynchronousSender


# this class represents a single alert level that is configured
class AlertLevel:

	def __init__(self):

		# this flag tells if the alert level has an email notification
		# enabled
		self.smtpActivated = None

		# the email address the email notification should be sent to
		# (if it is enabled)
		self.toAddr = None

		# this value indicates the alert level
		self.level = None

		# gives the name of this alert level
		self.name = None

		# this flag indicates if a sensor alert with this alert level
		# should trigger regardless of if the alert system is active or not
		self.triggerAlways = None


# this class is woken up if a sensor alert is received
# and executes all necessary steps
class SensorAlertExecuter(threading.Thread):

	def __init__(self, globalData):
		threading.Thread.__init__(self)

		# get global configured data
		self.globalData = globalData
		self.serverSessions = self.globalData.serverSessions
		self.managerUpdateExecuter = self.globalData.managerUpdateExecuter
		self.smtpAlert = self.globalData.smtpAlert
		self.storage = self.globalData.storage
		self.alertLevels = self.globalData.alertLevels

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# create an event that is used to wake this thread up
		# and reacte on sensor alert
		self.sensorAlertEvent = threading.Event()
		self.sensorAlertEvent.clear()

		# set exit flag as false
		self.exitFlag = False


	def run(self):

		while 1:

			# check if thread should terminate
			if self.exitFlag:
				return

			# check if manager update executer object reference does exist
			# => if not get it from the global data
			if self.managerUpdateExecuter is None:
				self.managerUpdateExecuter = \
					self.globalData.managerUpdateExecuter

			# get a list of all sensor alerts from database
			# list is a list of tuples of tuples (sensorAlertId, sensorId,
			# timeReceived, alertDelay, state, description)
			sensorAlertList = self.storage.getSensorAlerts()

			# check if no sensor alerts exist in database
			if (sensorAlertList is None
				or len(sensorAlertList) == 0):
				# wait until the next sensor alert occurs
				self.sensorAlertEvent.wait()
				self.sensorAlertEvent.clear()
				continue

			# get the flag if the system is active or not
			isAlertSystemActive = self.storage.isAlertSystemActive()

			# check all sensor alerts that have triggered
			for sensorAlert in sensorAlertList:
				sensorAlertId = sensorAlert[0]
				sensorId = sensorAlert[1]
				timeReceived = sensorAlert[2]
				alertDelay = sensorAlert[3]
				state = sensorAlert[4]
				description = sensorAlert[5]

				# get all alert levels for this sensor
				sensorAlertLevels = self.storage.getSensorAlertLevels(sensorId)
				if sensorAlertLevels is None:
					logging.error("[%s]: No alert levels " % self.fileName
						+ "for sensor in database. Can not trigger alert.")

				# check if sensor alert has triggered
				if (time.time() - timeReceived) > alertDelay:

					# get all alert levels that are triggered
					# because of this sensor alert
					triggeredAlertLevels = list()
					for configuredAlertLevel in self.alertLevels:
						for sensorAlertLevel in sensorAlertLevels:
							if (configuredAlertLevel.level == 
								sensorAlertLevel[0]):
								# check if alert system is active
								# or alert level triggers always
								if (isAlertSystemActive 
									or configuredAlertLevel.triggerAlways):
									triggeredAlertLevels.append(
										configuredAlertLevel)

					# check if a alert level to trigger was found
					# if not => just trigger state change for manager clients
					if not triggeredAlertLevels:
						logging.debug("[%s]: No alert level " % self.fileName
							+ "to trigger was found.")

						# alert can not be handled => delete it
						self.storage.deleteSensorAlert(sensorAlertId)

						# add sensorId of the triggered sensor alert
						# to the queue for state changes of the
						# manager update executer
						if self.managerUpdateExecuter != None:
							self.managerUpdateExecuter.queueStateChange.append(
								sensorId)

						continue

					# check if one of the triggered alert levels
					# has email notification (smtpAlert) activated
					# => send email alert
					for triggeredAlertLevel in triggeredAlertLevels:
						if triggeredAlertLevel.smtpActivated:

							# get tuple of (hostname, description,
							# timeReceived)
							# from database for email alert
							resultTuple = self.storage.getSensorAlertDetails(
								sensorAlertId)

							# check if storage backend returned sensor alert
							# details
							if not resultTuple is None:
								hostname = resultTuple[0]
								description = resultTuple[1]
								timeReceived = resultTuple[2]

								# send email alert to configured email address
								self.smtpAlert.sendSensorAlert(hostname,
									description, timeReceived,
									triggeredAlertLevel.toAddr)

							# send only one email for a triggered sensor alert
							break

					# send sensor alert to all manager and alert clients
					for serverSession in self.serverSessions:
						# ignore sessions which do not exist yet
						# and that are not managers
						if serverSession.clientComm == None:
							continue
						if (serverSession.clientComm.nodeType != "manager"
							and serverSession.clientComm.nodeType != "alert"):
							continue
						if not serverSession.clientComm.clientInitialized:
							continue

						# sending sensor alert to manager/alert node
						# via a thread to not block the sensor alert executer
						sensorAlertProcess = AsynchronousSender(
							self.globalData, serverSession.clientComm)
						# set thread to daemon
						# => threads terminates when main thread terminates	
						sensorAlertProcess.daemon = True
						sensorAlertProcess.sendSensorAlert = True
						sensorAlertProcess.sensorAlertSensorId = sensorId
						sensorAlertProcess.sensorAlertState = state

						# generate integer list of alert levels
						intListAlertLevel = list()
						for triggeredAlertLevel in triggeredAlertLevels:
							intListAlertLevel.append(triggeredAlertLevel.level)

						sensorAlertProcess.sensorAlertAlertLevels = \
							intListAlertLevel
						sensorAlertProcess.sensorAlertSensorDescription = \
							description

						logging.debug("[%s]: Sending sensor " % self.fileName
							+ "alert to manager/alert (%s:%d)."
							% (serverSession.clientComm.clientAddress,
							serverSession.clientComm.clientPort))
						sensorAlertProcess.start()

					# after alert triggers => delete it
					self.storage.deleteSensorAlert(sensorAlertId)

				# if the sensor alert has not triggered yet
				# => send state change to manager clients
				else:
					# add sensorId of the triggered sensor alert
					# to the queue for state changes of the
					# manager update executer
					if self.managerUpdateExecuter != None:
						self.managerUpdateExecuter.queueStateChange.append(
							sensorId)

			# wake up manager update executer even if sensor alerts are
			# deactivated => state change will be transmitted
			# (because it is in the queue)
			if self.managerUpdateExecuter != None:
				self.managerUpdateExecuter.managerUpdateEvent.set()

			time.sleep(0.5)


	# sets the exit flag to shut down the thread
	def exit(self):
		self.exitFlag = True
		return