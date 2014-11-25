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

		# create an empty list for sensor alerts
		# that have to be handled
		sensorAlertsToHandle = list()

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
			# list is a list of tuples (sensorAlertId, sensorId, nodeId,
			# timeReceived, alertDelay, state, description)
			sensorAlertList = self.storage.getSensorAlerts()

			# check if no sensor alerts are to handle and exist in database
			if (not sensorAlertsToHandle
				and not sensorAlertList):
				# wait until the next sensor alert occurs
				self.sensorAlertEvent.wait()
				self.sensorAlertEvent.clear()
				continue

			# get the flag if the system is active or not
			isAlertSystemActive = self.storage.isAlertSystemActive()

			# check if sensor alerts from the database
			# have to be handled
			for sensorAlert in sensorAlertList:
				sensorAlertId = sensorAlert[0]
				sensorId = sensorAlert[1]

				# delete sensor alert from the database
				self.storage.deleteSensorAlert(sensorAlertId)

				# get all alert levels for this sensor
				sensorAlertLevels = self.storage.getSensorAlertLevels(sensorId)
				if sensorAlertLevels is None:
					logging.error("[%s]: No alert levels " % self.fileName
						+ "for sensor in database. Can not trigger alert.")
					continue

				# get all alert levels that are triggered
				# because of this sensor alert (used as a pre filter)
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

				# add sensorId of the sensor alert
				# to the queue for state changes of the
				# manager update executer
				if self.managerUpdateExecuter != None:
					self.managerUpdateExecuter.queueStateChange.append(
						sensorId)

				# check if an alert level to trigger was found
				# if not => just ignore it
				if not triggeredAlertLevels:
					logging.debug("[%s]: No alert level " % self.fileName
						+ "to trigger was found.")	

					continue

				# update alert levels to trigger
				else:

					# add sensor alert with alert levels
					# to the list of sensor alerts to handle
					sensorAlertsToHandle.append( [sensorAlert,
						triggeredAlertLevels] )

			# wake up manager update executer 
			# => state change will be transmitted
			# (because it is in the queue)
			if self.managerUpdateExecuter != None:
				self.managerUpdateExecuter.managerUpdateEvent.set()

			# when no sensor alerts exist to handle => restart loop
			if not sensorAlertsToHandle:
				continue

			# get the flag if the system is active or not
			isAlertSystemActive = self.storage.isAlertSystemActive()

			# check all sensor alerts to handle if they have to be triggered
			for sensorAlertToHandle in list(sensorAlertsToHandle):
				sensorAlertId = sensorAlertToHandle[0][0]
				sensorId = sensorAlertToHandle[0][1]
				nodeId = sensorAlertToHandle[0][2]
				timeReceived = sensorAlertToHandle[0][3]
				alertDelay = sensorAlertToHandle[0][4]
				state = self.storage.getSensorState(sensorId)
				description = sensorAlertToHandle[0][6]

				# get all alert levels that are triggered
				# because of this sensor alert
				triggeredAlertLevels = list()
				for configuredAlertLevel in self.alertLevels:
					for sensorAlertLevel in sensorAlertToHandle[1]:
						if (configuredAlertLevel.level == 
							sensorAlertLevel.level):
							# check if alert system is active
							# or alert level triggers always
							if (isAlertSystemActive 
								or configuredAlertLevel.triggerAlways):
								triggeredAlertLevels.append(
									configuredAlertLevel)

				# check if an alert level to trigger remains
				# if not => just remove sensor alert to handle from the list
				if not triggeredAlertLevels:
					logging.debug("[%s]: No alert level " % self.fileName
						+ "to trigger remains.")	

					sensorAlertsToHandle.remove(sensorAlertToHandle)

					continue

				# update alert levels to trigger
				else:
					sensorAlertToHandle[1] = triggeredAlertLevels

				# check if sensor alert has triggered
				if (time.time() - timeReceived) > alertDelay:

					# check if one of the triggered alert levels
					# has email notification (smtpAlert) activated
					# => send email alert (to all of the alert levels)
					for triggeredAlertLevel in sensorAlertToHandle[1]:
						if triggeredAlertLevel.smtpActivated:

							# get hostname of the client that triggered the
							# sensor alert
							hostname = self.storage.getNodeHostnameById(nodeId)

							# check if storage backend returned a valid
							# hostname
							if not hostname is None:

								# send email alert to configured email address
								self.smtpAlert.sendSensorAlert(hostname,
									description, timeReceived,
									triggeredAlertLevel.toAddr)

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

					# after sensor alert was triggered
					# => remove sensor alert to handle
					sensorAlertsToHandle.remove(sensorAlertToHandle)

			time.sleep(0.5)


	# sets the exit flag to shut down the thread
	def exit(self):
		self.exitFlag = True
		return