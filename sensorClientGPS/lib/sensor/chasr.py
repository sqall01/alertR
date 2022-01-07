#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.
import binascii
import os
import logging
import requests
import hashlib
import time
from typing import Optional, Dict, Any
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
from Crypto.Util import Padding
from .gps import _GPSSensor
from ..globalData.sensorObjects import SensorDataGPS


class ServerError(Exception):
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

        self._last_position = None  # type: Optional[SensorDataGPS]

    def _check_hmac(self, data: Dict[str, str]) -> bool:
        hmac = HMAC.new(self._key, digestmod=SHA256)
        hmac.update(data["device_name"].encode("utf-8"))
        hmac.update(str(data["utctime"]).encode("utf-8"))
        hmac.update(data["lat"].encode("utf-8"))
        hmac.update(data["lon"].encode("utf-8"))
        hmac.update(data["alt"].encode("utf-8"))
        hmac.update(data["speed"].encode("utf-8"))

        try:
            hmac.hexverify(data["authtag"])

        except Exception as e:
            return False

        return True

    def _decrypt_data(self, data: Dict[str, str]) -> Optional[Dict[str, str]]:
        decrypted_data = {
            "device_name": data["device_name"],
            "utctime": data["utctime"],
            "authtag": data["authtag"]
        }

        iv = binascii.unhexlify(data["iv"])

        for k in ["lat", "lon", "alt", "speed"]:
            cipher = AES.new(self._key, AES.MODE_CBC, iv)
            decrypted_data[k] = Padding.unpad(cipher.decrypt(binascii.unhexlify(data[k])),
                                              16,
                                              'pkcs7').decode("utf-8")

        return decrypted_data

    def _get_data(self) -> SensorDataGPS:

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
            logging.exception("[%s] Failed to fetch GPS data." % self._log_tag)
            raise

        # Decrypt and authenticate data if fetching was successful.
        if request_result["code"] == ChasRErrorCodes.NO_ERROR:

            decrypted_data = None
            try:
                decrypted_data = self._decrypt_data(request_result["data"]["locations"][0])

            except Exception as e:
                logging.exception("[%s] Failed to decrypt GPS data." % self._log_tag)

            if decrypted_data is None:
                logging.error("[%s] Unable to decrypt GPS data." % self._log_tag)
                raise ValueError("Decryption Error")

            if decrypted_data["device_name"] != self.device:
                logging.error("[%s] Received GPS data for wrong device." % self._log_tag)
                raise ValueError("Wrong device")

            if not self._check_hmac(decrypted_data):
                logging.error("[%s] Unable to authenticate GPS data." % self._log_tag)
                raise ValueError("Unauthenticated Data")

            self._last_position = SensorDataGPS(float(decrypted_data["lat"]),
                                                float(decrypted_data["lon"]),
                                                int(decrypted_data["utctime"]))

            return self._last_position

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

    def _get_optional_data(self) -> Optional[Dict[str, Any]]:
        if self._last_position is None:
            return None

        url = "https://alertr.de/chasr/map.php#mode=view&device_name=%s&start=%d&end=%d" \
              % (self.device, self._last_position.utctime, self._last_position.utctime)

        time_str = time.strftime("%d %b %Y at %H:%M:%S", time.localtime(self._last_position.utctime))

        msg = "GPS position (Lat: %f, Lon: %f) at %s. View: %s"\
              % (self._last_position.lat, self._last_position.lon, time_str, url)

        optional_data = {
            "device": self.device,
            "username": self.username,
            "url": url,
            "message": msg
        }
        return optional_data

    def initialize(self) -> bool:
        if not super().initialize():
            return False

        # Create decryption key from the secret.
        sha256 = hashlib.sha256()
        sha256.update(self.secret.encode("utf-8"))
        self._key = sha256.digest()

        return True
