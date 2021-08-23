import binascii
import os
import time
import hashlib
from unittest import TestCase
from typing import Dict, Any
from Crypto.Cipher import AES
from Crypto.Util import Padding
from lib.sensor.chasr import ChasRSensor


class TestChasRSensor(TestCase):

    def _encrypt_and_auth_data(self, secret: str, data: Dict[str, str]):

        encrypted_data = {
            "device_name": data["device_name"],
            "utctime": data["utctime"]
        }

        # Create key.
        sha256 = hashlib.sha256()
        sha256.update(secret.encode("utf-8"))
        key = sha256.digest()

        # Create IV.
        iv = os.urandom(16)
        encrypted_data["iv"] = binascii.hexlify(iv).decode("utf-8")

        for k in ["lat", "lon", "alt", "speed"]:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted_data[k] = binascii.hexlify(cipher.encrypt(Padding.pad(data[k].encode("utf-8"),
                                                                            16,
                                                                            'pkcs7'))).decode("utf-8")

        # TODO: authenticate data with hmac
        encrypted_data["authtag"] = "blah"

        return encrypted_data

    def test_decrypt_data_valid(self):
        """
        Tests the decryption function with valid data.
        """
        secret = "best_secret_ever"
        device = "test_device"

        data = {
            "device_name": device,
            "utctime": int(time.time()),
            "lat": "52.52437",
            "lon": "13.41053",
            "alt": "4.3242",
            "speed": "30.3"
        }

        encrypted_data = self._encrypt_and_auth_data(secret, data)

        sensor = ChasRSensor()
        sensor.secret = secret
        sensor.triggerState = 1
        self.assertTrue(sensor.initialize())

        decrypted_data = sensor._decrypt_data(encrypted_data)

        for k in ["lat", "lon", "alt", "speed", "device_name", "utctime"]:
            self.assertEqual(decrypted_data[k], data[k])
