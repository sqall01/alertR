#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import smtplib
import logging
import os
import socket


# this class handles the eMail alerts that are sent via smtp
class SMTPAlert:

	def __init__(self, host, port, fromAddr, toAddr):

		if (host != "127.0.0.1" 
			or port != 25):
			raise NotImplementedError('Only host "127.0.0.1" and '
				+ 'port "25" is implemented')

		self.host = host
		self.port = port
		self.fromAddr = fromAddr
		self.toAddr = toAddr
		self.fileName = os.path.basename(__file__)

		# this flag indicates that a communication alert
		# was already sent (this prevents email flodding)
		self.communicationAlertSent = False

		# this flag indicates that an update check alert
		# was already sent (this prevents email flodding)
		self.updateFailureAlertSent = False

		# this values keep track about the update available
		# notifications that were already sent (this prevents email flodding)
		self.newestVersion = None
		self.newestRev = None


	# this function sends an email alert in case of
	# a communication failure
	def sendCommunicationAlert(self, connectionRetries):

		if self.communicationAlertSent:
			return True

		subject = "[alertR] (%s) Communication problems detected" \
			% socket.gethostname()

		message = "Communication problems detected between the host '%s' " \
			% socket.gethostname() \
			+ "and the server. The host '%s' was not able to establish " \
			% socket.gethostname() \
			+ "a connection after %d retries." \
			% connectionRetries

		emailHeader = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" \
			% (self.fromAddr, self.toAddr, subject)

		# sending eMail alert to configured smtp server
		logging.info("[%s]: Sending eMail alert to %s." 
			% (self.fileName, self.toAddr))
		try:
			smtpServer = smtplib.SMTP(self.host, self.port)
			smtpServer.sendmail(self.fromAddr, self.toAddr, 
				emailHeader + message)
			smtpServer.quit()
		except Exception as e:
			logging.exception("[%s]: Unable to send eMail alert. " 
				% self.fileName)
			return False

		# set flag that a communication alert was sent before exiting
		self.communicationAlertSent = True

		return True


	# this function sends an email in case of
	# a communication failure was cleared
	def sendCommunicationAlertClear(self):

		if not self.communicationAlertSent:
			return True

		subject = "[alertR] (%s) Communication problems solved" \
			% socket.gethostname()

		message = "The communication problems between the host '%s' " \
			% socket.gethostname() \
			+ "and the server were solved."

		emailHeader = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" \
			% (self.fromAddr, self.toAddr, subject)

		# sending eMail alert to configured smtp server
		logging.info("[%s]: Sending eMail alert to %s." 
			% (self.fileName, self.toAddr))
		try:
			smtpServer = smtplib.SMTP(self.host, self.port)
			smtpServer.sendmail(self.fromAddr, self.toAddr, 
				emailHeader + message)
			smtpServer.quit()
		except Exception as e:
			logging.exception("[%s]: Unable to send eMail alert. " 
				% self.fileName)
			return False

		# clear flag that a communication alert was sent before exiting
		self.communicationAlertSent = False

		return True


	# this function sends an email in case of
	# a problem with the update check
	def sendUpdateCheckFailureAlert(self, updateFailCount, clientName):

		if self.updateFailureAlertSent:
			return True

		subject = "[alertR] Update check problems detected"

		message = "Problems detected on the client '%s' on host '%s'. " \
			% (clientName, socket.gethostname()) \
			+ "The client was not able to check for an update for %d times " \
			% updateFailCount \
			+ "in a row."

		emailHeader = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" \
			% (self.fromAddr, self.toAddr, subject)

		# sending eMail alert to configured smtp server
		logging.info("[%s]: Sending eMail alert to %s." 
			% (self.fileName, self.toAddr))
		try:
			smtpServer = smtplib.SMTP(self.host, self.port)
			smtpServer.sendmail(self.fromAddr, self.toAddr, 
				emailHeader + message)
			smtpServer.quit()
		except Exception as e:
			logging.exception("[%s]: Unable to send eMail alert. " 
				% self.fileName)
			return False

		# set flag that an update check problem alert was sent before exiting
		self.updateFailureAlertSent = True

		return True


	# this function sends an email in case of
	# a problem with the update check was cleared
	def sendUpdateCheckFailureAlertClear(self, updateFailCount, clientName):

		if not self.updateFailureAlertSent:
			return True

		subject = "[alertR] Update check problems solved"

		message = "The problems with the update check on the client " \
			+ "'%s' on host '%s' were solved after %d attempts." \
			% (clientName, socket.gethostname(), updateFailCount)

		emailHeader = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" \
			% (self.fromAddr, self.toAddr, subject)

		# sending eMail alert to configured smtp server
		logging.info("[%s]: Sending eMail alert to %s." 
			% (self.fileName, self.toAddr))
		try:
			smtpServer = smtplib.SMTP(self.host, self.port)
			smtpServer.sendmail(self.fromAddr, self.toAddr, 
				emailHeader + message)
			smtpServer.quit()
		except Exception as e:
			logging.exception("[%s]: Unable to send eMail alert. " 
				% self.fileName)
			return False

		# clear flag that an update check problem alert was sent before exiting
		self.updateFailureAlertSent = False

		return True


	# this function sends an email in case of
	# a new version is available for this client
	def sendUpdateCheckNewVersion(self, currVersion, currRev, version,
		rev, clientName):

		if (self.newestVersion >= version
			and self.newestRev >= rev):
			return True

		# check if the update changes the protocol
		protocolUpdate = False
		if int(version * 10) > int(currVersion * 10):
			protocolUpdate = True

		# check if the update changes the configuration file
		configUpdate = False
		if version > currVersion:
			configUpdate = True

		subject = "[alertR] Update available"

		message = "For the instance '%s' on host '%s' is a new version " \
			% (clientName, socket.gethostname()) \
			+ "available.\n\n" \
			+ "Current version: %.3f-%d\n" \
			% (currVersion, currRev) \
			+ "New version: %.3f-%d\n" \
			% (version, rev)

		# add additional information if the protocol changes after the update
		if protocolUpdate is True:
			message += "\n" \
				+ "NOTE: The update changes the used protocol. This means " \
				+ "that when you update this alertR instance " \
				+ "you also have to update all your other alertR instances " \
				+ "in order to have a working system again." \
				+ "\n"

		# add additional information if the configuration changes
		# after the update
		if configUpdate is True:
			message += "\n" \
				+ "NOTE: The update needs changes in the used configuration " \
				+ "file. This means that when you update this alertR " \
				+ "instance, you have to manually update your " \
				+ "used configuration file before you can start this alertR " \
				+ "instance again." \
				+ "\n"

		emailHeader = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" \
			% (self.fromAddr, self.toAddr, subject)

		# sending eMail alert to configured smtp server
		logging.info("[%s]: Sending eMail alert to %s." 
			% (self.fileName, self.toAddr))
		try:
			smtpServer = smtplib.SMTP(self.host, self.port)
			smtpServer.sendmail(self.fromAddr, self.toAddr, 
				emailHeader + message)
			smtpServer.quit()
		except Exception as e:
			logging.exception("[%s]: Unable to send eMail alert. " 
				% self.fileName)
			return False

		# store the new version and revision
		self.newestVersion = version
		self.newestRev = rev

		return True