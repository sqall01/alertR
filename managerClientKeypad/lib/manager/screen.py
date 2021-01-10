#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import logging
import os
import urwid
import time
from typing import Optional
from .audio import AudioOutput
from .elementPin import PinUrwid
from .elementProfile import ProfileChoiceUrwid
from .elementStatus import StatusUrwid
from .elementWarning import WarningUrwid
from ..globalData import GlobalData
from ..client import ServerCommunication


# this class handles the complete screen/console
class Console:

    def __init__(self, global_data: GlobalData):
        self.fileName = os.path.basename(__file__)

        # get global configured data
        self.globalData = global_data
        self.serverComm = self.globalData.serverComm  # type: ServerCommunication
        self.audioOutput = self.globalData.audioOutput  # type: AudioOutput
        self.pins = self.globalData.pins
        self.timeDelayedActivation = self.globalData.timeDelayedActivation
        self.audioOutput = self.globalData.audioOutput
        self.sensorWarningStates = self.globalData.sensorWarningStates
        self.unlockedScreenTimeout = self.globalData.unlockedScreenTimeout
        self.system_data = self.globalData.system_data

        # lock that is being used so only one thread can update the screen
        self.consoleLock = threading.BoundedSemaphore(1)

        # urwid object that shows the connection status
        self._connection_status = None  # type: Optional[StatusUrwid]

        # urwid object that shows the currently used system profile
        self._profile_urwid = None  # type: Optional[StatusUrwid]

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
        self.warningView = None  # type: Optional[WarningUrwid]

        # this is the urwid object of the profile choice field
        self._profile_choice_view = None  # type: Optional[ProfileChoiceUrwid]

        # flag that signalizes if the pin view is shown or not
        self.inPinView = True

        # flag that signalizes if the menu view is shown or not
        self.inMenuView = False

        # flag that signalizes if the warning view is shown or not
        self.inWarningView = False

        # Flag that indicates if the profile choice view is shown or not.
        self._in_profile_choice_view = False

        # callback function of the action that is chosen during the menu view
        # (is used to show warnings if some sensors are not in
        # the correct state and after confirmation execute the chosen option)
        self.callbackOptionToExecute = None

        # list of sensors that are in the warning state and need user
        # confirmation
        self.sensorsToWarn = list()

        # Color palettes for profiles.
        # Depending on the id of the profile, a color is chosen.
        self._profile_colors = ["profile_0", "profile_1", "profile_2", "profile_3", "profile_4"]

    # internal function that acquires the lock
    def _acquireLock(self):
        logging.debug("[%s]: Acquire lock." % self.fileName)
        self.consoleLock.acquire()

    def _callback_profile_choice(self, profile_id: int, delay: int):
        """
        Internal callback function used by the profile choice view.
        :param profile_id: profile id to change to
        :param delay: delay in seconds send in the option message
        :return:
        """
        profile = self.system_data.get_profile_by_id(profile_id)
        if profile is None:
            logging.error("[%s]: Profile with id %d does not exist." % (self.fileName, profile_id))
            self.showPinView()
            return

        logging.info("[%s]: Changing system profile to '%s' in %d seconds."
                     % (self.fileName, profile.name, delay))

        # check if output is activated
        if self.audioOutput is not None:
            if delay == 0:
                self.audioOutput.audioActivating()  # TODO change to "changing system profile"

            else:
                self.audioOutput.audioActivatingDelayed()  # TODO change to "delayed system profile change"

        self.serverComm.send_option("profile", float(profile.id), delay)

        self.showPinView()

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

            elif self._profile_choice_view.get() == pileTuple[0]:
                self.editPartScreen.contents.remove(pileTuple)
                continue

    # internal function that creates a list of sensors that do not
    # satisfy the configured sensor warning states
    def _checkSensorStatesSatisfied(self):

        # get a list of sensors that do not satisfy the warning states
        statesNotSatisfied = list()
        for sensorWarningState in self.sensorWarningStates:

            currentSensor = self.system_data.get_sensor_by_remote_id(sensorWarningState.username,
                                                                     sensorWarningState.remoteSensorId)

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

    # internal function that handles the keypress for the menu view
    def _handleMenuKeypress(self, key: str):

        # Check if option 1 was chosen => change system profile
        if key == '1':
            self._show_profile_choice_view(0)

            # TODO handle warning states
            '''
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
            '''

        # Check if option 2 was chosen => change system profile in x seconds
        elif key == '2':
            self._show_profile_choice_view(self.timeDelayedActivation)
            # TODO

            '''
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
            '''

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

    def _thread_screen_unlock_checker(self):
        while True:
            utcTimestamp = int(time.time())
            if (not self.inPinView
                    and (utcTimestamp - self.screenUnlockedTime) > self.unlockedScreenTimeout):

                logging.info("[%s]: Timeout for unlocked screen." % self.fileName)

                if not self.updateScreen("lockscreen"):
                    logging.error("[%s]: Locking screen failed." % self.fileName)

            time.sleep(5)

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
            self._connection_status.update_value("Online")
            self._connection_status.set_color("neutral")

            # Change active system profile widget according to received data.
            option = self.system_data.get_option_by_type("profile")
            if option is None:
                logging.error("[%s]: No profile option." % self.fileName)

            else:
                profile = self.system_data.get_profile_by_id(int(option.value))
                if profile is None:
                    logging.error("[%s]: Profile with id %d does not exist." % (self.fileName, int(option.value)))

                else:
                    self._profile_urwid.update_value(profile.name)
                    self._profile_urwid.set_color(self._profile_colors[profile.id % len(self._profile_colors)])

        # check if the connection to the server failed
        elif received_str == "connectionfail":
            logging.debug("[%s]: Status connection failed received. Updating screen elements." % self.fileName)

            # update connection status urwid widget
            self._connection_status.update_value("Offline")
            self._connection_status.set_color("redColor")

            # update alert system active widget
            self._profile_urwid.set_color("grayColor")

        # check if a sensor alert was received from the server
        elif received_str == "sensoralert":
            logging.debug("[%s]: Sensor alert received. Removing it." % self.fileName)

            # remove all sensor alerts
            self.system_data.delete_sensor_alerts_received_before(int(time.time() + 1))

        # check if the screen should be locked
        elif received_str == "lockscreen":
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
        self._in_profile_choice_view = False

        # remove views from the screen
        self._clearEditPartScreen()

        # show menu view
        self.editPartScreen.contents.append((self.menuPile, self.editPartScreen.options()))

    # show the pin view
    def showPinView(self):

        logging.info("[%s] Locking screen." % self.fileName)

        self.inMenuView = False
        self.inPinView = True
        self.inWarningView = False
        self._in_profile_choice_view = False

        # reset unlock time
        self.screenUnlockedTime = 0

        # reset callback and warnings
        self.callbackOptionToExecute = None
        self.sensorsToWarn = list()

        # remove views from the screen
        self._clearEditPartScreen()

        # show pin view
        self.editPartScreen.contents.append((self.pinEdit, self.editPartScreen.options()))

    def _show_profile_choice_view(self, delay: int):
        """
        Internal function that shows the profile choice view.
        :param delay: delay in seconds that is used for the option message send for the profile change
        """
        self.inMenuView = False
        self.inPinView = False
        self.inWarningView = False
        self._in_profile_choice_view = True

        # remove views from the screen
        self._clearEditPartScreen()

        # Show profile choice view.
        self._profile_choice_view = ProfileChoiceUrwid(self.system_data.get_profiles_list(order_by_id=True),
                                                       self._profile_colors,
                                                       self._callback_profile_choice,
                                                       delay)
        self.editPartScreen.contents.append((self._profile_choice_view.get(), self.editPartScreen.options()))

    # show the warning view
    def showWarningView(self):

        self.inMenuView = False
        self.inPinView = False
        self.inWarningView = True
        self._in_profile_choice_view = False

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

        # Generate widget to show the profile which is currently used by the system.
        option = self.system_data.get_option_by_type("profile")
        if option is None:
            logging.error("[%s]: No profile option." % self.fileName)
            return

        profile = self.system_data.get_profile_by_id(int(option.value))
        if profile is None:
            logging.error("[%s]: Profile with id %d does not exist." % (self.fileName, int(option.value)))
            return

        self._profile_urwid = StatusUrwid("Active System Profile", "Profile", profile.name)
        self._profile_urwid.set_color(self._profile_colors[profile.id % len(self._profile_colors)])

        # generate widget to show the status of the connection
        self._connection_status = StatusUrwid("Connection Status", "Status", "Online")
        self._connection_status.set_color("neutral")

        # generate pin field
        self.pinEdit = PinUrwid("Enter PIN:\n",
                                False,
                                "*",
                                self)

        # Generate menu.
        option1 = urwid.Text("1. Change system profile")
        option2 = urwid.Text("2. Change system profile in %d seconds" % self.timeDelayedActivation)
        separator = urwid.Text("")
        instruction = urwid.Text("Please, choose an option.")
        self.menuPile = urwid.Pile([option1, option2, separator, instruction])

        # generate edit/menu part of the screen
        self.editPartScreen = urwid.Pile([self.pinEdit])
        boxedEditPartScreen = urwid.LineBox(self.editPartScreen, title="Menu")

        # initialize warning view urwid
        self.warningView = WarningUrwid()

        # generate final body object
        self.finalBody = urwid.Pile([self._profile_urwid.get(), self._connection_status.get(), boxedEditPartScreen])
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
            ('profile_0', 'black', 'dark green'),
            ('profile_1', 'black', 'dark red'),
            ('profile_2', 'black', 'dark cyan'),
            ('profile_3', 'black', 'dark magenta'),
            ('profile_4', 'black', 'yellow'),
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
        self._in_profile_choice_view = False

        # Start unlock checker thread.
        thread = threading.Thread(target=self._thread_screen_unlock_checker)
        thread.daemon = True
        thread.start()

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
