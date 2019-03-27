#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import csv
import logging
import os
import StringIO
import bcrypt
import threading


# Class that holds user data information.
class UserData(object):

    def __init__(self, username, pwhash, nodeType, instance):
        self.username = username
        self.pwhash = pwhash
        self.nodeType = nodeType
        self.instance = instance


    def toList(self):
        return [self.username,
            self.pwhash,
            self.nodeType,
            self.instance]


# Internal abstract class for new user backends.
class _userBackend():

    # This function checks if the user credentials are valid
    #
    # return True or False
    def areUserCredentialsValid(self, username, password):
        raise NotImplemented("Function not implemented yet.")


    # This function checks if the node type and instance of the client
    # is correct
    #
    # return True or False
    def checkNodeTypeAndInstance(self, username, nodeType, instance):
        raise NotImplemented("Function not implemented yet.")


    # This function checks if the user exists.
    #
    # return True or False
    def userExists(self, username):
        raise NotImplemented("Function not implemented yet.")


    # This function writes the currently cached user data back to the backend.
    def writeUserdata(self):
        raise NotImplemented("Function not implemented yet.")


    # This function reads the user data from the backend and updates
    # the current cached one.
    def readUserdata(self):
        raise NotImplemented("Function not implemented yet.")


    # This function adds the user to the backend and returns if it was
    # successful.
    #
    # return True or False
    def addUser(self, username, password, nodeType, instance):
        raise NotImplemented("Function not implemented yet.")


    # This function deletes the user from the backend and returns if it was
    # successful.
    #
    # return True or False
    def deleteUser(self, username):
        raise NotImplemented("Function not implemented yet.")


    # This function changes the password of the user and returns if it was
    # successful.
    #
    # return True or False
    def changePassword(self, username, password):
        raise NotImplemented("Function not implemented yet.")


    # This function changes the node type and instance of the user
    # and returns if it was successful.
    #
    # return True or False
    def changeNodeTypeAndInstance(self, username, nodeType, instance):
        raise NotImplemented("Function not implemented yet.")


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

        self.readUserdata()


    # Internal function that acquires the lock.
    def _acquireLock(self):
        self.logger.debug("[%s]: Acquire lock." % self.fileName)
        self.userDataLock.acquire()


    # Internal function that releases the lock.
    def _releaseLock(self):
        self.logger.debug("[%s]: Release lock." % self.fileName)
        self.userDataLock.release()


    # Parses the data in csv version 0.
    # Does not acquire or release the lock.
    def _parseVersion0(self, csvData):
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
            if any(map(lambda x : x.username == username,
                self.userCredentials)):

                self.logger.error("[%s]: Username '%s' already exists "
                    % (self.fileName, username)
                    + "in CSV file.")

                continue

            pwhash = bcrypt.hashpw(password, bcrypt.gensalt())
            userData = UserData(username, pwhash, nodeType, instance)
            self.userCredentials.append(userData)


    # Parses the data in csv version 1.
    # Does not acquire or release the lock.
    def _parseVersion1(self, csvData):
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
            if any(map(lambda x : x.username == username,
                self.userCredentials)):

                self.logger.error("[%s]: Username '%s' already exists "
                    % (self.fileName, username)
                    + "in CSV file.")

                continue

            userData = UserData(username, pwhash, nodeType, instance)
            self.userCredentials.append(userData)


    # Extracts the version from the file.
    def _getVersion(self, csvData):
        version = 0
        for row in csvData:
            if len(row) == 1 and row[0].startswith("Version:"):
                try:
                    version = int(row[0][8:])
                except Exception as e:
                    self.logger.exception("[%s]: Unable to extract version of "
                        % self.fileName
                        + "CSV file")
            break
        return version


    # This function checks if the user credentials are valid.
    #
    # return True or False
    def areUserCredentialsValid(self, username, password):

        self._acquireLock()

        # Check all usernames if the given username exist
        # and then if the password is the correct one.
        for userData in self.userCredentials:

            if userData.username != username:
                continue

            else:
                if bcrypt.checkpw(password, userData.pwhash):
                    self._releaseLock()
                    return True
                else:
                    self._releaseLock()
                    return False

        self._releaseLock()
        return False


    # This function checks if the node type and instance of the client
    # is correct.
    #
    # return True or False
    def checkNodeTypeAndInstance(self, username, nodeType, instance):

        self._acquireLock()

        # check all usernames if the given username exists
        # and then check the given node type and instance
        for userData in self.userCredentials:

            if userData.username != username:
                continue

            else:
                if (userData.nodeType.upper() == nodeType.upper()
                    and userData.instance.upper() == instance.upper()):

                    self._releaseLock()
                    return True

                else:
                    self._releaseLock()
                    return False

        self._releaseLock()
        return False


    # This function checks if the user exists.
    #
    # return True or False
    def userExists(self, username):

        self._acquireLock()

        # Check all usernames if the given username exists.
        found = False
        for userData in self.userCredentials:
            if userData.username == username:
                found = True
                break

        self._releaseLock()

        return found

    # This function reads the user data from the backend and updates
    # the current cached one.
    def readUserdata(self):

        self.logger.info("[%s]: Reading user data from CSV file."
            % self.fileName)

        self._acquireLock()

        # Stores all user credentials as an object.
        self.userCredentials = list()

        # Check users.csv file exists before parsing.
        version = 0
        if os.path.isfile(self.csvLocation):

            # Parse csv file and store all user credentials.
            csvData = []
            with open(self.csvLocation, 'rb') as csvFile:
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
                self.logger.error("[%s]: Do not know how to parse CSV file "
                    % self.fileName
                    + "with version %d."
                    % version)

        else:
            self.logger.error("[%s]: No CSV file found."
                % self.fileName)

        self._releaseLock()

        # Write user data back if we have changed the csv file format.
        if version != self.csvVersion:
            self.writeUserdata()


    # This function writes the currently cached user data back to the backend.
    def writeUserdata(self):

        self.logger.info("[%s]: Writing user data to CSV file."
            % self.fileName)

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
        output = StringIO.StringIO()
        csvWriter = csv.writer(output,
            delimiter=",",
            quoting=csv.QUOTE_ALL)
        for userData in self.userCredentials:
            csvWriter.writerow(userData.toList())

        # Add csv data to the final file data.
        fileData += output.getvalue()
        output.close()

        # Write final file.
        with open(self.csvLocation, 'wb') as csvFile:
            csvFile.write(fileData)

        self._releaseLock()


    # This function adds the user to the backend and returns if it was
    # successful.
    #
    # return True or False
    def addUser(self, username, password, nodeType, instance):

        self.logger.info("[%s]: Adding user '%s' to backend."
            % (self.fileName, username))

        self._acquireLock()

        # Check if username has a duplicate.
        if any(map(lambda x : x.username == username,
            self.userCredentials)):

            self.logger.error("[%s]: Username '%s' already exists "
                % (self.fileName, username)
                + "in CSV file.")

            self._releaseLock()
            return False

        pwhash = bcrypt.hashpw(password, bcrypt.gensalt())
        userData = UserData(username, pwhash, nodeType, instance)
        self.userCredentials.append(userData)

        self._releaseLock()

        return True


    # This function deletes the user from the backend and returns if it was
    # successful.
    #
    # return True or False
    def deleteUser(self, username):

        self.logger.info("[%s]: Deleting user '%s' from backend."
            % (self.fileName, username))

        self._acquireLock()

        for userData in self.userCredentials:
            if userData.username == username:
                self.userCredentials.remove(userData)
                self._releaseLock()
                return True

        self.logger.error("[%s]: Not able to find username '%s'."
            % (self.fileName, username))

        self._releaseLock()

        return False


    # This function changes the password of the user and returns if it was
    # successful.
    #
    # return True or False
    def changePassword(self, username, password):

        self.logger.info("[%s]: Changing password from user."
            % self.fileName)

        self._acquireLock()

        for userData in self.userCredentials:
            if userData.username == username:
                pwhash = bcrypt.hashpw(password, bcrypt.gensalt())
                userData.pwhash = pwhash
                self._releaseLock()
                return True

        self.logger.error("[%s]: Not able to find username '%s'."
            % (self.fileName, username))

        self._releaseLock()

        return False


    # This function changes the node type and instance of the user
    # and returns if it was successful.
    #
    # return True or False
    def changeNodeTypeAndInstance(self, username, nodeType, instance):

        # NOTE: Changing the node type and instance while the server is
        # running can corrupt the database. If it is done while the server
        # is not running, it will only change the entries in the user backend.
        # The database still contains the old node type and instance and
        # all entries regarding the client. However, when the client connects
        # with the new node type and instance, the database is directly
        # updated. Therefore, we do not have to do it manually here.

        self.logger.info("[%s]: Changing node type and instance from user."
            % self.fileName)

        self._acquireLock()

        for userData in self.userCredentials:
            if userData.username == username:
                userData.nodeType = nodeType
                userData.instance = instance
                self._releaseLock()
                return True

        self.logger.error("[%s]: Not able to find username '%s'."
            % (self.fileName, username))

        self._releaseLock()

        return False