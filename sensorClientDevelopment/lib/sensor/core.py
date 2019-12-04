#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import os
import logging
import threading
from ..client import AsynchronousSender
from ..localObjects import SensorAlert, StateChange
from ..globalData import GlobalData
from typing import Optional, List


# Internal class that holds the important attributes
# for a sensor to work (this class must be inherited from the
# used sensor class).
class _PollingSensor:

    def __init__(self):

        # Id of this sensor on this client. Will be handled as
        # "remoteSensorId" by the server.
        self.id = None # type: Optional[int]

        # Description of this sensor.
        self.description = None # type: Optional[str]

        # Delay in seconds this sensor has before a sensor alert is
        # issued by the server.
        self.alertDelay = None # type: Optional[int]

        # Local state of the sensor (either 1 or 0). This state is translated
        # (with the help of "triggerState") into 1 = "triggered" / 0 = "normal"
        # when it is send to the server.
        self.state = None # type: Optional[int]

        # State the sensor counts as triggered (either 1 or 0).
        self.triggerState = None # type: Optional[int]

        # A list of alert levels this sensor belongs to.
        self.alertLevels = list() # type: List[int]

        # Flag that indicates if this sensor should trigger a sensor alert
        # for the state "triggered" (true or false).
        self.triggerAlert = None # type: Optional[bool]

        # Flag that indicates if this sensor should trigger a sensor alert
        # for the state "normal" (true or false).
        self.triggerAlertNormal = None # type: Optional[bool]

        # The type of data the sensor holds (i.e., none at all, integer, ...).
        # Type is given by the enum class "SensorDataType".
        self.sensorDataType = None # type: Optional[int]

        # The actual data the sensor holds.
        self.sensorData = None # type: Optional[int, float]

        # Flag indicates if this sensor alert also holds
        # the data the sensor has. For example, the data send
        # with this alarm message could be the data that triggered
        # the alarm, but not necessarily the data the sensor
        # currently holds. Therefore, this flag indicates
        # if the data contained by this message is also the
        # current data of the sensor and can be used for example
        # to update the data the sensor has.
        self.hasLatestData = None # type: Optional[bool]

        # Flag that indicates if a sensor alert that is send to the server
        # should also change the state of the sensor accordingly. This flag
        # can be useful if the sensor watches multiple entities. For example,
        # a timeout sensor could watch multiple hosts and has the state
        # "triggered" when at least one host has timed out. When one host
        # connects back and still at least one host is timed out,
        # the sensor can still issue a sensor alert for the "normal"
        # state of the host that connected back, but the sensor
        # can still has the state "triggered".
        self.changeState = None # type: Optional[bool]

        # Optional data that can be transfered when a sensor alert is issued.
        self.hasOptionalData = False # type: bool
        self.optionalData = None

        # Flag indicates if the sensor changes its state directly
        # by using forceSendAlert() and forceSendState() and the SensorExecuter
        # should ignore state changes and thereby not generate sensor alerts.
        self.handlesStateMsgs = False # type: bool

    # this function returns the current state of the sensor
    def getState(self) -> int:
        raise NotImplementedError("Function not implemented yet.")


    # this function updates the state variable of the sensor
    def updateState(self):
        raise NotImplementedError("Function not implemented yet.")

    # This function initializes the sensor.
    #
    # Returns True or False depending on the success of the initialization.
    def initializeSensor(self) -> bool:
        raise NotImplementedError("Function not implemented yet.")

    # This function decides if a sensor alert for this sensor should be sent
    # to the server. It is checked regularly and can be used to force
    # a sensor alert despite the state of the sensor has not changed.
    #
    # Returns an object of class SensorAlert if a sensor alert should be sent
    # or None.
    def forceSendAlert(self) -> Optional[SensorAlert]:
        raise NotImplementedError("Function not implemented yet.")

    # This function decides if an update for this sensor should be sent
    # to the server. It is checked regularly and can be used to force an update
    # of the state and data of this sensor to be sent to the server.
    #
    # Returns an object of class StateChange if a sensor alert should be sent
    # or None.
    def forceSendState(self) -> Optional[StateChange]:
        raise NotImplementedError("Function not implemented yet.")


# this class polls the sensor states and triggers alerts and state changes
class SensorExecuter(threading.Thread):

    def __init__(self, globalData: GlobalData):
        threading.Thread.__init__(self)
        self.fileName = os.path.basename(__file__)
        self.globalData = globalData
        self.connection = self.globalData.serverComm
        self.sensors = self.globalData.sensors

        # Flag indicates if the thread is initialized.
        self._isInitialized = False

    def isInitialized(self) -> bool:
        return self._isInitialized

    def run(self):
        self.execute()

    def execute(self):

        # time on which the last full sensor states were sent
        # to the server
        lastFullStateSent = 0

        # Get reference to server communication object.
        while self.connection is None:
            time.sleep(0.5)
            self.connection = self.globalData.serverComm

        self._isInitialized = True

        while True:

            # check if the client is connected to the server
            # => wait and continue loop until client is connected
            if not self.connection.isConnected():
                time.sleep(0.5)
                continue

            # poll all sensors and check their states
            for sensor in self.sensors:

                oldState = sensor.getState()
                sensor.updateState()
                currentState = sensor.getState()

                # Check if a sensor alert is forced to send to the server.
                # => update already known state and continue
                sensorAlert = sensor.forceSendAlert()
                if sensorAlert:
                    oldState = currentState

                    asyncSenderProcess = AsynchronousSender(
                        self.connection, self.globalData)
                    # set thread to daemon
                    # => threads terminates when main thread terminates 
                    asyncSenderProcess.daemon = True
                    asyncSenderProcess.sendSensorAlert = True
                    asyncSenderProcess.sendSensorAlertSensorAlert = sensorAlert
                    asyncSenderProcess.start()

                    continue

                # check if the current state is the same
                # than the already known state => continue
                elif oldState == currentState:
                    continue

                # Check if we should ignore state changes and just let
                # the sensor handle sensor alerts by using forceSendAlert()
                # and forceSendState().
                elif sensor.handlesStateMsgs:
                    continue

                # check if the current state is an alert triggering state
                elif currentState == sensor.triggerState:

                    # check if the sensor triggers a sensor alert
                    # => send sensor alert to server
                    if sensor.triggerAlert:

                        logging.info("[%s]: Sensor alert " % self.fileName
                            + "triggered by '%s'." % sensor.description)

                        # Create sensor alert object to send to the server.
                        sensorAlert = SensorAlert()
                        sensorAlert.clientSensorId = sensor.id
                        sensorAlert.state = 1
                        sensorAlert.hasOptionalData = sensor.hasOptionalData
                        sensorAlert.optionalData = sensor.optionalData
                        sensorAlert.changeState = sensor.changeState
                        sensorAlert.hasLatestData = sensor.hasLatestData
                        sensorAlert.dataType = sensor.sensorDataType
                        sensorAlert.sensorData = sensor.sensorData

                        asyncSenderProcess = AsynchronousSender(
                            self.connection, self.globalData)
                        # set thread to daemon
                        # => threads terminates when main thread terminates 
                        asyncSenderProcess.daemon = True
                        asyncSenderProcess.sendSensorAlert = True
                        asyncSenderProcess.sendSensorAlertSensorAlert = \
                            sensorAlert
                        asyncSenderProcess.start()

                    # if sensor does not trigger sensor alert
                    # => just send changed state to server
                    else:

                        logging.debug("[%s]: State " % self.fileName
                            + "changed by '%s'." % sensor.description)

                        # Create state change object to send to the server.
                        stateChange = StateChange()
                        stateChange.clientSensorId = sensor.id
                        stateChange.state = 1
                        stateChange.dataType = sensor.sensorDataType
                        stateChange.sensorData = sensor.sensorData

                        asyncSenderProcess = AsynchronousSender(
                            self.connection, self.globalData)
                        # set thread to daemon
                        # => threads terminates when main thread terminates 
                        asyncSenderProcess.daemon = True
                        asyncSenderProcess.sendStateChange = True
                        asyncSenderProcess.sendStateChangeStateChange = \
                            stateChange
                        asyncSenderProcess.start()

                # only possible situation left => sensor changed
                # back from triggering state to a normal state
                else:

                    # check if the sensor triggers a sensor alert when
                    # state is back to normal
                    # => send sensor alert to server
                    if sensor.triggerAlertNormal:

                        logging.info("[%s]: Sensor alert " % self.fileName
                            + "for normal state "
                            + "triggered by '%s'." % sensor.description)

                        # Create sensor alert object to send to the server.
                        sensorAlert = SensorAlert()
                        sensorAlert.clientSensorId = sensor.id
                        sensorAlert.state = 0
                        sensorAlert.hasOptionalData = sensor.hasOptionalData
                        sensorAlert.optionalData = sensor.optionalData
                        sensorAlert.changeState = sensor.changeState
                        sensorAlert.hasLatestData = sensor.hasLatestData
                        sensorAlert.dataType = sensor.sensorDataType
                        sensorAlert.sensorData = sensor.sensorData

                        asyncSenderProcess = AsynchronousSender(
                            self.connection, self.globalData)
                        # set thread to daemon
                        # => threads terminates when main thread terminates 
                        asyncSenderProcess.daemon = True
                        asyncSenderProcess.sendSensorAlert = True
                        asyncSenderProcess.sendSensorAlertSensorAlert = \
                            sensorAlert
                        asyncSenderProcess.start()

                    # if sensor does not trigger sensor alert when
                    # state is back to normal
                    # => just send changed state to server
                    else:

                        logging.debug("[%s]: State " % self.fileName
                            + "changed by '%s'." % sensor.description)

                        # Create state change object to send to the server.
                        stateChange = StateChange()
                        stateChange.clientSensorId = sensor.id
                        stateChange.state = 0
                        stateChange.dataType = sensor.sensorDataType
                        stateChange.sensorData = sensor.sensorData

                        asyncSenderProcess = AsynchronousSender(
                            self.connection, self.globalData)
                        # set thread to daemon
                        # => threads terminates when main thread terminates 
                        asyncSenderProcess.daemon = True
                        asyncSenderProcess.sendStateChange = True
                        asyncSenderProcess.sendStateChangeStateChange = \
                            stateChange
                        asyncSenderProcess.start()

            # Poll all sensors if they want to force an update that should
            # be send to the server.
            for sensor in self.sensors:

                stateChange = sensor.forceSendState()
                if stateChange:
                    asyncSenderProcess = AsynchronousSender(
                        self.connection, self.globalData)
                    # set thread to daemon
                    # => threads terminates when main thread terminates 
                    asyncSenderProcess.daemon = True
                    asyncSenderProcess.sendStateChange = True
                    asyncSenderProcess.sendStateChangeStateChange = stateChange
                    asyncSenderProcess.start()

            # check if the last state that was sent to the server
            # is older than 60 seconds => send state update
            utcTimestamp = int(time.time())
            if (utcTimestamp - lastFullStateSent) > 60:

                logging.debug("[%s]: Last state " % self.fileName
                    + "timed out.")

                asyncSenderProcess = AsynchronousSender(
                    self.connection, self.globalData)
                # set thread to daemon
                # => threads terminates when main thread terminates 
                asyncSenderProcess.daemon = True
                asyncSenderProcess.sendSensorsState = True
                asyncSenderProcess.start()

                # update time on which the full state update was sent
                lastFullStateSent = utcTimestamp
                
            time.sleep(0.5)
