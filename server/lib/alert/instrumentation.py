#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.
import json
import logging
import os
import subprocess
import threading
from ..localObjects import AlertLevel, SensorAlert


class Instrumentation:

    def __init__(self, alert_level: AlertLevel, sensor_alert: SensorAlert, logger: logging.Logger):
        self._log_tag = os.path.basename(__file__)
        self._logger = logger
        self._alert_level = alert_level
        self._sensor_alert = sensor_alert
        self._thread = None

    def _execute(self):
        temp_execute = [self._alert_level.instrumentation_cmd, json.dumps(self._sensor_alert.convertToDict())]
        self._logger.debug("[%s]: Executing command '%s'." % (self._log_tag, " ".join(temp_execute)))

        try:
            subprocess.Popen(temp_execute, close_fds=True)
        except Exception as e:
            self._logger.exception("[%s]: Executing instrumentation for Alert Level '%d' failed."
                              % (self._log_tag, self._alert_level.level))
            self._logger.error("[%s]: Command was: %s" % (self._log_tag, " ".join(temp_execute)))

    def execute(self):
        """
        Execute instrumentation in a non-blocking way.
        """
        self._thread = threading.Thread(target=self._execute)
        self._thread.daemon = True
        self._thread.start()
