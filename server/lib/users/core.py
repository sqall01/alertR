#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# Class that holds user data information.
class UserData(object):

    def __init__(self,
                 username: str,
                 pwhash: str,
                 nodeType: str,
                 instance: str):
        self.username = username  # type: str
        self.pwhash = pwhash  # type: str
        self.nodeType = nodeType  # type: str
        self.instance = instance  # type: str

    def toList(self):
        return [self.username,
                self.pwhash,
                self.nodeType,
                self.instance]


# Internal abstract class for new user backends.
class _userBackend:

    def areUserCredentialsValid(self, username: str, password: str) -> bool:
        """
        This function checks if the user credentials are valid

        :param username: name of the user
        :param password: password of the user
        :return True or False
        """
        raise NotImplementedError("Abstract class")

    def checkNodeTypeAndInstance(self, username: str, nodeType: str, instance: str) -> bool:
        """
        This function checks if the node type and instance of the client is correct

        :param username: name of the user
        :param nodeType: type of the node (alert, manager, sensor, server)
        :param instance: exact instance of the node
        :return True or False
        """
        raise NotImplementedError("Abstract class")

    def userExists(self, username: str) -> bool:
        """
        This function checks if the user exists.

        :param username: name of the user
        :return True or False
        """
        raise NotImplementedError("Abstract class")

    def writeUserdata(self):
        """
        This function writes the currently cached user data back to the backend.
        """
        raise NotImplementedError("Abstract class")

    def readUserdata(self):
        """
        This function reads the user data from the backend and updates the current cached one.
        """
        raise NotImplementedError("Abstract class")

    def addUser(self, username: str, password: str, nodeType: str, instance: str) -> bool:
        """
        This function adds the user to the backend and returns if it was successful.

        :param username: name of the user
        :param password: password of the user
        :param nodeType: type of the node (alert, manager, sensor, server)
        :param instance: exact instance of the node
        :return True or False
        """
        raise NotImplementedError("Abstract class")

    def deleteUser(self, username: str) -> bool:
        """
        This function deletes the user from the backend and returns if it was successful.

        :param username: name of the user
        :return True or False
        """
        raise NotImplementedError("Abstract class")

    def changePassword(self, username: str, password: str) -> bool:
        """
        This function changes the password of the user and returns if it was successful.

        :param username: name of the user
        :param password: password of the user
        :return True or False
        """
        raise NotImplementedError("Abstract class")

    def changeNodeTypeAndInstance(self, username: str, nodeType: str, instance: str) -> bool:
        """
        This function changes the node type and instance of the user and returns if it was successful.

        :param username: name of the user
        :param nodeType: type of the node (alert, manager, sensor, server)
        :param instance: exact instance of the node
        :return True or False
        """
        raise NotImplementedError("Abstract class")
