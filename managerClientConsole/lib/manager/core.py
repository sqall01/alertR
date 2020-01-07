#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import logging
from typing import List, Any
from ..localObjects import Option, Node, Sensor, Manager, Alert, AlertLevel, SensorAlert, SensorDataType
from ..globalData import GlobalData


# this class handles an incoming server event (sensor alert message,
# status update, ...)
class ServerEventHandler:

    def __init__(self, globalData: GlobalData):

        # file name of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # get global configured data
        self.globalData = globalData
        self.screenUpdater = self.globalData.screenUpdater
        self.options = self.globalData.options
        self.nodes = self.globalData.nodes
        self.sensors = self.globalData.sensors
        self.managers = self.globalData.managers
        self.alerts = self.globalData.alerts
        self.alertLevels = self.globalData.alertLevels
        self.sensorAlerts = self.globalData.sensorAlerts

        # keep track of the server time
        self.serverTime = 0.0

    # internal function that checks if all options are checked
    def _checkAllOptionsAreChecked(self) -> bool:
        for option in self.options:
            if option.checked is False:
                return False
        return True

    # internal function that removes all nodes that are not checked
    def _removeNotCheckedNodes(self):
        for node in self.nodes:
            if node.checked is False:

                # check if node object has a link to the sensor urwid object
                if node.sensorUrwid is not None:
                    # check if sensor urwid object is linked to node object
                    if node.sensorUrwid.node is not None:
                        # used for urwid only:
                        # remove reference from urwid object to node object
                        # (the objects are double linked)
                        node.sensorUrwid.node = None

                # check if node object has a link to the alert urwid object
                elif node.alertUrwid is not None:
                    # check if sensor urwid object is linked to node object
                    if node.alertUrwid.node is not None:
                        # used for urwid only:
                        # remove reference from urwid object to node object
                        # (the objects are double linked)
                        node.alertUrwid.node = None

                # remove sensor from list of sensors
                # to delete all references to object
                # => object will be deleted by garbage collector
                self.nodes.remove(node)

        for sensor in self.sensors:
            if sensor.checked is False:

                # check if sensor object has a link to the sensor urwid object
                if sensor.sensorUrwid is not None:
                    # check if sensor urwid object is linked to sensor object
                    if sensor.sensorUrwid.sensor is not None:
                        # used for urwid only:
                        # remove reference from urwid object to sensor object
                        # (the objects are double linked)
                        sensor.sensorUrwid.sensor = None

                # remove sensor from list of sensors
                # to delete all references to object
                # => object will be deleted by garbage collector
                self.sensors.remove(sensor)

        for manager in self.managers:
            if manager.checked is False:

                # check if manager object has a link to the 
                # manager urwid object
                if manager.managerUrwid is not None:
                    # check if manager urwid object is linked to manager object
                    if manager.managerUrwid.manager is not None:
                        # used for urwid only:
                        # remove reference from urwid object to manager object
                        # (the objects are double linked)
                        manager.managerUrwid.manager = None

                # remove manager from list of managers
                # to delete all references to object
                # => object will be deleted by garbage collector
                self.managers.remove(manager)

        for alert in self.alerts:
            if alert.checked is False:

                # check if alert object has a link to the alert urwid object
                if alert.alertUrwid is not None:
                    # check if alert urwid object is linked to alert object
                    if alert.alertUrwid.alert is not None:
                        # used for urwid only:
                        # remove reference from urwid object to alert object
                        # (the objects are double linked)
                        alert.alertUrwid.alert = None

                # remove alert from list of alerts
                # to delete all references to object
                # => object will be deleted by garbage collector
                self.alerts.remove(alert)

        for alertLevel in self.alertLevels:
            if alertLevel.checked is False:

                # check if alert level object has a link to 
                # the alert level urwid object
                if alertLevel.alertLevelUrwid is not None:
                    # check if alert level urwid object is 
                    # linked to alert level object
                    if alertLevel.alertLevelUrwid.alertLevel is not None:
                        # used for urwid only:
                        # remove reference from urwid object to 
                        # alert level object
                        # (the objects are double linked)
                        alertLevel.alertLevelUrwid.alertLevel = None

                # remove alert level from list of alert levels
                # to delete all references to object
                # => object will be deleted by garbage collector
                self.alertLevels.remove(alertLevel)

    # internal function that marks all nodes as not checked
    def _markAlertSystemObjectsAsNotChecked(self):
        for option in self.options:
            option.checked = False

        for node in self.nodes:
            node.checked = False

        for sensor in self.sensors:
            sensor.checked = False      

        for manager in self.managers:
            manager.checked = False

        for alert in self.alerts:
            alert.checked = False

        for alertLevel in self.alertLevels:
            alertLevel.checked = False

    # is called when a status update event was received from the server
    def receivedStatusUpdate(self,
                             serverTime: int,
                             options: List[Option],
                             nodes: List[Node],
                             sensors: List[Sensor],
                             managers: List[Manager],
                             alerts: List[Alert],
                             alertLevels: List[AlertLevel]) -> bool:

        self.serverTime = serverTime

        # mark all nodes as not checked
        self._markAlertSystemObjectsAsNotChecked()

        # process received options
        for recvOption in options:

            # search option in list of known options
            # => if not known add it
            found = False
            for option in self.options:
                # ignore options that are already checked
                if option.checked:

                    # check if the type is unique
                    if option.type == recvOption.type:
                        logging.error("[%s]: Received optionType '%s' is not unique."
                                      % (self.fileName, recvOption.type))
                        return False

                    continue

                # when found => mark option as checked and update information
                if option.type == recvOption.type:
                    option.checked = True
                    option.value = recvOption.value
                    found = True
                    break

            # when not found => add option to list
            if not found:
                recvOption.checked = True
                self.options.append(recvOption)

        # check if all options are checked
        # => if not, one was removed on the server
        if not self._checkAllOptionsAreChecked():
            logging.exception("[%s]: Options are inconsistent." % self.fileName)

            return False

        # process received nodes
        for recvNode in nodes:

            # search node in list of known nodes
            # => if not known add it
            found = False
            for node in self.nodes:
                # ignore nodes that are already checked
                if node.checked:

                    # check if the nodeId is unique
                    if node.nodeId == recvNode.nodeId:
                        logging.error("[%s]: Received nodeId '%d' is not unique." % (self.fileName, recvNode.nodeId))
                        return False

                    continue

                # when found => mark node as checked and update information
                if node.nodeId == recvNode.nodeId:
                    node.checked = True
                    node.deepCopy(recvNode)
                    found = True
                    break

            # when not found => add node to list
            if not found:
                recvNode.checked = True
                self.nodes.append(recvNode)

        # process received sensors
        for recvSensor in sensors:

            # search sensor in list of known sensors
            # => if not known add it
            found = False
            for sensor in self.sensors:
                # ignore sensors that are already checked
                if sensor.checked:

                    # check if the sensorId is unique
                    if sensor.sensorId == recvSensor.sensorId:
                        logging.error("[%s]: Received sensorId '%d' is not unique."
                                      % (self.fileName, recvSensor.sensorId))

                        return False

                    continue

                # when found => mark sensor as checked and update information
                if sensor.sensorId == recvSensor.sensorId:
                    sensor.checked = True
                    tempLastStateUpdated = sensor.lastStateUpdated
                    tempState = sensor.state
                    sensor.deepCopy(recvSensor)

                    # Revert change to the state if the old state was newer.
                    if sensor.lastStateUpdated < tempLastStateUpdated:
                        sensor.lastStateUpdated = tempLastStateUpdated
                        sensor.state = tempState

                    found = True
                    break

            # when not found => add sensor to list
            if not found:
                recvSensor.checked = True
                self.sensors.append(recvSensor)

        self.sensors.sort(key=lambda x: x.description.lower())

        # process received managers
        for recvManager in managers:

            # search manager in list of known managers
            # => if not known add it
            found = False
            for manager in self.managers:
                # ignore managers that are already checked
                if manager.checked:

                    # check if the managerId is unique
                    if manager.managerId == recvManager.managerId:
                        logging.error("[%s]: Received managerId '%d' is not unique."
                                      % (self.fileName, recvManager.managerId))
                        return False

                    continue

                # when found => mark manager as checked and update information
                if manager.managerId == recvManager.managerId:
                    manager.checked = True
                    manager.deepCopy(recvManager)
                    found = True
                    break

            # when not found => add manager to list
            if not found:
                recvManager.checked = True
                self.managers.append(recvManager)

        self.managers.sort(key=lambda x: x.description.lower())

        # process received alerts
        for recvAlert in alerts:

            # search alert in list of known alerts
            # => if not known add it
            found = False
            for alert in self.alerts:
                # ignore alerts that are already checked
                if alert.checked:

                    # check if the alertId is unique
                    if alert.alertId == recvAlert.alertId:
                        logging.error("[%s]: Received alertId '%d' is not unique." % (self.fileName, recvAlert.alertId))

                        return False

                    continue

                # when found => mark alert as checked and update information
                if alert.alertId == recvAlert.alertId:
                    alert.checked = True
                    alert.deepCopy(recvAlert)
                    found = True
                    break

            # when not found => add alert to list
            if not found:
                recvAlert.checked = True
                self.alerts.append(recvAlert)

        self.alerts.sort(key=lambda x: x.description.lower())

        # process received alertLevels
        for recvAlertLevel in alertLevels:

            # search alertLevel in list of known alertLevels
            # => if not known add it
            found = False
            for alertLevel in self.alertLevels:
                # ignore alertLevels that are already checked
                if alertLevel.checked:

                    # check if the level is unique
                    if alertLevel.level == recvAlertLevel.level:
                        logging.error("[%s]: Received alertLevel '%d' is not unique."
                                      % (self.fileName, recvAlertLevel.level))

                        return False

                    continue

                # when found => mark alertLevel as checked
                # and update information
                if alertLevel.level == recvAlertLevel.level:
                    alertLevel.checked = True
                    alertLevel.name = recvAlertLevel.name
                    alertLevel.triggerAlways = recvAlertLevel.triggerAlways
                    alertLevel.rulesActivated = recvAlertLevel.rulesActivated
                    found = True
                    break

            # when not found => add alertLevel to list
            if not found:
                recvAlertLevel.checked = True
                self.alertLevels.append(recvAlertLevel)

        self.alertLevels.sort(key=lambda x: x.level)

        # remove all nodes that are not checked
        self._removeNotCheckedNodes()

        return True

    # is called when a sensor alert event was received from the server
    def receivedSensorAlert(self, serverTime: int, sensorAlert: SensorAlert) -> bool:

        self.serverTime = serverTime
        self.sensorAlerts.append(sensorAlert)

        # If rules are not activated (and therefore the sensor alert was
        # only triggered by one distinct sensor).
        # => Update information in sensor which triggered the sensor alert.
        if not sensorAlert.rulesActivated:
            found = False
            for sensor in self.sensors:
                if sensor.sensorId == sensorAlert.sensorId:
                    sensor.lastStateUpdated = serverTime

                    # Only update sensor state information if the flag
                    # was set in the received message.
                    if sensorAlert.changeState:
                        sensor.state = sensorAlert.state

                    # Only update sensor data information if the flag
                    # was set in the received message.
                    if sensorAlert.hasLatestData:
                        if sensorAlert.dataType == sensor.dataType:
                            sensor.data = sensorAlert.sensorData
                        else:
                            logging.error("[%s]: Sensor data type different. Skipping data assignment."
                                          % self.fileName)

                    found = True
                    break
            if not found:
                logging.error("[%s]: Sensor of sensor alert not known." % self.fileName)

                return False

        return True

    # is called when a state change event was received from the server
    def receivedStateChange(self,
                            serverTime: int,
                            sensorId: int,
                            state: int,
                            dataType: SensorDataType,
                            sensorData: Any) -> bool:

        self.serverTime = serverTime

        # search sensor in list of known sensors
        # => if not known return failure
        sensor = None
        for tempSensor in self.sensors:
            if tempSensor.sensorId == sensorId:
                sensor = tempSensor
                break
        if not sensor:
            logging.error("[%s]: Sensor for state change not known." % self.fileName)

            return False

        # Change sensor state.
        sensor.state = state
        sensor.lastStateUpdated = serverTime

        if dataType == sensor.dataType:
            sensor.data = sensorData
        else:
            logging.error("[%s]: Sensor data type different. Skipping data assignment." % self.fileName)

        return True

    # is called when an incoming server event has to be handled
    def handleEvent(self):

        # wake up the screen updater
        self.screenUpdater.screenUpdaterEvent.set()
