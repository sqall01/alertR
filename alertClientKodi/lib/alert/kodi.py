#!/usr/bin/python3

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

    # this function is called once when the alert client has connected itself
    # to the server
    def initializeAlert(self):

        # set the time of the trigger
        self.triggered = 0.0

    # this function is called when this alert is triggered
    def triggerAlert(self, sensorAlert: SensorAlert):

        # only execute if the last triggered alert was more than
        # the configured trigger delay ago
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.triggered) > self.triggerDelay:

            # set the time the alert was triggered
            self.triggered = utcTimestamp

            # extract the received message if it was received and should be
            # displayed
            receivedMessage = None
            if self.displayReceivedMessage and sensorAlert.hasOptionalData:

                if "message" in sensorAlert.optionalData.keys():
                    receivedMessage = sensorAlert.optionalData["message"]

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
            if not response is None and response["result"] == "pong":

                # get player id of the player instance that plays audio/video
                playerId = None
                response = kodi_obj.Player.GetActivePlayers()
                for i in range(len(response["result"])):
                    if response["result"][i]["type"] == "audio" or response["result"][i]["type"] == "video":
                        playerId = response["result"][i]["playerid"]

                # if audio/video is played => pause it if configured
                if not playerId is None and self.pausePlayer is True:
                    kodi_obj.Player.PlayPause(playerid=playerId, play=False)

                # show a message on the display if configured
                if self.showMessage is True:

                    # differentiate between a generic displayed notification
                    # and a notification which also shows the received message
                    if receivedMessage is None:

                        # differentiate between a sensor alert triggered by
                        # a sensor going back in normal state or in alert state
                        if sensorAlert.state == 1:
                            tempMessage = "\"" + sensorAlert.description + "\" triggered."
                        else:
                            tempMessage = "\"" + sensorAlert.description + "\" back to normal."

                    else:

                        # differentiate between a sensor alert triggered by
                        # a sensor going back in normal state or in alert state
                        if sensorAlert.state == 1:
                            tempMessage = "\"" \
                                          + sensorAlert.description \
                                          + "\" triggered. Received message: \"" \
                                          + receivedMessage \
                                          + "\""
                        else:
                            tempMessage = "\"" \
                                          + sensorAlert.description \
                                          + "\" back to normal. Received message: \"" \
                                          + receivedMessage \
                                          + "\""

                    kodi_obj.GUI.ShowNotification(title="AlertR",
                                                  message=tempMessage,
                                                  image=self.icon,
                                                  displaytime=self.displayTime)

            else:
                logging.error("[%s]: Kodi does not respond." % self.fileName)

    # this function is called when the alert is stopped
    def stopAlert(self, sensorAlert: SensorAlert):
        pass
