#!/usr/bin/python3

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
import time
import socket
from typing import Type
from ..globalData import GlobalData

BUFSIZE = 1024


# this class is used for the threaded unix stream server and 
# extends the constructor to pass the global configured data to all threads
class ThreadedUnixStreamServer(socketserver.ThreadingMixIn,
                               socketserver.UnixStreamServer):
    
    def __init__(self, globalData: GlobalData,
                 serverAddress: str,
                 RequestHandlerClass: Type[socketserver.BaseRequestHandler]):

        # get reference to global data object
        self.globalData = globalData

        socketserver.TCPServer.__init__(self,
                                        serverAddress,
                                        RequestHandlerClass)


# this class is used for incoming local client connections (i.e., web page)
class LocalServerSession(socketserver.BaseRequestHandler):

    def __init__(self,
                 request: socket,
                 clientAddress: str,
                 server: ThreadedUnixStreamServer):

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # get reference to global data object
        self.globalData = server.globalData
        self.serverComm = self.globalData.serverComm

        socketserver.BaseRequestHandler.__init__(self, request, clientAddress, server)

    def handle(self):

        logging.info("[%s]: Client connected." % self.fileName)

        # get received data
        data_raw = self.request.recv(BUFSIZE)
        data = data_raw.decode("ascii")

        # convert data to json
        try:
            incomingMessage = json.loads(data)

            # at the moment only option messages are allowed
            if incomingMessage["message"] != "option":

                # send error message back
                try:
                    utcTimestamp = int(time.time())
                    message = {"serverTime": utcTimestamp,
                               "message": incomingMessage["message"],
                               "error": "only option message valid"}
                    self.request.send(json.dumps(message).encode('ascii'))

                except Exception:
                    pass

                return

        except Exception:
            logging.exception("[%s]: Received message invalid." % self.fileName)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                           "message": "unknown",
                           "error": "received json message invalid"}
                self.request.send(json.dumps(message).encode('ascii'))

            except Exception:
                pass

            return

        # extract option type and value from message
        try:
            optionType = str(incomingMessage["payload"]["optionType"])
            optionValue = float(incomingMessage["payload"]["value"])
            optionDelay = int(incomingMessage["payload"]["timeDelay"])

        except Exception:
            logging.exception("[%s]: Attributes of option message invalid." % self.fileName)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                           "message": incomingMessage["message"],
                           "error": "received attributes invalid"}
                self.request.send(json.dumps(message).encode('ascii'))

            except Exception:
                pass

            return

        # at the moment only "alertSystemActive" is an allowed option type
        if optionType != "alertSystemActive":

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                           "message": incomingMessage["message"],
                           "error": "only option type 'alertSystemActive' allowed"}
                self.request.send(json.dumps(message).encode('ascii'))

            except Exception:
                pass

            return

        # send option message to server
        promise = self.serverComm.send_option(optionType, optionValue, optionDelay)
        promise.is_finished(blocking=True)

        if promise.was_successful():

            # send response to client
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                           "message": incomingMessage["message"],
                           "payload": {"type": "response",
                                       "result": "ok"}}
                self.request.send(json.dumps(message).encode('ascii'))

            except Exception:
                logging.exception("[%s]: Sending response message failed." % self.fileName)

        else:
            logging.error("[%s]: Sending message to server failed." % self.fileName)

            # send error message back
            try:
                utcTimestamp = int(time.time())
                message = {"serverTime": utcTimestamp,
                           "message": incomingMessage["message"],
                           "error": "sending message to server failed"}
                self.request.send(json.dumps(message).encode('ascii'))

            except Exception:
                pass
