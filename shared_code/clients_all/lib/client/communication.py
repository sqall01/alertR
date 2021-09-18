#!/usr/bin/env python3

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
from typing import Optional, Dict, Any
from .core import BUFSIZE, RecvTimeout, Connection
from .util import MsgChecker


class MsgState:
    OK = 1
    EXPIRED = 2


class MsgRequest:

    def __init__(self,
                 msg_dict: Dict[str, Any],
                 transaction_id: int,
                 time_received: int,
                 state: int):
        self._msg_dict = msg_dict
        self._state = state
        self._transaction_id = transaction_id
        self._time_received = time_received

    @property
    def msg_dict(self) -> Dict[str, Any]:
        return self._msg_dict

    @property
    def state(self) -> int:
        return self._state


class PromiseState:
    SUCCESS = 1
    FAILED = 2
    PENDING = 3


class Promise:

    def __init__(self,
                 msg_type: str,
                 msg: str):
        self._finished_event = threading.Event()
        self._finished_event.clear()
        self._state = PromiseState.PENDING
        self._msg = msg
        self._msg_type = msg_type.lower()
        self._creation_time = int(time.time())

        # Store transaction id to refer to this id if we have a multi-part transaction.
        # (Multi-part transactions do not exist at the moment, perhaps we need them later)
        self._transaction_id = None  # type: Optional[int]

    @property
    def msg(self) -> str:
        return self._msg

    @property
    def msg_type(self) -> str:
        return self._msg_type

    @property
    def transaction_id(self) -> Optional[int]:
        return self._transaction_id

    def clear_transaction_id(self):
        self._transaction_id = None

    def is_finished(self,
                    blocking: bool = False,
                    timeout: Optional[float] = None) -> bool:
        if blocking:
            self._finished_event.wait()

        if timeout is not None:
            self._finished_event.wait(timeout)

        return self._state != PromiseState.PENDING

    def set_failed(self):
        self._state = PromiseState.FAILED
        self._finished_event.set()

    def set_success(self):
        self._state = PromiseState.SUCCESS
        self._finished_event.set()

    def set_transaction_id(self, transaction_id: int):
        if self._transaction_id is not None:
            raise ValueError("Transaction id already set.")
        self._transaction_id = transaction_id

    def was_successful(self):
        if self._state == PromiseState.SUCCESS:
            return True

        elif self._state == PromiseState.FAILED:
            return False

        else:
            raise ValueError("Request not finished.")


class Communication:

    def __init__(self,
                 connection: Connection,
                 is_server: bool = False):

        # Maximum time in milliseconds the communication is backed off in case of collision.
        # Prioritize server messages.
        if is_server:
            self._backoff_min = 0
            self._backoff_max = 500
        else:
            self._backoff_min = 1000
            self._backoff_max = 2000

        # Time in seconds a message is considered fresh and thus will be processed.
        # Since messages are queued if no connection to the client/server is available,
        # we want to discard too old messages.
        self._msg_expiration = 600

        self._connection_lock = threading.Lock()
        self._connection = connection

        self._exit_flag = False
        self._log_tag = os.path.basename(__file__)

        self._new_msg_event = threading.Event()
        self._new_msg_event.clear()

        self._msg_queue = []
        self._msg_queue_lock = threading.Lock()

        self._transaction_ids = dict()
        self._transaction_ids_lock = threading.Lock()

        # Timestamp when the last communication with the other side occurred.
        self._last_communication = 0

        # Flag that indicates if we have a valid communication channel to the other side.
        self._has_channel = False

        self._is_server = is_server

        # Start request sender thread.
        self._thread_request_sender = threading.Thread(target=self._request_sender,
                                                       daemon=True)
        self._thread_request_sender.start()

    @property
    def has_channel(self):
        return self._has_channel

    @property
    def last_communication(self):
        return self._last_communication

    # noinspection PyBroadException
    def _initiate_transaction(self, promise: Promise) -> bool:
        """
        This internal function tries to initiate a transaction with the other side.

        :param promise:
        :return:
        """
        # Generate a random "unique" transaction id for this transaction.
        transaction_id = random.randint(0, 0xffffffff)

        # send RTS (request to send) message
        logging.debug("[%s]: Sending RTS %d message." % (self._log_tag, transaction_id))
        try:
            payload = {"type": "rts",
                       "id": transaction_id}
            message = {"size": len(promise.msg),
                       "message": promise.msg_type,
                       "payload": payload}
            self._connection.send(json.dumps(message))

        except Exception:
            self._has_channel = False
            logging.exception("[%s]: Sending RTS failed." % self._log_tag)
            return False

        # get CTS (clear to send) message
        logging.debug("[%s]: Receiving CTS." % self._log_tag)

        received_transaction_id = -1
        received_message_type = ""
        received_payload_type = ""
        try:
            data = self._connection.recv(BUFSIZE).decode("ascii")
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
            self._has_channel = False
            logging.exception("[%s]: Receiving CTS failed." % self._log_tag)
            return False

        # check if RTS is acknowledged by a CTS
        # => exit transaction initiation loop
        if (received_transaction_id == transaction_id
                and received_message_type == promise.msg_type
                and received_payload_type == "CTS"):

            logging.debug("[%s]: Initiate transaction succeeded." % self._log_tag)
            self._last_communication = int(time.time())
            promise.set_transaction_id(transaction_id)
            return True

        # if RTS was not acknowledged
        # => release lock and backoff for a random time then retry again
        else:
            logging.warning("[%s]: Initiate transaction failed. Backing off." % self._log_tag)
            return False

    # noinspection PyBroadException
    def _request_sender(self):
        """
        Request sender loop that processes the message queue.

        :return:
        """
        logging.info("[%s] Starting Request Sender thread." % self._log_tag)

        while True:

            # If we still have messages in the queue, wait a short time before starting a new sending round.
            if self._msg_queue:
                time.sleep(0.5)

            # Wait until a new message has to be sent if we do not have anything in the queue.
            else:
                self._new_msg_event.wait(5)

            if self._exit_flag:
                logging.info("[%s] Exiting Request Sender thread." % self._log_tag)
                return

            # Only process message queue if we have a working communication channel.
            if not self._has_channel:
                continue

            backoff = False
            while self._msg_queue:

                # Backoff random time between X and Y seconds.
                if backoff:
                    backoff_time = float(random.randint(self._backoff_min, self._backoff_max))/1000
                    logging.debug("[%s] Backing off from sending request for %.3f seconds."
                                  % (self._log_tag, backoff_time))
                    time.sleep(backoff_time)

                if self._exit_flag:
                    logging.info("[%s] Exiting Request Sender thread." % self._log_tag)
                    return

                with self._msg_queue_lock:
                    promise = self._msg_queue.pop(0)

                # Have the connection exclusively locked for this communication.
                with self._connection_lock:

                    # Only send message if we have a working communication channel.
                    if not self._has_channel:
                        self._msg_queue.insert(0, promise)
                        break

                    # Initiate transaction with other side.
                    backoff = False
                    if not self._initiate_transaction(promise):
                        with self._msg_queue_lock:
                            promise.clear_transaction_id()
                            self._msg_queue.insert(0, promise)
                        backoff = True
                        continue

                    # Send message.
                    try:
                        logging.debug("[%s]: Sending message of type '%s'." % (self._log_tag, promise.msg_type))
                        self._connection.send(promise.msg)

                    except OSError:
                        logging.exception("[%s]: Sending message of type '%s' failed (retrying)."
                                          % (self._log_tag, promise.msg_type))
                        with self._msg_queue_lock:
                            promise.clear_transaction_id()
                            self._msg_queue.insert(0, promise)
                        self._has_channel = False
                        break

                    except Exception:
                        logging.exception("[%s]: Sending message of type '%s' failed (giving up)."
                                          % (self._log_tag, promise.msg_type))
                        self._has_channel = False
                        promise.set_failed()
                        break

                    # Receive response.
                    try:
                        data = self._connection.recv(BUFSIZE).decode("ascii")
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
                                message = {"message": message["message"],
                                           "error": "%s message expected" % promise.msg_type}
                                self._connection.send(json.dumps(message))
                            except Exception:
                                self._has_channel = False

                            promise.set_failed()
                            continue

                        # Check if the received type (rts/cts/request/response) is the correct one.
                        if str(message["payload"]["type"]).lower() != "response":

                            logging.error("[%s]: Response expected for message of type '%s'."
                                          % (self._log_tag, promise.msg_type))

                            # Send error message back
                            try:
                                message = {"message": message["message"],
                                           "error": "response expected"}
                                self._connection.send(json.dumps(message))

                            except Exception:
                                self._has_channel = False

                            promise.set_failed()
                            continue

                        msg_result = str(message["payload"]["result"]).lower()
                        # Check if result of message was ok.
                        if msg_result == "ok":
                            logging.debug("[%s]: Received valid response for message of type '%s'."
                                          % (self._log_tag, promise.msg_type))
                            promise.set_success()

                        # Check if result of message was expired
                        # (too long in queue that other side does not process it).
                        elif msg_result == "expired":
                            logging.warning("[%s]: Other side said message of type '%s' is expired (too old)."
                                            % (self._log_tag, promise.msg_type))
                            promise.set_failed()

                        else:
                            logging.error("[%s]: Wrong result for message of type '%s' received: %s"
                                          % (self._log_tag, promise.msg_type, msg_result))
                            promise.set_failed()

                    except OSError:
                        logging.exception("[%s]: Receiving response for message of type '%s' failed (retrying)."
                                          % (self._log_tag, promise.msg_type))
                        with self._msg_queue_lock:
                            promise.clear_transaction_id()
                            self._msg_queue.insert(0, promise)
                        self._has_channel = False
                        break

                    except Exception:
                        logging.exception("[%s]: Receiving response for message of type '%s' failed (giving up)."
                                          % (self._log_tag, promise.msg_type))
                        self._has_channel = False
                        promise.set_failed()
                        break

            self._new_msg_event.clear()

    # noinspection PyBroadException
    def connect(self) -> bool:

        if not self._is_server:
            # Closes existing connection if we have one.
            try:
                self._connection.close()
            except Exception:
                pass

            try:
                self._connection.connect()

            except Exception:
                logging.exception("[%s]: Connecting to server failed." % self._log_tag)
                self._has_channel = False

                try:
                    self._connection.close()
                except Exception:
                    pass

                return False

        return True

    def exit(self):
        """
        Destroys the communication object by setting the exit flag to shut down the thread and closes connection.
        NOTE: communication object not usable afterwards.
        """
        self._exit_flag = True
        self.close()
        self._new_msg_event.set()

    # noinspection PyBroadException
    def close(self):
        """
        Closes the connection to the other side.
        """
        self._has_channel = False
        try:
            self._connection.close()
        except Exception:
            pass

    # noinspection PyBroadException
    def recv_raw(self) -> Optional[str]:
        """
        Raw receiving method that just plainly returns the received data.

        :return: Data received as string.
        """
        with self._connection_lock:
            try:
                data = self._connection.recv(BUFSIZE)
            except Exception:
                logging.exception("[%s]: Receiving failed." % self._log_tag)
                self._has_channel = False
                return None

            if not data:
                return None

        self._last_communication = int(time.time())
        return data.decode("ascii")

    # noinspection PyBroadException
    def recv_request(self) -> Optional[MsgRequest]:
        """
        Returns received request as string. Blocking until request is received or error occurs.
        Does not block the channel. Handles RTS/CTS messages with other side.

        :return: Data of the received request.
        """
        is_timeout_exception = False

        while True:

            # Only try to receive requests if we are connected.
            if not self._has_channel:
                return None

            # Exit if requested.
            if self._exit_flag:
                return None

            # Wait on a timeout exception to let other threads send data to the other side
            # (wait 0.5 seconds in between, because lock
            # are released in random order => other threads could be
            # unlucky and not be chosen => this has happened when
            # loglevel was not debug => hdd I/O has slowed this process down)
            if is_timeout_exception:
                time.sleep(0.5)

            with self._connection_lock:

                received_transaction_id = None
                try:
                    data = self._connection.recv(BUFSIZE, timeout=0.5).decode("ascii")
                    if not data:
                        self._has_channel = False
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
                        message = {"message": str(message["message"]),
                                   "payload": payload}
                        self._connection.send(json.dumps(message))

                        # After initiating transaction receive actual command.
                        num_read = 0
                        # NOTE: Use bytearray since bytes are immutable and
                        # for each += operator a new allocation is done.
                        data_raw = bytearray(message_size)
                        while num_read < message_size:
                            temp_data = self._connection.recv(message_size - len(data))
                            if not temp_data:
                                break

                            recv_length = len(temp_data)
                            data_raw[num_read:num_read+recv_length] = temp_data
                            num_read += recv_length

                        if num_read != message_size:
                            logging.error("[%s]: Received data incomplete. Closing connection." % self._log_tag)
                            self._has_channel = False
                            return None

                        data = data_raw.decode("ascii")

                    # if no RTS was received
                    # => other side does not stick to protocol
                    # => terminate session
                    else:
                        logging.error("[%s]: Did not receive RTS. Other side sent: %s"
                                      % (self._log_tag, data))
                        return None

                except RecvTimeout:
                    # Continue receiving.
                    is_timeout_exception = True
                    continue

                except Exception:
                    logging.exception("[%s]: Receiving failed." % self._log_tag)
                    self._has_channel = False
                    return None

                recv_message = {}
                try:
                    recv_message = json.loads(data)
                    # check if an error was received
                    if "error" in recv_message.keys():
                        logging.error("[%s]: Error received: '%s'."
                                      % (self._log_tag, recv_message["error"]))
                        self._has_channel = False
                        return None

                except Exception:
                    logging.exception("[%s]: Received data not valid: '%s'." % (self._log_tag, data))
                    self._has_channel = False
                    return None

                error_msg = MsgChecker.check_received_message(recv_message)
                if error_msg is not None:

                    request_type = "unknown"
                    if "message" in recv_message.keys() and type(recv_message["message"]) != str:
                        request_type = recv_message["message"]

                    # send error message back
                    try:
                        message = {"message": request_type,
                                   "error": error_msg}
                        self._connection.send(json.dumps(message))
                    except Exception:
                        pass

                    self._has_channel = False
                    return None

                request_type = recv_message["message"]
                logging.debug("[%s]: Received request message of type '%s'." % (self._log_tag, request_type))
                time_received = int(time.time())

                # Sending response.
                msg_request = None
                msg_time = recv_message["msgTime"]
                time_diff = int(time.time()) - msg_time
                # Consider time differences in both directions:
                # 1) if message is too old, it was either hold too long in the queue because of a disconnect or
                # the time of both hosts are too far out of sync
                # 2) if message lies in the future, the time of both hosts are too far out of sync
                if time_diff > self._msg_expiration or time_diff < (-1 * self._msg_expiration):

                    logging.warning("[%s]: Received request message of type '%s' is expired "
                                    % (self._log_tag, request_type)
                                    + "(%d seconds difference, allowed (+/-)%d seconds)."
                                    % (time_diff, self._msg_expiration))

                    logging.debug("[%s]: Sending 'expired' response message of type '%s'."
                                  % (self._log_tag, request_type))
                    try:
                        payload = {"type": "response",
                                   "result": "expired"}
                        message = {"message": request_type,
                                   "payload": payload}
                        self._connection.send(json.dumps(message))

                    except Exception:
                        logging.exception("[%s]: Sending 'expired' response message of type '%s' failed."
                                          % (self._log_tag, request_type))
                        self._has_channel = False
                        return None

                    msg_request = MsgRequest(recv_message,
                                             received_transaction_id,
                                             time_received,
                                             MsgState.EXPIRED)

                else:
                    logging.debug("[%s]: Sending 'ok' response message of type '%s'." % (self._log_tag, request_type))
                    try:
                        payload = {"type": "response",
                                   "result": "ok"}
                        message = {"message": request_type,
                                   "payload": payload}
                        self._connection.send(json.dumps(message))

                    except Exception:
                        logging.exception("[%s]: Sending 'ok' response message of type '%s' failed."
                                          % (self._log_tag, request_type))
                        self._has_channel = False
                        return None

                    msg_request = MsgRequest(recv_message,
                                             received_transaction_id,
                                             time_received,
                                             MsgState.OK)

                self._last_communication = int(time.time())
                return msg_request

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
    def send_raw(self,
                 msg: str):
        """
        Sends the given message to the other side. Does not guarantee that the message is received
        (kind of an UDP packet ;) ).

        :param msg: Message string to send.
        """
        with self._connection_lock:
            try:
                self._connection.send(msg)
                self._last_communication = int(time.time())

            except Exception:
                self._has_channel = False

    def set_connected(self):
        self._has_channel = True
