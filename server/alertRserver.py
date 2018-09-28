#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import sys
import os
from lib import ConnectionWatchdog, ConfigWatchdog
from lib import ServerSession, ThreadedTCPServer
from lib import Sqlite, Mysql
from lib import SensorDataType, AlertLevel
from lib import SensorTimeoutSensor, NodeTimeoutSensor, \
	AlertSystemActiveSensor, VersionInformerSensor
from lib import SensorAlertExecuter
from lib import RuleStart, RuleElement, RuleBoolean, RuleSensor, RuleWeekday, \
	RuleMonthday, RuleHour, RuleMinute, RuleSecond
from lib import CSVBackend
from lib import ManagerUpdateExecuter
from lib import GlobalData
from lib import SurveyExecuter
from lib import VersionInformer
import socket
import logging
import time
import threading
import random
import xml.etree.ElementTree


# Function creates a path location for the given user input.
def makePath(inputLocation):
	# Do nothing if the given location is an absolute path.
	if inputLocation[0] == "/":
		return inputLocation
	# Replace ~ with the home directory.
	elif inputLocation[0] == "~":
		return os.environ["HOME"] + inputLocation[1:]
	# Assume we have a given relative path.
	return os.path.dirname(os.path.abspath(__file__)) + "/" + inputLocation


# function is used to parse a rule of an alert level recursively
def parseRuleRecursively(currentRoot, currentRule):

	if currentRoot.tag == "not":

		# get possible elemts
		orItem = currentRoot.find("or")
		andItem = currentRoot.find("and")
		notItem = currentRoot.find("not")
		sensorItem = currentRoot.find("sensor")
		weekdayItem = currentRoot.find("weekday")
		monthdayItem = currentRoot.find("monthday")
		hourItem = currentRoot.find("hour")
		minuteItem = currentRoot.find("minute")
		secondItem = currentRoot.find("second")

		# check that only one tag is given in not tag
		# (because only one is allowed)
		counter = 0
		if not orItem is None:
			counter += 1
		if not andItem is None:
			counter += 1
		if not notItem is None:
			counter += 1
		if not sensorItem is None:
			counter += 1
		if not weekdayItem is None:
			counter += 1
		if not monthdayItem is None:
			counter += 1
		if not hourItem is None:
			counter += 1
		if not minuteItem is None:
			counter += 1
		if not secondItem is None:
			counter += 1
		if counter != 1:
			raise ValueError("Only one tag is valid inside a 'not' tag.")

		# start parsing the rule
		if not orItem is None:

			# create a new "or" rule
			ruleNew = RuleBoolean()
			ruleNew.type = "or"

			# create a wrapper element around the rule
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "boolean"
			ruleElement.element = ruleNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

			# parse rule starting from the new element
			parseRuleRecursively(orItem, ruleNew)

		elif not andItem is None:

			# create a new "and" rule
			ruleNew = RuleBoolean()
			ruleNew.type = "and"

			# create a wrapper element around the rule
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "boolean"
			ruleElement.element = ruleNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

			# parse rule starting from the new element
			parseRuleRecursively(andItem, ruleNew)

		elif not notItem is None:

			# create a new "not" rule
			ruleNew = RuleBoolean()
			ruleNew.type = "not"

			# create a wrapper element around the rule
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "boolean"
			ruleElement.element = ruleNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

			# parse rule starting from the new element
			parseRuleRecursively(notItem, ruleNew)

		elif not sensorItem is None:

			ruleSensorNew = RuleSensor()
			ruleSensorNew.username = str(sensorItem.attrib["username"])
			ruleSensorNew.remoteSensorId = int(sensorItem.attrib[
				"remoteSensorId"])

			# create a wrapper element around the sensor element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "sensor"
			ruleElement.element = ruleSensorNew
			ruleElement.timeTriggeredFor = float(
				sensorItem.attrib["timeTriggeredFor"])

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		elif not weekdayItem is None:

			ruleWeekdayNew = RuleWeekday()

			# get time attribute and check if valid
			ruleWeekdayNew.time = str(weekdayItem.attrib["time"])
			if (ruleWeekdayNew.time != "local" and
				ruleWeekdayNew.time != "utc"):
				raise ValueError("No valid value for 'time' attribute "
					+ "in weekday tag.")

			# get weekday attribute and check if valid
			ruleWeekdayNew.weekday = int(weekdayItem.attrib[
				"weekday"])
			if (ruleWeekdayNew.weekday < 0 or
				ruleWeekdayNew.weekday > 6):
				raise ValueError("No valid value for 'weekday' "
					+ "attribute in weekday tag.")

			# create a wrapper element around the weekday element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "weekday"
			ruleElement.element = ruleWeekdayNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		elif not monthdayItem is None:

			ruleMonthdayNew = RuleMonthday()

			# get time attribute and check if valid
			ruleMonthdayNew.time = str(monthdayItem.attrib["time"])
			if (ruleMonthdayNew.time != "local" and
				ruleMonthdayNew.time != "utc"):
				raise ValueError("No valid value for 'time' attribute "
					+ "in monthday tag.")

			# get monthday attribute and check if valid
			ruleMonthdayNew.monthday = int(monthdayItem.attrib[
				"monthday"])
			if (ruleMonthdayNew.monthday < 1 or
				ruleMonthdayNew.monthday > 31):
				raise ValueError("No valid value for 'monthday' "
					+ "attribute in monthday tag.")

			# create a wrapper element around the monthday element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "monthday"
			ruleElement.element = ruleMonthdayNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		elif not hourItem is None:

			ruleHourNew = RuleHour()

			# get time attribute and check if valid
			ruleHourNew.time = str(hourItem.attrib["time"])
			if (ruleHourNew.time != "local" and
				ruleHourNew.time != "utc"):
				raise ValueError("No valid value for 'time' attribute "
					+ "in hour tag.")

			# get start attribute and check if valid
			ruleHourNew.start = int(hourItem.attrib[
				"start"])
			if (ruleHourNew.start < 0 or
				ruleHourNew.start > 23):
				raise ValueError("No valid value for 'start' "
					+ "attribute in hour tag.")

			# get end attribute and check if valid
			ruleHourNew.end = int(hourItem.attrib[
				"end"])
			if (ruleHourNew.start < 0 or
				ruleHourNew.start > 23):
				raise ValueError("No valid value for 'end' "
					+ "attribute in hour tag.")

			if ruleHourNew.start > ruleHourNew.end:
				raise ValueError("'start' attribute not allowed to be "
					+ "greater than 'end' attribute in hour tag.")

			# create a wrapper element around the hour element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "hour"
			ruleElement.element = ruleHourNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		elif not minuteItem is None:

			ruleMinuteNew = RuleMinute()

			# get start attribute and check if valid
			ruleMinuteNew.start = int(minuteItem.attrib[
				"start"])
			if (ruleMinuteNew.start < 0 or
				ruleMinuteNew.start > 59):
				raise ValueError("No valid value for 'start' "
					+ "attribute in minute tag.")

			# get end attribute and check if valid
			ruleMinuteNew.end = int(minuteItem.attrib[
				"end"])
			if (ruleMinuteNew.start < 0 or
				ruleMinuteNew.start > 59):
				raise ValueError("No valid value for 'end' "
					+ "attribute in minute tag.")

			if ruleMinuteNew.start > ruleMinuteNew.end:
				raise ValueError("'start' attribute not allowed to be "
					+ "greater than 'end' attribute in minute tag.")

			# create a wrapper element around the minute element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "minute"
			ruleElement.element = ruleMinuteNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		elif not secondItem is None:

			ruleSecondNew = RuleSecond()

			# get start attribute and check if valid
			ruleSecondNew.start = int(secondItem.attrib[
				"start"])
			if (ruleSecondNew.start < 0 or
				ruleSecondNew.start > 59):
				raise ValueError("No valid value for 'start' "
					+ "attribute in second tag.")

			# get end attribute and check if valid
			ruleSecondNew.end = int(secondItem.attrib[
				"end"])
			if (ruleSecondNew.start < 0 or
				ruleSecondNew.start > 59):
				raise ValueError("No valid value for 'end' "
					+ "attribute in second tag.")

			if ruleSecondNew.start > ruleSecondNew.end:
				raise ValueError("'start' attribute not allowed to be "
					+ "greater than 'end' attribute in second tag.")

			# create a wrapper element around the second element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "second"
			ruleElement.element = ruleSecondNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		else:
			raise ValueError("No valid tag was found.")

		# NOT is always an invalid rule (ignores all elements inside the
		# NOT element)
		return False

	elif (currentRoot.tag == "and"
		or currentRoot.tag == "or"):

		# set the current rule element to invald
		ruleValid = False

		# parse all "sensor" tags
		for item in currentRoot.iterfind("sensor"):

			ruleSensorNew = RuleSensor()
			ruleSensorNew.username = str(item.attrib["username"])
			ruleSensorNew.remoteSensorId = int(item.attrib["remoteSensorId"])

			# create a wrapper element around the sensor element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "sensor"
			ruleElement.element = ruleSensorNew
			ruleElement.timeTriggeredFor = float(
				item.attrib["timeTriggeredFor"])

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

			# a sensor element always sets the rule to a valid rule
			ruleValid = True

		# parse all "weekday" tags
		for item in currentRoot.iterfind("weekday"):

			ruleWeekdayNew = RuleWeekday()

			# get time attribute and check if valid
			ruleWeekdayNew.time = str(item.attrib["time"])
			if (ruleWeekdayNew.time != "local" and
				ruleWeekdayNew.time != "utc"):
				raise ValueError("No valid value for 'time' attribute "
					+ "in weekday tag.")

			# get weekday attribute and check if valid
			ruleWeekdayNew.weekday = int(item.attrib[
				"weekday"])
			if (ruleWeekdayNew.weekday < 0 or
				ruleWeekdayNew.weekday > 6):
				raise ValueError("No valid value for 'weekday' "
					+ "attribute in weekday tag.")

			# create a wrapper element around the weekday element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "weekday"
			ruleElement.element = ruleWeekdayNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		# parse all "monthday" tags
		for item in currentRoot.iterfind("monthday"):

			ruleMonthdayNew = RuleMonthday()

			# get time attribute and check if valid
			ruleMonthdayNew.time = str(item.attrib["time"])
			if (ruleMonthdayNew.time != "local" and
				ruleMonthdayNew.time != "utc"):
				raise ValueError("No valid value for 'time' attribute "
					+ "in monthday tag.")

			# get monthday attribute and check if valid
			ruleMonthdayNew.monthday = int(item.attrib[
				"monthday"])
			if (ruleMonthdayNew.monthday < 1 or
				ruleMonthdayNew.monthday > 31):
				raise ValueError("No valid value for 'monthday' "
					+ "attribute in monthday tag.")

			# create a wrapper element around the monthday element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "monthday"
			ruleElement.element = ruleMonthdayNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		# parse all "hour" tags
		for item in currentRoot.iterfind("hour"):

			ruleHourNew = RuleHour()

			# get time attribute and check if valid
			ruleHourNew.time = str(item.attrib["time"])
			if (ruleHourNew.time != "local" and
				ruleHourNew.time != "utc"):
				raise ValueError("No valid value for 'time' attribute "
					+ "in hour tag.")

			# get start attribute and check if valid
			ruleHourNew.start = int(item.attrib[
				"start"])
			if (ruleHourNew.start < 0 or
				ruleHourNew.start > 23):
				raise ValueError("No valid value for 'start' "
					+ "attribute in hour tag.")

			# get end attribute and check if valid
			ruleHourNew.end = int(item.attrib[
				"end"])
			if (ruleHourNew.start < 0 or
				ruleHourNew.start > 23):
				raise ValueError("No valid value for 'end' "
					+ "attribute in hour tag.")

			if ruleHourNew.start > ruleHourNew.end:
				raise ValueError("'start' attribute not allowed to be"
					+ "greater than 'end' attribute in hour tag.")

			# create a wrapper element around the hour element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "hour"
			ruleElement.element = ruleHourNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		# parse all "minute" tags
		for item in currentRoot.iterfind("minute"):

			ruleMinuteNew = RuleMinute()

			# get start attribute and check if valid
			ruleMinuteNew.start = int(item.attrib[
				"start"])
			if (ruleMinuteNew.start < 0 or
				ruleMinuteNew.start > 59):
				raise ValueError("No valid value for 'start' "
					+ "attribute in minute tag.")

			# get end attribute and check if valid
			ruleMinuteNew.end = int(item.attrib[
				"end"])
			if (ruleMinuteNew.start < 0 or
				ruleMinuteNew.start > 59):
				raise ValueError("No valid value for 'end' "
					+ "attribute in minute tag.")

			if ruleMinuteNew.start > ruleMinuteNew.end:
				raise ValueError("'start' attribute not allowed to be "
					+ "greater than 'end' attribute in minute tag.")

			# create a wrapper element around the minute element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "minute"
			ruleElement.element = ruleMinuteNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		# parse all "second" tags
		for item in currentRoot.iterfind("second"):

			ruleSecondNew = RuleSecond()

			# get start attribute and check if valid
			ruleSecondNew.start = int(item.attrib[
				"start"])
			if (ruleSecondNew.start < 0 or
				ruleSecondNew.start > 59):
				raise ValueError("No valid value for 'start' "
					+ "attribute in second tag.")

			# get end attribute and check if valid
			ruleSecondNew.end = int(item.attrib[
				"end"])
			if (ruleSecondNew.start < 0 or
				ruleSecondNew.start > 59):
				raise ValueError("No valid value for 'end' "
					+ "attribute in second tag.")

			if ruleSecondNew.start > ruleSecondNew.end:
				raise ValueError("'start' attribute not allowed to be "
					+ "greater than 'end' attribute in second tag.")

			# create a wrapper element around the second element
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "second"
			ruleElement.element = ruleSecondNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

		# parse all "and" tags
		for item in currentRoot.iterfind("and"):

			# create a new "and" rule
			ruleNew = RuleBoolean()
			ruleNew.type = "and"

			# create a wrapper element around the rule
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "boolean"
			ruleElement.element = ruleNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

			# parse rule starting from the new element
			tempValid = parseRuleRecursively(item, ruleNew)

			# only set the rule to the result of the recursively parsing
			# if it is not already valid
			if not ruleValid:
				ruleValid = tempValid

		# parse all "or" tags
		for item in currentRoot.iterfind("or"):

			# create a new "or" rule
			ruleNew = RuleBoolean()
			ruleNew.type = "or"

			# create a wrapper element around the rule
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "boolean"
			ruleElement.element = ruleNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

			# parse rule starting from the new element
			tempValid = parseRuleRecursively(item, ruleNew)

			# only set the rule to the result of the recursively parsing
			# if it is not already valid
			if not ruleValid:
				ruleValid = tempValid

		# parse all "not" tags
		for item in currentRoot.iterfind("not"):

			# create a new "not" rule
			ruleNew = RuleBoolean()
			ruleNew.type = "not"

			# create a wrapper element around the rule
			# to have meta information (i.e. triggered,
			# time when triggered, etc.)
			ruleElement = RuleElement()
			ruleElement.type = "boolean"
			ruleElement.element = ruleNew

			# add wrapper element to the current rule
			currentRule.elements.append(ruleElement)

			# parse rule starting from the new element
			parseRuleRecursively(item, ruleNew)

		# return if the current rule is valid
		return ruleValid

	else:
		raise ValueError("No valid tag found in rule.")


# function is used to write the parsed rules to the log file
def logRule(ruleElement, spaces, fileName):

	if isinstance(ruleElement, RuleStart):
		logString = ("RULE (order=%d, " % ruleElement.order
			+ "minTimeAfterPrev=%.2f, " % ruleElement.minTimeAfterPrev
			+ "maxTimeAfterPrev=%.2f, " % ruleElement.maxTimeAfterPrev
			+ "counterActivated=%s, " % str(ruleElement.counterActivated)
			+ "counterLimit=%d, " % ruleElement.counterLimit
			+ "counterWaitTime=%d)" % ruleElement.counterWaitTime)
		logging.info("[%s]: %s" % (fileName, logString))

	spaceString = ""
	for i in range(spaces):
		spaceString += "   "

	if ruleElement.type == "boolean":
		logString = "%s %s" % (spaceString, ruleElement.element.type)
		logging.info("[%s]: %s" % (fileName, logString))

		spaceString += "   "

		for item in ruleElement.element.elements:

			if item.type == "boolean":
				logRule(item, spaces+1, fileName)

			elif item.type == "sensor":
				logString = ("%s sensor " % spaceString
					+ "(triggeredFor=%.2f, " % item.timeTriggeredFor
					+ "user=%s, " % item.element.username
					+ "remoteId=%d)" % item.element.remoteSensorId)
				logging.info("[%s]: %s" % (fileName, logString))

			elif item.type == "weekday":

				logString = ("%s weekday " % spaceString
					+ "(time=%s, " % item.element.time
					+ "weekday=%d)" % item.element.weekday)
				logging.info("[%s]: %s" % (fileName, logString))

			elif item.type == "monthday":

				logString = ("%s monthday " % spaceString
					+ "(time=%s, " % item.element.time
					+ "monthday=%d)" % item.element.monthday)
				logging.info("[%s]: %s" % (fileName, logString))

			elif item.type == "hour":

				logString = ("%s hour " % spaceString
					+ "(time=%s, " % item.element.time
					+ "start=%d, " % item.element.start
					+ "end=%d)") % item.element.end
				logging.info("[%s]: %s" % (fileName, logString))

			elif item.type == "minute":

				logString = ("%s minute " % spaceString
					+ "(start=%d, " % item.element.start
					+ "end=%d)") % item.element.end
				logging.info("[%s]: %s" % (fileName, logString))

			elif item.type == "second":

				logString = ("%s second " % spaceString
					+ "(start=%d, " % item.element.start
					+ "end=%d)") % item.element.end
				logging.info("[%s]: %s" % (fileName, logString))

			else:
				raise ValueError("Rule has invalid type: '%s'."
					% ruleElement.type)

	elif ruleElement.type == "sensor":

		logString = ("%s sensor " % spaceString
			+ "(triggeredFor=%.2f, " % ruleElement.timeTriggeredFor
			+ "user=%s, " % ruleElement.element.username
			+ "remoteId=%d)" % ruleElement.element.remoteSensorId)
		logging.info("[%s]: %s" % (fileName, logString))

	elif ruleElement.type == "weekday":

		logString = ("%s weekday " % spaceString
			+ "(time=%s, " % ruleElement.element.time
			+ "weekday=%d)" % ruleElement.element.weekday)
		logging.info("[%s]: %s" % (fileName, logString))

	elif ruleElement.type == "monthday":

		logString = ("%s monthday " % spaceString
			+ "(time=%s, " % ruleElement.element.time
			+ "monthday=%d)" % ruleElement.element.monthday)
		logging.info("[%s]: %s" % (fileName, logString))

	elif ruleElement.type == "hour":

		logString = ("%s hour " % spaceString
			+ "(time=%s, " % ruleElement.element.time
			+ "start=%d, " % ruleElement.element.start
			+ "end=%d)") % ruleElement.element.end
		logging.info("[%s]: %s" % (fileName, logString))

	elif ruleElement.type == "minute":

		logString = ("%s minute " % spaceString
			+ "(start=%d, " % ruleElement.element.start
			+ "end=%d)") % ruleElement.element.end
		logging.info("[%s]: %s" % (fileName, logString))

	elif ruleElement.type == "second":

		logString = ("%s second " % spaceString
			+ "(start=%d, " % ruleElement.element.start
			+ "end=%d)") % ruleElement.element.end
		logging.info("[%s]: %s" % (fileName, logString))

	else:
		raise ValueError("Rule has invalid type: '%s'." % ruleElement.type)


if __name__ == '__main__':

	# generate object of the global needed data
	globalData = GlobalData()

	fileName = os.path.basename(__file__)

	# parse config file, get logfile configurations
	# and initialize logging
	try:
		configRoot = xml.etree.ElementTree.parse(
			globalData.configFile).getroot()

		globalData.logdir = makePath(str(configRoot.find("general").find(
			"log").attrib["dir"]))

		# parse chosen log level
		tempLoglevel = str(
			configRoot.find("general").find("log").attrib["level"])
		tempLoglevel = tempLoglevel.upper()
		if tempLoglevel == "DEBUG":
			globalData.loglevel = logging.DEBUG
		elif tempLoglevel == "INFO":
			globalData.loglevel = logging.INFO
		elif tempLoglevel == "WARNING":
			globalData.loglevel = logging.WARNING
		elif tempLoglevel == "ERROR":
			globalData.loglevel = logging.ERROR
		elif tempLoglevel == "CRITICAL":
			globalData.loglevel = logging.CRITICAL
		else:
			raise ValueError("No valid log level in config file.")

		# initialize logging
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
			datefmt='%m/%d/%Y %H:%M:%S',
			filename=globalData.logdir + "/all.log",
			level=globalData.loglevel)

		globalData.logger = logging.getLogger("server")
		fh = logging.FileHandler(globalData.logdir + "/server.log")
		fh.setLevel(globalData.loglevel)
		format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s',
			'%m/%d/%Y %H:%M:%S')
		fh.setFormatter(format)
		globalData.logger.addHandler(fh)

	except Exception as e:
		print "Config could not be parsed."
		print e
		sys.exit(1)

	# parse the rest of the config with initialized logging
	try:

		# check if config and client version are compatible
		version = float(configRoot.attrib["version"])
		if version != globalData.version:
			raise ValueError("Config version '%.3f' not "
				% version
				+ "compatible with client version '%.3f'."
				% globalData.version)

		# parse update options
		globalData.logger.debug("[%s]: Parsing update configuration."
			% fileName)
		updateActivated = (str(
			configRoot.find("update").find("general").attrib[
			"activated"]).upper() == "TRUE")
		updateServer = None
		updateLocation = None
		if updateActivated is True:
			updateServer = str(
				configRoot.find("update").find("server").attrib["host"])
			updatePort = int(
				configRoot.find("update").find("server").attrib["port"])
			updateLocation = str(
				configRoot.find("update").find("server").attrib["location"])
			updateCaFile = makePath(str(
				configRoot.find("update").find("server").attrib["caFile"]))
			updateInterval = int(
				configRoot.find("update").find("general").attrib["interval"])

		# configure user credentials backend
		globalData.logger.debug("[%s]: Parsing user backend configuration."
			% fileName)
		userBackendMethod = str(
			configRoot.find("storage").find("userBackend").attrib[
			"method"]).upper()
		if userBackendMethod == "CSV":
			globalData.userBackend = CSVBackend(globalData,
				globalData.userBackendCsvFile)

		else:
			raise ValueError("No valid user backend method in config file.")

		# configure storage backend (check which backend is configured)
		globalData.logger.debug("[%s]: Parsing storage backend configuration."
			% fileName)
		userBackendMethod = str(
			configRoot.find("storage").find("storageBackend").attrib[
			"method"]).upper()
		if userBackendMethod == "SQLITE":
			globalData.storage = Sqlite(globalData.storageBackendSqliteFile,
				globalData)

		elif userBackendMethod == "MYSQL":

			backendUsername = str(configRoot.find("storage").find(
				"storageBackend").attrib["username"])
			backendPassword = str(configRoot.find("storage").find(
				"storageBackend").attrib["password"])
			backendServer = str(configRoot.find("storage").find(
				"storageBackend").attrib["server"])
			backendPort = int(configRoot.find("storage").find(
				"storageBackend").attrib["port"])
			backendDatabase = str(configRoot.find("storage").find(
				"storageBackend").attrib["database"])

			globalData.storage = Mysql(backendServer, backendPort,
				backendDatabase, backendUsername, backendPassword,
				globalData)

		else:
			raise ValueError("No valid storage backend method in config file.")

		# Add server as node to the database.
		serverUsername = globalData.storage.getUniqueID()
		if not globalData.storage.addNode(serverUsername,
			socket.gethostname(),
			"server",
			"server",
			globalData.version,
			globalData.rev,
			1):
			raise ValueError("Not able to add server as node to the database.")
		serverNodeId = globalData.storage.getNodeId(serverUsername)

		# Mark server node as connected.
		if not globalData.storage.markNodeAsConnected(serverNodeId):
			raise ValueError("Not able to mark server node as connected.")

		# Get survey configurations
		globalData.logger.debug("[%s]: Parsing survey configuration."
			% fileName)
		surveyActivated = (str(
			configRoot.find("general").find("survey").attrib[
			"participate"]).upper() == "TRUE")

		# get server configurations
		globalData.logger.debug("[%s]: Parsing server configuration."
			% fileName)
		globalData.serverCertFile = makePath(str(configRoot.find(
			"general").find("server").attrib["certFile"]))
		globalData.serverKeyFile = makePath(str(configRoot.find(
			"general").find("server").attrib["keyFile"]))
		port = int(configRoot.find("general").find("server").attrib["port"])

		if (os.path.exists(globalData.serverCertFile) is False
			or os.path.exists(globalData.serverKeyFile) is False):
			raise ValueError("Server certificate or key does not exist.")

		# get client configurations
		globalData.useClientCertificates = (str(
			configRoot.find("general").find("client").attrib[
			"useClientCertificates"]).upper() == "TRUE")

		if globalData.useClientCertificates is True:

			globalData.clientCAFile = makePath(str(configRoot.find(
				"general").find("client").attrib["clientCAFile"]))

			if os.path.exists(globalData.clientCAFile) is False:
				raise ValueError("Client CA file does not exist.")

		# parse all alert levels
		globalData.logger.debug("[%s]: Parsing alert levels configuration."
			% fileName)
		for item in configRoot.find("alertLevels").iterfind("alertLevel"):

			alertLevel = AlertLevel()

			alertLevel.level = int(item.find("general").attrib["level"])
			alertLevel.name = str(item.find("general").attrib["name"])
			alertLevel.triggerAlways = (str(item.find("general").attrib[
				"triggerAlways"]).upper() == "TRUE")
			alertLevel.triggerAlertTriggered = (
				str(item.find("general").attrib[
				"triggerAlertTriggered"]).upper() == "TRUE")
			alertLevel.triggerAlertNormal = (str(item.find("general").attrib[
				"triggerAlertNormal"]).upper() == "TRUE")

			# check if rules are activated
			# => parse rules
			alertLevel.rulesActivated = (str(item.find("rules").attrib[
				"activated"]).upper() == "TRUE")
			if alertLevel.rulesActivated:

				# a list of flags that indicates if the rule is valid or
				# invalid when it is used alone => one of the rules have to
				# be valid in order for the rule chain to be valid
				# NOTE: the rule engine works event based, this means that
				# at least one sensor has to be in the rule chain that
				# is not negated by a NOT
				rulesValid = list()

				rulesRoot = item.find("rules")

				# parse all rule tags
				for firstRule in rulesRoot.iterfind("rule"):

					# get start of the rule
					orRule = firstRule.find("or")
					andRule = firstRule.find("and")
					notRule = firstRule.find("not")
					sensorRule = firstRule.find("sensor")
					weekdayRule = firstRule.find("weekday")
					monthdayRule = firstRule.find("monthday")
					hourRule = firstRule.find("hour")
					minuteRule = firstRule.find("minute")
					secondRule = firstRule.find("second")

					# check that only one tag is given in rule
					counter = 0
					if not orRule is None:
						counter += 1
					if not andRule is None:
						counter += 1
					if not notRule is None:
						counter += 1
					if not sensorRule is None:
						counter += 1
					if not weekdayRule is None:
						counter += 1
					if not monthdayRule is None:
						counter += 1
					if not hourRule is None:
						counter += 1
					if not minuteRule is None:
						counter += 1
					if not secondRule is None:
						counter += 1
					if counter != 1:
						raise ValueError("Only one tag "
							+ "is valid as starting part of the rule.")

					# create a wrapper element around the rule element
					# to have meta information (i.e. triggered,
					# time when triggered, etc.)
					ruleElement = RuleStart()

					# get order attribute
					ruleElement.order = int(firstRule.attrib[
						"order"])

					# get minTimeAfterPrev attribute
					ruleElement.minTimeAfterPrev = float(firstRule.attrib[
						"minTimeAfterPrev"])

					# get maxTimeAfterPrev attribute
					ruleElement.maxTimeAfterPrev = float(firstRule.attrib[
						"maxTimeAfterPrev"])

					if (ruleElement.minTimeAfterPrev >
						ruleElement.maxTimeAfterPrev):
						raise ValueError("'minTimeAfterPrev' attribute not "
							+ "allowed to be greater than "
							+ "'maxTimeAfterPrev' attribute in rule tag.")

					# get counterActivated attribute
					ruleElement.counterActivated = (str(firstRule.attrib[
						"counterActivated"]).upper() == "TRUE")

					# only parse counter attributes if it is activated
					if ruleElement.counterActivated:

						# get counterLimit attribute
						ruleElement.counterLimit = int(firstRule.attrib[
						"counterLimit"])

						if ruleElement.counterLimit < 0:
							raise ValueError("'counterLimit' attribute "
							+ "not allowed to be smaller than 0.")

						# get counterWaitTime attribute
						ruleElement.counterWaitTime = int(firstRule.attrib[
						"counterWaitTime"])

						if ruleElement.counterWaitTime < 0:
							raise ValueError("'counterWaitTime' attribute "
							+ "not allowed to be smaller than 0.")

					# start parsing the rule
					if not orRule is None:

						ruleStart = RuleBoolean()
						ruleStart.type = "or"

						# fill wrapper element
						ruleElement.type = "boolean"
						ruleElement.element = ruleStart

						ruleValid = parseRuleRecursively(orRule, ruleStart)

						# flag current rule as valid/invalid
						rulesValid.append(ruleValid)

					elif not andRule is None:

						ruleStart = RuleBoolean()
						ruleStart.type = "and"

						# fill wrapper element
						ruleElement.type = "boolean"
						ruleElement.element = ruleStart

						ruleValid = parseRuleRecursively(andRule, ruleStart)

						# flag current rule as valid/invalid
						rulesValid.append(ruleValid)

					elif not notRule is None:

						ruleStart = RuleBoolean()
						ruleStart.type = "not"

						# fill wrapper element
						ruleElement.type = "boolean"
						ruleElement.element = ruleStart

						parseRuleRecursively(notRule, ruleStart)

						# flag current rule as invalid
						rulesValid.append(False)

					elif not sensorRule is None:

						ruleSensorNew = RuleSensor()
						ruleSensorNew.username = str(sensorRule.attrib[
							"username"])
						ruleSensorNew.remoteSensorId = int(sensorRule.attrib[
							"remoteSensorId"])

						# fill wrapper element
						ruleElement.type = "sensor"
						ruleElement.element = ruleSensorNew
						ruleElement.timeTriggeredFor = float(
							sensorRule.attrib["timeTriggeredFor"])

						# flag current rule as valid
						rulesValid.append(True)

					elif not weekdayRule is None:

						ruleWeekdayNew = RuleWeekday()

						# get time attribute and check if valid
						ruleWeekdayNew.time = str(weekdayRule.attrib["time"])
						if (ruleWeekdayNew.time != "local" and
							ruleWeekdayNew.time != "utc"):
							raise ValueError("No valid value for 'time' "
								+ "attribute in weekday tag.")

						# get weekday attribute and check if valid
						ruleWeekdayNew.weekday = int(weekdayRule.attrib[
							"weekday"])
						if (ruleWeekdayNew.weekday < 0 or
							ruleWeekdayNew.weekday > 6):
							raise ValueError("No valid value for 'weekday' "
								+ "attribute in weekday tag.")

						# fill wrapper element
						ruleElement.type = "weekday"
						ruleElement.element = ruleWeekdayNew

						# flag current rule as invalid
						rulesValid.append(False)

					elif not monthdayRule is None:

						ruleMonthdayNew = RuleMonthday()

						# get time attribute and check if valid
						ruleMonthdayNew.time = str(monthdayRule.attrib["time"])
						if (ruleMonthdayNew.time != "local" and
							ruleMonthdayNew.time != "utc"):
							raise ValueError("No valid value for 'time' "
								+ "attribute in monthday tag.")

						# get monthday attribute and check if valid
						ruleMonthdayNew.monthday = int(monthdayRule.attrib[
							"monthday"])
						if (ruleMonthdayNew.monthday < 1 or
							ruleMonthdayNew.monthday > 31):
							raise ValueError("No valid value for 'monthday' "
								+ "attribute in monthday tag.")

						# fill wrapper element
						ruleElement.type = "monthday"
						ruleElement.element = ruleMonthdayNew

						# flag current rule as invalid
						rulesValid.append(False)

					elif not hourRule is None:

						ruleHourNew = RuleHour()

						# get time attribute and check if valid
						ruleHourNew.time = str(hourRule.attrib["time"])
						if (ruleHourNew.time != "local" and
							ruleHourNew.time != "utc"):
							raise ValueError("No valid value for 'time' "
								+ "attribute in hour tag.")

						# get start attribute and check if valid
						ruleHourNew.start = int(hourRule.attrib[
							"start"])
						if (ruleHourNew.start < 0 or
							ruleHourNew.start > 23):
							raise ValueError("No valid value for 'start' "
								+ "attribute in hour tag.")

						# get end attribute and check if valid
						ruleHourNew.end = int(hourRule.attrib[
							"end"])
						if (ruleHourNew.start < 0 or
							ruleHourNew.start > 23):
							raise ValueError("No valid value for 'end' "
								+ "attribute in hour tag.")

						if ruleHourNew.start > ruleHourNew.end:
							raise ValueError("'start' attribute not allowed "
								+ "to be greater than 'end' attribute in "
								+ "hour tag.")

						# fill wrapper element
						ruleElement.type = "hour"
						ruleElement.element = ruleHourNew

						# flag current rule as invalid
						rulesValid.append(False)

					elif not minuteRule is None:

						ruleMinuteNew = RuleMinute()

						# get start attribute and check if valid
						ruleMinuteNew.start = int(minuteRule.attrib[
							"start"])
						if (ruleMinuteNew.start < 0 or
							ruleMinuteNew.start > 59):
							raise ValueError("No valid value for 'start' "
								+ "attribute in minute tag.")

						# get end attribute and check if valid
						ruleMinuteNew.end = int(minuteRule.attrib[
							"end"])
						if (ruleMinuteNew.start < 0 or
							ruleMinuteNew.start > 59):
							raise ValueError("No valid value for 'end' "
								+ "attribute in minute tag.")

						if ruleMinuteNew.start > ruleMinuteNew.end:
							raise ValueError("'start' attribute not allowed "
								+ "to be greater than 'end' attribute in "
								+ "minute tag.")

						# fill wrapper element
						ruleElement.type = "minute"
						ruleElement.element = ruleMinuteNew

						# flag current rule as invalid
						rulesValid.append(False)

					elif not secondRule is None:

						ruleSecondNew = RuleSecond()

						# get start attribute and check if valid
						ruleSecondNew.start = int(secondRule.attrib[
							"start"])
						if (ruleSecondNew.start < 0 or
							ruleSecondNew.start > 59):
							raise ValueError("No valid value for 'start' "
								+ "attribute in second tag.")

						# get end attribute and check if valid
						ruleSecondNew.end = int(secondRule.attrib[
							"end"])
						if (ruleSecondNew.start < 0 or
							ruleSecondNew.start > 59):
							raise ValueError("No valid value for 'end' "
								+ "attribute in second tag.")

						if ruleSecondNew.start > ruleSecondNew.end:
							raise ValueError("'start' attribute not allowed "
								+ "to be greater than 'end' attribute in "
								+ "second tag.")

						# fill wrapper element
						ruleElement.type = "second"
						ruleElement.element = ruleSecondNew

						# flag current rule as invalid
						rulesValid.append(False)

					else:
						raise ValueError("No valid tag was found.")

					# check if order of all rules only exists once
					for existingRule in alertLevel.rules:
						if existingRule.order == ruleElement.order:
							raise ValueError("Order of rule must be unique.")

					alertLevel.rules.append(ruleElement)

				# check if any of the rules in this rule chain is valid
				# => if not the rule chain is not valid
				if not any(rulesValid):
					raise ValueError("Rule chain for alert level '%d' "
						% alertLevel.level
						+ "is not valid.")

				# sort rules by order
				alertLevel.rules.sort(key=lambda x: x.order)

				# check if parsed rules should be logged
				if (globalData.loglevel == logging.INFO
					or globalData.loglevel == logging.DEBUG):

					globalData.logger.info("[%s]: Parsed rules for alert "
						% fileName
						+ "level %d."
						% alertLevel.level)

					for ruleElement in alertLevel.rules:
						logRule(ruleElement, 0, fileName)

			# check if the alert level only exists once
			for tempAlertLevel in globalData.alertLevels:
				if tempAlertLevel.level == alertLevel.level:
					raise ValueError("Alert level must be unique.")

			globalData.alertLevels.append(alertLevel)

		# check if all alert levels for alert clients that exist in the
		# database are configured in the configuration file
		alertLevelsInDb = globalData.storage.getAllAlertsAlertLevels()
		if alertLevelsInDb == None:
			raise ValueError("Could not get alert client "
				+ "alert levels from database.")
		for alertLevelInDb in alertLevelsInDb:
			found = False
			for alertLevel in globalData.alertLevels:
				if alertLevelInDb[0] == alertLevel.level:
					found = True
					break
			if found:
				continue
			else:
				raise ValueError("An alert level for an alert client exists "
					+ "in the database that is not configured.")

		# check if all alert levels for sensors that exist in the
		# database are configured in the configuration file
		alertLevelsInDb = globalData.storage.getAllSensorsAlertLevels()
		if alertLevelsInDb == None:
			raise ValueError("Could not get sensor alert "
				+ "levels from database.")
		for alertLevelInDb in alertLevelsInDb:
			found = False
			for alertLevel in globalData.alertLevels:
				if alertLevelInDb[0] == alertLevel.level:
					found = True
					break
			if found:
				continue
			else:
				raise ValueError("An alert level for a sensor exists "
					+ "in the database that is not configured.")

		# Parse internal server sensors
		globalData.logger.debug("[%s]: Parsing internal sensors configuration."
			% fileName)
		internalSensorsCfg = configRoot.find("internalSensors")
		dbSensors = list()
		dbInitialStateList = list()

		# Parse sensor timeout sensor (if activated).
		item = internalSensorsCfg.find("sensorTimeout")
		if (str(item.attrib["activated"]).upper() == "TRUE"):

			sensor = SensorTimeoutSensor()

			sensor.nodeId = serverNodeId
			sensor.alertDelay = 0
			sensor.state = 0
			sensor.lastStateUpdated = int(time.time())
			sensor.description = str(item.attrib["description"])

			# Sensor timeout sensor has always this fix internal id
			# (stored as remoteSensorId).
			sensor.remoteSensorId = 0

			sensor.alertLevels = list()
			for alertLevelXml in item.iterfind("alertLevel"):
				sensor.alertLevels.append(int(alertLevelXml.text))

			globalData.internalSensors.append(sensor)

			# Create sensor dictionary element for database interaction.
			temp = dict()
			temp["clientSensorId"] = sensor.remoteSensorId
			temp["alertDelay"] = sensor.alertDelay
			temp["alertLevels"] = sensor.alertLevels
			temp["description"] = sensor.description
			temp["state"] = 0
			temp["dataType"] = sensor.dataType
			dbSensors.append(temp)

			# Add tuple to db state list to set initial states of the
			# internal sensors.
			dbInitialStateList.append( (sensor.remoteSensorId, 0) )

		# Parse node timeout sensor (if activated).
		item = internalSensorsCfg.find("nodeTimeout")
		if (str(item.attrib["activated"]).upper() == "TRUE"):

			sensor = NodeTimeoutSensor()

			sensor.nodeId = serverNodeId
			sensor.alertDelay = 0
			sensor.state = 0
			sensor.lastStateUpdated = int(time.time())
			sensor.description = str(item.attrib["description"])

			# Node timeout sensor has always this fix internal id
			# (stored as remoteSensorId).
			sensor.remoteSensorId = 1

			sensor.alertLevels = list()
			for alertLevelXml in item.iterfind("alertLevel"):
				sensor.alertLevels.append(int(alertLevelXml.text))

			globalData.internalSensors.append(sensor)

			# Create sensor dictionary element for database interaction.
			temp = dict()
			temp["clientSensorId"] = sensor.remoteSensorId
			temp["alertDelay"] = sensor.alertDelay
			temp["alertLevels"] = sensor.alertLevels
			temp["description"] = sensor.description
			temp["state"] = 0
			temp["dataType"] = sensor.dataType
			dbSensors.append(temp)

			# Add tuple to db state list to set initial states of the
			# internal sensors.
			dbInitialStateList.append( (sensor.remoteSensorId, 0) )

		# Parse alert system active sensor (if activated).
		item = internalSensorsCfg.find("alertSystemActive")
		if (str(item.attrib["activated"]).upper() == "TRUE"):

			sensor = AlertSystemActiveSensor()

			sensor.nodeId = serverNodeId
			sensor.alertDelay = 0
			sensor.state = 0
			sensor.lastStateUpdated = int(time.time())
			sensor.description = str(item.attrib["description"])

			# Alert system active sensor has always this fix internal id
			# (stored as remoteSensorId).
			sensor.remoteSensorId = 2

			sensor.alertLevels = list()
			for alertLevelXml in item.iterfind("alertLevel"):
				sensor.alertLevels.append(int(alertLevelXml.text))

			globalData.internalSensors.append(sensor)

			# Create sensor dictionary element for database interaction.
			temp = dict()
			temp["clientSensorId"] = sensor.remoteSensorId
			temp["alertDelay"] = sensor.alertDelay
			temp["alertLevels"] = sensor.alertLevels
			temp["description"] = sensor.description
			temp["state"] = 0
			temp["dataType"] = sensor.dataType
			dbSensors.append(temp)

			# Set initial state of the internal sensor to the state
			# of the alert system.
			if globalData.storage.isAlertSystemActive():
				initState = 1
			else:
				initState = 0

			# Add tuple to db state list to set initial states of the
			# internal sensors.
			dbInitialStateList.append( (sensor.remoteSensorId, initState) )

		# Parse version informer sensor (if activated).
		item = internalSensorsCfg.find("versionInformer")
		if (str(item.attrib["activated"]).upper() == "TRUE"):

			sensor = VersionInformerSensor()

			sensor.nodeId = serverNodeId
			sensor.alertDelay = 0
			sensor.state = 0
			sensor.lastStateUpdated = int(time.time())
			sensor.description = str(item.attrib["description"])

			# Version informer sensor has always this fix internal id
			# (stored as remoteSensorId).
			sensor.remoteSensorId = 3

			sensor.alertLevels = list()
			for alertLevelXml in item.iterfind("alertLevel"):
				sensor.alertLevels.append(int(alertLevelXml.text))

			globalData.internalSensors.append(sensor)

			# Create sensor dictionary element for database interaction.
			temp = dict()
			temp["clientSensorId"] = sensor.remoteSensorId
			temp["alertDelay"] = sensor.alertDelay
			temp["alertLevels"] = sensor.alertLevels
			temp["description"] = sensor.description
			temp["state"] = 0
			temp["dataType"] = sensor.dataType
			dbSensors.append(temp)

			# Add tuple to db state list to set initial states of the
			# internal sensors.
			dbInitialStateList.append( (sensor.remoteSensorId, 0) )

		# Add internal sensors to database (updates/deletes also old
		# sensor data in the database).
		if not globalData.storage.addSensors(serverUsername, dbSensors):
			raise ValueError("Not able to add internal sensors "
				+ "to database.")

		# get sensor id for each activated internal sensor from the database
		for sensor in globalData.internalSensors:

			sensor.sensorId = globalData.storage.getSensorId(sensor.nodeId,
				sensor.remoteSensorId)
			if sensor.sensorId is None:
				raise ValueError("Not able to get sensor id for "
					+ "internal sensor from database.")

		# Set initial states of the internal sensors.
		globalData.storage.updateSensorState(serverNodeId, dbInitialStateList)

	except Exception as e:
		globalData.logger.exception("[%s]: Could not parse config." % fileName)
		sys.exit(1)

	globalData.logger.debug("[%s]: Parsing configuration succeeded."
		% fileName)

	random.seed()

	# start the thread that handles all sensor alerts
	globalData.logger.info("[%s] Starting sensor alert manage thread."
		% fileName)
	globalData.sensorAlertExecuter = SensorAlertExecuter(globalData)
	# set thread to daemon
	# => threads terminates when main thread terminates
	globalData.sensorAlertExecuter.daemon = True
	globalData.sensorAlertExecuter.start()

	globalData.logger.info("[%s] Starting manager client manage thread."
		% fileName)
	# start the thread that handles the manager updates
	globalData.managerUpdateExecuter = ManagerUpdateExecuter(globalData)
	# set thread to daemon
	# => threads terminates when main thread terminates
	globalData.managerUpdateExecuter.daemon = True
	globalData.managerUpdateExecuter.start()

	# start server process
	while 1:
		try:
			server = ThreadedTCPServer(globalData, ('0.0.0.0', port),
				ServerSession)
			break
		except Exception as e:
			globalData.logger.exception("[%s]: Starting server failed. "
				% fileName
				+ "Try again in 5 seconds.")
			time.sleep(5)

	globalData.logger.info("[%s] Starting server thread." % fileName)
	serverThread = threading.Thread(target=server.serve_forever)
	# set thread to daemon
	# => threads terminates when main thread terminates
	serverThread.daemon =True
	serverThread.start()

	# start a watchdog thread that controls all server sessions
	globalData.logger.info("[%s] Starting connection watchdog thread."
		% fileName)
	globalData.connectionWatchdog = ConnectionWatchdog(globalData,
		globalData.connectionTimeout)
	# set thread to daemon
	# => threads terminates when main thread terminates
	globalData.connectionWatchdog.daemon = True
	globalData.connectionWatchdog.start()

	# Start a watchdog thread that checks all configuration files.
	globalData.logger.info("[%s] Starting config watchdog thread."
		% fileName)
	globalData.configWatchdog = ConfigWatchdog(globalData,
		globalData.configCheckInterval)
	# set thread to daemon
	# => threads terminates when main thread terminates
	globalData.configWatchdog.daemon = True
	globalData.configWatchdog.start()

	# Only start version informer if update check is available.
	if updateActivated is True:
		globalData.logger.info("[%s] Starting version checker thread."
			% fileName)
		versionInformer = VersionInformer(updateServer, updatePort,
			updateLocation, updateCaFile, updateInterval, globalData)
		# set thread to daemon
		# => threads terminates when main thread terminates
		versionInformer.daemon = True
		versionInformer.start()

	# only start survey executer if user wants to participate
	if surveyActivated:
		globalData.logger.info("[%s] Starting survey executer thread."
			% fileName)
		surveyExecuter = SurveyExecuter(updateActivated, updateServer,
			updateLocation, globalData)
		# set thread to daemon
		# => threads terminates when main thread terminates
		surveyExecuter.daemon = True
		surveyExecuter.start()

	globalData.logger.info("[%s] Server started." % fileName)

	# Wait until the connection watchdog is initialized.
	while not globalData.connectionWatchdog.isInitialized():
		time.sleep(0.5)

	# handle requests in an infinity loop
	while True:
		server.handle_request()