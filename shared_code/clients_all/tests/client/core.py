import threading
import time
import logging
import json
from typing import List, Tuple
from lib.client.core import Connection, RecvTimeout
from lib.client.communication import Communication, MsgRequest


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
             timeout: float = 20.0) -> bytes:
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
        pass

    def send(self,
             data: str):

        logging.debug("[%s]: Sending: %s" % (self._tag, data))
        with self._send_lock:
            self._send_msg_queue.append(data)

    def recv(self,
             buffsize: int,
             timeout: float = 20.0) -> bytes:

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
                    return data.encode("ascii")
            time.sleep(0.2)

    def close(self):
        raise NotImplementedError("Abstract class.")


class SimulatedErrorConnection(SimulatedConnection):

    def __init__(self,
                 send_msg_queue: List[str],
                 send_lock: threading.Lock,
                 recv_msg_queue: List[str],
                 recv_lock: threading.Lock,
                 tag: str,
                 sim_error_rts: bool = False,
                 sim_error_cts: bool = False,
                 sim_error_request: bool = False,
                 sim_error_response: bool = False):

        super().__init__(send_msg_queue,
                         send_lock,
                         recv_msg_queue,
                         recv_lock,
                         tag)
        self.sim_error_rts = sim_error_rts
        self.sim_error_cts = sim_error_cts
        self.sim_error_request = sim_error_request
        self.sim_error_response = sim_error_response

    def connect(self):
        raise NotImplementedError("Abstract class.")

    def send(self,
             data: str):

        try:
            data_json = json.loads(data)
        except:
            raise ValueError("Unexpected data format")

        raise_error = False
        if self.sim_error_rts and data_json["payload"]["type"] == "rts":
            self.sim_error_rts = False
            raise_error = True

        elif self.sim_error_cts and data_json["payload"]["type"] == "cts":
            self.sim_error_cts = False
            raise_error = True

        elif self.sim_error_request and data_json["payload"]["type"] == "request":
            self.sim_error_request = False
            raise_error = True

        elif self.sim_error_response and data_json["payload"]["type"] == "response":
            self.sim_error_response = False
            raise_error = True

        if raise_error:
            super().send("SIM_EXCEPTION")
            raise OSError("Simulated connection error")

        super().send(data)

    def recv(self,
             buffsize: int,
             timeout: float = 20.0) -> bytes:

        data = super().recv(buffsize, timeout=timeout)
        if data == b"SIM_EXCEPTION":
            raise OSError("Simulated connection error")
        return data

    def close(self):
        raise NotImplementedError("Abstract class.")


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


def create_simulated_error_communication() -> Tuple[Communication, Communication]:
    lock_send_client = threading.Lock()
    lock_send_server = threading.Lock()
    msg_queue_send_client = []
    msg_queue_send_server = []

    conn_client = SimulatedErrorConnection(msg_queue_send_client,
                                           lock_send_client,
                                           msg_queue_send_server,
                                           lock_send_server,
                                           "client")

    conn_server = SimulatedErrorConnection(msg_queue_send_server,
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


def msg_receiver(**kwargs):

    count = kwargs["count"]  # type: int
    comm = kwargs["comm"]  # type: Communication
    msg_requests = kwargs["msg_requests"]  # type: List[MsgRequest]
    sync = kwargs["sync"]  # type: threading.Event

    # Wait until we are clear to receive messages.
    sync.wait()
    logging.debug("[%s]: Starting receiver loop." % comm._log_tag)

    for _ in range(count):

        while not comm.has_channel:
            time.sleep(0.5)

        msg_request = comm.recv_request()
        msg_requests.append(msg_request)
