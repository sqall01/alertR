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
                self._connection.exit()
                return

            # only run the communication handler
            self._connection.handle_requests()

            time.sleep(1)

    # sets the exit flag to shut down the thread
    def exit(self):
        self._exit_flag = True
