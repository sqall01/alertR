#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import socket
import ssl

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


class Client(Connection):

    def __init__(self,
                 host: str,
                 port: int,
                 serverCAFile: str,
                 clientCertFile: str,
                 clientKeyFile: str):
        self.host = host
        self.port = port
        self.serverCAFile = serverCAFile
        self.clientCertFile = clientCertFile
        self.clientKeyFile = clientKeyFile
        self.socket = None
        self.sslSocket = None

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # check if a client certificate is required
        if self.clientCertFile is None or self.clientKeyFile is None:
            self.sslSocket = ssl.wrap_socket(self.socket,
                                             ca_certs=self.serverCAFile,
                                             cert_reqs=ssl.CERT_REQUIRED)
        else:
            self.sslSocket = ssl.wrap_socket(self.socket,
                                             ca_certs=self.serverCAFile,
                                             cert_reqs=ssl.CERT_REQUIRED,
                                             certfile=self.clientCertFile,
                                             keyfile=self.clientKeyFile)

        self.sslSocket.connect((self.host, self.port))

    def send(self,
             data: str):
        self.sslSocket.send(data.encode('ascii'))

    def recv(self,
             buffsize: int,
             timeout: float = 20.0) -> str:
        self.sslSocket.settimeout(timeout)

        try:
            data = self.sslSocket.recv(buffsize)

        except socket.timeout:
            raise RecvTimeout

        self.sslSocket.settimeout(None)
        return data.decode("ascii")

    def close(self):
        # closing SSLSocket will also close the underlying socket
        self.sslSocket.close()
