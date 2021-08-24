import binascii
import os
import time
import hashlib
import copy
from unittest import TestCase
from typing import Dict
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
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

        # Calculate authentication tag.
        hmac = HMAC.new(key, digestmod=SHA256)
        hmac.update(data["device_name"].encode("utf-8"))
        hmac.update(str(data["utctime"]).encode("utf-8"))
        hmac.update(data["lat"].encode("utf-8"))
        hmac.update(data["lon"].encode("utf-8"))
        hmac.update(data["alt"].encode("utf-8"))
        hmac.update(data["speed"].encode("utf-8"))
        encrypted_data["authtag"] = hmac.hexdigest()

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

    def test_decrypt_data_invalid_secret(self):
        """
        Tests the decryption function with invalid data (wrong secret).
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
        sensor.secret = secret + "_invalid"
        sensor.triggerState = 1
        self.assertTrue(sensor.initialize())

        was_exception = False
        try:
            sensor._decrypt_data(encrypted_data)

        except Exception as e:
            was_exception = True

        self.assertTrue(was_exception)

    def test_decrypt_data_invalid_data(self):
        """
        Tests the decryption function with invalid data (wrong data).
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

        # Invalidate data.
        encrypted_data["lat"] = encrypted_data["lat"][1:]

        sensor = ChasRSensor()
        sensor.secret = secret + "_invalid"
        sensor.triggerState = 1
        self.assertTrue(sensor.initialize())

        was_exception = False
        try:
            sensor._decrypt_data(encrypted_data)

        except Exception as e:
            was_exception = True

        self.assertTrue(was_exception)

    def test_check_hmac_valid(self):
        """
        Tests the hmac validation function with valid data.
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

        decrypted_data = copy.deepcopy(data)
        decrypted_data["authtag"] = encrypted_data["authtag"]

        self.assertTrue(sensor._check_hmac(decrypted_data))

    def test_check_hmac_invalid_secret(self):
        """
        Tests the hmac validation function with invalid data (wrong secret).
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
        sensor.secret = secret + "_wrong"
        sensor.triggerState = 1
        self.assertTrue(sensor.initialize())

        decrypted_data = copy.deepcopy(data)
        decrypted_data["authtag"] = encrypted_data["authtag"]

        self.assertFalse(sensor._check_hmac(decrypted_data))

    def test_check_hmac_invalid_data(self):
        """
        Tests the hmac validation function with invalid data (wrong data).
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

        decrypted_data = copy.deepcopy(data)
        decrypted_data["authtag"] = encrypted_data["authtag"]

        # Manipulate data.
        temp = decrypted_data["lat"]
        decrypted_data["lat"] = decrypted_data["lon"]
        decrypted_data["lon"] = temp

        self.assertFalse(sensor._check_hmac(decrypted_data))
