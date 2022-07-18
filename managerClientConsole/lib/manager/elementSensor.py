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
from .eventHandler import ManagerEventHandler
from ..globalData import ManagerObjNode, ManagerObjSensor, ManagerObjAlertLevel
from ..globalData.sensorObjects import _SensorData, SensorDataType, SensorErrorState


# this class is an urwid object for a sensor
class SensorUrwid:

    def __init__(self,
                 sensor: ManagerObjSensor,
                 node: ManagerObjNode,
                 connectionTimeout: int,
                 serverEventHandler: ManagerEventHandler):

        # is needed to decide when a sensor has timed out
        self.connectionTimeout = connectionTimeout
        self.serverEventHandler = serverEventHandler

        sensorPileList = list()
        self.descriptionWidget = urwid.Text("Desc.: " + sensor.description)
        sensorPileList.append(self.descriptionWidget)

        self.dataWidget = urwid.Text("")
        if sensor.dataType != SensorDataType.NONE:
            self.dataWidget.set_text("Data: " + str(sensor.data))
            sensorPileList.append(self.dataWidget)

        self.sensorPile = urwid.Pile(sensorPileList)
        sensorBox = urwid.LineBox(self.sensorPile, title="Host: " + node.hostname)
        paddedSensorBox = urwid.Padding(sensorBox, left=1, right=1)

        # check if node is connected and set the color accordingly
        # and consider the state of the sensor (1 = triggered)
        if node.connected == 0:
            if node.persistent == 1:
                self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox, "disconnected_error")
                self.sensorUrwidMap.set_focus_map({None: "disconnected_error_focus"})
            else:
                self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox, "disconnected_ok")
                self.sensorUrwidMap.set_focus_map({None: "disconnected_ok_focus"})

        # check if sensor has an error and change color accordingly
        elif sensor.error_state.state != SensorErrorState.OK:
            self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox, "errorstate")
            self.sensorUrwidMap.set_focus_map({None: "errorstate_focus"})

        # check if the node is connected and no sensor alert is triggered
        elif sensor.state == 0:
            self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox, "connected")
            self.sensorUrwidMap.set_focus_map({None: "connected_focus"})

        # last possible combination is a triggered sensor alert
        else:
            self.sensorUrwidMap = urwid.AttrMap(paddedSensorBox, "sensoralert")
            self.sensorUrwidMap.set_focus_map({None: "sensoralert_focus"})



        # store reference to sensor object and node object
        self.sensor = sensor
        self.node = node

        # store reference in sensor object to this urwid sensor object
        self.sensor.internal_data["urwid"] = self

        # Store the current data type of the sensor. This is used to check
        # if the data type has changed and the urwid object has to be adjusted.
        self.lastDataType = self.sensor.dataType

    # this function returns the final urwid widget that is used
    # to render the box of a sensor
    def get(self) -> urwid.AttrMap:
        return self.sensorUrwidMap

    # this function updates the description of the object
    def updateDescription(self, description: str):
        self.descriptionWidget.set_text("Desc.: " + description)

    # this function updates the connected status of the object
    # (and changes color accordingly)
    def updateConnected(self, connected: int):

        # change color according to connection state
        # and consider the state of the sensor (1 = triggered)
        if connected == 0:
            if self.node.persistent == 1:
                self.sensorUrwidMap.set_attr_map({None: "disconnected_error"})
                self.sensorUrwidMap.set_focus_map({None: "disconnected_error_focus"})
            else:
                self.sensorUrwidMap.set_attr_map({None: "disconnected_ok"})
                self.sensorUrwidMap.set_focus_map({None: "disconnected_ok_focus"})

        # check if sensor has an error and change color accordingly
        elif self.sensor.error_state.state != SensorErrorState.OK:
            self.sensorUrwidMap.set_attr_map({None: "errorstate"})
            self.sensorUrwidMap.set_focus_map({None: "errorstate_focus"})

        else:
            self.sensorUrwidMap.set_attr_map({None: "connected"})
            self.sensorUrwidMap.set_focus_map({None: "connected_focus"})

    def update_error_state(self, error_state: SensorErrorState):
        """
        This function updates the sensor error state of the object (and changes color accordingly).
        :param error_state:
        :return:
        """
        # Only update error state if node is connected.
        if self.node.connected == 1:
            if error_state.state != SensorErrorState.OK:
                self.sensorUrwidMap.set_attr_map({None: "errorstate"})
                self.sensorUrwidMap.set_focus_map({None: "errorstate_focus"})

            else:
                self.updateState(self.sensor.state)

    # this function updates the state of the object
    # (and changes color accordingly)
    def updateState(self, state: int):

        # check if the node is connected and change the color accordingly
        if self.node.connected == 0:
            if self.node.persistent == 1:
                self.sensorUrwidMap.set_attr_map({None: "disconnected_error"})
                self.sensorUrwidMap.set_focus_map({None: "disconnected_error_focus"})
            else:
                self.sensorUrwidMap.set_attr_map({None: "disconnected_ok"})
                self.sensorUrwidMap.set_focus_map({None: "disconnected_ok_focus"})

        else:
            # check to which state the color should be changed
            if state == 0:
                self.sensorUrwidMap.set_attr_map({None: "connected"})
                self.sensorUrwidMap.set_focus_map({None: "connected_focus"})

            else:
                self.sensorUrwidMap.set_attr_map({None: "sensoralert"})
                self.sensorUrwidMap.set_focus_map({None: "sensoralert_focus"})

            # check if the sensor has an error and change the color accordingly
            if self.sensor.error_state.state != SensorErrorState.OK:
                self.sensorUrwidMap.set_attr_map({None: "errorstate"})
                self.sensorUrwidMap.set_focus_map({None: "errorstate_focus"})

    # this function updates the data of the object
    def updateData(self, data: _SensorData, dataType: int):
        self.dataWidget.set_text("Data: " + str(data))

        # If the data type has changed and the new data type is "none",
        # remove the data widget.
        if self.lastDataType != dataType and dataType == SensorDataType.NONE:
            for pileTuple in self.sensorPile.contents:
                if self.dataWidget == pileTuple[0]:
                    self.sensorPile.contents.remove(pileTuple)
                    break

        # If the data type has changed and the new data type is not "none",
        # add the data widget.
        elif self.lastDataType != dataType and dataType != SensorDataType.NONE:
            self.sensorPile.contents.append((self.dataWidget, self.sensorPile.options()))

        # Needed to check if the data type has changed.
        self.lastDataType = dataType

    # this function updates all internal widgets and checks if
    # the sensor/node still exists
    def updateCompleteWidget(self) -> bool:

        # check if sensor/node still exists
        if self.sensor.is_deleted() or self.node.is_deleted():
            # return false if object no longer exists
            return False

        self.updateDescription(self.sensor.description)
        self.updateConnected(self.node.connected)
        self.updateState(self.sensor.state)
        self.updateData(self.sensor.data, self.sensor.dataType)
        self.update_error_state(self.sensor.error_state)

        # return true if object was updated
        return True

    # this functions sets the color when the connection to the server
    # has failed
    def setConnectionFail(self):
        self.sensorUrwidMap.set_attr_map({None: "connectionfail"})
        self.sensorUrwidMap.set_focus_map({None: "connectionfail_focus"})


# this class is an urwid object for a detailed sensor output
class SensorDetailedUrwid:

    def __init__(self, sensor: ManagerObjSensor, node: ManagerObjNode, alertLevels: List[ManagerObjAlertLevel]):

        self.node = node
        self.sensor = sensor

        content = list()

        content.append(urwid.Divider("="))
        content.append(urwid.Text("Node"))
        content.append(urwid.Divider("="))
        temp = self._createNodeWidgetList(node)
        self.nodePileWidget = urwid.Pile(temp)
        content.append(self.nodePileWidget)

        content.append(urwid.Divider())
        content.append(urwid.Divider("="))
        content.append(urwid.Text("Sensor"))
        content.append(urwid.Divider("="))
        temp = self._createSensorWidgetList(sensor)
        self.sensorPileWidget = urwid.Pile(temp)
        content.append(self.sensorPileWidget)

        content.append(urwid.Divider())
        content.append(urwid.Divider("="))
        content.append(urwid.Text("Alert Levels"))
        content.append(urwid.Divider("="))
        temp = self._createAlertLevelsWidgetList(alertLevels)
        self.alertLevelsPileWidget = urwid.Pile(temp)
        content.append(self.alertLevelsPileWidget)

        # use ListBox here because it handles all the
        # scrolling part automatically
        detailedList = urwid.ListBox(urwid.SimpleListWalker(content))
        detailedFrame = urwid.Frame(detailedList, footer=urwid.Text("Keys: ESC - Back, Up/Down - Scrolling"))
        self.detailedBox = urwid.LineBox(detailedFrame, title="Sensor: " + self.sensor.description)

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

        if not temp:
            temp.append(urwid.Text("None"))

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

    # this function creates the detailed output of a sensor object
    # in a list
    def _createSensorWidgetList(self, sensor: ManagerObjSensor) -> List[urwid.Widget]:

        temp = list()

        temp.append(urwid.Text("Sensor ID:"))
        temp.append(urwid.Text(str(sensor.sensorId)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Client Sensor ID:"))
        temp.append(urwid.Text(str(sensor.clientSensorId)))
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
        elif sensor.dataType == SensorDataType.GPS:
            temp.append(urwid.Text("GPS"))
        else:
            temp.append(urwid.Text("Unknown"))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Data:"))
        temp.append(urwid.Text(str(sensor.data)))
        temp.append(urwid.Divider())

        temp.append(urwid.Text("Error State:"))
        temp.append(urwid.Text(str(sensor.error_state)))

        return temp

    # this function returns the final urwid widget that is used
    # to render this object
    def get(self) -> urwid.LineBox:
        return self.detailedBox

    # this function updates all internal widgets
    def updateCompleteWidget(self, alertLevels: List[ManagerObjAlertLevel]):
        self.updateNodeDetails()
        self.updateSensorDetails()
        self.updateAlertLevelsDetails(alertLevels)

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

    # this function updates the sensor information shown
    def updateSensorDetails(self):

        # crate new sensor pile content
        temp = self._createSensorWidgetList(self.sensor)

        # create a list of tuples for the pile widget
        pileOptions = self.sensorPileWidget.options()
        temp = [(x, pileOptions) for x in temp]

        # empty pile widget contents and replace it with the new widgets
        del self.sensorPileWidget.contents[:]
        self.sensorPileWidget.contents.extend(temp)
