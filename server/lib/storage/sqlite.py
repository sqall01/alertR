#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import threading
import time
import socket
import struct
import hashlib
import logging
import sqlite3
from typing import Any, Optional, List, Union, Tuple, Dict
from .core import _Storage
from ..localObjects import Node, Alert, Manager, Sensor, SensorData, Option
from ..globalData.globalData import GlobalData
# noinspection PyProtectedMember
from ..globalData.sensorObjects import SensorDataGPS, SensorDataNone, SensorDataFloat, SensorDataInt, _SensorData, \
    SensorDataType


class Sqlite(_Storage):

    def __init__(self,
                 storagePath: str,
                 globalData: GlobalData,
                 read_only: bool = False):

        self.globalData = globalData
        self.logger = self.globalData.logger

        # version of server
        self.version = self.globalData.version
        self.rev = self.globalData.rev
        self.dbVersion = self.globalData.dbVersion

        # file nme of this file (used for logging)
        self.log_tag = os.path.basename(__file__)

        # path to the sqlite database
        self.storagePath = storagePath

        # sqlite is not thread safe => use lock
        self.dbLock = threading.Lock()

        mode = ""
        if read_only:
            mode = "?mode=ro"
        uri = "file:" + self.storagePath + mode

        # Check if database already exists.
        create_new = False
        if os.path.exists(self.storagePath) is False:
            self.logger.info("[%s]: No database found. Creating new one." % self.log_tag)
            create_new = True

        self.logger.info("[%s]: Opening database '%s'." % (self.log_tag, uri))
        self.conn = sqlite3.connect(uri,
                                    check_same_thread=False,
                                    uri=True)
        self.cursor = self.conn.cursor()

        if create_new:
            uniqueID = self._generateUniqueId()
            self._createStorage(uniqueID)

        # check if the versions are compatible
        self.checkVersionAndClearConflict()

    def _usernameInDb(self,
                      username: str) -> bool:
        """
        Internal function that checks if the username is known.

        :param username:
        :return: Success or Failure
        """
        # check if the username does exist => if not node is not known
        self.cursor.execute("SELECT id FROM nodes WHERE username = ? ", (username, ))
        result = self.cursor.fetchall()

        # return if username was found or not
        if len(result) == 0:
            return False

        else:
            return True

    def _generateUniqueId(self) -> str:
        """
        Internal function that generates a unique id for this server instance.

        :return: freshly generated unique ID
        """
        # generate unique id for this installation
        utcTimestamp = int(time.time())
        uniqueString = socket.gethostname().encode("ascii") \
                       + struct.pack("d", utcTimestamp) \
                       + os.urandom(200)
        sha256 = hashlib.sha256()
        sha256.update(uniqueString)
        uniqueID = sha256.hexdigest()

        return uniqueID

    def _convertNodeTupleToObj(self,
                               nodeTuple: List[Any]) -> Node:
        """
        Internal function that converts a tuple that is fetched from the
        database by "SELECT * FROM nodes" to an node object.

        :param nodeTuple:
        :return: a node object
        """
        node = Node()
        node.id = nodeTuple[0]
        node.hostname = nodeTuple[1]
        node.username = nodeTuple[2]
        node.nodeType = nodeTuple[3]
        node.instance = nodeTuple[4]
        node.connected = nodeTuple[5]
        node.version = nodeTuple[6]
        node.rev = nodeTuple[7]
        node.persistent = nodeTuple[8]
        return node

    def _getNodeId(self,
                   username: str) -> int:
        """
        Internal function that gets the id of a node when a username is given.

        :param username:
        :return: node id corresponding to username
        """
        # check if the username does exist
        if self._usernameInDb(username):
            # get id of username
            self.cursor.execute("SELECT id FROM nodes WHERE username = ? ", (username, ))
            result = self.cursor.fetchall()
            return result[0][0]

        else:
            raise ValueError("Node id was not found.")

    def _getAlertById(self,
                      alertId: int,
                      logger: logging.Logger = None) -> Optional[Alert]:
        """
        Internal function that gets the alert from the database given by its id.

        :param alertId:
        :param logger:
        :return: an alert object or None
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        alert = None
        try:
            self.cursor.execute("SELECT * FROM alerts WHERE id = ?", (alertId, ))

            result = self.cursor.fetchall()

            if len(result) == 1:
                alert = Alert()
                alert.alertId = result[0][0]
                alert.nodeId = result[0][1]
                alert.clientAlertId = result[0][2]
                alert.description = result[0][3]

                # Set alert levels for alert.
                alertLevels = self._getAlertAlertLevels(alert.alertId, logger)
                if alertLevels is None:
                    logger.error("[%s]: Not able to get alert levels for alert with id %d."
                                 % (self.log_tag, alert.alertId))
                    return None

                alert.alertLevels = alertLevels

        except Exception as e:
            logger.exception("[%s]: Not able to get alert with id %d." % (self.log_tag, alertId))
            return None

        return alert

    def _getManagerById(self,
                        managerId: int,
                        logger: logging.Logger = None) -> Optional[Manager]:
        """
        Internal function that gets the manager from the database given by its id.

        :param managerId:
        :param logger:
        :return: a manager object or None
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        manager = None
        try:
            self.cursor.execute("SELECT * FROM managers WHERE id = ?", (managerId, ))

            result = self.cursor.fetchall()

            if len(result) == 1:
                manager = Manager()
                manager.managerId = result[0][0]
                manager.nodeId = result[0][1]
                manager.description = result[0][2]

        except Exception as e:
            logger.exception("[%s]: Not able to get manager with id %d." % (self.log_tag, managerId))
            return None

        return manager

    def _getNodeById(self,
                     nodeId: int,
                     logger: logging.Logger = None) -> Optional[Node]:
        """
        Internal function that gets the node from the database given by its id.

        :param nodeId:
        :param logger:
        :return: a node object or None
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        try:
            self.cursor.execute("SELECT * FROM nodes WHERE id = ?", (nodeId, ))
            result = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get node with id %d." % (self.log_tag, nodeId))
            return None

        if len(result) == 1:
            try:
                return self._convertNodeTupleToObj(result[0])

            except Exception as e:
                logger.exception("[%s]: Not able to convert node data for id %d to object." % (self.log_tag, nodeId))

        return None

    def _getSensorById(self,
                       sensorId: int,
                       logger: logging.Logger = None) -> Optional[Sensor]:
        """
        Internal function that gets the sensor from the database given by its id.

        :param sensorId:
        :param logger:
        :return: a sensor object or None
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        sensor = None
        try:
            self.cursor.execute("SELECT * FROM sensors WHERE id = ?", (sensorId, ))

            result = self.cursor.fetchall()

            if len(result) == 1:
                sensor = Sensor()
                sensor.sensorId = result[0][0]
                sensor.nodeId = result[0][1]
                sensor.clientSensorId = result[0][2]
                sensor.description = result[0][3]
                sensor.state = result[0][4]
                sensor.lastStateUpdated = result[0][5]
                sensor.alertDelay = result[0][6]
                sensor.dataType = result[0][7]

                # Set alert levels for sensor.
                alertLevels = self._getSensorAlertLevels(sensor.sensorId, logger)
                if alertLevels is None:
                    logger.error("[%s]: Not able to get alert levels for sensor with id %d."
                                 % (self.log_tag, sensor.sensorId))
                    return None

                sensor.alertLevels = alertLevels

                # Extract sensor data.
                if sensor.dataType == SensorDataType.NONE:
                    sensor.data = SensorDataNone()

                elif sensor.dataType == SensorDataType.INT:
                    self.cursor.execute("SELECT value, unit FROM sensorsDataInt WHERE sensorId = ?", (sensor.sensorId, ))
                    subResult = self.cursor.fetchall()

                    if len(subResult) != 1:
                        logger.error("[%s]: Sensor data for sensor with id %d was not found."
                                     % (self.log_tag, sensor.sensorId))
                        return None

                    sensor.data = SensorDataInt(subResult[0][0],
                                                subResult[0][1])

                elif sensor.dataType == SensorDataType.FLOAT:
                    self.cursor.execute("SELECT value, unit FROM sensorsDataFloat WHERE sensorId = ?", (sensor.sensorId, ))
                    subResult = self.cursor.fetchall()

                    if len(subResult) != 1:
                        logger.error("[%s]: Sensor data for sensor with id %d was not found."
                                     % (self.log_tag, sensor.sensorId))
                        return None

                    sensor.data = SensorDataFloat(subResult[0][0],
                                                subResult[0][1])

                elif sensor.dataType == SensorDataType.GPS:
                    self.cursor.execute("SELECT lat, lon, utctime FROM sensorsDataGPS WHERE sensorId = ?",
                                        (sensor.sensorId, ))
                    subResult = self.cursor.fetchall()

                    if len(subResult) != 1:
                        logger.error("[%s]: Sensor data for sensor with id %d was not found."
                                     % (self.log_tag, sensor.sensorId))
                        return None

                    sensor.data = SensorDataGPS(subResult[0][0],
                                                subResult[0][1],
                                                subResult[0][2])

                else:
                    logger.error("[%s]: Not able to get sensor with id %d. Data type in database unknown."
                                 % (self.log_tag, sensor.sensorId))
                    return None

        except Exception as e:
            logger.exception("[%s]: Not able to get sensor with id %d." % (self.log_tag, sensorId))
            return None

        return sensor

    def _getSensorId(self,
                     nodeId: int,
                     clientSensorId: int) -> int:
        """
        Internal function that gets the sensor id of a sensor when the id
        of a node is given and the client sensor id that is used by the node internally.

        :param nodeId:
        :param clientSensorId:
        :return: sensorId or raised Exception
        """
        # get sensorId from database
        self.cursor.execute("SELECT id FROM sensors WHERE nodeId = ? AND clientSensorId = ?", (nodeId, clientSensorId))
        result = self.cursor.fetchall()

        if len(result) != 1:
            raise ValueError("Sensor does not exist in database.")

        sensorId = result[0][0]
        return sensorId

    def _getAlertId(self,
                    nodeId: int,
                    clientAlertId: int) -> int:
        """
        internal function that gets the alert id of an alert when the id
        of a node is given and the client alert id that is used by the node internally.

        :param nodeId:
        :param clientAlertId:
        :return: alertId or raised Exception
        """
        # get alertId from database
        self.cursor.execute("SELECT id FROM alerts WHERE nodeId = ? AND clientAlertId = ?", (nodeId, clientAlertId))
        result = self.cursor.fetchall()

        if len(result) != 1:
            raise ValueError("Alert does not exist in database.")

        alertId = result[0][0]
        return alertId

    def _getManagerId(self,
                      nodeId: int) -> int:
        """
        Internal function that gets the manager id of a manager when the id of a node is given.

        :param nodeId:
        :return: managerId or raised Exception
        """
        # get managerId from database
        self.cursor.execute("SELECT id FROM managers WHERE nodeId = ?", (nodeId, ))
        result = self.cursor.fetchall()

        if len(result) != 1:
            raise ValueError("Manager does not exist in database.")

        managerId = result[0][0]
        return managerId

    def _getUniqueID(self,
                     logger: logging.Logger = None) -> Optional[str]:
        """
        Internal function that gets the unique id from the database.

        :param logger:
        :return: return unique id or None
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        # if unique id already cached => return it
        if self.globalData.uniqueID is not None:
            return self.globalData.uniqueID

        try:
            self.cursor.execute("SELECT value FROM internals WHERE type=?", ("uniqueID", ))
            self.globalData.uniqueID = self.cursor.fetchall()[0][0]

        except Exception as e:
            logger.exception("[%s]: Not able to get the unique id." % self.log_tag)

        return self.globalData.uniqueID

    def _acquireLock(self,
                     logger: logging.Logger = None):
        """
        Internal function that acquires the lock.

        :param logger:
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self.dbLock.acquire()

    def _releaseLock(self,
                     logger: logging.Logger = None):
        """
        Internal function that releases the lock.

        :param logger:
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self.dbLock.release()

    def _createStorage(self,
                       uniqueID: str):
        """
        Internal function that creates the database (should only be called if the database does not exist).
        No return value but raise exception if it fails.

        :param uniqueID:
        """
        # create internals table
        self.cursor.execute("CREATE TABLE internals ("
                            + "type TEXT NOT NULL PRIMARY KEY, "
                            + "value TEXT NOT NULL)")

        # insert version of server
        self.cursor.execute("INSERT INTO internals ("
                            + "type, "
                            + "value) VALUES (?, ?)", ("version", self.version))

        # insert db version of server
        self.cursor.execute("INSERT INTO internals ("
                            + "type, "
                            + "value) VALUES (?, ?)", ("dbversion", self.dbVersion))

        # insert unique id
        self.cursor.execute("INSERT INTO internals ("
                            + "type, "
                            + "value) VALUES (?, ?)", ("uniqueID", uniqueID))

        # create options table
        self.cursor.execute("CREATE TABLE options ("
                            + "type TEXT NOT NULL PRIMARY KEY, "
                            + "value INTEGER NOT NULL)")

        # Insert option which profile is currently used by the system.
        # NOTE: at least one profile with id 0 is enforced during configuration parsing.
        self.cursor.execute("INSERT INTO options ("
                            + "type, "
                            + "value) VALUES (?, ?)", ("profile", 0))

        # create nodes table
        self.cursor.execute("CREATE TABLE nodes ("
                            + "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                            + "hostname TEXT NOT NULL, "
                            + "username TEXT NOT NULL UNIQUE, "
                            + "nodeType TEXT NOT NULL, "
                            + "instance TEXT NOT NULL, "
                            + "connected INTEGER NOT NULL, "
                            + "version REAL NOT NULL, "
                            + "rev INTEGER NOT NULL, "
                            + "persistent INTEGER NOT NULL)")

        # create sensors table
        self.cursor.execute("CREATE TABLE sensors ("
                            + "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                            + "nodeId INTEGER NOT NULL, "
                            + "clientSensorId INTEGER NOT NULL, "
                            + "description TEXT NOT NULL, "
                            + "state INTEGER NOT NULL, "
                            + "lastStateUpdated INTEGER NOT NULL, "
                            + "alertDelay INTEGER NOT NULL, "
                            + "dataType INTEGER NOT NULL, "
                            + "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

        # create sensorsAlertLevels table
        self.cursor.execute("CREATE TABLE sensorsAlertLevels ("
                            + "sensorId INTEGER NOT NULL, "
                            + "alertLevel INTEGER NOT NULL, "
                            + "PRIMARY KEY(sensorId, alertLevel), "
                            + "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

        # Create sensorsDataInt table.
        self.cursor.execute("CREATE TABLE sensorsDataInt ("
                            + "sensorId INTEGER NOT NULL PRIMARY KEY, "
                            + "value INTEGER NOT NULL, "
                            + "unit TEXT NOT NULL, "
                            + "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

        # Create sensorsDataFloat table.
        self.cursor.execute("CREATE TABLE sensorsDataFloat ("
                            + "sensorId INTEGER NOT NULL PRIMARY KEY, "
                            + "value REAL NOT NULL, "
                            + "unit TEXT NOT NULL, "
                            + "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

        # Create sensorsDataGPS table.
        self.cursor.execute("CREATE TABLE sensorsDataGPS ("
                            + "sensorId INTEGER NOT NULL PRIMARY KEY, "
                            + "lat REAL NOT NULL, "
                            + "lon REAL NOT NULL, "
                            + "utctime INTEGER NOT NULL, "
                            + "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

        # create alerts table
        self.cursor.execute("CREATE TABLE alerts ("
                            + "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                            + "nodeId INTEGER NOT NULL, "
                            + "clientAlertId INTEGER NOT NULL, "
                            + "description TEXT NOT NULL, "
                            + "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

        # create alertsAlertLevels table
        self.cursor.execute("CREATE TABLE alertsAlertLevels ("
                            + "alertId INTEGER NOT NULL, "
                            + "alertLevel INTEGER NOT NULL, "
                            + "PRIMARY KEY(alertId, alertLevel), "
                            + "FOREIGN KEY(alertId) REFERENCES alerts(id))")

        # create managers table
        self.cursor.execute("CREATE TABLE managers ("
                            + "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                            + "nodeId INTEGER NOT NULL, "
                            + "description TEXT NOT NULL, "
                            + "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

        # commit all changes
        self.conn.commit()

    def _deleteStorage(self):
        """
        Internal function that deletes the database (should only be called if parts of the database do exist).
        No return value but raise exception if it fails.
        """
        # Delete all tables from the database to clear the old version.
        self.cursor.execute("DROP TABLE IF EXISTS internals")
        self.cursor.execute("DROP TABLE IF EXISTS options")
        self.cursor.execute("DROP TABLE IF EXISTS sensorsAlertLevels")
        self.cursor.execute("DROP TABLE IF EXISTS sensorsDataInt")
        self.cursor.execute("DROP TABLE IF EXISTS sensorsDataFloat")
        self.cursor.execute("DROP TABLE IF EXISTS sensorsDataGPS")
        self.cursor.execute("DROP TABLE IF EXISTS sensors")
        self.cursor.execute("DROP TABLE IF EXISTS alertsAlertLevels")
        self.cursor.execute("DROP TABLE IF EXISTS alerts")
        self.cursor.execute("DROP TABLE IF EXISTS managers")
        self.cursor.execute("DROP TABLE IF EXISTS nodes")

        # Remove tables of former versions.
        self.cursor.execute("DROP TABLE IF EXISTS sensorAlertsDataInt")
        self.cursor.execute("DROP TABLE IF EXISTS sensorAlertsDataFloat")
        self.cursor.execute("DROP TABLE IF EXISTS sensorAlerts")

        # commit all changes
        self.conn.commit()

    def _deleteAlertsForNodeId(self,
                               nodeId: int,
                               logger: logging.Logger = None) -> bool:
        """
        Internal function that deletes all alert data corresponding to the given node id.

        :param nodeId:
        :param logger:
        :return: Returns true if everything worked fine.
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        try:
            # Get all alert ids that are connected to
            # the node.
            self.cursor.execute("SELECT id FROM alerts WHERE nodeId = ?", (nodeId, ))
            result = self.cursor.fetchall()

            # Delete all alert alert levels and alerts of
            # this node
            for alertIdResult in result:

                self.cursor.execute("DELETE FROM alertsAlertLevels WHERE alertId = ?", (alertIdResult[0], ))

                self.cursor.execute("DELETE FROM alerts WHERE id = ?", (alertIdResult[0], ))

            # Commit all changes.
            self.conn.commit()

        except Exception as e:
            logger.exception("[%s]: Not able to delete alerts for node with id %d." % (self.log_tag, nodeId))

            return False

        return True

    def _deleteManagerForNodeId(self,
                                nodeId: int,
                                logger: logging.Logger = None) -> bool:
        """
        Internal function that deletes all manager data corresponding to the given node id.

        :param nodeId:
        :param logger:
        :return: Returns true if everything worked fine.
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        try:
            self.cursor.execute("DELETE FROM managers WHERE nodeId = ?", (nodeId, ))

            # Commit all changes.
            self.conn.commit()

        except Exception as e:
            logger.exception("[%s]: Not able to delete manager for node with id %d." % (self.log_tag, nodeId))
            return False

        return True

    def _deleteSensorsForNodeId(self,
                                nodeId: int,
                                logger: logging.Logger = None) -> bool:
        """
        Internal function that deletes all sensor data corresponding to the given node id.

        :param nodeId:
        :param logger:
        :return: Returns true if everything worked fine.
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        try:
            # Get all sensor ids that are connected to
            # the old sensor.
            self.cursor.execute("SELECT id FROM sensors WHERE nodeId = ? ", (nodeId, ))
            result = self.cursor.fetchall()

            # Delete all data and sensors of this node.
            for sensorIdResult in result:
                self.cursor.execute("DELETE FROM sensorsDataInt WHERE sensorId = ?", (sensorIdResult[0], ))
                self.cursor.execute("DELETE FROM sensorsDataFloat WHERE sensorId = ?", (sensorIdResult[0], ))
                self.cursor.execute("DELETE FROM sensorsDataGPS WHERE sensorId = ?", (sensorIdResult[0], ))
                self.cursor.execute("DELETE FROM sensors WHERE id = ?", (sensorIdResult[0], ))

            # Commit all changes.
            self.conn.commit()

        except Exception as e:
            logger.exception("[%s]: Not able to delete sensors for node with id %d." % (self.log_tag, nodeId))
            return False

        return True

    def _getAlertAlertLevels(self,
                             alertId: int,
                             logger: logging.Logger = None) -> Optional[List[int]]:
        """
        Internal function that gets all alert levels for a specific alert given by alertId.

        :param alertId:
        :param logger:
        :return: list of alertLevels or None
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        try:
            self.cursor.execute("SELECT alertLevel FROM alertsAlertLevels WHERE alertId = ?", (alertId, ))
            result = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get alert levels for alert with id %d." % (self.log_tag, alertId))
            return None

        # return list of alertLevels
        return [x[0] for x in result]

    def _getSensorAlertLevels(self,
                              sensorId: int,
                              logger: logging.Logger = None) -> Optional[List[int]]:
        """
        Internal function that gets all alert levels for a specific sensor given by sensorId.

        :param sensorId:
        :param logger:
        :return: list of alertLevel or None
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        try:
            self.cursor.execute("SELECT alertLevel FROM sensorsAlertLevels WHERE sensorId = ?", (sensorId, ))
            result = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get alert levels for sensor with id %d." % (self.log_tag, sensorId))

            # return None if action failed
            return None

        # return list of alertLevel
        return [x[0] for x in result]

    def _insertSensorData(self,
                          sensorId: int,
                          dataType: int,
                          data: _SensorData,
                          logger: logging.Logger = None) -> bool:
        """
        Internal function that inserts sensor data according to its type.

        :param sensorId:
        :param dataType:
        :param data:
        :param logger:
        :return: true if everything worked fine.
        """
        # Depending on the data type of the sensor add it to the
        # corresponding table.
        if dataType == SensorDataType.NONE:
            return True

        elif dataType == SensorDataType.INT:
            try:
                # noinspection PyUnresolvedReferences
                self.cursor.execute("INSERT INTO sensorsDataInt (sensorId, value, unit) VALUES (?, ?, ?)",
                                    (sensorId, data.value, data.unit))

            except Exception as e:
                logger.exception("[%s]: Not able to add sensor's integer data." % self.log_tag)
                return False

        elif dataType == SensorDataType.FLOAT:
            try:
                # noinspection PyUnresolvedReferences
                self.cursor.execute("INSERT INTO sensorsDataFloat (sensorId, value, unit) VALUES (?, ?, ?)",
                                    (sensorId, data.value, data.unit))

            except Exception as e:
                logger.exception("[%s]: Not able to add sensor's floating point data." % self.log_tag)
                return False

        elif dataType == SensorDataType.GPS:
            try:
                # noinspection PyUnresolvedReferences
                self.cursor.execute("INSERT INTO sensorsDataGPS (sensorId, lat, lon, utctime) VALUES (?, ?, ?, ?)",
                                    (sensorId, data.lat, data.lon, data.utctime))

            except Exception as e:
                logger.exception("[%s]: Not able to add sensor's GPS data." % self.log_tag)
                return False

        else:
            logger.error("[%s]: Data type not known. Not able to add sensor." % self.log_tag)
            return False

        return True


    def checkVersionAndClearConflict(self,
                                     logger: logging.Logger = None):

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # get version from the current database
        self.cursor.execute("SELECT value FROM internals WHERE type = ?", ("dbversion", ))
        result = self.cursor.fetchall()

        # In case the current database does not have any db version
        # set it.
        if result:
            currDbVersion = int(result[0][0])

        else:
            currDbVersion = -1

        # If the versions are not compatible
        # => update database schema.
        if currDbVersion < self.dbVersion:

            logger.info("[%s]: Needed database version '%d' not compatible with current database layout version '%d'. "
                        % (self.log_tag, self.dbVersion, currDbVersion)
                        + "Updating database.")

            # get old uniqueId to keep it
            uniqueID = self._getUniqueID()
            if uniqueID is None:
                uniqueID = self._generateUniqueId()

            self._deleteStorage()

            # create new database
            self._createStorage(uniqueID)

            # commit all changes
            self.conn.commit()

        # Raise an exception if database layout version
        # is newer than the one we need.
        elif currDbVersion > self.dbVersion:
            raise ValueError("Current database layout version ('%d') newer than the one this server uses ('%d')."
                             % (currDbVersion, self.dbVersion))

        self._releaseLock(logger)

    def addNode(self,
                username: str,
                hostname: str,
                nodeType: str,
                instance: str,
                version: float,
                rev: int,
                persistent: int,
                logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # check if a node with the same username already exists
        # => if not add node
        if not self._usernameInDb(username):

            logger.info("[%s]: Node with username '%s' does not exist in database. Adding it."
                        % (self.log_tag, username))

            try:
                # NOTE: connection state is changed later on
                # in the registration process
                self.cursor.execute("INSERT INTO nodes ("
                                    + "hostname, "
                                    + "username, "
                                    + "nodeType, "
                                    + "instance, "
                                    + "connected, "
                                    + "version, "
                                    + "rev, "
                                    + "persistent) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                    (hostname, username, nodeType, instance, 0, version, rev, persistent))

            except Exception as e:
                logger.exception("[%s]: Not able to add node." % self.log_tag)
                self._releaseLock(logger)
                return False

        # if a node with this username exists
        # => check if everything is the same
        else:
            logger.info("[%s]: Node with username '%s' already exists in database."
                        % (self.log_tag, username))

            nodeId = self._getNodeId(username)

            # get hostname, nodeType, version, revision, persistent
            try:
                self.cursor.execute("SELECT hostname, "
                                    + "nodeType, "
                                    + "instance, "
                                    + "version, "
                                    + "rev, "
                                    + "persistent "
                                    + "FROM nodes WHERE id = ?",
                                    (nodeId, ))
                result = self.cursor.fetchall()
                dbHostname = result[0][0]
                dbNodeType = result[0][1]
                dbInstance = result[0][2]
                dbVersion = result[0][3]
                dbRev = result[0][4]
                dbPersistent = result[0][5]

            except Exception as e:
                logger.exception("[%s]: Not able to get node information." % self.log_tag)
                self._releaseLock(logger)
                return False

            # change hostname if it had changed
            if dbHostname != hostname:
                logger.info("[%s]: Hostname of node has changed from '%s' to '%s'. Updating database."
                            % (self.log_tag, dbHostname, hostname))

                try:
                    self.cursor.execute("UPDATE nodes SET "
                                        + "hostname = ? "
                                        + "WHERE id = ?",
                                        (hostname, nodeId))

                except Exception as e:
                    logger.exception("[%s]: Not able to update hostname of node." % self.log_tag)
                    self._releaseLock(logger)
                    return False

            # change instance if it had changed
            if dbInstance != instance:
                logger.info("[%s]: Instance of node has changed from '%s' to '%s'. Updating database."
                            % (self.log_tag, dbInstance, instance))

                try:
                    self.cursor.execute("UPDATE nodes SET "
                                        + "instance = ? "
                                        + "WHERE id = ?",
                                        (instance, nodeId))

                except Exception as e:
                    logger.exception("[%s]: Not able to update instance of node." % self.log_tag)
                    self._releaseLock(logger)
                    return False

            # change version if it had changed
            if dbVersion != version:
                logger.info("[%s]: Version of node has changed from '%.3f' to '%.3f'. Updating database."
                            % (self.log_tag, dbVersion, version))

                try:
                    self.cursor.execute("UPDATE nodes SET "
                                        + "version = ? "
                                        + "WHERE id = ?",
                                        (version, nodeId))

                except Exception as e:
                    logger.exception("[%s]: Not able to update version of node." % self.log_tag)
                    self._releaseLock(logger)
                    return False

            # change revision if it had changed
            if dbRev != rev:
                logger.info("[%s]: Revision of node has changed from '%d' to '%d'. Updating database."
                            % (self.log_tag, dbRev, rev))

                try:
                    self.cursor.execute("UPDATE nodes SET "
                                        + "rev = ? "
                                        + "WHERE id = ?",
                                        (rev, nodeId))

                except Exception as e:
                    logger.exception("[%s]: Not able to update revision of node." % self.log_tag)
                    self._releaseLock(logger)
                    return False

            # change persistent if it had changed
            if dbPersistent != persistent:
                logger.info("[%s]: Persistent flag of node has changed from '%d' to '%d'. Updating database."
                            % (self.log_tag, dbPersistent, persistent))

                try:
                    self.cursor.execute("UPDATE nodes SET "
                                        + "persistent = ? "
                                        + "WHERE id = ?",
                                        (persistent, nodeId))

                except Exception as e:
                    logger.exception("[%s]: Not able to update persistent flag of node." % self.log_tag)
                    self._releaseLock(logger)
                    return False

            # if node type has changed
            # => delete sensors/alerts/manager information of old node
            # and change node type
            if dbNodeType != nodeType:
                logger.info("[%s]: Type of node has changed from '%s' to '%s'. Updating database."
                            % (self.log_tag, dbNodeType, nodeType))

                # if old node had type "sensor"
                # => delete all sensors
                if dbNodeType == "sensor":
                    if not self._deleteSensorsForNodeId(nodeId, logger):
                        self._releaseLock(logger)
                        return False

                # if old node had type "alert"
                # => delete all alerts
                elif dbNodeType == "alert":
                    if not self._deleteAlertsForNodeId(nodeId, logger):
                        self._releaseLock(logger)
                        return False

                # if old node had type "manager"
                # => delete all manager information
                elif dbNodeType == "manager":
                    if not self._deleteManagerForNodeId(nodeId, logger):
                        self._releaseLock(logger)
                        return False

                # if old node had type "server"
                # => delete all sensor information
                elif dbNodeType == "server":
                    if not self._deleteSensorsForNodeId(nodeId, logger):
                        self._releaseLock(logger)
                        return False

                # node type in database not known
                else:
                    logger.error("[%s]: Unknown node type when deleting old sensors/alerts/manager information."
                                 % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # update node type
                try:
                    self.cursor.execute("UPDATE nodes SET "
                                        + "nodeType = ? "
                                        + "WHERE id = ?",
                                        (nodeType, nodeId))

                except Exception as e:
                    logger.exception("[%s]: Not able to update type of node." % self.log_tag)
                    self._releaseLock(logger)
                    return False

        # commit all changes
        self.conn.commit()

        self._releaseLock(logger)
        return True

    def addSensors(self,
                   username: str,
                   sensors: List[Dict[str, Any]],
                   logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # get the id of the node
        try:
            nodeId = self._getNodeId(username)

        except Exception as e:
            logger.exception("[%s]: Not able to get node id." % self.log_tag)
            self._releaseLock(logger)
            return False

        # add/update all sensors
        for sensor in sensors:

            # Extract sensor data.
            sensor_data_class = SensorDataType.get_sensor_data_class(sensor["dataType"])
            sensor_data = sensor_data_class.copy_from_dict(sensor["data"])

            # check if a sensor with the same client id for this node
            # already exists in the database
            self.cursor.execute("SELECT id FROM sensors WHERE nodeId = ? AND clientSensorId = ?",
                                (nodeId, sensor["clientSensorId"]))
            result = self.cursor.fetchall()

            # if the sensor does not exist
            # => add it
            if not result:

                logger.info("[%s]: Sensor with client id '%d' does not exist in database. Adding it."
                            % (self.log_tag, int(sensor["clientSensorId"])))

                # add sensor to database
                try:
                    utcTimestamp = int(time.time())
                    self.cursor.execute("INSERT INTO sensors ("
                                        + "nodeId, "
                                        + "clientSensorId, "
                                        + "description, "
                                        + "state, "
                                        + "lastStateUpdated, "
                                        + "alertDelay, "
                                        + "dataType) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                        (nodeId,
                                         sensor["clientSensorId"],
                                         sensor["description"],
                                         sensor["state"],
                                         utcTimestamp,
                                         sensor["alertDelay"],
                                         sensor["dataType"]))

                except Exception as e:
                    logger.exception("[%s]: Not able to add sensor." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # get sensorId of current added sensor
                sensorId = self.cursor.lastrowid

                # add sensor alert levels to database
                try:
                    for alertLevel in sensor["alertLevels"]:
                        self.cursor.execute("INSERT INTO sensorsAlertLevels ("
                                            + "sensorId, "
                                            + "alertLevel) VALUES (?, ?)",
                                            (sensorId, alertLevel))

                except Exception as e:
                    logger.exception("[%s]: Not able to add sensor's alert levels." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # Depending on the data type of the sensor add it to the corresponding table.
                if not self._insertSensorData(sensorId, sensor["dataType"], sensor_data, logger):
                    logger.error("[%s]: Not able to add data for newly added sensor." % self.log_tag)
                    self._releaseLock(logger)
                    return False

            # if the sensor does already exist
            # => check if everything is the same
            else:
                logger.info("[%s]: Sensor with client id '%d' already exists in database."
                            % (self.log_tag, int(sensor["clientSensorId"])))

                # get sensorId, description, alertDelay and dataType
                try:
                    sensorId = self._getSensorId(nodeId, int(sensor["clientSensorId"]))

                    self.cursor.execute("SELECT description, "
                                        + "alertDelay, "
                                        + "dataType "
                                        + "FROM sensors "
                                        + "WHERE id = ?",
                                        (sensorId, ))
                    result = self.cursor.fetchall()
                    dbDescription = result[0][0]
                    dbAlertDelay = result[0][1]
                    dbDataType = result[0][2]

                except Exception as e:
                    logger.exception("[%s]: Not able to get sensor information." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # change description if it had changed
                if dbDescription != str(sensor["description"]):
                    logger.info("[%s]: Description of sensor has changed from '%s' to '%s'. Updating database."
                                % (self.log_tag, dbDescription, str(sensor["description"])))

                    try:
                        self.cursor.execute("UPDATE sensors SET "
                                            + "description = ? "
                                            + "WHERE id = ?",
                                            (str(sensor["description"]), sensorId))

                    except Exception as e:
                        logger.exception("[%s]: Not able to update description of sensor." % self.log_tag)
                        self._releaseLock(logger)
                        return False

                # change alert delay if it had changed
                if dbAlertDelay != int(sensor["alertDelay"]):
                    logger.info("[%s]: Alert delay of sensor has changed from '%d' to '%d'. Updating database."
                                % (self.log_tag, dbAlertDelay, int(sensor["alertDelay"])))

                    try:
                        self.cursor.execute("UPDATE sensors SET "
                                            + "alertDelay = ? "
                                            + "WHERE id = ?",
                                            (int(sensor["alertDelay"]), sensorId))

                    except Exception as e:
                        logger.exception("[%s]: Not able to update alert delay of sensor." % self.log_tag)
                        self._releaseLock(logger)
                        return False

                # Change data type if it had changed (and remove
                # old data).
                if dbDataType != sensor["dataType"]:
                    logger.info("[%s]: Data type of sensor has changed from '%d' to '%d'. Updating database."
                                % (self.log_tag, dbDataType, sensor["dataType"]))

                    # Remove old data entry of sensor.
                    try:
                        self.cursor.execute("DELETE FROM "
                                            + "sensorsDataInt "
                                            + "WHERE sensorId = ?",
                                            (sensorId, ))
                        self.cursor.execute("DELETE FROM "
                                            + "sensorsDataFloat "
                                            + "WHERE sensorId = ?",
                                            (sensorId, ))
                        self.cursor.execute("DELETE FROM "
                                            + "sensorsDataGPS "
                                            + "WHERE sensorId = ?",
                                            (sensorId, ))

                    except Exception as e:
                        logger.exception("[%s]: Not able to remove old data entry of sensor." % self.log_tag)
                        self._releaseLock(logger)
                        return False

                    # Update data type.
                    try:
                        self.cursor.execute("UPDATE sensors SET "
                                            + "dataType = ? "
                                            + "WHERE id = ?",
                                            (int(sensor["dataType"]), sensorId))

                    except Exception as e:
                        logger.exception("[%s]: Not able to update data type of sensor." % self.log_tag)
                        self._releaseLock(logger)
                        return False

                    # Depending on the data type of the sensor add it to the
                    # corresponding table.
                    if not self._insertSensorData(sensorId, sensor["dataType"], sensor_data, logger):
                        logger.error("[%s]: Not able to add data for changed sensor." % self.log_tag)
                        self._releaseLock(logger)
                        return False

                # get sensor alert levels from database
                try:
                    self.cursor.execute("SELECT alertLevel "
                                        + "FROM sensorsAlertLevels "
                                        + "WHERE sensorId = ? ", (sensorId, ))
                    result = self.cursor.fetchall()

                except Exception as e:
                    logger.exception("[%s]: Not able to get alert levels of the sensor." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # check if the alert levels do already
                # exist in the database
                # => add alert level if it does not
                for alertLevel in sensor["alertLevels"]:
                    # check if alert level already exists
                    found = False
                    for dbAlertLevel in result:
                        if dbAlertLevel[0] == alertLevel:
                            found = True
                            break
                    if found:
                        continue

                    logger.info("[%s]: Alert level '%d' of sensor does not exist in database. Adding it."
                                % (self.log_tag, alertLevel))

                    # add sensor alert level to database
                    self.cursor.execute("INSERT INTO sensorsAlertLevels ("
                                        + "sensorId, "
                                        + "alertLevel) VALUES (?, ?)",
                                        (sensorId, alertLevel))

                # get updated sensor alert levels from database
                try:
                    self.cursor.execute("SELECT alertLevel "
                                        + "FROM sensorsAlertLevels "
                                        + "WHERE sensorId = ? ", (sensorId, ))
                    result = self.cursor.fetchall()

                except Exception as e:
                    logger.exception("[%s]: Not able to get updated alert levels of the sensor." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # check if the alert levels from the database
                # do still exist in the sensor
                # => delete alert level if it does not
                for dbAlertLevel in result:
                    # check if database alert level does exist
                    found = False
                    for alertLevel in sensor["alertLevels"]:
                        if dbAlertLevel[0] == alertLevel:
                            found = True
                            break
                    if found:
                        continue

                    logger.info("[%s]: Alert level '%d' in database does not exist anymore for sensor. Deleting it."
                                % (self.log_tag, dbAlertLevel[0]))

                    self.cursor.execute("DELETE FROM sensorsAlertLevels "
                                        + "WHERE sensorId = ? AND alertLevel = ?",
                                        (sensorId, dbAlertLevel[0]))

        # get updated sensors from database
        try:
            self.cursor.execute("SELECT id, "
                                + "clientSensorId "
                                + "FROM sensors "
                                + "WHERE nodeId = ? ", (nodeId, ))
            result = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get updated sensors from database." % self.log_tag)
            self._releaseLock(logger)
            return False

        # check if the sensors from the database
        # do still exist for the node
        # => delete sensor if it does not
        for dbSensor in result:
            found = False
            for sensor in sensors:
                if dbSensor[1] == int(sensor["clientSensorId"]):
                    found = True
                    break
            if found:
                continue

            logger.info("[%s]: Sensor with client id '%d' in database does not exist anymore for the node. Deleting it."
                        % (self.log_tag, dbSensor[1]))

            try:
                # Delete sensor alertLevels.
                self.cursor.execute("DELETE FROM sensorsAlertLevels "
                                    + "WHERE sensorId = ?",
                                    (dbSensor[0], ))
                # Delete old data entries (if any exist at all).
                self.cursor.execute("DELETE FROM "
                                    + "sensorsDataInt "
                                    + "WHERE sensorId = ?",
                                    (dbSensor[0], ))
                self.cursor.execute("DELETE FROM "
                                    + "sensorsDataFloat "
                                    + "WHERE sensorId = ?",
                                    (dbSensor[0], ))
                self.cursor.execute("DELETE FROM "
                                    + "sensorsDataGPS "
                                    + "WHERE sensorId = ?",
                                    (dbSensor[0], ))

                # Finally, delete sensor.
                self.cursor.execute("DELETE FROM sensors "
                                    + "WHERE id = ?",
                                    (dbSensor[0], ))

            except Exception as e:
                logger.exception("[%s]: Not able to delete sensor." % self.log_tag)
                self._releaseLock(logger)
                return False

        # commit all changes
        self.conn.commit()
        self._releaseLock(logger)
        return True

    def addAlerts(self,
                  username: str,
                  alerts: List[Dict[str, Any]],
                  logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # get the id of the node
        try:
            nodeId = self._getNodeId(username)

        except Exception as e:
            logger.exception("[%s]: Not able to get node id." % self.log_tag)
            self._releaseLock(logger)
            return False

        # add/update all alerts
        for alert in alerts:

            # check if an alert with the same client id for this node
            # already exists in the database
            self.cursor.execute("SELECT id FROM alerts "
                                + "WHERE nodeId = ? AND clientAlertId = ?",
                                (nodeId, int(alert["clientAlertId"])))
            result = self.cursor.fetchall()

            # if the alert does not exist
            # => add it
            if len(result) == 0:
                logger.info("[%s]: Alert with client id '%d' does not exist in database. Adding it."
                            % (self.log_tag, int(alert["clientAlertId"])))

                # add alert to database
                try:
                    self.cursor.execute("INSERT INTO alerts ("
                                        + "nodeId, "
                                        + "clientAlertId, "
                                        + "description) VALUES (?, ?, ?)",
                                        (nodeId,
                                         int(alert["clientAlertId"]),
                                         str(alert["description"])))

                except Exception as e:
                    logger.exception("[%s]: Not able to add alert." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # get alertId of current added alert
                try:
                    alertId = self._getAlertId(nodeId, int(alert["clientAlertId"]))

                except Exception as e:
                    logger.exception("[%s]: Not able to get alertId." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # add alert alert levels to database
                try:
                    for alertLevel in alert["alertLevels"]:
                        self.cursor.execute("INSERT INTO alertsAlertLevels ("
                                            + "alertId, "
                                            + "alertLevel) VALUES (?, ?)",
                                            (alertId, alertLevel))

                except Exception as e:
                    logger.exception("[%s]: Not able to add alert alert levels." % self.log_tag)
                    self._releaseLock(logger)
                    return False

            # if the alert does already exist
            # => check if everything is the same
            else:
                logger.info("[%s]: Alert with client id '%d' already exists in database."
                            % (self.log_tag, int(alert["clientAlertId"])))

                # get alertId and description
                try:
                    alertId = self._getAlertId(nodeId, int(alert["clientAlertId"]))

                    self.cursor.execute("SELECT description "
                                        + "FROM alerts "
                                        + "WHERE id = ?",
                                        (alertId, ))
                    result = self.cursor.fetchall()
                    dbDescription = result[0][0]

                except Exception as e:
                    logger.exception("[%s]: Not able to get alert information." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # change description if it had changed
                if dbDescription != str(alert["description"]):
                    logger.info("[%s]: Description of alert has changed from '%s' to '%s'. Updating database."
                                % (self.log_tag, dbDescription, str(alert["description"])))

                    try:
                        self.cursor.execute("UPDATE alerts SET "
                                            + "description = ? "
                                            + "WHERE id = ?",
                                            (str(alert["description"]), alertId))

                    except Exception as e:
                        logger.exception("[%s]: Not able to update description of alert." % self.log_tag)
                        self._releaseLock(logger)
                        return False

                # get alert alert levels from database
                try:
                    self.cursor.execute("SELECT alertLevel "
                                        + "FROM alertsAlertLevels "
                                        + "WHERE alertId = ? ", (alertId, ))
                    result = self.cursor.fetchall()

                except Exception as e:
                    logger.exception("[%s]: Not able to get alert levels of the alert." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # check if the alert levels do already
                # exist in the database
                # => add alert level if it does not
                for alertLevel in alert["alertLevels"]:
                    # check if alert level already exists
                    found = False
                    for dbAlertLevel in result:
                        if dbAlertLevel[0] == alertLevel:
                            found = True
                            break
                    if found:
                        continue

                    logger.info("[%s]: Alert level '%d' of alert does not exist in database. Adding it."
                                % (self.log_tag, alertLevel))

                    # add alert alert level to database
                    self.cursor.execute("INSERT INTO alertsAlertLevels ("
                                        + "alertId, "
                                        + "alertLevel) VALUES (?, ?)",
                                        (alertId, alertLevel))

                # get updated alert alert levels from database
                try:
                    self.cursor.execute("SELECT alertLevel "
                                        + "FROM alertsAlertLevels "
                                        + "WHERE alertId = ? ", (alertId, ))
                    result = self.cursor.fetchall()

                except Exception as e:
                    logger.exception("[%s]: Not able to get updated alert levels of the alert." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                # check if the alert levels from the database
                # do still exist in the alert
                # => delete alert level if it does not
                for dbAlertLevel in result:
                    # check if database alert level does exist
                    found = False
                    for alertLevel in alert["alertLevels"]:
                        if dbAlertLevel[0] == alertLevel:
                            found = True
                            break
                    if found:
                        continue

                    logger.info("[%s]: Alert level '%d' in database does not exist anymore for alert. Deleting it."
                                % (self.log_tag, dbAlertLevel[0]))
                    self.cursor.execute("DELETE FROM alertsAlertLevels "
                                        + "WHERE alertId = ? AND alertLevel = ?",
                                        (alertId, dbAlertLevel[0]))

        # get updated alerts from database
        try:
            self.cursor.execute("SELECT id, "
                                + "clientAlertId "
                                + "FROM alerts "
                                + "WHERE nodeId = ? ", (nodeId, ))
            result = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get updated alerts from database." % self.log_tag)
            self._releaseLock(logger)
            return False

        # check if the alerts from the database
        # do still exist for the node
        # => delete alert if it does not
        for dbAlert in result:
            found = False
            for alert in alerts:
                if dbAlert[1] == int(alert["clientAlertId"]):
                    found = True
                    break
            if found:
                continue

            logger.info("[%s]: Alert with client id '%d' in database does not exist anymore for the node. Deleting it."
                        % (self.log_tag, dbAlert[1]))

            try:
                self.cursor.execute("DELETE FROM alertsAlertLevels "
                                    + "WHERE alertId = ?",
                                    (dbAlert[0], ))
                self.cursor.execute("DELETE FROM alerts "
                                    + "WHERE id = ?",
                                    (dbAlert[0], ))

            except Exception as e:
                logger.exception("[%s]: Not able to delete alert." % self.log_tag)
                self._releaseLock(logger)
                return False

        # commit all changes
        self.conn.commit()
        self._releaseLock(logger)
        return True

    def addManager(self,
                   username: str,
                   manager: Dict[str, Any],
                   logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # get the id of the node
        try:
            nodeId = self._getNodeId(username)

        except Exception as e:
            logger.exception("[%s]: Not able to get node id." % self.log_tag)
            self._releaseLock(logger)
            return False

        # check if a manager with the same node id
        # already exists in the database
        self.cursor.execute("SELECT id FROM managers "
                            + "WHERE nodeId = ?",
                            (nodeId, ))
        result = self.cursor.fetchall()

        # if the manager does not exist
        # => add it
        if len(result) == 0:
            logger.info("[%s]: Manager does not exist in database. Adding it." % self.log_tag)

            # add manager to database
            try:
                self.cursor.execute("INSERT INTO managers ("
                                    + "nodeId, "
                                    + "description) VALUES (?, ?)",
                                    (nodeId,
                                     str(manager["description"])))

            except Exception as e:
                logger.exception("[%s]: Not able to add manager." % self.log_tag)
                self._releaseLock(logger)
                return False

        # if the manager does already exist
        # => check if everything is the same
        else:
            logger.info("[%s]: Manager already exists in database." % self.log_tag)

            # get managerId and description
            try:
                managerId = self._getManagerId(nodeId)
                self.cursor.execute("SELECT description "
                                    + "FROM managers "
                                    + "WHERE id = ?",
                                    (managerId, ))
                result = self.cursor.fetchall()
                dbDescription = result[0][0]

            except Exception as e:
                logger.exception("[%s]: Not able to get manager information." % self.log_tag)
                self._releaseLock(logger)
                return False

            # change description if it had changed
            if dbDescription != str(manager["description"]):
                logger.info("[%s]: Description of manager has changed from '%s' to '%s'. Updating database."
                            % (self.log_tag, dbDescription, str(manager["description"])))

                try:
                    self.cursor.execute("UPDATE managers SET "
                                        + "description = ? "
                                        + "WHERE id = ?",
                                        (str(manager["description"]), managerId))

                except Exception as e:
                    logger.exception("[%s]: Not able to update description of manager." % self.log_tag)
                    self._releaseLock(logger)
                    return False

        # commit all changes
        self.conn.commit()
        self._releaseLock(logger)
        return True

    def getNodeId(self,
                  username: str,
                  logger: logging.Logger = None) -> Optional[int]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        nodeId = None
        try:
            nodeId = self._getNodeId(username)

        except Exception as e:
            logger.exception("[%s]: Not able to get node id." % self.log_tag)

        self._releaseLock(logger)
        return nodeId

    def getNodeIds(self,
                   logger: logging.Logger = None) -> List[int]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        nodeIds = list()
        try:
            self.cursor.execute("SELECT id FROM nodes")
            result = self.cursor.fetchall()

            # Unpack list of tuples of one integer to list of integers.
            nodeIds = [x[0] for x in result]

        except Exception as e:
            logger.exception("[%s]: Not able to get node ids." % self.log_tag)

        self._releaseLock(logger)
        return nodeIds

    def getSensorCount(self,
                       nodeId: str,
                       logger: logging.Logger = None) -> Optional[int]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # get all sensors on this nodes
        sensorCount = None
        try:
            self.cursor.execute("SELECT id FROM sensors "
                                + "WHERE nodeId = ?",
                                (nodeId, ))
            result = self.cursor.fetchall()
            sensorCount = len(result)

        except Exception as e:
            logger.exception("[%s]: Not able to get sensor count." % self.log_tag)

        self._releaseLock(logger)
        return sensorCount

    def getSurveyData(self,
                      logger: logging.Logger = None) -> Optional[List[Tuple[str, float, int]]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        surveyData = None
        try:
            self.cursor.execute("SELECT "
                                + "instance, "
                                + "version, "
                                + "rev "
                                + "FROM nodes")
            surveyData = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get survey data." % self.log_tag)

        self._releaseLock(logger)
        return surveyData

    def getUniqueID(self,
                    logger: logging.Logger = None) -> Optional[str]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)
        uniqueID = self._getUniqueID()
        self._releaseLock(logger)

        return uniqueID

    def updateSensorState(self,
                          nodeId: int,
                          stateList: List[Tuple[int, int]],
                          logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # stateList is a list of tuples of (clientSensorId, state)
        for stateTuple in stateList:

            try:

                # check if the sensor does exist in the database
                self.cursor.execute("SELECT id FROM sensors "
                                    + "WHERE nodeId = ? "
                                    + "AND clientSensorId = ?", (nodeId, stateTuple[0]))
                result = self.cursor.fetchall()
                if len(result) != 1:
                    logger.error("[%s]: Sensor does not exist in database." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                utcTimestamp = int(time.time())
                self.cursor.execute("UPDATE sensors SET "
                                    + "state = ?, "
                                    + "lastStateUpdated = ? "
                                    + "WHERE nodeId = ? "
                                    + "AND clientSensorId = ?",
                                    (stateTuple[1], utcTimestamp, nodeId, stateTuple[0]))

            except Exception as e:
                logger.exception("[%s]: Not able to update sensor state." % self.log_tag)
                self._releaseLock(logger)
                return False

        # commit all changes
        self.conn.commit()
        self._releaseLock(logger)
        return True

    def updateSensorData(self,
                         nodeId: int,
                         dataList: List[Tuple[int, _SensorData]],
                         logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # dataList is a list of tuples of (clientSensorId, data)
        for dataTuple in dataList:

            try:
                # Check if the sensor does exist in the database and get its
                # data type.
                self.cursor.execute("SELECT id, dataType FROM sensors "
                                    + "WHERE nodeId = ? "
                                    + "AND clientSensorId = ?", (nodeId, dataTuple[0]))
                result = self.cursor.fetchall()

                if len(result) != 1:
                    logger.error("[%s]: Sensor does not exist in database." % self.log_tag)
                    self._releaseLock(logger)
                    return False

                sensorId = result[0][0]
                dataType = result[0][1]

                if dataType == SensorDataType.NONE:
                    pass

                elif dataType == SensorDataType.INT:
                    # noinspection PyUnresolvedReferences
                    self.cursor.execute("UPDATE sensorsDataInt SET "
                                        + "value = ?, "
                                        + "unit = ? "
                                        + "WHERE sensorId = ?",
                                        (dataTuple[1].value,
                                         dataTuple[1].unit,
                                         sensorId))

                elif dataType == SensorDataType.FLOAT:
                    # noinspection PyUnresolvedReferences
                    self.cursor.execute("UPDATE sensorsDataFloat SET "
                                        + "value = ?, "
                                        + "unit = ? "
                                        + "WHERE sensorId = ?",
                                        (dataTuple[1].value,
                                         dataTuple[1].unit,
                                         sensorId))

                elif dataType == SensorDataType.GPS:
                    # noinspection PyUnresolvedReferences
                    self.cursor.execute("UPDATE sensorsDataGPS SET "
                                        + "lat = ?, "
                                        + "lon = ?, "
                                        + "utctime = ? "
                                        + "WHERE sensorId = ?",
                                        (dataTuple[1].lat,
                                         dataTuple[1].lon,
                                         dataTuple[1].utctime,
                                         sensorId))

            except Exception as e:
                logger.exception("[%s]: Not able to update sensor data." % self.log_tag)
                self._releaseLock(logger)
                return False

        # commit all changes
        self.conn.commit()
        self._releaseLock(logger)
        return True

    def updateSensorTime(self,
                         sensorId: int,
                         logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # Update time of sensor in the database.
        try:
            utcTimestamp = int(time.time())
            self.cursor.execute("UPDATE sensors SET "
                                + "lastStateUpdated = ? "
                                + "WHERE id = ?",
                                (utcTimestamp, sensorId))

        except Exception as e:
            logger.exception("[%s]: Not able to update sensor time." % self.log_tag)
            self._releaseLock(logger)
            return False

        # commit all changes
        self.conn.commit()
        self._releaseLock(logger)
        return True

    def getSensorId(self,
                    nodeId: int,
                    clientSensorId: int,
                    logger: logging.Logger = None) -> Optional[int]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        try:
            sensorId = self._getSensorId(nodeId, clientSensorId)

        except Exception as e:
            logger.exception("[%s]: Not able to get sensorId from database." % self.log_tag)
            self._releaseLock(logger)
            return None

        self._releaseLock(logger)
        return sensorId

    def getAlertId(self,
                   nodeId: int,
                   clientAlertId: int,
                   logger: logging.Logger = None) -> Optional[int]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        try:
            alertId = self._getAlertId(nodeId, clientAlertId)

        except Exception as e:
            logger.exception("[%s]: Not able to get alertId from database." % self.log_tag)
            self._releaseLock(logger)
            return None

        self._releaseLock(logger)
        return alertId

    def getSensorAlertLevels(self,
                             sensorId: int,
                             logger: logging.Logger = None) -> Optional[List[int]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        result = self._getSensorAlertLevels(sensorId, logger)

        self._releaseLock(logger)

        # return list of alertLevel
        return result

    def getAlertAlertLevels(self,
                            alertId: int,
                            logger: logging.Logger = None) -> Optional[List[int]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        result = self._getAlertAlertLevels(alertId, logger)

        self._releaseLock(logger)

        # return list of alertLevels
        return result

    def deleteNode(self,
                   nodeId: int,
                   logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # Get node type from database.
        nodeObj = self._getNodeById(nodeId, logger)
        if nodeObj is None:
            logger.error("[%s]: Not able to get node with id %d." % (self.log_tag, nodeId))
            self._releaseLock(logger)
            return False

        # Delete all corresponding alert entries from database.
        if nodeObj.nodeType == "alert":

            if not self._deleteAlertsForNodeId(nodeId, logger):
                self._releaseLock(logger)
                return False

        # Delete all corresponding manager entries from database.
        elif nodeObj.nodeType == "manager":

            if not self._deleteManagerForNodeId(nodeId, logger):
                self._releaseLock(logger)
                return False

        # Delete all corresponding sensor entries from database.
        elif nodeObj.nodeType == "sensor":

            if not self._deleteSensorsForNodeId(nodeId, logger):
                self._releaseLock(logger)
                return False

        # Return if we do not know how to handle the node.
        else:
            logger.exception("[%s]: Unknown node type '%s' for node with id %d."
                             % (self.log_tag, nodeObj.nodeType, nodeId))
            self._releaseLock(logger)
            return False

        # Delete node from database.
        try:
            self.cursor.execute("DELETE FROM "
                                + "nodes "
                                + "WHERE id = ?",
                                (nodeId, ))

        except Exception as e:
            logger.exception("[%s]: Not able to delete node with id %d." % (self.log_tag, nodeId))
            self._releaseLock(logger)
            return False

        # commit all changes
        self.conn.commit()
        self._releaseLock(logger)
        return True


    def getAllAlertsAlertLevels(self,
                                logger: logging.Logger = None) -> Optional[List[int]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        try:
            self.cursor.execute("SELECT alertLevel "
                                + "FROM alertsAlertLevels")
            result = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get all alert levels for alert clients." % self.log_tag)
            self._releaseLock(logger)
            # return None if action failed
            return None

        self._releaseLock(logger)

        # return list alertLevels as integer
        return [x[0] for x in result]

    def getAllSensorsAlertLevels(self,
                                 logger: logging.Logger = None) -> Optional[List[int]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        try:
            self.cursor.execute("SELECT alertLevel "
                                + "FROM sensorsAlertLevels")
            result = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get all alert levels for sensors." % self.log_tag)
            self._releaseLock(logger)
            # return None if action failed
            return None

        self._releaseLock(logger)

        # return list alertLevels as integer
        return [x[0] for x in result]

    def getAllConnectedNodeIds(self,
                               logger: logging.Logger = None) -> Optional[List[int]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # get all connected node ids from database
        try:
            self.cursor.execute("SELECT id "
                                + "FROM nodes "
                                + "WHERE connected = ?", (1, ))
            result = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get all connected node ids." % self.log_tag)
            self._releaseLock(logger)
            # return None if action failed
            return None

        self._releaseLock(logger)

        # return list of nodeIds
        return [x[0] for x in result]

    def getAllPersistentNodeIds(self,
                                logger: logging.Logger = None) -> Optional[List[int]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        # get all persistent node ids from database
        try:
            self.cursor.execute("SELECT id "
                                + "FROM nodes "
                                + "WHERE persistent = ?", (1, ))
            result = self.cursor.fetchall()

        except Exception as e:
            logger.exception("[%s]: Not able to get all persistent node ids." % self.log_tag)
            self._releaseLock(logger)
            # return None if action failed
            return None

        self._releaseLock(logger)

        # return list of nodeIds
        return [x[0] for x in result]

    def markNodeAsNotConnected(self,
                               nodeId: int,
                               logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        try:
            self.cursor.execute("UPDATE nodes SET "
                                + "connected = ? WHERE id = ?",
                                (0, nodeId))

        except Exception as e:
            logger.exception("[%s]: Not able to mark node '%d' as not connected." % (self.log_tag, nodeId))
            self._releaseLock(logger)
            return False

        # commit all changes
        self.conn.commit()
        self._releaseLock(logger)
        return True

    def markNodeAsConnected(self,
                            nodeId: int,
                            logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        try:
            self.cursor.execute("UPDATE nodes SET "
                                + "connected = ? WHERE id = ?",
                                (1, nodeId))

        except Exception as e:
            logger.exception("[%s]: Not able to mark node '%d' as connected." % (self.log_tag, nodeId))
            self._releaseLock(logger)
            return False

        # commit all changes
        self.conn.commit()
        self._releaseLock(logger)
        return True

    def getSensorsUpdatedOlderThan(self,
                                   oldestTimeUpdated: int,
                                   logger: logging.Logger = None) -> Optional[List[Sensor]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        sensorList = list()
        try:
            self.cursor.execute("SELECT id "
                                + "FROM sensors "
                                + "WHERE lastStateUpdated < ?",
                                (oldestTimeUpdated, ))

            results = self.cursor.fetchall()

            for resultTuple in results:
                sensorId = resultTuple[0]
                sensor = self._getSensorById(sensorId, logger)
                if sensor is not None:
                    sensorList.append(sensor)

        except Exception as e:
            logger.exception("[%s]: Not able to get sensors from database which update was older than %d."
                             % (self.log_tag, oldestTimeUpdated))
            self._releaseLock(logger)
            return None

        self._releaseLock(logger)

        # return list of sensor objects
        return sensorList

    def getAlertById(self,
                     alertId: int,
                     logger: logging.Logger = None) -> Optional[Alert]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        result = self._getAlertById(alertId, logger)

        self._releaseLock(logger)

        # return an alert object or None
        return result

    def getManagerById(self,
                       managerId: int,
                       logger: logging.Logger = None) -> Optional[Manager]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        result = self._getManagerById(managerId, logger)

        self._releaseLock(logger)

        # return a manager object or None
        return result

    def getNodeById(self,
                    nodeId: int,
                    logger: logging.Logger = None) -> Optional[Node]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        result = self._getNodeById(nodeId, logger)

        self._releaseLock(logger)

        # return a node object or None
        return result

    def getSensorById(self,
                      sensorId: int,
                      logger: logging.Logger = None) -> Optional[Sensor]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        result = self._getSensorById(sensorId, logger)

        self._releaseLock(logger)

        # return a sensor object or None
        return result

    def getNodes(self,
                 logger: logging.Logger = None) -> Optional[List[Node]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        nodes = list()
        try:

            # Get all nodes information.
            self.cursor.execute("SELECT * FROM nodes")
            nodeTuples = self.cursor.fetchall()
            for nodeTuple in nodeTuples:
                node = self._convertNodeTupleToObj(nodeTuple)
                nodes.append(node)

        except Exception as e:
            logger.exception("[%s]: Not able to get nodes from database." % self.log_tag)
            self._releaseLock(logger)
            return None

        self._releaseLock(logger)

        # list(node objects)
        return nodes

    def getAlertSystemInformation(self,
                                  logger: logging.Logger = None) -> Optional[List[List[Union[Option,
                                                                                             Node,
                                                                                             Sensor,
                                                                                             Manager,
                                                                                             Alert]]]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        try:

            # Get all options.
            optionList = list()
            self.cursor.execute("SELECT type, "
                                + "value "
                                + "FROM options")
            results = self.cursor.fetchall()
            for resultTuple in results:
                optionObj = Option()
                optionObj.type = resultTuple[0]
                optionObj.value = resultTuple[1]
                optionList.append(optionObj)

            # Get all nodes.
            nodeList = list()
            self.cursor.execute("SELECT * FROM nodes")
            results = self.cursor.fetchall()
            for resultTuple in results:
                nodeObj = self._convertNodeTupleToObj(resultTuple)
                nodeList.append(nodeObj)

            # Get all sensors.
            sensorList = list()
            self.cursor.execute("SELECT id FROM sensors")
            results = self.cursor.fetchall()
            for resultTuple in results:
                sensorObj = self._getSensorById(resultTuple[0], logger)
                if sensorObj is None:
                    raise ValueError("Can not retrieve sensor with id %d." % resultTuple[0])

                sensorList.append(sensorObj)

            # Get all managers.
            managerList = list()
            self.cursor.execute("SELECT id FROM managers")
            results = self.cursor.fetchall()
            for resultTuple in results:
                managerObj = self._getManagerById(resultTuple[0], logger)
                if managerObj is None:
                    raise ValueError("Can not retrieve manager with id %d." % resultTuple[0])

                managerList.append(managerObj)

            # Get all alerts.
            alertList = list()
            self.cursor.execute("SELECT id FROM alerts")
            results = self.cursor.fetchall()
            for resultTuple in results:
                alertObj = self._getAlertById(resultTuple[0], logger)
                if alertObj is None:
                    raise ValueError("Can not retrieve alert with id %d." % resultTuple[0])

                alertList.append(alertObj)

            # Generate a list with system information.
            alertSystemInformation = list()
            alertSystemInformation.append(optionList)
            alertSystemInformation.append(nodeList)
            alertSystemInformation.append(sensorList)
            alertSystemInformation.append(managerList)
            alertSystemInformation.append(alertList)

        except Exception as e:
            logger.exception("[%s]: Not able to get complete system information from database." % self.log_tag)
            self._releaseLock(logger)
            return None

        self._releaseLock(logger)

        # return a list of
        # list[0] = list(option objects)
        # list[1] = list(node objects)
        # list[2] = list(sensor objects)
        # list[3] = list(manager objects)
        # list[4] = list(alert objects)
        return alertSystemInformation

    def getSensorState(self,
                       sensorId: int,
                       logger: logging.Logger = None) -> Optional[int]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        try:
            # get sensor state from database
            self.cursor.execute("SELECT state "
                                + "FROM sensors "
                                + "WHERE id = ?",
                                (sensorId, ))
            result = self.cursor.fetchall()
            if len(result) != 1:
                logger.error("[%s]: Sensor was not found." % self.log_tag)
                self._releaseLock(logger)
                return None

            state = result[0][0]

        except Exception as e:
            logger.exception("[%s]: Not able to get sensor state from database." % self.log_tag)
            self._releaseLock(logger)
            return None

        self._releaseLock(logger)
        return state

    def getSensorData(self,
                      sensorId: int,
                      logger: logging.Logger = None) -> Optional[SensorData]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        try:
            # Get data type from database.
            self.cursor.execute("SELECT dataType "
                                + "FROM sensors "
                                + "WHERE id = ?",
                                (sensorId, ))
            result = self.cursor.fetchall()
            if len(result) != 1:
                logger.error("[%s]: Sensor was not found." % self.log_tag)
                self._releaseLock(logger)
                return None

            dataType = result[0][0]

        except Exception as e:
            logger.exception("[%s]: Not able to get sensor data type from database." % self.log_tag)
            self._releaseLock(logger)
            return None

        data = SensorData()
        data.sensorId = sensorId
        data.dataType = dataType
        if dataType == SensorDataType.NONE:
            data.data = SensorDataNone()

        elif dataType == SensorDataType.INT:
            try:
                # Get data type from database.
                self.cursor.execute("SELECT value, unit "
                                    + "FROM sensorsDataInt "
                                    + "WHERE sensorId = ?",
                                    (sensorId, ))
                result = self.cursor.fetchall()
                if len(result) != 1:
                    logger.error("[%s]: Sensor data was not found." % self.log_tag)
                    self._releaseLock(logger)
                    return None

                data.data = SensorDataInt(result[0][0],
                                          result[0][1])

            except Exception as e:
                logger.exception("[%s]: Not able to get sensor data from database." % self.log_tag)
                self._releaseLock(logger)
                return None

        elif dataType == SensorDataType.FLOAT:
            try:
                # Get data type from database.
                self.cursor.execute("SELECT value, unit "
                                    + "FROM sensorsDataFloat "
                                    + "WHERE sensorId = ?",
                                    (sensorId, ))
                result = self.cursor.fetchall()
                if len(result) != 1:
                    logger.error("[%s]: Sensor data was not found." % self.log_tag)
                    self._releaseLock(logger)
                    return None

                data.data = SensorDataFloat(result[0][0],
                                            result[0][1])

            except Exception as e:
                logger.exception("[%s]: Not able to get sensor data from database." % self.log_tag)
                self._releaseLock(logger)
                return None

        elif dataType == SensorDataType.GPS:
            try:
                # Get data type from database.
                self.cursor.execute("SELECT lat, lon, utctime "
                                    + "FROM sensorsDataGPS "
                                    + "WHERE sensorId = ?",
                                    (sensorId, ))
                result = self.cursor.fetchall()
                if len(result) != 1:
                    logger.error("[%s]: Sensor data was not found." % self.log_tag)
                    self._releaseLock(logger)
                    return None

                data.data = SensorDataGPS(result[0][0],
                                          result[0][1],
                                          result[0][2])

            except Exception as e:
                logger.exception("[%s]: Not able to get sensor data from database." % self.log_tag)
                self._releaseLock(logger)
                return None

        self._releaseLock(logger)

        # return a sensor data object or None
        return data

    def close(self,
              logger: logging.Logger = None):

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        self._acquireLock(logger)

        self.cursor.close()
        self.conn.close()

        self._releaseLock(logger)

    #region Refactored API

    def _delete_option_by_type(self,
                               option_type: str,
                               logger: logging.Logger = None) -> bool:
        """
        Internal function that deletes option given by type.

        :param option_type:
        :param logger:
        :return: Success or Failure
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        try:
            self.cursor.execute("DELETE FROM options WHERE type = ?", (option_type, ))

        except Exception as e:
            logger.exception("[%s]: Not able to delete option with type '%s'." % (self.log_tag, option_type))
            return False

        return True

    def _get_option_by_type(self,
                            option_type: str,
                            logger: logging.Logger = None) -> Optional[Option]:
        """
        Internal function that gets the option from the database given by its type.

        :param option_type:
        :param logger:
        :return: an option object or None
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        option = None
        try:
            self.cursor.execute("SELECT type, value FROM options WHERE type = ?", (option_type, ))

            result = self.cursor.fetchall()

            if len(result) == 1:
                option = Option()
                option.type = result[0][0]
                option.value = result[0][1]

        except Exception as e:
            logger.exception("[%s]: Not able to get option with type %s." % (self.log_tag, option_type))
            return None

        return option

    def _get_options_list(self, logger: logging.Logger = None) -> Optional[List[Option]]:
        """
        Internal function that gets the options from the database.

        :param logger:
        :return: list of option objects or None
        """
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        options = list()
        try:
            self.cursor.execute("SELECT type, value FROM options")

            result = self.cursor.fetchall()

            for option_tuple in result:
                option = Option()
                option.type = option_tuple[0]
                option.value = option_tuple[1]
                options.append(option)

        except Exception as e:
            logger.exception("[%s]: Not able to get options ." % self.log_tag)
            return None

        return options

    def _update_option(self,
                       option: Option,
                       logger: logging.Logger = None) -> bool:
        """
        Internal function that updates option data.

        :param option:
        :param logger:
        :return: success of failure
        """

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        try:
            # check if option does exist
            self.cursor.execute("SELECT type "
                                + "FROM options "
                                + "WHERE type = ?",
                                (option.type, ))
            result = self.cursor.fetchall()

            # Insert option data.
            if len(result) == 0:
                self.cursor.execute("INSERT INTO options ("
                                    + "type, "
                                    + "value) "
                                    + "VALUES (?, ?)",
                                    (option.type, option.value))

            # Update option data.
            elif len(result) == 1:
                self.cursor.execute("UPDATE options SET "
                                    + "value = ? "
                                    + "WHERE type = ?",
                                    (option.value, option.type))

            else:
                raise ValueError("Option type not unique.")

        except Exception as e:
            logger.exception("[%s]: Not able to update option with type '%s' in database."
                             % (self.log_tag, option.type))
            return False

        return True

    def delete_option_by_type(self,
                              option_type: str,
                              logger: logging.Logger = None) -> bool:
        # Set logger instance to use.
        if not logger:
            logger = self.logger

        with self.dbLock:
            if self._delete_option_by_type(option_type, logger):
                self.conn.commit()
                return True

        return False

    def get_option_by_type(self,
                           option_type: str,
                           logger: logging.Logger = None) -> Optional[Option]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        with self.dbLock:
            return self._get_option_by_type(option_type,
                                            logger)

    def get_options_list(self, logger: logging.Logger = None) -> Optional[List[Option]]:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        with self.dbLock:
            return self._get_options_list(logger)

    def update_option(self,
                      option_type: str,
                      option_value: int,
                      logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        option = Option()
        option.type = option_type
        option.value = option_value

        with self.dbLock:
            if self._update_option(option, logger):
                self.conn.commit()
                return True

        return False

    def update_option_by_obj(self,
                             option: Option,
                             logger: logging.Logger = None) -> bool:

        # Set logger instance to use.
        if not logger:
            logger = self.logger

        with self.dbLock:
            if self._update_option(option, logger):
                self.conn.commit()
                return True

        return False

    #endregion