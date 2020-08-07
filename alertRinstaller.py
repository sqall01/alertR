#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import subprocess
import sys
import time
import logging
import json
import hashlib
import tempfile
import shutil
import stat
import math
import importlib
import threading
import optparse
import io
from typing import Optional, Dict, Any, Union, List

################ GLOBAL CONFIGURATION DATA ################

# used log level
# valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
loglevel = logging.INFO

# repository information
url = "https://raw.githubusercontent.com/sqall01/alertR/master/"

################ GLOBAL CONFIGURATION DATA ################

# Minimum version of requests required.
requests_min_version = "2.20.0"


# internal class that is used as an enum to represent the type of file update
class _FileUpdateType:
    NEW = 1
    DELETE = 2
    MODIFY = 3


# this class processes all actions concerning the update process
class Updater:

    def __init__(self,
                 url: str,
                 instance: str,
                 targetLocation: str,
                 localInstanceInfo: Optional[Dict[str, Any]] = None,
                 retrieveInfo: bool = True,
                 timeout: float = 20.0):

        # used for logging
        self.fileName = os.path.basename(__file__)

        # the updater object is not thread safe
        self.updaterLock = threading.Lock()

        # Compatible repository versions.
        self.supported_versions = [1, 2]

        # set global configured data
        self.version = 0
        self.rev = 0
        self.instance = instance
        self.instanceLocation = targetLocation

        # set update server configuration
        if not url.lower().startswith("https"):
            raise ValueError("Only 'https' is allowed.")
        self.url = url
        self.timeout = timeout

        # needed to keep track of the newest version
        self.newestVersion = self.version
        self.newestRev = self.rev
        self.newestFiles = None  # type: Optional[Dict[str, str]]
        self.newestSymlinks = None  # type: Optional[List[str]]
        self.lastChecked = 0
        self.repoInfo = None  # type: Dict[str, Any]
        self.repoInstanceLocation = None  # type: Optional[str]
        self.instanceInfo = None  # type: Dict[str, Any]
        self.repo_version = 1
        self.max_redirections = 10

        if localInstanceInfo is None:
            self.localInstanceInfo = {"files": {}}
        else:
            self.localInstanceInfo = localInstanceInfo

        # size of the download chunks
        self.chunkSize = 4096

        # Get newest data from repository.
        if retrieveInfo:
            if not self._getNewestVersionInformation():
                raise ValueError("Not able to get newest repository information.")

    def _acquireLock(self):
        """
        Internal function that acquires the lock.
        """
        logging.debug("[%s]: Acquire lock." % self.fileName)
        self.updaterLock.acquire()

    def _releaseLock(self):
        """
        # Internal function that releases the lock.
        """
        logging.debug("[%s]: Release lock." % self.fileName)
        self.updaterLock.release()

    def _checkFilesToUpdate(self) -> Optional[Dict[str, int]]:
        """
        Internal function that checks which files are new and which files have to be updated.

        :return: a dict of files that are affected by this update (and how) or None
        """
        # check if the last version information check was done shortly before
        # or was done at all
        # => if not get the newest version information
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.lastChecked) > 60 or self.newestFiles is None or self.newestSymlinks is None:
            if self._getNewestVersionInformation() is False:
                logging.error("[%s]: Not able to get version information for checking files." % self.fileName)
                return None

        counterUpdate = 0
        counterNew = 0
        counterDelete = 0
        fileList = self.newestFiles.keys()

        # get all files that have to be updated
        filesToUpdate = dict()
        for clientFile in fileList:

            # check if file already exists
            # => check if file has to be updated
            if os.path.exists(os.path.join(self.instanceLocation, clientFile)):

                f = open(os.path.join(self.instanceLocation, clientFile), 'rb')
                sha256Hash = self._sha256File(f)
                f.close()

                # check if file has changed
                # => if not ignore it
                if sha256Hash == self.newestFiles[clientFile]:
                    logging.debug("[%s]: Not changed: '%s'" % (self.fileName, clientFile))
                    continue

                # => if it has changed add it to the list of files to update
                else:
                    logging.debug("[%s]: New version: '%s'" % (self.fileName, clientFile))
                    filesToUpdate[clientFile] = _FileUpdateType.MODIFY
                    counterUpdate += 1

            # => if the file does not exist, just add it
            else:
                logging.debug("[%s]: New file: '%s'" % (self.fileName, clientFile))
                filesToUpdate[clientFile] = _FileUpdateType.NEW
                counterNew += 1

        # Get all files that have to be deleted.
        for clientFile in self.localInstanceInfo["files"].keys():

            if clientFile not in fileList:
                logging.debug("[%s]: Delete file: '%s'" % (self.fileName, clientFile))
                filesToUpdate[clientFile] = _FileUpdateType.DELETE
                counterDelete += 1

        logging.info("[%s]: Files to modify: %d; New files: %d; Files to delete: %d"
                     % (self.fileName, counterUpdate, counterNew, counterDelete))

        return filesToUpdate

    def _checkFilePermissions(self, filesToUpdate: Dict[str, int]) -> bool:
        """
        Internal function that checks the needed permissions to perform the update

        :param filesToUpdate: Dict of files and their modification state
        :return: True or False
        """
        # check permissions for each file that is affected by this update
        for clientFile in filesToUpdate.keys():

            # check if the file just has to be modified
            if filesToUpdate[clientFile] == _FileUpdateType.MODIFY:

                # check if the file is not writable
                # => cancel update
                if not os.access(os.path.join(self.instanceLocation, clientFile), os.W_OK):
                    logging.error("[%s]: File '%s' is not writable." % (self.fileName, clientFile))
                    return False

                logging.debug("[%s]: File '%s' is writable." % (self.fileName, clientFile))

            # check if the file is new and has to be created
            elif filesToUpdate[clientFile] == _FileUpdateType.NEW:
                logging.debug("[%s]: Checking write permissions for new file: '%s'"
                              % (self.fileName, clientFile))

                folderStructure = clientFile.split("/")

                # check if the new file is located in the root directory
                # of the instance
                # => check root directory of the instance for write permissions
                if len(folderStructure) == 1:
                    if not os.access(self.instanceLocation, os.W_OK):
                        logging.error("[%s]: Folder './' is not writable." % self.fileName)
                        return False

                    logging.debug("[%s]: Folder './' is writable." % self.fileName)

                # if new file is not located in the root directory
                # of the instance
                # => check all folders on the way to the new file for write
                # permissions
                else:
                    tempPart = ""
                    for filePart in folderStructure:

                        # check if folder exists
                        if os.path.exists(os.path.join(self.instanceLocation, tempPart, filePart)):

                            # check if folder is not writable
                            # => cancel update
                            if not os.access(os.path.join(self.instanceLocation, tempPart, filePart), os.W_OK):
                                logging.error("[%s]: Folder '%s' is not writable."
                                              % (self.fileName, os.path.join(tempPart, filePart)))
                                return False

                            logging.debug("[%s]: Folder '%s' is writable."
                                          % (self.fileName, os.path.join(tempPart, filePart)))

                            tempPart = os.path.join(tempPart, filePart)

            # check if the file has to be deleted
            elif filesToUpdate[clientFile] == _FileUpdateType.DELETE:

                # check if the file is not writable
                # => cancel update
                if not os.access(os.path.join(self.instanceLocation, clientFile), os.W_OK):
                    logging.error("[%s]: File '%s' is not writable (deletable)."
                                  % (self.fileName, clientFile))
                    return False

                logging.debug("[%s]: File '%s' is writable (deletable)."
                              % (self.fileName, clientFile))

            else:
                raise ValueError("Unknown file update type.")

        return True

    def _createSubDirectories(self, fileLocation: str, targetDirectory: str) -> bool:
        """
        Internal function that creates sub directories in the target directory for the given file location

        :param fileLocation: location of the file
        :param targetDirectory: location of the target directory
        :return: True or False
        """
        folderStructure = fileLocation.split("/")
        if len(folderStructure) != 1:

            try:
                i = 0
                tempPart = ""
                while i < (len(folderStructure) - 1):

                    # check if the sub directory already exists
                    # => if not create it
                    if not os.path.exists(os.path.join(targetDirectory, tempPart, folderStructure[i])):
                        logging.debug("[%s]: Creating directory '%s'."
                                      % (self.fileName, os.path.join(targetDirectory, tempPart, folderStructure[i])))

                        os.mkdir(os.path.join(targetDirectory, tempPart, folderStructure[i]))

                    # if the sub directory already exists then check
                    # if it is a directory
                    # => raise an exception if it is not
                    elif not os.path.isdir(os.path.join(targetDirectory, tempPart, folderStructure[i])):
                        raise ValueError("Location '%s' already exists and is not a directory."
                                         % (os.path.join(tempPart, folderStructure[i])))

                    # only log if sub directory already exists
                    else:
                        logging.debug("[%s]: Directory '%s' already exists."
                                      % (self.fileName, os.path.join(targetDirectory, tempPart, folderStructure[i])))

                    tempPart = os.path.join(tempPart, folderStructure[i])
                    i += 1

            except Exception as e:
                logging.exception("[%s]: Creating directory structure for '%s' failed."
                                  % (self.fileName, fileLocation))
                return False

        return True

    def _deleteSubDirectories(self, fileLocation: str, targetDirectory: str) -> bool:
        """
        Internal function that deletes sub directories in the target directory for the given file location if
        they are empty.

        :param fileLocation: location of the file
        :param targetDirectory: location of the target directory
        :return: True or False
        """
        folderStructure = fileLocation.split("/")
        del folderStructure[-1]

        try:
            i = len(folderStructure) - 1
            while 0 <= i:

                tempDir = ""
                for j in range(i + 1):
                    tempDir = os.path.join(tempDir, folderStructure[j])

                # If the directory to delete is not empty then finish
                # the whole sub directory delete process.
                if os.listdir(os.path.join(targetDirectory, tempDir)):
                    break

                logging.debug("[%s]: Deleting directory '%s'."
                              % (self.fileName, os.path.join(targetDirectory, tempDir)))

                os.rmdir(os.path.join(targetDirectory, tempDir))
                i -= 1

        except Exception as e:
            logging.exception("[%s]: Deleting directory structure for '%s' failed."
                              % (self.fileName, fileLocation))
            return False

        return True

    def _downloadFile(self, file_location: str, file_hash: str) -> Optional[io.BufferedRandom]:
        """
        Internal function that downloads the given file into a temporary file and checks if the given hash is correct

        :param file_location: location of the file
        :param file_hash: hash of the file
        :return: None or the handle to the temporary file
        """
        logging.info("[%s]: Downloading file: '%s'" % (self.fileName, file_location))

        # create temporary file
        try:
            fileHandle = tempfile.TemporaryFile(mode='w+b')

        except Exception as e:
            logging.exception("[%s]: Creating temporary file failed." % self.fileName)
            return None

        # Download file from server.
        redirect_ctr = 0
        while True:

            if redirect_ctr > self.max_redirections:
                logging.error("[%s]: Too many redirections during download. Something is wrong with the repository."
                              % self.fileName)
                return None

            try:
                url = os.path.join(self.url, self.repoInstanceLocation, file_location)
                with requests.get(url,
                                  verify=True,
                                  stream=True,
                                  timeout=self.timeout) as r:

                    # Check if server responded correctly
                    # => download file
                    r.raise_for_status()

                    # get the size of the response
                    fileSize = -1
                    maxChunks = 0
                    try:
                        fileSize = int(r.headers.get('content-type'))

                    except Exception as e:
                        fileSize = -1

                    # Check if the file size was part of the header
                    # and we can output the status of the download
                    showStatus = False
                    if fileSize > 0:
                        showStatus = True
                        maxChunks = int(math.ceil(float(fileSize) / float(self.chunkSize)))

                    # Actually download file.
                    chunkCount = 0
                    printedPercentage = 0
                    for chunk in r.iter_content(chunk_size=self.chunkSize):
                        if not chunk:
                            continue
                        fileHandle.write(chunk)

                        # output status of the download
                        chunkCount += 1
                        if showStatus:
                            if chunkCount > maxChunks:
                                showStatus = False
                                logging.warning("[%s]: Content information of received header flawed. Stopping "
                                                % self.fileName
                                                + "to show download status.")
                                continue

                            else:
                                percentage = int((float(chunkCount) / float(maxChunks)) * 100)
                                if (percentage / 10) > printedPercentage:
                                    printedPercentage = percentage / 10

                                    logging.info("[%s]: Download: %d%%" % (self.fileName, printedPercentage * 10))

            except Exception as e:
                logging.exception("[%s]: Downloading file '%s' from the server failed."
                                  % (self.fileName, file_location))
                return None

            # We have downloaded the final file if it is not listed as symlink.
            if file_location not in self.newestSymlinks:
                break

            logging.info("[%s]: File '%s' is symlink." % (self.fileName, file_location))

            # We have downloaded a symlink => read correct location, reset file handle, and download correct file.
            fileHandle.seek(0)
            # The symlink accessed via githubs HTTPS API just contains a string of the target file relative to the
            # current download path.
            base_path = os.path.dirname(file_location)
            file_location = os.path.join(base_path, fileHandle.readline().decode("ascii").strip())
            fileHandle.seek(0)

            logging.info("[%s]: Downloading new location: %s" % (self.fileName, file_location))
            redirect_ctr += 1

        # calculate sha256 hash of the downloaded file
        fileHandle.seek(0)
        sha256Hash = self._sha256File(fileHandle)
        fileHandle.seek(0)

        # check if downloaded file has the correct hash
        if sha256Hash != file_hash:
            logging.error("[%s]: Temporary file does not have the correct hash." % self.fileName)
            logging.debug("[%s]: Temporary file: %s" % (self.fileName, sha256Hash))
            logging.debug("[%s]: Repository: %s" % (self.fileName, file_hash))
            return None

        logging.info("[%s]: Successfully downloaded file: '%s'" % (self.fileName, file_location))
        return fileHandle

    def _sha256File(self, fileHandle: Union[io.TextIOBase, io.BufferedIOBase]) -> str:
        """
        Internal function that calculates the sha256 hash of the file.

        :param fileHandle: file handle for which the hash should be created
        :return: sha256 hash digest
        """
        fileHandle.seek(0)
        sha256 = hashlib.sha256()
        while True:
            data = fileHandle.read(128)
            if not data:
                break
            sha256.update(data)
        return sha256.hexdigest()

    def _getInstanceInformation(self) -> bool:
        """
        Internal function that gets the newest instance information from the online repository.

        :return: True or False
        """
        if self.repoInfo is None or self.repoInstanceLocation is None:
            try:
                if self._getRepositoryInformation() is False:
                    raise ValueError("Not able to get newest repository information.")

            except Exception as e:
                logging.exception("[%s]: Retrieving newest repository information failed." % self.fileName)
                return False

        logging.debug("[%s]: Downloading instance information." % self.fileName)

        # get instance information string from the server
        instanceInfoString = ""
        try:
            url = os.path.join(self.url, self.repoInstanceLocation, "instanceInfo.json")
            with requests.get(url,
                              verify=True,
                              timeout=self.timeout) as r:
                r.raise_for_status()
                instanceInfoString = r.text

        except Exception as e:
            logging.exception("[%s]: Getting instance information failed." % self.fileName)
            return False

        # parse instance information string
        try:
            self.instanceInfo = json.loads(instanceInfoString)

            if not isinstance(self.instanceInfo["version"], float):
                raise ValueError("Key 'version' is not of type float.")

            if not isinstance(self.instanceInfo["rev"], int):
                raise ValueError("Key 'rev' is not of type int.")

            if not isinstance(self.instanceInfo["dependencies"], dict):
                raise ValueError("Key 'dependencies' is not of type dict.")

            # Check if symlinks exist to be compatible with version 1 repositories.
            if "symlinks" in self.instanceInfo.keys():
                if not isinstance(self.instanceInfo["symlinks"], list):
                    raise ValueError("Key 'symlinks' is not of type list.")

        except Exception as e:
            logging.exception("[%s]: Parsing instance information failed." % self.fileName)
            return False

        return True

    def _getRepositoryInformation(self) -> bool:
        """
        Internal function that gets the newest repository information from the online repository.

        :return: True or False
        """
        logging.debug("[%s]: Downloading repository information." % self.fileName)

        # get repository information from the server
        repoInfoString = ""
        try:
            url = os.path.join(self.url, "repoInfo.json")
            with requests.get(url,
                              verify=True,
                              timeout=self.timeout) as r:
                r.raise_for_status()
                repoInfoString = r.text

        except Exception as e:
            logging.exception("[%s]: Getting repository information failed." % self.fileName)
            return False

        # parse repository information string
        try:
            self.repoInfo = json.loads(repoInfoString)

            if not isinstance(self.repoInfo, dict):
                raise ValueError("Received repository information is not of type dict.")

            if "instances" not in self.repoInfo.keys():
                raise ValueError("Received repository information has no information about the instances.")

            if self.instance not in self.repoInfo["instances"].keys():
                raise ValueError("Instance '%s' is not managed by used repository." % self.instance)

            if "version" in self.repoInfo.keys():
                self.repo_version = self.repoInfo["version"]

            logging.debug("[%s]: Repository version: %d" % (self.fileName, self.repo_version))

        except Exception as e:
            logging.exception("[%s]: Parsing repository information failed." % self.fileName)
            return False

        if self.repo_version not in self.supported_versions:
            logging.error("[%s]: Updater is not compatible with repository "
                          % self.fileName
                          + "(Repository version: %d; Supported versions: %s)."
                          % (self.repo_version, ", ".join([str(i) for i in self.supported_versions])))
            logging.error("[%s]: Please visit https://github.com/sqall01/alertR/wiki/Update "
                          % self.fileName
                          + "to see how to fix this issue.")
            return False

        # Set repository location on server.
        self.repoInstanceLocation = str(self.repoInfo["instances"][self.instance]["location"])

        return True

    def _getNewestVersionInformation(self) -> bool:
        """
        Internal function that gets the newest version information from the online repository.

        :return: True or False
        """
        try:
            if self._getInstanceInformation() is False:
                raise ValueError("Not able to get newest instance information.")

        except Exception as e:
            logging.exception("[%s]: Retrieving newest instance information failed." % self.fileName)
            return False

        # Parse version information.
        try:
            version = float(self.instanceInfo["version"])
            rev = int(self.instanceInfo["rev"])
            newestFiles = self.instanceInfo["files"]

            # Check if symlinks exist to be compatible with version 1 repositories.
            if "symlinks" in self.instanceInfo.keys():
                newestSymlinks = self.instanceInfo["symlinks"]
            else:
                newestSymlinks = []

            if not isinstance(newestFiles, dict):
                raise ValueError("Key 'files' is not of type dict.")

            if not isinstance(newestSymlinks, list):
                raise ValueError("Key 'symlinks' is not of type list.")

        except Exception as e:
            logging.exception("[%s]: Parsing version information failed." % self.fileName)
            return False

        logging.debug("[%s]: Newest version information: %.3f-%d." % (self.fileName, version, rev))

        # check if the version on the server is newer than the used one
        # or we have no information about the files
        # => update information
        if (version > self.newestVersion
           or (rev > self.newestRev and version == self.newestVersion)
           or self.newestFiles is None
           or self.newestSymlinks is None):

            # update newest known version information
            self.newestVersion = version
            self.newestRev = rev
            self.newestFiles = newestFiles
            self.newestSymlinks = newestSymlinks

        self.lastChecked = int(time.time())
        return True

    def getInstanceInformation(self) -> Dict[str, Any]:
        """
        This function returns the instance information data.

        :return: instance information data.
        """
        self._acquireLock()
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.lastChecked) > 60 or self.instanceInfo is None:

            if not self._getInstanceInformation():
                self._releaseLock()
                raise ValueError("Not able to get newest instance information.")

        self._releaseLock()
        return self.instanceInfo

    def getRepositoryInformation(self) -> Dict[str, Any]:
        """
        This function returns the repository information data.

        :return: repository information data
        """
        self._acquireLock()
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.lastChecked) > 60 or self.repoInfo is None:

            if not self._getRepositoryInformation():
                self._releaseLock()
                raise ValueError("Not able to get newest repository information.")

        self._releaseLock()
        return self.repoInfo

    def updateInstance(self) -> bool:
        """
        Function that updates this instance of the AlertR infrastructure.

        :return: Success or failure
        """
        self._acquireLock()

        # check all files that have to be updated
        filesToUpdate = self._checkFilesToUpdate()

        if filesToUpdate is None:
            logging.error("[%s] Checking files for update failed." % self.fileName)
            self._releaseLock()
            return False

        if len(filesToUpdate) == 0:
            logging.info("[%s] No files have to be updated." % self.fileName)
            self._releaseLock()
            return True

        # check file permissions of the files that have to be updated
        if self._checkFilePermissions(filesToUpdate) is False:
            logging.info("[%s] Checking file permissions failed." % self.fileName)
            self._releaseLock()
            return False

        # download all files that have to be updated
        downloadedFileHandles = dict()
        for fileToUpdate in filesToUpdate.keys():

            # only download file if it is new or has to be modified
            if (filesToUpdate[fileToUpdate] == _FileUpdateType.NEW
               or filesToUpdate[fileToUpdate] == _FileUpdateType.MODIFY):

                # download new files, if one file fails
                # => close all file handles and abort update process
                downloadedFileHandle = self._downloadFile(fileToUpdate, self.newestFiles[fileToUpdate])

                if downloadedFileHandle is None:
                    logging.error("[%s]: Downloading files from the repository failed. Aborting update process."
                                  % self.fileName)

                    # close all temporary file handles
                    # => temporary file is automatically deleted
                    for fileHandle in downloadedFileHandles.keys():
                        downloadedFileHandles[fileHandle].close()

                    self._releaseLock()
                    return False

                else:
                    downloadedFileHandles[fileToUpdate] = downloadedFileHandle

        # copy all files to the correct location
        for fileToUpdate in filesToUpdate.keys():

            # check if the file has to be deleted
            if filesToUpdate[fileToUpdate] == _FileUpdateType.DELETE:

                # remove old file.
                try:
                    logging.debug("[%s]: Deleting file '%s'." % (self.fileName, fileToUpdate))
                    os.remove(os.path.join(self.instanceLocation, fileToUpdate))

                except Exception as e:
                    logging.exception("[%s]: Deleting file '%s' failed." % (self.fileName, fileToUpdate))
                    self._releaseLock()
                    return False

                # Delete sub directories (if they are empty).
                self._deleteSubDirectories(fileToUpdate, self.instanceLocation)
                continue

            # check if the file is new
            # => create all sub directories (if they are missing)
            elif filesToUpdate[fileToUpdate] == _FileUpdateType.NEW:
                self._createSubDirectories(fileToUpdate, self.instanceLocation)

            # copy file to correct location
            try:
                logging.debug("[%s]: Copying file '%s' to AlertR instance directory." % (self.fileName, fileToUpdate))
                dest = open(os.path.join(self.instanceLocation, fileToUpdate), 'wb')
                shutil.copyfileobj(downloadedFileHandles[fileToUpdate], dest)
                dest.close()

            except Exception as e:
                logging.exception("[%s]: Copying file '%s' failed." % (self.fileName, fileToUpdate))
                self._releaseLock()
                return False

            # check if the hash of the copied file is correct
            f = open(os.path.join(self.instanceLocation, fileToUpdate), 'rb')
            sha256Hash = self._sha256File(f)
            f.close()
            if sha256Hash != self.newestFiles[fileToUpdate]:
                logging.error("[%s]: Hash of file '%s' is not correct after copying." % (self.fileName, fileToUpdate))
                self._releaseLock()
                return False

            # change permission of files that have to be executable
            if fileToUpdate == "alertRclient.py" or fileToUpdate == "alertRserver.py":

                logging.debug("[%s]: Changing permissions of '%s'." % (self.fileName, fileToUpdate))

                try:
                    os.chmod(os.path.join(self.instanceLocation, fileToUpdate),
                             stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

                except Exception as e:
                    logging.exception("[%s]: Changing permissions of '%s' failed." % (self.fileName, fileToUpdate))
                    self._releaseLock()
                    return False

            # Change permission of files that should not be accessible by others.
            elif fileToUpdate == "config/config.xml.template":

                logging.debug("[%s]: Changing permissions of '%s'." % (self.fileName, fileToUpdate))

                try:
                    os.chmod(os.path.join(self.instanceLocation, fileToUpdate),
                             stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)

                except Exception as e:
                    logging.exception("[%s]: Changing permissions of '%s' failed." % (self.fileName, fileToUpdate))
                    self._releaseLock()
                    return False

        # close all temporary file handles
        # => temporary file is automatically deleted
        for fileHandle in downloadedFileHandles.keys():
            downloadedFileHandles[fileHandle].close()

        self._releaseLock()
        return True

    def setInstance(self, instance: str, retrieveInfo: bool = True):
        """
        Sets the instance to the newly given instance. Necessary if globalData does not hold the instance we
        are looking for.

        :param instance: target instance
        :param retrieveInfo: should we directly retrieve all information from the online repository?
        """
        self.instance = instance
        self.instanceInfo = None
        self.lastChecked = 0
        self.repoInfo = None
        self.repoInstanceLocation = None

        if retrieveInfo:
            if not self._getNewestVersionInformation():
                raise ValueError("Not able to get newest repository information.")


# this function checks if the dependencies are satisfied
def check_dependencies(dependencies: Dict[str, Any]) -> bool:

    fileName = os.path.basename(__file__)

    # check if all pip dependencies are met
    if "pip" in dependencies.keys():

        for pip in dependencies["pip"]:

            import_name = pip["import"]
            packet = pip["packet"]

            # only get version if it exists
            version = None
            if "version" in pip.keys():
                version = pip["version"]

            # try to import needed module
            temp = None
            try:
                logging.info("[%s]: Checking module '%s'..." % (fileName, import_name))
                temp = importlib.import_module(import_name)

            except Exception as e:
                try:
                    logging.info("[%s]: Module '%s' not installed. Trying to install it..." % (fileName, import_name))
                    subprocess.check_call([sys.executable, "-m", "pip", "install", packet])
                    temp = importlib.import_module(import_name)
                    
                except Exception as e:
                    logging.error("[%s]: Error installing module '%s'." % (fileName, import_name))
                    print("")
                    print("The needed module '%s' is not installed. " % import_name, end="")
                    print("You can install the module by executing ", end="")
                    print("'pip3 install %s' " % packet, end="")
                    print("(if you do not have installed pip, you can install it ", end="")
                    print("on Debian like systems by executing ", end="")
                    print("'apt-get install python3-pip').")
                    return False
                                      
                else:
                    logging.info("[%s]: Successfully installed module '%s'." % (fileName, import_name))
                
            else:
                logging.info("[%s]: Module '%s' is installed" % (fileName, import_name))    

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
                            break

                        elif int(installedVersion[i]) < int(neededVersion[i]):
                            try:
                                logging.info("[%s]: Module '%s' is too old. Trying to update it..." % (fileName, import_name))
                                subprocess.check_call([sys.executable, "-m", "pip", "install", packet, "--upgrade"])
                                temp = importlib.import_module(import_name)
                                
                            except Exception as e:
                                logging.error("[%s]: Error updating module '%s'." % (fileName, import_name))
                                versionCorrect = False
                                break
                            
                            else:
                                logging.info("[%s]: Successfully updated module '%s'." % (fileName, import_name))

                except Exception as e:
                    logging.error("[%s]: Could not verify installed version of module '%s'." % (fileName, import_name))
                    versionCheckFailed = True

                # if the version check failed, ask the user for confirmation
                if versionCheckFailed is True:
                    print("")
                    print("Could not automatically verify the installed ", end="")
                    print("version of the module '%s'. " % import_name, end="")
                    print("You have to verify the version yourself.")
                    print("")
                    print("Installed version: %s" % installedVersion)
                    print("Needed version: %s" % version)
                    print("")
                    print("Do you have a version installed that satisfies ", end="")
                    print("the needed version?")

                    if not user_confirmation():
                        versionCorrect = False

                    else:
                        versionCorrect = True

                # if the version is not correct => abort the next checks
                if versionCorrect is False:
                    print("")
                    print("The needed version '%s' " % version, end="")
                    print("of module '%s' is not satisfied " % import_name, end="")
                    print("(you have version '%s' " % installedVersion, end="")
                    print("installed).")
                    print("Please update your installed version of the pip ", end="")
                    print("packet '%s'." % packet)
                    return False

    # check if all other dependencies are met
    if "other" in dependencies.keys():

        for other in dependencies["other"]:

            import_name = other["import"]

            # Only get version if it exists.
            version = None
            if "version" in other.keys():
                version = other["version"]

            # try to import needed module
            temp = None
            try:
                logging.info("[%s]: Checking module '%s'." % (fileName, import_name))
                temp = importlib.import_module(import_name)

            except Exception as e:
                logging.error("[%s]: Module '%s' not installed." % (fileName, import_name))
                print("")
                print("The needed module '%s' is not " % import_name, end="")
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
                            break

                        elif int(installedVersion[i]) < int(neededVersion[i]):
                            versionCorrect = False
                            break

                except Exception as e:
                    logging.error("[%s]: Could not verify installed version of module '%s'." % (fileName, import_name))
                    versionCheckFailed = True

                # if the version check failed, ask the user
                # for confirmation
                if versionCheckFailed is True:
                    print("")
                    print("Could not automatically verify the installed ", end="")
                    print("version of the module '%s'. " % import_name, end="")
                    print("You have to verify the version yourself.")
                    print("")
                    print("Installed version: %s" % installedVersion)
                    print("Needed version: %s" % version)
                    print("")
                    print("Do you have a version installed that satisfies ", end="")
                    print("the needed version?")

                    if not user_confirmation():
                        versionCorrect = False

                    else:
                        versionCorrect = True

                # if the version is not correct => abort the next checks
                if versionCorrect is False:
                    print("")
                    print("The needed version '%s' " % version, end="")
                    print("of module '%s' is not satisfied " % import_name, end="")
                    print("(you have version '%s' " % installedVersion, end="")
                    print("installed).")
                    print("Please update your installed version.")
                    return False

    return True


def check_requests_available() -> bool:
    """
    Checks if the module "requests" is available in the correct version.

    :return: True if available
    """

    import_name = "requests"
    version = requests_min_version

    # try to import needed module
    temp = None
    try:
        logging.info("[%s]: Checking module '%s'..." % (fileName, import_name))
        temp = importlib.import_module(import_name)

    except Exception as e:
        logging.error("[%s]: Module '%s' not installed." % (fileName, import_name))
        return False
        
    else:
        logging.info("[%s]: Module '%s' is installed" % (fileName, import_name))    

    version_correct = False
    version_check_failed = False
    installed_version = "Information Not Available"

    # Try to extract version from package.
    try:
        installed_version = temp.__version__.split(".")
        needed_version = version.split(".")

        max_length = 0
        if len(installed_version) > len(needed_version):
            max_length = len(installed_version)

        else:
            max_length = len(needed_version)

        # Check the needed version and the installed version
        for i in range(max_length):
            if int(installed_version[i]) > int(needed_version[i]):
                version_correct = True
                break

            elif int(installed_version[i]) < int(needed_version[i]):
                version_correct = False
                break

    except Exception as e:
        logging.error("[%s]: Could not verify installed version of module '%s'." % (fileName, import_name))
        version_check_failed = True

    if version_check_failed:
        print("")
        print("Could not automatically verify the installed version of the module '%s'." % import_name)
        print("You have to verify the version yourself.")
        print("")
        print("Installed version: %s" % installed_version)
        print("Needed version: %s" % version)
        print("")
        print("Do you have a version installed that satisfies the needed version?")

        if not user_confirmation():
            version_correct = False

        else:
            version_correct = True

    return version_correct


# this function lists all available instances
def list_all_instances(url: str) -> bool:

    # Use "server" as temporary instance for updater class to retrieve repository information.
    updater_obj = Updater(url, "server", "", retrieveInfo=False)
    try:
        repo_info = updater_obj.getRepositoryInformation()
    except Exception as e:
        print(e)
        repo_info = None
    if repo_info is None:
        return False

    temp = list(repo_info["instances"].keys())
    temp.sort()

    print("")

    for instance in temp:

        # Overwrite instance and instance information to force update of instance information.
        updater_obj.setInstance(instance, retrieveInfo=False)
        instance_info = updater_obj.getInstanceInformation()

        print(repo_info["instances"][instance]["name"])
        print("-"*len(repo_info["instances"][instance]["name"]))
        print("Instance:")
        print(instance)
        print("")
        print("Type:")
        print(repo_info["instances"][instance]["type"])
        print("")
        print("Version:")
        print("%.3f-%d" % (instance_info["version"], instance_info["rev"]))
        print("")
        print("Dependencies:")

        # print instance dependencies
        idx = 1
        if "pip" in instance_info["dependencies"].keys():
            for pip in instance_info["dependencies"]["pip"]:
                import_name = pip["import"]
                packet = pip["packet"]
                print("%d: %s (pip packet: %s)" % (idx, import_name, packet), end="")
                if "version" in pip.keys():
                    print(" (lowest version: %s)" % pip["version"])
                else:
                    print("")
                idx += 1

        if "other" in instance_info["dependencies"].keys():
            for other in instance_info["dependencies"]["other"]:
                import_name = other["import"]
                print("%d: %s" % (idx, import_name), end="")
                if "version" in other.keys():
                    print("(lowest version: %s)" % other["version"])
                else:
                    print("")
                idx += 1

        if idx == 1:
            print("None")

        print("")
        print("Description:")
        print(repo_info["instances"][instance]["desc"])
        print("")
        print("")


def output_failure_and_exit():
    print("")
    print("INSTALLATION FAILED!")
    print("To see the reason take a look at the installation process output.", end="")
    print("You can change the log level in the file to 'DEBUG'", end="")
    print("and repeat the installation process to get more detailed information.")
    sys.exit(1)


# this function asks the user for confirmation
def user_confirmation() -> bool:

    while True:
        try:
            localInput = input("(y/n): ")
        except KeyboardInterrupt:
            print("Bye.")
            sys.exit(0)
        except Exception:
            continue

        if localInput.strip().upper() == "Y":
            return True
        elif localInput.strip().upper() == "N":
            return False
        else:
            print("Invalid input.")


if __name__ == '__main__':

    # initialize logging
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=loglevel)

    fileName = os.path.basename(__file__)

    # parsing command line options
    parser = optparse.OptionParser()

    parser.formatter = optparse.TitledHelpFormatter()

    parser.description = "Downloads an AlertR instance from the online repository."

    parser.epilog = "Example command to install the AlertR server instance: " \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "'python3 %s -i server -t /home/alertr/' " % sys.argv[0] \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "Example command to list all available AlertR instances: " \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "'python3 %s -l' " % sys.argv[0] \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "For more detailed examples how to install an AlertR instance " \
                    + "please visit: " \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "https://github.com/sqall01/alertR/wiki/Installation"

    installationGroup = optparse.OptionGroup(parser,
                                             "Arguments needed to install an AlertR instance")
    installationGroup.add_option("-i",
                                 "--instance",
                                 dest="instance",
                                 action="store",
                                 help="Instance that should be installed (use --list to get a list "
                                      + "of all available AlertR instances). (Required)",
                                 default=None)
    installationGroup.add_option("-t",
                                 "--target",
                                 dest="targetDirectory",
                                 action="store",
                                 help="The target directory into which the chosen AlertR instance"
                                      + " should be installed. (Required)",
                                 default=None)
    installationGroup.add_option("-f",
                                 "--force",
                                 dest="force",
                                 action="store_true",
                                 help="Do not check the dependencies. Just install it. (Optional)",
                                 default=False)

    listGroup = optparse.OptionGroup(parser,
                                     "Show information about the online repository")
    listGroup.add_option("-l",
                         "--list",
                         dest="list",
                         action="store_true",
                         help="List all available AlertR instances in the repository.",
                         default=False)

    parser.add_option_group(installationGroup)
    parser.add_option_group(listGroup)

    (options, args) = parser.parse_args()

    # Import requests if it is available.
    if check_requests_available():
        import requests

    else:
        print("")
        print("The installation process needs the module 'requests' at least in version '%s' installed."
              % requests_min_version)
        print("You can install the module by executing 'pip3 install requests'.")
        print("If you do not have installed pip, you can install it on Debian like systems by executing ", end="")
        print("'apt-get install python3-pip'.")
        sys.exit(1)

    # list all available instances in the used AlertR repository
    if options.list:
        if list_all_instances(url) is False:
            print("")
            print("Could not list repository information.")
            sys.exit(1)
        sys.exit(0)

    # install the chosen AlertR instance
    elif options.instance is not None and options.targetDirectory is not None:

        instance = options.instance
        targetLocation = options.targetDirectory

        # check if path is an absolute or relative path.
        if targetLocation[:1] != "/":
            targetLocation = os.path.join(os.path.dirname(os.path.abspath(__file__)), targetLocation)

        # check if the chosen target location does exist
        if os.path.exists(targetLocation) is False or os.path.isdir(targetLocation) is False:
            print("")
            print("Chosen target location does not exist.")
            sys.exit(1)

        # Use "server" as temporary instance for updater class to retrieve repository information.
        updater_obj = Updater(url, "server", targetLocation, retrieveInfo=False)
        try:
            repo_info = updater_obj.getRepositoryInformation()
        except Exception as e:
            print(e)
            repo_info = None
        if repo_info is None:
            print("")
            print("Could not download repository information from repository.")
            sys.exit(1)

        # get the correct case of the instance to install
        found = False
        for repo_key in repo_info["instances"].keys():
            if repo_key.upper() == instance.upper():
                instance = repo_key
                found = True
                break
        # check if chosen instance exists
        if not found:
            print("")
            print("Chosen AlertR instance '%s' does not exist in repository." % instance)
            sys.exit(1)

        # Overwrite instance and instance information to force update of instance information.
        updater_obj.setInstance(instance, retrieveInfo=False)
        instance_info = updater_obj.getInstanceInformation()

        if instance_info is None:
            print("")
            print("Could not download instance information from repository.")
            sys.exit(1)

        # extract needed data from instance information
        version = float(instance_info["version"])
        rev = int(instance_info["rev"])
        dependencies = instance_info["dependencies"]

        logging.info("[%s]: Checking the dependencies..." % fileName)

        # check all dependencies this instance needs
        if options.force is False:
            if not check_dependencies(dependencies):
                sys.exit(1)

        else:
            logging.info("[%s]: Ignoring dependency check. Forcing installation." % fileName)

        # Install the chosen AlertR instance
        if updater_obj.updateInstance() is False:
            logging.error("[%s]: Installation failed." % fileName)
            output_failure_and_exit()

        else:
            # Store instance information file manually afterwards.
            try:
                with open(os.path.join(targetLocation, "instanceInfo.json"), 'w') as fp:
                    fp.write(json.dumps(instance_info))

            except Exception:
                logging.exception("[%s]: Not able to store 'instanceInfo.json'." % fileName)
                output_failure_and_exit()

            print("")
            print("INSTALLATION SUCCESSFUL!")
            print("Please configure this AlertR instance before you start it.")

    # no option chosen
    else:
        print("Use --help to get all available options.")
