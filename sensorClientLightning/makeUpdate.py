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


if __name__ == '__main__':

	# generate object of the global needed data
	globalData = GlobalData()

	fileName = os.path.basename(__file__)

	try:
		# parse config file
		configRoot = xml.etree.ElementTree.parse(
			"./config/config.xml").getroot()

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
			print "NOTE: Automatic checking for updates is deactivated."
			print "Please, make sure you configured the update section of " \
				+ "the config file correctly. Do you want to continue the " \
				+ "update process?"

			while True:
				try:
					localInput = raw_input("(y/n): ")
				except KeyboardInterrupt:
					print "Bye."
					sys.exit(0)
				except:
					continue

				if localInput.strip().upper() == "Y":
					break
				elif localInput.strip().upper() == "N":
					print "Bye."
					sys.exit(0)
				else:
					print "Invalid input."

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


		# TODO

		print "NEWER"


		print updater.newestFiles






	else:
		logging.error("[%s]: No new version available." % fileName)
		sys.exit(0)


