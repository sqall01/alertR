#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import logging
from typing import Dict
from ..localObjects import Alert, AlertLevel, Manager, Node, Sensor, SensorAlert, Option


class SystemData:

    def __init__(self):

        # key: type
        self._options = dict()  # type: Dict[str, Option]

        # key: nodeId
        self._nodes = dict()  # type: Dict[int, Node]

        # key: sensorId
        self._sensors = dict()  # type: Dict[int, Sensor]

        # key: managerId
        self._managers = dict()  # type: Dict[int, Manager]

        # key: alertId
        self._alerts = dict()  # type: Dict[int, Alert]

        # TODO: list perhaps better? How long do we store sensorAlerts? Perhaps give function to delete all sensor alerts older than X?
        self._sensor_alerts = dict()

        # key: level
        self._alert_levels = dict()  # type: Dict[int, AlertLevel]

        self._data_lock = threading.Lock()

    def _alert_sanity_check(self, alert: Alert):
        # Does corresponding node exist?
        if alert.nodeId not in self._nodes.keys():
            raise ValueError("Node %d for corresponding alert %d does not exist."
                             % (alert.nodeId, alert.alertId))

        # Does corresponding node have correct type?
        if self._nodes[alert.alertId].nodeType.lower() != "alert":
            raise ValueError("Node %d not of correct type for corresponding alert %d."
                             % (alert.nodeId, alert.alertId))

    def update_option(self, option: Option):
        """
        Updates the given option data.
        :param option:
        :return: success of failure
        """
        with self._data_lock:
            # Just change value, does not make a difference if it already exists or not.
            self._options[option.type] = option.value

    def update_alert(self, alert: Alert):
        """
        Updates the given alert data.
        :param alert:
        """
        with self._data_lock:

            # Add alert object if it does not exist yet.
            if alert.alertId not in self._alerts.keys():
                self._alert_sanity_check(alert)
                self._alerts[alert.alertId] = alert

            # Update alert object data.
            else:
                self._alert_sanity_check(alert)

                # Do update of data instead of just using new alert object
                # to make sure others can work on the same object.
                self._alerts[alert.alertId].deepCopy(alert)

    def update_alert_level(self, alert_level: AlertLevel):
        """
        Updates the given alert level data.
        :param alert_level:
        """
        with self._data_lock:

            # Add alert level object if it does not exist yet.
            if alert_level.level not in self._alert_levels.keys():
                self._alert_levels[alert_level.level] = alert_level

            # Update alert level object data.
            else:

                # Do update of data instead of just using new alert level object
                # to make sure others can work on the same object.
                self._alert_levels[alert_level.level].deepCopy(alert_level)





# TODO
# * handle storage of AlertR data
# * only have atomic interfaces (update, delete, get) and let big picture like "node X was deleted" be handled by eventmanager
# * lock data when accessed
# * give interfaces to get copy of data (perhaps also list of Node/Alert/... to be compatible with old managers?)
# * test cases to check if it works