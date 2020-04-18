import logging
import time
import threading
from typing import List, Tuple, Any, Dict
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
                    logging.debug("[%s]: Received: %s" % (self._tag, data))
                    return data
            time.sleep(0.2)


class TestCommunicationBasic(TestCase):

    def _config_logging(self):
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%m/%d/%Y %H:%M:%S',
                            level=logging.DEBUG)

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

    def _msg_receiver(self,
                      **kwargs):

        count = kwargs["count"]  # type: int
        comm = kwargs["comm"]  # type: Communication
        recv_msgs = kwargs["recv_msgs"]  # type: List[Dict[str, Any]]
        sync = kwargs["sync"]  # type: threading.Event

        # Wait until we are clear to receive messages.
        sync.wait()
        logging.debug("[%s]: Starting receiver loop." % comm._log_tag)

        for _ in range(count):
            recv_msg = comm.recv_request()
            recv_msgs.append(recv_msg)

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

    def test_stress_communication(self):

        count = 1

        self._config_logging()

        comm_client, comm_server = self._create_communication()

        receiving_sync = threading.Event()
        receiving_sync.clear()

        msgs_recv_server = []
        kwargs = {"count": count,
                  "comm": comm_server,
                  "recv_msgs": msgs_recv_server,
                  "sync": receiving_sync}
        server_receiver = threading.Thread(target=self._msg_receiver,
                                           kwargs=kwargs,
                                           daemon=True)
        server_receiver.start()

        msgs_recv_client = []
        kwargs = {"count": count,
                  "comm": comm_client,
                  "recv_msgs": msgs_recv_client,
                  "sync": receiving_sync}
        client_receiver = threading.Thread(target=self._msg_receiver,
                                           kwargs=kwargs,
                                           daemon=True)
        client_receiver.start()

        receiving_sync.set()

        # Send requests from client to server.
        requests_client = []
        for _ in range(count):
            ping_msg = MsgBuilder.build_ping_msg()
            promise = comm_client.send_request("ping", ping_msg)
            requests_client.append(promise)

        # Send requests from server to client.
        requests_server = []
        for _ in range(count):
            ping_msg = MsgBuilder.build_ping_msg()
            ping_msg = ping_msg.replace("clientTime", "serverTime")
            promise = comm_server.send_request("ping", ping_msg)
            requests_server.append(promise)

        # Give each received message 2 seconds time.
        client_receiver.join(timeout=(count * 10.0)) # TODO
        if client_receiver.isAlive():
            self.fail("Client timed out while receiving messages.")

        # Give each received message 2 seconds time.
        server_receiver.join(timeout=(count * 10.0)) # TODO
        if server_receiver.isAlive():
            self.fail("Server timed out while receiving messages.")

        if len(requests_client) != len(msgs_recv_server):
            self.fail("Client requests differ from messages received by server.")

        if len(requests_server) != len(msgs_recv_client):
            self.fail("Server requests differ from messages received by client.")

        for i in range(len(requests_client)):
            promise = requests_client[i]
            recv_msg = msgs_recv_server[i]

            if promise.msg_type != recv_msg["message"]:
                self.fail("Message type from send and receive different.")

            # TODO check if correct order

        print("HIER")