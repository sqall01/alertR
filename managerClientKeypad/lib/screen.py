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

		# this options are used when the thread should
		# send delayed a new option to the server
		self.sendOptionDelayed = False
		self.optionTypeDelayed = None
		self.optionValueDelayed = None
		self.optionDelayDelayed = None


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
					+ "change to the server failed.")
				return

		# check if an option message should be send delayed to the server
		elif self.sendOptionDelayed:

			# check if the server communication object is available
			if self.serverComm is None:
				logging.error("[%s]: Sending delayed option " % self.fileName
						+ "change to server failed. No server communication "
						+ "object available.")
				return

			# send option change to server
			if not self.serverComm.sendOption(self.optionTypeDelayed,
				self.optionValueDelayed, self.optionDelayDelayed):
				logging.error("[%s]: Sending option " % self.fileName
					+ "change delayed to the server failed.")
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
		self.unlockedScreenTimeout = self.globalData.unlockedScreenTimeout

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
			# or 5 seconds elapsed
			self.screenUpdaterEvent.wait(5)
			self.screenUpdaterEvent.clear()

			# if reference to console object does not exist
			# => get it from global data or if it does not exist continue loop
			if self.console == None:
				if self.globalData.console != None:
					self.console = self.globalData.console
				else:
					continue

			# check if the screen is unlocked
			# and the screen unlocked time has timed out
			# => lock screen
			if (self.console.screenUnlocked
				and (int(time.time()) - self.console.screenUnlockedTime)
				> self.unlockedScreenTimeout):
				if not self.console.updateScreen("lockscreen"):
					logging.error("[%s]: Locking screen " % self.fileName
						+ "failed.")

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


# this class is an urwid object for the pin field object
class PinUrwid(urwid.Edit):

	# get the instance of the console object
	def registerConsoleInstance(self, console):
		self.fileName = os.path.basename(__file__)
		self.console = console


	# this functions handles the key presses
	def keypress(self, size, key):
		if key != "enter":
			return super(PinUrwid, self).keypress(size,key)

		# get user input and clear pin field
		inputPin = self.edit_text.strip()
		self.set_edit_text("")

		# check given pin
		if not self.console.checkPin(inputPin):
			return True

		# set screen as unlocked and store time
		# when screen was unlocked
		self.console.screenUnlocked = True
		self.console.screenUnlockedTime = int(time.time())

		# remove pin field from the screen
		for pileTuple in self.console.editPartScreen.contents:
			if self.console.pinEdit == pileTuple[0]:
				self.console.editPartScreen.contents.remove(pileTuple)
				break

		# show options menu
		self.console.editPartScreen.contents.append((self.console.menuPile,
			self.console.editPartScreen.options()))

		return True


# this class is an urwid object for the edit menu object
class MenuUrwid(urwid.Edit):

	# get the instance of the console object
	def registerConsoleInstance(self, console):
		self.fileName = os.path.basename(__file__)
		self.console = console


	# this functions handles the key presses
	def keypress(self, size, key):

		# check if option 1 was chosen => activate alert system
		if key == '1':

			logging.info("[%s]: Activating alert system." % self.fileName)

			# send option message to server via a thread to not block
			# the urwid console thread
			updateProcess = ScreenActionExecuter(self.console.globalData)
			# set thread to daemon
			# => threads terminates when main thread terminates	
			updateProcess.daemon = True
			updateProcess.sendOption = True
			updateProcess.optionType = "alertSystemActive"
			updateProcess.optionValue = 1
			updateProcess.start()

			# set screen as locked and reset the time
			# when screen was unlocked
			self.console.screenUnlocked = False
			self.console.screenUnlockedTime = 0

			# remove menu from the screen
			for pileTuple in self.console.editPartScreen.contents:
				if self.console.menuPile == pileTuple[0]:
					self.console.editPartScreen.contents.remove(pileTuple)
					break

			# show pin field
			self.console.editPartScreen.contents.append((self.console.pinEdit,
				self.console.editPartScreen.options()))

		# check if option 2 was chosen => deactivate alert system
		elif key == '2':

			logging.info("[%s]: Deactivating alert system." % self.fileName)

			# send option message to server via a thread to not block
			# the urwid console thread
			updateProcess = ScreenActionExecuter(self.console.globalData)
			# set thread to daemon
			# => threads terminates when main thread terminates	
			updateProcess.daemon = True
			updateProcess.sendOption = True
			updateProcess.optionType = "alertSystemActive"
			updateProcess.optionValue = 0
			updateProcess.start()

			# set screen as locked and reset the time
			# when screen was unlocked
			self.console.screenUnlocked = False
			self.console.screenUnlockedTime = 0

			# remove menu from the screen
			for pileTuple in self.console.editPartScreen.contents:
				if self.console.menuPile == pileTuple[0]:
					self.console.editPartScreen.contents.remove(pileTuple)
					break

			# show pin field
			self.console.editPartScreen.contents.append((self.console.pinEdit,
				self.console.editPartScreen.options()))

		# check if option 3 was chosen
		elif key == '3':

			logging.info("[%s]: Activating alert system " % self.fileName
				+ "in 60 seconds.")

			# send option message to server via a thread to not block
			# the urwid console thread
			updateProcess = ScreenActionExecuter(self.console.globalData)
			# set thread to daemon
			# => threads terminates when main thread terminates	
			updateProcess.daemon = True
			updateProcess.sendOptionDelayed = True
			updateProcess.optionTypeDelayed = "alertSystemActive"
			updateProcess.optionValueDelayed = 1
			updateProcess.optionDelayDelayed = 30
			updateProcess.start()

			# set screen as locked and reset the time
			# when screen was unlocked
			self.console.screenUnlocked = False
			self.console.screenUnlockedTime = 0

			# remove menu from the screen
			for pileTuple in self.console.editPartScreen.contents:
				if self.console.menuPile == pileTuple[0]:
					self.console.editPartScreen.contents.remove(pileTuple)
					break

			# show pin field
			self.console.editPartScreen.contents.append((self.console.pinEdit,
				self.console.editPartScreen.options()))

		else:
			return True


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
		self.serverComm = self.globalData.serverComm
		self.pins = self.globalData.pins

		# lock that is being used so only one thread can update the screen
		self.consoleLock = threading.BoundedSemaphore(1)

		# urwid object that shows the connection status
		self.connectionStatus = None

		# urwid object that shows if the alert system is active
		self.alertSystemActive = None

		# the file descriptor for the urwid callback to update the screen
		self.screenFd = None

		# this is the urwid object of the pin field
		self.pinEdit = None

		# this is the urwid object of the options menu
		self.menuPile = None

		# this is the urwid object of the whole edit part of the screen
		self.editPartScreen = None

		# this flag tells if the screen is locked or unlocked
		self.screenUnlocked = False

		# gives the time in seconds when the screen was unlocked
		# (used to check if it was timed out)
		self.screenUnlockedTime = 0


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.consoleLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
		self.consoleLock.release()


	# this function checks if the given pin is in the list of allowed pins
	def checkPin(self, inputPin):
		if inputPin in self.pins:
			return True
		return False


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
		# => disable key/mouse input
		return True


	# this function initializes the urwid objects and displays
	# them (it starts also the urwid main loop and will not
	# return unless the client is terminated)
	def startConsole(self):

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

		# generate pin field
		self.pinEdit = PinUrwid("Enter PIN:\n", multiline=False, mask="*")
		self.pinEdit.registerConsoleInstance(self)

		# generate menu
		option1 = urwid.Text("1. Activate alert system")
		option2 = urwid.Text("2. Deactivate alert system")
		option3 = urwid.Text("3. Activate alert system in 30 seconds")
		separator = urwid.Text("")
		menuEdit = MenuUrwid("Choose option:\n", multiline=False)
		menuEdit.registerConsoleInstance(self)
		self.menuPile = urwid.Pile([option1, option2, option3, separator,
			menuEdit])

		# generate edit/menu part of the screen
		self.editPartScreen = urwid.Pile([self.pinEdit])
		boxedEditPartScreen = urwid.LineBox(self.editPartScreen, title="menu")

		# generate final body object
		finalBody = urwid.Pile([self.alertSystemActive.get(),
			self.connectionStatus.get(), boxedEditPartScreen])
		fillerBody = urwid.Filler(finalBody, "top")

		# generate header
		header = urwid.Text("alertR keypad manager", align="center")

		# build frame for final rendering
		frame = urwid.Frame(fillerBody, header=header)

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

		# check if the connection to the server failed
		if receivedData == "connectionfail":
			logging.debug("[%s]: Status connection failed "  % self.fileName
				+ "received. Updating screen elements.")

			# update connection status urwid widget
			self.connectionStatus.updateStatusValue("Offline")
			self.connectionStatus.turnRed()

			# update alert system active widget
			self.alertSystemActive.turnGray()

		# check if a sensor alert was received from the server
		if receivedData == "sensoralert":

			logging.debug("[%s]: Sensor alert "  % self.fileName
				+ "received. Removing it.")

			# remove all sensor alerts
			del self.sensorAlerts[:]

		# check if the screen should be locked
		if receivedData == "lockscreen":

			logging.debug("[%s]: Locking screen."  % self.fileName)

			# set screen as locked and reset the time
			# when screen was unlocked
			self.screenUnlocked = False
			self.screenUnlockedTime = 0

			# remove menu from the screen
			for pileTuple in self.editPartScreen.contents:
				if self.menuPile == pileTuple[0]:
					self.editPartScreen.contents.remove(pileTuple)
					break

			# show pin field
			self.editPartScreen.contents.append((self.pinEdit,
				self.editPartScreen.options()))

		# return true so the file descriptor will NOT be closed
		self._releaseLock()
		return True