#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import logging
import time
from ..client import EventHandler
from ..localObjects import Option, Node, Sensor, Manager, Alert, AlertLevel, SensorAlert, SensorDataType
from ..globalData import GlobalData
from typing import List, Any


# this class handles an incoming server event (sensor alert message,
# status update, ...)
class BaseManagerEventHandler(EventHandler):

    def __init__(self,
                 globalData: GlobalData):
        super().__init__()

        # file name of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # get global configured data
        self.globalData = globalData
        self.options = self.globalData.options
        self.nodes = self.globalData.nodes
        self.sensors = self.globalData.sensors
        self.managers = self.globalData.managers
        self.alerts = self.globalData.alerts
        self.alertLevels = self.globalData.alertLevels
        self.sensorAlerts = self.globalData.sensorAlerts
        self.events = self.globalData.events
        self.connectionTimeout = self.globalData.connectionTimeout

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

        timeReceived = int(time.time())

        for node in self.nodes:
            if node.checked is False:

                # create delete node event
                tempEvent = EventDeleteNode(timeReceived)
                tempEvent.hostname = node.hostname
                tempEvent.nodeType = node.nodeType
                tempEvent.instance = node.instance
                self.events.append(tempEvent)

                # remove node from list of nodes
                # to delete all references to object
                # => object will be deleted by garbage collector
                self.nodes.remove(node)

        for sensor in self.sensors:
            if sensor.checked is False:

                # create delete sensor event
                tempEvent = EventDeleteSensor(timeReceived)
                tempEvent.description = sensor.description
                self.events.append(tempEvent)

                # remove sensor from list of sensors
                # to delete all references to object
                # => object will be deleted by garbage collector
                self.sensors.remove(sensor)

        for manager in self.managers:
            if manager.checked is False:

                # create delete manager event
                tempEvent = EventDeleteManager(timeReceived)
                tempEvent.description = manager.description
                self.events.append(tempEvent)

                # remove manager from list of managers
                # to delete all references to object
                # => object will be deleted by garbage collector
                self.managers.remove(manager)

        for alert in self.alerts:
            if alert.checked is False:

                # create delete alert event
                tempEvent = EventDeleteAlert(timeReceived)
                tempEvent.description = alert.description
                self.events.append(tempEvent)

                # remove alert from list of alerts
                # to delete all references to object
                # => object will be deleted by garbage collector
                self.alerts.remove(alert)

        for alertLevel in self.alertLevels:
            if alertLevel.checked is False:

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

    def _update_db_data(self):
        """
        Internal function that updates alarm system data in the database.
        """
                # check if configured to not store sensor alerts
        # => delete them directly
        if self.sensorAlertLifeSpan == 0:
            del self.sensorAlerts[:]

        # check if a sensor has timed out
        # => create an event for it
        for sensor in self.sensors:
            if sensor.lastStateUpdated < (self.serverTime - (2 * self.connectionTimeout)):

                # create sensor time out event
                # (only add it if node is connected)
                foundNode = None
                for node in self.nodes:
                    if node.nodeId == sensor.nodeId:
                        foundNode = node
                        break
                if foundNode is None:
                    logging.error("[%s]: Could not find node with id '%d' for sensor with id '%d'."
                                  % (self.fileName, sensor.nodeId, sensor.sensorId))
                    continue

                if foundNode.connected == 1:
                    utcTimestamp = int(time.time())
                    tempEvent = EventSensorTimeOut(utcTimestamp)
                    tempEvent.hostname = foundNode.hostname
                    tempEvent.description = sensor.description
                    tempEvent.state = sensor.state
                    self.events.append(tempEvent)

        # update the local server information
        if not self.storage.updateServerInformation(self.serverTime,
                                                    self.options,
                                                    self.nodes,
                                                    self.sensors,
                                                    self.alerts,
                                                    self.managers,
                                                    self.alertLevels,
                                                    self.sensorAlerts):

            logging.error("[%s]: Unable to update server information." % self.fileName)

        else:
            # empty sensor alerts list to prevent it
            # from getting too big
            del self.sensorAlerts[:]

    # is called when a status update event was received from the server
    def status_update(self,
                      server_time: int,
                      options: List[Option],
                      nodes: List[Node],
                      sensors: List[Sensor],
                      managers: List[Manager],
                      alerts: List[Alert],
                      alert_levels: List[AlertLevel]) -> bool:

        self.serverTime = server_time
        timeReceived = int(time.time())

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

                    # only change value when it has changed
                    if option.value != recvOption.value:

                        # create change option event
                        tempEvent = EventChangeOption(timeReceived)
                        tempEvent.type = option.type
                        tempEvent.oldValue = option.value
                        tempEvent.newValue = recvOption.value
                        self.events.append(tempEvent)

                        option.value = recvOption.value

                    found = True
                    break

            # when not found => add option to list
            if not found:
                recvOption.checked = True
                self.options.append(recvOption)

                # create new option event
                tempEvent = EventNewOption(timeReceived)
                tempEvent.type = recvOption.type
                tempEvent.value = recvOption.value
                self.events.append(tempEvent)

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

                    # create change node event (only add it if an information
                    # has changed)
                    changed = False
                    tempEvent = EventChangeNode(timeReceived)

                    # only update information if they have changed
                    tempEvent.oldHostname = node.hostname
                    tempEvent.newHostname = recvNode.hostname
                    if node.hostname != recvNode.hostname:
                        changed = True

                    tempEvent.oldNodeType = node.nodeType
                    tempEvent.newNodeType = recvNode.nodeType
                    if node.nodeType != recvNode.nodeType:
                        changed = True

                    tempEvent.oldInstance = node.instance
                    tempEvent.newInstance = recvNode.instance
                    if node.instance != recvNode.instance:
                        changed = True

                    tempEvent.oldVersion = node.version
                    tempEvent.newVersion = recvNode.version
                    if node.version != recvNode.version:
                        changed = True

                    tempEvent.oldRev = node.rev
                    tempEvent.newRev = recvNode.rev
                    if node.rev != recvNode.rev:
                        changed = True

                    tempEvent.oldUsername = node.username
                    tempEvent.newUsername = recvNode.username
                    if node.username != recvNode.username:
                        changed = True

                    tempEvent.oldPersistent = node.persistent
                    tempEvent.newPersistent = recvNode.persistent
                    if node.persistent != recvNode.persistent:
                        changed = True

                    # add event to event queue if an information has changed
                    if changed:
                        self.events.append(tempEvent)

                    # only change connected value when it has changed
                    if node.connected != recvNode.connected:
                        
                        # create connected change event
                        tempEvent = EventConnectedChange(timeReceived)
                        tempEvent.hostname = node.hostname
                        tempEvent.nodeType = node.nodeType
                        tempEvent.instance = node.instance
                        tempEvent.connected = recvNode.connected
                        self.events.append(tempEvent)

                    node.deepCopy(recvNode)
                    found = True
                    break

            # when not found => add node to list
            if not found:
                recvNode.checked = True
                self.nodes.append(recvNode)

                # create new node event
                tempEvent = EventNewNode(timeReceived)
                tempEvent.hostname = recvNode.hostname
                tempEvent.nodeType = recvNode.nodeType
                tempEvent.instance = recvNode.instance
                self.events.append(tempEvent)

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

                    # create change sensor event (only add it if an information
                    # has changed)
                    changed = False
                    tempEvent = EventChangeSensor(timeReceived)

                    # only update information if they have changed
                    tempEvent.oldAlertDelay = sensor.alertDelay
                    tempEvent.newAlertDelay = recvSensor.alertDelay
                    if sensor.alertDelay != recvSensor.alertDelay:
                        changed = True

                    tempEvent.oldDescription = sensor.description
                    tempEvent.newDescription = recvSensor.description
                    if sensor.description != recvSensor.description:
                        changed = True

                    tempEvent.oldRemoteSensorId = sensor.remoteSensorId
                    tempEvent.newRemoteSensorId = recvSensor.remoteSensorId
                    if sensor.remoteSensorId != recvSensor.remoteSensorId:
                        changed = True

                    # add event to event queue if an information has changed
                    if changed:
                        self.events.append(tempEvent)

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

                # create new sensor event
                foundNode = None
                for node in self.nodes:
                    if node.nodeId == recvSensor.nodeId:
                        foundNode = node
                        break

                if foundNode is None:
                    logging.error("[%s]: Could not find node with id '%d' for sensor with id '%d'."
                                  % (self.fileName, recvSensor.nodeId, recvSensor.sensorId))
                    return False

                tempEvent = EventNewSensor(timeReceived)
                tempEvent.hostname = foundNode.hostname
                tempEvent.description = recvSensor.description
                tempEvent.state = recvSensor.state
                self.events.append(tempEvent)

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

                    # create change manager event
                    # (only add it if an information has changed)
                    changed = False
                    tempEvent = EventChangeManager(timeReceived)

                    # only update information if they have changed
                    tempEvent.oldDescription = manager.description
                    tempEvent.newDescription = recvManager.description
                    if manager.description != recvManager.description:
                        changed = True

                    # add event to event queue if an information has changed
                    if changed:
                        self.events.append(tempEvent)

                    manager.deepCopy(recvManager)
                    found = True
                    break

            # when not found => add manager to list
            if not found:
                recvManager.checked = True
                self.managers.append(recvManager)

                # create new manager event
                foundNode = None
                for node in self.nodes:
                    if node.nodeId == recvManager.nodeId:
                        foundNode = node
                        break

                if foundNode is None:
                    logging.error("[%s]: Could not find node with id '%d' for manager with id '%d'."
                                  % (self.fileName, recvManager.nodeId, recvManager.managerId))
                    return False

                tempEvent = EventNewManager(timeReceived)
                tempEvent.hostname = foundNode.hostname
                tempEvent.description = recvManager.description
                self.events.append(tempEvent)

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

                    # create change alert event (only add it if an information
                    # has changed)
                    changed = False
                    tempEvent = EventChangeAlert(timeReceived)

                    # only update information if they have changed
                    tempEvent.oldDescription = alert.description
                    tempEvent.newDescription = recvAlert.description
                    if alert.description != recvAlert.description:
                        changed = True

                    tempEvent.oldRemoteAlertId = alert.remoteAlertId
                    tempEvent.newRemoteAlertId = recvAlert.remoteAlertId
                    if alert.remoteAlertId != recvAlert.remoteAlertId:
                        changed = True

                    # add event to event queue if an information has changed
                    if changed:
                        self.events.append(tempEvent)

                    alert.deepCopy(recvAlert)
                    found = True
                    break

            # when not found => add alert to list
            if not found:
                recvAlert.checked = True
                self.alerts.append(recvAlert)

                # create new alert event
                foundNode = None
                for node in self.nodes:
                    if node.nodeId == recvAlert.nodeId:
                        foundNode = node
                        break
                if foundNode is None:
                    logging.error("[%s]: Could not find node with id '%d' for alert with id '%d'."
                                  % (self.fileName, recvAlert.nodeId, recvAlert.alertId))
                    return False

                tempEvent = EventNewAlert(timeReceived)
                tempEvent.hostname = foundNode.hostname
                tempEvent.description = recvAlert.description
                self.events.append(tempEvent)

        # process received alertLevels
        for recvAlertLevel in alert_levels:

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

        # remove all nodes that are not checked
        self._removeNotCheckedNodes()

        self._update_db_data()

        return True

    # is called when a sensor alert event was received from the server
    def sensor_alert(self, server_time: int, sensor_alert: SensorAlert) -> bool:

        self.serverTime = server_time
        timeReceived = int(time.time())
        self.sensorAlerts.append(sensor_alert)

        # when events are activated
        # => create events
        if self.eventsLifeSpan != 0:

            # create sensor alert event
            tempEvent = EventSensorAlert(timeReceived)
            tempEvent.description = sensor_alert.description
            tempEvent.state = sensor_alert.state
            tempEvent.dataType = sensor_alert.dataType
            tempEvent.sensorData = sensor_alert.sensorData

            tempEvent.alertLevels = list(sensor_alert.alertLevels)
            self.events.append(tempEvent)

            # When rules are not activated and change state flag is set.
            # => Create state change event.
            if not sensor_alert.rulesActivated and sensor_alert.changeState:
                tempStateEvent = EventStateChange(timeReceived)
                tempStateEvent.state = sensor_alert.state

                # Only store data for this state change event if the sensor
                # alert carries the latest data of the sensor.
                if sensor_alert.hasLatestData:
                    tempStateEvent.dataType = sensor_alert.dataType
                    tempStateEvent.data = sensor_alert.sensorData
                else:
                    tempStateEvent.dataType = SensorDataType.NONE

                triggeredSensor = None
                for sensor in self.sensors:
                    if sensor.sensorId == sensor_alert.sensorId:
                        tempStateEvent.description = sensor.description
                        triggeredSensor = sensor
                        break

                if triggeredSensor is not None:
                    for node in self.nodes:
                        if node.nodeId == triggeredSensor.nodeId:
                            tempStateEvent.hostname = node.hostname
                            self.events.append(tempStateEvent)
                            break

                    if tempStateEvent.hostname is None:
                        logging.error("[%s]: Unable to find corresponding node to sensor for state change event."
                                      % self.fileName)

                else:
                    logging.error("[%s]: Unable to find corresponding sensor to sensor alert for state change event."
                                  % self.fileName)

        # If rules are not activated (and therefore the sensor alert was
        # only triggered by one distinct sensor).
        # => Update information in sensor which triggered the sensor alert.
        if not sensor_alert.rulesActivated:
            found = False
            for sensor in self.sensors:
                if sensor.sensorId == sensor_alert.sensorId:
                    sensor.lastStateUpdated = server_time

                    # Only update sensor state information if the flag
                    # was set in the received message.
                    if sensor_alert.changeState:
                        sensor.state = sensor_alert.state

                    # Only update sensor data information if the flag
                    # was set in the received message.
                    if sensor_alert.hasLatestData:
                        if sensor_alert.dataType == sensor.dataType:
                            sensor.data = sensor_alert.sensorData

                        else:
                            logging.error("[%s]: Sensor data type different. Skipping data assignment."
                                          % self.fileName)

                    found = True
                    break

            if not found:
                logging.error("[%s]: Sensor of sensor alert not known." % self.fileName)
                return False

        self._update_db_data()

        return True

    # is called when a state change event was received from the server
    def state_change(self,
                     server_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: SensorDataType,
                     sensor_data: Any) -> bool:

        self.serverTime = server_time

        # search sensor in list of known sensors
        # => if not known return failure
        sensor = None
        for tempSensor in self.sensors:
            if tempSensor.sensorId == sensor_id:
                sensor = tempSensor
                break
        if not sensor:
            logging.error("[%s]: Sensor for state change not known." % self.fileName)
            return False

        # when events are activated
        # => create state change event
        if self.eventsLifeSpan != 0:
            utcTimestamp = int(time.time())
            tempStateEvent = EventStateChange(utcTimestamp)
            tempStateEvent.state = state
            tempStateEvent.description = sensor.description
            tempStateEvent.dataType = sensor.dataType
            tempStateEvent.data = sensor.data

            for node in self.nodes:
                if node.nodeId == sensor.nodeId:
                    tempStateEvent.hostname = node.hostname
                    self.events.append(tempStateEvent)
                    break
            if not tempStateEvent.hostname:
                logging.error("[%s]: Unable to find corresponding node to sensor for state change event."
                              % self.fileName)

        # Change sensor state.
        sensor.state = state
        sensor.lastStateUpdated = server_time

        if data_type == sensor.dataType:
            sensor.data = sensor_data
        else:
            logging.error("[%s]: Sensor data type different. Skipping data assignment." % self.fileName)

        self._update_db_data()

        return True

    def close_connection(self):
        self._update_db_data()

    def new_connection(self):
        self._update_db_data()



# TODO
# * store data in globalData "systemData" class and update it
# * write test cases for this class