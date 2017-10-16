#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import socket
import ssl
import httplib
import threading
import os
import time
import logging
import json
import hashlib
import tempfile
import shutil
import stat
import math


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


# this class processes all actions concerning the update process
class Updater:

	def __init__(self, host, port, serverPath, caFile, globalData,
		localInstanceInfo):

		# used for logging
		self.fileName = os.path.basename(__file__)

		# the updater object is not thread safe
		self.updaterLock = threading.Semaphore(1)

		# get global configured data
		self.globalData = globalData
		self.logger = self.globalData.logger
		self.version = self.globalData.version
		self.rev = self.globalData.rev
		self.instance = self.globalData.instance

		# location of this instance
		self.instanceLocation = os.path.dirname(os.path.abspath(__file__)) \
			+ "/../"

		# set update server configuration
		self.host = host
		self.port = port
		self.serverPath = serverPath
		self.caFile = caFile

		# needed to keep track of the newest version
		self.newestVersion = self.version
		self.newestRev = self.rev
		self.newestFiles = None
		self.lastChecked = 0
		self.localInstanceInfo = localInstanceInfo
		self.repoInfo = None
		self.instanceInfo = None

		# size of the download chunks
		self.chunkSize = 4096

		# Get newest data from repository.
		if not self._getNewestVersionInformation():
			raise ValueError("Not able to get newest repository information.")


	# internal function that acquires the lock
	def _acquireLock(self):
		self.logger.debug("[%s]: Acquire lock." % self.fileName)
		self.updaterLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		self.logger.debug("[%s]: Release lock." % self.fileName)
		self.updaterLock.release()


	# internal function that checks which files are new and which files have
	# to be updated
	#
	# return a dict of files that are affected by this update (and how) or None
	def _checkFilesToUpdate(self):

		# check if the last version information check was done shortly before
		# or was done at all
		# => if not get the newest version information
		utcTimestamp = int(time.time())
		if ((utcTimestamp - self.lastChecked) > 60
			or self.newestFiles is None):
			if self._getNewestVersionInformation() is False:
				self.logger.error("[%s]: Not able to get version "
					% self.fileName
					+ "information for checking files.")
				return None

		counterUpdate = 0
		counterNew = 0
		counterDelete = 0
		fileList = self.newestFiles.keys()

		# get all files that have to be updated
		filesToUpdate = dict()
		for clientFile in fileList:

			# check if file already exists
			# => check if file has to be updated
			if os.path.exists(self.instanceLocation + clientFile):

				f = open(self.instanceLocation + clientFile, 'r')
				sha256Hash = self._sha256File(f)
				f.close()

				# check if file has changed
				# => if not ignore it
				if sha256Hash == self.newestFiles[clientFile]:

					self.logger.debug("[%s]: Not changed: '%s'"
						% (self.fileName, clientFile))

					continue

				# => if it has changed add it to the list of files to update
				else:

					self.logger.debug("[%s]: New version: '%s'"
						% (self.fileName, clientFile))

					filesToUpdate[clientFile] = _FileUpdateType.MODIFY
					counterUpdate += 1

			# => if the file does not exist, just add it
			else:

				self.logger.debug("[%s]: New file: '%s'"
					% (self.fileName, clientFile))

				filesToUpdate[clientFile] = _FileUpdateType.NEW
				counterNew += 1

		# Get all files that have to be deleted.
		for clientFile in self.localInstanceInfo["files"].keys():
			if clientFile not in fileList:

				self.logger.debug("[%s]: Delete file: '%s'"
					% (self.fileName, clientFile))

				filesToUpdate[clientFile] = _FileUpdateType.DELETE
				counterDelete += 1

		self.logger.info("[%s]: Files to modify: %d; New files: %d; "
			% (self.fileName, counterUpdate, counterNew)
			+ "Files to delete: %d"
			% counterDelete)

		return filesToUpdate


	# internal function that checks the needed permissions to
	# perform the update
	#
	# return True or False
	def _checkFilePermissions(self, filesToUpdate):

		# check permissions for each file that is affected by this update
		for clientFile in filesToUpdate.keys():

			# check if the file just has to be modified
			if filesToUpdate[clientFile] == _FileUpdateType.MODIFY:

				# check if the file is not writable
				# => cancel update
				if not os.access(self.instanceLocation + clientFile, os.W_OK):
					self.logger.error("[%s]: File '%s' is not writable."
						% (self.fileName, clientFile))
					return False

				self.logger.debug("[%s]: File '%s' is writable."
						% (self.fileName, clientFile))


			# check if the file is new and has to be created
			elif filesToUpdate[clientFile] == _FileUpdateType.NEW:

				self.logger.debug("[%s]: Checking write permissions for new "
					% self.fileName
					+ "file: '%s'"
					% clientFile)

				folderStructure = clientFile.split("/")

				# check if the new file is located in the root directory
				# of the instance
				# => check root directory of the instance for write permissions
				if len(folderStructure) == 1:
					if not os.access(self.instanceLocation, os.W_OK):
						self.logger.error("[%s]: Folder './' is not "
							% self.fileName
							+ "writable.")
						return False

					self.logger.debug("[%s]: Folder './' is writable."
						% self.fileName)

				# if new file is not located in the root directory
				# of the instance
				# => check all folders on the way to the new file for write
				# permissions
				else:
					tempPart = ""
					for filePart in folderStructure:

						# check if folder exists
						if os.path.exists(self.instanceLocation + tempPart
							+ "/" + filePart):

							# check if folder is not writable
							# => cancel update
							if not os.access(self.instanceLocation + tempPart
								+ "/" + filePart, os.W_OK):
								self.logger.error("[%s]: Folder '.%s/%s' "
									% (self.fileName, tempPart, filePart)
									+ "is not writable.")
								return False

							self.logger.debug("[%s]: Folder '.%s/%s' "
								% (self.fileName, tempPart, filePart)
								+ "is writable.")

							tempPart += "/"
							tempPart += filePart


			# check if the file has to be deleted
			elif filesToUpdate[clientFile] == _FileUpdateType.DELETE:

				# check if the file is not writable
				# => cancel update
				if not os.access(self.instanceLocation + clientFile, os.W_OK):
					self.logger.error("[%s]: File '%s' is not writable "
						% (self.fileName, clientFile)
						+ "(deletable).")
					return False

				self.logger.debug("[%s]: File '%s' is writable (deletable)."
						% (self.fileName, clientFile))

			else:
				raise ValueError("Unknown file update type.")

		return True


	# internal function that creates sub directories in the target directory
	# for the given file location
	#
	# return True or False
	def _createSubDirectories(self, fileLocation, targetDirectory):

		folderStructure = fileLocation.split("/")
		if len(folderStructure) != 1:

			try:

				i = 0
				tempPart = ""
				while i < (len(folderStructure) - 1):

					# check if the sub directory already exists
					# => if not create it
					if not os.path.exists(targetDirectory + tempPart + "/"
						+ folderStructure[i]):

						self.logger.debug("[%s]: Creating directory "
							% self.fileName
							+ "'%s/%s/%s'."
							% (targetDirectory, tempPart, folderStructure[i]))

						os.mkdir(targetDirectory + tempPart + "/"
							+ folderStructure[i])

					# if the sub directory already exists then check
					# if it is a directory
					# => raise an exception if it is not
					elif not os.path.isdir(targetDirectory + tempPart + "/"
						+ folderStructure[i]):

						raise ValueError("Location '%s' already exists "
							% (tempPart + "/" + folderStructure[i])
							+ "and is not a directory.")

					# only log if sub directory already exists
					else:
						self.logger.debug("[%s]: Directory '%s/%s/%s' already "
							% (self.fileName, targetDirectory, tempPart,
							folderStructure[i])
							+ "exists.")

					tempPart += "/"
					tempPart += folderStructure[i]

					i += 1

			except Exception as e:

				self.logger.exception("[%s]: Creating directory structure for "
					% self.fileName
					+ "'%s' failed."
					% fileLocation)

				return False

		return True


	# Internal function that deletes sub directories in the target directory
	# for the given file location if they are empty.
	#
	# return True or False
	def _deleteSubDirectories(self, fileLocation, targetDirectory):

		folderStructure = fileLocation.split("/")
		del folderStructure[-1]

		try:

			i = len(folderStructure) - 1
			
			while 0 <= i:

				tempDir = ""
				for j in range(i + 1):
					tempDir = tempDir + "/" + folderStructure[j]

				# If the directory to delete is not empty then finish
				# the whole sub directory delete process.
				if os.listdir(targetDirectory + tempDir):
					break

				self.logger.debug("[%s]: Deleting directory '%s/%s/'."
					% (self.fileName, targetDirectory, tempDir))

				os.rmdir(targetDirectory + tempDir)

				i -= 1

		except Exception as e:

			self.logger.exception("[%s]: Deleting directory structure for "
				% self.fileName
				+ "'%s' failed."
				% fileLocation)

			return False

		return True


	# internal function that downloads the given file into a temporary file
	# and checks if the given hash is correct
	#
	# return None or the handle to the temporary file
	def _downloadFile(self, fileLocation, fileHash):

		self.logger.info("[%s]: Downloading file: '%s'"
			% (self.fileName, fileLocation))

		# create temporary file
		try:
			fileHandle = tempfile.TemporaryFile()

		except Exception as e:

			self.logger.exception("[%s]: Creating temporary file failed."
				% self.fileName)

			return None


		# download file from server
		conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)
		try:

			conn.request("GET", self.serverPath + "/"
				+ self.repoInstanceLocation + "/" + fileLocation)
			response = conn.getresponse()

			# check if server responded correctly
			# => download file
			if response.status == 200:

				# get the size of the response
				fileSize = -1
				try:
					headers = response.getheaders()
					for header in headers:
						if header[0] == "content-length":
							fileSize = int(header[1])
							break
				except:
					fileSize = -1

				# check if the file size was part of the header
				# and we can output the status of the download
				showStatus = False
				if fileSize > 0:
					showStatus = True
					maxChunks = int(math.ceil(float(fileSize)
						/ float(self.chunkSize)))

				# actually download file
				chunkCount = 0
				printedPercentage = 0
				while True:
					chunk = response.read(self.chunkSize)
					if not chunk:
						break
					fileHandle.write(chunk)

					# output status of the download
					chunkCount += 1
					if showStatus:
						if chunkCount > maxChunks:
							showStatus = False

							self.logger.warning("[%s]: Concent information of "
									% self.fileName
									+ "received header flawed. Stopping "
									+ "to show download status.")

							continue

						else:
							percentage = int((float(chunkCount)
								/ float(maxChunks)) * 100)
							if (percentage / 10) > printedPercentage:
								printedPercentage = percentage / 10

								self.logger.info("[%s]: Download: %d%%"
									% (self.fileName, printedPercentage * 10))

			else:
				raise ValueError("Server response code not 200 (was %d)."
					% response.status)

		except Exception as e:
			self.logger.exception("[%s]: Downloading file '%s' from the "
				% (self.fileName, fileLocation)
				+ "server failed.")

			return None


		# calculate sha256 hash of the downloaded file
		fileHandle.seek(0)
		sha256Hash = self._sha256File(fileHandle)
		fileHandle.seek(0)

		# check if downloaded file has the correct hash
		if sha256Hash != fileHash:

			self.logger.error("[%s]: Temporary file does not have the "
				% self.fileName
				+ "correct hash.")

			self.logger.debug("[%s]: Temporary file: %s"
				% (self.fileName, sha256Hash))

			self.logger.debug("[%s]: Repository: %s"
				% (self.fileName, fileHash))

			return None

		self.logger.info("[%s]: Successfully downloaded file: '%s'"
			% (self.fileName, fileLocation))

		return fileHandle


	# internal function that calculates the sha256 hash of the file
	def _sha256File(self, fileHandle):
		fileHandle.seek(0)
		sha256 = hashlib.sha256()
		while True:
			data = fileHandle.read(128)
			if not data:
				break
			sha256.update(data)
		return sha256.hexdigest()


	# Internal function that gets the newest instance information from the
	# online repository
	#
	# return True or False
	def _getInstanceInformation(self, conn=None):

		if conn is None:
			conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)

		try:
			if self._getRepositoryInformation(conn) is False:
				raise ValueError("Not able to get newest "
					+ "repository information.")

		except Exception as e:
			self.logger.exception("[%s]: Retrieving newest repository "
				% self.fileName
				+ "information failed.")

			return False

		self.logger.debug("[%s]: Downloading instance information."
			% self.fileName)

		# get instance information string from the server
		instanceInfoString = ""
		try:

			conn.request("GET", self.serverPath + "/"
				+ self.repoInstanceLocation + "/instanceInfo.json")
			response = conn.getresponse()

			# check if server responded correctly
			if response.status == 200:
				instanceInfoString = response.read()

			else:
				raise ValueError("Server response code not 200 (was %d)."
					% response.status)

			conn.close()

		except Exception as e:
			self.logger.exception("[%s]: Getting version information failed."
				% self.fileName)

			return False

		# parse instance information string
		try:
			self.instanceInfo = json.loads(instanceInfoString)

			if not isinstance(self.instanceInfo["version"], float):
				raise ValueError("Key 'version' is not of type float.")

			if not isinstance(self.instanceInfo["rev"], int):
				raise ValueError("Key 'rev' is not of type int.")

			if not isinstance(self.instanceInfo["dependencies"], dict):
				raise ValueError("Key 'dependencies' is not of type dict.")

		except Exception as e:
			self.logger.exception("[%s]: Parsing version information failed."
				% self.fileName)

			return False

		return True


	# Internal function that gets the newest repository information from the
	# online repository.
	#
	# return True or False
	def _getRepositoryInformation(self, conn=None):

		if conn is None:
			conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)

		self.logger.debug("[%s]: Downloading repository information."
			% self.fileName)

		# get repository information from the server
		repoInfoString = ""
		try:

			conn.request("GET", self.serverPath + "/repoInfo.json")
			response = conn.getresponse()

			# check if server responded correctly
			if response.status == 200:
				repoInfoString = response.read()

			else:
				raise ValueError("Server response code not 200 (was %d)."
					% response.status)

			conn.close()

		except Exception as e:
			self.logger.exception("[%s]: Getting repository information "
				% self.fileName
				+ "failed.")

			return False


		# parse repository information string
		try:
			self.repoInfo = json.loads(repoInfoString)

			if not isinstance(self.repoInfo, dict):
				raise ValueError("Received repository information is "
					+ "not of type dict.")

			if not "instances" in self.repoInfo.keys():
				raise ValueError("Received repository information has "
					+ "no information about the instances.")

			if not self.instance in self.repoInfo["instances"].keys():
				raise ValueError("Instance '%s' is not managed by "
					% self.instance
					+ "used repository.")

		except Exception as e:
			self.logger.exception("[%s]: Parsing repository information "
				% self.fileName
				+ "failed.")

			return False

		# Set repository location on server.
		self.repoInstanceLocation = str(
				self.repoInfo["instances"][self.instance]["location"])

		return True


	# internal function that gets the newest version information from the
	# online repository
	#
	# return True or False
	def _getNewestVersionInformation(self, conn=None):

		if conn is None:
			conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)

		try:
			if self._getInstanceInformation(conn) is False:
				raise ValueError("Not able to get newest "
					+ "instance information.")

		except Exception as e:
			self.logger.exception("[%s]: Retrieving newest instance "
				% self.fileName
				+ "information failed.")

			return False

		# Parse version information.
		try:
			version = float(self.instanceInfo["version"])
			rev = int(self.instanceInfo["rev"])
			newestFiles = self.instanceInfo["files"]

			if not isinstance(newestFiles, dict):
				raise ValueError("Key 'files' is not of type dict.")

		except Exception as e:
			self.logger.exception("[%s]: Parsing version information failed."
				% self.fileName)

			return False

		self.logger.debug("[%s]: Newest version information: %.3f-%d."
			% (self.fileName, version, rev))

		# check if the version on the server is newer than the used one
		# or we have no information about the files
		# => update information
		if (version > self.newestVersion or
			(rev > self.newestRev and version == self.newestVersion)
			or self.newestFiles is None):

			# update newest known version information
			self.newestVersion = version
			self.newestRev = rev
			self.newestFiles = newestFiles

		self.lastChecked = int(time.time())

		return True


	# This function returns the instance information data.
	def getInstanceInformation(self):

		self._acquireLock()
		utcTimestamp = int(time.time())
		if ((utcTimestamp - self.lastChecked) > 60
			or self.instanceInfo is None):

			if not self._getInstanceInformation():
				self._releaseLock()
				raise ValueError("Not able to get newest "
					+ "instance information.")

		self._releaseLock()

		return self.instanceInfo


	# This function returns the repository information data.
	def getRepositoryInformation(self):

		self._acquireLock()
		utcTimestamp = int(time.time())
		if ((utcTimestamp - self.lastChecked) > 60
			or self.repoInfo is None):

			if not self._getRepositoryInformation():
				self._releaseLock()
				raise ValueError("Not able to get newest "
					+ "repository information.")

		self._releaseLock()

		return self.repoInfo


	# function that updates this instance of the alertR infrastructure
	def updateInstance(self):

		self._acquireLock()

		# check all files that have to be updated
		filesToUpdate = self._checkFilesToUpdate()

		if filesToUpdate is None:
			self.logger.error("[%s] Checking files for update failed."
				% self.fileName)

			self._releaseLock()

			return False

		if len(filesToUpdate) == 0:

			self.logger.info("[%s] No files have to be updated."
				% self.fileName)

			self._releaseLock()

			return True

		# check file permissions of the files that have to be updated
		if self._checkFilePermissions(filesToUpdate) is False:

			self.logger.info("[%s] Checking file permissions failed."
				% self.fileName)

			self._releaseLock()

			return False


		# download all files that have to be updated
		downloadedFileHandles = dict()
		for fileToUpdate in filesToUpdate.keys():

			# only download file if it is new or has to be modified
			if (filesToUpdate[fileToUpdate] == _FileUpdateType.NEW
				or filesToUpdate[fileToUpdate] == _FileUpdateType.MODIFY):

				# download new files, if one file fails
				# => close all file handles and abort update process
				downloadedFileHandle = self._downloadFile(fileToUpdate,
					self.newestFiles[fileToUpdate])
				if downloadedFileHandle is None:

					self.logger.error("[%s]: Downloading files from the "
						% self.fileName
						+ "repository failed. Aborting update process.")

					# close all temporary file handles
					# => temporary file is automatically deleted
					for fileHandle in downloadedFileHandles.keys():
						downloadedFileHandles[fileHandle].close()

					self._releaseLock()

					return False

				else:

					downloadedFileHandles[fileToUpdate] = downloadedFileHandle


		# copy all files to the correct location
		for fileToUpdate in filesToUpdate.keys():

			# check if the file has to be deleted
			if filesToUpdate[fileToUpdate] == _FileUpdateType.DELETE:

				# remove old file.
				try:

					self.logger.debug("[%s]: Deleting file '%s'."
						% (self.fileName, fileToUpdate))

					os.remove(self.instanceLocation + "/" + fileToUpdate)

				except Exception as e:
					self.logger.exception("[%s]: Deleting file '%s' failed."
					% (self.fileName, fileToUpdate))

					self._releaseLock()

					return False

				# Delete sub directories (if they are empty).
				self._deleteSubDirectories(fileToUpdate, self.instanceLocation)

				continue

			# check if the file is new
			# => create all sub directories (if they are missing)
			elif filesToUpdate[fileToUpdate] == _FileUpdateType.NEW:
				self._createSubDirectories(fileToUpdate, self.instanceLocation)

			# copy file to correct location
			try:

				self.logger.debug("[%s]: Copying file '%s' to alertR instance "
					% (self.fileName, fileToUpdate)
					+ "directory.")

				dest = open(self.instanceLocation + "/" + fileToUpdate, 'wb')
				shutil.copyfileobj(downloadedFileHandles[fileToUpdate], dest)
				dest.close()

			except Exception as e:
				self.logger.exception("[%s]: Copying file '%s' failed."
				% (self.fileName, fileToUpdate))

				self._releaseLock()

				return False

			# check if the hash of the copied file is correct
			f = open(self.instanceLocation + "/" + fileToUpdate, 'r')
			sha256Hash = self._sha256File(f)
			f.close()
			if sha256Hash != self.newestFiles[fileToUpdate]:
				self.logger.error("[%s]: Hash of file '%s' is not correct "
				% (self.fileName, fileToUpdate)
				+ "after copying.")

				self._releaseLock()

				return False

			# change permission of files that have to be executable
			if (fileToUpdate == "alertRclient.py"
				or fileToUpdate == "alertRserver.py"):

				self.logger.debug("[%s]: Changing permissions of '%s'."
					% (self.fileName, fileToUpdate))

				try:
					os.chmod(self.instanceLocation + "/" + fileToUpdate,
						stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

				except Exception as e:

					self.logger.exception("[%s]: Changing permissions of '%s' "
						% (self.fileName, fileToUpdate)
						+ "failed.")

					self._releaseLock()

					return False

		
		# close all temporary file handles
		# => temporary file is automatically deleted
		for fileHandle in downloadedFileHandles.keys():
			downloadedFileHandles[fileHandle].close()

		self._releaseLock()

		return True