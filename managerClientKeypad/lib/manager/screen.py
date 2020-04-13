#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import logging
import os
import time
import urwid
from .audio import AudioOutput
from .screenElements import PinUrwid, StatusUrwid, WarningUrwid
from ..globalData import GlobalData
from ..client import ServerCommunication


# this class handles the screen updates
class ScreenUpdater(threading.Thread):

    def __init__(self, globalData: GlobalData):
        threading.Thread.__init__(self)

        # get global configured data
        self.globalData = globalData
        self.sensorAlerts = self.globalData.sensorAlerts
        self.console = self.globalData.console
        self.serverComm = self.globalData.serverComm  # type: ServerCommunication
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

        while True:
            if self.exitFlag:
                return

            # wait until thread is woken up by an event to update the screen
            # or 5 seconds elapsed
            self.screenUpdaterEvent.wait(5)
            self.screenUpdaterEvent.clear()

            # if reference to console object does not exist
            # => get it from global data or if it does not exist continue loop
            if self.console is None:
                if self.globalData.console is not None:
                    self.console = self.globalData.console

                else:
                    continue

            # check if the screen is unlocked
            # and the screen unlocked time has timed out
            # => lock screen
            utcTimestamp = int(time.time())
            if (not self.console.inPinView
               and (utcTimestamp - self.console.screenUnlockedTime) > self.unlockedScreenTimeout):

                logging.info("[%s]: Timeout for unlocked screen." % self.fileName)

                if not self.console.updateScreen("lockscreen"):
                    logging.error("[%s]: Locking screen failed." % self.fileName)

            # check if a sensor alert was received
            # => update screen with sensor alert
            if len(self.sensorAlerts) != 0:
                logging.info("[%s]: Updating screen with sensor alert." % self.fileName)

                if not self.console.updateScreen("sensoralert"):
                    logging.error("[%s]: Updating screen with sensor alert failed." % self.fileName)

                # do not use the old status information from the server
                # to update the screen => wait for new status update
                continue

            # update screen normally
            logging.debug("[%s]: Updating screen." % self.fileName)
            if not self.console.updateScreen("status"):
                logging.error("[%s]: Updating screen failed." % self.fileName)

            # if reference to server communication object does not exist
            # => get it from global data or if it does not exist continue loop 
            if self.serverComm is None:
                if self.globalData.serverComm is not None:
                    self.serverComm = self.globalData.serverComm

                else:
                    continue

            # check if the client is not connected to the server
            # => update screen to connection failure
            if not self.serverComm.is_connected:
                logging.debug("[%s]: Updating screen for connection failure." % self.fileName)

                if not self.console.updateScreen("connectionfail"):
                    logging.error("[%s]: Updating screen failed." % self.fileName)

    # sets the exit flag to shut down the thread
    def exit(self):
        self.exitFlag = True


# this class handles the complete screen/console
class Console:

    def __init__(self, globalData: GlobalData):
        self.fileName = os.path.basename(__file__)

        # get global configured data
        self.globalData = globalData
        self.options = self.globalData.options
        self.nodes = self.globalData.nodes
        self.sensors = self.globalData.sensors
        self.managers = self.globalData.managers
        self.alerts = self.globalData.alerts
        self.sensorAlerts = self.globalData.sensorAlerts
        self.serverComm = self.globalData.serverComm  # type: ServerCommunication
        self.audioOutput = self.globalData.audioOutput  # type: AudioOutput
        self.pins = self.globalData.pins
        self.timeDelayedActivation = self.globalData.timeDelayedActivation
        self.audioOutput = self.globalData.audioOutput
        self.sensorWarningStates = self.globalData.sensorWarningStates

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

        # gives the time in seconds when the screen was unlocked
        # (used to check if it was timed out)
        self.screenUnlockedTime = 0

        # the main render loop for the interactive session
        self.mainLoop = None

        # the final body that contains the left and right part of the screen
        self.finalBody = None

        # the main frame around the final body
        self.mainFrame = None

        # the urwid object of the warning view
        self.warningView = None

        # flag that signalizes if the pin view is shown or not
        self.inPinView = True

        # flag that signalizes if the menu view is shown or not
        self.inMenuView = False

        # flag that signalizes if the warning view is shown or not
        self.inWarningView = False

        # callback function of the action that is chosen during the menu view
        # (is used to show warnings if some sensors are not in
        # the correct state and after confirmation execute the chosen option)
        self.callbackOptionToExecute = None

        # list of sensors that are in the warning state and need user
        # confirmation
        self.sensorsToWarn = list()

    # internal function that acquires the lock
    def _acquireLock(self):
        logging.debug("[%s]: Acquire lock." % self.fileName)
        self.consoleLock.acquire()

    # internal function that clears the edit/menu part of the screen
    def _clearEditPartScreen(self):

        # remove views from the screen (if exists)
        for pileTuple in self.editPartScreen.contents:
            if self.menuPile == pileTuple[0]:
                self.editPartScreen.contents.remove(pileTuple)
                continue

            elif self.pinEdit == pileTuple[0]:
                self.editPartScreen.contents.remove(pileTuple)
                continue

            elif self.warningView.get() == pileTuple[0]:
                self.editPartScreen.contents.remove(pileTuple)
                continue

    # internal function that creates a list of sensors that do not
    # satisfy the configured sensor warning states
    def _checkSensorStatesSatisfied(self):

        # get a list of sensors that do not satisfy the warning states
        statesNotSatisfied = list()
        for sensorWarningState in self.sensorWarningStates:

            # get the node corresponding to sensor warning state
            currentNode = None
            for node in self.nodes:
                if node.username == sensorWarningState.username:
                    currentNode = node
                    break

            # skip warning state if node is not found
            if currentNode is None:
                logging.warning("[%s]: Not able to find node for username '%s'."
                                % (self.fileName, sensorWarningState.username))
                continue

            # get the sensor corresponding to sensor warning state
            currentSensor = None
            for sensor in self.sensors:
                if sensor.nodeId == currentNode.nodeId and sensor.remoteSensorId == sensorWarningState.remoteSensorId:
                    currentSensor = sensor
                    break

            # skip warning state if sensor is not found
            if currentSensor is None:
                logging.warning("[%s]: Not able to find sensor with remote id '%d' for username '%s'."
                                % (self.fileName, sensorWarningState.remoteSensorId, sensorWarningState.username))
                continue

            # check if the sensor is in the warning state
            if currentSensor.state == sensorWarningState.warningState:
                statesNotSatisfied.append(currentSensor)

                logging.debug("[%s]: Sensor with remote id '%d' "
                              % (self.fileName, sensorWarningState.remoteSensorId)
                              + "for username '%s' and description '%s' in warning state."
                              % (sensorWarningState.username, currentSensor.description))

        return statesNotSatisfied

    # internal function that executes option 1 of the menu
    def _executeOption1(self):

        logging.info("[%s]: Activating alert system." % self.fileName)

        # check if output is activated
        if self.audioOutput is not None:
            self.audioOutput.audioActivating()

        self.serverComm.send_option("alertSystemActive", 1.0)

    # internal function that executes option 2 of the menu
    def _executeOption2(self):

        logging.info("[%s]: Deactivating alert system." % self.fileName)

        # check if output is activated
        if self.audioOutput is not None:
            self.audioOutput.audioDeactivating()

        self.serverComm.send_option("alertSystemActive", 0.0)

    # internal function that executes option 3 of the menu
    def _executeOption3(self):

        logging.info("[%s]: Activating alert system in %d seconds." % (self.fileName, self.timeDelayedActivation))

        # check if output is activated
        if self.audioOutput is not None:
            self.audioOutput.audioActivatingDelayed()

        self.serverComm.send_option("alertSystemActive", 1.0, self.timeDelayedActivation)

    # internal function that handles the keypress for the menu view
    def _handleMenuKeypress(self, key: str):

        # check if option 1 was chosen => activate alert system
        if key == '1':

            # get all sensors that do not satisfy the
            # configured warning states 
            self.sensorsToWarn = self._checkSensorStatesSatisfied()

            # check if no sensor is in the warning state
            # => execute chosen action
            if not self.sensorsToWarn:
                self._executeOption1()
                self.showPinView()

            # at least one sensor is in the warning state
            # => ask for user confirmation
            else:

                # set the function to execute when all warnings are confirmed
                self.callbackOptionToExecute = self._executeOption1

                # let the user confirm all warning states
                self._handleWarningStates()

        # check if option 2 was chosen => deactivate alert system
        elif key == '2':

            self._executeOption2()
            self.showPinView()

        # check if option 3 was chosen
        elif key == '3':

            # get all sensors that do not satisfy the
            # configured warning states 
            self.sensorsToWarn = self._checkSensorStatesSatisfied()

            # check if no sensor is in the warning state
            # => execute chosen action
            if not self.sensorsToWarn:
                self._executeOption3()
                self.showPinView()

            # at least one sensor is in the warning state
            # => ask for user confirmation
            else:

                # set the function to execute when all warnings are confirmed
                self.callbackOptionToExecute = self._executeOption3

                # let the user confirm all warning states
                self._handleWarningStates()

    # internal function that handles all sensors in warning states
    def _handleWarningStates(self):

        # check if a sensor that is in the warning state still exists
        # => warn about sensor
        if self.sensorsToWarn:

            sensorToWarn = self.sensorsToWarn.pop()
            self.warningView.setSensorData(sensorToWarn.description, sensorToWarn.state)
            self.showWarningView()

        # if no sensor in a warning state remains
        # => execute chosen action
        else:

            self.callbackOptionToExecute()
            self.showPinView()

    # internal function that releases the lock
    def _releaseLock(self):
        logging.debug("[%s]: Release lock." % self.fileName)
        self.consoleLock.release()

    # this function checks if the given pin is in the list of allowed pins
    def checkPin(self, inputPin: str) -> bool:
        if inputPin in self.pins:
            return True
        return False

    # this function is called if a key/mouse input was made
    def handleKeypress(self, key: str) -> bool:

        # check if we are in the pin field view
        if self.inPinView:

            # if pin field loses focus send key manually to it
            # (seems to happen sometimes if it was not used for a long time)
            if key in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                       "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l",
                       "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x",
                       "y", "z",
                       "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
                       "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X",
                       "Y", "Z",
                       "enter"]:

                logging.debug("[%s]: Sending keypress '%s' manually to pin field." % (key, self.fileName))

                self.pinEdit.keypress((100,), key)

        # check if we are in the menu view
        elif self.inMenuView:
            self._handleMenuKeypress(key)

        # check if we are in the warning view
        elif self.inWarningView:
            # option 1 continues the chosen action
            if key == "1":
                self._handleWarningStates()

            # option 2 aborts the chosen action
            elif key == "2":
                self.showPinView()

        # => disable key/mouse input
        return True

    # this function will be called from the urwid main loop
    # when the file descriptor of the callback
    # gets data written to it and updates the screen elements
    def screenCallback(self, received_data: bytes) -> True:

        received_str = received_data.decode("ascii")

        # if received data equals "status" or "sensoralert"
        # update the whole screen (in case of a sensor alert it can happen
        # that also a normal state change was received before and is forgotten
        # if a normal status update is not made)
        if received_str == "status" or received_str == "sensoralert":
            logging.debug("[%s]: Status update received. Updating screen elements." % self.fileName)

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
        if received_str == "connectionfail":
            logging.debug("[%s]: Status connection failed received. Updating screen elements." % self.fileName)

            # update connection status urwid widget
            self.connectionStatus.updateStatusValue("Offline")
            self.connectionStatus.turnRed()

            # update alert system active widget
            self.alertSystemActive.turnGray()

        # check if a sensor alert was received from the server
        if received_str == "sensoralert":
            logging.debug("[%s]: Sensor alert received. Removing it." % self.fileName)

            # remove all sensor alerts
            del self.sensorAlerts[:]

        # check if the screen should be locked
        if received_str == "lockscreen":
            logging.debug("[%s]: Locking screen." % self.fileName)

            self.showPinView()

        # return true so the file descriptor will NOT be closed
        self._releaseLock()
        return True

    # show the menu view
    def showMenuView(self):

        self.inMenuView = True
        self.inPinView = False
        self.inWarningView = False

        # remove views from the screen
        self._clearEditPartScreen()

        # show menu view
        self.editPartScreen.contents.append((self.menuPile, self.editPartScreen.options()))

    # show the pin view
    def showPinView(self):

        self.inMenuView = False
        self.inPinView = True
        self.inWarningView = False

        # reset unlock time
        self.screenUnlockedTime = 0

        # reset callback and warnings
        self.callbackOptionToExecute = None
        self.sensorsToWarn = list()

        # remove views from the screen
        self._clearEditPartScreen()

        # show pin view
        self.editPartScreen.contents.append((self.pinEdit, self.editPartScreen.options()))

    # show the warning view
    def showWarningView(self):

        self.inMenuView = False
        self.inPinView = False
        self.inWarningView = True

        # check if output is activated
        if self.audioOutput is not None:
            self.audioOutput.audioWarning()

        # remove views from the screen
        self._clearEditPartScreen()

        # show pin view
        self.editPartScreen.contents.append((self.warningView.get(), self.editPartScreen.options()))

    # this function initializes the urwid objects and displays
    # them (it starts also the urwid main loop and will not
    # return unless the client is terminated)
    def startConsole(self):

        # generate widget to show the status of the alert system
        for option in self.options:
            if option.type == "alertSystemActive":
                if option.value == 0:
                    self.alertSystemActive = StatusUrwid("alert system status", "Status", "Deactivated")
                    self.alertSystemActive.turnRed()

                else:
                    self.alertSystemActive = StatusUrwid("alert system status", "Status", "Activated")
                    self.alertSystemActive.turnGreen()

        if self.alertSystemActive is None:
            logging.error("[%s]: No alert system status option." % self.fileName)
            return

        # generate widget to show the status of the connection
        self.connectionStatus = StatusUrwid("connection status", "Status", "Online")
        self.connectionStatus.turnNeutral()

        # generate pin field
        self.pinEdit = PinUrwid("Enter PIN:\n",
                                False,
                                "*",
                                self)

        # generate menu
        option1 = urwid.Text("1. Activate alert system")
        option2 = urwid.Text("2. Deactivate alert system")
        option3 = urwid.Text("3. Activate alert system in %d seconds" % self.timeDelayedActivation)
        separator = urwid.Text("")
        instruction = urwid.Text("Please, choose an option.")
        self.menuPile = urwid.Pile([option1, option2, option3, separator, instruction])

        # generate edit/menu part of the screen
        self.editPartScreen = urwid.Pile([self.pinEdit])
        boxedEditPartScreen = urwid.LineBox(self.editPartScreen, title="menu")

        # initialize warning view urwid
        self.warningView = WarningUrwid()

        # generate final body object
        self.finalBody = urwid.Pile([self.alertSystemActive.get(), self.connectionStatus.get(), boxedEditPartScreen])
        fillerBody = urwid.Filler(self.finalBody, "top")

        # generate header
        header = urwid.Text("AlertR Keypad Manager", align="center")

        # build frame for final rendering
        self.mainFrame = urwid.Frame(fillerBody, header=header)

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
        self.mainLoop = urwid.MainLoop(self.mainFrame, palette=palette, unhandled_input=self.handleKeypress)

        # create a file descriptor callback to give other
        # threads the ability to communicate with the urwid thread
        self.screenFd = self.mainLoop.watch_pipe(self.screenCallback)

        # set the correct view in which we are
        self.inPinView = True
        self.inMenuView = False
        self.inWarningView = False

        # run urwid loop
        self.mainLoop.run()

    # this function is called to update the screen
    def updateScreen(self, status: str) -> bool:

        # write status to the callback file descriptor
        if self.screenFd is not None:

            self._acquireLock()

            os.write(self.screenFd, status.encode("ascii"))
            return True
        return False
