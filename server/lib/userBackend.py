#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import csv
import logging
import os


# internal abstract class for new user backends
class _userBackend():

	# this function checks if the user credentials are valid
	#
	# return True or False
	def areUserCredentialsValid(self, username, password):
		raise NotImplemented("Function not implemented yet.")


	# this function checks if the node type and instance of the client
	# is correct
	#
	# return True or False
	def checkNodeTypeAndInstance(self, username, nodeType, instance):
		raise NotImplemented("Function not implemented yet.")


# user backend that uses a simple csv file
# in the form of "username, password" per line
class CSVBackend(_userBackend):

	def __init__(self, globalData, csvLocation):

		self.globalData = globalData
		self.logger = self.globalData.logger

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# stores all user credentials as a tuple of values (username, password)
		self.userCredentials = list()

		# parse csv file and store all user credentials
		with open(csvLocation, 'rb') as csvFile:
			csvReader = csv.reader(csvFile, quoting=csv.QUOTE_ALL)
			for row in csvReader:
				if len(row) != 4:
					continue
				if row[0].find('#') != -1:
					continue

				username = row[0].replace(' ', '')
				password = row[1].replace(' ', '')
				nodeType = row[2].replace(' ', '')
				instance = row[3].replace(' ', '')

				# check if username has a duplicate
				if any(map(lambda x : x[0] == username,
					self.userCredentials)):

					self.logger.error("[%s]: Username '%s' already exists "
						% (self.fileName, logString)
						+ "in CSV file.")

					continue

				self.userCredentials.append( (username,
					password,
					nodeType,
					instance) )


	# this function checks if the user credentials are valid
	#
	# return True or False
	def areUserCredentialsValid(self, username, password):

		# check all usernames if the given username exist
		# and then if the password is the correct one
		for storedTuple in self.userCredentials:

			if storedTuple[0] != username:
				continue

			else:
				if storedTuple[1] == password:
					return True
				else:
					return False

		return False


	# this function checks if the node type and instance of the client
	# is correct
	#
	# return True or False
	def checkNodeTypeAndInstance(self, username, nodeType, instance):

		# check all usernames if the given username exist
		# and then check the given node type and instance
		for storedTuple in self.userCredentials:

			if storedTuple[0] != username:
				continue

			else:
				if (storedTuple[2].upper() == nodeType.upper()
					and storedTuple[3].upper() == instance.upper()):
					return True
				else:
					return False

		return False