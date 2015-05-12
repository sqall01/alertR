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


# internal class that is used as an enum to represent the type of file update
class _FileUpdateType:
	NEW = 1
	DELETE = 2
	MODIFY = 3


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

		# create an updater process
		self.updater = Updater(host, port, fileLocation, caFile,
			self.globalData)

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

			if self.updater.getNewestVersionInformation() is False:
				updateFailCount += 1
				continue

			# check if updates failed at least 10 times in a row before
			# => problems are now resolved => log and notify user
			if updateFailCount >= 10:
				logging.info("[%s]: Update problems resolved."
					% self.fileName)

				if self.emailNotification is True:
					self.smtpAlert.sendUpdateCheckFailureAlertClear(
						updateFailCount, self.globalData.name)

			updateFailCount = 0

			# check if the version on the server is newer than the used
			# (or last known) one
			# => notify user about the new version
			if (self.updater.newestVersion > self.newestVersion or
				(self.updater.newestRev > self.newestRev
				and self.updater.newestVersion == self.newestVersion)):

				logging.warning("[%s]: New version %.3f-%d available "
					% (self.fileName, self.updater.newestVersion,
					self.updater.newestRev)
					+ "(current version: %.3f-%d)."
					% (self.version, self.rev))

				# update newest known version
				self.newestVersion = self.updater.newestVersion
				self.newestRev = self.updater.newestRev

				if self.emailNotification is True:
					self.smtpAlert.sendUpdateCheckNewVersion(self.version,
						self.rev, self.newestVersion, self.newestRev,
						self.globalData.name)

			else:

				logging.info("[%s]: No new version available."
					% self.fileName)







class Updater:


	def __init__(self, host, port, fileLocation, caFile, globalData):

		# used for logging
		self.fileName = os.path.basename(__file__)

		# the updater object is not thread safe
		self.updaterLock = threading.Semaphore(1)

		# get global configured data
		self.globalData = globalData
		self.version = self.globalData.version
		self.rev = self.globalData.rev
		self.smtpAlert = self.globalData.smtpAlert

		# set update server configuration
		self.host = host
		self.port = port
		self.fileLocation = fileLocation
		self.caFile = caFile

		# needed to keep track of the newest version
		self.newestVersion = self.version
		self.newestRev = self.rev
		self.newestFiles = None
		self.lastChecked = 0.0


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.updaterLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
		self.updaterLock.release()


	# internal function that checks which files are new and which files have
	# to be updated
	#
	# return a dict of files that are affected by this update (and how) or None
	def _checkFilesToUpdate(self):

		# check if the last version information check was done shortly before
		# => if not get the newest version information
		if (time.time() - self.lastChecked) > 60:
			if self.getNewestVersionInformation() is False:
				logging.error("[%s]: Not able to get version "
					% self.fileName
					+ "information for checking files.")
				return None

		counterUpdate = 0
		counterNew = 0

		# get the absolute location to this instance
		instanceLocation = os.path.dirname(os.path.abspath(__file__)) + "/../"

		# get all files that have to be updated
		filesToUpdate = dict()
		for clientFile in self.newestFiles.keys():

			# check if file already exists
			# => check if file has to be updated
			if os.path.exists(instanceLocation + clientFile):

				sha256Hash = self._sha256File(instanceLocation + clientFile)

				# check if file has changed
				# => if not ignore it
				if sha256Hash == self.newestFiles[clientFile]:

					logging.debug("[%s]: Not changed: '%s'"
						% (self.fileName, clientFile))

					continue

				# => if it has changed add it to the list of files to update
				else:

					logging.debug("[%s]: New version: '%s'"
						% (self.fileName, clientFile))

					filesToUpdate[clientFile] = _FileUpdateType.MODIFY
					counterUpdate += 1

			# => if the file does not exist, just add it
			else:

				logging.debug("[%s]: New file: '%s'"
					% (self.fileName, clientFile))

				filesToUpdate[clientFile] = _FileUpdateType.NEW
				counterNew += 1

		logging.info("[%s]: Files to modify: %d; New files: %d"
			% (self.fileName, counterUpdate, counterNew))

		return filesToUpdate


	# internal function that checks the needed permissions to
	# perform the update
	#
	# return True or False
	def _checkFilePermissions(self, filesToUpdate):

		# get the absolute location to this instance
		instanceLocation = os.path.dirname(os.path.abspath(__file__)) + "/../"

		# check permissions for each file that is affected by this update
		for clientFile in filesToUpdate.keys():

			# check if the file just has to be modified
			if filesToUpdate[clientFile] == _FileUpdateType.MODIFY:

				# check if the file is not writable
				# => cancel update
				if not os.access(instanceLocation + clientFile, os.W_OK):
					logging.error("[%s]: File '%s' is not writable."
						% (self.fileName, clientFile))
					return False

				logging.debug("[%s]: File '%s' is writable."
						% (self.fileName, clientFile))


			# check if the file is new and has to be created
			elif filesToUpdate[clientFile] == _FileUpdateType.NEW:

				logging.debug("[%s]: Checking write permissions for new "
					% self.fileName
					+ "file: '%s'"
					% clientFile)

				folderStructure = clientFile.split("/")

				# check if the new file is located in the root directory
				# of the instance
				# => check root directory of the instance for write permissions
				if len(folderStructure) == 1:
					if not os.access(instanceLocation, os.W_OK):
						logging.error("[%s]: Folder './' is not "
							% self.fileName
							+ "writable.")
						return False

					logging.debug("[%s]: Folder './' is writable."
						% self.fileName)

				# if new file is not located in the root directory
				# of the instance
				# => check all folders on the way to the new file for write
				# permissions
				else:
					tempPart = ""
					for filePart in folderStructure:

						# check if folder exists
						if os.path.exists(instanceLocation + tempPart
							+ "/" + filePart):

							# check if folder is not writable
							# => cancel update
							if not os.access(instanceLocation + tempPart
								+ "/" + filePart, os.W_OK):
								logging.error("[%s]: Folder '.%s/%s' is not "
									% (self.fileName, tempPart, filePart)
									+ "writable.")
								return False

							logging.debug("[%s]: Folder '.%s/%s' is writable."
								% (self.fileName, tempPart, filePart))

							tempPart += "/"
							tempPart += filePart


			# check if the file has to be deleted
			elif filesToUpdate[clientFile] == _FileUpdateType.DELETE:
				raise NotImplementedError("Feature not yet implemented.")


		return True


	# internal function that calculates the sha256 hash of the file
	def _sha256File(self, inputFileName):
		f = open(inputFileName, 'r')
		sha256 = hashlib.sha256()
		while True:
			data = f.read(128)
			if not data:
				break
			sha256.update(data)
		f.close()
		return sha256.hexdigest()


	# function that gets the newest version information from the
	# online repository
	def getNewestVersionInformation(self):

		self._acquireLock()

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
				raise ValueError("Server response code not 200 (was %d)."
					% response.status)

		except Exception as e:
			logging.exception("[%s]: Getting version information failed."
				% self.fileName)

			self._releaseLock()

			return False


		# parse version information string
		try:
			jsonData = json.loads(versionString)

			version = float(jsonData["version"])
			rev = int(jsonData["rev"])

			newestFiles = jsonData["files"]

			if not isinstance(newestFiles, dict):

				raise ValueError("Key 'files' is not of type dict.")

				self._releaseLock()

				return False

		except Exception as e:
			logging.exception("[%s]: Parsing version information failed."
				% self.fileName)

			self._releaseLock()

			return False

		logging.debug("[%s]: Newest version information: %.3f-%d."
			% (self.fileName, version, rev))

		# check if the version on the server is newer than the used one
		# => update information
		if (version > self.newestVersion or
			(rev > self.newestRev and version == self.newestVersion)):

			# update newest known version information
			self.newestVersion = version
			self.newestRev = rev
			self.newestFiles = newestFiles

		self.lastChecked = time.time()

		self._releaseLock()

		return True

