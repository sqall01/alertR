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