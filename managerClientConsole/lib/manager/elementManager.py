#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import urwid
from typing import List
from ..globalData import ManagerObjNode, ManagerObjManager


# this class is an urwid object for a manager
class ManagerUrwid:

    def __init__(self, manager: ManagerObjManager, node: ManagerObjNode):

        # store reference to manager object and node object
        self.manager = manager
        self.node = node

        # store reference in manager object to this urwid manager object
        self.manager.internal_data["urwid"] = self

        managerPileList = list()
        self.descriptionWidget = urwid.Text("Desc.: " + self.manager.description)
        managerPileList.append(self.descriptionWidget)

        managerPile = urwid.Pile(managerPileList)
        managerBox = urwid.LineBox(managerPile, title="Host: " + node.hostname)
        paddedManagerBox = urwid.Padding(managerBox, left=1, right=1)

        # check if node is connected and set the color accordingly
        if self.node.connected == 0:
            if node.persistent == 1:
                self.managerUrwidMap = urwid.AttrMap(paddedManagerBox, "disconnected_error")
                self.managerUrwidMap.set_focus_map({None: "disconnected_error_focus"})
            else:
                self.managerUrwidMap = urwid.AttrMap(paddedManagerBox, "disconnected_ok")
                self.managerUrwidMap.set_focus_map({None: "disconnected_ok_focus"})

        else:
            self.managerUrwidMap = urwid.AttrMap(paddedManagerBox, "connected")
            self.managerUrwidMap.set_focus_map({None: "connected_focus"})

    # this function returns the final urwid widget that is used
    # to render the box of a manager
    def get(self) -> urwid.AttrMap:
        return self.managerUrwidMap

    # this function updates the description of the object
    def updateDescription(self, description: str):
        self.descriptionWidget.set_text("Desc.: " + description)

    # this function updates the connected status of the object
    # (and changes color arcordingly)
    def updateConnected(self, connected: int):

        # change color according to connection state
        if connected == 0:
            if self.node.persistent == 1:
                self.managerUrwidMap.set_attr_map({None: "disconnected_error"})
                self.managerUrwidMap.set_focus_map({None: "disconnected_error_focus"})
            else:
                self.managerUrwidMap.set_attr_map({None: "disconnected_ok"})
                self.managerUrwidMap.set_focus_map({None: "disconnected_ok_focus"})

        else:
            self.managerUrwidMap.set_attr_map({None: "connected"})
            self.managerUrwidMap.set_focus_map({None: "connected_focus"})

    # this function updates all internal widgets and checks if
    # the manager/node still exists
    def updateCompleteWidget(self):

        # check if manager/node still exists
        if self.manager.is_deleted() or self.node.is_deleted():
            # return false if object no longer exists
            return False

        self.updateDescription(self.manager.description)
        self.updateConnected(self.node.connected)

        # return true if object was updated
        return True

    # this functions sets the color when the connection to the server
    # has failed
    def setConnectionFail(self):
        self.managerUrwidMap.set_attr_map({None: "connectionfail"})
        self.managerUrwidMap.set_focus_map({None: "connectionfail_focus"})


# this class is an urwid object for a detailed manager output
class ManagerDetailedUrwid:

    def __init__(self, manager: ManagerObjManager, node: ManagerObjNode):

        self.node = node
        self.manager = manager

        content = list()

        content.append(urwid.Divider("="))
        content.append(urwid.Text("Node"))
        content.append(urwid.Divider("="))
        temp = self._createNodeWidgetList(node)
        self.nodePileWidget = urwid.Pile(temp)
        content.append(self.nodePileWidget)

        content.append(urwid.Divider())
        content.append(urwid.Divider("="))
        content.append(urwid.Text("Manager"))
        content.append(urwid.Divider("="))
        temp = self._createManagerWidgetList(manager)
        self.managerPileWidget = urwid.Pile(temp)
        content.append(self.managerPileWidget)

        # use ListBox here because it handles all the
        # scrolling part automatically
        detailedList = urwid.ListBox(urwid.SimpleListWalker(content))
        detailedFrame = urwid.Frame(detailedList, footer=urwid.Text("Keys: ESC - Back, Up/Down - Scrolling"))
        self.detailedBox = urwid.LineBox(detailedFrame, title="Manager: " + self.manager.description)

    # this function creates the detailed output of a alert object
    # in a list
    def _createManagerWidgetList(self, manager: ManagerObjManager) -> List[urwid.Widget]:

        temp = list()

        temp.append(urwid.Text("Manager ID:"))
        temp.append(urwid.Text(str(manager.managerId)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Description:"))
        temp.append(urwid.Text(manager.description))

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
            if node.persistent == 1:
                temp.append(urwid.AttrMap(urwid.Text("False"), "disconnected_error"))
            else:
                temp.append(urwid.AttrMap(urwid.Text("False"), "neutral"))
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
                temp.append(urwid.AttrMap(urwid.Text("True"), "disconnected_error"))

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
    def updateCompleteWidget(self):
        self.updateNodeDetails()
        self.updateManagerDetails()

    # this function updates the node information shown
    def updateManagerDetails(self):
        # crate new sensor pile content
        temp = self._createManagerWidgetList(self.manager)

        # create a list of tuples for the pile widget
        pileOptions = self.managerPileWidget.options()
        temp = [(x, pileOptions) for x in temp]

        # empty pile widget contents and replace it with the new widgets
        del self.managerPileWidget.contents[:]
        self.managerPileWidget.contents.extend(temp)

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
