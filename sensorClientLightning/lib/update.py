#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import socket
import ssl
import httplib
import threading
import os
import time
import logging
import json
import hashlib


# HTTPSConnection like class that verifies server certificates
class VerifiedHTTPSConnection(httplib.HTTPSConnection):
	# needs socket and ssl lib
	def __init__(self, host, port=None, servercert_file=None, 
		key_file=None, cert_file=None, strict=None, 
		timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
		httplib.HTTPSConnection.__init__(self, host, port, key_file, 
			cert_file, strict, timeout)
		self.servercert_file = servercert_file

	# overwrites the original version of httplib (python 2.6)
	def connect(self):
		"Connect to a host on a given (SSL) port."

		sock = socket.create_connection((self.host, self.port), self.timeout)
		if self._tunnel_host:
			self.sock = sock
			self._tunnel()

		# the only thing that has to be changed in the original function from
		# httplib (tell ssl.wrap_socket to verify server certificate)
		self.sock = ssl.wrap_socket(sock, self.key_file, 
			self.cert_file, cert_reqs=ssl.CERT_REQUIRED, 
			ca_certs=self.servercert_file)


# this class checks in specific intervals for updates and notifies
# the user about new versions of this client
class UpdateChecker(threading.Thread):

	def __init__(self, host, port, fileLocation, caFile, interval,
		emailNotification, globalData):
		threading.Thread.__init__(self)

		# used for logging
		self.fileName = os.path.basename(__file__)

		# get global configured data
		self.globalData = globalData
		self.version = self.globalData.version
		self.rev = self.globalData.rev
		self.smtpAlert = self.globalData.smtpAlert

		# set interval for update checking
		self.checkInterval = interval

		# set update server configuration
		self.host = host
		self.port = port
		self.fileLocation = fileLocation
		self.caFile = caFile

		self.emailNotification = emailNotification

		# needed to keep track of the newest version
		self.newestVersion = self.version
		self.newestRev = self.rev


	def run(self):

		updateFailCount = 0

		while True:

			time.sleep(self.checkInterval)

			# check if updates failed at least 10 times in a row
			# => log and notify user
			if updateFailCount >= 10:

				logging.error("[%s]: Update checking failed for %d "
					% (self.fileName, updateFailCount)
					+ "times in a row.")

				if self.emailNotification is True:
					self.smtpAlert.sendUpdateCheckFailureAlert(
						updateFailCount, self.globalData.name)

			logging.info("[%s]: Checking for a new version." % self.fileName)

			conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)
			versionString = ""

			# get version string from the server
			try:
				conn.request("GET", self.fileLocation)
				response = conn.getresponse()

				# check if server responded correctly
				if response.status == 200:
					versionString = response.read()

				else:
					raise ValueError("Server response code not 200 (was %d)"
						% response.status)

			except Exception as e:
				logging.exception("[%s]: Update check failed."
					% self.fileName)

				updateFailCount += 1

				continue


			# parse version string
			try:
				jsonData = json.loads(versionString)

				version = float(jsonData["version"])
				rev = int(jsonData["rev"])

			except Exception as e:
				logging.exception("[%s]: Parsing version failed."
					% self.fileName)

				updateFailCount += 1

				continue
			
			logging.debug("[%s]: Newest version: %.3f-%d."
				% (self.fileName, version, rev))

			# check if updates failed at least 10 times in a row before
			# => problems are now resolved => log and notify user
			if updateFailCount >= 10:
				logging.info("[%s]: Update problems resolved."
					% self.fileName)

				if self.emailNotification is True:
					self.smtpAlert.sendUpdateCheckFailureAlertClear(
						updateFailCount, self.globalData.name)

			updateFailCount = 0

			# check if the version on the server is newer than the used one
			# => notify user about the new version
			if (version > self.newestVersion or
				(rev > self.newestRev and version == self.newestVersion)):

				logging.warning("[%s]: New version %.3f-%d available "
				% (self.fileName, version, rev)
				+ "(current version: %.3f-%d)."
				% (self.version, self.rev))

				# update newest known version
				self.newestVersion = version
				self.newestRev = rev

				if self.emailNotification is True:
					self.smtpAlert.sendUpdateCheckNewVersion(self.version,
						self.rev, version, rev, self.globalData.name)

			else:

				logging.info("[%s]: No new version available."
					% self.fileName)