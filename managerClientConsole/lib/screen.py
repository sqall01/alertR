#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import threading
import logging
import os
import time
import urwid


# this class is used by the urwid console thread
# to process actions concurrently and do not block the console thread
class ScreenActionExecuter(threading.Thread):

	def __init__(self, globalData):
		threading.Thread.__init__(self)

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# get global configured data
		self.globalData = globalData
		self.serverComm = self.globalData.serverComm

		# this options are used when the thread should
		# send a new option to the server
		self.sendOption = False
		self.optionType = None
		self.optionValue = None


	def run(self):

		# check if an option message should be send to the server
		if self.sendOption:

			# check if the server communication object is available
			if self.serverComm is None:
				logging.error("[%s]: Sending option " % self.fileName
						+ "change to server failed. No server communication "
						+ "object available.")
				return

			# send option change to server
			if not self.serverComm.sendOption(self.optionType,
				self.optionValue):
				logging.error("[%s]: Sending option " % self.fileName
					+ "change to server failed.")
				return


# this class handles the screen updates
class ScreenUpdater(threading.Thread):

	def __init__(self, globalData):
		threading.Thread.__init__(self)

		# get global configured data
		self.globalData = globalData
		self.sensorAlerts = self.globalData.sensorAlerts
		self.console = self.globalData.console
		self.serverComm = self.globalData.serverComm

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# create an event that is used to wake this thread up
		# and update the screen
		self.screenUpdaterEvent = threading.Event()
		self.screenUpdaterEvent.clear()

		# set exit flag as false
		self.exitFlag = False


	def run(self):

		while 1:
			if self.exitFlag:
				return

			# wait until thread is woken up by an event to update the screen
			# or 10 seconds elapsed
			self.screenUpdaterEvent.wait(10)
			self.screenUpdaterEvent.clear()

			# if reference to console object does not exist
			# => get it from global data or if it does not exist continue loop
			if self.console == None:
				if self.globalData.console != None:
					self.console = self.globalData.console
				else:
					continue			

			# check if a sensor alert was received
			# => update screen with sensor alert
			if len(self.sensorAlerts) != 0:
				logging.info("[%s]: Updating screen with sensor alert."
					% self.fileName)
				if not self.console.updateScreen("sensoralert"):
					logging.error("[%s]: Updating screen " % self.fileName
						+ "with sensor alert failed.")

				# do not use the old status information from the server
				# to update the screen => wait for new status update
				continue

			# update screen normally
			logging.debug("[%s]: Updating screen." % self.fileName)
			if not self.console.updateScreen("status"):
				logging.error("[%s]: Updating screen failed." % self.fileName)

			# if reference to server communication object does not exist
			# => get it from global data or if it does not exist continue loop 
			if self.serverComm == None:
				if self.globalData.serverComm != None:
					self.serverComm = self.globalData.serverComm
				else:
					continue

			# check if the client is not connected to the server
			# => update screen to connection failure
			if not self.serverComm.isConnected:
				logging.debug("[%s]: Updating screen " % self.fileName
					+ "for connection failure.")
				if not self.console.updateScreen("connectionfail"):
					logging.error("[%s]: Updating screen failed."
						% self.fileName)


	# sets the exit flag to shut down the thread
	def exit(self):
		self.exitFlag = True
		return


# this class is an urwid object for a status
class StatusUrwid:

	def __init__(self, title, statusType, statusValue):

		self.title = title
		self.statusType = statusType
		self.statusValue = statusValue

		self.statusTextWidget = urwid.Text(self.statusType + ": "
			+ str(self.statusValue))
		statusBox = urwid.LineBox(self.statusTextWidget, title=self.title)
		paddedStatusBox = urwid.Padding(statusBox, left=0, right=0)
		self.statusUrwidMap = urwid.AttrMap(paddedStatusBox, "neutral")


	# this function returns the final urwid widget that is used
	# to render the box of a status
	def get(self):
		return self.statusUrwidMap


	# this functipn updates the status type
	def updateStatusType(self, statusType):
		self.statusType = statusType
		self.statusTextWidget.set_text(self.statusType + ": "
			+ str(self.statusValue))


	# this functipn updates the status value
	def updateStatusValue(self, statusValue):
		self.statusValue = statusValue
		self.statusTextWidget.set_text(self.statusType + ": "
			+ str(self.statusValue))


	# this function changes the color of this urwid object to red
	def turnRed(self):
		self.statusUrwidMap.set_attr_map({None: "redColor"})


	# this function changes the color of this urwid object to green
	def turnGreen(self):
		self.statusUrwidMap.set_attr_map({None: "greenColor"})


	# this function changes the color of this urwid object to gray
	def turnGray(self):
		self.statusUrwidMap.set_attr_map({None: "grayColor"})


	# this function changes the color of this urwid object to the
	# neutral color scheme
	def turnNeutral(self):
		self.statusUrwidMap.set_attr_map({None: "neutral"})


# this class is an urwid object for a sensor
class SensorUrwid:

	def __init__(self, sensor, node, connectionTimeout,
		showConnected, showAlertDelay,
		showLastUpdated, showState):

		# options which information should be displayed
		self.showConnected = showConnected
		self.showAlertDelay = showAlertDelay
		self.showLastUpdated = showLastUpdated
		self.showState = showState

		# is needed to decide when a sensor has timed out
		self.connectionTimeout = connectionTimeout

		sensorPileList = list()
		self.descriptionWidget = urwid.Text("Desc.: " + sensor.description)
		sensorPileList.append(self.descriptionWidget)

		# create text widget for the "connected" information if
		# it should be displayed
		if self.showConnected:
			self.connectedWidget = urwid.Text("Connected: "
				+ str(node.connected))
			sensorPileList.append(self.connectedWidget)

		# create text widget for the "alert delay" information if
		# it should be displayed
		if self.showAlertDelay:
			self.alertDelayWidget = urwid.Text("Alert delay (sec): "
				+ str(sensor.alertDelay))
			sensorPileList.append(self.alertDelayWidget)

		# create text widget for the "last updated" information if
		# it should be displayed
		if self.showLastUpdated:
			self.lastUpdatedWidget = urwid.Text("Last updated: " 
				+ time.strftime("%D %H:%M:%S",
				time.localtime(sensor.lastStateUpdated)))
			sensorPileList.append(self.lastUpdatedWidget)

		# create text widget for the "state" information if
		# it should be displayed
		if self.showState:
			self.stateWidget = urwid.Text("State: " + str(sensor.state))
			sensorPileList.append(self.stateWidget)

		sensorPile = urwid.Pile(sensorPileList)
		sensorBox = urwid.LineBox(sensorPile, title="host: " + node.hostname)
		paddedSensorBox = urwid.Padding(sensorBox, left=1, right=1)

		# check if node is connected and set the color accordingly
		# and consider the state of the sensor (1 = triggered)
		if node.connected == 0:
			self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox,
				"disconnected")

		# check if the node is connected and no sensor alert is triggered
		elif (node.connected == 1
			and sensor.state != 1):
			self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox, "connected")

		# last possible combination is a triggered sensor alert
		else:
			self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox, "sensoralert")

		# check if sensor has timed out and change color accordingly
		# and consider the state of the sensor (1 = triggered)
		if (sensor.lastStateUpdated < (int(time.time())
			- (2 * self.connectionTimeout))
			and sensor.state != 1):
			self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox,
				"timedout")

		# store reference to sensor object and node object
		self.sensor = sensor
		self.node = node

		# store reference in sensor object to this urwid sensor object
		self.sensor.sensorUrwid = self


	# this function returns the final urwid widget that is used
	# to render the box of a sensor
	def get(self):
		return self.sensorUrwidMap


	# this function updates the description of the object
	def updateDescription(self, description):
		self.descriptionWidget.set_text("Desc.: " + description)


	# this function updates the connected status of the object
	# (and changes color arcordingly)
	def updateConnected(self, connected):

		# only change text widget text if the information should be
		# displayed
		if self.showConnected:
			self.connectedWidget.set_text("Connected: " + str(connected))

		# change color according to connection state
		# and consider the state of the sensor (1 = triggered)
		if (connected == 0
			and self.sensor.state != 1):
			self.sensorUrwidMap.set_attr_map({None: "disconnected"})
		elif (connected == 1
			and self.sensor.state != 1):
			self.sensorUrwidMap.set_attr_map({None: "connected"})

		# check if sensor has timed out and change color accordingly
		# and consider the state of the sensor (1 = triggered)
		if (self.sensor.lastStateUpdated < (int(time.time())
			- (2 * self.connectionTimeout))
			and self.sensor.state != 1):
			self.sensorUrwidMap.set_attr_map({None: "timedout"})


	# this function updates the alert delay of the object
	def updateAlertDelay(self, alertDelay):

		# only change text widget text if the information should be
		# displayed
		if self.showAlertDelay:
			self.alertDelayWidget.set_text("Alert delay (sec): "
				+ str(alertDelay))


	# this function updates the last update status of the object
	# (and changes color arcordingly)
	def updateLastUpdated(self, lastStateUpdated):

		# only change text widget text if the information should be
		# displayed
		if self.showLastUpdated:
			self.lastUpdatedWidget.set_text("Last updated: " 
				+ time.strftime("%D %H:%M:%S",
				time.localtime(lastStateUpdated)))

		# check if sensor has timed out and change color accordingly
		if (lastStateUpdated < (int(time.time())
			- (2 * self.connectionTimeout))
			and self.sensor.state != 1):
			self.sensorUrwidMap.set_attr_map({None: "timedout"})


	# this function updates the state of the object
	# (and changes color arcordingly)
	def updateState(self, state):

		# only change text widget text if the information should be
		# displayed
		if self.showState:
			self.stateWidget.set_text("State: " + str(state))

		# check if the node is connected and change the color accordingly
		if self.node.connected == 0:
			self.sensorUrwidMap.set_attr_map({None: "disconnected"})

		else:
			# check to which state the color should be changed
			if state == 0:
				self.sensorUrwidMap.set_attr_map({None: "connected"})
				# check if the sensor timed out and change 
				# the color accordingly
				if (self.sensor.lastStateUpdated < (int(time.time())
					- (2 * self.connectionTimeout))):
					self.sensorUrwidMap.set_attr_map({None: "timedout"})
			elif state == 1:
				self.sensorUrwidMap.set_attr_map({None: "sensoralert"})


	# this function updates all internal widgets and checks if
	# the sensor/node still exists
	def updateCompleteWidget(self):

		# check if sensor/node still exists
		if (self.sensor is None
			or self.node is None):

			# return false if object no longer exists
			return False

		self.updateDescription(self.sensor.description)
		self.updateConnected(self.node.connected)
		self.updateAlertDelay(self.sensor.alertDelay)
		self.updateLastUpdated(self.sensor.lastStateUpdated)
		self.updateState(self.sensor.state)

		# return true if object was updated
		return True


	# this functions sets the color when the connection to the server
	# has failed
	def setConnectionFail(self):
		self.sensorUrwidMap.set_attr_map({None: "connectionfail"})


# this class is an urwid object for an alert
class AlertUrwid:

	def __init__(self, alert, node):

		# store reference to alert object and node object
		self.alert = alert
		self.node = node

		# store reference in alert object to this urwid alert object
		self.alert.alertUrwid = self

		alertPileList = list()
		self.descriptionWidget = urwid.Text("Desc.: " + self.alert.description)
		alertPileList.append(self.descriptionWidget)

		alertPile = urwid.Pile(alertPileList)
		alertBox = urwid.LineBox(alertPile, title=node.hostname)
		paddedAlertBox = urwid.Padding(alertBox, left=1, right=1)

		# check if node is connected and set the color accordingly
		if self.node.connected == 0:
			self.alertUrwidMap = urwid.AttrMap(paddedAlertBox,
				"disconnected")
		else:
			self.alertUrwidMap = urwid.AttrMap(paddedAlertBox, "connected")


	# this function returns the final urwid widget that is used
	# to render the box of an alert
	def get(self):
		return self.alertUrwidMap


	# this function updates the description of the object
	def updateDescription(self, description):
		self.descriptionWidget.set_text("Desc.: " + description)


	# this function updates the connected status of the object
	# (and changes color arcordingly)
	def updateConnected(self, connected):

		# change color according to connection state
		if connected == 0:
			self.alertUrwidMap.set_attr_map({None: "disconnected"})
		else:
			self.alertUrwidMap.set_attr_map({None: "connected"})


	# this function updates all internal widgets and checks if
	# the alert/node still exists
	def updateCompleteWidget(self):

		# check if alert/node still exists
		if (self.alert is None
			or self.node is None):

			# return false if object no longer exists
			return False

		self.updateDescription(self.alert.description)
		self.updateConnected(self.node.connected)

		# return true if object was updated
		return True


	# this functions sets the color when the connection to the server
	# has failed
	def setConnectionFail(self):
		self.alertUrwidMap.set_attr_map({None: "connectionfail"})


# this class is an urwid object for a sensor alert
class SensorAlertUrwid:

	def __init__(self, description, timeReceived, timeShowSensorAlert):

		self.description = description
		self.timeReceived = timeReceived
		self.timeShowSensorAlert = timeShowSensorAlert

		# generate the internal urwid widgets
		stringReceivedTime = time.strftime("%D %H:%M:%S",
			time.localtime(self.timeReceived))
		self.textWidget = urwid.Text(stringReceivedTime + " - " +
			self.description)
		

	# this function returns the final urwid widget that is used
	# to render the sensor alert
	def get(self):
		return self.textWidget


	# this function checks if the sensor alert widget is too old
	def sensorAlertOutdated(self):
		# check if the sensor alert is older than the configured time to
		# show the sensor alerts in the list
		if (int(time.time()) - self.timeReceived) > self.timeShowSensorAlert:
			return True
		return False


# this class handles the complete screen/console
class Console:

	def __init__(self, globalData):
		self.fileName = os.path.basename(__file__)

		# get global configured data
		self.globalData = globalData
		self.options = self.globalData.options
		self.nodes = self.globalData.nodes
		self.sensors = self.globalData.sensors
		self.managers = self.globalData.managers
		self.alerts = self.globalData.alerts
		self.sensorAlerts = self.globalData.sensorAlerts
		self.connectionTimeout = self.globalData.connectionTimeout
		self.serverComm = self.globalData.serverComm
		self.timeShowSensorAlert = self.globalData.timeShowSensorAlert
		self.maxCountShowSensorAlert = self.globalData.maxCountShowSensorAlert

		# lock that is being used so only one thread can update the screen
		self.consoleLock = threading.BoundedSemaphore(1)

		# options which information should be displayed
		# by a sensor urwid object
		self.urwidSensorShowConnected \
			= self.globalData.urwidSensorShowConnected
		self.urwidSensorShowAlertDelay \
			= self.globalData.urwidSensorShowAlertDelay
		self.urwidSensorShowLastUpdated \
			= self.globalData.urwidSensorShowLastUpdated
		self.urwidSensorShowState \
			= self.globalData.urwidSensorShowState

		# urwid grid object for sensors
		self.sensorsGrid = None

		# urwid grid object for sensor alerts
		self.sensorAlertsPile = None

		# urwid object that shows the connection status
		self.connectionStatus = None

		# urwid object that shows if the alert system is active
		self.alertSystemActive = None

		# urwid grid object for alerts
		self.alertsGrid = None

		# a list of all urwid sensor objects
		self.sensorUrwidObjects = list()

		# a list of all urwid sensor alert objects
		self.sensorAlertUrwidObjects = list()

		# a list of all urwid alert objects
		self.alertUrwidObjects = list()

		# the file descriptor for the urwid callback to update the screen
		self.screenFd = None


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.consoleLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
		self.consoleLock.release()


	# this function is called to update the screen
	def updateScreen(self, status):

		# write status to the callback file descriptor
		if self.screenFd != None:

			self._acquireLock()

			os.write(self.screenFd, status)
			return True
		return False


	# this function is called if a key/mouse input was made
	def handleKeypress(self, key):

		# check if key 1 is pressed => send alert system activation to server 
		if key in ['1']:
			logging.info("[%s]: Activating alert system." % self.fileName)

			# send option message to server via a thread to not block
			# the urwid console thread
			updateProcess = ScreenActionExecuter(self.globalData)
			# set thread to daemon
			# => threads terminates when main thread terminates	
			updateProcess.daemon = True
			updateProcess.sendOption = True
			updateProcess.optionType = "alertSystemActive"
			updateProcess.optionValue = 1
			updateProcess.start()

		# check if key 2 is pressed => send alert system deactivation to server
		elif key in ['2']:
			logging.info("[%s]: Deactivating alert system." % self.fileName)

			# send option message to server via a thread to not block
			# the urwid console thread
			updateProcess = ScreenActionExecuter(self.globalData)
			# set thread to daemon
			# => threads terminates when main thread terminates	
			updateProcess.daemon = True
			updateProcess.sendOption = True
			updateProcess.optionType = "alertSystemActive"
			updateProcess.optionValue = 0
			updateProcess.start()

		# check if key q/Q is pressed => shut down client
		elif key in ['q', 'Q']:
			raise urwid.ExitMainLoop()

		return True


	# this function initializes the urwid objects and displays
	# them (it starts also the urwid main loop and will not
	# return unless the client is terminated)
	def startConsole(self):

		# generate all sensor urwid objects
		for sensor in self.sensors:

			# get node the sensor belongs to
			nodeSensorBelongs = None
			for node in self.nodes:
				if node.nodeType != "sensor":
					continue
				if sensor.nodeId == node.nodeId:
					nodeSensorBelongs = node
					break

			# create new sensor urwid object
			# (also links urwid object to sensor object)
			sensorUrwid = SensorUrwid(sensor, nodeSensorBelongs,
				self.connectionTimeout, self.urwidSensorShowConnected,
				self.urwidSensorShowAlertDelay,
				self.urwidSensorShowLastUpdated,
				self.urwidSensorShowState)

			# append the final sensor urwid object to the list
			# of sensor objects
			self.sensorUrwidObjects.append(sensorUrwid)

		# check if sensor urwid objects list is not empty
		if self.sensorUrwidObjects != list():
			# create grid object for the sensors
			self.sensorsGrid = urwid.GridFlow(
				map(lambda x: x.get(), self.sensorUrwidObjects),
				40, 1, 1, 'left')
		else:
			# create empty grid object for the sensors
			self.sensorsGrid = urwid.GridFlow([], 40, 1, 1, 'left')

		# build box around the sensor grid with title
		sensorsBox = urwid.LineBox(self.sensorsGrid, title="sensors")

		leftDisplayPart = urwid.Pile([sensorsBox])

		# generate all alert urwid objects
		for alert in self.alerts:

			# get node the alert belongs to
			nodeAlertBelongs = None
			for node in self.nodes:
				if node.nodeType != "alert":
					continue
				if alert.nodeId == node.nodeId:
					nodeAlertBelongs = node
					break

			# create new alert urwid object
			# (also links urwid object to alert object)
			alertUrwid = AlertUrwid(alert, nodeAlertBelongs)

			# append the final alert urwid object to the list
			# of alert objects
			self.alertUrwidObjects.append(alertUrwid)

		# check if alert urwid objects list is not empty
		if self.alertUrwidObjects != list():
			# create grid object for the alerts
			self.alertsGrid = urwid.GridFlow(
				map(lambda x: x.get(), self.alertUrwidObjects),
				40, 1, 1, 'left')
		else:
			# create empty grid object for the alerts
			self.alertsGrid = urwid.GridFlow([], 40, 1, 1, 'left')

		# build box around the alert grid with title
		alertsBox = urwid.LineBox(self.alertsGrid, title="alert clients")

		# create empty sensor alerts pile
		self.sensorAlertsPile = urwid.Pile([])

		# build box around the sensor alerts grid with title
		sensorAlertsBox = urwid.LineBox(self.sensorAlertsPile,
			title="list of triggered alerts")

		# generate widget to show the status of the alert system
		for option in self.options:
			if option.type == "alertSystemActive":
				if option.value == 0:
					self.alertSystemActive = \
						StatusUrwid("alert system status",
							"Status", "Deactivated")
					self.alertSystemActive.turnRed()
				else:
					self.alertSystemActive = \
						StatusUrwid("alert system status",
							"Status", "Activated")
					self.alertSystemActive.turnGreen()
		if self.alertSystemActive == None:
			logging.error("[%s]: No alert system status option."
				% self.fileName)
			return

		# generate widget to show the status of the connection
		self.connectionStatus = StatusUrwid("connection status",
			"Status", "Online")
		self.connectionStatus.turnNeutral()

		# generate a column for the status widgets
		statusColumn = urwid.Columns([self.alertSystemActive.get(),
			self.connectionStatus.get()])

		# generate right part of the display
		rightDisplayPart = urwid.Pile([statusColumn, sensorAlertsBox,
			alertsBox])

		# generate final body object
		finalBody = urwid.Columns([leftDisplayPart, rightDisplayPart])
		fillerBody = urwid.Filler(finalBody, "top")

		# generate header and footer
		header = urwid.Text("alertR console manager", align="center")
		footer = urwid.Text("Key bindings: "
			+ "1 - activate, "
			+ "2 - deactivate, "
			+ "q - quit")

		# build frame for final rendering
		frame = urwid.Frame(fillerBody, footer=footer, header=header)

		# color palette
		palette = [
			('redColor', 'black', 'dark red'),
			('greenColor', 'black', 'dark green'),
			('grayColor', 'black', 'light gray'),
            ('connected', 'black', 'dark green'),
            ('disconnected', 'black', 'dark red'),
            ('sensoralert', 'black', 'yellow'),
            ('connectionfail', 'black', 'light gray'),
            ('timedout', 'black', 'dark red'),
            ('neutral', '', ''),
        ]

        # create urwid main loop for the rendering
		loop = urwid.MainLoop(frame, palette=palette,
			unhandled_input=self.handleKeypress)

		# create a file descriptor callback to give other
		# threads the ability to communicate with the urwid thread
		self.screenFd = loop.watch_pipe(self.screenCallback)

		# rut urwid loop
		loop.run()


	# this function will be called from the urwid main loop
	# when the file descriptor of the callback
	# gets data written to it and updates the screen elements
	def screenCallback(self, receivedData):

		# if received data equals "status" or "sensoralert"
		# update the whole screen (in case of a sensor alert it can happen
		# that also a normal state change was received before and is forgotten
		# if a normal status update is not made)
		if receivedData == "status" or receivedData == "sensoralert":
			logging.debug("[%s]: Status update received. "  % self.fileName
				+ "Updating screen elements.")

			# update connection status urwid widget
			self.connectionStatus.updateStatusValue("Online")
			self.connectionStatus.turnNeutral()

			# update all option widgets
			for option in self.options:
				# change alert system active widget according
				# to received status
				if option.type == "alertSystemActive":
					if option.value == 0:
						self.alertSystemActive.updateStatusValue("Deactivated")
						self.alertSystemActive.turnRed()
					else:
						self.alertSystemActive.updateStatusValue("Activated")
						self.alertSystemActive.turnGreen()

			# remove sensor alerts if they are too old
			for sensorAlertUrwid in self.sensorAlertUrwidObjects:
				if sensorAlertUrwid.sensorAlertOutdated():
					# search in the pile widget for the
					# sensor alert widget object
					# to remove it
					for pileTuple in self.sensorAlertsPile.contents:
						if sensorAlertUrwid.get() == pileTuple[0]:
							self.sensorAlertsPile.contents.remove(pileTuple)

							# remove sensor alert urwid object from
							# list of objects
							# to delete all references to object
							# => object will be deleted by garbage collector
							self.sensorAlertUrwidObjects.remove(
								sensorAlertUrwid)

			# update the information of all sensor urwid widgets
			for sensorUrwidObject in self.sensorUrwidObjects:
				# if update method returns false
				# => sensor object no longer exists
				# => remove it 
				if not sensorUrwidObject.updateCompleteWidget():
					# search in the grid widget for the sensor widget object
					# to remove it
					for gridTuple in self.sensorsGrid.contents:
						if sensorUrwidObject.get() == gridTuple[0]:
							self.sensorsGrid.contents.remove(gridTuple)

							# remove sensor urwid object from list of objects
							# to delete all references to object
							# => object will be deleted by garbage collector
							self.sensorUrwidObjects.remove(sensorUrwidObject)

			# add all sensors that were newly added
			for sensor in self.sensors:
				# check if a new sensor was added
				if sensor.sensorUrwid == None:
					# get node the sensor belongs to
					nodeSensorBelongs = None
					for node in self.nodes:
						if node.nodeType != "sensor":
							continue
						if sensor.nodeId == node.nodeId:
							nodeSensorBelongs = node
							break

					# create new sensor urwid object
					# (also links urwid object to sensor object)
					sensorUrwid = SensorUrwid(sensor, nodeSensorBelongs,
						self.connectionTimeout, self.urwidSensorShowConnected,
						self.urwidSensorShowAlertDelay,
						self.urwidSensorShowLastUpdated,
						self.urwidSensorShowState)

					# append the final sensor urwid object to the list
					# of sensor objects
					self.sensorUrwidObjects.append(sensorUrwid)

					# add new sensor urwid object to the sensors grid
					self.sensorsGrid.contents.append((sensorUrwid.get(),
						self.sensorsGrid.options()))

			# update the information of all alert urwid widgets
			for alertUrwidObject in self.alertUrwidObjects:
				# if update method returns false
				# => alert object no longer exists
				# => remove it 
				if not alertUrwidObject.updateCompleteWidget():
					# search in the grid widget for the alert widget object
					# to remove it
					for gridTuple in self.alertsGrid.contents:
						if alertUrwidObject.get() == gridTuple[0]:
							self.alertsGrid.contents.remove(gridTuple)

							# remove alert urwid object from list of objects
							# to delete all references to object
							# => object will be deleted by garbage collector
							self.alertUrwidObjects.remove(alertUrwidObject)

			# add all alerts that were newly added
			for alert in self.alerts:
				# check if a new alert was added
				if alert.alertUrwid == None:
					# get node the alert belongs to
					nodeAlertBelongs = None
					for node in self.nodes:
						if node.nodeType != "alert":
							continue
						if alert.nodeId == node.nodeId:
							nodeAlertBelongs = node
							break

					# create new alert urwid object
					# (also links urwid object to alert object)
					alertUrwid = AlertUrwid(alert, nodeAlertBelongs)

					# append the final alert urwid object to the list
					# of alert objects
					self.alertUrwidObjects.append(alertUrwid)

					# add new alert urwid object to the alerts grid
					self.alertsGrid.contents.append((alertUrwid.get(),
						self.alertsGrid.options()))

		# check if the connection to the server failed
		if receivedData == "connectionfail":
			logging.debug("[%s]: Status connection failed "  % self.fileName
				+ "received. Updating screen elements.")

			# update connection status urwid widget
			self.connectionStatus.updateStatusValue("Offline")
			self.connectionStatus.turnRed()

			# update alert system active widget
			self.alertSystemActive.turnGray()

			# update all sensor urwid widgets
			for sensorUrwidObject in self.sensorUrwidObjects:
				sensorUrwidObject.setConnectionFail()

			# update all alert urwid widgets
			for alertUrwidObject in self.alertUrwidObjects:
				alertUrwidObject.setConnectionFail()

		# check if a sensor alert was received from the server
		if receivedData == "sensoralert":

			logging.debug("[%s]: Sensor alert "  % self.fileName
				+ "received. Updating screen elements.")

			# output all sensor alerts
			for sensorAlert in self.sensorAlerts:

				description = ""

				# search for the sensor urwid object and update it
				for sensor in self.sensors:
					if sensorAlert.sensorId == sensor.sensorId:
						sensor.sensorUrwid.updateState(sensorAlert.state)
						sensor.sensorUrwid.updateLastUpdated(
							sensorAlert.timeReceived)

						# get description for the sensor alert to add
						description = sensor.description

						break

				# remove the first sensor alert object if there are more
				# than the configured count of sensor alert widgets
				# (the first one is the oldest because of the appending)
				if (len(self.sensorAlertUrwidObjects)
					> (self.maxCountShowSensorAlert - 1)):
					sensorAlertWidgetToRemove = self.sensorAlertUrwidObjects[0]
					# search in the pile widget for the sensor alert
					# widget object to remove it
					for pileTuple in self.sensorAlertsPile.contents:
						if sensorAlertWidgetToRemove.get() == pileTuple[0]:
							self.sensorAlertsPile.contents.remove(pileTuple)

							# remove sensor alert urwid object
							# from list of objects
							# to delete all references to object
							# => object will be deleted by garbage collector
							self.sensorAlertUrwidObjects.remove(
								sensorAlertWidgetToRemove)

				# create new sensor alert urwid object
				sensorAlertUrwid = SensorAlertUrwid(description,
					sensorAlert.timeReceived, self.timeShowSensorAlert)

				# add sensor alert urwid object to the list of
				# sensor alerts urwid objects
				self.sensorAlertUrwidObjects.append(sensorAlertUrwid)

				# insert sensor alert as first element in the list
				# => new sensor alerts will be displayed on top
				self.sensorAlertsPile.contents.insert(0,
					(sensorAlertUrwid.get(), self.sensorAlertsPile.options()))

				# remove sensor alert from the list of sensor alerts
				self.sensorAlerts.remove(sensorAlert)

		# return true so the file descriptor will NOT be closed
		self._releaseLock()
		return True