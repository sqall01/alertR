#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import os
import time
import collections
from typing import Optional
from .server import AsynchronousSender
from .globalData import GlobalData
from .localObjects import SensorData


# this class is woken up if a sensor alert or state change is received
# and sends updates to all manager clients
class ManagerUpdateExecuter(threading.Thread):

    def __init__(self, globalData: GlobalData):
        threading.Thread.__init__(self)

        # get global configured data
        self.globalData = globalData
        self.logger = self.globalData.logger
        self.managerUpdateInterval = self.globalData.managerUpdateInterval
        self.storage = self.globalData.storage
        self.serverSessions = self.globalData.serverSessions

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # create an event that is used to wake this thread up
        # and reacte on state changes/sensor alerts
        self._manager_update_event = threading.Event()
        self._manager_update_event.clear()

        # set exit flag as false
        self.exitFlag = False

        # this is used to know when the last status update was send to the
        # manager clients
        self.lastStatusUpdateSend = 0

        # this is used to know if a full status update has to be sent to
        # the manager clients (ignoring the time interval)
        self._force_status_update = False

        # this is a queue that is used to signalize the state changes
        # that should be sent to the manager clients
        self._queue_state_change = collections.deque()

    def run(self):

        while True:

            # check if thread should terminate
            if self.exitFlag:
                return

            # check if state change queue is empty before waiting
            # for event (or timeout)
            if len(self._queue_state_change) == 0:
                # wait 10 seconds before checking if a
                # status update to all manager nodes has to be sent
                # or check it when the event is triggered
                self._manager_update_event.wait(10)
                self._manager_update_event.clear()

            # check if last status update has timed out
            # or a status update is forced
            # => send status update to all manager
            utcTimestamp = int(time.time())
            if (utcTimestamp - self.managerUpdateInterval) > self.lastStatusUpdateSend or self._force_status_update:

                # update time when last status update was sent
                self.lastStatusUpdateSend = utcTimestamp

                # reset new client variable
                self._force_status_update = False

                # empty current state queue
                # (because the state changes are also transmitted
                # during the full state update)
                self._queue_state_change.clear()

                for serverSession in self.serverSessions:
                    # ignore sessions which do not exist yet
                    # and that are not managers
                    if serverSession.clientComm is None:
                        continue
                    if serverSession.clientComm.nodeType != "manager":
                        continue
                    if not serverSession.clientComm.clientInitialized:
                        continue

                    # sending status update to manager via a thread
                    # to not block the manager update executer
                    statusUpdateProcess = AsynchronousSender(self.globalData, serverSession.clientComm)
                    # set thread to daemon
                    # => threads terminates when main thread terminates
                    statusUpdateProcess.daemon = True
                    statusUpdateProcess.sendManagerUpdate = True
                    statusUpdateProcess.start()

                # if status update was sent to manager clients
                # => ignore state changes (because they are also covered
                # by a status update)
                continue

            # if status change queue is not empty
            # => send status changes to manager clients
            while len(self._queue_state_change) != 0:
                managerStateTuple = self._queue_state_change.popleft()
                sensorId = managerStateTuple[0]
                state = managerStateTuple[1]
                sensorDataObj = managerStateTuple[2]

                for serverSession in self.serverSessions:
                    # ignore sessions which do not exist yet
                    # and that are not managers
                    if serverSession.clientComm is None:
                        continue
                    if serverSession.clientComm.nodeType != "manager":
                        continue
                    if not serverSession.clientComm.clientInitialized:
                        continue

                    # sending status update to manager via a thread
                    # to not block the manager update executer
                    stateChangeProcess = AsynchronousSender(self.globalData, serverSession.clientComm)
                    # set thread to daemon
                    # => threads terminates when main thread terminates
                    stateChangeProcess.daemon = True
                    stateChangeProcess.sendManagerStateChange = True
                    stateChangeProcess.sendManagerStateChangeSensorId = sensorId
                    stateChangeProcess.sendManagerStateChangeState = state
                    stateChangeProcess.sendManagerStateChangeDataType = sensorDataObj.dataType
                    stateChangeProcess.sendManagerStateChangeData = sensorDataObj.data
                    stateChangeProcess.start()

    # sets the exit flag to shut down the thread
    def exit(self):
        self.exitFlag = True

    def force_status_update(self):
        """
        Force status update for manager clients.
        """
        self._force_status_update = True
        self._manager_update_event.set()

    def queue_state_change(self,
                           sensor_id: int,
                           state: int,
                           sensor_data: Optional[SensorData]):
        """
        Queues state change to send it to all connected manager clients.

        :param sensor_id:
        :param state:
        :param sensor_data:
        """
        self._queue_state_change.append((sensor_id, state, sensor_data))
        self._manager_update_event.set()
