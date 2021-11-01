#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import socket
import ssl
from typing import Optional

BUFSIZE = 4096


class RecvTimeout(Exception):
    pass


class Connection:

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
        raise NotImplementedError("Abstract class.")

    def recv(self,
             buffsize: int,
             timeout: Optional[float] = 20.0) -> bytes:
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


class Client(Connection):

    def __init__(self,
                 host: str,
                 port: int,
                 server_ca_file: Optional[str],
                 client_cert_file: Optional[str],
                 client_key_file: Optional[str]):
        self._host = host
        self._port = port
        self._server_ca_file = server_ca_file
        self._client_cert_file = client_cert_file
        self._client_key_file = client_key_file
        self._socket = None  # type: Optional[socket.socket]

    def connect(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Check if TLS is enabled.
        if self._server_ca_file is not None:
            # Check if a client certificate is required.
            if self._client_cert_file is None or self._client_key_file is None:
                self._socket = ssl.wrap_socket(self._socket,
                                               ca_certs=self._server_ca_file,
                                               cert_reqs=ssl.CERT_REQUIRED)
            else:
                self._socket = ssl.wrap_socket(self._socket,
                                               ca_certs=self._server_ca_file,
                                               cert_reqs=ssl.CERT_REQUIRED,
                                               certfile=self._client_cert_file,
                                               keyfile=self._client_key_file)

        self._socket.connect((self._host, self._port))

    def send(self,
             data: str):
        self._socket.send(data.encode('ascii'))

    def recv(self,
             buffsize: int,
             timeout: Optional[float] = 20.0) -> bytes:
        self._socket.settimeout(timeout)

        try:
            data = self._socket.recv(buffsize)

        except socket.timeout:
            raise RecvTimeout

        self._socket.settimeout(None)
        return data

    def close(self):
        if self._socket is not None:
            self._socket.close()
