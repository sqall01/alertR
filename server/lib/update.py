#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import requests
import threading
import os
import time
import json
import hashlib
import tempfile
import shutil
import stat
import math
import io
from .globalData import GlobalData
from typing import Dict, Any, Optional, Union, List


# internal class that is used as an enum to represent the type of file update
class _FileUpdateType:
    NEW = 1
    DELETE = 2
    MODIFY = 3


# this class processes all actions concerning the update process
class Updater:

    def __init__(self,
                 url: str,
                 globalData: GlobalData,
                 localInstanceInfo: Optional[Dict[str, Any]],
                 retrieveInfo: bool = True,
                 timeout: float = 20.0):

        # used for logging
        self.fileName = os.path.basename(__file__)

        # the updater object is not thread safe
        self.updaterLock = threading.Lock()

        # Compatible repository versions.
        self.supported_versions = [1, 2]

        # get global configured data
        self.globalData = globalData
        self.logger = self.globalData.logger
        self.version = self.globalData.version
        self.rev = self.globalData.rev
        self.instance = self.globalData.instance

        # location of this instance
        self.instanceLocation = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

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
        self.logger.debug("[%s]: Acquire lock." % self.fileName)
        self.updaterLock.acquire()

    def _releaseLock(self):
        """
        # Internal function that releases the lock.
        """
        self.logger.debug("[%s]: Release lock." % self.fileName)
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
                self.logger.error("[%s]: Not able to get version information for checking files." % self.fileName)
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
                    self.logger.debug("[%s]: Not changed: '%s'" % (self.fileName, clientFile))
                    continue

                # => if it has changed add it to the list of files to update
                else:
                    self.logger.debug("[%s]: New version: '%s'" % (self.fileName, clientFile))
                    filesToUpdate[clientFile] = _FileUpdateType.MODIFY
                    counterUpdate += 1

            # => if the file does not exist, just add it
            else:
                self.logger.debug("[%s]: New file: '%s'" % (self.fileName, clientFile))
                filesToUpdate[clientFile] = _FileUpdateType.NEW
                counterNew += 1

        # Get all files that have to be deleted.
        for clientFile in self.localInstanceInfo["files"].keys():

            if clientFile not in fileList:
                self.logger.debug("[%s]: Delete file: '%s'" % (self.fileName, clientFile))
                filesToUpdate[clientFile] = _FileUpdateType.DELETE
                counterDelete += 1

        self.logger.info("[%s]: Files to modify: %d; New files: %d; Files to delete: %d"
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
                    self.logger.error("[%s]: File '%s' is not writable." % (self.fileName, clientFile))
                    return False

                self.logger.debug("[%s]: File '%s' is writable." % (self.fileName, clientFile))

            # check if the file is new and has to be created
            elif filesToUpdate[clientFile] == _FileUpdateType.NEW:
                self.logger.debug("[%s]: Checking write permissions for new file: '%s'"
                                  % (self.fileName, clientFile))

                folderStructure = clientFile.split("/")

                # check if the new file is located in the root directory
                # of the instance
                # => check root directory of the instance for write permissions
                if len(folderStructure) == 1:
                    if not os.access(self.instanceLocation, os.W_OK):
                        self.logger.error("[%s]: Folder './' is not writable." % self.fileName)
                        return False

                    self.logger.debug("[%s]: Folder './' is writable." % self.fileName)

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
                                self.logger.error("[%s]: Folder '%s' is not writable."
                                                  % (self.fileName, os.path.join(tempPart, filePart)))
                                return False

                            self.logger.debug("[%s]: Folder '%s' is writable."
                                              % (self.fileName, os.path.join(tempPart, filePart)))

                            tempPart = os.path.join(tempPart, filePart)

            # check if the file has to be deleted
            elif filesToUpdate[clientFile] == _FileUpdateType.DELETE:

                # check if the file is not writable
                # => cancel update
                if not os.access(os.path.join(self.instanceLocation, clientFile), os.W_OK):
                    self.logger.error("[%s]: File '%s' is not writable (deletable)."
                                      % (self.fileName, clientFile))
                    return False

                self.logger.debug("[%s]: File '%s' is writable (deletable)."
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
                        self.logger.debug("[%s]: Creating directory '%s'."
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
                        self.logger.debug("[%s]: Directory '%s' already exists."
                                          % (self.fileName, os.path.join(targetDirectory, tempPart, folderStructure[i])))

                    tempPart = os.path.join(tempPart, folderStructure[i])
                    i += 1

            except Exception as e:
                self.logger.exception("[%s]: Creating directory structure for '%s' failed."
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

                self.logger.debug("[%s]: Deleting directory '%s'."
                                  % (self.fileName, os.path.join(targetDirectory, tempDir)))

                os.rmdir(os.path.join(targetDirectory, tempDir))
                i -= 1

        except Exception as e:
            self.logger.exception("[%s]: Deleting directory structure for '%s' failed."
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
        self.logger.info("[%s]: Downloading file: '%s'" % (self.fileName, file_location))

        # create temporary file
        try:
            fileHandle = tempfile.TemporaryFile(mode='w+b')

        except Exception as e:
            self.logger.exception("[%s]: Creating temporary file failed." % self.fileName)
            return None

        # Download file from server.
        redirect_ctr = 0
        while True:

            if redirect_ctr > self.max_redirections:
                self.logger.error("[%s]: Too many redirections during download. Something is wrong with the repository."
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
                                self.logger.warning("[%s]: Content information of received header flawed. Stopping "
                                                    % self.fileName
                                                    + "to show download status.")
                                continue

                            else:
                                percentage = int((float(chunkCount) / float(maxChunks)) * 100)
                                if (percentage / 10) > printedPercentage:
                                    printedPercentage = percentage / 10

                                    self.logger.info("[%s]: Download: %d%%" % (self.fileName, printedPercentage * 10))

            except Exception as e:
                self.logger.exception("[%s]: Downloading file '%s' from the server failed."
                                      % (self.fileName, file_location))
                return None

            # We have downloaded the final file if it is not listed as symlink.
            if file_location not in self.newestSymlinks:
                break

            self.logger.info("[%s]: File '%s' is symlink." % (self.fileName, file_location))

            # We have downloaded a symlink => read correct location, reset file handle, and download correct file.
            fileHandle.seek(0)
            # The symlink accessed via githubs HTTPS API just contains a string of the target file relative to the
            # current download path.
            base_path = os.path.dirname(file_location)
            file_location = os.path.join(base_path, fileHandle.readline().decode("ascii").strip())
            fileHandle.seek(0)

            self.logger.info("[%s]: Downloading new location: %s" % (self.fileName, file_location))
            redirect_ctr += 1

        # calculate sha256 hash of the downloaded file
        fileHandle.seek(0)
        sha256Hash = self._sha256File(fileHandle)
        fileHandle.seek(0)

        # check if downloaded file has the correct hash
        if sha256Hash != file_hash:
            self.logger.error("[%s]: Temporary file does not have the correct hash." % self.fileName)
            self.logger.debug("[%s]: Temporary file: %s" % (self.fileName, sha256Hash))
            self.logger.debug("[%s]: Repository: %s" % (self.fileName, file_hash))
            return None

        self.logger.info("[%s]: Successfully downloaded file: '%s'" % (self.fileName, file_location))
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
                self.logger.exception("[%s]: Retrieving newest repository information failed." % self.fileName)
                return False

        self.logger.debug("[%s]: Downloading instance information." % self.fileName)

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
            self.logger.exception("[%s]: Getting instance information failed." % self.fileName)
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
            self.logger.exception("[%s]: Parsing instance information failed." % self.fileName)
            return False

        return True

    def _getRepositoryInformation(self) -> bool:
        """
        Internal function that gets the newest repository information from the online repository.

        :return: True or False
        """
        self.logger.debug("[%s]: Downloading repository information." % self.fileName)

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
            self.logger.exception("[%s]: Getting repository information failed." % self.fileName)
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

            self.logger.debug("[%s]: Repository version: %d" % (self.fileName, self.repo_version))

        except Exception as e:
            self.logger.exception("[%s]: Parsing repository information failed." % self.fileName)
            return False

        if self.repo_version not in self.supported_versions:
            self.logger.error("[%s]: Updater is not compatible with repository "
                              % self.fileName
                              + "(Repository version: %d; Supported versions: %s)."
                              % (self.repo_version, ", ".join([str(i) for i in self.supported_versions])))
            self.logger.error("[%s]: Please visit https://github.com/sqall01/alertR/wiki/Update "
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
            self.logger.exception("[%s]: Retrieving newest instance information failed." % self.fileName)
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
            self.logger.exception("[%s]: Parsing version information failed." % self.fileName)
            return False

        self.logger.debug("[%s]: Newest version information: %.3f-%d." % (self.fileName, version, rev))

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
            self.logger.error("[%s] Checking files for update failed." % self.fileName)
            self._releaseLock()
            return False

        if len(filesToUpdate) == 0:
            self.logger.info("[%s] No files have to be updated." % self.fileName)
            self._releaseLock()
            return True

        # check file permissions of the files that have to be updated
        if self._checkFilePermissions(filesToUpdate) is False:
            self.logger.info("[%s] Checking file permissions failed." % self.fileName)
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
                    self.logger.error("[%s]: Downloading files from the repository failed. Aborting update process."
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
                    self.logger.debug("[%s]: Deleting file '%s'." % (self.fileName, fileToUpdate))
                    os.remove(os.path.join(self.instanceLocation, fileToUpdate))

                except Exception as e:
                    self.logger.exception("[%s]: Deleting file '%s' failed." % (self.fileName, fileToUpdate))
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
                self.logger.debug("[%s]: Copying file '%s' to AlertR instance directory." % (self.fileName, fileToUpdate))
                dest = open(os.path.join(self.instanceLocation, fileToUpdate), 'wb')
                shutil.copyfileobj(downloadedFileHandles[fileToUpdate], dest)
                dest.close()

            except Exception as e:
                self.logger.exception("[%s]: Copying file '%s' failed." % (self.fileName, fileToUpdate))
                self._releaseLock()
                return False

            # check if the hash of the copied file is correct
            f = open(os.path.join(self.instanceLocation, fileToUpdate), 'rb')
            sha256Hash = self._sha256File(f)
            f.close()
            if sha256Hash != self.newestFiles[fileToUpdate]:
                self.logger.error("[%s]: Hash of file '%s' is not correct after copying." % (self.fileName, fileToUpdate))
                self._releaseLock()
                return False

            # change permission of files that have to be executable
            if fileToUpdate == "alertRclient.py" or fileToUpdate == "alertRserver.py":

                self.logger.debug("[%s]: Changing permissions of '%s'." % (self.fileName, fileToUpdate))

                try:
                    os.chmod(os.path.join(self.instanceLocation, fileToUpdate),
                             stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

                except Exception as e:
                    self.logger.exception("[%s]: Changing permissions of '%s' failed." % (self.fileName, fileToUpdate))
                    self._releaseLock()
                    return False

            # Change permission of files that should not be accessible by others.
            elif fileToUpdate == "config/config.xml.template":

                self.logger.debug("[%s]: Changing permissions of '%s'." % (self.fileName, fileToUpdate))

                try:
                    os.chmod(os.path.join(self.instanceLocation, fileToUpdate),
                             stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)

                except Exception as e:
                    self.logger.exception("[%s]: Changing permissions of '%s' failed." % (self.fileName, fileToUpdate))
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
