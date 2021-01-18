#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import urwid
from typing import List
from ..globalData import ManagerObjNode, ManagerObjAlert, ManagerObjAlertLevel


# this class is an urwid object for an alert
class AlertUrwid:

    def __init__(self, alert: ManagerObjAlert, node: ManagerObjNode):

        # store reference to alert object and node object
        self.alert = alert
        self.node = node

        # store reference in alert object to this urwid alert object
        self.alert.internal_data["urwid"] = self

        alertPileList = list()
        self.descriptionWidget = urwid.Text("Desc.: " + self.alert.description)
        alertPileList.append(self.descriptionWidget)

        alertPile = urwid.Pile(alertPileList)
        alertBox = urwid.LineBox(alertPile, title="Host: " + node.hostname)
        paddedAlertBox = urwid.Padding(alertBox, left=1, right=1)

        # check if node is connected and set the color accordingly
        if self.node.connected == 0:
            self.alertUrwidMap = urwid.AttrMap(paddedAlertBox, "disconnected")
            self.alertUrwidMap.set_focus_map({None: "disconnected_focus"})

        else:
            self.alertUrwidMap = urwid.AttrMap(paddedAlertBox, "connected")
            self.alertUrwidMap.set_focus_map({None: "connected_focus"})

    # this function returns the final urwid widget that is used
    # to render the box of an alert
    def get(self) -> urwid.AttrMap:
        return self.alertUrwidMap

    # this function updates the description of the object
    def updateDescription(self, description: str):
        self.descriptionWidget.set_text("Desc.: " + description)

    # this function updates the connected status of the object
    # (and changes color arcordingly)
    def updateConnected(self, connected: int):

        # change color according to connection state
        if connected == 0:
            self.alertUrwidMap.set_attr_map({None: "disconnected"})
            self.alertUrwidMap.set_focus_map({None: "disconnected_focus"})
        else:
            self.alertUrwidMap.set_attr_map({None: "connected"})
            self.alertUrwidMap.set_focus_map({None: "connected_focus"})

    # this function updates all internal widgets and checks if
    # the alert/node still exists
    def updateCompleteWidget(self) -> bool:

        # check if alert/node still exists
        if self.alert.is_deleted() or self.node.is_deleted():
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
        self.alertUrwidMap.set_focus_map({None: "connectionfail_focus"})


# this class is an urwid object for a detailed alert output
class AlertDetailedUrwid:

    def __init__(self, alert: ManagerObjAlert, node: ManagerObjNode, alertLevels: List[ManagerObjAlertLevel]):

        self.node = node
        self.alert = alert

        content = list()

        content.append(urwid.Divider("="))
        content.append(urwid.Text("Node"))
        content.append(urwid.Divider("="))
        temp = self._createNodeWidgetList(node)
        self.nodePileWidget = urwid.Pile(temp)
        content.append(self.nodePileWidget)

        content.append(urwid.Divider())
        content.append(urwid.Divider("="))
        content.append(urwid.Text("Alert"))
        content.append(urwid.Divider("="))
        temp = self._createAlertWidgetList(alert)
        self.alertPileWidget = urwid.Pile(temp)
        content.append(self.alertPileWidget)

        content.append(urwid.Divider())
        content.append(urwid.Divider("="))
        content.append(urwid.Text("Alert Levels"))
        content.append(urwid.Divider("="))
        temp = self._createAlertLevelsWidgetList(alertLevels)
        self.alertLevelsPileWidget = None
        if temp:
            self.alertLevelsPileWidget = urwid.Pile(temp)
        else:
            self.alertLevelsPileWidget = urwid.Pile([urwid.Text("None")])
        content.append(self.alertLevelsPileWidget)

        # use ListBox here because it handles all the
        # scrolling part automatically
        detailedList = urwid.ListBox(urwid.SimpleListWalker(content))
        detailedFrame = urwid.Frame(detailedList, footer=urwid.Text("Keys: ESC - Back, Up/Down - Scrolling"))
        self.detailedBox = urwid.LineBox(detailedFrame, title="Alert: " + self.alert.description)

    # this function creates the detailed output of all alert level objects
    # in a list
    def _createAlertLevelsWidgetList(self, alertLevels: List[ManagerObjAlertLevel]) -> List[urwid.Widget]:

        temp = list()
        first = True
        for alertLevel in alertLevels:

            if first:
                first = False
            else:
                temp.append(urwid.Divider())
                temp.append(urwid.Divider("-"))

            temp.extend(self._createAlertLevelWidgetList(alertLevel))

        return temp

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

        temp.append(urwid.Text("Trigger Always:"))
        if alertLevel.triggerAlways == 0:
            temp.append(urwid.Text("No"))
        elif alertLevel.triggerAlways == 1:
            temp.append(urwid.Text("Yes"))
        else:
            temp.append(urwid.Text("Undefined"))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Profiles:"))
        temp.append(urwid.Text(", ".join([str(x) for x in alertLevel.profiles])))
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

    # this function creates the detailed output of a node object
    # in a list
    def _createNodeWidgetList(self, node: ManagerObjNode) -> List[urwid.Widget]:

        temp = list()

        temp.append(urwid.Text("Node ID:"))
        temp.append(urwid.Text(str(node.nodeId)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Username:"))
        temp.append(urwid.Text(node.username))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Hostname:"))
        temp.append(urwid.Text(node.hostname))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Node Type:"))
        temp.append(urwid.Text(node.nodeType))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Instance:"))
        temp.append(urwid.Text(node.instance))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Version:"))
        versionWidget = urwid.Text(str(node.version) + "-" + str(node.rev))
        temp.append(versionWidget)
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Connected:"))
        if node.connected == 0:
            temp.append(urwid.AttrMap(urwid.Text("False"), "disconnected"))
        elif node.connected == 1:
            temp.append(urwid.AttrMap(urwid.Text("True"), "neutral"))
        else:
            temp.append(urwid.AttrMap(urwid.Text("Undefined"), "redColor"))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Persistent Connection:"))
        if node.persistent == 0:
            temp.append(urwid.Text("False"))

        elif node.persistent == 1:
            if node.connected == 0:
                temp.append(urwid.AttrMap(urwid.Text("True"), "disconnected"))

            else:
                temp.append(urwid.Text("True"))

        else:
            temp.append(urwid.AttrMap(urwid.Text("Undefined"), "redColor"))

        return temp

    # this function returns the final urwid widget that is used
    # to render this object
    def get(self) -> urwid.LineBox:
        return self.detailedBox

    # this function updates all internal widgets
    def updateCompleteWidget(self, alertLevels: List[ManagerObjAlertLevel]):

        self.updateNodeDetails()
        self.updateAlertDetails()
        self.updateAlertLevelsDetails(alertLevels)

    # this function updates the node information shown
    def updateAlertDetails(self):

        # crate new sensor pile content
        temp = self._createAlertWidgetList(self.alert)

        # create a list of tuples for the pile widget
        pileOptions = self.alertPileWidget.options()
        temp = [(x, pileOptions) for x in temp]

        # empty pile widget contents and replace it with the new widgets
        del self.alertPileWidget.contents[:]
        self.alertPileWidget.contents.extend(temp)

    # this function updates the alert levels information shown
    def updateAlertLevelsDetails(self, alertLevels: List[ManagerObjAlertLevel]):

        # crate new sensor pile content
        temp = self._createAlertLevelsWidgetList(alertLevels)

        # create a list of tuples for the pile widget
        pileOptions = self.alertLevelsPileWidget.options()
        temp = [(x, pileOptions) for x in temp]

        # empty pile widget contents and replace it with the new widgets
        del self.alertLevelsPileWidget.contents[:]
        self.alertLevelsPileWidget.contents.extend(temp)

    # this function updates the node information shown
    def updateNodeDetails(self):

        # crate new sensor pile content
        temp = self._createNodeWidgetList(self.node)

        # create a list of tuples for the pile widget
        pileOptions = self.nodePileWidget.options()
        temp = [(x, pileOptions) for x in temp]

        # empty pile widget contents and replace it with the new widgets
        del self.nodePileWidget.contents[:]
        self.nodePileWidget.contents.extend(temp)
