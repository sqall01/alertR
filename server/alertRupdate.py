#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import sys
import os
import json
from lib import GlobalData
from lib import Updater
import xml.etree.ElementTree
import logging
import optparse
import importlib


def outputUpdateFailed():
    print("")
    print("UPDATE PROCESS FAILED!")
    print("To see the reason take a look at the update ", end="")
    print("process output. ", end="")
    print("You can change the log level in the configuration ", end="")
    print("file to 'DEBUG' ", end="")
    print("and repeat the update process to get more detailed ", end="")
    print("information.")


# This function asks the user for confirmation directly.
def userAsk():

    while True:
        try:
            localInput = input("(y/n): ")
        except KeyboardInterrupt:
            print("Bye.")
            sys.exit(0)
        except Exception as e:
            continue

        if localInput.strip().upper() == "Y":
            return True
        elif localInput.strip().upper() == "N":
            return False
        else:
            print("Invalid input.")


# This function asks the user for confirmation (if wanted).
def userConfirmation(arg_options):
    if arg_options is None or arg_options.yes is False:
        if userAsk() is False:
            print("Bye.")
            sys.exit(0)
    else:
        print("NOTE: Skipping confirmation.")


# This function checks if new dependencies exist and if they are met.
def checkDependencies(oldDependencies, newDependencies):

    fileName = os.path.basename(__file__)

    # Check if all pip dependencies are met.
    if "pip" in newDependencies.keys():

        for pip in newDependencies["pip"]:

            importName = pip["import"]
            packet = pip["packet"]

            # only get version if it exists
            version = None
            if "version" in pip.keys():
                version = pip["version"]

            # Check if this dependency already existed in the old version.
            skipCheck = False
            if "pip" in oldDependencies.keys():
                for oldPip in oldDependencies["pip"]:

                    oldImportName = oldPip["import"]
                    if importName != oldImportName:
                        continue

                    logging.debug("[%s]: Checking dependency of module '%s' has changed." % (fileName, importName))

                    # Only get version if it exists.
                    oldVersion = None
                    if "version" in oldPip.keys():
                        oldVersion = oldPip["version"]

                    # If we have the same dependency for the old and new
                    # version of the instance we skip the check.
                    if oldVersion == version:
                        skipCheck = True
                        break

                    logging.info("[%s]: Dependency of module '%s' "
                                 % (fileName, importName)
                                 + "has changed the version from '%s' to '%s'."
                                 % (oldVersion, version))

            # Skip check if we already have the correct version in the
            # old installation as dependency.
            if skipCheck:
                continue

            # try to import needed module
            temp = None
            try:

                logging.info("[%s]: Checking module '%s'." % (fileName, importName))

                temp = importlib.import_module(importName)

            except Exception as e:
                
                logging.error("[%s]: Module '%s' not installed." % (fileName, importName))

                print("")
                print("The needed module '%s' is not installed. " % importName, end="")
                print("You can install the module by executing ", end="")
                print("'pip3 install %s' " % packet, end="")
                print("(if you do not have installed pip, you can install it ", end="")
                print("on Debian like systems by executing ", end="")
                print("'apt-get install python3-pip').")

                return False

            # if a version string is given in the instance information
            # => check if the installed version satisfies the needed version
            if version is not None:

                versionCorrect = True
                versionCheckFailed = False
                installedVersion = "Information Not Available"

                # Try to extract version from package.
                try:
                    installedVersion = temp.__version__.split(".")
                    neededVersion = version.split(".")

                    maxLength = 0
                    if len(installedVersion) > len(neededVersion):
                        maxLength = len(installedVersion)
                    else:
                        maxLength = len(neededVersion)

                    # check the needed version and the installed version
                    for i in range(maxLength):
                        if int(installedVersion[i]) > int(neededVersion[i]):
                            versionCorrect = True
                            break
                        elif int(installedVersion[i]) < int(neededVersion[i]):
                            versionCorrect = False
                            break

                except Exception as e:
                    logging.error("[%s]: Could not verify installed version of module '%s'." % (fileName, importName))
                    versionCheckFailed = True

                # if the version check failed, ask the user for confirmation
                if versionCheckFailed is True:
                    print("")
                    print("Could not automatically verify the installed ", end="")
                    print("version of the module '%s'. " % importName, end="")
                    print("You have to verify the version yourself.")
                    print("")
                    print("Installed version: %s" % installedVersion)
                    print("Needed version: %s" % version)
                    print("")
                    print("Do you have a version installed that satisfies ", end="")
                    print("the needed version?")

                    if not userAsk():
                        versionCorrect = False
                    else:
                        versionCorrect = True

                # if the version is not correct => abort the next checks
                if versionCorrect is False:
                    print("")
                    print("The needed version '%s' " % version, end="")
                    print("of module '%s' is not satisfied " % importName, end="")
                    print("(you have version '%s' " % installedVersion, end="")
                    print("installed).")
                    print("Please update your installed version of the pip ", end="")
                    print("packet '%s'." % packet)

                    return False

    # check if all other dependencies are met
    if "other" in newDependencies.keys():

        for other in newDependencies["other"]:

            importName = other["import"]

            # Only get version if it exists.
            version = None
            if "version" in other.keys():
                version = other["version"]

            # Check if this dependency already existed in the old version.
            skipCheck = False
            if "other" in oldDependencies.keys():
                for oldOther in oldDependencies["other"]:

                    oldImportName = oldOther["import"]
                    if importName != oldImportName:
                        continue

                    logging.debug("[%s]: Checking dependency of module '%s' has changed." % (fileName, importName))

                    # Only get version if it exists.
                    oldVersion = None
                    if "version" in oldOther.keys():
                        oldVersion = oldOther["version"]

                    # If we have the same dependency for the old and new
                    # version of the instance we skip the check.
                    if oldVersion == version:
                        skipCheck = True
                        break

                    logging.info("[%s]: Dependency of module '%s' "
                                 % (fileName, importName)
                                 + "has changed the version from '%s' to '%s'."
                                 % (oldVersion, version))

            # Skip check if we already have the correct version in the
            # old installation as dependency.
            if skipCheck:
                continue

            # try to import needed module
            temp = None
            try:

                logging.info("[%s]: Checking module '%s'." % (fileName, importName))

                temp = importlib.import_module(importName)

            except Exception as e:

                logging.error("[%s]: Module '%s' not installed." % (fileName, importName))

                print("")
                print("The needed module '%s' is not " % importName, end="")
                print("installed. You need to install it before ", end="")
                print("you can use this AlertR instance.")

                return False

            # if a version string is given in the instance information
            # => check if the installed version satisfies the
            # needed version
            if version is not None:

                versionCorrect = True
                versionCheckFailed = False
                installedVersion = "Information Not Available"

                # Try to extract version from package.
                try:
                    installedVersion = temp.__version__.split(".")
                    neededVersion = version.split(".")

                    maxLength = 0
                    if len(installedVersion) > len(neededVersion):
                        maxLength = len(installedVersion)
                    else:
                        maxLength = len(neededVersion)

                    # check the needed version and the installed version
                    for i in range(maxLength):
                        if int(installedVersion[i]) > int(neededVersion[i]):
                            versionCorrect = True
                            break
                        elif int(installedVersion[i]) < int(neededVersion[i]):
                            versionCorrect = False
                            break

                except Exception as e:
                    logging.error("[%s]: Could not verify installed version of module '%s'." % (fileName, importName))
                    versionCheckFailed = True

                # if the version check failed, ask the user
                # for confirmation
                if versionCheckFailed is True:
                    print("")
                    print("Could not automatically verify the installed ", end="")
                    print("version of the module '%s'. " % importName, end="")
                    print("You have to verify the version yourself.")
                    print("")
                    print("Installed version: %s" % installedVersion)
                    print("Needed version: %s" % version)
                    print("")
                    print("Do you have a version installed that satisfies ", end="")
                    print("the needed version?")

                    if not userAsk():
                        versionCorrect = False
                    else:
                        versionCorrect = True

                # if the version is not correct => abort the next checks
                if versionCorrect is False:

                    print("")
                    print("The needed version '%s' " % version, end="")
                    print("of module '%s' is not satisfied " % importName, end="")
                    print("(you have version '%s' " % installedVersion, end="")
                    print("installed).")
                    print("Please update your installed version.")

                    return False

    return True


if __name__ == '__main__':

    # parsing command line options
    parser = optparse.OptionParser()
    parser.add_option("-y",
                      "--yes",
                      dest="yes",
                      action="store_true",
                      help="Do not ask me for confirmation. I know what I am doing.",
                      default=False)
    parser.add_option("-u",
                      "--update",
                      dest="update",
                      action="store_true",
                      help="Start update process now.",
                      default=False)
    parser.add_option("-f",
                      "--force",
                      dest="force",
                      action="store_true",
                      help="Do not check the version or dependencies. Just update all files.",
                      default=False)
    (options, args) = parser.parse_args()

    if options.update is False:
        print("Use --help to get all available options.")
        sys.exit(0)

    protocolUpdate = False
    configUpdate = False

    # generate object of the global needed data
    globalData = GlobalData()

    fileName = os.path.basename(__file__)
    instanceLocation = os.path.dirname(os.path.abspath(__file__)) + "/"

    try:
        # parse config file
        configRoot = xml.etree.ElementTree.parse(instanceLocation + "/config/config.xml").getroot()

        # parse chosen log level
        tempLoglevel = str(configRoot.find("general").find("log").attrib["level"])
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
                            datefmt='%m/%d/%Y %H:%M:%S',
                            level=loglevel)
        globalData.logger = logging.getLogger("server")

    except Exception as e:
        print("Config could not be parsed.")
        print(e)
        sys.exit(1)

    # parse the rest of the config with initialized logging
    try:

        # check if config and client version are compatible
        configVersion = float(configRoot.attrib["version"])
        if configVersion != globalData.version:
            raise ValueError("Config version '%.3f' not "
                             % configVersion
                             + "compatible with server version '%.3f'."
                             % globalData.version)

        # parse update options
        updateUrl = str(configRoot.find("update").find("server").attrib["url"])

    except Exception as e:
        logging.exception("[%s]: Could not parse config." % fileName)
        sys.exit(1)

    logging.info("[%s]: Current version: %.3f-%d." % (fileName, globalData.version, globalData.rev))

    # Parse local instance information (if it exists, otherwise create one).
    localInstanceInfo = None
    try:
        with open(instanceLocation + "/instanceInfo.json", 'r') as fp:
            localInstanceInfo = json.loads(fp.read())
    except Exception as e:
        localInstanceInfo = {"files": {},
                             "version": globalData.version,
                             "rev": globalData.rev,
                             "dependencies": {}}

    # create an updater process
    try:
        updater = Updater(updateUrl, globalData, localInstanceInfo)
    except:
        logging.exception("[%s]: Not able to create update object." % fileName)
        outputUpdateFailed()
        sys.exit(1)

    # Get new instance information.
    newInstanceInfo = updater.getInstanceInformation()

    logging.info("[%s]: Newest version available: %.3f-%d."
                 % (fileName, updater.newestVersion, updater.newestRev))

    # check if the received version is newer than the current one
    if (updater.newestVersion > globalData.version or
       (updater.newestRev > globalData.rev and updater.newestVersion == globalData.version)
       or options.force is True):

        if options.force is True:
            logging.info("[%s]: Forcing update of AlertR instance." % fileName)

        # Check if we have new dependencies before installing.
        logging.info("[%s]: Checking the dependencies." % fileName)
        newDependencies = newInstanceInfo["dependencies"]
        oldDependencies = localInstanceInfo["dependencies"]
        if options.force is not True and not checkDependencies(oldDependencies, newDependencies):
            logging.error("[%s]: Update failed due to dependencies." % fileName)
            outputUpdateFailed()
            sys.exit(1)

        # check if the update changes the protocol
        if int(updater.newestVersion * 10) > int(globalData.version * 10):
            protocolUpdate = True
            
        # check if the update changes the configuration file
        if updater.newestVersion > globalData.version:
            configUpdate = True

        # if the update changes the protocol
        # => notify user and ask for confirmation
        if protocolUpdate is True:
            print("")
            print("WARNING: You are about to make an update that changes ", end="")
            print("the used network protocol. ", end="")
            print("This means that after you have updated this AlertR ", end="")
            print("instance you also have to update your AlertR server and ", end="")
            print("all your AlertR clients in order to have a working ", end="")
            print("system again.")
            print("Are you sure you want to continue and update this ", end="")
            print("AlertR instance?")
            userConfirmation(options)

        # if the update needs changes in the configuration file
        # => notify user and ask for confirmation
        if configUpdate is True:
            print("")
            print("WARNING: You are about to make an update that needs ", end="")
            print("changes in the configuration file. ", end="")
            print("This means that you have to manually update your used ", end="")
            print("configuration file before you can use this AlertR ", end="")
            print("instance again.")
            print("Are you sure you want to continue and update this ", end="")
            print("AlertR instance?")
            userConfirmation(options)

        print("")
        print("Please make sure that this AlertR instance is stopped before ", end="")
        print("continuing the update process.")
        print("Are you sure this AlertR instance is not running?")
        userConfirmation(options)

        if updater.updateInstance() is False:
            logging.error("[%s]: Update failed." % fileName)
            outputUpdateFailed()
            sys.exit(1)

        # Store new instance information file manually afterwards.
        try:
            with open(instanceLocation + "/instanceInfo.json", 'w') as fp:
                fp.write(json.dumps(newInstanceInfo))
        except Exception as e:
            logging.exception("[%s]: Not able to store new 'instanceInfo.json'." % fileName)
            outputUpdateFailed()
            sys.exit(1)

        logging.info("[%s]: Update finished." % fileName)

        print("")
        print("UPDATE FINISHED!")

        # if the update changes the protocol
        # => output a reminder
        if protocolUpdate is True:
            print("NOTE: Please make sure you update all your AlertR ", end="")
            print("instances before you restart this instance.")

        # if the update needs changes in the configuration file
        # => output a reminder
        if configUpdate is True:
            print("NOTE: Please make sure you manually update the ", end="")
            print("configuration file of this AlertR instance before ", end="")
            print("you restart this instance.")

        if protocolUpdate is False and configUpdate is False:
            print("NOTE: Please start this AlertR instance now.")

    else:
        logging.info("[%s]: No new version available." % fileName)

        print("")
        print("SKIPPING UPDATE!")
        print("No new version is available in the configured repository.")

        sys.exit(0)
