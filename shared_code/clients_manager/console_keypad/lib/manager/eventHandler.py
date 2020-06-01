#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from typing import List, Any
from .screenUpdater import ScreenUpdater
from .core import BaseManagerEventHandler
from ..localObjects import Option, Node, Sensor, Manager, Alert, AlertLevel, SensorAlert, SensorDataType
from ..globalData import GlobalData


# this class handles an incoming server event (sensor alert message,
# status update, ...)
class ManagerEventHandler(BaseManagerEventHandler):

    def __init__(self,
                 global_data: GlobalData):
        super().__init__(global_data)

        # get global configured data
        self.global_data = global_data
        self.screen_updater = self.global_data.screenUpdater  # type: ScreenUpdater

    # is called when a status update event was received from the server
    def status_update(self,
                      server_time: int,
                      options: List[Option],
                      nodes: List[Node],
                      sensors: List[Sensor],
                      managers: List[Manager],
                      alerts: List[Alert],
                      alert_levels: List[AlertLevel]) -> bool:

        result = super().status_update(server_time,
                                       options,
                                       nodes,
                                       sensors,
                                       managers,
                                       alerts,
                                       alert_levels)


        # TODO
        '''
        self.sensors.sort(key=lambda x: x.description.lower())


        self.managers.sort(key=lambda x: x.description.lower())


        self.alerts.sort(key=lambda x: x.description.lower())


        self.alertLevels.sort(key=lambda x: x.level)
        '''

        self.screen_updater.update_status()

        return result

    # is called when a sensor alert event was received from the server
    def sensor_alert(self, server_time: int, sensor_alert: SensorAlert) -> bool:

        result = super().sensor_alert(server_time,
                                      sensor_alert)

        self.screen_updater.update_sensor_alerts()

        return result

    # is called when a state change event was received from the server
    def state_change(self,
                     server_time: int,
                     sensor_id: int,
                     state: int,
                     data_type: SensorDataType,
                     sensor_data: Any) -> bool:

        result = super().state_change(server_time,
                                      sensor_id,
                                      state,
                                      data_type,
                                      sensor_data)

        self.screen_updater.update_status()

        return result

    def close_connection(self):
        super().close_connection()

        self.screen_updater.update_connection_fail()

    def new_connection(self):
        super().new_connection()

        self.screen_updater.update_status()
