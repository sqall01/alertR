import logging
import time
import threading
from typing import List, Tuple
from unittest import TestCase
from lib.client.core import Connection, RecvTimeout
from lib.client.communication import Communication
from lib.client.util import MsgBuilder


class SimConnection(Connection):

    def __init__(self,
                 send_msg_queue: List[str],
                 send_lock: threading.Lock,
                 recv_msg_queue: List[str],
                 recv_lock: threading.Lock,
                 tag: str):

        self._send_msg_queue = send_msg_queue
        self._send_lock = send_lock
        self._recv_msg_queue = recv_msg_queue
        self._recv_lock = recv_lock
        self._tag = tag

    def send(self,
             data: str):

        logging.debug("[%s]: Sending: %s" % (self._tag, data))
        with self._send_lock:
            self._send_msg_queue.append(data)

    def recv(self,
             buffsize: int,
             timeout: float = 20.0) -> str:

        logging.debug("[%s]: Start receiving." % self._tag)
        start_time = time.time()
        while True:
            # Check if our received timed out.
            if (time.time() - start_time) > timeout:
                logging.debug("[%s]: Timeout while receiving." % self._tag)
                raise RecvTimeout

            with self._recv_lock:
                if self._recv_msg_queue:
                    data = self._recv_msg_queue.pop(0)
                    logging.debug("[%s]: Received : %s" % (self._tag, data))
                    return data
            time.sleep(0.2)


class TestCommunicationBasic(TestCase):

    def _config_logging(self):
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%m/%d/%Y %H:%M:%S',
                            level=logging.ERROR)

    def _create_communication(self) -> Tuple[Communication, Communication]:
        lock_send_client = threading.Lock()
        lock_send_server = threading.Lock()
        msg_queue_send_client = []
        msg_queue_send_server = []

        conn_client = SimConnection(msg_queue_send_client,
                                    lock_send_client,
                                    msg_queue_send_server,
                                    lock_send_server,
                                    "client")

        conn_server = SimConnection(msg_queue_send_server,
                                    lock_send_server,
                                    msg_queue_send_client,
                                    lock_send_client,
                                    "server")

        comm_client = Communication(conn_client)
        comm_server = Communication(conn_server, is_server=True)

        comm_client._log_tag = "client"
        comm_server._log_tag = "server"

        comm_client.set_connected()
        comm_server.set_connected()

        return comm_client, comm_server

    def test_single_communication(self):

        self._config_logging()

        comm_client, comm_server = self._create_communication()

        ping_msg = MsgBuilder.build_ping_msg()
        promise = comm_client.send_request("ping", ping_msg)

        recv_msg = comm_server.recv_request()
        if recv_msg is None:
            self.fail("Receiving message failed.")

        if "ping" != recv_msg["message"]:
            self.fail("Expected 'ping' message.")

        if not promise.is_finished(timeout=5.0):
            self.fail("Expected message to be sent.")

        if not promise.was_successful():
            self.fail("Sending message was not successful.")
