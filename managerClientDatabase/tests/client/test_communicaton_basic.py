from typing import List
from unittest import TestCase
from lib.client.core import Connection, RecvTimeout
from lib.client.communication import Communication


class ClientTester(Connection):

    def __init__(self):
        self._msg_list = []  # type: List[str]

    @property
    def msg_list(self):
        return list(self._msg_list)

    def connect(self):
        """
        Connects to the other side.
        """
        raise NotImplementedError("Abstract class.")

    def send(self,
             data: str):
        """
        Sends data to the other side.
        :param data: data to send as string
        """
        self._msg_list.append(data)

    def recv(self,
             buffsize: int,
             timeout: float = 20.0) -> str:
        """
        Receives data on the connection.
        :param buffsize: how much data at max is received
        :param timeout: timeout of the receiving call
        """
        raise NotImplementedError("Abstract class.")

    def close(self):
        """
        Closes connection.
        """
        raise NotImplementedError("Abstract class.")


class TestCommunicationBasic(TestCase):

    def _create_communication(self) -> Communication:
        comm = Communication(ClientTester())
        comm.set_connected()
        return comm

    def test_send_raw(self):
        test_msgs = ["test msg1", "test msg2", "test msg3"]
        comm = self._create_communication()

        for test_msg in test_msgs:
            comm.send_raw(test_msg)

            if not comm.has_channel:
                self.fail("Communication does not have connected channel.")

        recv_msgs = comm._connection.msg_list

        if len(recv_msgs) != len(test_msgs):
            self.fail("Number of send and received messages differ.")

        for i in range(len(test_msgs)):
            if recv_msgs[i] != test_msgs[i]:
                self.fail("Received message '%s' but expected message '%s'." % (recv_msgs[i], test_msgs[i]))
