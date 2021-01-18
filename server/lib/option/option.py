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
from typing import Optional
from ..globalData import GlobalData
from ..internalSensors import ProfileChangeSensor
from ..localObjects import Option
from ..server import AsynchronousSender


class OptionExecuter(threading.Thread):
    """
    This class is woken up if an option message is received and executes all necessary steps
    """

    def __init__(self,
                 global_data: GlobalData):
        threading.Thread.__init__(self)

        # get global configured data
        self._global_data = global_data
        self._logger = self._global_data.logger
        self._storage = self._global_data.storage
        self._manager_update_executer = self._global_data.managerUpdateExecuter
        self._server_sessions = self._global_data.serverSessions
        self._profiles = self._global_data.profiles

        # file nme of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        # Create an event that is used to wake this thread up and react on options.
        self._option_event = threading.Event()
        self._option_event.clear()

        self._exit_flag = False

        self._options_queue = dict()
        self._options_queue_lock = threading.Lock()

        # Get instance of the internal profile change sensor (if exists).
        self._internal_sensor = None  # type: Optional[ProfileChangeSensor]
        for internal_sensor in self._global_data.internalSensors:
            if isinstance(internal_sensor, ProfileChangeSensor):
                self._internal_sensor = internal_sensor

    def _send_profile_change(self, option: Option):
        """
        Internal function that sends a profile change message to all alert clients.
        :param option:
        """

        curr_profile = None
        for profile in self._profiles:
            if profile.id == int(option.value):
                curr_profile = profile
                break
        if curr_profile is None:
            self._logger.error("[%s]: Not able to find profile with id %d for profile change message."
                               % (self._log_tag, int(option.value)))
            return

        for server_session in self._server_sessions:
            # ignore sessions which do not exist yet and that are not alerts.
            if server_session.clientComm is None:
                continue
            if server_session.clientComm.nodeType != "alert":
                continue
            if not server_session.clientComm.clientInitialized:
                continue

            # sending sensor alerts off to alert client
            # via a thread to not block this one
            sender = AsynchronousSender(self._global_data, server_session.clientComm)
            # set thread to daemon
            # => threads terminates when main thread terminates
            sender.daemon = True
            sender.send_profile_change = True
            sender.profile = curr_profile
            self._logger.debug("[%s]: Sending profile change to alert client (%s:%d)."
                               % (self._log_tag, server_session.clientComm.clientAddress,
                                  server_session.clientComm.clientPort))
            sender.start()

    def _sensor_profile_change(self, option: Option):
        """
        Internal function that triggers the internal sensor for profile changes.
        :param option:
        """
        if self._internal_sensor is not None:
            self._internal_sensor.process_option(option)

    def add_option(self,
                   option_type: str,
                   option_value: float,
                   option_delay: int):
        """
        Adds received option for processing.

        :param option_type:
        :param option_value:
        :param option_delay:
        """
        option = Option()
        option.type = option_type
        option.value = option_value

        time_to_change = int(time.time()) + option_delay
        with self._options_queue_lock:
            self._options_queue[option.type] = (option, time_to_change)

        self._option_event.set()

    def run(self):
        """
        This function starts the endless loop of the option executer thread.
        """

        while True:

            # If we still have options in the queue, wait a short time before starting a new processing round.
            if self._options_queue:
                time.sleep(0.5)

            # Wait until a new option has to be processed if we do not have anything in the queue.
            else:
                self._option_event.wait()

            if self._exit_flag:
                return

            has_option_changes = False
            for option_type in list(self._options_queue.keys()):

                with self._options_queue_lock:
                    option, time_to_change = self._options_queue[option_type]

                # Check if it is time to process the option.
                current_time = int(time.time())
                if current_time < time_to_change:
                    continue

                self._logger.info("[%s]: Changing option '%s' to %.3f."
                                  % (self._log_tag, option.type, option.value))

                # Change option in database.
                if not self._storage.update_option(option.type, option.value):
                    self._logger.error("[%s]: Not able to change option '%s' to %.3f."
                                       % (self._log_tag, option.type, option.value))

                    # Remove option from queue.
                    with self._options_queue_lock:
                        del self._options_queue[option_type]

                    continue

                has_option_changes = True

                # Remove option from queue.
                with self._options_queue_lock:
                    del self._options_queue[option_type]

                # Special handling of "profile" options.
                if option.type == "profile":
                    self._sensor_profile_change(option)
                    self._send_profile_change(option)

            # Only wake up manager update executer if we have any option changes.
            if has_option_changes:
                self._manager_update_executer.force_status_update()

            self._option_event.clear()

    def exit(self):
        """
        sets the exit flag to shut down the thread
        """
        self._exit_flag = True
        self._option_event.set()
