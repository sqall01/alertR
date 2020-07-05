#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import os
import threading
import time
import json
import MySQLdb
from typing import List, Optional
from ..globalData.localObjects import Option, Node, Sensor, Alert, Manager, AlertLevel, SensorAlert, SensorDataType
from ..globalData import GlobalData


# internal abstract class for new storage backends
class _Storage:

    def synchronize_database_to_system_data(self):
        """
        Creates objects from the data in the database
        (should only be called during the initial connection to the database)

        no return value but raise exception if it fails
        """
        raise NotImplemented("Function not implemented yet.")

    def create_storage(self):
        """
        Creates the database (should only be called if the database does not exist)

        No return value but raise exception if it fails
        """
        raise NotImplemented("Function not implemented yet.")

    def update_server_information(self,
                                  serverTime: int,
                                  options: List[Option],
                                  nodes: List[Node],
                                  sensors: List[Sensor],
                                  alerts: List[Alert],
                                  managers: List[Manager],
                                  alertLevels: List[AlertLevel],
                                  sensorAlerts: List[SensorAlert]) -> bool:
        """
        Updates the received server information.

        :param serverTime:
        :param options:
        :param nodes:
        :param sensors:
        :param alerts:
        :param managers:
        :param alertLevels:
        :param sensorAlerts:
        :return Success or Failure
        """
        raise NotImplemented("Function not implemented yet.")


# class for using mysql as storage backend
class Mysql(_Storage):

    def __init__(self,
                 host: str,
                 port: int,
                 database: str,
                 username: str,
                 password: str,
                 globalData: GlobalData):

        # file nme of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        # needed mysql parameters
        self._host = host
        self._port = port
        self._database = database
        self._username = username
        self._password = password

        # get global configured data
        self._global_data = globalData
        self._system_data = self._global_data.system_data
        self._sensor_alert_life_span = self._global_data.sensorAlertLifeSpan
        self._version = self._global_data.version
        self._rev = self._global_data.rev
        self._connection_retries = self._global_data.storageBackendMysqlRetries

        # Hold a copy of the alert system objects locally to know which data we have stored in the database.
        self._db_copy_options: List[Option] = list()
        self._db_copy_nodes: List[Node] = list()
        self._db_copy_alerts: List[Alert] = list()
        self._db_copy_managers: List[Manager] = list()
        self._db_copy_sensors: List[Sensor] = list()
        self._db_copy_alert_levels: List[AlertLevel] = list()

        # mysql lock
        self._lock = threading.Lock()

        self._conn: Optional[MySQLdb.Connection] = None
        self._cursor: Optional[MySQLdb.cursors.Cursor] = None

        # connect to the database
        self._open_connection()

        # Check if version of database is the same as version of client
        self._cursor.execute("SHOW TABLES LIKE 'internals'")
        result = self._cursor.fetchall()
        if len(result) != 0:

            self._cursor.execute("SELECT type, value FROM internals")
            result = self._cursor.fetchall()

            # Extract internal data.
            db_version = 0.0
            db_rev = 0
            for internal_tuple in result:
                internal_type = internal_tuple[0]
                internal_value = internal_tuple[1]

                if internal_type.upper() == "VERSION":
                    db_version = internal_value
                    continue
                elif internal_type.upper() == "REV":
                    db_rev = int(internal_value)
                    continue

            # if version is not the same of db and client
            # => delete event tables
            if db_version != self._version or db_rev != self._rev:
                self._delete_storage()

                # commit all changes
                self._conn.commit()

                # close connection to the database
                self._close_connection()

                self.create_storage()

            else:
                # commit all changes
                self._conn.commit()

                # close connection to the database
                self._close_connection()

                self.synchronize_database_to_system_data()

        # tables do not exist yet
        # => create them
        else:
            # close connection to the database
            self._close_connection()

            self.create_storage()

    def _add_sensor_alert(self, sensor_alert: SensorAlert):
        """
        Internal function that adds a Sensor Alert to the database. Does not catch exceptions.

        :param sensor_alert:
        """
        # Try to convert received data to json to store it in the database.
        try:
            dataJson = json.dumps(sensor_alert.optionalData)

        except Exception:
            logging.exception("[%s]: Not able to convert optional data of Sensor Alert to json."
                              % self._log_tag)
            raise

        try:
            self._cursor.execute("INSERT INTO sensorAlerts ("
                                 + "sensorId, "
                                 + "state, "
                                 + "description, "
                                 + "timeReceived, "
                                 + "dataJson, "
                                 + "dataType) "
                                 + "VALUES (%s, %s, %s, %s, %s, %s)",
                                 (sensor_alert.sensorId,
                                  sensor_alert.state,
                                  sensor_alert.description,
                                  sensor_alert.timeReceived,
                                  dataJson,
                                  sensor_alert.dataType))
            db_sensor_alert_id = self._cursor.lastrowid

            for alert_level in sensor_alert.alertLevels:
                self._cursor.execute("INSERT INTO sensorAlertsAlertLevels ("
                                     + "sensorAlertId, "
                                     + "alertLevel) "
                                     + "VALUES (%s, %s)",
                                     (db_sensor_alert_id, alert_level))

            # Only store data if sensor alert carries it.
            if sensor_alert.dataType == SensorDataType.INT:
                self._cursor.execute("INSERT INTO sensorAlertsDataInt ("
                                     + "sensorAlertId, "
                                     + "data) "
                                     + "VALUES (%s, %s)",
                                     (db_sensor_alert_id, sensor_alert.sensorData))
            elif sensor_alert.dataType == SensorDataType.FLOAT:
                self._cursor.execute("INSERT INTO sensorAlertsDataFloat ("
                                     + "sensorAlertId, "
                                     + "data) "
                                     + "VALUES (%s, %s)",
                                     (db_sensor_alert_id, sensor_alert.sensorData))

        except Exception:
            logging.exception("[%s]: Not able to add Sensor Alert." % self._log_tag)
            raise

    def _add_sensor_data(self, sensor: Sensor):
        """
        Internal function that adds the data of the sensor to the database. Does not catch exceptions.

        :param sensor:
        """
        if sensor.dataType == SensorDataType.NONE:
            pass

        elif sensor.dataType == SensorDataType.INT:
            try:
                self._cursor.execute("INSERT INTO sensorsDataInt ("
                                     + "sensorId, "
                                     + "data) "
                                     + "VALUES (%s, %s)",
                                     (sensor.sensorId, sensor.data))

            except Exception:
                logging.exception("[%s]: Not able to add integer data for Sensor %d."
                                  % (self._log_tag, sensor.sensorId))
                raise

        elif sensor.dataType == SensorDataType.FLOAT:
            try:
                self._cursor.execute("INSERT INTO sensorsDataFloat ("
                                     + "sensorId, "
                                     + "data) "
                                     + "VALUES (%s, %s)",
                                     (sensor.sensorId, sensor.data))
            except Exception:
                logging.exception("[%s]: Not able to add float data for Sensor %d."
                                  % (self._log_tag, sensor.sensorId))
                raise

    def _close_connection(self):
        """
        Internal function that closes the connection to the mysql server.
        """
        try:
            self._cursor.close()
            self._conn.close()

        except Exception:
            pass

        self._cursor = None
        self._conn = None

    def _delete_alert(self, alert_id: int):
        """
        Internal function that deletes an Alert from the database. Does not catch exceptions.

        :param alert_id:
        """
        try:
            self._cursor.execute("DELETE FROM alertsAlertLevels "
                                 + "WHERE alertId = %s",
                                 (alert_id, ))

            self._cursor.execute("DELETE FROM alerts "
                                 + "WHERE id = %s",
                                 (alert_id, ))
        except Exception:
            logging.exception("[%s]: Not able to delete Alert with id %d."
                              % (self._log_tag, alert_id))
            raise

    def _delete_alert_level(self, level: int):
        """
        Internal function that deletes an Alert Level from the database. Does not catch exceptions.

        :param level:
        """
        try:
            self._cursor.execute("DELETE FROM alertsAlertLevels "
                                 + "WHERE alertLevel = %s",
                                 (level, ))

            self._cursor.execute("DELETE FROM sensorsAlertLevels "
                                 + "WHERE alertLevel = %s",
                                 (level, ))

            self._cursor.execute("DELETE FROM sensorAlertsAlertLevels "
                                 + "WHERE alertLevel = %s",
                                 (level, ))

            self._cursor.execute("DELETE FROM alertLevels "
                                 + "WHERE alertLevel = %s",
                                 (level, ))
        except Exception:
            logging.exception("[%s]: Not able to delete Alert Level %d."
                              % (self._log_tag, level))
            raise

    def _delete_manager(self, manager_id: int):
        """
        Internal function that deletes a Manager from the database. Does not catch exceptions.

        :param manager_id:
        """
        try:
            self._cursor.execute("DELETE FROM managers "
                                 + "WHERE id = %s",
                                 (manager_id, ))
        except Exception:
            logging.exception("[%s]: Not able to delete Manager with id %d."
                              % (self._log_tag, manager_id))
            raise

    def _delete_node(self, node_id: int):
        """
        Internal function that deletes a Node from the database. Does not catch exceptions.

        :param node_id:
        """
        try:
            # Delete all Alerts with the returned id.
            self._cursor.execute("SELECT id FROM alerts "
                                 + "WHERE nodeId = %s",
                                 (node_id, ))
            result = self._cursor.fetchall()
            for id_tuple in result:
                self._delete_alert(id_tuple[0])

            # Delete all Managers with the returned id.
            self._cursor.execute("SELECT id FROM managers "
                                 + "WHERE nodeId = %s",
                                 (node_id, ))
            result = self._cursor.fetchall()
            for id_tuple in result:
                self._delete_manager(id_tuple[0])

            # Delete all Sensors with the returned id.
            self._cursor.execute("SELECT id FROM sensors "
                                 + "WHERE nodeId = %s",
                                 (node_id, ))
            result = self._cursor.fetchall()
            for id_tuple in result:
                self._delete_sensor(id_tuple[0])

            self._cursor.execute("DELETE FROM nodes "
                                 + "WHERE id = %s",
                                 (node_id, ))
        except Exception:
            logging.exception("[%s]: Not able to delete Node with id %d."
                              % (self._log_tag, node_id))
            raise

    def _delete_option(self, option_type: str):
        """
        Internal function that deletes an Option from the database. Does not catch exceptions.

        :param option_type:
        """
        try:
            self._cursor.execute("DELETE FROM options "
                                 + "WHERE type = %s",
                                 (option_type, ))

        except Exception:
            logging.exception("[%s]: Not able to delete Option of type '%s'."
                              % (self._log_tag, option_type))
            raise

    def _delete_sensor(self, sensor_id: int):
        """
        Internal function that deletes a Sensor from the database. Does not catch exceptions.

        :param sensor_id:
        """
        try:
            self._cursor.execute("DELETE FROM sensorsAlertLevels "
                                 + "WHERE sensorId = %s",
                                 (sensor_id, ))

            # delete all sensor alerts with the returned id
            self._cursor.execute("SELECT id FROM sensorAlerts "
                                 + "WHERE sensorId = %s",
                                 (sensor_id, ))
            result = self._cursor.fetchall()
            for id_tuple in result:
                self._cursor.execute("DELETE FROM "
                                     + "sensorAlertsAlertLevels "
                                     + "WHERE sensorAlertId = %s",
                                     (id_tuple[0], ))
                self._cursor.execute("DELETE FROM "
                                     + "sensorAlertsDataInt "
                                     + "WHERE sensorAlertId = %s",
                                     (id_tuple[0], ))
                self._cursor.execute("DELETE FROM "
                                     + "sensorAlertsDataFloat "
                                     + "WHERE sensorAlertId = %s",
                                     (id_tuple[0], ))
                self._cursor.execute("DELETE FROM sensorAlerts "
                                     + "WHERE id = %s",
                                     (id_tuple[0], ))

            # Delete all sensor data from database.
            self._delete_sensor_data(sensor_id)

            self._cursor.execute("DELETE FROM sensors "
                                 + "WHERE id = %s",
                                 (sensor_id, ))

        except Exception:
            logging.exception("[%s]: Not able to delete Sensor with id %d."
                              % (self._log_tag, sensor_id))
            raise

    def _delete_sensor_alerts(self, max_life_in_seconds: int):
        """
        Internal function that deletes all Sensor Alerts exceeding their life span from the database.
        Does not catch exceptions.

        :param max_life_in_seconds:
        """

        try:
            # Delete all sensor alerts with the returned id.
            utc_timestamp = int(time.time())
            self._cursor.execute("SELECT id FROM sensorAlerts "
                                 + "WHERE (timeReceived + "
                                 + str(max_life_in_seconds)
                                 + ")"
                                 + "<= %s",
                                 (utc_timestamp, ))
            result = self._cursor.fetchall()

            for id_tuple in result:
                self._cursor.execute("DELETE FROM sensorAlertsAlertLevels "
                                     + "WHERE sensorAlertId = %s",
                                     (id_tuple[0], ))
                self._cursor.execute("DELETE FROM sensorAlertsDataInt "
                                     + "WHERE sensorAlertId = %s",
                                     (id_tuple[0], ))
                self._cursor.execute("DELETE FROM sensorAlertsDataFloat "
                                     + "WHERE sensorAlertId = %s",
                                     (id_tuple[0], ))
                self._cursor.execute("DELETE FROM sensorAlerts "
                                     + "WHERE id = %s",
                                     (id_tuple[0], ))

        except Exception:
            logging.exception("[%s]: Not able to delete Sensor Alerts." % self._log_tag)
            raise

    def _delete_sensor_data(self, sensor_id: int):
        """
        Internal function that removes the data of the sensor in the database. Does not catch exceptions.

        :param sensor_id:
        """
        try:
            self._cursor.execute("DELETE FROM sensorsDataInt "
                                 + "WHERE sensorId = %s",
                                 (sensor_id, ))

            self._cursor.execute("DELETE FROM sensorsDataFloat "
                                 + "WHERE sensorId = %s",
                                 (sensor_id, ))
        except Exception:
            logging.exception("[%s]: Not able to delete data of Sensor %d." % (self._log_tag, sensor_id))
            raise

    def _delete_storage(self):
        """
        Internal function that deletes the complete storage. Does not catch exceptions.
        """

        # Remove old event tables (not used anymore).
        self._cursor.execute("DROP TABLE IF EXISTS eventsNewVersion")
        self._cursor.execute("DROP TABLE IF EXISTS eventsSensorAlert")
        self._cursor.execute("DROP TABLE IF EXISTS eventsStateChange")
        self._cursor.execute("DROP TABLE IF EXISTS eventsConnectedChange")
        self._cursor.execute("DROP TABLE IF EXISTS eventsSensorTimeOut")
        self._cursor.execute("DROP TABLE IF EXISTS eventsNewOption")
        self._cursor.execute("DROP TABLE IF EXISTS eventsNewNode")
        self._cursor.execute("DROP TABLE IF EXISTS eventsNewSensor")
        self._cursor.execute("DROP TABLE IF EXISTS eventsNewAlert")
        self._cursor.execute("DROP TABLE IF EXISTS eventsNewManager")
        self._cursor.execute("DROP TABLE IF EXISTS eventsChangeOption")
        self._cursor.execute("DROP TABLE IF EXISTS eventsChangeNode")
        self._cursor.execute("DROP TABLE IF EXISTS eventsChangeSensor")
        self._cursor.execute("DROP TABLE IF EXISTS eventsChangeAlert")
        self._cursor.execute("DROP TABLE IF EXISTS eventsChangeManager")
        self._cursor.execute("DROP TABLE IF EXISTS eventsDeleteNode")
        self._cursor.execute("DROP TABLE IF EXISTS eventsDeleteSensor")
        self._cursor.execute("DROP TABLE IF EXISTS eventsDeleteAlert")
        self._cursor.execute("DROP TABLE IF EXISTS eventsDeleteManager")
        self._cursor.execute("DROP TABLE IF EXISTS eventsDataInt")
        self._cursor.execute("DROP TABLE IF EXISTS eventsDataFloat")
        self._cursor.execute("DROP TABLE IF EXISTS events")

        self._cursor.execute("DROP TABLE IF EXISTS internals")
        self._cursor.execute("DROP TABLE IF EXISTS options")
        self._cursor.execute("DROP TABLE IF EXISTS sensorsAlertLevels")
        self._cursor.execute("DROP TABLE IF EXISTS sensorAlertsAlertLevels")
        self._cursor.execute("DROP TABLE IF EXISTS sensorAlertsDataInt")
        self._cursor.execute("DROP TABLE IF EXISTS sensorAlertsDataFloat")
        self._cursor.execute("DROP TABLE IF EXISTS sensorAlerts")
        self._cursor.execute("DROP TABLE IF EXISTS sensorsDataInt")
        self._cursor.execute("DROP TABLE IF EXISTS sensorsDataFloat")
        self._cursor.execute("DROP TABLE IF EXISTS sensors")
        self._cursor.execute("DROP TABLE IF EXISTS alertsAlertLevels")
        self._cursor.execute("DROP TABLE IF EXISTS alerts")
        self._cursor.execute("DROP TABLE IF EXISTS managers")
        self._cursor.execute("DROP TABLE IF EXISTS alertLevels")
        self._cursor.execute("DROP TABLE IF EXISTS nodes")

    def _open_connection(self):
        """
        Internal function that connects to the mysql server
        (needed because direct changes to the database by another program
        are not seen if the connection to the mysql server is kept alive)
        """
        current_try = 0
        while True:
            try:

                self._conn = MySQLdb.connect(host=self._host,
                                             port=self._port,
                                             user=self._username,
                                             passwd=self._password,
                                             db=self._database)
                self._conn.autocommit(False)
                self._cursor = self._conn.cursor()
                break

            except Exception:
                # Re-throw the exception if we reached our retry limit.
                if current_try >= self._connection_retries:
                    raise

                current_try += 1
                logging.exception("[%s]: Not able to connect to the MySQL server. Waiting before retrying (%d/%d)."
                                  % (self._log_tag, current_try, self._connection_retries))

                time.sleep(5)

    def _update_alert(self, alert: Alert):
        """
        Internal function that updates an Alert in the database. Does not catch exceptions.

        :param alert:
        """
        try:
            self._cursor.execute("SELECT * FROM alerts WHERE id = %s",
                                 (alert.alertId,))

        except Exception:
            logging.exception("[%s]: Not able to get alert with id %d."
                              % (self._log_tag, alert.alertId))
            raise

        result = self._cursor.fetchall()

        # Update existing object.
        if len(result) != 0:
            try:
                self._cursor.execute("UPDATE alerts SET "
                                     + "nodeId = %s, "
                                     + "remoteAlertId = %s, "
                                     + "description = %s "
                                     + "WHERE id = %s",
                                     (alert.nodeId,
                                      alert.remoteAlertId,
                                      alert.description,
                                      alert.alertId))

                self._cursor.execute("DELETE FROM alertsAlertLevels "
                                     + "WHERE alertId = %s",
                                     (alert.alertId, ))

                for alertAlertLevel in alert.alertLevels:
                    self._cursor.execute("INSERT INTO alertsAlertLevels ("
                                         + "alertId, "
                                         + "alertLevel) "
                                         + "VALUES (%s, %s)",
                                         (alert.alertId, alertAlertLevel))

            except Exception:
                logging.exception("[%s]: Not able to update Alert with id %d."
                                  % (self._log_tag, alert.alertId))
                raise

        # Add not existing new object.
        else:
            try:
                self._cursor.execute("INSERT INTO alerts ("
                                     + "id, "
                                     + "nodeId, "
                                     + "remoteAlertId, "
                                     + "description) "
                                     + "VALUES (%s, %s, %s, %s)",
                                     (alert.alertId, alert.nodeId, alert.remoteAlertId, alert.description))

                for alertAlertLevel in alert.alertLevels:
                    self._cursor.execute("INSERT INTO alertsAlertLevels ("
                                         + "alertId, "
                                         + "alertLevel) "
                                         + "VALUES (%s, %s)",
                                         (alert.alertId, alertAlertLevel))

            except Exception:
                logging.exception("[%s]: Not able to add Alert with id %d."
                                  % (self._log_tag, alert.alertId))
                raise

    def _update_alert_level(self, alert_level: AlertLevel):
        """
        Internal function that updates an Alert Level in the database. Does not catch exceptions.

        :param alert_level:
        """
        try:
            self._cursor.execute("SELECT * FROM alertLevels WHERE alertLevel = %s",
                                 (alert_level.level,))

        except Exception:
            logging.exception("[%s]: Not able to get Alert Level %d."
                              % (self._log_tag, alert_level.level))
            raise

        result = self._cursor.fetchall()

        # Update existing object.
        if len(result) != 0:
            try:
                self._cursor.execute("UPDATE alertLevels SET "
                                     + "name = %s, "
                                     + "triggerAlways = %s, "
                                     + "rulesActivated = %s "
                                     + "WHERE alertLevel = %s",
                                     (alert_level.name,
                                      alert_level.triggerAlways,
                                      1 if alert_level.rulesActivated else 0,
                                      alert_level.level))

            except Exception:
                logging.exception("[%s]: Not able to update Alert Level %d."
                                  % (self._log_tag, alert_level.level))
                raise

        # Add not existing new object.
        else:
            try:
                self._cursor.execute("INSERT INTO alertLevels ("
                                     + "alertLevel, "
                                     + "name, "
                                     + "triggerAlways, "
                                     + "rulesActivated) "
                                     + "VALUES (%s, %s, %s, %s)",
                                     (alert_level.level,
                                      alert_level.name,
                                      alert_level.triggerAlways,
                                      1 if alert_level.rulesActivated else 0))

            except Exception:
                logging.exception("[%s]: Not able to add Alert Level %d."
                                  % (self._log_tag, alert_level.level))
                raise

    def _update_manager(self, manager: Manager):
        """
        Internal function that updates a Manager in the database. Does not catch exceptions.

        :param manager:
        """
        try:
            self._cursor.execute("SELECT * FROM managers WHERE id = %s",
                                 (manager.managerId,))

        except Exception:
            logging.exception("[%s]: Not able to get Manager with id %d."
                              % (self._log_tag, manager.managerId))
            raise

        result = self._cursor.fetchall()

        # Update existing object.
        if len(result) != 0:
            try:
                self._cursor.execute("UPDATE managers SET "
                                     + "nodeId = %s, "
                                     + "description = %s "
                                     + "WHERE id = %s",
                                     (manager.nodeId,
                                      manager.description,
                                      manager.managerId))

            except Exception:
                logging.exception("[%s]: Not able to update Manager with id %d."
                                  % (self._log_tag, manager.managerId))
                raise

        # Add not existing new object.
        else:
            try:
                self._cursor.execute("INSERT INTO managers ("
                                     + "id, "
                                     + "nodeId, "
                                     + "description) "
                                     + "VALUES (%s, %s, %s)",
                                     (manager.managerId, manager.nodeId, manager.description))

            except Exception:
                logging.exception("[%s]: Not able to add Manager with id %d."
                                  % (self._log_tag, manager.managerId))
                raise

    def _update_node(self, node: Node):
        """
        Internal function that updates a Node in the database. Does not catch exceptions.

        :param node:
        """

        try:
            self._cursor.execute("SELECT * FROM nodes WHERE id = %s",
                                 (node.nodeId,))

        except Exception:
            logging.exception("[%s]: Not able to get Node with id %d."
                              % (self._log_tag, node.nodeId))
            raise

        result = self._cursor.fetchall()

        # Update existing object.
        if len(result) != 0:
            try:
                node_id = result[0][0]
                node_type = result[0][2].lower()
                if node.nodeType.lower() != node_type:
                    if node_type == "alert":
                        # Delete all Alerts with the returned id.
                        self._cursor.execute("SELECT id FROM alerts "
                                             + "WHERE nodeId = %s",
                                             (node_id, ))
                        result = self._cursor.fetchall()
                        for id_tuple in result:
                            self._delete_alert(id_tuple[0])

                    elif node_type == "manager":
                        # Delete all Managers with the returned id.
                        self._cursor.execute("SELECT id FROM managers "
                                             + "WHERE nodeId = %s",
                                             (node_id, ))
                        result = self._cursor.fetchall()
                        for id_tuple in result:
                            self._delete_manager(id_tuple[0])

                    elif node_type in ["sensor", "server"]:
                        # Delete all Sensors with the returned id.
                        self._cursor.execute("SELECT id FROM sensors "
                                             + "WHERE nodeId = %s",
                                             (node_id, ))
                        result = self._cursor.fetchall()
                        for id_tuple in result:
                            self._delete_sensor(id_tuple[0])

                self._cursor.execute("UPDATE nodes SET "
                                     + "hostname = %s, "
                                     + "nodeType = %s, "
                                     + "instance = %s, "
                                     + "connected = %s, "
                                     + "version = %s, "
                                     + "rev = %s, "
                                     + "username = %s, "
                                     + "persistent = %s "
                                     + "WHERE id = %s",
                                     (node.hostname,
                                      node.nodeType,
                                      node.instance,
                                      node.connected,
                                      node.version,
                                      node.rev,
                                      node.username,
                                      node.persistent,
                                      node.nodeId))

            except Exception:
                logging.exception("[%s]: Not able to update Node with id %d."
                                  % (self._log_tag, node.nodeId))
                raise

        # Add not existing new object.
        else:
            try:
                self._cursor.execute("INSERT INTO nodes ("
                                     + "id, "
                                     + "hostname, "
                                     + "nodeType, "
                                     + "instance, "
                                     + "connected, "
                                     + "version, "
                                     + "rev, "
                                     + "username, "
                                     + "persistent) "
                                     + "VALUES "
                                     + "(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                     (node.nodeId,
                                      node.hostname,
                                      node.nodeType,
                                      node.instance,
                                      node.connected,
                                      node.version,
                                      node.rev,
                                      node.username,
                                      node.persistent))

            except Exception:
                logging.exception("[%s]: Not able to add Node with id %d."
                                  % (self._log_tag, node.nodeId))
                raise

    def _update_option(self, option: Option):
        """
        Internal function that updates an Option in the database. Does not catch exceptions.

        :param option:
        """
        try:
            self._cursor.execute("SELECT * FROM options WHERE type = %s",
                                 (option.type,))

        except Exception:
            logging.exception("[%s]: Not able to get Option of type '%s'."
                              % (self._log_tag, option.type))
            raise

        result = self._cursor.fetchall()

        # Update existing object.
        if len(result) != 0:
            try:
                self._cursor.execute("UPDATE options SET "
                                     + "value = %s WHERE type = %s",
                                     (option.value, option.type))

            except Exception:
                logging.exception("[%s]: Not able to update Option of type '%s'."
                                  % (self._log_tag, option.type))
                raise

        # Add not existing new object.
        else:
            try:
                self._cursor.execute("INSERT INTO options ("
                                     + "type, "
                                     + "value) VALUES (%s, %s)",
                                     (option.type, option.value))

            except Exception:
                logging.exception("[%s]: Not able to add Option of type '%s'."
                                  % (self._log_tag, option.type))
                raise

    def _update_sensor(self, sensor: Sensor):
        """
        Internal function that updates a Sensor in the database. Does not catch exceptions.

        :param sensor:
        """
        try:
            self._cursor.execute("SELECT * FROM sensors WHERE id = %s",
                                 (sensor.sensorId,))

        except Exception:
            logging.exception("[%s]: Not able to get Sensor with id %d."
                              % (self._log_tag, sensor.sensorId))
            raise

        result = self._cursor.fetchall()

        # Update existing object.
        if len(result) != 0:
            try:
                # Delete all sensor data from database.
                self._delete_sensor_data(sensor.sensorId)

                self._cursor.execute("UPDATE sensors SET "
                                     + "nodeId = %s, "
                                     + "remoteSensorId = %s, "
                                     + "description = %s, "
                                     + "state = %s ,"
                                     + "lastStateUpdated = %s, "
                                     + "alertDelay = %s, "
                                     + "dataType = %s "
                                     + "WHERE id = %s",
                                     (sensor.nodeId,
                                      sensor.remoteSensorId,
                                      sensor.description,
                                      sensor.state,
                                      sensor.lastStateUpdated,
                                      sensor.alertDelay,
                                      sensor.dataType,
                                      sensor.sensorId))

                self._cursor.execute("DELETE FROM sensorsAlertLevels "
                                     + "WHERE sensorId = %s",
                                     (sensor.sensorId, ))

                for sensorAlertLevel in sensor.alertLevels:
                    self._cursor.execute("INSERT INTO sensorsAlertLevels ("
                                         + "sensorId, "
                                         + "alertLevel) "
                                         + "VALUES (%s, %s)",
                                         (sensor.sensorId, sensorAlertLevel))

                # Add sensor data to database.
                self._add_sensor_data(sensor)

            except Exception:
                logging.exception("[%s]: Not able to update Sensor with id %d."
                                  % (self._log_tag, sensor.sensorId))
                raise

        # Add not existing new object.
        else:
            try:
                self._cursor.execute("INSERT INTO sensors ("
                                     + "id, "
                                     + "nodeId, "
                                     + "remoteSensorId, "
                                     + "description, "
                                     + "state, "
                                     + "lastStateUpdated, "
                                     + "alertDelay, "
                                     + "dataType) "
                                     + "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                     (sensor.sensorId,
                                      sensor.nodeId,
                                      sensor.remoteSensorId,
                                      sensor.description,
                                      sensor.state,
                                      sensor.lastStateUpdated,
                                      sensor.alertDelay,
                                      sensor.dataType))

                for sensorAlertLevel in sensor.alertLevels:
                    self._cursor.execute("INSERT INTO sensorsAlertLevels ("
                                         + "sensorId, "
                                         + "alertLevel) "
                                         + "VALUES (%s, %s)",
                                         (sensor.sensorId, sensorAlertLevel))

                # Add sensor data to database.
                self._add_sensor_data(sensor)

            except Exception:
                logging.exception("[%s]: Not able to add Sensor with id %d."
                                  % (self._log_tag, sensor.sensorId))
                raise

    def _update_server_time(self, server_time: int):
        """
        Internal function that updates server time in the database. Does not catch exceptions.

        :param server_time:
        """
        self._cursor.execute("UPDATE internals SET "
                             + "value = %s "
                             + "WHERE type = %s",
                             (server_time, "serverTime"))

    def synchronize_database_to_system_data(self):
        """
        Creates objects from the data in the database and stores them into the local system data storage.
        (should only be called during the initial connection to the database)
        Has no return value but raise exception if it fails.
        """

        # Clear system data
        self._system_data.clear_data()

        # connect to the database
        self._open_connection()

        # get last stored server time
        self._cursor.execute("SELECT "
                             + "value "
                             + "FROM internals WHERE type = 'serverTime'")
        result = self._cursor.fetchall()
        server_time = result[0][0]

        # create option objects from db
        self._cursor.execute("SELECT "
                             + "type, "
                             + "value "
                             + "FROM options")
        result = self._cursor.fetchall()

        for option_tuple in result:
            option = Option()
            option.type = option_tuple[0]
            option.value = option_tuple[1]

            self._system_data.update_option(option)

        # create alert levels objects from db
        self._cursor.execute("SELECT "
                             + "alertLevel, "
                             + "name, "
                             + "triggerAlways, "
                             + "rulesActivated "
                             + "FROM alertLevels")
        result = self._cursor.fetchall()

        for alert_level_tuple in result:
            alert_level = AlertLevel()
            alert_level.level = alert_level_tuple[0]
            alert_level.name = alert_level_tuple[1]
            alert_level.triggerAlways = alert_level_tuple[2]
            alert_level.rulesActivated = (alert_level_tuple[3] == 1)

            self._system_data.update_alert_level(alert_level)

        # create node objects from db
        self._cursor.execute("SELECT * FROM nodes")
        result = self._cursor.fetchall()

        for node_tuple in result:
            node = Node()
            node.nodeId = node_tuple[0]
            node.hostname = node_tuple[1]
            node.nodeType = node_tuple[2]
            node.instance = node_tuple[3]
            node.connected = node_tuple[4]
            node.version = node_tuple[5]
            node.rev = node_tuple[6]
            node.username = node_tuple[7]
            node.persistent = node_tuple[8]

            self._system_data.update_node(node)

        # create sensor objects from db
        self._cursor.execute("SELECT "
                             + "id, "
                             + "nodeId, "
                             + "remoteSensorId, "
                             + "description, "
                             + "state, "
                             + "lastStateUpdated, "
                             + "alertDelay, "
                             + "dataType "
                             + "FROM sensors")
        result = self._cursor.fetchall()

        for sensor_tuple in result:
            sensor = Sensor()
            sensor.sensorId = sensor_tuple[0]
            sensor.nodeId = sensor_tuple[1]
            sensor.remoteSensorId = sensor_tuple[2]
            sensor.description = sensor_tuple[3]
            sensor.state = sensor_tuple[4]
            sensor.lastStateUpdated = sensor_tuple[5]
            sensor.alertDelay = sensor_tuple[6]
            sensor.dataType = sensor_tuple[7]
            sensor.serverTime = server_time

            self._cursor.execute("SELECT "
                                 + "alertLevel "
                                 + "FROM sensorsAlertLevels "
                                 + "WHERE sensorId = %s", (sensor.sensorId, ))
            alert_level_result = self._cursor.fetchall()
            for alert_level_tuple in alert_level_result:
                sensor.alertLevels.append(alert_level_tuple[0])

            # Get sensor data from database.
            if sensor.dataType == SensorDataType.NONE:
                sensor.data = None

            elif sensor.dataType == SensorDataType.INT:
                self._cursor.execute("SELECT "
                                     + "data "
                                     + "FROM sensorsDataInt "
                                     + "WHERE sensorId = %s", (sensor.sensorId, ))
                data_result = self._cursor.fetchall()
                sensor.data = data_result[0][0]

            elif sensor.dataType == SensorDataType.FLOAT:
                self._cursor.execute("SELECT "
                                     + "data "
                                     + "FROM sensorsDataFloat "
                                     + "WHERE sensorId = %s", (sensor.sensorId, ))
                data_result = self._cursor.fetchall()
                sensor.data = data_result[0][0]

            self._system_data.update_sensor(sensor)

        # create alert objects from db
        self._cursor.execute("SELECT "
                             + "id, "
                             + "nodeId, "
                             + "remoteAlertId, "
                             + "description "
                             + "FROM alerts")
        result = self._cursor.fetchall()

        for alert_tuple in result:
            alert = Alert()
            alert.alertId = alert_tuple[0]
            alert.nodeId = alert_tuple[1]
            alert.remoteAlertId = alert_tuple[2]
            alert.description = alert_tuple[3]

            self._cursor.execute("SELECT "
                                 + "alertLevel "
                                 + "FROM alertsAlertLevels "
                                 + "WHERE alertId = %s", (alert.alertId, ))
            alert_level_result = self._cursor.fetchall()
            for alert_level_tuple in alert_level_result:
                alert.alertLevels.append(alert_level_tuple[0])

            self._system_data.update_alert(alert)

        # create manager objects from db
        self._cursor.execute("SELECT "
                             + "id, "
                             + "nodeId, "
                             + "description "
                             + "FROM managers")
        result = self._cursor.fetchall()

        for manager_tuple in result:
            manager = Manager()
            manager.managerId = manager_tuple[0]
            manager.nodeId = manager_tuple[1]
            manager.description = manager_tuple[2]

            self._system_data.update_manager(manager)

        # close connection to the database
        self._close_connection()

    def create_storage(self):
        """
        Creates the database (should only be called if the database does not exist).
        Has no return value but raise exception if it fails.
        """
        with self._lock:

            # connect to the database
            try:
                self._open_connection()

            except Exception:
                logging.exception("[%s]: Not able to connect to MySQL server." % self._log_tag)
                # remember to pass the exception
                raise

            # create internals table (used internally by the client)
            # if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'internals'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE internals ("
                                     + "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
                                     + "type VARCHAR(255) NOT NULL UNIQUE, "
                                     + "value DOUBLE NOT NULL)")

                # insert server time field
                self._cursor.execute("INSERT INTO internals ("
                                     + "type, "
                                     + "value) VALUES (%s, %s)",
                                     ("serverTime", 0.0))

                # insert version field
                self._cursor.execute("INSERT INTO internals ("
                                     + "type, "
                                     + "value) VALUES (%s, %s)",
                                     ("version", self._version))

                # insert rev field
                self._cursor.execute("INSERT INTO internals ("
                                     + "type, "
                                     + "value) VALUES (%s, %s)",
                                     ("rev", self._rev))

            # create options table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'options'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE options ("
                                     + "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
                                     + "type VARCHAR(255) NOT NULL UNIQUE, "
                                     + "value DOUBLE NOT NULL)")

            # create nodes table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'nodes'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE nodes ("
                                     + "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
                                     + "hostname VARCHAR(255) NOT NULL, "
                                     + "nodeType VARCHAR(255) NOT NULL, "
                                     + "instance VARCHAR(255) NOT NULL, "
                                     + "connected INTEGER NOT NULL, "
                                     + "version DOUBLE NOT NULL, "
                                     + "rev INTEGER NOT NULL, "
                                     + "username VARCHAR(255) NOT NULL, "
                                     + "persistent INTEGER NOT NULL)")

            # create sensors table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'sensors'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE sensors ("
                                     + "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
                                     + "nodeId INTEGER NOT NULL, "
                                     + "remoteSensorId INTEGER NOT NULL, "
                                     + "description VARCHAR(255) NOT NULL, "
                                     + "state INTEGER NOT NULL, "
                                     + "lastStateUpdated INTEGER NOT NULL, "
                                     + "alertDelay INTEGER NOT NULL, "
                                     + "dataType INTEGER NOT NULL, "
                                     + "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

            # Create sensorsDataInt table if it does not exist.
            self._cursor.execute("SHOW TABLES LIKE 'sensorsDataInt'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE sensorsDataInt ("
                                     + "sensorId INTEGER PRIMARY KEY NOT NULL, "
                                     + "data INTEGER NOT NULL, "
                                     + "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

            # Create sensorsDataFloat table if it does not exist.
            self._cursor.execute("SHOW TABLES LIKE 'sensorsDataFloat'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE sensorsDataFloat ("
                                     + "sensorId INTEGER PRIMARY KEY NOT NULL, "
                                     + "data REAL NOT NULL, "
                                     + "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

            # create sensorAlerts table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'sensorAlerts'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE sensorAlerts ("
                                     + "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
                                     + "sensorId INTEGER NOT NULL, "
                                     + "state INTEGER NOT NULL, "
                                     + "description TEXT NOT NULL,"
                                     + "timeReceived INTEGER NOT NULL, "
                                     + "dataJson TEXT NOT NULL, "
                                     + "dataType INTEGER NOT NULL)")

            # Create sensorAlertsDataInt table if it does not exist.
            self._cursor.execute("SHOW TABLES LIKE 'sensorAlertsDataInt'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE sensorAlertsDataInt ("
                                     + "sensorAlertId INTEGER PRIMARY KEY NOT NULL, "
                                     + "data INTEGER NOT NULL, "
                                     + "FOREIGN KEY(sensorAlertId) REFERENCES sensorAlerts(id))")

            # Create sensorAlertsDataFloat table if it does not exist.
            self._cursor.execute("SHOW TABLES LIKE 'sensorAlertsDataFloat'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE sensorAlertsDataFloat ("
                                     + "sensorAlertId INTEGER PRIMARY KEY NOT NULL, "
                                     + "data REAL NOT NULL, "
                                     + "FOREIGN KEY(sensorAlertId) REFERENCES sensorAlerts(id))")

            # create sensorAlertsAlertLevels table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'sensorAlertsAlertLevels'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE sensorAlertsAlertLevels ("
                                     + "sensorAlertId INTEGER NOT NULL, "
                                     + "alertLevel INTEGER NOT NULL, "
                                     + "PRIMARY KEY(sensorAlertId, alertLevel), "
                                     + "FOREIGN KEY(sensorAlertId) REFERENCES sensorAlerts(id))")

            # create sensorsAlertLevels table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'sensorsAlertLevels'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE sensorsAlertLevels ("
                                     + "sensorId INTEGER NOT NULL, "
                                     + "alertLevel INTEGER NOT NULL, "
                                     + "PRIMARY KEY(sensorId, alertLevel), "
                                     + "FOREIGN KEY(sensorId) REFERENCES sensors(id))")

            # create alerts table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'alerts'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE alerts ("
                                     + "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
                                     + "nodeId INTEGER NOT NULL, "
                                     + "remoteAlertId INTEGER NOT NULL, "
                                     + "description VARCHAR(255) NOT NULL, "
                                     + "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

            # create alertsAlertLevels table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'alertsAlertLevels'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE alertsAlertLevels ("
                                     + "alertId INTEGER NOT NULL, "
                                     + "alertLevel INTEGER NOT NULL, "
                                     + "PRIMARY KEY(alertId, alertLevel), "
                                     + "FOREIGN KEY(alertId) REFERENCES alerts(id))")

            # create managers table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'managers'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE managers ("
                                     + "id INTEGER PRIMARY KEY AUTO_INCREMENT, "
                                     + "nodeId INTEGER NOT NULL, "
                                     + "description VARCHAR(255) NOT NULL, "
                                     + "FOREIGN KEY(nodeId) REFERENCES nodes(id))")

            # create alert levels table if it does not exist
            self._cursor.execute("SHOW TABLES LIKE 'alertLevels'")
            result = self._cursor.fetchall()
            if len(result) == 0:
                self._cursor.execute("CREATE TABLE alertLevels ("
                                     + "alertLevel INTEGER PRIMARY KEY, "
                                     + "name VARCHAR(255) NOT NULL, "
                                     + "triggerAlways INTEGER NOT NULL, "
                                     + "rulesActivated INTEGER NOT NULL)")

            # commit all changes
            self._conn.commit()

            # close connection to the database
            self._close_connection()

    def update_server_information(self,
                                  server_time: int,
                                  options: List[Option],
                                  nodes: List[Node],
                                  sensors: List[Sensor],
                                  alerts: List[Alert],
                                  managers: List[Manager],
                                  alert_levels: List[AlertLevel],
                                  sensorAlerts: List[SensorAlert]) -> bool:
        """
        Updates the received server information.

        :param server_time:
        :param options:
        :param nodes:
        :param sensors:
        :param alerts:
        :param managers:
        :param alert_levels:
        :param sensorAlerts:
        :return: Success or Failure
        """
        with self._lock:

            # connect to the database
            try:
                self._open_connection()

            except Exception:
                logging.exception("[%s]: Not able to connect to MySQL server." % self._log_tag)
                self._close_connection()
                return False

            # Update server time.
            try:
                self._update_server_time(server_time)

            except Exception:
                logging.exception("[%s]: Not able to update server time." % self._log_tag)
                self._close_connection()
                return False

            # STEP ONE: delete all objects that do not exist anymore
            for option in self._db_copy_options:

                # Check if object does not exist anymore in received data.
                if option.is_deleted():
                    try:
                        self._delete_option(option.type)

                    except Exception:
                        self._close_connection()
                        return False

            # Delete all sensor alerts that are older than the configured life span.
            try:
                self._delete_sensor_alerts(self._sensor_alert_life_span * 86400)

            except Exception:
                self._close_connection()
                return False

            for sensor in self._db_copy_sensors:

                # Check if object does not exist anymore in received data.
                if sensor.is_deleted():
                    try:
                        self._delete_sensor(sensor.sensorId)

                    except Exception:
                        self._close_connection()
                        return False

            for alert in self._db_copy_alerts:

                # Check if object does not exist anymore in received data.
                if alert.is_deleted():
                    try:
                        self._delete_alert(alert.alertId)

                    except Exception:
                        self._close_connection()
                        return False

            for manager in self._db_copy_managers:

                # Check if object does not exist anymore in received data.
                if manager.is_deleted():
                    try:
                        self._delete_manager(manager.managerId)

                    except Exception:
                        self._close_connection()
                        return False

            for node in self._db_copy_nodes:

                # Check if object does not exist anymore in received data.
                if node not in nodes:
                    try:
                        self._delete_node(node.nodeId)

                    except Exception:
                        self._close_connection()
                        return False

            for alert_level in self._db_copy_alert_levels:

                # Check if object does not exist anymore in received data.
                if alert_level.is_deleted():
                    try:
                        self._delete_alert_level(alert_level.level)

                    except Exception:
                        self._close_connection()
                        return False

            # STEP TWO: update all existing objects and add new ones
            # (NOTE: first add nodes before alerts, sensors and managers
            # because of the foreign key dependency)
            for option in options:
                try:
                    self._update_option(option)

                except Exception:
                    self._close_connection()
                    return False

            for node in nodes:
                try:
                    self._update_node(node)

                except Exception:
                    self._close_connection()
                    return False

            for sensor in sensors:
                try:
                    self._update_sensor(sensor)

                except Exception:
                    self._close_connection()
                    return False

            for alert in alerts:
                try:
                    self._update_alert(alert)

                except Exception:
                    self._close_connection()
                    return False

            for manager in managers:
                try:
                    self._update_manager(manager)

                except Exception:
                    self._close_connection()
                    return False

            for alert_level in alert_levels:
                try:
                    self._update_alert_level(alert_level)

                except Exception:
                    self._close_connection()
                    return False

            for sensor_alert in sensorAlerts:
                try:
                    self._add_sensor_alert(sensor_alert)

                except Exception:
                    self._close_connection()
                    return False

            # commit all changes
            self._conn.commit()

            # close connection to the database
            self._close_connection()

            self._db_copy_options = options
            self._db_copy_nodes = nodes
            self._db_copy_alerts = alerts
            self._db_copy_managers = managers
            self._db_copy_sensors = sensors
            self._db_copy_alert_levels = alert_levels

            return True
