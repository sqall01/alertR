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








# TODO


class RuleSensor:

	def __init__(self):

		def __init__(self):

			self.username = None
			self.remoteSensorId = None



class RuleElement:

	def __init__(self):

		# sensor, rule
		self.type = None 

		self.triggered = False

		# time when rule element triggered
		self.timeWhenTriggered = 0.0 

		# time how long this element counts as triggered
		# (not used by type "rule")
		self.timeTriggeredFor = 0.0 

		self.element = None



class Rule:

	def __init__(self):

		# and, or, not
		self.type = None

		self.elements = list()












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

		# this flag tells if the alert level has rules activated
		# that has to match before an alert is triggered (flag: True) or
		# if it just triggers when a sensor alert is received (flag: False)
		self.rulesActivated = None


		self.rules = list()











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





	def _updateRuleValuesRecursively(self, sensorAlertList,
		currentRuleElement):

		# check if rule element is of type "sensor"
		# => update values of rule
		if currentRuleElement.type == "sensor":

			# get node id of sensor client
			ruleNodeId = self.storage.getNodeId(
				currentRuleElement.element.username)
			if ruleNodeId is None:
				logging.error("[%s]: Not able to get " % self.fileName
					+ "node id for sensor to update rule.")
				return False

			# get sensor id of sensor
			ruleSensorId = self.storage.getSensorId(ruleNodeId,
				currentRuleElement.element.remoteSensorId)
			if ruleSensorId is None:
				logging.error("[%s]: Not able to get " % self.fileName
					+ "sensor id for sensor to update rule.")
				return False

			# update sensor rule element (set as not triggered)
			# if sensor does not count as triggered
			# => unset triggered flag
			if (((currentRuleElement.timeWhenTriggered
				+ currentRuleElement.timeTriggeredFor) < time.time())
				and currentRuleElement.triggered):

				logging.debug("[%s]: Sensor " % self.fileName
					+ "with id '%d' does not count as triggered anymore."
					% ruleSensorId)
				# TODO DEBUG
				print "Sensor with id '%d' does not count as triggered anymore." % ruleSensorId

				currentRuleElement.triggered = False

			# update sensor rule values with current sensor alerts
			for sensorAlert in sensorAlertList:
				sensorAlertNodeId = sensorAlert[2]
				sensorAlertSensorId = sensorAlert[1]
				sensorAlertTimeReceived = sensorAlert[3]
				sensorAlertAlertDelay = sensorAlert[4]

				# check if received sensor alert is triggered by
				# the sensor of the rule
				if (sensorAlertNodeId == ruleNodeId
					and sensorAlertSensorId == ruleSensorId):

					logging.debug("[%s]: Found match " % self.fileName
						+ "for sensor with id '%d' and sensor in rule."
						% ruleSensorId)

					# checked if the received sensor alert
					# is newer than the stored time when triggered
					# => update time when triggered
					if ((sensorAlertTimeReceived + sensorAlertAlertDelay)
						> currentRuleElement.timeWhenTriggered):

						logging.debug("[%s]: New sensor " % self.fileName
							+ "alert for sensor with id '%d' received."
							% ruleSensorId)
						# TODO DEBUG
						print "New sensor alert for sensor with id '%d' received." % ruleSensorId

						currentRuleElement.timeWhenTriggered = \
							sensorAlertTimeReceived + sensorAlertAlertDelay

						# check if sensor still counts as triggered
						# => set triggered flag
						if ((currentRuleElement.timeWhenTriggered
							+ currentRuleElement.timeTriggeredFor)
							> time.time()):

							logging.debug("[%s]: Sensor " % self.fileName
							+ "with id '%d' counts as triggered."
							% ruleSensorId)
							# TODO DEBUG
							print "Sensor with id '%d' counts as triggered."% ruleSensorId

							currentRuleElement.triggered = True

						# if sensor does not count as triggered
						# => unset triggered flag
						else:

							logging.debug("[%s]: Sensor " % self.fileName
							+ "with id '%d' does not count as triggered."
							% ruleSensorId)
							# TODO DEBUG
							print "Sensor with id '%d' does not count as triggered." % ruleSensorId

							currentRuleElement.triggered = False

		# check if rule element is of type "rule"
		# => traverse rule recursively
		elif currentRuleElement.type == "rule":

			# update values of all rule elements in current rule element
			for ruleElement in currentRuleElement.element.elements:
				self._updateRuleValuesRecursively(sensorAlertList,
					ruleElement)

		else:
			logging.error("[%s]: Rule element " % self.fileName
				+ "has an invalid type.")
			return False

		return True




	def _evaluateRuleElementsRecursively(self, currentRuleElement):

		# only evaluate rule elements of type "rule"
		if currentRuleElement.type == "rule":

			# evaluate "and" rule element
			if currentRuleElement.element.type == "and":

				andElement = currentRuleElement.element

				# check if all elements of the "and" rule element are triggered
				for element in andElement.elements:

					# check if sensor element is not triggered
					# => if it is, set current rule element also as
					# not triggered (if it was triggered) and return
					if element.type == "sensor":
						if not element.triggered:

							if currentRuleElement.triggered:
								logging.debug("[%s]: Sensor rule element with "
									% self.fileName
									+ "remote id '%d' and username '%s' not "
									% (element.element.remoteSensorId,
									element.element.username)
									+ "triggered. Set 'and' rule "
									+ "also to not triggered.")

								# TODO DEBUG
								print ("Sensor rule element with "
									+ "remote id '%d' and username '%s' not "
									% (element.element.remoteSensorId,
									element.element.username)
									+ "triggered. Set 'and' rule "
									+ "also to not triggered.")

								currentRuleElement.triggered = False

							return True

					elif element.type == "rule":
						if not self._evaluateRuleElementsRecursively(element):
							return False

						# check if rule element was set to not triggered
						# => if it was, set current rule element
						# also as not triggered (when it was triggered)
						# and return
						if not element.triggered:

							if currentRuleElement.triggered:
								logging.debug("[%s]: Rule element evaluates "
									% self.fileName
									+ "to not triggered. Set 'and' rule "
									+ "also to not triggered.")

								# TODO DEBUG
								print ("Rule element evaluates "
									+ "to not triggered. Set 'and' rule "
									+ "also to not triggered.")

								currentRuleElement.triggered = False

							return True

					else:
						logging.error("[%s]: Type of " % self.fileName
							+ "rule element not valid.")
						return False

				# when this point is reached, every element of the "and"
				# rule is triggered
				# => set current element as triggered (when not triggered)
				# and return
				if not currentRuleElement.triggered:

					logging.debug("[%s]: Each rule element evaluates "
						% self.fileName
						+ "to triggered. Set 'and' rule "
						+ "also to triggered.")

					# TODO DEBUG
					print ("Each rule element evaluates "
						+ "to triggered. Set 'and' rule "
						+ "also to triggered.")

					currentRuleElement.triggered = True
					currentRuleElement.timeWhenTriggered = time.time()

				return True

			# evaluate "or" rule element
			elif currentRuleElement.element.type == "or":

				orElement = currentRuleElement.element

				# first check all elements if there exist a "not rule" element
				# that is triggered
				# => if it does, set current rule element
				# also as triggered (if it was not triggered) and return
				# (done for optimization)
				for element in orElement.elements:

					if (element.type == "sensor"
						and element.triggered == True):

						if not currentRuleElement.triggered:
							logging.debug("[%s]: Sensor rule element with "
								% self.fileName
								+ "remote id '%d' and username '%s' "
								% (element.element.remoteSensorId,
								element.element.username)
								+ "triggered. Set 'or' rule "
								+ "also to triggered.")

							# TODO DEBUG
							print ("Sensor rule element with "
								+ "remote id '%d' and username '%s' "
								% (element.element.remoteSensorId,
								element.element.username)
								+ "triggered. Set 'or' rule "
								+ "also to triggered.")

							currentRuleElement.triggered = True
							currentRuleElement.timeWhenTriggered = time.time()

						return True

				# if there exists no element that is already triggered
				# => update rule elements and evaluate them
				for element in orElement.elements:

					# only update rule elements
					if element.type == "rule":
						if not self._evaluateRuleElementsRecursively(element):
							return False

						# check if rule element was set to triggered
						# => if it was, set current rule element
						# also as triggered (if it was not triggered)
						# and return
						if element.triggered:

							if not currentRuleElement.triggered:
								logging.debug("[%s]: Rule element evaluates "
									% self.fileName
									+ "to triggered. Set 'or' rule "
									+ "also to triggered.")

								# TODO DEBUG
								print ("Rule element evaluates "
									+ "to triggered. Set 'or' rule "
									+ "also to triggered.")

								currentRuleElement.triggered = True
								currentRuleElement.timeWhenTriggered = \
									time.time()

							return True

				# when this point is reached, every element of the "or"
				# rule is not triggered
				# => set current element as not triggered (if it was triggered)
				# and return
				if currentRuleElement.triggered:
					logging.debug("[%s]: Each rule element evaluates "
						% self.fileName
						+ "to not triggered. Set 'or' rule "
						+ "also to not triggered.")

					# TODO DEBUG
					print ("Each rule element evaluates "
						+ "to not triggered. Set 'or' rule "
						+ "also to not triggered.")

					currentRuleElement.triggered = False

				return True

			# evaluate "not" rule element
			elif currentRuleElement.element.type == "not":

				notElement = currentRuleElement.element

				element = notElement.elements[0]

				# check if sensor rule element and current not rule element
				# have the same triggered value
				# => toggle current not element triggered value
				if element.type == "sensor":
					if element.triggered == currentRuleElement.triggered:

						logging.debug("[%s]: Sensor rule element with "
							% self.fileName
							+ "remote id '%d' and username '%s' has same "
							% (element.element.remoteSensorId,
							element.element.username)
							+ "triggered value as 'not' rule. "
							+ "Toggle triggered value of 'not' rule.")

						# TODO DEBUG
						print ("Sensor rule element with "
							+ "remote id '%d' and username '%s' has same "
							% (element.element.remoteSensorId,
							element.element.username)
							+ "triggered value as 'not' rule. "
							+ "Toggle triggered value of 'not' rule.")

						# toggle current rule element triggered value
						currentRuleElement.triggered = not element.triggered

					return True

				elif element.type == "rule":
					if not self._evaluateRuleElementsRecursively(element):
						return False

					# check if rule element was evaluated to the same
					# triggered value as the not rule element
					# => toggle current not element triggered value
					if element.triggered == currentRuleElement.triggered:

						logging.debug("[%s]: Rule element evaluates "
							% self.fileName
							+ "to the same triggered value as 'not' rule. "
							+ "Toggle triggered value of 'not' rule.")

						# TODO DEBUG
						print ("Rule element evaluates "
							+ "to the same triggered value as 'not' rule. "
							+ "Toggle triggered value of 'not' rule.")

						# toggle current rule element triggered value
						currentRuleElement.triggered = not element.triggered

					return True

				else:
					logging.error("[%s]: Type of " % self.fileName
						+ "rule element not valid.")
					return False







	def _updateRule(self, sensorAlertList, alertLevel):

		logging.debug("[%s]: Updating rule values " % self.fileName
			+ "for alert level '%d'." % alertLevel.level)

		for ruleElement in alertLevel.rules:

			# update all rule values (sets also the sensors as triggered
			# or not triggered)
			if not self._updateRuleValuesRecursively(sensorAlertList,
				ruleElement):
				logging.error("[%s]: Not able to update " % self.fileName
					+ "values for alert level '%d'." % alertLevel.level)
				return False

			# evaluate all and/or/not rule elements
			if not self._evaluateRuleElementsRecursively(ruleElement):
				logging.error("[%s]: Not able to evaluate " % self.fileName
					+ "rule for alert level '%d'." % alertLevel.level)
				return False







		# empty sensor alert list after values are updated in rule
		del sensorAlertList[:]






			# TODO
			# update triggered values




		# TODO
		# improve by only update rule when sensoralertlist is not empty



		# TODO
		# remove all sensor alerts from sensorAlertList when rule updating
		# is done ( because it can happen that one sensor is used more than
		# once in the rule)






	def _evaluateRules(self, alertLevel):

		logging.debug("[%s]: Evaluate rules " % self.fileName
			+ "for alert level '%d'." % alertLevel.level)

		# check only the "root" element of the last rule
		# if it has triggered, because only the last rule in the rules chain
		# have to be triggered to trigger the alert level (all other rules
		# in the chain had to be triggered at some point in time to trigger
		# the last rule)
		ruleElement = alertLevel.rules[-1]
		return ruleElement.triggered







	def _checkRulesCanTriggerRecursively(self, currentRuleElement):


		# check if rule element is of type "sensor"
		# => return if it is triggered
		if currentRuleElement.type == "sensor":

			return currentRuleElement.triggered

		# check if rule element is of type "rule"
		# => traverse rule recursively
		elif currentRuleElement.type == "rule":

			# check all rule elements of the current rule element
			# if one rule element is triggered => rule can still trigger
			for ruleElement in currentRuleElement.element.elements:

				if self._checkRulesCanTriggerRecursively(ruleElement):
					return True

			# when this point is reached, no rule element of the current one
			# is triggered
			return False

		else:
			logging.error("[%s]: Rule element " % self.fileName
				+ "has an invalid type while checking.")
			return False





	def _checkRulesCanTrigger(self, alertLevel):

		logging.debug("[%s]: Check if rules of " % self.fileName
			+ "alert level '%d' can trigger." % alertLevel.level)

		# check all rules if they can still trigger
		# if one of the rules chain can => complete rules chain can trigger
		for ruleElement in alertLevel.rules:
			if self._checkRulesCanTriggerRecursively(ruleElement):
				return True

		# when this point is reached, no rule of the rules chain can trigger
		# at the moment
		return False




	def run(self):

		# create an empty list for sensor alerts
		# that have to be handled
		sensorAlertsToHandle = list()

		# create an empty list for sensor alerts
		# that have to be handled and which alert levels have rules
		sensorAlertsToHandleWithRules = list()

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
				and not sensorAlertsToHandleWithRules
				and not sensorAlertList):
					
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

								# split sensor alerts into alerts with rules
								# (each alert level with a rule is handled
								# as a single sensor alert and appended
								# into a separate list)
								if configuredAlertLevel.rulesActivated:

									# check if an alert level with a rule
									# is already triggered
									# => add current sensor alert to it
									found = False
									for alertWithRule in \
										sensorAlertsToHandleWithRules:

										if (configuredAlertLevel ==
											alertWithRule[1]):

											alertWithRule[0].append(
												sensorAlert)

											found = True
											break

									# if no alert level with a rule was found
									# => create a new sensor alert with rule
									# to handle for it
									if not found:
										sensorAlertsToHandleWithRules.append(
											[ [sensorAlert],
											configuredAlertLevel] )

								# create a list of sensor alerts to handle
								# without rules activated
								else:
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
					logging.info("[%s]: No alert level " % self.fileName
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
			if (not sensorAlertsToHandle
				and not sensorAlertsToHandleWithRules):
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
					logging.info("[%s]: No alert level " % self.fileName
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

					# generate integer list of alert levels that have triggered
					# (needed for sensor alert message)
					intListAlertLevel = list()
					for triggeredAlertLevel in triggeredAlertLevels:
						intListAlertLevel.append(triggeredAlertLevel.level)

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





			print "check of sensor alerts with rules NOW"


			# TODO

			# check all sensor alerts to handle with alert levels that have
			# rules if they have to be triggered
			for sensorAlertToHandle in list(sensorAlertsToHandleWithRules):

				print sensorAlertToHandle

				sensorAlertList = sensorAlertToHandle[0]
				alertLevel = sensorAlertToHandle[1]

				self._updateRule(sensorAlertList, alertLevel)





				if self._evaluateRules(alertLevel):

					logging.info("[%s]: Alert level " % self.fileName
						+ "'%d' rules have triggered." % alertLevel.level)



					# TODO
					# send sensor alerts to clients (and email)
					print "Rule has triggered"



					# remove sensor alert to handle from list
					# after it has triggered
					sensorAlertsToHandleWithRules.remove(sensorAlertToHandle)

				else:
					print "Rule has not triggered (yet)"

					if not self._checkRulesCanTrigger(alertLevel):

						logging.debug("[%s]: Alert level " % self.fileName
							+ "'%d' rules can not trigger at the moment."
							% alertLevel.level)


						print "Rule can not trigger at the moment"

						# remove sensor alert to handle from list
						# when it can not trigger at the current state
						sensorAlertsToHandleWithRules.remove(
							sensorAlertToHandle)


					# TODO
					# check if each element of rule is false => remove sensor alert



				'''
				sensorAlertId = sensorAlertToHandle[0][0]
				sensorId = sensorAlertToHandle[0][1]
				nodeId = sensorAlertToHandle[0][2]
				timeReceived = sensorAlertToHandle[0][3]
				alertDelay = sensorAlertToHandle[0][4]
				state = self.storage.getSensorState(sensorId)
				description = sensorAlertToHandle[0][6]
				'''
				


				# TODO
				# store timeReceived of sensor alert in timeWhenTriggered
				# (but only if it is newer then the timeWhenTriggered)

				# steps:
				# 1) update metadata in rule (with newly received sensor alerts)
				# 2) check if alert level has triggered => remove sensor alert
				# 3) check if everything is false => remove sensor alert

				#sensorAlertsToHandleWithRules.remove(sensorAlertToHandle)



				# TODO
				# check alertDelay for triggered sensor alert


			time.sleep(0.5)


	# sets the exit flag to shut down the thread
	def exit(self):
		self.exitFlag = True
		return