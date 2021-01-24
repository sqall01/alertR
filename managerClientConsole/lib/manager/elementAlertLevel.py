#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import urwid
from typing import List
from ..globalData import ManagerObjSensor, ManagerObjAlert, ManagerObjAlertLevel, ManagerObjProfile, SensorDataType


# this class is an urwid object for an alert level
class AlertLevelUrwid:

    def __init__(self, alertLevel: ManagerObjAlertLevel):
        # store reference to alert level object
        self.alertLevel = alertLevel

        # store reference in alert level object to
        # this urwid alert level object
        self.alertLevel.internal_data["urwid"] = self

        alertLevelPileList = list()
        self.nameWidget = urwid.Text("Name: " + self.alertLevel.name)
        alertLevelPileList.append(self.nameWidget)

        alertLevelPile = urwid.Pile(alertLevelPileList)
        alertLevelBox = urwid.LineBox(alertLevelPile, title="Level: %d" % self.alertLevel.level)
        paddedAlertLevelBox = urwid.Padding(alertLevelBox, left=1, right=1)

        # set the color of the urwid object
        self.alertLevelUrwidMap = urwid.AttrMap(paddedAlertLevelBox, "greenColor")
        self.alertLevelUrwidMap.set_focus_map({None: "greenColor_focus"})

    # this function returns the final urwid widget that is used
    # to render the box of an alert level
    def get(self) -> urwid.AttrMap:
        return self.alertLevelUrwidMap

    # this function updates the description of the object
    def updateName(self, name: str):
        self.nameWidget.set_text("Name: " + name)

    # this function changes the color of this urwid object to red
    def turnRed(self):
        self.alertLevelUrwidMap.set_attr_map({None: "redColor"})
        self.alertLevelUrwidMap.set_focus_map({None: "redColor_focus"})

    # this function changes the color of this urwid object to green
    def turnGreen(self):
        self.alertLevelUrwidMap.set_attr_map({None: "greenColor"})
        self.alertLevelUrwidMap.set_focus_map({None: "greenColor_focus"})

    # this function changes the color of this urwid object to gray
    def turnGray(self):
        self.alertLevelUrwidMap.set_attr_map({None: "grayColor"})
        self.alertLevelUrwidMap.set_focus_map({None: "grayColor_focus"})

    # this function changes the color of this urwid object to the
    # neutral color scheme
    def turnNeutral(self):
        self.alertLevelUrwidMap.set_attr_map({None: "neutral"})

    # this function updates all internal widgets and checks if
    # the alert level still exists
    def updateCompleteWidget(self):
        # check if alert level still exists
        if self.alertLevel.is_deleted():
            # return false if object no longer exists
            return False

        self.turnGreen()
        self.updateName(self.alertLevel.name)

        # return true if object was updated
        return True

    # this functions sets the color when the connection to the server has failed.
    def setConnectionFail(self):
        self.alertLevelUrwidMap.set_attr_map({None: "connectionfail"})
        self.alertLevelUrwidMap.set_focus_map({None: "connectionfail_focus"})


# this class is an urwid object for a detailed alert level output
class AlertLevelDetailedUrwid:

    def __init__(self,
                 alertLevel: ManagerObjAlertLevel,
                 sensors: List[ManagerObjSensor],
                 alerts: List[ManagerObjAlert],
                 profiles: List[ManagerObjProfile]):

        self.alertLevel = alertLevel

        content = list()

        content.append(urwid.Divider("="))
        content.append(urwid.Text("Alert Level"))
        content.append(urwid.Divider("="))
        temp = self._createAlertLevelWidgetList(alertLevel)
        self.alertLevelPileWidget = urwid.Pile(temp)
        content.append(self.alertLevelPileWidget)

        content.append(urwid.Divider())
        content.append(urwid.Divider("="))
        content.append(urwid.Text("Profiles"))
        content.append(urwid.Divider("="))
        temp = self._create_profiles_widget_list(profiles)
        self._profiles_pile_widget = None
        if temp:
            self._profiles_pile_widget = urwid.Pile(temp)
        else:
            self._profiles_pile_widget = urwid.Pile([urwid.Text("None")])
        content.append(self._profiles_pile_widget)

        content.append(urwid.Divider())
        content.append(urwid.Divider("="))
        content.append(urwid.Text("Alerts"))
        content.append(urwid.Divider("="))
        temp = self._createAlertsWidgetList(alerts)
        self.alertsPileWidget = None
        if temp:
            self.alertsPileWidget = urwid.Pile(temp)
        else:
            self.alertsPileWidget = urwid.Pile([urwid.Text("None")])
        content.append(self.alertsPileWidget)

        content.append(urwid.Divider())
        content.append(urwid.Divider("="))
        content.append(urwid.Text("Sensors"))
        content.append(urwid.Divider("="))
        temp = self._createSensorsWidgetList(sensors)
        self.sensorsPileWidget = None
        if temp:
            self.sensorsPileWidget = urwid.Pile(temp)
        else:
            self.sensorsPileWidget = urwid.Pile([urwid.Text("None")])
        content.append(self.sensorsPileWidget)

        # use ListBox here because it handles all the
        # scrolling part automatically
        detailedList = urwid.ListBox(urwid.SimpleListWalker(content))
        detailedFrame = urwid.Frame(detailedList, footer=urwid.Text("Keys: ESC - Back, Up/Down - Scrolling"))
        self.detailedBox = urwid.LineBox(detailedFrame, title="Alert Level: " + self.alertLevel.name)

    # this function creates the detailed output of a alert level object
    # in a list
    def _createAlertLevelWidgetList(self, alertLevel: ManagerObjAlertLevel) -> List[urwid.Widget]:

        temp = list()

        temp.append(urwid.Text("Alert Level:"))
        temp.append(urwid.Text(str(alertLevel.level)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Name:"))
        temp.append(urwid.Text(alertLevel.name))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Profiles:"))
        profile_str = ", ".join(map(lambda x: str(x), alertLevel.profiles))
        temp.append(urwid.Text(profile_str))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Instrumentation Activated:"))
        if alertLevel.instrumentation_active is None:
            temp.append(urwid.Text("Undefined"))
        elif alertLevel.instrumentation_active:
            temp.append(urwid.Text("Yes"))
            temp.append(urwid.Divider())
            temp.append(urwid.Text("Instrumentation Cmd:"))
            temp.append(urwid.Text(alertLevel.instrumentation_cmd))
            temp.append(urwid.Divider())
            temp.append(urwid.Text("Instrumentation Timeout:"))
            temp.append(urwid.Text(str(alertLevel.instrumentation_timeout) + " Seconds"))
        else:
            temp.append(urwid.Text("No"))

        return temp

    # this function creates the detailed output of all alert objects
    # in a list
    def _createAlertsWidgetList(self, alerts: List[ManagerObjAlert]) -> List[urwid.Widget]:

        temp = list()
        first = True
        for alert in alerts:

            if first:
                first = False
            else:
                temp.append(urwid.Divider())
                temp.append(urwid.Divider("-"))

            temp.extend(self._createAlertWidgetList(alert))

        return temp

    # this function creates the detailed output of a alert object
    # in a list
    def _createAlertWidgetList(self, alert: ManagerObjAlert) -> List[urwid.Widget]:

        temp = list()

        temp.append(urwid.Text("Alert ID:"))
        temp.append(urwid.Text(str(alert.alertId)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Remote Alert ID:"))
        temp.append(urwid.Text(str(alert.remoteAlertId)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Description:"))
        temp.append(urwid.Text(alert.description))

        return temp

    # this function creates the detailed output of all profile objects in a list
    def _create_profiles_widget_list(self, profiles: List[ManagerObjProfile]) -> List[urwid.Widget]:

        temp = list()
        first = True
        for profile in profiles:

            if first:
                first = False
            else:
                temp.append(urwid.Divider())
                temp.append(urwid.Divider("-"))

            temp.extend(self._create_profile_widget_list(profile))

        return temp

    # this function creates the detailed output of a profile object in a list
    def _create_profile_widget_list(self, profile: ManagerObjProfile) -> List[urwid.Widget]:

        temp = list()

        temp.append(urwid.Text("Profile ID:"))
        temp.append(urwid.Text(str(profile.profileId)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Name:"))
        temp.append(urwid.Text(profile.name))

        return temp

    # this function creates the detailed output of all sensor objects
    # in a list
    def _createSensorsWidgetList(self, sensors: List[ManagerObjSensor]) -> List[urwid.Widget]:

        temp = list()
        first = True
        for sensor in sensors:

            if first:
                first = False
            else:
                temp.append(urwid.Divider())
                temp.append(urwid.Divider("-"))

            temp.extend(self._createSensorWidgetList(sensor))

        return temp

    # this function creates the detailed output of a sensor object
    # in a list
    def _createSensorWidgetList(self, sensor: ManagerObjSensor) -> List[urwid.Widget]:

        temp = list()

        temp.append(urwid.Text("Sensor ID:"))
        temp.append(urwid.Text(str(sensor.sensorId)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Remote Sensor ID:"))
        temp.append(urwid.Text(str(sensor.remoteSensorId)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Alert Delay:"))
        temp.append(urwid.Text(str(sensor.alertDelay) + " Seconds"))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Description:"))
        temp.append(urwid.Text(sensor.description))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("State:"))
        if sensor.state == 0:
            temp.append(urwid.AttrMap(urwid.Text("Normal"), "neutral"))
        elif sensor.state == 1:
            temp.append(urwid.AttrMap(urwid.Text("Triggered"), "sensoralert"))
        else:
            temp.append(urwid.AttrMap(urwid.Text("Undefined"), "redColor"))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Data Type:"))
        if sensor.dataType == SensorDataType.NONE:
            temp.append(urwid.Text("None"))
        elif sensor.dataType == SensorDataType.INT:
            temp.append(urwid.Text("Integer"))
        elif sensor.dataType == SensorDataType.FLOAT:
            temp.append(urwid.Text("Floating Point"))
        else:
            temp.append(urwid.Text("Unknown"))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Data:"))
        if sensor.dataType == SensorDataType.NONE:
            temp.append(urwid.Text("None"))
        else:
            temp.append(urwid.Text(str(sensor.data)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Last Updated (Server Time):"))
        lastUpdatedWidget = urwid.Text(time.strftime("%D %H:%M:%S", time.localtime(sensor.lastStateUpdated)))
        temp.append(lastUpdatedWidget)

        return temp

    # this function returns the final urwid widget that is used
    # to render this object
    def get(self) -> urwid.LineBox:
        return self.detailedBox

    # this function updates all internal widgets
    def updateCompleteWidget(self,
                             sensors: List[ManagerObjSensor],
                             alerts: List[ManagerObjAlert],
                             profiles: List[ManagerObjProfile]):
        self.updateAlertLevelDetails()
        self.updateSensorsDetails(sensors)
        self.updateAlertsDetails(alerts)
        self.update_profile_details(profiles)

    # this function updates the alert level information shown
    def updateAlertLevelDetails(self):

        # crate new sensor pile content
        temp = self._createAlertLevelWidgetList(self.alertLevel)

        # create a list of tuples for the pile widget
        pileOptions = self.alertLevelPileWidget.options()
        temp = [(x, pileOptions) for x in temp]

        # empty pile widget contents and replace it with the new widgets
        del self.alertLevelPileWidget.contents[:]
        self.alertLevelPileWidget.contents.extend(temp)

    # this function updates the node information shown
    def updateAlertsDetails(self, alerts: List[ManagerObjAlert]):

        # crate new sensor pile content
        temp = self._createAlertsWidgetList(alerts)

        # create a list of tuples for the pile widget
        pileOptions = self.alertsPileWidget.options()
        temp = [(x, pileOptions) for x in temp]

        # empty pile widget contents and replace it with the new widgets
        del self.alertsPileWidget.contents[:]
        self.alertsPileWidget.contents.extend(temp)

    def update_profile_details(self, profiles: List[ManagerObjProfile]):
        """
        This function updates the profile information shown.

        :param profiles:
        """
        temp = self._create_profiles_widget_list(profiles)

        # Create a list of tuples for the pile widget.
        pile_options = self._profiles_pile_widget.options()
        new_profiles_list = [(x, pile_options) for x in temp]

        # Empty pile widget contents and replace it with the new widgets.
        del self._profiles_pile_widget.contents[:]
        self._profiles_pile_widget.contents.extend(new_profiles_list)

    # this function updates the sensor information shown
    def updateSensorsDetails(self, sensors: List[ManagerObjSensor]):

        # crate new sensor pile content
        temp = self._createSensorsWidgetList(sensors)

        # create a list of tuples for the pile widget
        pileOptions = self.sensorsPileWidget.options()
        temp = [(x, pileOptions) for x in temp]

        # empty pile widget contents and replace it with the new widgets
        del self.sensorsPileWidget.contents[:]
        self.sensorsPileWidget.contents.extend(temp)
