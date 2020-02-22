#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

from .localObjects import ErrorCodes
from .globalData import GlobalData
import time
import threading
import os
import json
import requests


# this class participates in the AlertR survey (if it is activated)
class SurveyExecuter(threading.Thread):

    def __init__(self,
                 uses_version_informer_sensor: bool,
                 updateUrl: str,
                 globalData: GlobalData,
                 timeout: float = 20.0):
        threading.Thread.__init__(self)

        # used for logging
        self.fileName = os.path.basename(__file__)

        # get global configured data
        self.globalData = globalData
        self.logger = self.globalData.logger
        self.storage = self.globalData.storage
        self.instance = self.globalData.instance
        self.version = self.globalData.version
        self.rev = self.globalData.rev
        self.uses_version_informer_sensor = uses_version_informer_sensor
        self.updateUrl = updateUrl
        self.timeout = timeout

        # fixed values for survey
        self.surveyInterval = 604800  # week
        self.host = "https://alertr.de/submit.php"

    def sendSurveyData(self) -> bool:
        """
        Gather and send survey data.

        :return: Success or Failure
        """
        self.logger.info("[%s]: Starting to send survey data." % self.fileName)

        # gather survey data
        surveyNodes = self.storage.getSurveyData()
        if surveyNodes is None:
            self.logger.error("[%s]: Did not get any survey data from the database." % self.fileName)
            return False

        surveyData = dict()
        surveyData["type"] = "survey"
        surveyData["nodes"] = surveyNodes

        surveyUpdate = dict()
        surveyUpdate["activated"] = self.uses_version_informer_sensor
        surveyUpdate["server"] = self.updateUrl
        surveyUpdate["location"] = ""

        surveyData["update"] = surveyUpdate
        surveyData["uniqueID"] = self.storage.getUniqueID()

        # Send survey data to server.
        try:
            payload = {"data": json.dumps(surveyData)}
            r = requests.post(self.host,
                              verify=True,
                              data=payload,
                              timeout=self.timeout)

            # Check if server responded correctly.
            if r.status_code != 200:
                raise ValueError("Server response code not 200 (was %d)." % r.status_code)

            data = r.json()
            if data["code"] != ErrorCodes.NO_ERROR:
                msg = ""
                if "msg" in data.keys():
                    msg = data["msg"]
                raise ValueError("Server responded with error code '%d' and message: '%s'." % (data["code"], msg))

        except Exception as e:
            self.logger.exception("[%s]: Sending survey data failed." % self.fileName)
            return False

        self.logger.info("[%s]: Survey data successfully sent." % self.fileName)
        return True

    def run(self):
        while True:
            # sleep for the interval before participating to the survey
            time.sleep(self.surveyInterval)
            self.sendSurveyData()
