import logging
import time
import threading
import json
from unittest import TestCase
from tests.client.core import config_logging, create_simulated_communication, msg_receiver
from lib.client.util import MsgBuilder


class TestCommunicationStress(TestCase):

    def test_single_communication(self):
        """
        Tests single request sending through the communication channel from the client to the server.
        """
        config_logging(logging.ERROR)

        comm_client, comm_server = create_simulated_communication()

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
        """
        Stress tests communication by letting client and server trying to send
        X messages to each other at the same time. Checks order of the send/received messages
        as well as not to take too long to send messages.
        """

        count = 30

        config_logging(logging.ERROR)

        comm_client, comm_server = create_simulated_communication()

        receiving_sync = threading.Event()
        receiving_sync.clear()

        msgs_recv_server = []
        kwargs = {"count": count,
                  "comm": comm_server,
                  "recv_msgs": msgs_recv_server,
                  "sync": receiving_sync}
        server_receiver = threading.Thread(target=msg_receiver,
                                           kwargs=kwargs,
                                           daemon=True)
        server_receiver.start()

        msgs_recv_client = []
        kwargs = {"count": count,
                  "comm": comm_client,
                  "recv_msgs": msgs_recv_client,
                  "sync": receiving_sync}
        client_receiver = threading.Thread(target=msg_receiver,
                                           kwargs=kwargs,
                                           daemon=True)
        client_receiver.start()

        start_timer = time.time()
        receiving_sync.set()

        # Send requests from client to server.
        requests_client = []
        for i in range(count):
            ping_msg = MsgBuilder.build_ping_msg()
            ping_dict = json.loads(ping_msg)
            # Insert bogus field to uniquely identify messages on the other side.
            ping_dict["test_msg_name"] = "client_" + str(i)
            ping_msg = json.dumps(ping_dict)
            promise = comm_client.send_request("ping", ping_msg)
            requests_client.append(promise)

        # Send requests from server to client.
        requests_server = []
        for i in range(count):
            ping_msg = MsgBuilder.build_ping_msg()
            ping_dict = json.loads(ping_msg)
            # Since the server is sending the message, swap clientTime with serverTime
            ping_dict["serverTime"] = ping_dict["clientTime"]
            del ping_dict["clientTime"]
            # Insert bogus field to uniquely identify messages on the other side.
            ping_dict["test_msg_name"] = "server_" + str(i)
            ping_msg = json.dumps(ping_dict)
            promise = comm_server.send_request("ping", ping_msg)
            requests_server.append(promise)

        # Give each message 5 seconds time
        # ("count" messages sent by client and "count" messages sent by server).
        for _ in range(count * 2 * 5):
            if client_receiver.isAlive():
                client_receiver.join(timeout=1.0)
            elif server_receiver.isAlive():
                server_receiver.join(timeout=1.0)
            else:
                break
        if client_receiver.isAlive():
            self.fail("Client timed out while receiving messages.")
        if server_receiver.isAlive():
            self.fail("Server timed out while receiving messages.")

        if len(requests_client) != len(msgs_recv_server):
            self.fail("Client requests differ from messages received by server.")

        if len(requests_server) != len(msgs_recv_client):
            self.fail("Server requests differ from messages received by client.")

        # Check requests send by the client.
        for i in range(len(requests_client)):
            promise = requests_client[i]
            send_msg = json.loads(promise.msg)
            recv_msg = msgs_recv_server[i]

            if promise.msg_type != recv_msg["message"]:
                self.fail("Message type from send and receive different (client -> server).")

            if send_msg["test_msg_name"] != recv_msg["test_msg_name"]:
                self.fail("Messages sent and received different or different order (client -> server).")

        # Check requests send by the server.
        for i in range(len(requests_client)):
            promise = requests_server[i]
            send_msg = json.loads(promise.msg)
            recv_msg = msgs_recv_client[i]

            if promise.msg_type != recv_msg["message"]:
                self.fail("Message type from send and receive different (server -> client).")

            if send_msg["test_msg_name"] != recv_msg["test_msg_name"]:
                self.fail("Messages sent and received different or different order (server -> client).")

        time_elapsed = time.time() - start_timer
        logging.info("Needed %.2f seconds to send/receive messages." % time_elapsed)
