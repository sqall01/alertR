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
from .elementAlert import AlertDetailedUrwid, AlertUrwid
from .elementAlertLevel import AlertLevelDetailedUrwid, AlertLevelUrwid
from .elementCore import SearchViewUrwid
from .elementManager import ManagerDetailedUrwid, ManagerUrwid
from .elementProfile import ProfileChoiceUrwid
from .elementStatus import StatusUrwid
from .elementSensor import SensorDetailedUrwid, SensorUrwid
from .elementSensorAlert import SensorAlertUrwid
from .eventHandler import ManagerEventHandler
from ..globalData import ManagerObjSensor, ManagerObjAlert, ManagerObjAlertLevel, ManagerObjProfile
from ..globalData import GlobalData
from ..client import ServerCommunication
from typing import Any, List, Optional


class FocusedElement:
    sensors = 0
    alerts = 1
    managers = 3
    alertLevels = 4


# this class handles the complete screen/console
class Console:

    def __init__(self, global_data: GlobalData):
        self.fileName = os.path.basename(__file__)

        # get global configured data
        self.globalData = global_data
        self.system_data = self.globalData.system_data
        self.connectionTimeout = self.globalData.connectionTimeout
        self.serverComm = self.globalData.serverComm  # type: ServerCommunication
        self.serverEventHandler = self.serverComm.event_handler  # type: ManagerEventHandler
        self.timeShowSensorAlert = self.globalData.timeShowSensorAlert
        self.maxCountShowSensorAlert = self.globalData.maxCountShowSensorAlert
        self.maxCountShowSensorsPerPage = self.globalData.maxCountShowSensorsPerPage
        self.maxCountShowAlertsPerPage = self.globalData.maxCountShowAlertsPerPage
        self.maxCountShowManagersPerPage = self.globalData.maxCountShowManagersPerPage
        self.maxCountShowAlertLevelsPerPage = self.globalData.maxCountShowAlertLevelsPerPage

        # lock that is being used so only one thread can update the screen
        self.consoleLock = threading.BoundedSemaphore(1)

        # urwid grid object for sensor alerts
        self.sensorAlertsPile = None

        # this urwid object is used as an empty sensor alert
        # to fill up the list of sensor alerts
        self.emtpySensorAlert = None

        # urwid object that shows the connection status
        self.connectionStatus = None

        # urwid object that shows the currently used system profile
        self._profile_urwid = None  # type: Optional[StatusUrwid]

        # A list of all urwid sensor objects.
        self.sensorUrwidObjects = list()

        # A list of active urwid sensor objects.
        self.activeSensorUrwidObjects = list()

        # a list of all urwid sensor objects that are shown on the page
        self.shownSensorUrwidObjects = list()

        # urwid grid object for sensors
        self.sensorsGrid = None

        # the current page of the sensor objects that is shown
        self.currentSensorPage = 0

        # the footer of the sensor box (which shows the current page number)
        self.sensorsFooter = None

        # a list of all urwid alert objects
        self.alertUrwidObjects = list()

        # A list of active urwid alert objects.
        self.activeAlertUrwidObjects = list()

        # a list of all urwid alert objects that are shown on the page
        self.shownAlertUrwidObjects = list()

        # urwid grid object for alerts
        self.alertsGrid = None

        # the current page of the alert objects that is shown
        self.currentAlertPage = 0

        # the footer of the alert box (which shows the current page number)
        self.alertsFooter = None

        # a list of all urwid manager objects
        self.managerUrwidObjects = list()

        # A list of active urwid manager objects.
        self.activeManagerUrwidObjects = list()

        # a list of all urwid manager objects that are shown on the page
        self.shownManagerUrwidObjects = list()

        # urwid grid object for managers
        self.managersGrid = None

        # the current page of the manager objects that is shown
        self.currentManagerPage = 0

        # the footer of the manager box (which shows the current page number)
        self.managersFooter = None

        # a list of all urwid alert level objects
        self.alertLevelUrwidObjects = list()

        # A list of active urwid alert level objects.
        self.activeAlertLevelUrwidObjects = list()

        # a list of all urwid alert level objects that are shown on the page
        self.shownAlertLevelUrwidObjects = list()

        # urwid grid object for alert levels
        self.alertLevelsGrid = None

        # the current page of the alert level objects that is shown
        self.currentAlertLevelPage = 0

        # the footer of the alert level box
        # (which shows the current page number)
        self.alertLevelsFooter = None

        # a list of all urwid sensor alert objects
        self.sensorAlertUrwidObjects = list()

        # the file descriptor for the urwid callback to update the screen
        self.screenFd = None

        # the main render loop for the interactive session
        self.mainLoop = None

        # the value that represents the currently focused element group
        # (an enum class is used for it)
        self.currentFocused = None

        # the final body that contains the left and right part of the screen
        self.finalBody = None

        # the main frame around the final body
        self.mainFrame = None

        # left and right part of the screen
        self.rightDisplayPart = None
        self.leftDisplayPart = None

        # the keybinding text below each element group
        self.sensorsKeyBindings = None
        self.managersKeyBindings = None
        self.alertsKeyBindings = None
        self.alertLevelsKeyBindings = None

        # the boxes around the element groups
        self.sensorsBox = None
        self.alertsBox = None
        self.managersBox = None
        self.alertLevelsBox = None

        # flag that signalizes if a detailed view of an object is shown or not
        self.inDetailView = False

        # Flag that signalizes if the search view is shown or not
        self.inSearchView = False

        # Flag that indicates if the profile choice view is shown or not.
        self._in_profile_choice_view = False

        # the urwid object of the detailed view
        self.detailedView = None

        # The urwid object of the search view
        self.searchView = None

        # The keyword that is currently searched for.
        self.searchKeyword = ""

        # The urwid object of the profile choice view.
        self._profile_choice_view = None

        # Color palettes for profiles.
        # Depending on the id of the profile, a color is chosen.
        self._profile_colors = ["profile_0", "profile_1", "profile_2", "profile_3", "profile_4"]

    # set the focus to the sensors
    def _focusSensors(self):
        logging.debug("[%s]: Focus sensors." % self.fileName)

        # get index of element to focus and focus it
        idx = 0
        for i in self.finalBody.contents:
            if i[0] == self.leftDisplayPart:
                break
            idx += 1
        if idx >= len(self.finalBody.contents):
            return
        self.finalBody.focus_position = idx

        # get index of element to focus and focus it
        idx = 0
        for i in self.leftDisplayPart.contents:
            if i[0] == self.sensorsBox:
                break
            idx += 1
        if idx >= len(self.leftDisplayPart.contents):
            return
        self.leftDisplayPart.focus_position = idx

        try:
            self.sensorsGrid.focus_position = 0
        except IndexError:  # raised if no element in element group
            pass

    # set the focus to the alerts
    def _focusAlerts(self):
        logging.debug("[%s]: Focus alerts." % self.fileName)

        # get index of element to focus and focus it
        idx = 0
        for i in self.finalBody.contents:
            if i[0] == self.rightDisplayPart:
                break
            idx += 1
        if idx >= len(self.finalBody.contents):
            return
        self.finalBody.focus_position = idx

        # get index of element to focus and focus it
        idx = 0
        for i in self.rightDisplayPart.contents:
            if i[0] == self.alertsBox:
                break
            idx += 1
        if idx >= len(self.rightDisplayPart.contents):
            return
        self.rightDisplayPart.focus_position = idx

        try:
            self.alertsGrid.focus_position = 0
        except IndexError:  # raised if no element in element group
            pass

    # set the focus to the managers
    def _focusManagers(self):
        logging.debug("[%s]: Focus managers." % self.fileName)

        # get index of element to focus and focus it
        idx = 0
        for i in self.finalBody.contents:
            if i[0] == self.leftDisplayPart:
                break
            idx += 1
        if idx >= len(self.finalBody.contents):
            return
        self.finalBody.focus_position = idx

        # get index of element to focus and focus it
        idx = 0
        for i in self.leftDisplayPart.contents:
            if i[0] == self.managersBox:
                break
            idx += 1
        if idx >= len(self.leftDisplayPart.contents):
            return
        self.leftDisplayPart.focus_position = idx

        try:
            self.managersGrid.focus_position = 0
        except IndexError:  # raised if no element in element group
            pass

    # set the focus to the alert levels
    def _focusAlertLevels(self):
        logging.debug("[%s]: Focus alert levels." % self.fileName)

        # get index of element to focus and focus it
        idx = 0
        for i in self.finalBody.contents:
            if i[0] == self.rightDisplayPart:
                break
            idx += 1
        if idx >= len(self.finalBody.contents):
            return
        self.finalBody.focus_position = idx

        # get index of element to focus and focus it
        idx = 0
        for i in self.rightDisplayPart.contents:
            if i[0] == self.alertLevelsBox:
                break
            idx += 1
        if idx >= len(self.rightDisplayPart.contents):
            return
        self.rightDisplayPart.focus_position = idx

        try:
            self.alertLevelsGrid.focus_position = 0
        except IndexError:  # raised if no element in element group
            pass

    # close the detailed view
    def _closeDetailedView(self):
        self.mainLoop.widget = self.mainFrame
        self.inDetailView = False
        self.detailedView = None

    # Close the search view.
    def _closeSearchView(self):
        self.mainLoop.widget = self.mainFrame
        self.inSearchView = False
        self.searchView = None

    def _close_profile_choice_view(self):
        self.mainLoop.widget = self.mainFrame
        self._in_profile_choice_view = False
        self._profile_choice_view = None

    # Shows the results of the search.
    def _showSearchResult(self):
        keyword = self.searchKeyword
        if self.currentFocused == FocusedElement.sensors:

            # Filter for all sensor urwid objects that contain the keyword
            # (case-insensitive).
            foundSensors = [obj for obj in self.sensorUrwidObjects if keyword in obj.sensor.description.lower()]

            logging.debug("[%s]: Found %d sensors for keyword '%s'."
                          % (self.fileName, len(foundSensors), keyword))

            # Display currently found objects.
            self.activeSensorUrwidObjects = foundSensors
            self._showSensorsAtPageIndex(0)

        elif self.currentFocused == FocusedElement.alerts:

            # Filter for all alert urwid objects that contain the keyword
            # (case-insensitive).
            foundAlerts = [obj for obj in self.alertUrwidObjects if keyword in obj.alert.description.lower()]

            logging.debug("[%s]: Found %d alerts for keyword '%s'."
                          % (self.fileName, len(foundAlerts), keyword))

            # Display currently found objects.
            self.activeAlertUrwidObjects = foundAlerts
            self._showAlertsAtPageIndex(0)

        elif self.currentFocused == FocusedElement.managers:

            # Filter for all manager urwid objects that contain the keyword
            # (case-insensitive).
            foundManagers = [obj for obj in self.managerUrwidObjects if keyword in obj.manager.description.lower()]

            logging.debug("[%s]: Found %d managers for keyword '%s'."
                          % (self.fileName, len(foundManagers), keyword))

            # Display currently found objects.
            self.activeManagerUrwidObjects = foundManagers
            self._showManagersAtPageIndex(0)

        elif self.currentFocused == FocusedElement.alertLevels:

            # Filter for all alert level urwid objects that contain the keyword
            # (case-insensitive).
            foundAlertLevels = [obj for obj in self.alertLevelUrwidObjects if keyword in obj.alertLevel.name.lower()]

            logging.debug("[%s]: Found %d alert levels for keyword '%s'."
                          % (self.fileName, len(foundAlertLevels), keyword))

            # Display currently found objects.
            self.activeAlertLevelUrwidObjects = foundAlertLevels
            self._showAlertLevelsAtPageIndex(0)

    # switches focus to the next element group
    def _switchFocusedElementGroup(self):
        if self.currentFocused == FocusedElement.sensors:
            self.currentFocused = FocusedElement.alerts
            self._focusAlerts()
            self.alertsKeyBindings.set_text("Keys: b - Previous Page, n - Next Page, s - Search")
            self.managersKeyBindings.set_text("Keys: None")
            self.alertLevelsKeyBindings.set_text("Keys: None")
            self.sensorsKeyBindings.set_text("Keys: None")

        elif self.currentFocused == FocusedElement.alerts:
            self.currentFocused = FocusedElement.managers
            self._focusManagers()
            self.alertsKeyBindings.set_text("Keys: None")
            self.managersKeyBindings.set_text("Keys: b - Previous Page, n - Next Page, s - Search")
            self.alertLevelsKeyBindings.set_text("Keys: None")
            self.sensorsKeyBindings.set_text("Keys: None")

        elif self.currentFocused == FocusedElement.managers:
            self.currentFocused = FocusedElement.alertLevels
            self._focusAlertLevels()
            self.alertsKeyBindings.set_text("Keys: None")
            self.managersKeyBindings.set_text("Keys: None")
            self.alertLevelsKeyBindings.set_text("Keys: b - Previous Page, n - Next Page, s - Search")
            self.sensorsKeyBindings.set_text("Keys: None")

        else:
            self.currentFocused = FocusedElement.sensors
            self._focusSensors()
            self.alertsKeyBindings.set_text("Keys: None")
            self.managersKeyBindings.set_text("Keys: None")
            self.alertLevelsKeyBindings.set_text("Keys: None")
            self.sensorsKeyBindings.set_text("Keys: b - Previous Page, n - Next Page, s - Search")

    # this function moves the focus to the next element depending
    # to the currently focused element group
    def _moveFocus(self, key: str):

        # get current focused element group
        if self.currentFocused == FocusedElement.sensors:
            currentElements = self.sensorsGrid
        elif self.currentFocused == FocusedElement.alerts:
            currentElements = self.alertsGrid
        elif self.currentFocused == FocusedElement.managers:
            currentElements = self.managersGrid
        else:
            currentElements = self.alertLevelsGrid

        currPos = None
        if len(currentElements.contents) != 0:
            currPos = currentElements.focus_position
        else:
            return

        # get the width we need for calculating the current
        # elements per row
        calcCellWidth = currentElements.cell_width + 1

        # use the half of the total width for calculations
        # (current design splits window in to halfs)
        calcTotalWidth = int((self.mainLoop.screen.get_cols_rows()[0]-1) / 2)

        # calculate the cells that are displayed per row
        cellsPerRow = int(calcTotalWidth / calcCellWidth)
        if cellsPerRow == 0:
            cellsPerRow += 1

        # move focus to the element above in the grid
        if key == "up":
            currPos = currPos - cellsPerRow
            if currPos >= 0:
                currentElements.focus_position = currPos

        # move focus to the element below in the grid
        elif key == "down":
            currPos = currPos + cellsPerRow
            if currPos < len(currentElements.contents):
                currentElements.focus_position = currPos

        # move focus to the element left in the grid
        elif key == "left":
            tempPos = currPos - 1
            if (tempPos >= 0
               and currPos % cellsPerRow != 0):
                currentElements.focus_position = tempPos

        # move focus to the element right in the grid
        elif key == "right":
            tempPos = currPos + 1
            if (tempPos < len(currentElements.contents)
               and (currPos+1) % cellsPerRow != 0):
                currentElements.focus_position = tempPos

    # internal function that acquires the lock
    def _acquireLock(self):
        logging.debug("[%s]: Acquire lock." % self.fileName)
        self.consoleLock.acquire()

    # internal function that releases the lock
    def _releaseLock(self):
        logging.debug("[%s]: Release lock." % self.fileName)
        self.consoleLock.release()


    def _callbackSearchFieldChange(self, editElement, state: str, userData):
        """
        Callback function for the search field that is called whenever
        the state of the field changes (a user presses a new key).
        This function searches instantly for the entered keyword and shows the result.
        :param editElement:
        :param state:
        :param userData:
        """
        self.searchKeyword = state.lower()
        self._showSearchResult()

    def _callback_profile_choice(self, button: urwid.Button, profile: ManagerObjProfile):
        """
        Callback function for the profile choice overlay that is called if a button is pressed.
        :param button:
        :param profile:
        """
        logging.info("[%s]: Changing system profile to '%s'." % (self.fileName, profile.name))
        self.serverComm.send_option("profile", float(profile.id))

        self._close_profile_choice_view()

    # get a list of alert level objects that belong to the given
    # object (object has to have attribute alertLevels)
    def _getAlertLevelsOfObj(self, obj: Any) -> List[ManagerObjAlertLevel]:

        # get all alert levels the focused sensor belongs to
        currentAlertLevels = list()
        for alertLevel in self.system_data.get_alert_levels_list(order_by_level=True):
            if alertLevel.level in obj.alertLevels:
                currentAlertLevels.append(alertLevel)

        return currentAlertLevels

    # get a list of alert objects that belong to the given
    # alert level
    def _getAlertsOfAlertLevel(self, alertLevel: ManagerObjAlertLevel) -> List[ManagerObjAlert]:

        # get all alerts that belong to the focused alert level
        currentAlerts = list()
        for alert in self.system_data.get_alerts_list(order_by_desc=True):
            if alertLevel.level in alert.alertLevels:
                currentAlerts.append(alert)

        return currentAlerts

    # get a list of sensor objects that belong to the given
    # alert level
    def _getSensorsOfAlertLevel(self, alertLevel: ManagerObjAlertLevel) -> List[ManagerObjSensor]:

        # get all sensors that belong to the focused alert level
        currentSensors = list()
        for sensor in self.system_data.get_sensors_list(order_by_desc=True):
            if alertLevel.level in sensor.alertLevels:
                currentSensors.append(sensor)

        return currentSensors

    # internal function that shows the alert urwid objects given
    # by a page index
    def _showAlertsAtPageIndex(self, pageIndex: int):

        # calculate how many pages the alert urwid objects have
        activeLength = len(self.activeAlertUrwidObjects)
        alertPageCount = int(activeLength / self.maxCountShowAlertsPerPage)
        if (activeLength % self.maxCountShowAlertsPerPage) != 0:
            alertPageCount += 1

        # check if the index to show is within the page range
        if pageIndex >= alertPageCount:
            pageIndex = 0
        elif pageIndex < 0:
            pageIndex = alertPageCount - 1

        logging.debug("[%s]: Update shown alerts with page index: %d." % (self.fileName, pageIndex))

        # get all alert urwid objects that should be shown on the new page
        del self.shownAlertUrwidObjects[:]
        for i in range(self.maxCountShowAlertsPerPage):
            tempItemIndex = i + (pageIndex * self.maxCountShowAlertsPerPage)
            if tempItemIndex >= activeLength:
                break
            self.shownAlertUrwidObjects.append(
                self.activeAlertUrwidObjects[tempItemIndex])

        # delete all old shown alert objects and replace them by the new ones
        del self.alertsGrid.contents[:]
        for newShownAlert in self.shownAlertUrwidObjects:
            self.alertsGrid.contents.append((newShownAlert.get(), self.alertsGrid.options()))

        # update alerts page footer
        tempText = "Page %d / %d " % (pageIndex + 1, alertPageCount)
        self.alertsFooter.set_text(tempText)

    # internal function that shows the next page of alert objects
    def _showAlertsNextPage(self):

        logging.debug("[%s]: Show next alerts page." % self.fileName)

        # calculate how many pages the alert urwid objects have
        activeLength = len(self.activeAlertUrwidObjects)
        alertPageCount = int(activeLength / self.maxCountShowAlertsPerPage)
        if alertPageCount == 0:
            return
        if (activeLength % self.maxCountShowAlertsPerPage) != 0:
            alertPageCount += 1

        # calculate next page that should be shown
        self.currentAlertPage += 1
        if self.currentAlertPage >= alertPageCount:
            self.currentAlertPage = 0

        # update shown alerts
        self._showAlertsAtPageIndex(self.currentAlertPage)

    # internal function that shows the previous page of alert objects
    def _showAlertsPreviousPage(self):

        logging.debug("[%s]: Show previous alerts page." % self.fileName)

        # calculate how many pages the alert urwid objects have
        activeLength = len(self.activeAlertUrwidObjects)
        alertPageCount = int(activeLength / self.maxCountShowAlertsPerPage)
        if alertPageCount == 0:
            return
        if (activeLength % self.maxCountShowAlertsPerPage) != 0:
            alertPageCount += 1

        # calculate next page that should be shown
        self.currentAlertPage -= 1
        if self.currentAlertPage < 0:
            self.currentAlertPage = alertPageCount - 1

        # update shown alerts
        self._showAlertsAtPageIndex(self.currentAlertPage)

    # internal function that shows the alert level urwid objects given
    # by a page index
    def _showAlertLevelsAtPageIndex(self, pageIndex: int):

        # calculate how many pages the alert level urwid objects have
        activeLength = len(self.activeAlertLevelUrwidObjects)
        alertLevelPageCount = int(activeLength / self.maxCountShowAlertLevelsPerPage)
        if (activeLength % self.maxCountShowAlertLevelsPerPage) != 0:
            alertLevelPageCount += 1

        # check if the index to show is within the page range
        if pageIndex >= alertLevelPageCount:
            pageIndex = 0
        elif pageIndex < 0:
            pageIndex = alertLevelPageCount - 1

        logging.debug("[%s]: Update shown alert levels with page index: %d." % (self.fileName, pageIndex))

        # get all alert level urwid objects
        # that should be shown on the new page
        del self.shownAlertLevelUrwidObjects[:]
        for i in range(self.maxCountShowAlertLevelsPerPage):
            tempItemIndex = i + (pageIndex * self.maxCountShowAlertLevelsPerPage)
            if tempItemIndex >= activeLength:
                break
            self.shownAlertLevelUrwidObjects.append(self.activeAlertLevelUrwidObjects[tempItemIndex])

        # delete all old shown alert level objects
        # and replace them by the new ones
        del self.alertLevelsGrid.contents[:]
        for newShownAlertLevel in self.shownAlertLevelUrwidObjects:
            self.alertLevelsGrid.contents.append((newShownAlertLevel.get(), self.alertLevelsGrid.options()))

        # update alert levels page footer
        tempText = "Page %d / %d " % (pageIndex + 1, alertLevelPageCount)
        self.alertLevelsFooter.set_text(tempText)

    # internal function that shows the next page of alert level objects
    def _showAlertLevelsNextPage(self):

        logging.debug("[%s]: Show next alert levels page." % self.fileName)

        # calculate how many pages the alert level urwid objects have
        activeLength = len(self.activeAlertLevelUrwidObjects)
        alertLevelPageCount = int(activeLength / self.maxCountShowAlertLevelsPerPage)
        if alertLevelPageCount == 0:
            return
        if (activeLength % self.maxCountShowAlertLevelsPerPage) != 0:
            alertLevelPageCount += 1

        # calculate next page that should be shown
        self.currentAlertLevelPage += 1
        if self.currentAlertLevelPage >= alertLevelPageCount:
            self.currentAlertLevelPage = 0

        # update shown alert levels
        self._showAlertLevelsAtPageIndex(self.currentAlertLevelPage)

    # internal function that shows the previous page of alert level objects
    def _showAlertLevelsPreviousPage(self):

        logging.debug("[%s]: Show previous alert levels page." % self.fileName)

        # calculate how many pages the alert level urwid objects have
        activeLength = len(self.activeAlertLevelUrwidObjects)
        alertLevelPageCount = int(activeLength / self.maxCountShowAlertLevelsPerPage)
        if alertLevelPageCount == 0:
            return
        if (activeLength % self.maxCountShowAlertLevelsPerPage) != 0:
            alertLevelPageCount += 1

        # calculate next page that should be shown
        self.currentAlertLevelPage -= 1
        if self.currentAlertLevelPage < 0:
            self.currentAlertLevelPage = alertLevelPageCount - 1

        # update shown alert levels
        self._showAlertLevelsAtPageIndex(self.currentAlertLevelPage)

    # creates an overlayed view with the detailed about the focused object
    def _showDetailedView(self) -> bool:

        # get current focused element
        if self.currentFocused == FocusedElement.sensors:
            currentElements = self.sensorsGrid

            currPos = None
            if len(currentElements.contents) != 0:
                currPos = currentElements.focus_position
            else:
                return False

            # search for element for detailed view
            currentElement = None
            currentWidgetElement = currentElements.contents[currPos][0]
            for temp in self.sensorUrwidObjects:
                if currentWidgetElement == temp.get():
                    currentElement = temp
                    break
            if currentElement is None:
                logging.error("[%s] Not able to find sensor element for detailed view." % self.fileName)
                return True

            # get all alert levels the focused sensor belongs to
            currentAlertLevels = self._getAlertLevelsOfObj(currentElement.sensor)

            self.detailedView = SensorDetailedUrwid(currentElement.sensor, currentElement.node, currentAlertLevels)

        elif self.currentFocused == FocusedElement.alerts:
            currentElements = self.alertsGrid

            currPos = None
            if len(currentElements.contents) != 0:
                currPos = currentElements.focus_position
            else:
                return False

            # search for element for detailed view
            currentElement = None
            currentWidgetElement = currentElements.contents[currPos][0]
            for temp in self.alertUrwidObjects:
                if currentWidgetElement == temp.get():
                    currentElement = temp
                    break
            if currentElement is None:
                logging.error("[%s] Not able to find alert element for detailed view." % self.fileName)
                return True

            # get all alert levels the focused alert belongs to
            currentAlertLevels = self._getAlertLevelsOfObj(currentElement.alert)

            self.detailedView = AlertDetailedUrwid(currentElement.alert, currentElement.node, currentAlertLevels)

        elif self.currentFocused == FocusedElement.managers:
            currentElements = self.managersGrid

            currPos = None
            if len(currentElements.contents) != 0:
                currPos = currentElements.focus_position
            else:
                return False

            # search for element for detailed view
            currentElement = None
            currentWidgetElement = currentElements.contents[currPos][0]
            for temp in self.managerUrwidObjects:
                if currentWidgetElement == temp.get():
                    currentElement = temp
                    break
            if currentElement is None:
                logging.error("[%s] Not able to find manager element for detailed view." % self.fileName)
                return True

            self.detailedView = ManagerDetailedUrwid(currentElement.manager, currentElement.node)

        else:
            currentElements = self.alertLevelsGrid

            currPos = None
            if len(currentElements.contents) != 0:
                currPos = currentElements.focus_position
            else:
                return False

            # search for element for detailed view
            currentElement = None
            currentWidgetElement = currentElements.contents[currPos][0]
            for temp in self.alertLevelUrwidObjects:
                if currentWidgetElement == temp.get():
                    currentElement = temp
                    break
            if currentElement is None:
                logging.error("[%s] Not able to find alert level element for detailed view." % self.fileName)
                return True

            # get all sensors that belong to the focused alert level
            currentSensors = self._getSensorsOfAlertLevel(currentElement.alertLevel)

            # get all alerts that belong to the focused alert level
            currentAlerts = self._getAlertsOfAlertLevel(currentElement.alertLevel)

            curr_profiles = list(filter(lambda x: x.id in currentElement.alertLevel.profiles,
                                        self.system_data.get_profiles_list(order_by_id=True)))
            self.detailedView = AlertLevelDetailedUrwid(currentElement.alertLevel,
                                                        currentSensors,
                                                        currentAlerts,
                                                        curr_profiles)

        # show detailed view as an overlay
        overlayView = urwid.Overlay(self.detailedView.get(),
                                    self.mainFrame,
                                    align="center",
                                    width=("relative", 80),
                                    min_width=80,
                                    valign="middle",
                                    height=("relative", 80),
                                    min_height=50)
        self.mainLoop.widget = overlayView
        self.inDetailView = True

    # internal function that shows the manager urwid objects given
    # by a page index
    def _showManagersAtPageIndex(self, pageIndex: int):

        # calculate how many pages the manager urwid objects have
        activeLength = len(self.activeManagerUrwidObjects)
        managerPageCount = int(activeLength / self.maxCountShowManagersPerPage)
        if (activeLength % self.maxCountShowManagersPerPage) != 0:
            managerPageCount += 1

        # check if the index to show is within the page range
        if pageIndex >= managerPageCount:
            pageIndex = 0
        elif pageIndex < 0:
            pageIndex = managerPageCount - 1

        logging.debug("[%s]: Update shown managers with page index: %d." % (self.fileName, pageIndex))

        # get all manager urwid objects that should be shown on the new page
        del self.shownManagerUrwidObjects[:]
        for i in range(self.maxCountShowManagersPerPage):
            tempItemIndex = i + (pageIndex * self.maxCountShowManagersPerPage)
            if tempItemIndex >= activeLength:
                break
            self.shownManagerUrwidObjects.append(
                self.activeManagerUrwidObjects[tempItemIndex])

        # delete all old shown manager objects and replace them by the new ones
        del self.managersGrid.contents[:]
        for newShownManager in self.shownManagerUrwidObjects:
            self.managersGrid.contents.append((newShownManager.get(), self.managersGrid.options()))

        # update managers page footer
        tempText = "Page %d / %d " % (pageIndex + 1, managerPageCount)
        self.managersFooter.set_text(tempText)

    # internal function that shows the next page of manager objects
    def _showManagersNextPage(self):

        logging.debug("[%s]: Show next managers page." % self.fileName)

        # calculate how many pages the manager urwid objects have
        activeLength = len(self.activeManagerUrwidObjects)
        managerPageCount = int(activeLength / self.maxCountShowManagersPerPage)
        if managerPageCount == 0:
            return
        if (activeLength % self.maxCountShowManagersPerPage) != 0:
            managerPageCount += 1

        # calculate next page that should be shown
        self.currentManagerPage += 1
        if self.currentManagerPage >= managerPageCount:
            self.currentManagerPage = 0

        # update shown managers
        self._showManagersAtPageIndex(self.currentManagerPage)

    # internal function that shows the previous page of manager objects
    def _showManagersPreviousPage(self):

        logging.debug("[%s]: Show previous managers page." % self.fileName)

        # calculate how many pages the manager urwid objects have
        activeLength = len(self.activeManagerUrwidObjects)
        managerPageCount = int(activeLength / self.maxCountShowManagersPerPage)
        if managerPageCount == 0:
            return
        if (activeLength % self.maxCountShowManagersPerPage) != 0:
            managerPageCount += 1

        # calculate next page that should be shown
        self.currentManagerPage -= 1
        if self.currentManagerPage < 0:
            self.currentManagerPage = managerPageCount - 1

        # update shown managers
        self._showManagersAtPageIndex(self.currentManagerPage)

    def _show_profile_choice_view(self):
        """
        Creates an overlayed view with all profiles to choose from.
        """
        self._profile_choice_view = ProfileChoiceUrwid(self.system_data.get_profiles_list(order_by_id=True),
                                                       self._profile_colors,
                                                       self._callback_profile_choice)

        # show search view as an overlay
        overlayView = urwid.Overlay(self._profile_choice_view.get(),
                                    self.mainFrame,
                                    align="center",
                                    width=("relative", 40),
                                    min_width=80,
                                    valign="middle",
                                    height=("relative", 20),
                                    min_height=5)
        self.mainLoop.widget = overlayView
        self._in_profile_choice_view = True

    # Creates an overlayed view with the search field.
    def _showSearchView(self):

        # noinspection PyTypeChecker
        self.searchView = SearchViewUrwid(self._callbackSearchFieldChange)

        # show search view as an overlay
        overlayView = urwid.Overlay(self.searchView.get(),
                                    self.mainFrame,
                                    align="center",
                                    width=("relative", 80),
                                    min_width=80,
                                    valign="middle",
                                    height=("relative", 5),
                                    min_height=5)
        self.mainLoop.widget = overlayView
        self.inSearchView = True

    # internal function that shows the sensor urwid objects given
    # by a page index
    def _showSensorsAtPageIndex(self, pageIndex: int):

        # calculate how many pages the sensor urwid objects have
        activeLength = len(self.activeSensorUrwidObjects)
        sensorPageCount = int(activeLength / self.maxCountShowSensorsPerPage)
        if (activeLength % self.maxCountShowSensorsPerPage) != 0:
            sensorPageCount += 1

        # check if the index to show is within the page range
        if pageIndex >= sensorPageCount:
            pageIndex = 0
        elif pageIndex < 0:
            pageIndex = sensorPageCount - 1

        logging.debug("[%s]: Update shown sensors with page index: %d." % (self.fileName, pageIndex))

        # get all sensor urwid objects that should be shown on the new page
        del self.shownSensorUrwidObjects[:]
        for i in range(self.maxCountShowSensorsPerPage):
            tempItemIndex = i + (pageIndex * self.maxCountShowSensorsPerPage)
            if tempItemIndex >= activeLength:
                break
            self.shownSensorUrwidObjects.append(
                self.activeSensorUrwidObjects[tempItemIndex])

        # delete all old shown sensor objects and replace them by the new ones
        del self.sensorsGrid.contents[:]
        for newShownSensor in self.shownSensorUrwidObjects:
            self.sensorsGrid.contents.append((newShownSensor.get(), self.sensorsGrid.options()))

        # update sensors page footer
        tempText = "Page %d / %d " % (pageIndex + 1, sensorPageCount)
        self.sensorsFooter.set_text(tempText)

    # internal function that shows the next page of sensor objects
    def _showSensorsNextPage(self):

        logging.debug("[%s]: Show next sensors page." % self.fileName)

        # calculate how many pages the sensor urwid objects have
        activeLength = len(self.activeSensorUrwidObjects)
        sensorPageCount = int(activeLength / self.maxCountShowSensorsPerPage)
        if sensorPageCount == 0:
            return
        if (activeLength % self.maxCountShowSensorsPerPage) != 0:
            sensorPageCount += 1

        # calculate next page that should be shown
        self.currentSensorPage += 1
        if self.currentSensorPage >= sensorPageCount:
            self.currentSensorPage = 0

        # update shown sensors
        self._showSensorsAtPageIndex(self.currentSensorPage)

    # internal function that shows the previous page of sensor objects
    def _showSensorsPreviousPage(self):

        logging.debug("[%s]: Show previous sensors page." % self.fileName)

        # calculate how many pages the sensor urwid objects have
        activeLength = len(self.activeSensorUrwidObjects)
        sensorPageCount = int(activeLength / self.maxCountShowSensorsPerPage)
        if sensorPageCount == 0:
            return
        if (activeLength % self.maxCountShowSensorsPerPage) != 0:
            sensorPageCount += 1

        # calculate next page that should be shown
        self.currentSensorPage -= 1
        if self.currentSensorPage < 0:
            self.currentSensorPage = sensorPageCount - 1

        # update shown sensors
        self._showSensorsAtPageIndex(self.currentSensorPage)

    # Resets the search result and display all elements again.
    def _resetSearchResult(self):

        self.searchKeyword = ""

        if self.currentFocused == FocusedElement.sensors:
            self.activeSensorUrwidObjects = list(self.sensorUrwidObjects)
            self._showSensorsAtPageIndex(0)
        
        elif self.currentFocused == FocusedElement.alerts:
            self.activeAlertUrwidObjects = list(self.alertUrwidObjects)
            self._showAlertsAtPageIndex(0)

        elif self.currentFocused == FocusedElement.managers:
            self.activeManagerUrwidObjects = list(self.managerUrwidObjects)
            self._showManagersAtPageIndex(0)

        elif self.currentFocused == FocusedElement.alertLevels:
            self.activeAlertLevelUrwidObjects = list(
                self.alertLevelUrwidObjects)
            self._showAlertLevelsAtPageIndex(0)

    # this function is called to update the screen
    def updateScreen(self, status: str) -> bool:

        # write status to the callback file descriptor
        if self.screenFd is not None:

            # Lock is closed in screenCallback() function which handles our request.
            self._acquireLock()

            os.write(self.screenFd, status.encode("ascii"))
            return True
        return False

    # this function is called if a key/mouse input was made
    def handleKeypress(self, key: str) -> bool:

        # check if key b/B is pressed => show previous page of focused elements
        if key in ["b", "B"]:
            if not self.inDetailView and not self.inSearchView and not self._in_profile_choice_view:
                if self.currentFocused == FocusedElement.sensors:
                    self._showSensorsPreviousPage()

                elif self.currentFocused == FocusedElement.alerts:
                    self._showAlertsPreviousPage()

                elif self.currentFocused == FocusedElement.managers:
                    self._showManagersPreviousPage()

                else:
                    self._showAlertLevelsPreviousPage()

        # check if key n/N is pressed => show next page of focused elements
        elif key in ["n", "N"]:
            if not self.inDetailView and not self.inSearchView and not self._in_profile_choice_view:
                if self.currentFocused == FocusedElement.sensors:
                    self._showSensorsNextPage()

                elif self.currentFocused == FocusedElement.alerts:
                    self._showAlertsNextPage()

                elif self.currentFocused == FocusedElement.managers:
                    self._showManagersNextPage()

                else:
                    self._showAlertLevelsNextPage()

        # change focus to next element group
        # order: (sensors, alerts, managers, alert levels)
        elif key in ["tab"]:
            if not self.inDetailView and not self.inSearchView and not self._in_profile_choice_view:
                if self.searchKeyword != "":
                    self._resetSearchResult()
                self._switchFocusedElementGroup()

        # move focus to next element in the element group
        elif key in ["up", "down", "left", "right"]:
            if not self.inDetailView and not self.inSearchView and not self._in_profile_choice_view:
                self._moveFocus(key)

        # when an overlayed view is shown
        # => go back to main view
        # when in main view
        # => exit
        elif key in ["esc"]:
            if self.inDetailView:
                self._closeDetailedView()

            elif self.inSearchView:
                self._resetSearchResult()
                self._closeSearchView()

            elif self.searchKeyword != "":
                self._resetSearchResult()

            elif self._in_profile_choice_view:
                self._close_profile_choice_view()

            else:
                raise urwid.ExitMainLoop()

        # Open overlayed view with detailed information
        # or apply search keyword.
        elif key in ["enter"]:
            if self.inSearchView:

                keyword = self.searchView.getText()
                self.searchKeyword = keyword.lower()

                self._showSearchResult()

                self._closeSearchView()

            elif not self.inDetailView and not self._in_profile_choice_view:
                self._showDetailedView()

        # Open overlayed view with search field.
        elif key in ["s", "S"]:
            if not self.inDetailView and not self.inSearchView and not self._in_profile_choice_view:
                self._showSearchView()

        elif key in ["p", "P"]:
            if not self.inDetailView and not self.inSearchView and not self._in_profile_choice_view:
                self._show_profile_choice_view()

        return True

    # this function initializes the urwid objects and displays
    # them (it starts also the urwid main loop and will not
    # return unless the client is terminated)
    def startConsole(self):

        # generate all sensor urwid objects
        for sensor in self.system_data.get_sensors_list(order_by_desc=True):

            # get node the sensor belongs to
            nodeSensorBelongs = self.system_data.get_node_by_id(sensor.nodeId)
            if nodeSensorBelongs is None:
                raise ValueError("Could not find a node the sensor belongs to.")
            elif nodeSensorBelongs.nodeType != "sensor" and nodeSensorBelongs.nodeType != "server":
                raise ValueError('Node the sensor belongs to is not of type "sensor" or "server".')

            # create new sensor urwid object
            # (also links urwid object to sensor object)
            sensorUrwid = SensorUrwid(sensor, nodeSensorBelongs, self.connectionTimeout, self.serverEventHandler)

            # Append the final sensor urwid object to the list
            # of sensor objects.
            self.sensorUrwidObjects.append(sensorUrwid)
            self.activeSensorUrwidObjects.append(sensorUrwid)

        # check if sensor urwid objects list is not empty
        if self.activeSensorUrwidObjects:

            # get the sensor objects for the first page
            for i in range(self.maxCountShowSensorsPerPage):
                # break if there are less sensor urwid objects than should
                # be shown
                if i >= len(self.activeSensorUrwidObjects):
                    break
                self.shownSensorUrwidObjects.append(self.activeSensorUrwidObjects[i])

            # create grid object for the sensors
            self.sensorsGrid = urwid.GridFlow([x.get() for x in self.shownSensorUrwidObjects],
                                              40,
                                              1,
                                              1,
                                              'left')

        else:
            # create empty grid object for the sensors
            self.sensorsGrid = urwid.GridFlow([], 40, 1, 1, 'left')

        # calculate how many pages the sensor urwid objects have
        activeLength = len(self.activeSensorUrwidObjects)
        sensorPageCount = int(activeLength / self.maxCountShowSensorsPerPage)
        if (activeLength % self.maxCountShowSensorsPerPage) != 0:
            sensorPageCount += 1

        # generate footer text for sensors box
        tempText = "Page 1 / %d " % sensorPageCount 
        self.sensorsFooter = urwid.Text(tempText, align='center')
        self.sensorsKeyBindings = urwid.Text("Keys: b - Previous Page, n - Next Page, s - Search", align='center')

        # build box around the sensor grid with title
        self.sensorsBox = urwid.LineBox(urwid.Pile([self.sensorsGrid,
                                                    urwid.Divider(),
                                                    self.sensorsFooter,
                                                    self.sensorsKeyBindings]),
                                        title="Sensors")

        # generate all manager urwid objects
        for manager in self.system_data.get_managers_list(order_by_desc=True):

            # get node the manager belongs to
            nodeManagerBelongs = self.system_data.get_node_by_id(manager.nodeId)
            if nodeManagerBelongs is None:
                raise ValueError("Could not find a node the manager belongs to.")
            elif nodeManagerBelongs.nodeType != "manager":
                raise ValueError('Node the manager belongs to is not of type "manager"')

            # create new manager urwid object
            # (also links urwid object to manager object)
            managerUrwid = ManagerUrwid(manager, nodeManagerBelongs)

            # append the final manager urwid object to the list
            # of manager objects
            self.managerUrwidObjects.append(managerUrwid)
            self.activeManagerUrwidObjects.append(managerUrwid)

        # check if manager urwid objects list is not empty
        if self.activeManagerUrwidObjects:

            # get the manager objects for the first page
            for i in range(self.maxCountShowManagersPerPage):
                # break if there are less manager urwid objects than should
                # be shown
                if i >= len(self.activeManagerUrwidObjects):
                    break
                self.shownManagerUrwidObjects.append(self.activeManagerUrwidObjects[i])

            # create grid object for the managers
            self.managersGrid = urwid.GridFlow([x.get() for x in self.shownManagerUrwidObjects],
                                               40,
                                               1,
                                               1,
                                               'left')
        else:
            # create empty grid object for the managers
            self.managersGrid = urwid.GridFlow([], 40, 1, 1, 'left')

        # calculate how many pages the manager urwid objects have
        activeLength = len(self.activeManagerUrwidObjects)
        managerPageCount = int(activeLength / self.maxCountShowManagersPerPage)
        if (activeLength % self.maxCountShowManagersPerPage) != 0:
            managerPageCount += 1

        # generate footer text for sensors box
        tempText = "Page 1 / %d " % managerPageCount 
        self.managersFooter = urwid.Text(tempText, align='center')
        self.managersKeyBindings = urwid.Text("Keys: None", align='center')

        # build box around the manager grid with title
        self.managersBox = urwid.LineBox(urwid.Pile([self.managersGrid,
                                                     urwid.Divider(),
                                                     self.managersFooter,
                                                     self.managersKeyBindings]),
                                         title="Manager Clients")

        self.leftDisplayPart = urwid.Pile([self.sensorsBox, self.managersBox])

        # generate all alert urwid objects
        for alert in self.system_data.get_alerts_list(order_by_desc=True):

            # get node the alert belongs to
            nodeAlertBelongs = self.system_data.get_node_by_id(alert.nodeId)
            if nodeAlertBelongs is None:
                raise ValueError("Could not find a node the alert belongs to.")
            elif nodeAlertBelongs.nodeType != "alert":
                raise ValueError('Node the alert belongs to is not of type "alert"')

            # create new alert urwid object
            # (also links urwid object to alert object)
            alertUrwid = AlertUrwid(alert, nodeAlertBelongs)

            # append the final alert urwid object to the list
            # of alert objects
            self.alertUrwidObjects.append(alertUrwid)
            self.activeAlertUrwidObjects.append(alertUrwid)

        # check if alert urwid objects list is not empty
        if self.activeAlertUrwidObjects:

            # get the alert objects for the first page
            for i in range(self.maxCountShowAlertsPerPage):
                # break if there are less alert urwid objects than should
                # be shown
                if i >= len(self.activeAlertUrwidObjects):
                    break
                self.shownAlertUrwidObjects.append(
                    self.activeAlertUrwidObjects[i])

            # create grid object for the alerts
            self.alertsGrid = urwid.GridFlow([x.get() for x in self.shownAlertUrwidObjects],
                                             40,
                                             1,
                                             1,
                                             'left')
        else:
            # create empty grid object for the alerts
            self.alertsGrid = urwid.GridFlow([], 40, 1, 1, 'left')

        # calculate how many pages the alert urwid objects have
        activeLength = len(self.activeAlertUrwidObjects)
        alertPageCount = int(activeLength / self.maxCountShowAlertsPerPage)
        if (activeLength % self.maxCountShowAlertsPerPage) != 0:
            alertPageCount += 1

        # generate footer text for sensors box
        tempText = "Page 1 / %d " % alertPageCount 
        self.alertsFooter = urwid.Text(tempText, align='center')
        self.alertsKeyBindings = urwid.Text("Keys: None", align='center')

        # build box around the alert grid with title
        self.alertsBox = urwid.LineBox(urwid.Pile([self.alertsGrid,
                                                   urwid.Divider(),
                                                   self.alertsFooter,
                                                   self.alertsKeyBindings]),
                                       title="Alert Clients")

        # generate all alert level urwid objects
        for alertLevel in self.system_data.get_alert_levels_list(order_by_level=True):

            # create new alert level urwid object
            # (also links urwid object to alert level object)
            alertLevelUrwid = AlertLevelUrwid(alertLevel)

            # append the final alert level urwid object to the list
            # of alert level objects
            self.alertLevelUrwidObjects.append(alertLevelUrwid)
            self.activeAlertLevelUrwidObjects.append(alertLevelUrwid)

        # check if alert level urwid objects list is not empty
        if self.activeAlertLevelUrwidObjects:

            # get the alert level objects for the first page
            for i in range(self.maxCountShowAlertLevelsPerPage):
                # break if there are less alert level urwid objects than should
                # be shown
                if i >= len(self.activeAlertLevelUrwidObjects):
                    break
                self.shownAlertLevelUrwidObjects.append(
                    self.activeAlertLevelUrwidObjects[i])

            # create grid object for the alert levels
            self.alertLevelsGrid = urwid.GridFlow([x.get() for x in self.shownAlertLevelUrwidObjects],
                                                  40,
                                                  1,
                                                  1,
                                                  'left')
        else:
            # create empty grid object for the alert levels
            self.alertLevelsGrid = urwid.GridFlow([], 40, 1, 1, 'left')

        # calculate how many pages the alert level urwid objects have
        activeLength = len(self.activeAlertLevelUrwidObjects)
        alertLevelPageCount = int(activeLength / self.maxCountShowAlertLevelsPerPage)
        if (activeLength % self.maxCountShowAlertLevelsPerPage) != 0:
            alertLevelPageCount += 1

        # generate footer text for sensors box
        tempText = "Page 1 / %d " % alertLevelPageCount 
        self.alertLevelsFooter = urwid.Text(tempText, align='center')
        self.alertLevelsKeyBindings = urwid.Text("Keys: None", align='center')

        # build box around the alert level grid with title
        self.alertLevelsBox = urwid.LineBox(urwid.Pile([self.alertLevelsGrid,
                                                        urwid.Divider(),
                                                        self.alertLevelsFooter,
                                                        self.alertLevelsKeyBindings]),
                                            title="Alert Levels")

        # create empty sensor alerts pile
        emptySensorAlerts = list()
        self.emtpySensorAlert = urwid.Text("")
        for i in range(self.maxCountShowSensorAlert):
            emptySensorAlerts.append(self.emtpySensorAlert)
        self.sensorAlertsPile = urwid.Pile(emptySensorAlerts)

        # build box around the sensor alerts grid with title
        sensorAlertsBox = urwid.LineBox(self.sensorAlertsPile, title="List of Triggered Sensor Alerts")

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
        self.connectionStatus = StatusUrwid("Connection Status", "Status", "Online")
        self.connectionStatus.set_color("neutral")

        # generate a column for the status widgets
        statusColumn = urwid.Columns([self._profile_urwid.get(), self.connectionStatus.get()])

        # generate right part of the display
        self.rightDisplayPart = urwid.Pile([statusColumn, sensorAlertsBox, self.alertsBox, self.alertLevelsBox])

        # generate final body object
        self.finalBody = urwid.Columns([self.leftDisplayPart, self.rightDisplayPart])
        fillerBody = urwid.Filler(self.finalBody, "top")

        # generate header and footer
        header = urwid.Text("AlertR Console Manager", align="center")
        footer = urwid.Text("Keys: "
                            + "p - Change Profile, "
                            + "ESC - Back/Quit, "
                            + "TAB - Next Elements, "
                            + "Up/Down/Left/Right - Move Cursor, "
                            + "Enter - Select Element")

        # build frame for final rendering
        self.mainFrame = urwid.Frame(fillerBody, footer=footer, header=header)

        # color palette
        palette = [
            ('redColor', 'black', 'dark red'),
            ('redColor_focus', 'black', 'light red'),
            ('greenColor', 'black', 'dark green'),
            ('greenColor_focus', 'black', 'light green'),
            ('grayColor', 'black', 'dark gray'),
            ('grayColor_focus', 'black', 'light gray'),
            ('connected', 'black', 'dark green'),
            ('connected_focus', 'black', 'light green'),
            ('disconnected', 'black', 'dark red'),
            ('disconnected_focus', 'black', 'light red'),
            ('sensoralert', 'black', 'dark cyan'),
            ('sensoralert_focus', 'black', 'light cyan'),
            ('connectionfail', 'black', 'dark gray'),
            ('connectionfail_focus', 'black', 'light gray'),
            ('timedout', 'black', 'dark magenta'),
            ('timedout_focus', 'black', 'light magenta'),
            ('neutral', '', ''),
            ('profile_0', 'black', 'dark green'),
            ('profile_1', 'black', 'dark red'),
            ('profile_2', 'black', 'dark cyan'),
            ('profile_3', 'black', 'dark magenta'),
            ('profile_4', 'black', 'yellow'),
        ]

        # set focus on sensor
        self.currentFocused = FocusedElement.sensors

        # create urwid main loop for the rendering
        self.mainLoop = urwid.MainLoop(self.mainFrame, palette=palette, unhandled_input=self.handleKeypress)

        # create a file descriptor callback to give other
        # threads the ability to communicate with the urwid thread
        self.screenFd = self.mainLoop.watch_pipe(self.screenCallback)

        # rut urwid loop
        self.mainLoop.run()

    # this function will be called from the urwid main loop
    # when the file descriptor of the callback
    # gets data written to it and updates the screen elements
    def screenCallback(self, received_data: bytes) -> bool:

        received_str = received_data.decode("ascii")

        # if received data equals "status" or "sensoralert"
        # update the whole screen (in case of a sensor alert it can happen
        # that also a normal state change was received before and is forgotten
        # if a normal status update is not made)
        if received_str == "status" or received_str == "sensoralert":
            logging.debug("[%s]: Status update received. Updating screen elements." % self.fileName)

            # update connection status urwid widget
            self.connectionStatus.update_value("Online")
            self.connectionStatus.set_color("neutral")

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
                            self.sensorAlertUrwidObjects.remove(sensorAlertUrwid)

            # update the information of all sensor urwid widgets
            for sensorUrwidObject in self.sensorUrwidObjects:
                # if update method returns false
                # => sensor object no longer exists
                # => remove it 
                if not sensorUrwidObject.updateCompleteWidget():

                    # Remove sensor urwid object from the list of the
                    # currently shown objects if it is shown.
                    if sensorUrwidObject in self.shownSensorUrwidObjects:
                        self.shownSensorUrwidObjects.remove(sensorUrwidObject)

                        # update shown sensors
                        self._showSensorsAtPageIndex(self.currentSensorPage)

                    # Remove sensor urwid object from the list of the
                    # currently active objects.
                    if sensorUrwidObject in self.activeSensorUrwidObjects:
                        self.activeSensorUrwidObjects.remove(sensorUrwidObject)

                    # remove sensor urwid object from list of objects
                    # to delete all references to object
                    # => object will be deleted by garbage collector
                    self.sensorUrwidObjects.remove(sensorUrwidObject)

                    # if the detailed view is shown and this sensor was removed
                    # => close detailed view
                    if (self.inDetailView
                            and self.detailedView.sensor not in self.system_data.get_sensors_list()):
                        self._closeDetailedView()

                # if the detailed view is shown of a sensor
                # => update the information shown for the corresponding sensor
                else:
                    if (self.inDetailView
                       and self.currentFocused == FocusedElement.sensors
                       and self.detailedView.sensor == sensorUrwidObject.sensor):

                        objAlertLevels = self._getAlertLevelsOfObj(sensorUrwidObject.sensor)
                        self.detailedView.updateCompleteWidget(objAlertLevels)

            # add all sensors that were newly added
            for sensor in self.system_data.get_sensors_list(order_by_desc=True):
                # check if a new sensor was added
                if "urwid" not in sensor.internal_data.keys():
                    # get node the sensor belongs to
                    nodeSensorBelongs = self.system_data.get_node_by_id(sensor.nodeId)
                    if nodeSensorBelongs is None:
                        raise ValueError("Could not find a node the sensor belongs to.")
                    elif nodeSensorBelongs.nodeType != "sensor" and nodeSensorBelongs.nodeType != "server":
                        raise ValueError('Node the sensor belongs to is not of type "sensor" or "server".')

                    # create new sensor urwid object
                    # (also links urwid object to sensor object)
                    sensorUrwid = SensorUrwid(sensor,
                                              nodeSensorBelongs,
                                              self.connectionTimeout,
                                              self.serverEventHandler)

                    # Append the final sensor urwid object to the list
                    # of sensor objects.
                    self.sensorUrwidObjects.append(sensorUrwid)

                    # Add it to active sensor urwid objects if sensors
                    # are not focused.
                    if self.currentFocused != FocusedElement.sensors:
                        self.activeSensorUrwidObjects.append(sensorUrwid)

                    # Add it to active sensor urwid objects if we do not
                    # search anything or the keyword does match the sensor.
                    else:
                        if self.searchKeyword == "" or self.searchKeyword in sensorUrwid.sensor.description.lower():
                            self.activeSensorUrwidObjects.append(sensorUrwid)

                    # update shown sensors
                    self._showSensorsAtPageIndex(self.currentSensorPage)

            # update the information of all alert urwid widgets
            for alertUrwidObject in self.alertUrwidObjects:
                # if update method returns false
                # => alert object no longer exists
                # => remove it 
                if not alertUrwidObject.updateCompleteWidget():

                    # remove alert urwid object from the list of the
                    # current shown objects if it is shown
                    if alertUrwidObject in self.shownAlertUrwidObjects:
                        self.shownAlertUrwidObjects.remove(alertUrwidObject)

                        # update shown alerts
                        self._showAlertsAtPageIndex(self.currentAlertPage)

                    # Remove alert urwid object from the list of the
                    # currently active objects.
                    if alertUrwidObject in self.activeAlertUrwidObjects:
                        self.activeAlertUrwidObjects.remove(alertUrwidObject)

                    # remove alert urwid object from list of objects
                    # to delete all references to object
                    # => object will be deleted by garbage collector
                    self.alertUrwidObjects.remove(alertUrwidObject)

                    # if the detailed view is shown and this alert
                    # was removed
                    # => close detailed view
                    if (self.inDetailView
                            and self.detailedView.alert not in self.system_data.get_alerts_list()):
                        self._closeDetailedView()

                # if the detailed view is shown of an alert
                # => update the information shown for the corresponding alert
                else:
                    if (self.inDetailView
                       and self.currentFocused == FocusedElement.alerts
                       and self.detailedView.alert == alertUrwidObject.alert):

                        objAlertLevels = self._getAlertLevelsOfObj(alertUrwidObject.alert)
                        self.detailedView.updateCompleteWidget(objAlertLevels)

            # add all alerts that were newly added
            for alert in self.system_data.get_alerts_list(order_by_desc=True):
                # check if a new alert was added
                if "urwid" not in alert.internal_data.keys():
                    # get node the alert belongs to
                    nodeAlertBelongs = self.system_data.get_node_by_id(alert.nodeId)
                    if nodeAlertBelongs is None:
                        raise ValueError("Could not find a node the alert belongs to.")
                    elif nodeAlertBelongs.nodeType != "alert":
                        raise ValueError('Node the alert belongs to is not of type "alert".')

                    # create new alert urwid object
                    # (also links urwid object to alert object)
                    alertUrwid = AlertUrwid(alert, nodeAlertBelongs)

                    # append the final alert urwid object to the list
                    # of alert objects
                    self.alertUrwidObjects.append(alertUrwid)

                    # Add it to active alert urwid objects if alerts
                    # are not focused.
                    if self.currentFocused != FocusedElement.alerts:
                        self.activeAlertUrwidObjects.append(alertUrwid)

                    # Add it to active alert urwid objects if we do not
                    # search anything or the keyword does match the alert.
                    else:
                        if self.searchKeyword == "" or self.searchKeyword in alertUrwid.alert.description.lower():
                            self.activeAlertUrwidObjects.append(alertUrwid)

                    # update shown alerts
                    self._showAlertsAtPageIndex(self.currentAlertPage)

            # update the information of all manager urwid widgets
            for managerUrwidObject in self.managerUrwidObjects:
                # if update method returns false
                # => manager object no longer exists
                # => remove it 
                if not managerUrwidObject.updateCompleteWidget():

                    # remove manager urwid object from the list of the
                    # current shown objects if it is shown
                    if managerUrwidObject in self.shownManagerUrwidObjects:
                        self.shownManagerUrwidObjects.remove(managerUrwidObject)

                        # update shown managers
                        self._showManagersAtPageIndex(self.currentManagerPage)

                    # Remove manager urwid object from the list of the
                    # currently active objects.
                    if managerUrwidObject in self.activeManagerUrwidObjects:
                        self.activeManagerUrwidObjects.remove(managerUrwidObject)

                    # remove manager urwid object from list of objects
                    # to delete all references to object
                    # => object will be deleted by garbage collector
                    self.managerUrwidObjects.remove(managerUrwidObject)

                    # if the detailed view is shown and this manager
                    # was removed
                    # => close detailed view
                    if (self.inDetailView
                            and self.detailedView.manager not in self.system_data.get_managers_list()):
                        self._closeDetailedView()

                # if the detailed view is shown of a manager
                # => update the information shown for the corresponding manager
                else:
                    if (self.inDetailView
                       and self.currentFocused == FocusedElement.managers
                       and self.detailedView.manager == managerUrwidObject.manager):

                        self.detailedView.updateCompleteWidget()

            # add all managers that were newly added
            for manager in self.system_data.get_managers_list(order_by_desc=True):
                # check if a new manager was added
                if "urwid" not in manager.internal_data.keys():
                    # get node the manager belongs to
                    nodeManagerBelongs = self.system_data.get_node_by_id(manager.nodeId)
                    if nodeManagerBelongs is None:
                        raise ValueError("Could not find a node the manager belongs to.")
                    elif nodeManagerBelongs.nodeType != "manager":
                        raise ValueError('Node the manager belongs to is not of type "manager".')

                    # create new manager urwid object
                    # (also links urwid object to manager object)
                    managerUrwid = ManagerUrwid(manager, nodeManagerBelongs)

                    # append the final manager urwid object to the list
                    # of manager objects
                    self.managerUrwidObjects.append(managerUrwid)

                    # Add it to active manager urwid objects if managers
                    # are not focused.
                    if self.currentFocused != FocusedElement.managers:

                        self.activeManagerUrwidObjects.append(managerUrwid)

                    # Add it to active manager urwid objects if we do not
                    # search anything or the keyword does match the manager.
                    else:
                        if self.searchKeyword == "" or self.searchKeyword in managerUrwid.manager.description.lower():
                            self.activeManagerUrwidObjects.append(managerUrwid)

                    # update shown managers
                    self._showManagersAtPageIndex(self.currentManagerPage)

            # update the information of all alert level urwid widgets
            for alertLevelUrwidObject in self.alertLevelUrwidObjects:
                # if update method returns false
                # => alert level object no longer exists
                # => remove it 
                if not alertLevelUrwidObject.updateCompleteWidget():

                    # remove alert level urwid object from the list of the
                    # current shown objects if it is shown
                    if alertLevelUrwidObject in self.shownAlertLevelUrwidObjects:
                        self.shownAlertLevelUrwidObjects.remove(alertLevelUrwidObject)

                        # update shown alert levels
                        self._showAlertLevelsAtPageIndex(self.currentAlertLevelPage)

                    # Remove alert level urwid object from the list of the
                    # currently active objects.
                    if alertLevelUrwidObject in self.activeAlertLevelUrwidObjects:
                        self.activeAlertLevelUrwidObjects.remove(alertLevelUrwidObject)

                    # remove alert level urwid object from list of objects
                    # to delete all references to object
                    # => object will be deleted by garbage collector
                    self.alertLevelUrwidObjects.remove(alertLevelUrwidObject)

                    # if the detailed view is shown and this alert level
                    # was removed
                    # => close detailed view
                    if (self.inDetailView
                            and self.detailedView.alertLevel not in self.system_data.get_alert_levels_list()):
                        self._closeDetailedView()

                # if the detailed view is shown of a manager
                # => update the information shown for the corresponding manager
                else:
                    if (self.inDetailView
                       and self.currentFocused == FocusedElement.alertLevels
                       and self.detailedView.alertLevel == alertLevelUrwidObject.alertLevel):

                        # get all sensors that belong to the focused
                        # alert level
                        currentSensors = self._getSensorsOfAlertLevel(alertLevelUrwidObject.alertLevel)

                        # get all alerts that belong to the focused alert level
                        currentAlerts = self._getAlertsOfAlertLevel(alertLevelUrwidObject.alertLevel)

                        curr_profiles = list(filter(lambda x: x.id in alertLevelUrwidObject.alertLevel.profiles,
                                                    self.system_data.get_profiles_list(order_by_id=True)))

                        self.detailedView.updateCompleteWidget(currentSensors, currentAlerts, curr_profiles)

            # add all alert levels that were newly added
            for alertLevel in self.system_data.get_alert_levels_list(order_by_level=True):
                # check if a new alert level was added
                if "urwid" not in alertLevel.internal_data.keys():
                    # create new alert level urwid object
                    # (also links urwid object to alert level object)
                    alertLevelUrwid = AlertLevelUrwid(alertLevel)

                    # append the final alert level urwid object to the list
                    # of alert level objects
                    self.alertLevelUrwidObjects.append(alertLevelUrwid)

                    # Add it to active alert level urwid objects if
                    # alert levels are not focused.
                    if self.currentFocused != FocusedElement.alertLevels:

                        self.activeAlertLevelUrwidObjects.append(alertLevelUrwid)

                    # Add it to active alert level urwid objects if we do not
                    # search anything or the keyword does match the
                    # alert level.
                    else:
                        if self.searchKeyword == "" or self.searchKeyword in alertLevelUrwid.alertLevel.name.lower():
                            self.activeAlertLevelUrwidObjects.append(alertLevelUrwid)

                    # update shown alert levels
                    self._showAlertLevelsAtPageIndex(self.currentAlertLevelPage)

        # check if the connection to the server failed
        elif received_str == "connectionfail":
            logging.debug("[%s]: Status connection failed received. Updating screen elements." % self.fileName)

            # update connection status urwid widget
            self.connectionStatus.update_value("Offline")
            self.connectionStatus.set_color("redColor")

            # update alert system active widget
            self._profile_urwid.set_color("grayColor")

            # update all sensor urwid widgets
            for sensorUrwidObject in self.sensorUrwidObjects:
                sensorUrwidObject.setConnectionFail()

            # update all alert urwid widgets
            for alertUrwidObject in self.alertUrwidObjects:
                alertUrwidObject.setConnectionFail()

            # update all manager urwid widgets
            for managerUrwidObject in self.managerUrwidObjects:
                managerUrwidObject.setConnectionFail()

            # update all alert level urwid widgets
            for alertLevelUrwidObject in self.alertLevelUrwidObjects:
                alertLevelUrwidObject.setConnectionFail()

        # check if a sensor alert was received from the server
        if received_str == "sensoralert":

            logging.debug("[%s]: Sensor alert received. Updating screen elements." % self.fileName)

            # output all sensor alerts
            for sensorAlert in self.system_data.get_sensor_alerts_list():

                sensor = self.system_data.get_sensor_by_id(sensorAlert.sensorId)

                # Only update sensor state information if the flag
                # was set in the received message.
                if sensorAlert.changeState:
                    sensor.internal_data["urwid"].updateState(sensorAlert.state)

                sensor.internal_data["urwid"].updateLastUpdated(sensorAlert.timeReceived)

                # get description for the sensor alert to add
                description = sensor.description

                # differentiate if sensor alert was triggered
                # for a "triggered" or "normal" state
                if sensorAlert.state == 0:
                    description += " (normal)"
                elif sensorAlert.state == 1:
                    description += " (triggered)"
                else:
                    description += " (undefined)"

                # check if more sensor alerts are shown than are received
                # => there still exists empty sensor alerts
                # => remove them first
                if len(self.sensorAlertsPile.contents) > len(self.sensorAlertUrwidObjects):

                    # search for an empty sensor alert and remove it
                    for pileTuple in self.sensorAlertsPile.contents:
                        if self.emtpySensorAlert == pileTuple[0]:
                            self.sensorAlertsPile.contents.remove(pileTuple)
                            break

                # remove the first sensor alert object
                # (the first one is the oldest because of the appending)
                else:
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
                            self.sensorAlertUrwidObjects.remove(sensorAlertWidgetToRemove)
                            break

                # create new sensor alert urwid object
                sensorAlertUrwid = SensorAlertUrwid(sensorAlert, description, self.timeShowSensorAlert)

                # add sensor alert urwid object to the list of
                # sensor alerts urwid objects
                self.sensorAlertUrwidObjects.append(sensorAlertUrwid)

                # insert sensor alert as first element in the list
                # => new sensor alerts will be displayed on top
                self.sensorAlertsPile.contents.insert(0, (sensorAlertUrwid.get(), self.sensorAlertsPile.options()))

                # Remove sensor alert (as well as all others) from the list of sensor alerts,
                # we only care for displaying them.
                self.system_data.delete_sensor_alerts_received_before(sensorAlert.timeReceived + 1)

        # return true so the file descriptor will NOT be closed
        self._releaseLock()
        return True
