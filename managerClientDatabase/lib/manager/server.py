#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import socketserver
import logging
import os
import json
import socket
from typing import Type
from ..globalData import GlobalData
from ..client import ServerCommunication

BUFSIZE = 1024


# this class is used for the threaded unix stream server and 
# extends the constructor to pass the global configured data to all threads
class ThreadedUnixStreamServer(socketserver.ThreadingMixIn,
                               socketserver.UnixStreamServer):
    
    def __init__(self, global_data: GlobalData,
                 server_address: str,
                 RequestHandlerClass: Type[socketserver.BaseRequestHandler]):

        # get reference to global data object
        self.global_data = global_data

        socketserver.TCPServer.__init__(self,
                                        server_address,
                                        RequestHandlerClass)


# this class is used for incoming local client connections (i.e., web page)
class LocalServerSession(socketserver.BaseRequestHandler):

    def __init__(self,
                 request: socket,
                 client_address: str,
                 server: ThreadedUnixStreamServer):

        self._log_tag = os.path.basename(__file__)

        # get reference to global data object
        self._global_data = server.global_data
        self._server_comm = self._global_data.serverComm  # type: ServerCommunication

        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self):

        logging.info("[%s]: Client connected." % self._log_tag)

        # Get received data.
        try:
            data_raw = self.request.recv(BUFSIZE)
            data = data_raw.decode("ascii")

            incomingMessage = json.loads(data)

            # At the moment only option messages are allowed.
            if incomingMessage["message"].lower() != "option":

                # send error message back
                try:
                    message = {"message": incomingMessage["message"],
                               "error": "only option message valid"}
                    self.request.send(json.dumps(message).encode('ascii'))

                except Exception:
                    pass

                return

        except Exception:
            logging.exception("[%s]: Received message invalid." % self._log_tag)

            # send error message back
            try:
                message = {"message": "unknown",
                           "error": "received message invalid"}
                self.request.send(json.dumps(message).encode('ascii'))

            except Exception:
                pass

            return

        # Extract option type and value from message.
        try:
            option_type = str(incomingMessage["payload"]["optionType"]).lower()
            option_value = float(incomingMessage["payload"]["value"])
            option_delay = int(incomingMessage["payload"]["timeDelay"])

        except Exception:
            logging.exception("[%s]: Attributes of option message invalid." % self._log_tag)

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "received attributes invalid"}
                self.request.send(json.dumps(message).encode('ascii'))

            except Exception:
                pass

            return

        # At the moment only "profile" is an allowed option type.
        if option_type != "profile":

            # send error message back
            try:
                message = {"message": incomingMessage["message"],
                           "error": "only option type 'profile' allowed"}
                self.request.send(json.dumps(message).encode('ascii'))

            except Exception:
                pass

            return

        # Send option message to server.
        self._server_comm.send_option(option_type, option_value, option_delay)

        # Send response to client.
        try:
            message = {"message": incomingMessage["message"],
                       "payload": {"type": "response",
                                   "result": "ok"}}
            self.request.send(json.dumps(message).encode('ascii'))

        except Exception:
            logging.exception("[%s]: Sending response message failed." % self._log_tag)
