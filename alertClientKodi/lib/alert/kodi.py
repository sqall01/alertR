#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import os
import logging
import kodijson
from .core import _Alert, SensorAlert


# this function class an alert that controls a kodi instance
# (for example shows a notification and pauses the player)
class KodiAlert(_Alert):

    def __init__(self):
        _Alert.__init__(self)

        self.fileName = os.path.basename(__file__)

        # these values are used to check when the alert was triggered
        # the last time and if it should trigger again
        self.triggered = None
        self.triggerDelay = None

        # host and port of the kodi instance
        self.host = None
        self.port = None
        
        # message notification
        self.showMessage = None
        self.displayTime = None

        # display a received message (if any was received)
        self.displayReceivedMessage = None

        # should the player be paused
        self.pausePlayer = None

        # File location of icon to display.
        self.icon = ""  # type: str

    def _process_alert(self, sensor_alert: SensorAlert):

        # only execute if the last triggered alert was more than
        # the configured trigger delay ago
        utc_timestamp = int(time.time())
        if (utc_timestamp - self.triggered) > self.triggerDelay:

            # set the time the alert was triggered
            self.triggered = utc_timestamp

            # extract the received message if it was received and should be
            # displayed
            received_message = None
            if self.displayReceivedMessage and sensor_alert.hasOptionalData:

                if "message" in sensor_alert.optionalData.keys():
                    received_message = sensor_alert.optionalData["message"]

            # connect to the kodi json rpc service
            try:
                kodi_obj = kodijson.Kodi("http://" + self.host + ":" + str(self.port) + "/jsonrpc")

            except Exception as e:
                logging.exception("[%s]: Not able to connect to Kodi instance." % self.fileName)
                return

            # ping the kodi instance
            try:
                response = kodi_obj.JSONRPC.Ping()

            except Exception as e:
                logging.exception("[%s]: Not able to ping Kodi instance." % self.fileName)
                return

            # check if kodi instance respond
            if response is not None and response["result"] == "pong":

                # get player id of the player instance that plays audio/video
                player_id = None
                response = kodi_obj.Player.GetActivePlayers()
                for i in range(len(response["result"])):
                    if response["result"][i]["type"] == "audio" or response["result"][i]["type"] == "video":
                        player_id = response["result"][i]["playerid"]

                # if audio/video is played => pause it if configured
                if player_id is not None and self.pausePlayer is True:
                    kodi_obj.Player.PlayPause(playerid=player_id, play=False)

                # show a message on the display if configured
                if self.showMessage is True:

                    # differentiate between a generic displayed notification
                    # and a notification which also shows the received message
                    if received_message is None:

                        # differentiate between a sensor alert triggered by
                        # a sensor going back in normal state or in alert state
                        if sensor_alert.state == 1:
                            temp_message = "\"" + sensor_alert.description + "\" triggered."
                        else:
                            temp_message = "\"" + sensor_alert.description + "\" back to normal."

                    else:

                        # differentiate between a sensor alert triggered by
                        # a sensor going back in normal state or in alert state
                        if sensor_alert.state == 1:
                            temp_message = "\"" \
                                          + sensor_alert.description \
                                          + "\" triggered. Received message: \"" \
                                          + received_message \
                                          + "\""
                        else:
                            temp_message = "\"" \
                                          + sensor_alert.description \
                                          + "\" back to normal. Received message: \"" \
                                          + received_message \
                                          + "\""

                    kodi_obj.GUI.ShowNotification(title="AlertR",
                                                  message=temp_message,
                                                  image=self.icon,
                                                  displaytime=self.displayTime)

            else:
                logging.error("[%s]: Kodi does not respond." % self.fileName)

    def initialize(self):
        """
        Is called when Alert Client is started to initialize the Alert object.
        """

        # set the time of the trigger
        self.triggered = 0.0

    def alert_triggered(self, sensor_alert: SensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 1.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        self._process_alert(sensor_alert)

    def alert_normal(self, sensor_alert: SensorAlert):
        """
        Is called when Alert Client receives a "sensoralert" message with the state set to 0.

        :param sensor_alert: object that contains the received "sensoralert" message.
        """
        self._process_alert(sensor_alert)

    def alert_off(self):
        """
        Is called when Alert Client receives a "sensoralertsoff" message which is
        sent as soon as AlertR alarm status is deactivated.
        """
        pass
