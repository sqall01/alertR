#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import logging
import requests
import hashlib
from typing import Tuple, Optional, Dict
from .gps import _GPSSensor


class ServerError(BaseException):
    pass


class ChasRErrorCodes:
    NO_ERROR = 0
    DATABASE_ERROR = 1
    AUTH_ERROR = 2
    ILLEGAL_MSG_ERROR = 3
    SESSION_EXPIRED = 4
    ACL_ERROR = 5


class ChasRSensor(_GPSSensor):
    """
    Represents one ChasR GPS device.
    """
    def __init__(self):
        super().__init__()

        # used for logging
        self._log_tag = os.path.basename(__file__)

        self._timeout = 30.0
        self._url = "https://alertr.de/chasr/get.php"
        self._key = None  # type: Optional[bytes]

        # Name of the device to fetch GPS data for.
        self.device = None  # type: Optional[str]

        self.username = None  # type: Optional[str]
        self.password = None  # type: Optional[str]

        self.secret = None  # type: Optional[str]

    def _check_hmac(self, data: Dict[str, str]) -> bool:
        raise NotImplementedError("TODO")

    def _decrypt_data(self, data: Dict[str, str]) -> Optional[Dict[str, str]]:
        raise NotImplementedError("TODO")

    def _get_data(self) -> Tuple[float, float, int]:

        logging.debug("[%s] Fetching data for device: %s" % (self._log_tag, self.device))

        # Prepare POST data.
        payload = {"user": self.username,
                   "password": self.password}

        # Submit data.
        request_result = None
        try:
            r = requests.post(self._url + "?mode=last&device=%s" % self.device,
                              verify=True,
                              data=payload,
                              timeout=self._timeout)
            request_result = r.json()

        except Exception as e:
            logging.exception("[%s] Failed to fetch GPS data."
                              % self._log_tag)
            raise

        # Decrypt and authenticate data if fetching was successful.
        if request_result["code"] == ChasRErrorCodes.NO_ERROR:

            decrypted_data = self._decrypt_data(request_result["data"][0])
            if decrypted_data is None:
                logging.error("[%s] Unable to decrypt GPS data.")
                raise ValueError("Decryption Error")

            if not self._check_hmac(decrypted_data):
                logging.error("[%s] Unable to authenticate GPS data.")
                raise ValueError("Unauthenticated Data")

            return float(decrypted_data["lat"]), float(decrypted_data["lon"]), int(decrypted_data["utctime"])

        # Server has a database error.
        elif request_result["code"] == ChasRErrorCodes.DATABASE_ERROR:
            logging.error("[%s] Failed to fetch GPS data. Server has a database error." % self._log_tag)
            if "msg" in request_result.keys():
                logging.error("[%s] Server message: %s" % (self._log_tag, request_result["msg"]))
            raise ServerError("Server Database Error")

        # Authentication error.
        elif request_result["code"] == ChasRErrorCodes.AUTH_ERROR:
            logging.error("[%s] Failed to fetch GPS data. Authentication failed." % self._log_tag)
            if "msg" in request_result.keys():
                logging.error("[%s] Server message: %s" % (self._log_tag, request_result["msg"]))
            raise ServerError("Authentication Error")

        # Illegal message error.
        elif request_result["code"] == ChasRErrorCodes.ILLEGAL_MSG_ERROR:
            logging.error("[%s] Failed to fetch GPS data. Message illegal." % self._log_tag)
            if "msg" in request_result.keys():
                logging.error("[%s] Server message: %s" % (self._log_tag, request_result["msg"]))
            raise ServerError("Illegal Message Error")

        # Session expired error.
        elif request_result["code"] == ChasRErrorCodes.SESSION_EXPIRED:
            logging.error("[%s] Failed to fetch GPS data. Session expired." % self._log_tag)
            if "msg" in request_result.keys():
                logging.error("[%s] Server message: %s" % (self._log_tag, request_result["msg"]))
            raise ServerError("Session Expired")

        # Request not allowed (e.g., no device slots left).
        elif request_result["code"] == ChasRErrorCodes.ACL_ERROR:
            logging.error("[%s] Failed to fetch GPS data. ACL error." % self._log_tag)
            if "msg" in request_result.keys():
                logging.error("[%s] Server message: %s" % (self._log_tag, request_result["msg"]))
            raise ServerError("ACL Error")

        # Unknown error.
        else:
            logging.error("[%s] Failed to fetch GPS data. Unknown error: %d." % (self._log_tag, request_result["code"]))
            if "msg" in request_result.keys():
                logging.error("[%s] Server message: %s" % (self._log_tag, request_result["msg"]))
            raise ServerError("Unknown Error")

    def initialize(self) -> bool:
        if not super().initialize():
            return False

        # Create decryption key from the secret.
        sha256 = hashlib.sha256()
        sha256.update(self.secret.encode("utf-8"))
        self._key = sha256.digest()
