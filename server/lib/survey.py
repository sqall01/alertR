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
import urllib
import time
import threading
import os
import json
import logging


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
			ca_certs=self.servercert_file, server_side=False)


# this class participates in the alertR survey (if it is activated)
class SurveyExecuter(threading.Thread):

	def __init__(self, updateActivated, updateServer, updateLocation,
		globalData):
		threading.Thread.__init__(self)

		# used for logging
		self.fileName = os.path.basename(__file__)

		# get global configured data
		self.globalData = globalData
		self.storage = self.globalData.storage
		self.instance = self.globalData.instance
		self.version = self.globalData.version
		self.rev = self.globalData.rev
		self.updateActivated = updateActivated
		self.updateServer = updateServer
		self.updateLocation = updateLocation

		# fixed values for survey
		self.surveyInterval = 604800 # week
		self.host = "survey.alertr.de"
		self.port = "444"
		self.caFile = os.path.dirname(os.path.abspath(
			__file__)) + "/../config/survey.alertr.de.crt"


	# gather and send survey data
	def sendSurveyData(self):

		logging.info("[%s]: Starting to send survey data."
				% self.fileName)

		# gather survey data
		surveyNodes = self.storage.getSurveyData()
		if surveyNodes is None:

			logging.error("[%s]: Did not get any survey data from "
				% self.fileName
				+ "the database.")
			return False
		surveyData = dict()
		surveyData["nodes"] = surveyNodes
		
		surveyUpdate = dict()
		surveyUpdate["activated"] = self.updateActivated
		surveyUpdate["server"] = self.updateServer
		surveyUpdate["location"] = self.updateLocation
		surveyData["update"] = surveyUpdate

		surveyData["uniqueID"] = self.storage.getUniqueID()

		# send survey data to server
		conn = VerifiedHTTPSConnection(self.host, self.port, self.caFile)
		try:

			headers = {"Connection": "keep-alive", 
				"Content-type": "application/x-www-form-urlencoded", 
				"Accept": "text/plain"}
			data = urllib.urlencode({
				'data': json.dumps(surveyData)})

			conn.request("POST", "/submit.php", data, headers)
			response = conn.getresponse()

			# check if server responded correctly
			if response.status != 200:
				raise ValueError("Server response code not 200 (was %d)."
					% response.status)

			data = response.read()
			if data != "ok":
				raise ValueError("Server responded with error: %s." % data)

		except Exception as e:
			logging.exception("[%s]: Sending survey data failed."
				% self.fileName)

			return False

		logging.info("[%s]: Survey data successfully sent."
				% self.fileName)

		return True


	def run(self):

		while True:

			# sleep for the interval before participating to the survey
			time.sleep(self.surveyInterval)

			self.sendSurveyData()