#!/usr/bin/python2

import time
import socket
import ssl
import threading
import logging
import os
import base64
import xml.etree.cElementTree
import random
import json
import hashlib
import sys
from Crypto.Cipher import AES
from lib import GlobalData
from lib import ErrorCodes
BUFSIZE = 4096


# simple class of an ssl tcp client
class Client:

	def __init__(self, host, port, serverCAFile):
		self.host = host
		self.port = port
		self.serverCAFile = serverCAFile
		self.socket = None
		self.sslSocket = None


	def connect(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.sslSocket = ssl.wrap_socket(self.socket,
			ca_certs=self.serverCAFile, cert_reqs=ssl.CERT_REQUIRED,
			ssl_version=ssl.PROTOCOL_TLSv1)

		self.sslSocket.connect((self.host, self.port))


	def send(self, data):
		count = self.sslSocket.send(data)


	def recv(self, buffsize, timeout=3.0):
		data = None
		self.sslSocket.settimeout(timeout)
		data = self.sslSocket.recv(buffsize)
		self.sslSocket.settimeout(None)
		return data


	def close(self):
		# closing SSLSocket will also close the underlying socket
		self.sslSocket.close()


# Function creates a path location for the given user input.
def makePath(inputLocation):
	# Do nothing if the given location is an absolute path.
	if inputLocation[0] == "/":
		return inputLocation
	# Replace ~ with the home directory.
	elif inputLocation[0] == "~":
		return os.environ["HOME"] + inputLocation[1:]
	# Assume we have a given relative path.
	return os.path.dirname(os.path.abspath(__file__)) + "/" + inputLocation


if __name__ == '__main__':

	fileName = os.path.basename(__file__)
	instanceLocation = os.path.dirname(os.path.abspath(__file__)) + "/"

	# generate object of the global needed data
	globalData = GlobalData()

	try:
		# parse config file
		configRoot = xml.etree.ElementTree.parse(instanceLocation +
			"/config/config.xml").getroot()

		# parse chosen log level
		tempLoglevel = str(
			configRoot.find("general").find("log").attrib["level"])
		tempLoglevel = tempLoglevel.upper()
		if tempLoglevel == "DEBUG":
			loglevel = logging.DEBUG
		elif tempLoglevel == "INFO":
			loglevel = logging.INFO
		elif tempLoglevel == "WARNING":
			loglevel = logging.WARNING
		elif tempLoglevel == "ERROR":
			loglevel = logging.ERROR
		elif tempLoglevel == "CRITICAL":
			loglevel = logging.CRITICAL
		else:
			raise ValueError("No valid log level in config file.")

		# initialize logging
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
			datefmt='%m/%d/%Y %H:%M:%S', level=loglevel)

	except Exception as e:
		print "Config could not be parsed."
		print e
		sys.exit(1)

	# parse the rest of the config with initialized logging
	alerts = list()
	try:

		# parse all alerts
		for item in configRoot.find("alerts").iterfind("alert"):

			alert = dict()

			# Read the push notification settings.
			alert["username"] = str(item.find("push").attrib["username"])
			alert["password"] = str(item.find("push").attrib["password"])
			alert["channel"] = str(item.find("push").attrib["channel"])
			alert["encSecret"] = str(item.find("push").attrib["secret"])
			alert["subject"] = str(item.find("push").attrib["subject"])
			alert["templateFile"] = makePath(
				str(item.find("push").attrib["templateFile"]))

			# check if the template file exists
			if not os.path.isfile(alert["templateFile"]):
				raise ValueError("Message template file '%s' does not exist."
					% alert.templateFile)

			alert["id"] = int(item.find("general").attrib["id"])
			alert["description"] = str(item.find("general").attrib["description"])

			# check if the id of the alert is unique
			for registeredAlert in alerts:
				if registeredAlert["id"] == alert["id"]:
					raise ValueError("Id of alert %d"
						% alert["id"] + "is already taken.")

			alerts.append(alert)

	except Exception as e:
		logging.exception("[%s]: Could not parse config." % fileName)
		sys.exit(1)

	# Sending test messages for the configured alerts.
	for alert in alerts:
		logging.info("[%s]: Sending message for alert id %d (%s)."
			% (fileName, alert["id"], alert["description"]))

		client = Client(globalData.pushServerAddress,
			globalData.pushServerPort,
			globalData.pushServerCert)

		client.connect()

		subject = "Test message for alert with id %d" % alert["id"]
		message = "This is a test message for the alert:\n\n" \
			+ "Id: %d\nDescription: %s\n\nCheers,\nalertR" \
			% (alert["id"], alert["description"])

		utc_timestamp = int(time.time())
		payload = json.dumps( {
			"sbj": subject,
			"msg": message,
			"tt": utc_timestamp,
			"ts": utc_timestamp,
			"is_sa": True,
			"st": 1
			} )

		enc_secret = alert["encSecret"]

		# Create a encryption key from the secret.
		sha256 = hashlib.sha256()
		sha256.update(enc_secret)
		key = sha256.digest()

		# Add random bytes in the beginning of
		# the message to increase randomness.
		iv = os.urandom(16)
		internal_iv = os.urandom(4)
		padded_payload = internal_iv + payload

		padding = len(padded_payload) % 16
		if padding != 0:
			for i in range(16 - padding):
				# Use whitespaces as padding since they are ignored by json.
				padded_payload += " "

		cipher = AES.new(key, AES.MODE_CBC, iv)
		encrypted_payload = cipher.encrypt(padded_payload)

		temp = iv + encrypted_payload
		data_send = base64.b64encode(temp)

		data = {"username": alert["username"],
				"password": alert["password"],
				"channel": alert["channel"],
				"data": data_send,
				"version": 0.1}

		client.send(json.dumps(data))

		response_str = client.recv(BUFSIZE)

		response = json.loads(response_str)

		# Process response.
		if response["Code"] == ErrorCodes.NO_ERROR:
			logging.info("[%s]: Message successfully transmitted." % fileName)
		elif response["Code"] == ErrorCodes.DATABASE_ERROR:
			logging.error("[%s]: Database error on server side. "
				% fileName
				+ "Please try again later.")
		elif response["Code"] == ErrorCodes.AUTH_ERROR:
			logging.error("[%s]: Authentication failed. "
				% fileName
				+ "Check your credentials.")
		elif response["Code"] == ErrorCodes.ILLEGAL_MSG_ERROR:
			logging.error("[%s]: Illegal message was sent. "
				% fileName
				+ "Please make sure to use the newest version. "
				+ "If you do, please open an issue on "
				+ "https://github.com/sqall01/alertR.")
		elif response["Code"] == ErrorCodes.GOOGLE_MSG_TOO_LARGE:
			logging.error("[%s]: Transmitted message too large. "
				% fileName
				+ "Please shorten it.")
		elif response["Code"] == ErrorCodes.GOOGLE_CONNECTION:
			logging.error("[%s]: Connection error on server side. "
				% fileName
				+ "Please try again later.")
		elif response["Code"] == ErrorCodes.GOOGLE_AUTH:
			logging.error("[%s]: Authentication error on server side. "
				% fileName
				+ "Please try again later.")
		elif response["Code"] == ErrorCodes.VERSION_MISSMATCH:
			logging.error("[%s]: Version missmatch. "
				% fileName
				+ "Please update your client.")
		elif response["Code"] == ErrorCodes.NO_NOTIFICATION_PERMISSION:
			logging.error("[%s]: No permission to use notification channel. "
				% fileName
				+ "Please update channel configuration.")
		else:
			logging.error("[%s]: The following error code occured: %d."
				% (fileName, response["Code"])
				+ "Please make sure to use the newest version. "
				+ "If you do, please open an issue on "
				+ "https://github.com/sqall01/alertR.")