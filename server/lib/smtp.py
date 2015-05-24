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
import time


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
		self.fileName = os.path.basename(__file__)

		# this is the general email address problems are sent to
		# (this does not include sensor alerts => these email addresses
		# are separately configured for each alert level)
		self.toAddr = toAddr

		# this values keep track about the update available
		# notifications that were already sent (this prevents email flodding)
		self.newestVersion = None
		self.newestRev = None


	# this function sends an email alert in case of
	# a sensor alert
	def sendSensorAlert(self, hostname, description, timeReceived, toAddr):

		subject = "[alertR] (%s) Sensor alert triggered" \
			% hostname

		message = "A sensor alert was triggered by '%s' on %s. " \
			% (hostname,
			time.strftime("%D %H:%M:%S", time.localtime(timeReceived))) \
			+ "The description of the sensor is '%s'." \
			% description

		emailHeader = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" \
			% (self.fromAddr, toAddr, subject)

		# sending eMail alert to configured smtp server
		logging.info("[%s]: Sending eMail alert to %s." 
			% (self.fileName, toAddr))
		try:

			smtpServer = smtplib.SMTP(self.host, self.port)
			smtpServer.sendmail(self.fromAddr, toAddr, 
				emailHeader + message)
			smtpServer.quit()
		except Exception as e:
			logging.exception("[%s]: Unable to send eMail alert. " 
				% self.fileName)
			return False

		return True


	# this function sends an email alert in case of
	# a sensor alert is triggered for an alert level with an activated rule
	def sendSensorAlertRulesActivated(self, alertLevelName, timeTriggered,
		toAddr):

		subject = "[alertR] Alert level rule triggered"

		message = "The rule of the alert level '%s' " % alertLevelName \
			+ "triggered on %s." \
			% time.strftime("%D %H:%M:%S", time.localtime(timeTriggered))

		emailHeader = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" \
			% (self.fromAddr, toAddr, subject)

		# sending eMail alert to configured smtp server
		logging.info("[%s]: Sending eMail alert to %s." 
			% (self.fileName, toAddr))
		try:

			smtpServer = smtplib.SMTP(self.host, self.port)
			smtpServer.sendmail(self.fromAddr, toAddr, 
				emailHeader + message)
			smtpServer.quit()
		except Exception as e:
			logging.exception("[%s]: Unable to send eMail alert. " 
				% self.fileName)
			return False

		return True


	# this function sends an email alert in case of
	# a timed out sensor
	def sendSensorTimeoutAlert(self, hostname, description, lastStateUpdated):

		subject = "[alertR] (%s) Sensor timed out" \
			% hostname

		message = "A sensor timed out from '%s'. " \
			% hostname \
			+ "The Description of the sensor is '%s'. " \
			% description \
			+ "The last state was received at: %s" \
			% time.strftime("%D %H:%M:%S", time.localtime(lastStateUpdated))

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

		return True


	# this function sends an email in case of
	# a sensor time out failure was cleared
	def sendSensorTimeoutAlertClear(self, hostname, description,
		lastStateUpdated):

		subject = "[alertR] (%s) Sensor timeout problem solved" \
			% socket.gethostname()

		message = "A new state from the sensor of the host '%s' with " \
			% hostname \
			+ "the description '%s' " \
			% description \
			+ "has been received at: %s" \
			% time.strftime("%D %H:%M:%S", time.localtime(lastStateUpdated))

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
	# a new version is available for this instance
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
				+ "file. This means that you have to manually update your " \
				+ "used configuration file before you can use this alertR " \
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