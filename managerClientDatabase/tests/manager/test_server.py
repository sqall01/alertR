import logging
import os
import tempfile
import shutil
import socket
import json
import threading
from typing import List, Tuple
from unittest import TestCase
from tests.util import config_logging
from lib.client.communication import Promise
from lib.globalData.globalData import GlobalData
from lib.manager.server import ThreadedUnixStreamServer, LocalServerSession


class MockServerCommunication:

    def __init__(self):
        self._options = list()

    def send_option(self,
                    option_type: str,
                    option_value: int,
                    option_delay: int = 0) -> Promise:
        self._options.append((option_type, option_value, option_delay))
        return Promise("option", "mock_msg")

    def get_options(self) -> List[Tuple[str, int, int]]:
        return self._options


class TestManagerServer(TestCase):

    def _create_server(self) -> Tuple[ThreadedUnixStreamServer, GlobalData]:
        config_logging(logging.ERROR)

        global_data = GlobalData()

        dir = tempfile.mkdtemp()
        global_data.unixSocketFile = os.path.join(dir, "test_socket")

        global_data.serverComm = MockServerCommunication()

        server = ThreadedUnixStreamServer(global_data, global_data.unixSocketFile, LocalServerSession)

        server_thread = threading.Thread(target=server.serve_forever,
                                         daemon=True)
        server_thread.start()

        self.addCleanup(self._destroy_server, server, global_data)

        return server, global_data

    def _destroy_server(self, server: ThreadedUnixStreamServer, global_data: GlobalData):
        try:
            server.server_close()
        except:
            pass

        try:
            shutil.rmtree(os.path.dirname(global_data.unixSocketFile))
        except:
            pass

    def test_send_option_profile(self):
        """
        Tests sending an option message to change the system profile.
        """
        num = 5

        server, global_data = self._create_server()

        for i in range(num):

            value = i
            delay = i

            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect(global_data.unixSocketFile)

            except Exception as e:
                self.fail(str(e))

            send_msg = {"message": "option",
                        "payload": {"optionType": "profile",
                                    "value": value,
                                    "timeDelay": delay
                        }}

            sock.send(json.dumps(send_msg).encode('ascii'))

            data = sock.recv(1024)
            recv_msg = json.loads(data.decode("ascii"))

            self.assertEqual(recv_msg["message"], "option")
            self.assertEqual(recv_msg["payload"]["type"], "response")
            self.assertEqual(recv_msg["payload"]["result"], "ok")

            options = global_data.serverComm.get_options()
            self.assertEqual(len(options), i+1)
            self.assertEqual(options[i][0], "profile")
            self.assertEqual(options[i][1], value)
            self.assertEqual(options[i][2], delay)

            sock.close()

    def test_send_option_not_profile(self):
        """
        Tests sending an option message that is not a system profile change.
        """

        server, global_data = self._create_server()

        value = 1
        delay = 2

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(global_data.unixSocketFile)

        except Exception as e:
            self.fail(str(e))

        send_msg = {"message": "option",
                    "payload": {"optionType": "not_profile",
                                "value": value,
                                "timeDelay": delay
                    }}

        sock.send(json.dumps(send_msg).encode('ascii'))

        data = sock.recv(1024)
        recv_msg = json.loads(data.decode("ascii"))

        self.assertEqual(recv_msg["message"], "option")
        self.assertTrue("error" in recv_msg.keys())

        options = global_data.serverComm.get_options()
        self.assertEqual(len(options), 0)

        sock.close()

    def test_send_option_missing_value(self):
        """
        Tests sending an option message that misses a value attribute.
        """

        server, global_data = self._create_server()

        delay = 2

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(global_data.unixSocketFile)

        except Exception as e:
            self.fail(str(e))

        send_msg = {"message": "option",
                    "payload": {"optionType": "profile",
                                "timeDelay": delay
                    }}

        sock.send(json.dumps(send_msg).encode('ascii'))

        data = sock.recv(1024)
        recv_msg = json.loads(data.decode("ascii"))

        self.assertEqual(recv_msg["message"], "option")
        self.assertTrue("error" in recv_msg.keys())

        options = global_data.serverComm.get_options()
        self.assertEqual(len(options), 0)

        sock.close()

    def test_send_option_missing_delay(self):
        """
        Tests sending an option message that misses a timeDelay attribute.
        """

        server, global_data = self._create_server()

        value = 1

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(global_data.unixSocketFile)

        except Exception as e:
            self.fail(str(e))

        send_msg = {"message": "option",
                    "payload": {"optionType": "profile",
                                "value": value
                    }}

        sock.send(json.dumps(send_msg).encode('ascii'))

        data = sock.recv(1024)
        recv_msg = json.loads(data.decode("ascii"))

        self.assertEqual(recv_msg["message"], "option")
        self.assertTrue("error" in recv_msg.keys())

        options = global_data.serverComm.get_options()
        self.assertEqual(len(options), 0)

        sock.close()

    def test_send_invalid_message(self):
        """
        Tests sending an invalid message.
        """

        server, global_data = self._create_server()

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(global_data.unixSocketFile)

        except Exception as e:
            self.fail(str(e))

        sock.send("invalid_msg".encode("ascii"))

        data = sock.recv(1024)
        recv_msg = json.loads(data.decode("ascii"))

        self.assertEqual(recv_msg["message"], "unknown")
        self.assertTrue("error" in recv_msg.keys())

        options = global_data.serverComm.get_options()
        self.assertEqual(len(options), 0)

        sock.close()
