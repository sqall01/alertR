#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import threading
import logging
import random
import json
import os
import socket
from typing import Optional
from .core import BUFSIZE, Client


class PromiseState:
    SUCCESS = 1
    FAILED = 2
    PENDING = 3


class Promise:

    def __init__(self, msg_type: str, msg: str):
        self._finished_event = threading.Event()
        self._finished_event.clear()
        self._state = PromiseState.PENDING
        self._msg = msg
        self._msg_type = msg_type.lower()
        self._creation_time = int(time.time())

    @property
    def msg(self):
        return self._msg

    @property
    def msg_type(self):
        return self._msg_type

    def is_finished(self, blocking: bool = False) -> bool:
        if blocking:
            self._finished_event.wait()

        return self._state != PromiseState.PENDING

    def set_failed(self):
        self._state = PromiseState.FAILED
        self._finished_event.set()

    def set_success(self):
        self._state = PromiseState.SUCCESS
        self._finished_event.set()

    def was_successful(self):
        if self._state == PromiseState.SUCCESS:
            return True

        elif self._state == PromiseState.FAILED:
            return False

        else:
            raise ValueError("Request not finisehd.")


class Communication(threading.Thread):

    def __init__(self,
                 host: str,
                 port: int,
                 server_ca_file: str,
                 client_cert_file: str,
                 client_key_file: str):
        threading.Thread.__init__(self)

        self.host = host
        self.port = port
        self.server_ca_file = server_ca_file
        self.client_cert_file = client_cert_file
        self.client_key_file = client_key_file

        self._client_lock = threading.Lock()
        self._client = None

        self._exit_flag = False
        self._log_tag = os.path.basename(__file__)

        self._new_msg_event = threading.Event()
        self._new_msg_event.clear()

        self._msg_queue = []
        self._msg_queue_lock = threading.Lock()

    # noinspection PyBroadException
    def connect(self) -> bool:

        # Closes existing connection if we have one.
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass

        # create client instance and connect to the server
        self._client = Client(self.host,
                              self.port,
                              self.server_ca_file,
                              self.client_cert_file,
                              self.client_key_file)

        try:
            self._client.connect()

        except Exception:
            logging.exception("[%s]: Connecting to server failed." % self._log_tag)
            try:
                self._client.close()
            except Exception:
                pass

            return False

        return True

    # noinspection PyBroadException
    def _initiate_transaction(self,
                              messageType: str,
                              messageSize: int) -> bool:
        """
        This internal function tries to initiate a transaction with the server.

        :param messageType:
        :param messageSize:
        :return:
        """

        # generate a random "unique" transaction id
        # for this transaction
        transaction_id = random.randint(0, 0xffffffff)

        # send RTS (request to send) message
        logging.debug("[%s]: Sending RTS %d message."
                      % (self._log_tag, transaction_id))
        try:
            payload = {"type": "rts",
                       "id": transaction_id}
            utc_timestamp = int(time.time())
            message = {"clientTime": utc_timestamp,
                       "size": messageSize,
                       "message": messageType,
                       "payload": payload}
            self._client.send(json.dumps(message))

        except Exception:
            logging.exception("[%s]: Sending RTS failed." % self._log_tag)
            return False

        # get CTS (clear to send) message
        logging.debug("[%s]: Receiving CTS." % self._log_tag)

        received_transaction_id = -1
        received_message_type = ""
        received_payload_type = ""
        try:
            data = self._client.recv(BUFSIZE)
            message = json.loads(data)

            # Check if an error was received
            # (only log error, gets handled afterwards)
            if "error" in message.keys():
                logging.error("[%s]: Error received: %s"
                              % (self._log_tag, message["error"]))

            # if no error => extract values from message
            else:
                received_transaction_id = int(message["payload"]["id"])
                received_message_type = str(message["message"])
                received_payload_type = str(message["payload"]["type"]).upper()

        except Exception:
            logging.exception("[%s]: Receiving CTS failed." % self._log_tag)
            return False

        # check if RTS is acknowledged by a CTS
        # => exit transaction initiation loop
        if (received_transaction_id == transaction_id
           and received_message_type == messageType
           and received_payload_type == "CTS"):

            logging.debug("[%s]: Initiate transaction succeeded." % self._log_tag)
            return True

        # if RTS was not acknowledged
        # => release lock and backoff for a random time then retry again
        else:
            logging.warning("[%s]: Initiate transaction failed. Backing off." % self._log_tag)
            return False

    # noinspection PyBroadException
    def exit(self):
        """
        Sets the exit flag to shut down the thread and closes connection.
        """
        self._exit_flag = True

        try:
            self._client.close()
        except Exception:
            pass

    def run(self):

        logging.info("[%s] Starting Request Sender thread." % self._log_tag)

        while True:

            # Wait until a new message has to be sent.
            self._new_msg_event.wait(5)

            if self._exit_flag:
                logging.info("[%s] Exiting Request Sender thread." % self._log_tag)
                return

            backoff = False
            while self._msg_queue:

                # Backoff random time between 0 and 1 second.
                if backoff:
                    backoff_time = float(random.randint(0, 100))/100
                    logging.debug("[%s] Backing off from sending request for %.3f seconds."
                                  % (self._log_tag, backoff_time))
                    time.sleep(backoff_time)

                if self._exit_flag:
                    logging.info("[%s] Exiting Request Sender thread." % self._log_tag)
                    return

                with self._msg_queue_lock:
                    promise = self._msg_queue.pop(0)

                # Have the client exclusively locked for this communication.
                with self._client_lock:

                    # Initiate transaction with server.
                    backoff = False
                    if not self._initiate_transaction(promise.msg_type, len(promise.msg)):
                        with self._msg_queue_lock:
                            self._msg_queue.insert(0, promise)
                        backoff = True
                        continue

                    # Send message.
                    try:
                        logging.debug("[%s]: Sending message of type '%s'." % (self._log_tag, promise.msg_type))
                        self._client.send(promise.msg)

                    except Exception:
                        logging.exception("[%s]: Sending message of type '%s' failed." % (self._log_tag, promise.msg_type))
                        backoff = True
                        continue

                    # Receive response.
                    try:
                        data = self._client.recv(BUFSIZE)
                        message = json.loads(data)

                        # check if an error was received
                        if "error" in message.keys():
                            logging.error("[%s]: Error received for message of type '%s': %s"
                                          % (self._log_tag, promise.msg_type, message["error"]))
                            promise.set_failed()
                            continue

                        # Check if we received an answer to our sent request.
                        if str(message["message"]).lower() != promise.msg_type:
                            logging.error("[%s]: Wrong message type for message of type '%s' received: %s"
                                          % (self._log_tag, promise.msg_type, message["message"]))

                            # Send error message back.
                            try:
                                utcTimestamp = int(time.time())
                                message = {"clientTime": utcTimestamp,
                                           "message": message["message"],
                                           "error": "%s message expected" % promise.msg_type}
                                self._client.send(json.dumps(message))
                            except Exception:
                                pass

                            promise.set_failed()
                            continue

                        # Check if the received type (rts/cts/request/response) is the correct one.
                        if str(message["payload"]["type"]).lower() != "response":

                            logging.error("[%s]: Response expected for message of type '%s'."
                                          % (self._log_tag, promise.msg_type))

                            # Send error message back
                            try:
                                utcTimestamp = int(time.time())
                                message = {"clientTime": utcTimestamp,
                                           "message": message["message"],
                                           "error": "response expected"}
                                self._client.send(json.dumps(message))
                            except Exception as e:
                                pass

                            promise.set_failed()
                            continue

                        # Check if result of message was ok.
                        if str(message["payload"]["result"]).lower() != "ok":
                            logging.error("[%s]: Wrong result for message of type '%s' received: %s"
                                          % (self._log_tag, promise.msg_type, message["payload"]["result"]))

                            promise.set_failed()
                            continue

                        logging.debug("[%s]: Received valid response for message of type '%s'."
                                      % (self._log_tag, promise.msg_type))

                        promise.set_success()

                    except Exception:
                        logging.exception("[%s]: Receiving response for message of type '%s' failed."
                                          % (self._log_tag, promise.msg_type))
                        promise.set_failed()
                        continue

            self._new_msg_event.clear()

    def send_request(self,
                     msg_type: str,
                     msg: str) -> Promise:
        """
        Inserts a message into the send queue and returns a promise that it is to be sent.

        :param msg: Message string to send.
        :param msg_type: Type of the message we are sending.
        :return: promise which contains the results after it was send and data was received.
        """
        promise = Promise(msg_type, msg)
        with self._msg_queue_lock:
            self._msg_queue.append(promise)

        self._new_msg_event.set()
        return promise

    # noinspection PyBroadException
    def send(self,
             msg: str):
        """
        Sends the given message to the server. Does not guarantee that the message is received
        (kind of an UDP packet ;) ).

        :param msg: Message string to send.
        """
        with self._client_lock:
            try:
                self._client.send(msg)
            except Exception:
                pass

    # noinspection PyBroadException
    def recv(self) -> Optional[str]:
        """
        Raw receiving method that just plainly returns the received data.

        :return: Data received as string.
        """
        with self._client_lock:
            try:
                data = self._client.recv(BUFSIZE)
            except Exception:
                logging.exception("[%s]: Receiving failed." % self._log_tag)
                return None

            if not data:
                return None
        return data

    # noinspection PyBroadException
    def recv_request(self) -> Optional[str]:
        """
        Returns received request as string. Blocking until request is received or error occurs.
        Does not block the channel. Handles RTS/CTS messages with server.

        :return: Data of the received request.
        """
        while True:
            try:
                with self._client_lock:
                    data = self._client.recv(BUFSIZE, timeout=0.5)
                    if not data:
                        return None

                    data = data.strip()
                    message = json.loads(data)

                    # Check if an error was received.
                    if "error" in message.keys():
                        logging.error("[%s]: Error received: %s" % (self._log_tag, message["error"]))
                        return None

                    # Check if RTS was received
                    # => acknowledge
                    if str(message["payload"]["type"]).lower() == "rts":
                        received_transaction_id = int(message["payload"]["id"])
                        message_size = int(message["size"])

                        # Received RTS (request to send) message.
                        logging.debug("[%s]: Received RTS %s message."
                                      % (self._log_tag, received_transaction_id))

                        logging.debug("[%s]: Sending CTS %s message."
                                      % (self._log_tag, received_transaction_id))

                        # send CTS (clear to send) message
                        payload = {"type": "cts",
                                   "id": received_transaction_id}
                        utc_timestamp = int(time.time())
                        message = {"clientTime": utc_timestamp,
                                   "message": str(message["message"]),
                                   "payload": payload}
                        self._client.send(json.dumps(message))

                        # After initiating transaction receive actual command.
                        data = ""
                        last_size = 0
                        while len(data) < message_size:
                            data += self._client.recv(BUFSIZE)

                            # Check if the size of the received data has changed.
                            # If not we detected a possible dead lock.
                            if last_size != len(data):
                                last_size = len(data)

                            else:
                                logging.error("[%s]: Possible dead lock detected while receiving data. "
                                              % self._log_tag
                                              + "Closing connection to server.")
                                return None

                    # if no RTS was received
                    # => server does not stick to protocol
                    # => terminate session
                    else:

                        logging.error("[%s]: Did not receive RTS. Server sent: %s"
                                      % (self._log_tag, data))
                        return None

            except socket.timeout as e:
                # release lock and acquire to let other threads send
                # data to the server
                # (wait 0.5 seconds in between, because semaphore
                # are released in random order => other threads could be
                # unlucky and not be chosen => this has happened when
                # loglevel was not debug => hdd I/O has slowed this process down)
                time.sleep(0.5)

                # Continue receiving.
                continue

            except Exception:
                logging.exception("[%s]: Receiving failed." % self._log_tag)
                return None

            return data
