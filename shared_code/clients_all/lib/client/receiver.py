#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import threading
import os
from .serverCommunication import ServerCommunication


# this class handles the receive part of the client
class Receiver(threading.Thread):

    def __init__(self,
                 connection: ServerCommunication):

        threading.Thread.__init__(self)
        self._connection = connection
        self._log_tag = os.path.basename(__file__)
        self._exit_flag = False

    def run(self):

        while True:
            if self._exit_flag:
                return

            # Only run the communication handler.
            # NOTE: Connection initialization is performed once during AlertR client start up
            # and by connection watchdog if it was lost.
            self._connection.handle_requests()

            time.sleep(1)

    # Sets the exit flag to shut down the thread and exists connection.
    def exit(self):
        self._exit_flag = True
        self._connection.exit()
