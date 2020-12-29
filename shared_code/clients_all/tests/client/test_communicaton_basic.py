import logging
import json
import threading
import time
from unittest import TestCase
from lib.client.util import MsgBuilder
from lib.client.communication import MsgState
from tests.util import config_logging
from tests.client.core import create_basic_communication, create_simulated_error_communication, \
                              msg_receiver, create_simulated_communication


class TestCommunicationBasic(TestCase):

    def test_send_raw(self):
        """
        Tests the raw send function of the communication.
        """

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

    def test_single_communication(self):
        """
        Tests single request sending through the communication channel from the client to the server.
        """
        config_logging(logging.CRITICAL)

        comm_client, comm_server = create_simulated_communication()

        ping_msg = MsgBuilder.build_ping_msg()
        promise = comm_client.send_request("ping", ping_msg)

        msg_request = comm_server.recv_request()
        if msg_request is None:
            self.fail("Receiving message failed.")

        self.assertEqual(msg_request.state, MsgState.OK)

        if "ping" != msg_request.msg_dict["message"]:
            self.fail("Expected 'ping' message.")

        if not promise.is_finished(timeout=5.0):
            self.fail("Expected message to be sent.")

        if not promise.was_successful():
            self.fail("Sending message was not successful.")

    def test_send_request_rts_error(self):
        """
        Tests communication error handling by letting the client send a ping request to the server
        and failing the rts message part the first time.
        """

        config_logging(logging.CRITICAL)

        comm_client, comm_server = create_simulated_error_communication()

        # Inject in first "rts" an error.
        comm_client._connection.sim_error_rts = True

        receiving_sync = threading.Event()
        receiving_sync.clear()

        msg_requests_server = []
        kwargs = {"count": 2,  # we receive 2 messages: None because of the error and the ping
                  "comm": comm_server,
                  "msg_requests": msg_requests_server,
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

        if not msg_requests_server:
            self.fail("Received no message.")

        if len(msg_requests_server) != 2:
            self.fail("Expected two messages.")

        if msg_requests_server[0] is not None:
            self.fail("Expected None as first received message.")

        msg_request = msg_requests_server[1]
        if msg_request is None:
            self.fail("Receiving message failed.")

        self.assertEqual(msg_request.state, MsgState.OK)

        if "ping" != msg_request.msg_dict["message"]:
            self.fail("Expected 'ping' message.")

        if not promise.is_finished(timeout=5.0):
            self.fail("Expected message to be sent.")

        if not promise.was_successful():
            self.fail("Sending message was not successful.")

        time_elapsed = time.time() - start_timer
        logging.info("Needed %.2f seconds to send/receive messages." % time_elapsed)

    def test_send_request_cts_error(self):
        """
        Tests communication error handling by letting the client send a ping request to the server
        and failing the cts message part the first time.
        """

        config_logging(logging.CRITICAL)

        comm_client, comm_server = create_simulated_error_communication()

        # Inject in first "cts" an error.
        comm_server._connection.sim_error_cts = True

        receiving_sync = threading.Event()
        receiving_sync.clear()

        msg_requests_server = []
        kwargs = {"count": 2,  # we receive 2 messages: None because of the error and the ping
                  "comm": comm_server,
                  "msg_requests": msg_requests_server,
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

        if not msg_requests_server:
            self.fail("Received no message.")

        if len(msg_requests_server) != 2:
            self.fail("Expected two messages.")

        if msg_requests_server[0] is not None:
            self.fail("Expected None as first received message.")

        msg_request = msg_requests_server[1]
        if msg_request is None:
            self.fail("Receiving message failed.")

        self.assertEqual(msg_request.state, MsgState.OK)

        if "ping" != msg_request.msg_dict["message"]:
            self.fail("Expected 'ping' message.")

        if not promise.is_finished(timeout=5.0):
            self.fail("Expected message to be sent.")

        if not promise.was_successful():
            self.fail("Sending message was not successful.")

        time_elapsed = time.time() - start_timer
        logging.info("Needed %.2f seconds to send/receive messages." % time_elapsed)

    def test_send_request_request_error(self):
        """
        Tests communication error handling by letting the client send a ping request to the server
        and failing the request message part the first time.
        """

        config_logging(logging.CRITICAL)

        comm_client, comm_server = create_simulated_error_communication()

        # Inject in first "request" an error.
        comm_client._connection.sim_error_request = True

        receiving_sync = threading.Event()
        receiving_sync.clear()

        msg_requests_server = []
        kwargs = {"count": 2,  # we receive 2 messages: None because of the error and the ping
                  "comm": comm_server,
                  "msg_requests": msg_requests_server,
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

        if not msg_requests_server:
            self.fail("Received no message.")

        if len(msg_requests_server) != 2:
            self.fail("Expected two messages.")

        if msg_requests_server[0] is not None:
            self.fail("Expected None as first received message.")

        msg_request = msg_requests_server[1]
        if msg_request is None:
            self.fail("Receiving message failed.")

        self.assertEqual(msg_request.state, MsgState.OK)

        if "ping" != msg_request.msg_dict["message"]:
            self.fail("Expected 'ping' message.")

        if not promise.is_finished(timeout=5.0):
            self.fail("Expected message to be sent.")

        if not promise.was_successful():
            self.fail("Sending message was not successful.")

        time_elapsed = time.time() - start_timer
        logging.info("Needed %.2f seconds to send/receive messages." % time_elapsed)

    def test_send_request_response_error(self):
        """
        Tests communication error handling by letting the client send a ping request to the server
        and failing the response message part the first time.
        """

        config_logging(logging.CRITICAL)

        comm_client, comm_server = create_simulated_error_communication()

        # Inject in first "response" an error.
        comm_server._connection.sim_error_response = True

        receiving_sync = threading.Event()
        receiving_sync.clear()

        msg_requests_server = []
        kwargs = {"count": 2,  # we receive 2 messages: None because of the error and the ping
                  "comm": comm_server,
                  "msg_requests": msg_requests_server,
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

        if not msg_requests_server:
            self.fail("Received no message.")

        if len(msg_requests_server) != 2:
            self.fail("Expected two messages.")

        if msg_requests_server[0] is not None:
            self.fail("Expected None as first received message.")

        msg_request = msg_requests_server[1]
        if msg_request is None:
            self.fail("Receiving message failed.")

        self.assertEqual(msg_request.state, MsgState.OK)

        if "ping" != msg_request.msg_dict["message"]:
            self.fail("Expected 'ping' message.")

        if not promise.is_finished(timeout=5.0):
            self.fail("Expected message to be sent.")

        if not promise.was_successful():
            self.fail("Sending message was not successful.")

        time_elapsed = time.time() - start_timer
        logging.info("Needed %.2f seconds to send/receive messages." % time_elapsed)

    def test_recv_too_old(self):
        """
        Tests communication expired handling by letting the client send a ping request to the server
        which is too old.
        """
        config_logging(logging.WARNING)

        comm_client, comm_server = create_simulated_communication()

        ping_msg = MsgBuilder.build_ping_msg()
        json_msg = json.loads(ping_msg)
        json_msg["msgTime"] = int(time.time()) - (comm_server._msg_expiration + 1)
        promise = comm_client.send_request("ping", json.dumps(json_msg))

        msg_request = comm_server.recv_request()
        self.assertIsNotNone(msg_request)
        self.assertEqual(msg_request.state, MsgState.EXPIRED)
        self.assertEqual(msg_request.msg_dict["message"], "ping")
        self.assertTrue(promise.is_finished(timeout=5.0))
        self.assertFalse(promise.was_successful())

    def test_recv_too_young(self):
        """
        Tests communication expired handling by letting the client send a ping request to the server
        which is too young.
        """
        config_logging(logging.WARNING)

        comm_client, comm_server = create_simulated_communication()

        ping_msg = MsgBuilder.build_ping_msg()
        json_msg = json.loads(ping_msg)
        json_msg["msgTime"] = int(time.time()) + comm_server._msg_expiration + 5
        promise = comm_client.send_request("ping", json.dumps(json_msg))

        msg_request = comm_server.recv_request()
        self.assertIsNotNone(msg_request)
        self.assertEqual(msg_request.state, MsgState.EXPIRED)
        self.assertEqual(msg_request.msg_dict["message"], "ping")
        self.assertTrue(promise.is_finished(timeout=5.0))
        self.assertFalse(promise.was_successful())
