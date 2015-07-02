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


# this class handles the version information for a given instance
class VersionInformation:

	def __init__(self, host, port, serverPath, caFile, instance,
		repoInstanceLocation):

		# used for logging
		self.fileName = os.path.basename(__file__)

		# the updater object is not thread safe
		self.versionInformerLock = threading.Semaphore(1)

		# get global configured data
		self.instance = instance
		
		# location of this instance
		self.instanceLocation = os.path.dirname(os.path.abspath(__file__)) \
			+ "/../"

		# set update server configuration
		self.host = host
		self.port = port
		self.serverPath = serverPath
		self.caFile = caFile
		self.repoInstanceLocation = repoInstanceLocation

		# needed to keep track of the newest version
		self.newestVersion = -1.0
		self.newestRev = -1
		

	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.versionInformerLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
		self.versionInformerLock.release()


	# internal function that gets the newest version information from the
	# online repository
	#
	# return True or False
	def _getNewestVersionInformation(self):

		conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)

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
			logging.exception("[%s]: Getting version information "
				% self.fileName
				+ "for instance '%s' failed."
				% self.instance)

			return False


		# parse version information string
		try:
			jsonData = json.loads(versionString)

			version = float(jsonData["version"])
			rev = int(jsonData["rev"])

		except Exception as e:
			logging.exception("[%s]: Parsing version information"
				% self.fileName
				+ "for instance '%s' failed."
				% self.instance)

			return False

		logging.debug("[%s]: Newest version information for instance '%s': "
			% (self.fileName, self.instance)
			+ "%.3f-%d."
			% (version, rev))

		# check if the version on the server is newer than the used one
		# => update information
		if (version > self.newestVersion or
			(rev > self.newestRev and version == self.newestVersion)):

			# update newest known version information
			self.newestVersion = version
			self.newestRev = rev

		return True


	# function that gets the newest version information from the
	# online repository
	def getNewestVersionInformation(self):

		self._acquireLock()

		result = self._getNewestVersionInformation()

		self._releaseLock()

		return result


# this class checks in specific intervals for new versions of all available
# instances in the given repository
class VersionInformer(threading.Thread):

	def __init__(self, host, port, serverPath, caFile, interval, globalData):
		threading.Thread.__init__(self)

		# used for logging
		self.fileName = os.path.basename(__file__)

		# set update server configuration
		self.host = host
		self.port = port
		self.serverPath = serverPath
		self.caFile = caFile

		# get global configured data
		self.globalData = globalData
		self.nodes = self.globalData.nodes

		# set interval for update checking
		self.checkInterval = interval

		self.repoLocations = dict()
		self.repoVersions = dict()


	def run(self):

		while True:

			time.sleep(self.checkInterval)

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
				logging.exception("[%s]: Getting repository information "
					% self.fileName
					+ "failed.")

				continue


			# parse repository information string
			try:
				jsonData = json.loads(repoInfoString)

				if not isinstance(jsonData, dict):
					raise ValueError("Received repository information is "
						+ "not of type dict.")

				# store the information about the repository instances
				self.repoLocations = dict()
				for instance in jsonData["instances"].keys():
					self.repoLocations[instance] \
						= jsonData["instances"][instance]["location"]


			except Exception as e:
				logging.exception("[%s]: Parsing repository information "
					% self.fileName
					+ "failed.")

				continue


			# update the locations of all version information objects 
			# for all instances in the repository
			for repoInstance in self.repoLocations.keys():

				# if instance version information object already exists
				# => only update repository location
				if repoInstance in self.repoVersions.keys():
					self.repoVersions[repoInstance].repoInstanceLocation \
						= self.repoLocations[repoInstance]

				# => add version information object for the current instance
				else:

					verInfoObj = VersionInformation(self.host, self.port,
						self.serverPath, self.caFile, repoInstance,
						self.repoLocations[repoInstance])
					self.repoVersions[repoInstance] = verInfoObj

			# check if instances were removed from the repository
			# and remove them
			for repoInstance in self.repoVersions.keys():
				if not repoInstance in self.repoLocations.keys():
					del self.repoVersions[repoInstance]

			# get the version information of all version information objects
			for repoInstance in self.repoVersions.keys():

				verInfoObj = self.repoVersions[repoInstance]
				if not verInfoObj.getNewestVersionInformation():

					logging.exception("[%s]: Getting version information "
					% self.fileName
					+ "for instance '%s' failed."
					% verInfoObj.instance)