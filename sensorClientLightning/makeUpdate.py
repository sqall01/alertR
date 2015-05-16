#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import sys
import os
from lib import GlobalData
from lib import UpdateChecker
from lib import Updater
import xml.etree.ElementTree
import logging


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


if __name__ == '__main__':

	majorUpdate = False

	# generate object of the global needed data
	globalData = GlobalData()

	fileName = os.path.basename(__file__)
	instanceLocation = os.path.dirname(os.path.abspath(__file__)) + "/"

	try:
		# parse config file
		configRoot = xml.etree.ElementTree.parse(instanceLocation +
			"/config/config.xml").getroot()

		# parse chosen log level
		tempLoglevel = str(
			configRoot.find("general").find("log").attrib["level"])
		tempLoglevel = tempLoglevel.upper()
		if tempLoglevel == "DEBUG":
			loglevel = logging.DEBUG
		elif tempLoglevel == "INFO":
			loglevel = logging.INFO
		elif tempLoglevel == "WARNING":
			loglevel = logging.WARNING
		elif tempLoglevel == "ERROR":
			loglevel = logging.ERROR
		elif tempLoglevel == "CRITICAL":
			loglevel = logging.CRITICAL
		else:
			raise ValueError("No valid log level in config file.")

		# initialize logging
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
			datefmt='%m/%d/%Y %H:%M:%S', level=loglevel)

	except Exception as e:
		print "Config could not be parsed."
		print e
		sys.exit(1)

	# parse the rest of the config with initialized logging
	try:

		# check if config and client version are compatible
		configVersion = float(configRoot.attrib["version"])
		if configVersion != globalData.version:
			raise ValueError("Config version '%.3f' not "
				% configVersion
				+ "compatible with client version '%.3f'."
				% globalData.version)

		# parse update options
		updateActivated = (str(
			configRoot.find("update").find("general").attrib[
			"activated"]).upper() == "TRUE")
		updateServer = str(
			configRoot.find("update").find("server").attrib["host"])
		updatePort = int(
			configRoot.find("update").find("server").attrib["port"])
		updateLocation = str(
			configRoot.find("update").find("server").attrib["location"])
		updateCaFile = str(
			configRoot.find("update").find("server").attrib["caFile"])
		updateInterval = int(
			configRoot.find("update").find("general").attrib["interval"])

		# when automatic update is not activated
		# => ask before continuing
		if updateActivated is False:
			print
			print "NOTE: Automatic checking for updates is deactivated.",
			print "Please, make sure you configured the update section of",
			print "the configuration file correctly."
			print "Do you want to continue the update process?"

			if userConfirmation() is False:
				print "Bye."
				sys.exit(0)

	except Exception as e:
		logging.exception("[%s]: Could not parse config." % fileName)
		sys.exit(1)

	logging.info("[%s]: Current version: %.3f-%d." %
		(fileName, globalData.version, globalData.rev))

	# create an updater process
	updater = Updater(updateServer, updatePort, updateLocation,
		updateCaFile, globalData)

	# get newest version information
	if updater.getNewestVersionInformation() is False:
		sys.exit(1)

	# check if the received version is newer than the current one
	if (updater.newestVersion > globalData.version or
		(updater.newestRev > globalData.rev
		and updater.newestVersion == globalData.version)):

		# check if update is a major update (this means that
		# the config and/or protocol has changed)
		# => notify user and ask for confirmation
		if updater.newestVersion > globalData.version:

			majorUpdate = True

			print
			print "WARNING: You are about to make a major update.", 
			print "This means that the configuration and/or the protocol has",
			print "changed. Therefore, after you have updated this alertR",
			print "instance you also have to update your alertR server and",
			print "all your alertR clients in order to have a working",
			print "system again."
			print "Are you sure you want to continue and update this",
			print "alertR instance?"

			if userConfirmation() is False:
				print "Bye."
				sys.exit(0)

		print
		print "Please make sure that this alertR instance is stopped before",
		print "continuing the update process."
		print "Are you sure this alertR instance is not running?"
		if userConfirmation() is False:
			print "Bye."
			sys.exit(0)

		if updater.updateInstance() is False:

			logging.error("[%s]: Update failed." % fileName)

			print
			print "UPDATE PROCESS FAILED!"
			print "To see the reason take a look at the update",
			print "process output.",
			print "You can change the log level in the configuration",
			print "file to 'DEBUG'",
			print "and repeat the update process to get more detailed",
			print "information."
			sys.exit(1)

		logging.info("[%s]: Update finished." % fileName)

		print
		print "UPDATE FINISHED!"

		if majorUpdate:
			print "Please make sure to update your configuration file",
			print "and to update all other alertR instances before starting",
			print "this alertR instance."

		else:
			print "Please start this alertR instance now."

	else:
		logging.info("[%s]: No new version available." % fileName)

		print
		print "SKIPPING UPDATE!"
		print "No new version is available in the configured repository."

		sys.exit(0)