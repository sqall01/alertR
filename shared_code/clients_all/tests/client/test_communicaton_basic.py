import logging
import threading
import time
from unittest import TestCase
from lib.client.util import MsgBuilder
from tests.client.core import config_logging, create_basic_communication, create_simulated_error_communication, \
                              msg_receiver


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

    def test_send_request_rts_error(self):

        config_logging(logging.ERROR)

        comm_client, comm_server = create_simulated_error_communication()

        # Inject in first "rts" an error.
        comm_client._connection.sim_error_rts = True

        receiving_sync = threading.Event()
        receiving_sync.clear()

        msgs_recv_server = []
        kwargs = {"count": 2,  # we receive 2 messages: None because of the error and the ping
                  "comm": comm_server,
                  "recv_msgs": msgs_recv_server,
                  "sync": receiving_sync}
        server_receiver = threading.Thread(target=msg_receiver,
                                           kwargs=kwargs,
                                           daemon=True)
        server_receiver.start()

        start_timer = time.time()
        receiving_sync.set()

        ping_msg = MsgBuilder.build_ping_msg()
        promise = comm_client.send_request("ping", ping_msg)

        # Give message 5 seconds time.
        reconnect_client_ctr = 0
        reconnect_server_ctr = 0
        for _ in range(5):
            if server_receiver.isAlive():

                # Re-connect channel if it is down (since we simulate an error we have to re-connect).
                if not comm_client.has_channel:
                    comm_client.set_connected()
                    reconnect_client_ctr += 1

                # Re-connect channel if it is down (since we simulate an error we have to re-connect).
                if not comm_server.has_channel:
                    comm_server.set_connected()
                    reconnect_server_ctr += 1

                server_receiver.join(timeout=1.0)

            else:
                break

        if server_receiver.isAlive():
            self.fail("Server timed out while receiving messages.")

        if reconnect_client_ctr > 1:
            self.fail("Client had to re-connect more than once to server.")

        if reconnect_server_ctr > 1:
            self.fail("Server had to re-connect more than once with client.")

        if not msgs_recv_server:
            self.fail("Received no message.")

        if len(msgs_recv_server) != 2:
            self.fail("Expected two messages.")

        if msgs_recv_server[0] is not None:
            self.fail("Expected None as first received message.")

        recv_msg = msgs_recv_server[1]
        if recv_msg is None:
            self.fail("Receiving message failed.")

        if "ping" != recv_msg["message"]:
            self.fail("Expected 'ping' message.")

        if not promise.is_finished(timeout=5.0):
            self.fail("Expected message to be sent.")

        if not promise.was_successful():
            self.fail("Sending message was not successful.")

        time_elapsed = time.time() - start_timer
        logging.info("Needed %.2f seconds to send/receive messages." % time_elapsed)

    def test_send_request_cts_error(self):

        config_logging(logging.ERROR)

        comm_client, comm_server = create_simulated_error_communication()

        # Inject in first "cts" an error.
        comm_server._connection.sim_error_cts = True

        receiving_sync = threading.Event()
        receiving_sync.clear()

        msgs_recv_server = []
        kwargs = {"count": 2,  # we receive 2 messages: None because of the error and the ping
                  "comm": comm_server,
                  "recv_msgs": msgs_recv_server,
                  "sync": receiving_sync}
        server_receiver = threading.Thread(target=msg_receiver,
                                           kwargs=kwargs,
                                           daemon=True)
        server_receiver.start()

        start_timer = time.time()
        receiving_sync.set()

        ping_msg = MsgBuilder.build_ping_msg()
        promise = comm_client.send_request("ping", ping_msg)

        # Give message 5 seconds time.
        reconnect_client_ctr = 0
        reconnect_server_ctr = 0
        for _ in range(5):
            if server_receiver.isAlive():

                # Re-connect channel if it is down (since we simulate an error we have to re-connect).
                if not comm_client.has_channel:
                    comm_client.set_connected()
                    reconnect_client_ctr += 1

                # Re-connect channel if it is down (since we simulate an error we have to re-connect).
                if not comm_server.has_channel:
                    comm_server.set_connected()
                    reconnect_server_ctr += 1

                server_receiver.join(timeout=1.0)

            else:
                break

        if server_receiver.isAlive():
            self.fail("Server timed out while receiving messages.")

        if reconnect_client_ctr > 1:
            self.fail("Client had to re-connect more than once to server.")

        if reconnect_server_ctr > 1:
            self.fail("Server had to re-connect more than once with client.")

        if not msgs_recv_server:
            self.fail("Received no message.")

        if len(msgs_recv_server) != 2:
            self.fail("Expected two messages.")

        if msgs_recv_server[0] is not None:
            self.fail("Expected None as first received message.")

        recv_msg = msgs_recv_server[1]
        if recv_msg is None:
            self.fail("Receiving message failed.")

        if "ping" != recv_msg["message"]:
            self.fail("Expected 'ping' message.")

        if not promise.is_finished(timeout=5.0):
            self.fail("Expected message to be sent.")

        if not promise.was_successful():
            self.fail("Sending message was not successful.")

        time_elapsed = time.time() - start_timer
        logging.info("Needed %.2f seconds to send/receive messages." % time_elapsed)
