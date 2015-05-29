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
import os
import sys
import time
import logging
import json
import hashlib
import tempfile
import shutil
import stat
import math
import importlib
import threading
import optparse


################ GLOBAL CONFIGURATION DATA ################

# used log level
# valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
loglevel = logging.INFO

# repository information
host = "raw.githubusercontent.com"
port = 443
serverPath = "/sqall01/alertR/master/"

################ GLOBAL CONFIGURATION DATA ################

# ca certificate of used github repository
# (/etc/ssl/certs/DigiCert_High_Assurance_EV_Root_CA.pem)
caCertificate = "-----BEGIN CERTIFICATE-----\n" \
	+ "MIIDxTCCAq2gAwIBAgIQAqxcJmoLQJuPC3nyrkYldzANBgkqhkiG9w0BAQUFADBs\n" \
	+ "MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3\n" \
	+ "d3cuZGlnaWNlcnQuY29tMSswKQYDVQQDEyJEaWdpQ2VydCBIaWdoIEFzc3VyYW5j\n" \
	+ "ZSBFViBSb290IENBMB4XDTA2MTExMDAwMDAwMFoXDTMxMTExMDAwMDAwMFowbDEL\n" \
	+ "MAkGA1UEBhMCVVMxFTATBgNVBAoTDERpZ2lDZXJ0IEluYzEZMBcGA1UECxMQd3d3\n" \
	+ "LmRpZ2ljZXJ0LmNvbTErMCkGA1UEAxMiRGlnaUNlcnQgSGlnaCBBc3N1cmFuY2Ug\n" \
	+ "RVYgUm9vdCBDQTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMbM5XPm\n" \
	+ "+9S75S0tMqbf5YE/yc0lSbZxKsPVlDRnogocsF9ppkCxxLeyj9CYpKlBWTrT3JTW\n" \
	+ "PNt0OKRKzE0lgvdKpVMSOO7zSW1xkX5jtqumX8OkhPhPYlG++MXs2ziS4wblCJEM\n" \
	+ "xChBVfvLWokVfnHoNb9Ncgk9vjo4UFt3MRuNs8ckRZqnrG0AFFoEt7oT61EKmEFB\n" \
	+ "Ik5lYYeBQVCmeVyJ3hlKV9Uu5l0cUyx+mM0aBhakaHPQNAQTXKFx01p8VdteZOE3\n" \
	+ "hzBWBOURtCmAEvF5OYiiAhF8J2a3iLd48soKqDirCmTCv2ZdlYTBoSUeh10aUAsg\n" \
	+ "EsxBu24LUTi4S8sCAwEAAaNjMGEwDgYDVR0PAQH/BAQDAgGGMA8GA1UdEwEB/wQF\n" \
	+ "MAMBAf8wHQYDVR0OBBYEFLE+w2kD+L9HAdSYJhoIAu9jZCvDMB8GA1UdIwQYMBaA\n" \
	+ "FLE+w2kD+L9HAdSYJhoIAu9jZCvDMA0GCSqGSIb3DQEBBQUAA4IBAQAcGgaX3Nec\n" \
	+ "nzyIZgYIVyHbIUf4KmeqvxgydkAQV8GK83rZEWWONfqe/EW1ntlMMUu4kehDLI6z\n" \
	+ "eM7b41N5cdblIZQB2lWHmiRk9opmzN6cN82oNLFpmyPInngiK3BD41VHMWEZ71jF\n" \
	+ "hS9OMPagMRYjyOfiZRYzy78aG6A9+MpeizGLYAiJLQwGXFK3xPkKmNEVX58Svnw2\n" \
	+ "Yzi9RKR/5CYrCsSXaQ3pjOLAEFe4yHYSkVXySGnYvCoCWw9E1CAx2/S6cCZdkGCe\n" \
	+ "vEsXCS+0yx5DaMkHJ8HSXPfqIbloEpw8nL+e/IBcm2PN7EeqJSdnoDfzAIJ9VNep\n" \
	+ "+OkuE6N36B9K\n" \
	+ "-----END CERTIFICATE-----\n"

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

	def __init__(self, host, port, serverPath, caFile, instance,
		targetLocation):

		# used for logging
		self.fileName = os.path.basename(__file__)

		# the updater object is not thread safe
		self.updaterLock = threading.Semaphore(1)

		# set global configured data
		self.version = 0
		self.rev = 0
		self.instance = instance
		self.instanceLocation = targetLocation

		# set update server configuration
		self.host = host
		self.port = port
		self.serverPath = serverPath
		self.caFile = caFile

		# needed to keep track of the newest version
		self.newestVersion = self.version
		self.newestRev = self.rev
		self.newestFiles = None
		self.lastChecked = 0.0
		self.repoInstanceLocation = None

		# size of the download chunks
		self.chunkSize = 4096


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
		# or was done at all
		# => if not get the newest version information
		if ((time.time() - self.lastChecked) > 60
			or self.newestFiles == None):
			if self._getNewestVersionInformation() is False:
				logging.error("[%s]: Not able to get version "
					% self.fileName
					+ "information for checking files.")
				return None

		counterUpdate = 0
		counterNew = 0

		# get all files that have to be updated
		filesToUpdate = dict()
		for clientFile in self.newestFiles.keys():

			# check if file already exists
			# => check if file has to be updated
			if os.path.exists(self.instanceLocation + clientFile):

				f = open(self.instanceLocation + clientFile, 'r')
				sha256Hash = self._sha256File(f)
				f.close()

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

		# check permissions for each file that is affected by this update
		for clientFile in filesToUpdate.keys():

			# check if the file just has to be modified
			if filesToUpdate[clientFile] == _FileUpdateType.MODIFY:

				# check if the file is not writable
				# => cancel update
				if not os.access(self.instanceLocation + clientFile, os.W_OK):
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
					if not os.access(self.instanceLocation, os.W_OK):
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
						if os.path.exists(self.instanceLocation + tempPart
							+ "/" + filePart):

							# check if folder is not writable
							# => cancel update
							if not os.access(self.instanceLocation + tempPart
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

						logging.debug("[%s]: Creating directory '%s/%s/%s'."
							% (self.fileName, targetDirectory, tempPart,
							folderStructure[i]))

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
						logging.debug("[%s]: Directory '%s/%s/%s' already "
							% (self.fileName, targetDirectory, tempPart,
							folderStructure[i])
							+ "exists.")

					tempPart += "/"
					tempPart += folderStructure[i]

					i += 1

			except Exception as e:

				logging.exception("[%s]: Creating directory structure for "
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

		logging.info("[%s]: Downloading file: '%s'"
			% (self.fileName, fileLocation))

		# create temporary file
		try:
			fileHandle = tempfile.TemporaryFile()

		except Exception as e:

			logging.exception("[%s]: Creating temporary file failed."
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

							logging.warning("[%s]: Concent information of "
									% self.fileName
									+ "received header flawed. Stopping "
									+ "to show download status.")

							continue

						else:
							percentage = int((float(chunkCount)
								/ float(maxChunks)) * 100)
							if (percentage / 10) > printedPercentage:
								printedPercentage = percentage / 10

								logging.info("[%s]: Download: %d%%"
									% (self.fileName, printedPercentage * 10))

			else:
				raise ValueError("Server response code not 200 (was %d)."
					% response.status)

		except Exception as e:
			logging.exception("[%s]: Downloading file '%s' from the "
				% (self.fileName, fileLocation)
				+ "server failed.")

			return None


		# calculate sha256 hash of the downloaded file
		fileHandle.seek(0)
		sha256Hash = self._sha256File(fileHandle)
		fileHandle.seek(0)

		# check if downloaded file has the correct hash
		if sha256Hash != fileHash:

			logging.error("[%s]: Temporary file does not have the "
				% self.fileName
				+ "correct hash.")

			return None

		logging.info("[%s]: Successfully downloaded file: '%s'"
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


	# internal function that gets the newest version information from the
	# online repository
	#
	# return True or False
	def _getNewestVersionInformation(self):

		conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)

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

		except Exception as e:
			logging.exception("[%s]: Getting repository information failed."
				% self.fileName)

			return False


		# parse repository information string
		try:
			jsonData = json.loads(repoInfoString)

			if not isinstance(jsonData, dict):
				raise ValueError("Received repository information is "
					+ "not of type dict.")

			if not self.instance in jsonData["instances"].keys():
				raise ValueError("Instance '%s' is not managed by "
					% self.instance
					+ "used repository.")

			self.repoInstanceLocation = str(
				jsonData["instances"][self.instance]["location"])

		except Exception as e:
			logging.exception("[%s]: Parsing repository information failed."
				% self.fileName)

			return False


		# get version string from the server
		versionString = ""
		try:

			conn.request("GET", self.serverPath + "/"
				+ self.repoInstanceLocation + "/instanceInfo.json")
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

			return False


		# parse version information string
		try:
			jsonData = json.loads(versionString)

			version = float(jsonData["version"])
			rev = int(jsonData["rev"])

			newestFiles = jsonData["files"]

			if not isinstance(newestFiles, dict):
				raise ValueError("Key 'files' is not of type dict.")

		except Exception as e:
			logging.exception("[%s]: Parsing version information failed."
				% self.fileName)

			return False

		logging.debug("[%s]: Newest version information: %.3f-%d."
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

		self.lastChecked = time.time()

		return True


	# function that gets the newest version information from the
	# online repository
	def getNewestVersionInformation(self):

		self._acquireLock()

		result = self._getNewestVersionInformation()

		self._releaseLock()

		return result


	# function that updates this instance of the alertR infrastructure
	def updateInstance(self):

		self._acquireLock()

		# check all files that have to be updated
		filesToUpdate = self._checkFilesToUpdate()

		if filesToUpdate is None:
			logging.error("[%s] Checking files for update failed."
				% self.fileName)

			self._releaseLock()

			return False

		if len(filesToUpdate) == 0:

			logging.info("[%s] No files have to be updated."
				% self.fileName)

			self._releaseLock()

			return True

		# check file permissions of the files that have to be updated
		if self._checkFilePermissions(filesToUpdate) is False:

			logging.info("[%s] Checking file permissions failed."
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

					logging.error("[%s]: Downloading files from the "
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
				raise NotImplementedError("Not yet implemented.")

			# check if the file is new
			# => create all sub directories (if they are missing)
			elif filesToUpdate[fileToUpdate] == _FileUpdateType.NEW:
				self._createSubDirectories(fileToUpdate, self.instanceLocation)

			# copy file to correct location
			try:

				logging.debug("[%s]: Copying file '%s' to alertR instance "
					% (self.fileName, fileToUpdate)
					+ "directory.")

				dest = open(self.instanceLocation + "/" + fileToUpdate, 'wb')
				shutil.copyfileobj(downloadedFileHandles[fileToUpdate], dest)
				dest.close()

			except Exception as e:
				logging.exception("[%s]: Copying file '%s' failed."
				% (self.fileName, fileToUpdate))

				self._releaseLock()

				return False

			# check if the hash of the copied file is correct
			f = open(self.instanceLocation + "/" + fileToUpdate, 'r')
			sha256Hash = self._sha256File(f)
			f.close()
			if sha256Hash != self.newestFiles[fileToUpdate]:
				logging.error("[%s]: Hash of file '%s' is not correct "
				% (self.fileName, fileToUpdate)
				+ "after copying.")

				self._releaseLock()

				return False

			# change permission of files that have to be executable
			if (fileToUpdate == "alertRclient.py"
				or fileToUpdate == "alertRserver.py"):

				logging.debug("[%s]: Changing permissions of '%s'."
					% (self.fileName, fileToUpdate))

				try:
					os.chmod(self.instanceLocation + "/" + fileToUpdate,
						stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

				except Exception as e:

					logging.exception("[%s]: Changing permissions of '%s' "
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


# this function asks the user for confirmation
def userConfirmation():

	while True:
		try:
			localInput = raw_input("(y/n): ")
		except KeyboardInterrupt:
			print "Bye."
			sys.exit(0)
		except:
			continue

		if localInput.strip().upper() == "Y":
			return True
		elif localInput.strip().upper() == "N":
			return False
		else:
			print "Invalid input."


# this function checks if the dependencies are satisfied
def checkDependencies(dependencies):

	fileName = os.path.basename(__file__)

	# check if all pip dependencies are met
	if "pip" in dependencies.keys():

		for pip in dependencies["pip"]:

			importName = pip["import"]
			packet = pip["packet"]

			# only get version if it exists
			version = None
			if "version" in pip.keys():
				version = pip["version"]

			# try to import needed module
			temp = None
			try:

				logging.info("[%s]: Checking module '%s'."
					% (fileName, importName))

				temp = importlib.import_module(importName)

			except Exception as e:
				
				logging.error("[%s]: Module '%s' not installed."
					% (fileName, importName))

				print 
				print "The needed module '%s' is not installed." % importName,
				print "You can install the module by executing",
				print "'pip install %s'" % packet,
				print "(if you do not have installed pip, you can install it",
				print "on Debian like systems by executing",
				print "'apt-get install python-pip')."

				return False


			# if a version string is given in the instance information
			# => check if the installed version satisfies the needed version
			if not version is None:

				installedVersion = temp.__version__.split(".")
				neededVersion = version.split(".")

				maxLength = 0
				if len(installedVersion) > len(neededVersion):
					maxLength = len(installedVersion)
				else:
					maxLength = len(neededVersion)

				# check the needed version and the installed version
				versionCorrect = True
				versionCheckFailed = False
				try:
					for i in range(maxLength):
						if int(installedVersion[i]) > int(neededVersion[i]):
							versionCorrect = True
							break
						elif int(installedVersion[i]) < int(neededVersion[i]):
							versionCorrect = False
							break

				except Exception as e:

					logging.error("[%s]: Could not verify installed version "
						% fileName
						+ "of module '%s'."
						% importName)

					versionCheckFailed = True

				# if the version check failed, ask the user for confirmation
				if versionCheckFailed is True:

					print 
					print "Could not automatically verify the installed",
					print "version of the module '%s'."  % importName,
					print "You have to verify the version yourself."
					print
					print "Installed version: %s" % temp.__version__
					print "Needed version: %s" % version
					print
					print "Do you have a version installed that satisfies",
					print "the needed version?"

					if not userConfirmation():
						versionCorrect = False

				# if the version is not correct => abort the next checks
				if versionCorrect is False:

					print 
					print "The needed version '%s'" % version,
					print "of module '%s' is not satisfied" % importName,
					print "(you have version '%s'" % temp.__version__,
					print "installed)."
					print "Please update your installed version of the pip",
					print "packet '%s'." % packet

					return False


	# check if all other dependencies are met
	if "other" in dependencies.keys():

		for other in dependencies["other"]:

			importName = other["import"]

			# only get version if it exists
			version = None
			if "version" in other.keys():
				version = other["version"]

			# check if the version has to be checked manually
			# (this can happen for example if the module has no
			# __version__ string or can only be imported as 'root')
			if other["manual"] is True:

				print 
				print "Can not automatically verify the installed",
				print "version of the module '%s'."  % importName,
				print "You have to verify the version and if",
				print "it is installed yourself."
				print
				print "Needed version: %s" % version
				print
				print "Do you have a version installed that satisfies",
				print "the needed version?"

				if not userConfirmation():
					versionCorrect = False

			# check the installed module automatically
			else:

				# try to import needed module
				temp = None
				try:

					logging.info("[%s]: Checking module '%s'."
						% (fileName, importName))

					temp = importlib.import_module(importName)

				except Exception as e:
					
					logging.error("[%s]: Module '%s' not installed."
						% (fileName, importName))

					print 
					print "The needed module '%s' is not" % importName,
					print "installed. You need to install it before",
					print "you can use this alertR instance."

					return False

				# if a version string is given in the instance information
				# => check if the installed version satisfies the
				# needed version
				if not version is None:

					installedVersion = temp.__version__.split(".")
					neededVersion = version.split(".")

					maxLength = 0
					if len(installedVersion) > len(neededVersion):
						maxLength = len(installedVersion)
					else:
						maxLength = len(neededVersion)

					# check the needed version and the installed version
					versionCorrect = True
					versionCheckFailed = False
					try:
						for i in range(maxLength):
							if (int(installedVersion[i]) >
								int(neededVersion[i])):
								versionCorrect = True
								break
							elif (int(installedVersion[i]) <
								int(neededVersion[i])):
								versionCorrect = False
								break

					except Exception as e:

						logging.error("[%s]: Could not verify installed "
							% fileName
							+ "version of module '%s'."
							% importName)

						versionCheckFailed = True

					# if the version check failed, ask the user
					# for confirmation
					if versionCheckFailed is True:

						print 
						print "Could not automatically verify the installed",
						print "version of the module '%s'."  % importName,
						print "You have to verify the version yourself."
						print
						print "Installed version: %s" % temp.__version__
						print "Needed version: %s" % version
						print
						print "Do you have a version installed that satisfies",
						print "the needed version?"

						if not userConfirmation():
							versionCorrect = False

					# if the version is not correct => abort the next checks
					if versionCorrect is False:

						print 
						print "The needed version '%s'" % version,
						print "of module '%s' is not satisfied" % importName,
						print "(you have version '%s'" % temp.__version__,
						print "installed)."
						print "Please update your installed version."

						return False

	return True


# this function gets the repository information data
def getRepositoryInformation(host, port, caFile, serverPath):

	fileName = os.path.basename(__file__)

	conn = VerifiedHTTPSConnection(host, port, caFile)

	logging.debug("[%s]: Downloading repository information."
		% fileName)

	# get repository information from the server
	repoInfoString = ""
	try:

		conn.request("GET", serverPath + "/repoInfo.json")
		response = conn.getresponse()

		# check if server responded correctly
		if response.status == 200:
			repoInfoString = response.read()

		else:
			raise ValueError("Server response code not 200 (was %d)."
				% response.status)

		conn.close()

	except Exception as e:
		logging.exception("[%s]: Getting repository information failed."
			% fileName)

		return None


	# parse repository information string
	try:
		jsonData = json.loads(repoInfoString)

		if not isinstance(jsonData, dict):
			raise ValueError("Received repository information is "
				+ "not of type dict.")

		if not "instances" in jsonData.keys():
			raise ValueError("Received repository information has "
				+ "no information about the instances.")

	except Exception as e:
		logging.exception("[%s]: Parsing repository information failed."
			% fileName)

		return None

	return jsonData


# this function gets the instance information data
def getInstanceInformation(host, port, caFile, serverPath,
	repoInstanceLocation):

	fileName = os.path.basename(__file__)

	conn = VerifiedHTTPSConnection(host, port, caFile)

	logging.debug("[%s]: Downloading instance information."
		% fileName)

	# get instance information string from the server
	instanceInfoString = ""
	try:

		conn.request("GET", serverPath + "/"
			+ repoInstanceLocation + "/instanceInfo.json")
		response = conn.getresponse()

		# check if server responded correctly
		if response.status == 200:
			instanceInfoString = response.read()

		else:
			raise ValueError("Server response code not 200 (was %d)."
				% response.status)

		conn.close()

	except Exception as e:
		logging.exception("[%s]: Getting version information failed."
			% fileName)

		return None


	# parse instance information string
	try:
		jsonData = json.loads(instanceInfoString)

		version = float(jsonData["version"])
		rev = int(jsonData["rev"])

		dependencies = jsonData["dependencies"]

		if not isinstance(dependencies, dict):
			raise ValueError("Key 'dependencies' is not of type dict.")

	except Exception as e:
		logging.exception("[%s]: Parsing version information failed."
			% fileName)

		return None

	return jsonData


# this function lists all available instances
def listAllInstances(host, port, caFile, serverPath):

	# download repository information
	repoInfo = getRepositoryInformation(host, port, caFile, serverPath)
	if repoInfo is None:
		return False

	temp = repoInfo["instances"].keys()
	temp.sort()

	print

	for instance in temp:

		instanceInfo = getInstanceInformation(host, port, caFile, serverPath,
			repoInfo["instances"][instance]["location"])

		print repoInfo["instances"][instance]["name"]
		print "-"*len(repoInfo["instances"][instance]["name"])
		print "Instance:"
		print instance
		print
		print "Type:"
		print repoInfo["instances"][instance]["type"]
		print
		print "Version:"
		print "%.3f-%d" % (instanceInfo["version"], instanceInfo["rev"])
		print
		print "Dependencies:"

		# print instance dependencies
		idx = 1
		if "pip" in instanceInfo["dependencies"].keys():			
			for pip in instanceInfo["dependencies"]["pip"]:
				importName = pip["import"]
				packet = pip["packet"]
				print "%d: %s (pip packet: %s)" % (idx, importName, packet),
				if "version" in pip.keys():
					print "(lowest version: %s)" % pip["version"]
				else:
					print
				idx += 1

		if "other" in instanceInfo["dependencies"].keys():
			for other in instanceInfo["dependencies"]["other"]:
				importName = other["import"]
				print "%d: %s" % (idx, importName),
				if "version" in other.keys():
					print "(lowest version: %s)" % other["version"]
				else:
					print
				idx += 1

		if idx == 1:
			print "None"

		print
		print "Description:"
		print repoInfo["instances"][instance]["desc"]

		print
		print


# this function makes a clean exit
def exit(exitCode, caFile):

	# remove temporary ca file
	try:
		os.remove(caFile)
	except Exception as e:
		logging.error("[%s]: Could not remove temporary "
			% fileName
			+ "certificate file.")

	sys.exit(exitCode)


if __name__ == '__main__':

	# initialize logging
	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
		datefmt='%m/%d/%Y %H:%M:%S', level=loglevel)

	fileName = os.path.basename(__file__)

	# create ca file used to connect to the repository
	# (unfortunately, because of the ssl api this is prone for a
	# race condition => exchange ca file before it is used to download
	# the client to connect to a malicious server)
	tempFileTuple = tempfile.mkstemp()
	caFileHandle = os.fdopen(tempFileTuple[0], "w")
	caFileHandle.write(caCertificate)
	caFileHandle.close()
	caFile = tempFileTuple[1]


	# parsing command line options
	parser = optparse.OptionParser()

	parser.formatter = optparse.TitledHelpFormatter()

	parser.description = "Downloads an alertR instance from the " \
		+ "online repository."

	parser.epilog = "Example command to install the alertR server instance: " \
		+ "\t\t\t\t\t\t\t\t\t\t" \
		+ "'python %s -i server -t /home/alertr/' " % sys.argv[0] \
		+ "\t\t\t\t\t\t\t\t\t\t" \
		+ "Example command to list all available alertR instances: " \
		+ "\t\t\t\t\t\t\t\t\t\t" \
		+ "'python %s -l' " % sys.argv[0] \
		+ "\t\t\t\t\t\t\t\t\t\t" \
		+ "For more detailed examples how to install an alertR instance " \
		+ "please visit: " \
		+ "\t\t\t\t\t\t\t\t\t\t" \
		+ "https://github.com/sqall01/alertR/wiki/Example-configuration"

	installationGroup = optparse.OptionGroup(parser,
		"Arguments needed to install an alertR instance")
	installationGroup.add_option("-i",
		"--instance",
		dest="instance",
		action="store",
		help="Instance that should be installed (use --list to get a list "
			+ "of all available alertR instances). (Required)",
		default=None)
	installationGroup.add_option("-t",
		"--target",
		dest="targetDirectory",
		action="store",
		help="The target directory into which the chosen alertR instance"
			+ " should be installed. (Required)",
		default=None)
	installationGroup.add_option("-f",
		"--force",
		dest="force",
		action="store_true",
		help="Do not check the dependencies. Just install it. (Optional)",
		default=False)

	listGroup = optparse.OptionGroup(parser,
		"Show information about the online repository")
	listGroup.add_option("-l",
		"--list",
		dest="list",
		action="store_true",
		help="List all available alertR instances in the repository.",
		default=False)

	parser.add_option_group(installationGroup)
	parser.add_option_group(listGroup)

	(options, args) = parser.parse_args()


	# list all available instances in the used alertR repository
	if options.list is True:

		if listAllInstances(host, port, caFile, serverPath) is False:

			print
			print "Could not list repository information."

			exit(1, caFile)

		exit(0, caFile)


	# install the chosen alertR instance
	elif (not options.instance is None
		and not options.targetDirectory is None):

		instance = options.instance
		targetLocation = options.targetDirectory

		# check if path is an absolute or relative path (and add trailing '/')
		if targetLocation[:1] != "/":
			targetLocation = os.path.dirname(os.path.abspath(__file__)) \
			+ "/" + targetLocation + "/"
		else:
			targetLocation += "/"

		# check if the chosen target location does exist
		if (os.path.exists(targetLocation) is False
			or os.path.isdir(targetLocation) is False):

			print
			print "Chosen target location does not exist."

			exit(1, caFile)

		# get the repository information
		repoInfo = getRepositoryInformation(host, port, caFile, serverPath)
		if repoInfo is None:

			print
			print "Could not download repository information from repository."

			exit(1, caFile)

		# get the correct case of the instance to install
		found = False
		for repoKey in repoInfo["instances"].keys():
			if repoKey.upper() == instance.upper():
				instance = repoKey
				found = True
				break

		# check if chosen instance exists
		if not found:
			
			print
			print "Chosen alertR instance '%s'" % instance,
			print "does not exist in repository."

			exit(1, caFile)

		try:
			repoInstanceLocation = \
				str(repoInfo["instances"][instance]["location"])
		except Exception as e:
			
			logging.exception("[%s]: Could not get location information for "
				% fileName
				+ "chosen instance.")

			print
			print "Location of chosen instance not in repository information."

			exit(1, caFile)

		# get the instance information
		instanceInfo = getInstanceInformation(host, port,
			caFile, serverPath, repoInstanceLocation)
		if instanceInfo is None:

			print
			print "Could not download instance information from repository."

			exit(1, caFile)

		# extract needed data from instance information
		version = float(instanceInfo["version"])
		rev = int(instanceInfo["rev"])
		dependencies = instanceInfo["dependencies"]


		logging.info("[%s]: Checking the dependencies." % fileName)

		# check all dependencies this instance needs
		if options.force is False:
			if not checkDependencies(dependencies):
				exit(1, caFile)
		else:
			logging.info("[%s]: Ignoring dependency check. "
				% fileName
				+ "Forcing installation.")


		# install the chosen alertR instance
		installer = Updater(host, port, serverPath, caFile, instance,
			targetLocation)
		if installer.updateInstance() is False:

			logging.error("[%s]: Installation failed." % fileName)

			print
			print "INSTALLATION FAILED!"
			print "To see the reason take a look at the installation",
			print "process output.",
			print "You can change the log level in the",
			print "file to 'DEBUG'",
			print "and repeat the installation process to get more detailed",
			print "information."
			exit(1, caFile)

		else:

			print
			print "INSTALLATION SUCCESSFUL!"
			print "Please configure this alertR instance before you start it."

		exit(0, caFile)


	# no option chosen
	else:
		print "Use --help to get all available options."

		exit(0, caFile)