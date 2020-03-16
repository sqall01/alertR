#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import logging
import os
import threading
from typing import Optional
from .serverCommunication import ServerCommunication
from ..smtp import SMTPAlert


# this class checks if the connection to the server has broken down
# => reconnects it if necessary
class ConnectionWatchdog(threading.Thread):

    def __init__(self, connection: ServerCommunication, pingInterval: int, smtpAlert: Optional[SMTPAlert]):
        threading.Thread.__init__(self)

        # the object that handles the communication with the server
        self.connection = connection

        # the interval in which a ping should be send when no data
        # was received in this time
        self.pingInterval = pingInterval

        # the object to send a email alert via smtp
        self.smtpAlert = smtpAlert

        # the file name of this file for logging
        self.fileName = os.path.basename(__file__)

        # set exit flag as false
        self.exitFlag = False

        # internal counter to get the current count of connection retries
        self.connectionRetries = 1

    def run(self):

        # check every 5 seconds if the client is still connected
        # and the time of the last received data
        # from the server lies too far in the past
        while True:

            # wait 5 seconds before checking time of last received data
            for i in range(5):
                if self.exitFlag:
                    logging.info("[%s]: Exiting ConnectionWatchdog." % self.fileName)
                    return
                time.sleep(1)

            # check if the client is still connected to the server
            if not self.connection.isConnected():

                logging.error("[%s]: Connection to server has died. " % self.fileName)

                # reconnect to the server
                while True:

                    # check if 5 unsuccessful attempts are made to connect
                    # to the server and if smtp alert is activated
                    # => send eMail alert
                    if self.smtpAlert is not None and (self.connectionRetries % 5) == 0:
                        self.smtpAlert.sendCommunicationAlert(self.connectionRetries)

                    # try to connect to the server
                    if self.connection.reconnect():
                        # if smtp alert is activated
                        # => send email that communication problems are solved
                        if self.smtpAlert is not None:
                            self.smtpAlert.sendCommunicationAlertClear()

                        logging.info("[%s] Reconnecting successful after %d attempts."
                                     % (self.fileName, self.connectionRetries))

                        self.connectionRetries = 1
                        break
                    self.connectionRetries += 1

                    logging.error("[%s]: Reconnecting failed. Retrying in 5 seconds." % self.fileName)
                    time.sleep(5)

                continue

            # check if the time of the data last received lies too far in the
            # past => send ping to check connection
            utcTimestamp = int(time.time())
            if (utcTimestamp - self.connection.lastRecv) > self.pingInterval:
                logging.debug("[%s]: Ping interval exceeded." % self.fileName)

                # check if PING failed
                if not self.connection.sendKeepalive():
                    logging.error("[%s]: Connection to server has died." % self.fileName)

                    # reconnect to the server
                    while True:

                        # check if 5 unsuccessful attempts are made to connect
                        # to the server and if smtp alert is activated
                        # => send eMail alert
                        if self.smtpAlert is not None and (self.connectionRetries % 5) == 0:
                            self.smtpAlert.sendCommunicationAlert(self.connectionRetries)

                        # try to connect to the server
                        if self.connection.reconnect():
                            # if smtp alert is activated
                            # => send email that communication
                            # problems are solved
                            if self.smtpAlert is not None:
                                self.smtpAlert.sendCommunicationAlertClear()

                            logging.info("[%s] Reconnecting successful after %d attempts."
                                         % (self.fileName, self.connectionRetries))

                            self.connectionRetries = 1
                            break
                        self.connectionRetries += 1

                        logging.error("[%s]: Reconnecting failed. Retrying in 5 seconds." % self.fileName)
                        time.sleep(5)

    # sets the exit flag to shut down the thread
    def exit(self):
        self.exitFlag = True
