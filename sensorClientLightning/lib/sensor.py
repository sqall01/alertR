#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import websocket
import json
import time
import random
import os
import logging
import threading
import calendar
from client import AsynchronousSender
from localObjects import SensorDataType, SensorAlert, StateChange


# internal class that represents a hull around the inner quadrant
class _Hull:

	# quadrants
	innerQuadrant = None
	outerQuadrant = None

	# subquadrants
	sw = None
	s = None
	se = None
	w = None
	e = None
	nw = None
	n = None
	ne = None


# internal class that represents a quadrant on the map
# (depict by two gps coordinates)
class _Quadrant:

	# time the quadrant was hit the last time by a lightning
	timeHit = 0.0

	x1 = None
	y1 = None
	x2 = None
	y2 = None


# internal class that represents a subquadrant of a hull
# (this quadrant also contains a direction)
class _SubQuadrant(_Quadrant):
	direction = None


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


# class that represents one quadrant that is watched by the system
class LightningmapSensor(_PollingSensor, threading.Thread):

	def __init__(self, lat, lon):
		threading.Thread.__init__(self)
		_PollingSensor.__init__(self)

		# Set sensor to not hold any data.
		self.sensorDataType = SensorDataType.NONE

		# used for logging
		self.fileName = os.path.basename(__file__)

		# factors used to calculate the hull of the home quadrant
		# (chosen by empirical tests)
		self.factorLat = 0.4
		self.factorLon = 0.4

		# how old (in seconds) a lightning can be before it is discarded
		# (value chosen by empirical tests)
		self.strokeTimeTolerance = 20

		# generate home quadrant from given gps coordinates
		# (values chosen by empirical tests)
		self.homeQuadrant = _Quadrant()
		self.homeQuadrant.y1 = lat - 0.09
		self.homeQuadrant.x1 = lon - 0.1
		self.homeQuadrant.y2 = lat + 0.09
		self.homeQuadrant.x2 = lon + 0.1

		# sanity check for home quadrant
		if self.homeQuadrant.y1 > self.homeQuadrant.y2:
			raise ValueError("Left down latitude of home quadrant "
				+ "greater than right upper latitude of home quadrant.")
		if self.homeQuadrant.x1 > self.homeQuadrant.x2:
			raise ValueError("Left down longitude of home quadrant "
				+ "greater than right upper longitude of home quadrant.")

		# inner and outer hull are needed to determine lightning position
		self.outerHull = None
		self.innerHull = None

		# time in seconds that have to passed before the
		# hit stroke does not count as sensor trigger anymore
		self.lightningTime = None

		# internal variables to manage two different kinds of
		# alerts by this sensor
		self._lastTriggeredHome = 0.0
		self._lastTriggeredHull = 0.0

		self._triggerHomeNext = False
		self._triggerHullNext = False

		self._currentHomeMessage = ""
		self._currentHullMessage = ""


	# internal function that checks if the lightning occurred
	# inside the quadrant
	def _checkCoordInQuadrant(self, quadrant, lat, lon):

		if (quadrant.x1 <= lon
			and quadrant.y1 <= lat
			and quadrant.x2 >= lon
			and quadrant.y2 >= lat):
			return True

		else:
			return False


	# internal function that gets the direction of the last lightning
	# that hit the hull
	def _getDirectionOfLastHit(self, hull):

		newestHit = 0.0

		direction = "unknown"
		if newestHit < hull.sw.timeHit:
			newestHit = hull.sw.timeHit
			direction = "sw"

		if newestHit < hull.s.timeHit:
			newestHit = hull.s.timeHit
			direction = "s"

		if newestHit < hull.se.timeHit:
			newestHit = hull.se.timeHit
			direction = "se"

		if newestHit < hull.w.timeHit:
			newestHit = hull.w.timeHit
			direction = "w"

		if newestHit < hull.e.timeHit:
			newestHit = hull.e.timeHit
			direction = "e"

		if newestHit < hull.nw.timeHit:
			newestHit = hull.nw.timeHit
			direction = "nw"

		if newestHit < hull.n.timeHit:
			newestHit = hull.n.timeHit
			direction = "n"

		if newestHit < hull.ne.timeHit:
			newestHit = hull.ne.timeHit
			direction = "ne"

		return direction


	def _convertDirectionToString(self, direction):
		if direction == "sw":
			return "southwest"
		elif direction == "s":
			return "south"
		elif direction == "se":
			return "southeast"
		elif direction == "w":
			return "west"
		elif direction == "e":
			return "east"
		elif direction == "nw":
			return "northwest"
		elif direction == "n":
			return "north"
		elif direction == "ne":
			return "northeast"
		else:
			return "unknown"


	def initializeSensor(self):
		self.changeState = True
		self.hasLatestData = False
		self.state = 1 - self.triggerState

		# calculate quadrant around home quadrant
		outerQuadrant = _Quadrant()
		outerQuadrant.y1 = self.homeQuadrant.y1 - self.factorLat
		outerQuadrant.x1 = self.homeQuadrant.x1 - self.factorLon
		outerQuadrant.y2 = self.homeQuadrant.y2 + self.factorLat
		outerQuadrant.x2 = self.homeQuadrant.x2 + self.factorLon

		# calculate quadrant between outer and home quadrant
		middleQudrant = _Quadrant()
		middleQudrant.y1 = self.homeQuadrant.y1 - (self.factorLat/2)
		middleQudrant.x1 = self.homeQuadrant.x1 - (self.factorLon/2)
		middleQudrant.y2 = self.homeQuadrant.y2 + (self.factorLat/2)
		middleQudrant.x2 = self.homeQuadrant.x2 + (self.factorLon/2)


		# generate outer hull
		self.outerHull = _Hull()
		self.outerHull.innerQuadrant = middleQudrant
		self.outerHull.outerQuadrant = outerQuadrant

		# SW
		self.outerHull.sw = _SubQuadrant()
		self.outerHull.sw.direction = "SW"
		self.outerHull.sw.y1 = outerQuadrant.y1
		self.outerHull.sw.x1 = outerQuadrant.x1
		self.outerHull.sw.y2 = middleQudrant.y1
		self.outerHull.sw.x2 = middleQudrant.x1

		# S
		self.outerHull.s = _SubQuadrant()
		self.outerHull.s.direction = "S"
		self.outerHull.s.y1 = outerQuadrant.y1
		self.outerHull.s.x1 = middleQudrant.x1
		self.outerHull.s.y2 = middleQudrant.y1
		self.outerHull.s.x2 = middleQudrant.x2

		# SE
		self.outerHull.se = _SubQuadrant()
		self.outerHull.se.direction = "SE"
		self.outerHull.se.y1 = outerQuadrant.y1
		self.outerHull.se.x1 = middleQudrant.x2
		self.outerHull.se.y2 = middleQudrant.y1
		self.outerHull.se.x2 = outerQuadrant.x2

		# W
		self.outerHull.w = _SubQuadrant()
		self.outerHull.w.direction = "W"
		self.outerHull.w.y1 = middleQudrant.y1
		self.outerHull.w.x1 = outerQuadrant.x1
		self.outerHull.w.y2 = middleQudrant.y2
		self.outerHull.w.x2 = middleQudrant.x1

		# E
		self.outerHull.e = _SubQuadrant()
		self.outerHull.e.direction = "E"
		self.outerHull.e.y1 = middleQudrant.y1
		self.outerHull.e.x1 = middleQudrant.x2
		self.outerHull.e.y2 = middleQudrant.y2
		self.outerHull.e.x2 = outerQuadrant.x2

		# NW
		self.outerHull.nw = _SubQuadrant()
		self.outerHull.nw.direction = "NW"
		self.outerHull.nw.y1 = middleQudrant.y2
		self.outerHull.nw.x1 = outerQuadrant.x1
		self.outerHull.nw.y2 = outerQuadrant.y2
		self.outerHull.nw.x2 = middleQudrant.x1

		# N
		self.outerHull.n = _SubQuadrant()
		self.outerHull.n.direction = "N"
		self.outerHull.n.y1 = middleQudrant.y2
		self.outerHull.n.x1 = middleQudrant.x1
		self.outerHull.n.y2 = outerQuadrant.y2
		self.outerHull.n.x2 = middleQudrant.x2

		# NE
		self.outerHull.ne = _SubQuadrant()
		self.outerHull.ne.direction = "NE"
		self.outerHull.ne.y1 = middleQudrant.y2
		self.outerHull.ne.x1 = middleQudrant.x2
		self.outerHull.ne.y2 = outerQuadrant.y2
		self.outerHull.ne.x2 = outerQuadrant.x2


		# generate inner hull
		self.innerHull = _Hull()
		self.innerHull.innerQuadrant = self.homeQuadrant
		self.innerHull.outerQuadrant = middleQudrant

		# SW
		self.innerHull.sw = _SubQuadrant()
		self.innerHull.sw.direction = "SW"
		self.innerHull.sw.y1 = middleQudrant.y1
		self.innerHull.sw.x1 = middleQudrant.x1
		self.innerHull.sw.y2 = self.homeQuadrant.y1
		self.innerHull.sw.x2 = self.homeQuadrant.x1

		# S
		self.innerHull.s = _SubQuadrant()
		self.innerHull.s.direction = "S"
		self.innerHull.s.y1 = middleQudrant.y1
		self.innerHull.s.x1 = self.homeQuadrant.x1
		self.innerHull.s.y2 = self.homeQuadrant.y1
		self.innerHull.s.x2 = self.homeQuadrant.x2

		# SE
		self.innerHull.se = _SubQuadrant()
		self.innerHull.se.direction = "SE"
		self.innerHull.se.y1 = middleQudrant.y1
		self.innerHull.se.x1 = self.homeQuadrant.x2
		self.innerHull.se.y2 = self.homeQuadrant.y1
		self.innerHull.se.x2 = middleQudrant.x2

		# W
		self.innerHull.w = _SubQuadrant()
		self.innerHull.w.direction = "W"
		self.innerHull.w.y1 = self.homeQuadrant.y1
		self.innerHull.w.x1 = middleQudrant.x1
		self.innerHull.w.y2 = self.homeQuadrant.y2
		self.innerHull.w.x2 = self.homeQuadrant.x1

		# E
		self.innerHull.e = _SubQuadrant()
		self.innerHull.e.direction = "E"
		self.innerHull.e.y1 = self.homeQuadrant.y1
		self.innerHull.e.x1 = self.homeQuadrant.x2
		self.innerHull.e.y2 = self.homeQuadrant.y2
		self.innerHull.e.x2 = middleQudrant.x2

		# NW
		self.innerHull.nw = _SubQuadrant()
		self.innerHull.nw.direction = "NW"
		self.innerHull.nw.y1 = self.homeQuadrant.y2
		self.innerHull.nw.x1 = middleQudrant.x1
		self.innerHull.nw.y2 = middleQudrant.y2
		self.innerHull.nw.x2 = self.homeQuadrant.x1

		# N
		self.innerHull.n = _SubQuadrant()
		self.innerHull.n.direction = "N"
		self.innerHull.n.y1 = self.homeQuadrant.y2
		self.innerHull.n.x1 = self.homeQuadrant.x1
		self.innerHull.n.y2 = middleQudrant.y2
		self.innerHull.n.x2 = self.homeQuadrant.x2

		# NE
		self.innerHull.ne = _SubQuadrant()
		self.innerHull.ne.direction = "NE"
		self.innerHull.ne.y1 = self.homeQuadrant.y2
		self.innerHull.ne.x1 = self.homeQuadrant.x2
		self.innerHull.ne.y2 = middleQudrant.y2
		self.innerHull.ne.x2 = middleQudrant.x2

		return True


	def getState(self):
		return self.state


	def updateState(self):

		# check if a hit in the home quadrant has to be triggered
		if self._triggerHomeNext:

			# clear flag to trigger alert for a hit in home quadrant next
			self._triggerHomeNext = False

			# clear flag to trigger alert for a hit in the hull next
			self._triggerHullNext = False

			# set sensor as triggered
			self.state = self.triggerState

			self.hasOptionalData = True
			self.optionalData = {"message": self._currentHomeMessage}

			return

		# check if a hit in the hull has to be triggered
		# (can only be triggered if hit in home quadrant is not triggered)
		elif self._triggerHullNext:

			# clear flag to trigger alert for a hit in the hull next
			self._triggerHullNext = False

			# set sensor as triggered
			self.state = self.triggerState

			self.hasOptionalData = True
			self.optionalData = {"message": self._currentHullMessage}

			return


		now = calendar.timegm(time.gmtime())


		# check if last time the home quadrant was triggered
		# is OLDER than the configured lightning time
		if (now - self._lastTriggeredHome) > self.lightningTime:

			# set sensor as not triggered
			self.state = 1 - self.triggerState

			# clear data transfer
			self.hasOptionalData = False
			self.optionalData = None

			# check if last time the home quadrant was hit
			# is YOUNGER than the configured lightning time
			# => an alert for a hit in the home quadrant was not yet triggered
			# and has to be triggered next
			if ((now - self.innerHull.innerQuadrant.timeHit)
				< self.lightningTime):

				# set flag to trigger alert for a hit in home quadrant next
				self._triggerHomeNext = True

				# set hull and home quadrant trigger time to now
				self._lastTriggeredHome = now
				self._lastTriggeredHull = now


		# check if last time the hull was triggered
		# is OLDER than the configured lightning time
		if (now - self._lastTriggeredHull) > self.lightningTime:

			# set sensor as not triggered
			self.state = 1 - self.triggerState

			# clear data transfer
			self.hasOptionalData = False
			self.optionalData = None

			# check if last time the hull was hit
			# is YOUNGER than the configured lightning time
			# => an alert for a hit in the home quadrant was not yet triggered
			# and has to be triggered next
			if ((now - self.innerHull.outerQuadrant.timeHit)
				< self.lightningTime):

				# set flag to trigger alert for a hit in the hull next
				self._triggerHullNext = True

				# set hull trigger time to now
				self._lastTriggeredHull = now


	def forceSendAlert(self):
		return None


	def forceSendState(self):
		return None


	def processData(self, data):

		# parse received data
		try:
			dataJson = json.loads(data)
		except Exception as e:
			logging.exception("[%s]: Received data not in json format."
				% self.fileName)
			return

		# check if the key "strokes" exist
		if not "strokes" in dataJson.keys():
			logging.warning("[%s]: Received data does "
				% self.fileName
				+ "not contain 'strokes'.")
			return


		# process each lightning of the received data
		for stroke in dataJson["strokes"]:

			# utc time stamp is given in ms => lower the precision
			strokeTime = stroke["time"] / 1000

			# get current utc time stamp
			now = calendar.timegm(time.gmtime())

			# skip stroke if it is too old
			if (now - strokeTime) > self.strokeTimeTolerance:
				logging.warning("[%s]: Received lightning is too old (%ds)."
					% (self.fileName, (now - strokeTime)))
				continue


			# check if stroke occurred in home quadrant
			# => thunderstorm reached home quadrant
			if self._checkCoordInQuadrant(self.innerHull.innerQuadrant,
				stroke["lat"], stroke["lon"]):

				logging.debug("[%s]: Sensor '%s': "
					% (self.fileName, self.description)
					+ "Stroke hit home quadrant.")

				# check if last occured lightning in home quadrant
				# is older than the configured lightning time
				if ((strokeTime - self.innerHull.innerQuadrant.timeHit)
					> self.lightningTime):

					# check if last occured lightning in hull of home quadrant
					# is older than the configured lightning time
					# => thunderstorm could have started in home quadrant
					if ((strokeTime - self.innerHull.outerQuadrant.timeHit)
						> self.lightningTime):

						# check if last occured lightning in outer hull
						# is older than the configured lightning time
						# => thunderstorm started in home quadrant
						if ((strokeTime - self.outerHull.outerQuadrant.timeHit)
							> self.lightningTime):

							self._currentHomeMessage = \
								"Thunderstorm started in home quadrant"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "started in home quadrant.")

						# => thunderstorm skipped hull of home quadrant
						else:

							# get direction from which thunderstorm approached
							direction = self._getDirectionOfLastHit(
								self.outerHull)

							self._currentHomeMessage = \
								"Thunderstorm reached from the %s" \
								% self._convertDirectionToString(direction)

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "reached home quadrant from the %s."
								% self._convertDirectionToString(direction))

					# => thunderstorm reached home quadrant
					else:

						# get direction from which thunderstorm approached
						direction = self._getDirectionOfLastHit(self.innerHull)

						self._currentHomeMessage = \
							"Thunderstorm reached from the %s" \
							% self._convertDirectionToString(direction)

						logging.info("[%s]: Sensor '%s': Thunderstorm "
							% (self.fileName, self.description)
							+ "reached home quadrant from the %s."
							% self._convertDirectionToString(direction))

				self.outerHull.outerQuadrant.timeHit = strokeTime
				self.innerHull.outerQuadrant.timeHit = strokeTime
				self.innerHull.innerQuadrant.timeHit = strokeTime


			# check if stroke occured in hull of home quadrant
			# => thunderstorm approaching home quadrant
			elif self._checkCoordInQuadrant(self.innerHull.outerQuadrant,
				stroke["lat"], stroke["lon"]):

				logging.debug("[%s]: Sensor '%s': "
					% (self.fileName, self.description)
					+ "Stroke hit inner hull.")

				# check if sw quadrant was hit
				if self._checkCoordInQuadrant(self.innerHull.sw,
					stroke["lat"], stroke["lon"]):

					# check if last occured lightning in hull of home quadrant
					# is older than the configured lightning time
					if ((strokeTime - self.innerHull.outerQuadrant.timeHit)
						> self.lightningTime):

						# check if last occured lightning in outer hull
						# is older than the configured lightning time
						# => thunderstorm started in hull of home quadrant
						if ((strokeTime - self.outerHull.outerQuadrant.timeHit)
							> self.lightningTime):

							self._currentHullMessage = \
								"Thunderstorm started in the southwest"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "started in hull in the southwest.")

						# => thunderstorm approaching
						else:

							self._currentHullMessage = \
								"Thunderstorm approaches from the southwest"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "approaches from the southwest.")

					# update hit time
					self.innerHull.sw.timeHit = strokeTime


				# check if s quadrant was hit
				elif self._checkCoordInQuadrant(self.innerHull.s,
					stroke["lat"], stroke["lon"]):

					# check if last occured lightning in hull of home quadrant
					# is older than the configured lightning time
					if ((strokeTime - self.innerHull.outerQuadrant.timeHit)
						> self.lightningTime):

						# check if last occured lightning in outer hull
						# is older than the configured lightning time
						# => thunderstorm started in hull of home quadrant
						if ((strokeTime - self.outerHull.outerQuadrant.timeHit)
							> self.lightningTime):

							self._currentHullMessage = \
								"Thunderstorm started in the south"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "started in hull in the south.")

						# => thunderstorm approaching
						else:

							self._currentHullMessage = \
								"Thunderstorm approaches from the south"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "approaches from the south.")

					# update hit time
					self.innerHull.s.timeHit = strokeTime


				# check if se quadrant was hit
				elif self._checkCoordInQuadrant(self.innerHull.se,
					stroke["lat"], stroke["lon"]):

					# check if last occured lightning in hull of home quadrant
					# is older than the configured lightning time
					if ((strokeTime - self.innerHull.outerQuadrant.timeHit)
						> self.lightningTime):

						# check if last occured lightning in outer hull
						# is older than the configured lightning time
						# => thunderstorm started in hull of home quadrant
						if ((strokeTime - self.outerHull.outerQuadrant.timeHit)
							> self.lightningTime):

							self._currentHullMessage = \
								"Thunderstorm started in the southeast"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "started in hull in the southeast.")

						# => thunderstorm approaching
						else:

							self._currentHullMessage = \
								"Thunderstorm approaches from the southeast"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "approaches from the southeast.")

					# update hit time
					self.innerHull.se.timeHit = strokeTime


				# check if w quadrant was hit
				elif self._checkCoordInQuadrant(self.innerHull.w,
					stroke["lat"], stroke["lon"]):

					# check if last occured lightning in hull of home quadrant
					# is older than the configured lightning time
					if ((strokeTime - self.innerHull.outerQuadrant.timeHit)
						> self.lightningTime):

						# check if last occured lightning in outer hull
						# is older than the configured lightning time
						# => thunderstorm started in hull of home quadrant
						if ((strokeTime - self.outerHull.outerQuadrant.timeHit)
							> self.lightningTime):

							self._currentHullMessage = \
								"Thunderstorm started in the west"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "started in hull in the west.")

						# => thunderstorm approaching
						else:

							self._currentHullMessage = \
								"Thunderstorm approaches from the west"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "approaches from the west.")

					# update hit time
					self.innerHull.w.timeHit = strokeTime


				# check if e quadrant was hit
				elif self._checkCoordInQuadrant(self.innerHull.e,
					stroke["lat"], stroke["lon"]):

					# check if last occured lightning in hull of home quadrant
					# is older than the configured lightning time
					if ((strokeTime - self.innerHull.outerQuadrant.timeHit)
						> self.lightningTime):

						# check if last occured lightning in outer hull
						# is older than the configured lightning time
						# => thunderstorm started in hull of home quadrant
						if ((strokeTime - self.outerHull.outerQuadrant.timeHit)
							> self.lightningTime):

							self._currentHullMessage = \
								"Thunderstorm started in the east"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "started in hull in the east.")

						# => thunderstorm approaching
						else:

							self._currentHullMessage = \
								"Thunderstorm approaches from the east"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "approaches from the east.")

					# update hit time
					self.innerHull.e.timeHit = strokeTime


				# check if nw quadrant was hit
				elif self._checkCoordInQuadrant(self.innerHull.nw,
					stroke["lat"], stroke["lon"]):

					# check if last occured lightning in hull of home quadrant
					# is older than the configured lightning time
					if ((strokeTime - self.innerHull.outerQuadrant.timeHit)
						> self.lightningTime):

						# check if last occured lightning in outer hull
						# is older than the configured lightning time
						# => thunderstorm started in hull of home quadrant
						if ((strokeTime - self.outerHull.outerQuadrant.timeHit)
							> self.lightningTime):

							self._currentHullMessage = \
								"Thunderstorm started in the northwest"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "started in hull in the northwest.")

						# => thunderstorm approaching
						else:

							self._currentHullMessage = \
								"Thunderstorm approaches from the northwest"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "approaches from the northwest.")

					# update hit time
					self.innerHull.nw.timeHit = strokeTime


				# check if n quadrant was hit
				elif self._checkCoordInQuadrant(self.innerHull.n,
					stroke["lat"], stroke["lon"]):

					# check if last occured lightning in hull of home quadrant
					# is older than the configured lightning time
					if ((strokeTime - self.innerHull.outerQuadrant.timeHit)
						> self.lightningTime):

						# check if last occured lightning in outer hull
						# is older than the configured lightning time
						# => thunderstorm started in hull of home quadrant
						if ((strokeTime - self.outerHull.outerQuadrant.timeHit)
							> self.lightningTime):

							self._currentHullMessage = \
								"Thunderstorm started in the north"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "started in hull in the north.")

						# => thunderstorm approaching
						else:

							self._currentHullMessage = \
								"Thunderstorm approaches from the north"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "approaches from the north.")

					# update hit time
					self.innerHull.n.timeHit = strokeTime


				# check if ne quadrant was hit
				elif self._checkCoordInQuadrant(self.innerHull.ne,
					stroke["lat"], stroke["lon"]):

					# check if last occured lightning in hull of home quadrant
					# is older than the configured lightning time
					if ((strokeTime - self.innerHull.outerQuadrant.timeHit)
						> self.lightningTime):

						# check if last occured lightning in outer hull
						# is older than the configured lightning time
						# => thunderstorm started in hull of home quadrant
						if ((strokeTime - self.outerHull.outerQuadrant.timeHit)
							> self.lightningTime):

							self._currentHullMessage = \
								"Thunderstorm started in the northeast"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "started in hull in the northeast.")

						# => thunderstorm approaching
						else:

							self._currentHullMessage = \
								"Thunderstorm approaches from the northeast"

							logging.info("[%s]: Sensor '%s': Thunderstorm "
								% (self.fileName, self.description)
								+ "approaches from the northeast.")

					# update hit time
					self.innerHull.ne.timeHit = strokeTime


				else:

					logging.error("[%s]: Sensor '%s': No "
						% (self.fileName, self.description)
						+ "direction in inner hull found.")


				# update time when hit
				self.outerHull.outerQuadrant.timeHit = strokeTime
				self.innerHull.outerQuadrant.timeHit = strokeTime


			# check if stroke occured in outer hull
			# => thunderstorm not yet at home quadrant
			elif self._checkCoordInQuadrant(self.outerHull.outerQuadrant,
				stroke["lat"], stroke["lon"]):

				logging.debug("[%s]: Sensor '%s': "
					% (self.fileName, self.description)
					+ "Stroke hit outer hull.")

				# check if sw quadrant was hit
				if self._checkCoordInQuadrant(self.outerHull.sw,
					stroke["lat"], stroke["lon"]):

					# update hit time
					self.outerHull.sw.timeHit = strokeTime

				# check if s quadrant was hit
				elif self._checkCoordInQuadrant(self.outerHull.s,
					stroke["lat"], stroke["lon"]):

					# update hit time
					self.outerHull.s.timeHit = strokeTime

				# check if se quadrant was hit
				elif self._checkCoordInQuadrant(self.outerHull.se,
					stroke["lat"], stroke["lon"]):

					# update hit time
					self.outerHull.se.timeHit = strokeTime

				# check if w quadrant was hit
				elif self._checkCoordInQuadrant(self.outerHull.w,
					stroke["lat"], stroke["lon"]):

					# update hit time
					self.outerHull.w.timeHit = strokeTime

				# check if e quadrant was hit
				elif self._checkCoordInQuadrant(self.outerHull.e,
					stroke["lat"], stroke["lon"]):

					# update hit time
					self.outerHull.e.timeHit = strokeTime

				# check if nw quadrant was hit
				elif self._checkCoordInQuadrant(self.outerHull.nw,
					stroke["lat"], stroke["lon"]):

					# update hit time
					self.outerHull.nw.timeHit = strokeTime

				# check if n quadrant was hit
				elif self._checkCoordInQuadrant(self.outerHull.n,
					stroke["lat"], stroke["lon"]):

					# update hit time
					self.outerHull.n.timeHit = strokeTime

				# check if ne quadrant was hit
				elif self._checkCoordInQuadrant(self.outerHull.ne,
					stroke["lat"], stroke["lon"]):

					# update hit time
					self.outerHull.ne.timeHit = strokeTime

				else:

					logging.error("[%s]: Sensor '%s': No "
						% (self.fileName, self.description)
						+ "direction in outer hull found.")


				self.outerHull.outerQuadrant.timeHit = strokeTime


# class that collects lightning data from lightningmaps.org
class LightningmapDataCollector(threading.Thread):

	def __init__(self, sensors):
		threading.Thread.__init__(self)

		# used for logging
		self.fileName = os.path.basename(__file__)

		self.connection = None
		self.sensors = sensors

		# addresses for websocket connections to lightningmaps.org
		self.addresses = ["ws://ws.lightningmaps.org:8081",
			"ws://ws.lightningmaps.org:8080",
			"ws://ws.lightningmaps.org:8082"]


	# connect to lightningmaps.org server
	def connect(self):

		# connect to randomly selected lightningmaps.org server
		# until a connection is successful
		while True:
			try:
				randIdx = random.randint(0, len(self.addresses) - 1)

				logging.info("[%s]: Connecting to '%s'."
					% (self.fileName, self.addresses[randIdx]))

				self.connection = websocket.create_connection(
					self.addresses[randIdx])

				break

			except Exception as e:
				logging.exception("[%s]: Connection to '%s' "
					% (self.fileName, self.addresses[randIdx])
					+ "failed.")

				time.sleep(5)


	def run(self):

		while True:

			self.connect()

			while True:

				# receive data from websocket (break if it fails)
				try:
					data = self.connection.recv()
				except Exception as e:
					logging.exception("[%s]: Receiving data from "
						% self.fileName
						+ "websocket failed.")

					break
				if data == "":
					break

				# give received data to each sensor for processing
				for sensor in self.sensors:
					sensor.processData(data)

			# close websocket connection and reconnect
			try:
				self.connection.close()
			except:
				pass


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
							+ "for normal state "
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