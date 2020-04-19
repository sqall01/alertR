from unittest import TestCase
from tests.client.core import create_basic_communication


class TestCommunicationBasic(TestCase):

    def test_send_raw(self):
        test_msgs = ["test msg1", "test msg2", "test msg3"]
        comm = create_basic_communication()

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
