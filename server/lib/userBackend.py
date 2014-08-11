#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import csv

# internal abstract class for new user backends
class _userBackend():
	
	# this function checks if the user credentials are valid
	#
	# return True or False
	def areUserCredentialsValid(self, username, password):
		raise NotImplemented("Function not implemented yet.")


# user backend that uses a simple csv file
# in the form of "username, password" per line
class CSVBackend(_userBackend):

	def __init__(self, csvLocation):

		# stores all user credentials as a tuple of values (username, password)
		self.userCredentials = list()

		# parse csv file and store all user credentials
		with open(csvLocation, 'rb') as csvFile:
			csvReader = csv.reader(csvFile, quoting=csv.QUOTE_ALL)
			for row in csvReader:
				if len(row) != 2:
					continue
				if row[0].find('#') != -1:
					continue

				username = row[0].replace(' ', '')
				password = row[1].replace(' ', '')

				self.userCredentials.append( (username, password) )


	# this function checks if the user credentials are valid
	#
	# return True or False
	def areUserCredentialsValid(self, username, password):

		# check all usernames if the given username exist
		# and then if the password is the correct one
		for storedUsername, storedPassword in self.userCredentials:

			if storedUsername != username:
				continue

			else:
				if storedPassword == password:
					return True
				else:
					return False

		return False