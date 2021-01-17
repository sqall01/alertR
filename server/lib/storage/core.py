#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
from typing import Any, Optional, List, Union, Tuple, Dict
from ..localObjects import Node, Alert, Manager, Sensor, SensorAlert, Option, SensorData


# Internal abstract class for new storage backends.
class _Storage:

    def checkVersionAndClearConflict(self,
                                     logger: logging.Logger = None):
        """
        Checks the version of the server and the version in the database and clears every compatibility issue.
        No return value but raise exception if it fails.

        :param logger:
        """
        raise NotImplemented("Function not implemented yet.")

    def addNode(self,
                username: str,
                hostname: str,
                nodeType: str,
                instance: str,
                version: float,
                rev: int,
                persistent: int,
                logger: logging.Logger = None) -> bool:
        """
        Adds a node if it does not exist or changes the registered values if it does exist.

        :param username:
        :param hostname:
        :param nodeType:
        :param instance:
        :param version:
        :param rev:
        :param persistent:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def addSensors(self,
                   username: str,
                   sensors: List[Dict[str, Any]],
                   logger: logging.Logger = None) -> bool:
        """
        Adds/updates the data that is given by the node for the sensors to the database.

        :param username:
        :param sensors:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def addAlerts(self,
                  username: str,
                  alerts: List[Dict[str, Any]],
                  logger: logging.Logger = None) -> bool:
        """
        Adds/updates the data that is given by the node for the alerts to the database-

        :param username:
        :param alerts:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def addManager(self,
                   username: str,
                   manager: Dict[str, Any],
                   logger: logging.Logger = None) -> bool:
        """
        Adds/updates the data that is given by the node for the manager to the database.

        :param username:
        :param manager:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def addSensorAlert(self,
                       nodeId: int,
                       sensorId: int,
                       state: int,
                       dataJson: str,
                       changeState: bool,
                       hasLatestData: bool,
                       dataType: int,
                       sensorData: Any,
                       logger: logging.Logger = None) -> bool:
        """
        Adds a sensor alert to the database when the id of a node is given, the id of the sensor that is used
        internally by the node and the state.

        :param nodeId:
        :param sensorId:
        :param state:
        :param dataJson:
        :param changeState:
        :param hasLatestData:
        :param dataType:
        :param sensorData:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def getNodeId(self,
                  username: str,
                  logger: logging.Logger = None) -> Optional[int]:
        """
        Gets the id of the node by a given username (usernames are unique to each node).

        :param username:
        :param logger:
        :return nodeId or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getNodeIds(self,
                   logger: logging.Logger = None) -> List[int]:
        """
        Gets the ids of all nodes.

        :param logger:
        :return list of nodeIds
        """
        raise NotImplemented("Function not implemented yet.")

    def getSensorCount(self,
                       nodeId: str,
                       logger: logging.Logger = None) -> Optional[int]:
        """
        Gets the count of the sensors of a node in the database.

        :param nodeId:
        :param logger:
        :return count of sensors or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getSensorId(self,
                    nodeId: int,
                    remoteSensorId: int,
                    logger: logging.Logger = None) -> Optional[int]:
        """
        Gets the sensor id of a sensor when the id of a node is given and the remote sensor id that
        is used by the node internally.

        :param nodeId:
        :param remoteSensorId:
        :param logger:
        :return sensorId or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getSurveyData(self,
                      logger: logging.Logger = None) -> Optional[List[Tuple[str, float, int]]]:
        """
        Gets all data needed for the survey.

        :param logger:
        :return list of tuples of (instance, version, rev) or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getUniqueID(self,
                    logger: logging.Logger = None) -> Optional[str]:
        """
        Gets the unique id from the database.

        :param logger:
        :return unique id or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getAlertId(self,
                   nodeId: int,
                   remoteAlertId: int,
                   logger: logging.Logger = None) -> Optional[int]:
        """
        Gets the alert id of an alert when the id of a node is given and the remote alert id that is
        used by the node internally.

        :param nodeId:
        :param remoteAlertId:
        :param logger:
        :return alertId or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getSensorAlertLevels(self,
                             sensorId: int,
                             logger: logging.Logger = None) -> Optional[List[int]]:
        """
        Gets all alert levels for a specific sensor given by sensorId.

        :param sensorId:
        :param logger:
        :return list of alertLevels or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getAlertAlertLevels(self,
                            alertId: int,
                            logger: logging.Logger = None) -> Optional[List[int]]:
        """
        Gets all alert levels for a specific alert given by alertId.

        :param alertId:
        :param logger:
        :return list of alertLevels or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getSensorAlerts(self,
                        logger: logging.Logger = None) -> Optional[List[SensorAlert]]:
        """
        Gets all sensor alerts in the database.

        :param logger:
        :return a list of sensorAlert objects or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getAllAlertsAlertLevels(self,
                                logger: logging.Logger = None) -> Optional[List[int]]:
        """
        Gets all alert levels for the alert clients from the database.

        :param logger:
        :return list alertLevels as integer or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getAllSensorsAlertLevels(self,
                                 logger: logging.Logger = None) -> Optional[List[int]]:
        """
        Gets all alert levels for the sensors from the database.

        :param logger:
        :return list alertLevels as integer or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getAllConnectedNodeIds(self,
                               logger: logging.Logger = None) -> Optional[List[int]]:
        """
        Gets all nodes from the database that are connected to the server.

        :param logger:
        :return list of nodeIds or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getAllPersistentNodeIds(self,
                                logger: logging.Logger = None) -> Optional[List[int]]:
        """
        Gets all nodes from the database that are registered as persistent to the server.

        :param logger:
        :return list of nodeIds or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getSensorsUpdatedOlderThan(self,
                                   oldestTimeUpdated: int,
                                   logger: logging.Logger = None) -> Optional[List[Sensor]]:
        """
        Gets the information of all sensors which last state updates are older than the given time.

        :param oldestTimeUpdated:
        :param logger:
        :return list of sensor objects or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getAlertById(self,
                     alertId: int,
                     logger: logging.Logger = None) -> Optional[Alert]:
        """
        Gets the alert from the database when its id is given.

        :param alertId:
        :param logger:
        :return an alert object or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getManagerById(self,
                       managerId: int,
                       logger: logging.Logger = None) -> Optional[Manager]:
        """
        Gets the manager from the database when its id is given.

        :param managerId:
        :param logger:
        :return a manager object or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getNodeById(self,
                    nodeId: int,
                    logger: logging.Logger = None) -> Optional[Node]:
        """
        Gets the node from the database when its id is given.

        :param nodeId:
        :param logger:
        :return a node object or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getSensorById(self,
                      sensorId: int,
                      logger: logging.Logger = None) -> Optional[Sensor]:
        """
        Gets the sensor from the database when its id is given.

        :param sensorId:
        :param logger:
        :return a sensor object or None
        """
        raise NotImplemented("Function not implemented yet.")

    def get_option_by_type(self,
                           option_type: str,
                           logger: logging.Logger = None) -> Optional[Option]:
        """
        Gets the option from the database given by type.

        :param option_type:
        :param logger:
        :return: an option object or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getNodes(self,
                 logger: logging.Logger = None) -> Optional[List[Node]]:
        """
        Gets all nodes from the database.

        :param logger:
        :return a list of node objects or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getAlertSystemInformation(self,
                                  logger: logging.Logger = None) -> Optional[List[List[Union[Option,
                                                                                             Node,
                                                                                             Sensor,
                                                                                             Manager,
                                                                                             Alert]]]]:
        """
        Gets all information that the server has at the current moment.

        :param logger:
        :return a list of
        :return list[0] = list(option objects)
        :return list[1] = list(node objects)
        :return list[2] = list(sensor objects)
        :return list[3] = list(manager objects)
        :return list[4] = list(alert objects)
        :return or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getSensorState(self,
                       sensorId: int,
                       logger: logging.Logger = None) -> Optional[int]:
        """
        Gets the state of a sensor given by id.

        :param sensorId:
        :param logger:
        :return sensor state or None
        """
        raise NotImplemented("Function not implemented yet.")

    def getSensorData(self,
                      sensorId: int,
                      logger: logging.Logger = None) -> Optional[SensorData]:
        """
        Gets the data of a sensor given by id.

        :param sensorId:
        :param logger:
        :return a sensor data object or None
        """
        raise NotImplemented("Function not implemented yet.")

    def changeOption(self,
                     optionType: str,
                     optionValue: float,
                     logger: logging.Logger = None) -> bool:
        """
        Ghange a option in the database.

        :param optionType:
        :param optionValue:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def markNodeAsNotConnected(self,
                               nodeId: int,
                               logger: logging.Logger = None) -> bool:
        """
        Marks a node given by its id as NOT connected.

        :param nodeId:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def markNodeAsConnected(self,
                            nodeId: int,
                            logger: logging.Logger = None) -> bool:
        """
        Marks a node given by its id as connected.

        :param nodeId:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def deleteSensorAlert(self,
                          sensorAlertId: int,
                          logger: logging.Logger = None) -> bool:
        """
        Deletes a sensor alert given by its sensor alert id.

        :param sensorAlertId:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def deleteNode(self,
                   nodeId: int,
                   logger: logging.Logger = None) -> bool:
        """
        Deletes a node given by its node id.

        :param nodeId:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def updateSensorState(self,
                          nodeId: int,
                          stateList: List[Tuple[int, int]],
                          logger: logging.Logger = None) -> bool:
        """
        Updates the states of the sensors of a node in the database (given in a tuple of (remoteSensorId, state)).

        :param nodeId:
        :param stateList:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def updateSensorData(self,
                         nodeId: int,
                         dataList: List[Tuple[int, Any]],
                         logger: logging.Logger = None) -> bool:
        """
        Updates the data of the sensors of a node in the database (given in a tuple of (remoteSensorId, data)).

        :param nodeId:
        :param dataList:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def updateSensorTime(self,
                         sensorId: int,
                         logger: logging.Logger = None) -> bool:
        """
        Updates the time the sensor send an update given by sensorId.

        :param sensorId:
        :param logger:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")

    def close(self,
              logger: logging.Logger = None):
        """
        Closes db for usage.

        :param logger:
        """
        raise NotImplemented("Function not implemented yet.")
