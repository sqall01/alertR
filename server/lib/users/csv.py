#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import csv
import os
import io
import bcrypt
import threading
from .core import _userBackend, UserData


# User backend that uses a simple csv file.
class CSVBackend(_userBackend):

    def __init__(self, globalData, csvLocation):

        self.globalData = globalData
        self.logger = self.globalData.logger

        self.userDataLock = threading.BoundedSemaphore(1)

        self.csvLocation = csvLocation

        # CSV version in case we have to change it.
        self.csvVersion = 1

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        self.userCredentials = list()

        self.readUserdata()

    def _acquireLock(self):
        """
        Internal function that acquires the lock.
        """
        self.userDataLock.acquire()

    def _releaseLock(self):
        """
        Internal function that releases the lock.
        """
        self.userDataLock.release()

    def _parseVersion0(self, csvData):
        """
        Parses the data in csv version 0. Does not acquire or release the lock.

        :param csvData:
        """
        for row in csvData:
            if row[0].find('#') != -1:
                continue

            if len(row) != 4:
                continue

            username = row[0].replace(' ', '')
            password = row[1].replace(' ', '')
            nodeType = row[2].replace(' ', '')
            instance = row[3].replace(' ', '')

            # Check if username has a duplicate.
            if any([x.username == username for x in self.userCredentials]):
                self.logger.error("[%s]: Username '%s' already exists in CSV file." % (self.fileName, username))
                continue

            pwhash = bcrypt.hashpw(password.encode("ascii"), bcrypt.gensalt()).decode("ascii")
            userData = UserData(username, pwhash, nodeType, instance)
            self.userCredentials.append(userData)

    def _parseVersion1(self, csvData):
        """
        Parses the data in csv version 1. Does not acquire or release the lock.
        :param csvData:
        """
        for row in csvData:
            if row[0].find('#') != -1:
                continue

            if len(row) != 4:
                continue

            username = row[0].replace(' ', '')
            pwhash = row[1].replace(' ', '')
            nodeType = row[2].replace(' ', '')
            instance = row[3].replace(' ', '')

            # Check if username has a duplicate.
            if any([x.username == username for x in self.userCredentials]):
                self.logger.error("[%s]: Username '%s' already exists in CSV file." % (self.fileName, username))
                continue

            userData = UserData(username, pwhash, nodeType, instance)
            self.userCredentials.append(userData)

    def _getVersion(self, csvData) -> int:
        """
        Extracts the version from the file.

        :param csvData:
        :return: version of the CSV file.
        """
        version = 0
        for row in csvData:
            if len(row) == 1 and row[0].startswith("Version:"):
                try:
                    version = int(row[0][8:])

                except Exception as e:
                    self.logger.exception("[%s]: Unable to extract version of CSV file." % self.fileName)

            break

        return version

    def areUserCredentialsValid(self, username: str, password: str) -> bool:
        """
        This function checks if the user credentials are valid

        :param username: name of the user
        :param password: password of the user
        :return True or False
        """
        self._acquireLock()

        # Check all usernames if the given username exist
        # and then if the password is the correct one.
        for userData in self.userCredentials:

            if userData.username != username:
                continue

            else:
                if bcrypt.checkpw(password.encode("ascii"), userData.pwhash.encode("ascii")):
                    self._releaseLock()
                    return True

                else:
                    self._releaseLock()
                    return False

        self._releaseLock()
        return False

    def checkNodeTypeAndInstance(self, username: str, nodeType: str, instance: str) -> bool:
        """
        This function checks if the node type and instance of the client is correct

        :param username: name of the user
        :param nodeType: type of the node (alert, manager, sensor, server)
        :param instance: exact instance of the node
        :return True or False
        """
        self._acquireLock()

        # check all usernames if the given username exists
        # and then check the given node type and instance
        for userData in self.userCredentials:
            if userData.username != username:
                continue

            else:
                if userData.nodeType.upper() == nodeType.upper() and userData.instance.upper() == instance.upper():
                    self._releaseLock()
                    return True

                else:
                    self.logger.error("[%s]: Node or instance invalid. Expected: '%s' and '%s'. "
                                      % (self.fileName, userData.nodeType, userData.instance)
                                      + "Received: '%s' and '%s'."
                                      % (nodeType, instance))

                    self._releaseLock()
                    return False

        self.logger.error("[%s]: User credentials for user '%s' not found." % (username, self.fileName))

        self._releaseLock()
        return False

    def userExists(self, username: str) -> bool:
        """
        This function checks if the user exists.

        :param username: name of the user
        :return True or False
        """
        self._acquireLock()

        # Check all usernames if the given username exists.
        found = False
        for userData in self.userCredentials:
            if userData.username == username:
                found = True
                break

        self._releaseLock()

        return found

    def readUserdata(self):
        """
        This function reads the user data from the backend and updates the current cached one.
        """
        self.logger.info("[%s]: Reading user data from CSV file." % self.fileName)

        self._acquireLock()

        # Stores all user credentials as an object.
        self.userCredentials = list()

        # Check users.csv file exists before parsing.
        version = 0
        if os.path.isfile(self.csvLocation):

            # Parse csv file and store all user credentials.
            csvData = []
            with open(self.csvLocation, 'rt',
                      encoding="ascii") as csvFile:
                csvReader = csv.reader(csvFile, quoting=csv.QUOTE_ALL)
                csvData = list(csvReader)

            # Extract version of the csv file.
            version = self._getVersion(csvData)

            # Parse the csv file according to the version.
            if version == 0:
                self._parseVersion0(csvData)

            elif version == 1:
                self._parseVersion1(csvData)

            else:
                self.logger.error("[%s]: Do not know how to parse CSV file with version %d."
                                  % (self.fileName, version))

        else:
            self.logger.error("[%s]: No CSV file found." % self.fileName)

        self._releaseLock()

        # Write user data back if we have changed the csv file format.
        if version != self.csvVersion:
            self.writeUserdata()

    def writeUserdata(self):
        """
        This function writes the currently cached user data back to the backend.
        """
        self.logger.info("[%s]: Writing user data to CSV file." % self.fileName)

        self._acquireLock()

        # Set version of the current csv format.
        fileData = "Version:%d\n" % self.csvVersion

        # Add comments for the csv file.
        fileData += "#\n"
        fileData += "# Characters not allowed for"
        fileData += " usage are '#', ',' and '\"'.\n"
        fileData += "# The values are \"username, bcrypt(password), node type,"
        fileData += " client instance\" per line.\n"
        fileData += "# Note: whitespaces will be removed during parsing.\n"
        fileData += "# Please do not modify this file directly and use\n" 
        fileData += "# 'manageUsers.py' instead.\n"

        # Create csv data for the file.
        output = io.StringIO()
        csvWriter = csv.writer(output,
                               delimiter=",",
                               quoting=csv.QUOTE_ALL)

        for userData in self.userCredentials:
            csvWriter.writerow(userData.toList())

        # Add csv data to the final file data.
        fileData += output.getvalue()
        output.close()

        # Write final file.
        with open(self.csvLocation, 'wt',
                  encoding="ascii") as csvFile:
            csvFile.write(fileData)

        self._releaseLock()

    def addUser(self, username: str, password: str, nodeType: str, instance: str) -> bool:
        """
        This function adds the user to the backend and returns if it was successful.

        :param username: name of the user
        :param password: password of the user
        :param nodeType: type of the node (alert, manager, sensor, server)
        :param instance: exact instance of the node
        :return True or False
        """
        self.logger.info("[%s]: Adding user '%s' to backend." % (self.fileName, username))

        self._acquireLock()

        # Check if username has a duplicate.
        if any([x.username == username for x in self.userCredentials]):
            self.logger.error("[%s]: Username '%s' already exists in CSV file." % (self.fileName, username))

            self._releaseLock()
            return False

        pwhash = bcrypt.hashpw(password.encode("ascii"), bcrypt.gensalt()).decode("ascii")
        userData = UserData(username, pwhash, nodeType, instance)
        self.userCredentials.append(userData)

        self._releaseLock()
        return True

    def deleteUser(self, username: str) -> bool:
        """
        This function deletes the user from the backend and returns if it was successful.

        :param username: name of the user
        :return True or False
        """
        self.logger.info("[%s]: Deleting user '%s' from backend." % (self.fileName, username))

        self._acquireLock()

        for userData in self.userCredentials:
            if userData.username == username:
                self.userCredentials.remove(userData)

                self._releaseLock()
                return True

        self.logger.error("[%s]: Not able to find username '%s'." % (self.fileName, username))

        self._releaseLock()
        return False

    def changePassword(self, username: str, password: str) -> bool:
        """
        This function changes the password of the user and returns if it was successful.

        :param username: name of the user
        :param password: password of the user
        :return True or False
        """
        self.logger.info("[%s]: Changing password from user." % self.fileName)

        self._acquireLock()

        for userData in self.userCredentials:
            if userData.username == username:
                pwhash = bcrypt.hashpw(password.encode("ascii"), bcrypt.gensalt()).decode("ascii")
                userData.pwhash = pwhash

                self._releaseLock()
                return True

        self.logger.error("[%s]: Not able to find username '%s'." % (self.fileName, username))

        self._releaseLock()
        return False

    def changeNodeTypeAndInstance(self, username: str, nodeType: str, instance: str) -> bool:
        """
        This function changes the node type and instance of the user and returns if it was successful.

        :param username: name of the user
        :param nodeType: type of the node (alert, manager, sensor, server)
        :param instance: exact instance of the node
        :return True or False
        """

        # NOTE: Changing the node type and instance while the server is
        # running can corrupt the database. If it is done while the server
        # is not running, it will only change the entries in the user backend.
        # The database still contains the old node type and instance and
        # all entries regarding the client. However, when the client connects
        # with the new node type and instance, the database is directly
        # updated. Therefore, we do not have to do it manually here.

        self.logger.info("[%s]: Changing node type and instance from user." % self.fileName)

        self._acquireLock()

        for userData in self.userCredentials:
            if userData.username == username:
                userData.nodeType = nodeType
                userData.instance = instance

                self._releaseLock()
                return True

        self.logger.error("[%s]: Not able to find username '%s'." % (self.fileName, username))

        self._releaseLock()
        return False
