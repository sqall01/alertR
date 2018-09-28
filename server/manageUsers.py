#!/usr/bin/python

from lib import CSVBackend
from lib import GlobalData
from lib import Updater
import logging
import xml.etree.ElementTree
import sys
import os
import optparse
import getpass


# Function creates a path location for the given user input.
def makePath(inputLocation):
	# Do nothing if the given location is an absolute path.
	if inputLocation[0] == "/":
		return inputLocation
	# Replace ~ with the home directory.
	elif inputLocation[0] == "~":
		return os.environ["HOME"] + inputLocation[1:]
	# Assume we have a given relative path.
	return os.path.dirname(os.path.abspath(__file__)) + "/" + inputLocation


# Function that asks user for node type and instance.
def chooseNodeTypeAndInstance(updater):

	nodeType = None
	instance = None

	# Only contact online repository when we are not set as working offline.
	repoInfo = {"instances": {}}
	if updater is not None:
		try:
			repoInfo = updater.getRepositoryInformation()
		except Exception as e:
			logging.exception("[%s]: Not able to contact online repository."
				% fileName)

		choiceList = filter(lambda x: x.lower() != "server",
			repoInfo["instances"].keys())
		choiceList.sort()

		alerts = list()
		managers = list()
		sensors = list()
		others = list()
		for instanceIter in choiceList:
			currType = repoInfo["instances"][instanceIter]["type"]
			if currType == "alert":
				alerts.append(instanceIter)
			elif currType == "manager":
				managers.append(instanceIter)
			elif currType == "sensor":
				sensors.append(instanceIter)
			else:
				others.append(instanceIter)
		
		# Create a list of all instances in the exact order in which
		# we output them.
		allInstances = list()

		print("#"*100)
		print("No.".ljust(5) + "| Option")
		print("#"*100)

		ctr = 1
		headline = " Type: alert "
		print("-"*40 + headline + "-"*(60-len(headline)))
		for instanceIter in alerts:
			output = "%d." % ctr
			output = output.ljust(5) + "| "
			output += "Use instance '%s'." % instanceIter
			print(output)
			ctr += 1
			allInstances.append(instanceIter)

		headline = " Type: manager "
		print("-"*40 + headline + "-"*(60-len(headline)))
		for instanceIter in managers:
			output = "%d." % ctr
			output = output.ljust(5) + "| "
			output += "Use instance '%s'." % instanceIter
			print(output)
			ctr += 1
			allInstances.append(instanceIter)

		headline = " Type: sensor "
		print("-"*40 + headline + "-"*(60-len(headline)))
		for instanceIter in sensors:
			output = "%d." % ctr
			output = output.ljust(5) + "| "
			output += "Use instance '%s'." % instanceIter
			print(output)
			ctr += 1
			allInstances.append(instanceIter)

		headline = " Type: other "
		print("-"*40 + headline + "-"*(60-len(headline)))
		for instanceIter in others:
			output = "%d." % ctr
			output = output.ljust(5) + "| "
			output += "Use instance '%s'." % instanceIter
			print(output)
			ctr += 1
			allInstances.append(instanceIter)

		print("%d. Enter instance and node type manually." % ctr)
		manualOption = ctr

		while True:
			userOptionStr = raw_input("Please choose an option: ")
			userOption = 0
			try:
				userOption = int(userOptionStr)
			except:
				pass
			if userOption == manualOption:
				break
			elif userOption > 0 and userOption < manualOption:
				instance = allInstances[userOption-1]
				nodeType = repoInfo["instances"][instance]["type"]
				break
			else:
				print("Invalid option. Please retry.")

	# If no node type and instance is chosen until now, ask user.
	if nodeType not in validNodeTypes:
		while True:
			nodeType = raw_input("Please enter node type:\n").lower()
			if nodeType in validNodeTypes:
				break
			else:
				print("Only valid node types are: "
					+ "'sensor', 'manager', 'alert'. Please retry.")
	if instance is None:
		instance = raw_input("Please enter instance:\n")

	return (nodeType, instance)


# Adds a user to the backend.
def addUser(userBackend, username, password, nodeType, instance, updater):

	if username is None:
		username = raw_input("Please enter username:\n")

	if password is None:
		while True:
			pw1 = getpass.getpass("Please enter password:\n")
			pw2 = getpass.getpass("Please verify password:\n")
			if pw1 == pw2:
				password = pw1
				break
			else:
				print("Passwords do not match. Please retry.")

	# If we have no instance given via argument
	# and we have online repository information, give the user a list
	# to choose from.
	if instance is None and updater is not None:
		nodeType, instance = chooseNodeTypeAndInstance(updater)

	# If no node type and instance is chosen until now, ask user.
	if nodeType not in validNodeTypes:
		while True:
			nodeType = raw_input("Please enter node type:\n").lower()
			if nodeType in validNodeTypes:
				break
			else:
				print("Only valid node types are: "
					+ "'sensor', 'manager', 'alert'. Please retry.")
	if instance is None:
		instance = raw_input("Please enter instance:\n")

	if userBackend.addUser(username, password, nodeType, instance):
		userBackend.writeUserdata()
		logging.info("[%s]: Adding user successful."
				% fileName)
	else:
		logging.error("[%s]: Adding user failed."
				% fileName)
		sys.exit(1)


# Modifies a user in the backend.
def modifyUser(userBackend, username, password, nodeType, instance, updater):

	# If we have no username given, ask for one.
	if username is None:
		allUsernames = listUsers(userBackend)

		while True:
			userOptionStr = raw_input("Choose number of username to modify: ")
			userOption = 0
			try:
				userOption = int(userOptionStr)
			except:
				pass
			if userOption > 0 and userOption <= len(allUsernames):
				username = allUsernames[userOption-1]
				break
			else:
				print("Invalid option. Please retry.")

	# Check if the username exists.
	if not userBackend.userExists(username):
		logging.error("[%s]: Username '%s' does not exist."
				% (fileName, username))
		sys.exit(1)

	# Ask for value to change if none was given via argument.
	if password is None and nodeType is None and instance is None:

		print("1. Change password.")
		print("2. Change instance and node type.")
		userOption = 0
		while True:
			userOptionStr = raw_input("Please choose an option: ")
			try:
				userOption = int(userOptionStr)
			except:
				pass
			if userOption > 0 and userOption < 3:
				break
			else:
				print("Invalid option. Please retry.")

		# Change password.
		if userOption == 1:
			while True:
				pw1 = getpass.getpass("Please enter password:\n")
				pw2 = getpass.getpass("Please verify password:\n")
				if pw1 == pw2:
					password = pw1
					break
				else:
					print("Passwords do not match. Please retry.")

		# Change instance and node type.
		elif userOption == 2:

			# Give user a list to choose from when we are not in offline mode.
			if updater is not None:
				nodeType, instance = chooseNodeTypeAndInstance(updater)

			# If no node type and instance is chosen until now, ask user.
			if nodeType not in validNodeTypes:
				while True:
					nodeType = raw_input("Please enter node type:\n").lower()
					if nodeType in validNodeTypes:
						break
					else:
						print("Only valid node types are: "
							+ "'sensor', 'manager', 'alert'. Please retry.")
			if instance is None:
				instance = raw_input("Please enter instance:\n")

	# Change password.
	if password is not None:
		if userBackend.changePassword(username, password):
			userBackend.writeUserdata()
			logging.info("[%s]: Changing password of user successful."
					% fileName)
		else:
			logging.error("[%s]: Changing password of user failed."
					% fileName)
			sys.exit(1)

	# Change node type and instance.
	if (nodeType is None or instance is None) and nodeType != instance:
		logging.error("[%s]: Node type and instance have to "
				% fileName
				+ "be modified together." )
		sys.exit(1)
	elif nodeType is not None and instance is not None:
		nodeType = nodeType.lower()
		if nodeType not in validNodeTypes:
			logging.error("[%s]: Node type '%s' invalid."
				% (fileName, nodeType))
			sys.exit(1)

		if userBackend.changeNodeTypeAndInstance(username, nodeType, instance):
			userBackend.writeUserdata()
			logging.info("[%s]: Changing node type and instance "
					% fileName
					+ "of user successful.")
		else:
			logging.error("[%s]: Changing node type and instance "
					% fileName
					+ "of user failed.")
			sys.exit(1)


# Deletes a user from the backend.
def deleteUser(userBackend, username):
	if username is None:
		allUsernames = listUsers(userBackend)

		while True:
			userOptionStr = raw_input("Choose number of username to delete: ")
			userOption = 0
			try:
				userOption = int(userOptionStr)
			except:
				pass
			if userOption > 0 and userOption <= len(allUsernames):
				username = allUsernames[userOption-1]
				break
			else:
				print("Invalid option. Please retry.")

	# Check if the username exists.
	if not userBackend.userExists(username):
		logging.error("[%s]: Username '%s' does not exist."
				% (fileName, username))
		sys.exit(1)

	if userBackend.deleteUser(username):
		userBackend.writeUserdata()
		logging.info("[%s]: Deleting user successful."
				% fileName)
	else:
		logging.error("[%s]: Deleting user failed."
				% fileName)
		sys.exit(1)


# Lists all existing users in the backend.
def listUsers(userBackend):

	# Divide data into node type category
	userDataDict = dict()
	alerts = list()
	managers = list()
	sensors = list()
	others = list()
	for userData in userBackend.userCredentials:
		userDataDict[userData.username] = userData
		if userData.nodeType == "alert":
			alerts.append(userData.username)
		elif userData.nodeType == "manager":
			managers.append(userData.username)
		elif userData.nodeType == "sensor":
			sensors.append(userData.username)
		else:
			others.append(userData.username)
	alerts.sort()
	managers.sort()
	sensors.sort()
	others.sort()

	# Create a list of all usernames in the exact order in which
	# we output them.
	allUsernames = list()

	print("#"*100)
	print("No.".ljust(5) + "| " + "Username".ljust(48) + "| Instance")
	print("#"*100)

	ctr = 1
	headline = " Type: alert "
	print("-"*40 + headline + "-"*(60-len(headline)))
	for username in alerts:
		output = "%d." % ctr
		output = output.ljust(5) + "| "
		output += username.ljust(48)
		output += "| "
		output += userDataDict[username].instance
		print(output)
		ctr += 1
		allUsernames.append(username)

	headline = " Type: manager "
	print("-"*40 + headline + "-"*(60-len(headline)))
	for username in managers:
		output = "%d." % ctr
		output = output.ljust(5) + "| "
		output += username.ljust(48)
		output += "| "
		output += userDataDict[username].instance
		print(output)
		ctr += 1
		allUsernames.append(username)

	headline = " Type: sensor "
	print("-"*40 + headline + "-"*(60-len(headline)))
	for username in sensors:
		output = "%d." % ctr
		output = output.ljust(5) + "| "
		output += username.ljust(48)
		output += "| "
		output += userDataDict[username].instance
		print(output)
		ctr += 1
		allUsernames.append(username)

	# The other category only exists because of compatibility reasons.
	# Perhaps a new category exists that is not known to this script.
	if others:
		headline = " Type: unknown "
		print("-"*40 + headline + "-"*(60-len(headline)))
		for username in others:
			output = "%d." % ctr
			output = output.ljust(5) + "| "
			output += username.ljust(48)
			output += "| "
			output += userDataDict[username].instance
			print(output)
			ctr += 1
			allUsernames.append(username)

	return allUsernames


if __name__ == '__main__':

	# Parsing command line options.
	parser = optparse.OptionParser()

	parser.add_option("-a",
		"--add",
		dest="add",
		action="store_true",
		help="Add a user..",
		default=False)
	parser.add_option("-d",
		"--delete",
		dest="delete",
		action="store_true",
		help="Delete an existing user.",
		default=False)
	parser.add_option("-m",
		"--modify",
		dest="modify",
		action="store_true",
		help="Modify an existing user.",
		default=False)
	parser.add_option("-l",
		"--list",
		dest="list",
		action="store_true",
		help="List all existing users.",
		default=False)

	optGroup = optparse.OptionGroup(parser,
		"Optional arguments available for adding/deleting/modifying a user")
	optGroup.add_option("-o",
		"--offline",
		dest="offline",
		action="store_true",
		help="Do not connect to the online repository in order give a "
			+ "list of choices. (Optional)",
		default=False)
	optGroup.add_option("-u",
		"--username",
		dest="username",
		action="store",
		help="Username to be added/deleted/modified. (Optional)",
		default=None)
	optGroup.add_option("-p",
		"--password",
		dest="password",
		action="store",
		help="Password for the user to be added/modified. (Optional)",
		default=None)
	optGroup.add_option("-t",
		"--type",
		dest="type",
		action="store",
		help="Type of the node to be added/modified. (Optional)",
		default=None)
	optGroup.add_option("-i",
		"--instance",
		dest="instance",
		action="store",
		help="Instance of the node to be added/modified. (Optional)",
		default=None)
	parser.add_option_group(optGroup)

	(options, args) = parser.parse_args()

	showHelp = (options.add
		or options.delete
		or options.modify
		or options.list)
	if showHelp is False:
		print "Use --help to get all available options."
		sys.exit(0)

	# Generate object of the global needed data.
	globalData = GlobalData()

	fileName = os.path.basename(__file__)
	instanceLocation = os.path.dirname(os.path.abspath(__file__)) + "/"

	validNodeTypes = ["sensor", "manager", "alert"]

	# Parse config file.
	try:
		configRoot = xml.etree.ElementTree.parse(instanceLocation +
				"/config/config.xml").getroot()

		# Parse chosen log level
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

		# Initialize logging.
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
			datefmt='%m/%d/%Y %H:%M:%S', level=loglevel)
		globalData.logger = logging.getLogger("server")

	except Exception as e:
		print "Config could not be parsed."
		print e
		sys.exit(1)

	# Parse the rest of the config with initialized logging.
	try:

		# Check if config and client version are compatible.
		configVersion = float(configRoot.attrib["version"])
		if configVersion != globalData.version:
			raise ValueError("Config version '%.3f' not "
				% configVersion
				+ "compatible with client version '%.3f'."
				% globalData.version)

		# Parse update options.
		updateServer = str(
			configRoot.find("update").find("server").attrib["host"])
		updatePort = int(
			configRoot.find("update").find("server").attrib["port"])
		updateLocation = str(
			configRoot.find("update").find("server").attrib["location"])
		updateCaFile = str(
			configRoot.find("update").find("server").attrib["caFile"])

		# Configure user credentials backend
		globalData.logger.debug("[%s]: Parsing user backend configuration."
			% fileName)
		userBackendMethod = str(
			configRoot.find("storage").find("userBackend").attrib[
			"method"]).upper()
		if userBackendMethod == "CSV":
			globalData.userBackend = CSVBackend(globalData,
				globalData.userBackendCsvFile)

		else:
			raise ValueError("No valid user backend method in config file.")

	except Exception as e:
		logging.exception("[%s]: Could not parse config." % fileName)
		sys.exit(1)

	# Create updater object only if we should contact the repository.
	updater = None
	if options.offline is False:

		# Create an updater process.
		try:
			updater = Updater(updateServer, updatePort, updateLocation,
				updateCaFile, globalData, None, retrieveInfo=False)
		except Exception as e:
			logging.exception("[%s]: Not able create updater object."
				% fileName)

	if options.add:
		addUser(globalData.userBackend,
			options.username,
			options.password,
			options.type,
			options.instance,
			updater)
	elif options.delete:
		deleteUser(globalData.userBackend,
			options.username)
	elif options.modify:
		modifyUser(globalData.userBackend,
			options.username,
			options.password,
			options.type,
			options.instance,
			updater)
	elif options.list:
		listUsers(globalData.userBackend)
	else:
		logging.error("[%s] Unknown option." % fileName)
		sys.exit(1)