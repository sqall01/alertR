import threading
import time
import logging
from typing import List, Tuple
from lib.client.core import Connection, RecvTimeout
from lib.client.communication import Communication


class BasicConnection(Connection):

    def __init__(self):
        self._msg_list = []  # type: List[str]

    @property
    def msg_list(self):
        return list(self._msg_list)

    def connect(self):
        raise NotImplementedError("Abstract class.")

    def send(self,
             data: str):

        self._msg_list.append(data)

    def recv(self,
             buffsize: int,
             timeout: float = 20.0) -> str:
        raise NotImplementedError("Abstract class.")

    def close(self):
        raise NotImplementedError("Abstract class.")


class SimulatedConnection(Connection):

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

    def connect(self):
        raise NotImplementedError("Abstract class.")

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

    def close(self):
        raise NotImplementedError("Abstract class.")


def config_logging(loglevel):
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=loglevel)


def create_basic_communication() -> Communication:
    comm = Communication(BasicConnection())
    comm.set_connected()
    return comm


def create_simulated_communication() -> Tuple[Communication, Communication]:
    lock_send_client = threading.Lock()
    lock_send_server = threading.Lock()
    msg_queue_send_client = []
    msg_queue_send_server = []

    conn_client = SimulatedConnection(msg_queue_send_client,
                                      lock_send_client,
                                      msg_queue_send_server,
                                      lock_send_server,
                                      "client")

    conn_server = SimulatedConnection(msg_queue_send_server,
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
