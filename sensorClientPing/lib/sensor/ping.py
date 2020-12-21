#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import subprocess
import time
import logging
from .core import _PollingSensor
from ..globalData import SensorAlert, StateChange, SensorDataType
from typing import Optional


# class that controls one watchdog of a challenge
class PingSensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        self.sensorDataType = SensorDataType.NONE

        # used for logging
        self.fileName = os.path.basename(__file__)

        # gives the time that the process has to execute
        self.timeout = None

        # gives the interval in seconds in which the process
        # should be checked
        self.intervalToCheck = None

        # gives the command/path that should be executed
        self.execute = None

        # gives the host of the service
        self.host = None

        # time when the process was executed
        self.timeExecute = None

        # the process itself
        self.process = None

    def initializeSensor(self):
        self.changeState = True
        self.hasLatestData = False
        self.hasOptionalData = True
        self.timeExecute = 0.0
        self.state = 1 - self.triggerState
        self.optionalData = {"host": self.host}
        return True

    def getState(self) -> int:
        return self.state

    def updateState(self):

        # check if a process is executed
        # => if none no process is executed
        if self.process is None:

            # check if the interval in which the service should be checked
            # is exceeded
            utcTimestamp = int(time.time())
            if (utcTimestamp - self.timeExecute) > self.intervalToCheck:

                logging.debug("[%s]: Executing process '%s'." % (self.fileName, self.description))
                self.process = subprocess.Popen([self.execute, "-c3", str(self.host)])
                self.timeExecute = utcTimestamp

        # => process is still running
        else:

            # check if process is not finished yet
            if self.process.poll() is None:

                # check if process has timed out
                utcTimestamp = int(time.time())
                if (utcTimestamp - self.timeExecute) > self.timeout:

                    self.state = self.triggerState

                    logging.error("[%s]: Process "
                                  % self.fileName
                                  + "'%s' has timed out."
                                  % self.description)

                    # terminate process
                    self.process.terminate()

                    # give the process one second to terminate
                    time.sleep(1)

                    # check if the process has terminated
                    # => if not kill it
                    exitCode = self.process.poll()
                    if exitCode != -15:
                        try:
                            logging.error("[%s]: Could not "
                                          % self.fileName
                                          + "terminate '%s'. Killing it."
                                          % self.description)

                            self.process.kill()
                            exitCode = self.process.poll()
                        except:
                            pass
                    self.optionalData["exitCode"] = exitCode

                    # set process to None so it can be newly started
                    # in the next state update
                    self.process = None

                    self.optionalData["reason"] = "processtimeout"

            # process has finished
            else:

                # check if the process has exited with code 0
                # => everything works fine
                exitCode = self.process.poll()
                if exitCode == 0:
                    self.state = 1 - self.triggerState
                    self.optionalData["reason"] = "reachable"
                # process did not exited correctly
                # => something is wrong with the ctf service
                else:
                    self.state = self.triggerState
                    self.optionalData["reason"] = "notreachable"
                self.optionalData["exitCode"] = exitCode

                # set process to none so it can be newly started
                # in the next state update
                self.process = None

    def forceSendAlert(self) -> Optional[SensorAlert]:
        return None

    def forceSendState(self) -> Optional[StateChange]:
        return None
