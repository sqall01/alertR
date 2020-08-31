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
import time
from typing import Optional
from ..localObjects import AlertLevel, SensorAlert


class PromiseState:
    SUCCESS = 1
    FAILED = 2
    PENDING = 3


class InstrumentationPromise:

    def __init__(self,
                 alert_level: AlertLevel,
                 sensor_alert: SensorAlert):
        self._alert_level = alert_level
        self._orig_sensor_alert = sensor_alert
        self._new_sensor_alert = None
        self._finished_event = threading.Event()
        self._finished_event.clear()
        self._state = PromiseState.PENDING
        self._creation_time = int(time.time())

    @property
    def alert_level(self):
        return self._alert_level

    @property
    def new_sensor_alert(self):
        return self._new_sensor_alert

    @property
    def orig_sensor_alert(self):
        return self._orig_sensor_alert

    def is_finished(self,
                    blocking: bool = False,
                    timeout: Optional[float] = None) -> bool:
        if blocking:
            self._finished_event.wait()

        if timeout is not None:
            self._finished_event.wait(timeout)

        return self._state != PromiseState.PENDING

    def set_failed(self):
        self._state = PromiseState.FAILED
        self._finished_event.set()

    def set_new_sensor_alert(self, sensor_alert: SensorAlert):
        self._new_sensor_alert = sensor_alert

    def set_success(self):
        self._state = PromiseState.SUCCESS
        self._finished_event.set()

    def was_successful(self):
        if self._state == PromiseState.SUCCESS:
            return True

        elif self._state == PromiseState.FAILED:
            return False

        else:
            raise ValueError("Instrumentation not finished.")


class Instrumentation:

    def __init__(self, alert_level: AlertLevel, sensor_alert: SensorAlert, logger: logging.Logger):
        self._log_tag = os.path.basename(__file__)
        self._logger = logger
        self._alert_level = alert_level
        self._sensor_alert = sensor_alert
        self._promise = None  # type: Optional[InstrumentationPromise]
        self._thread = None  # type: Optional[threading.Thread]

    def _execute(self):
        """
        Execute instrumentation script with sensor alert as first argument in json format and
        process output of instrumentation script.
        """
        temp_execute = [self._alert_level.instrumentation_cmd, json.dumps(self._sensor_alert.convert_to_dict())]
        self._logger.debug("[%s]: Executing command '%s'." % (self._log_tag, " ".join(temp_execute)))

        process = None
        try:
            process = subprocess.Popen(temp_execute,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

        except Exception:
            self._logger.exception("[%s]: Executing instrumentation for Alert Level '%d' failed."
                                   % (self._log_tag, self._alert_level.level))
            self._logger.error("[%s]: Command was: %s" % (self._log_tag, " ".join(temp_execute)))

            # Set result.
            self._promise.set_failed()

            return

        try:
            process.wait(self._alert_level.instrumentation_timeout)

        except subprocess.TimeoutExpired:
            self._logger.error("[%s]: Instrumentation for Alert Level '%d' timed out."
                               % (self._log_tag, self._alert_level.level))
            process.terminate()

            # Give the process one second to terminate
            time.sleep(1)

            # check if the process has terminated
            # => if not kill it
            exit_code = process.poll()
            if exit_code != -15:
                try:
                    self._logger.error("[%s]: Could not terminate instrumentation for Alert Level '%d'. Killing it."
                                       % (self._log_tag, self._alert_level.level))

                    process.kill()
                except Exception:
                    pass

            # Set result.
            self._promise.set_failed()

            return

        exit_code = process.poll()
        output, err = process.communicate()
        output = output.decode("ascii")
        err = err.decode("ascii")

        if exit_code == 0:

            new_sensor_alert = self._process_output(output)

            if new_sensor_alert is not None:
                self._logger.error("[%s]: Unable to process output from instrumentation for Alert Level '%d'."
                                   % (self._log_tag, self._alert_level.level))
                self._logger.error("[%s]: Instrumentation for Alert Level '%d' stdout: %s"
                                   % (self._log_tag, self._alert_level.level, output))
                self._logger.error("[%s]: Instrumentation for Alert Level '%d' stderr: %s"
                                   % (self._log_tag, self._alert_level.level, err))

                # Set result.
                self._promise.set_new_sensor_alert(new_sensor_alert)
                self._promise.set_success()

            else:
                # Set result.
                self._promise.set_failed()

        else:
            self._logger.error("[%s]: Instrumentation for Alert Level '%d' exited with exit code '%d'."
                               % (self._log_tag, self._alert_level.level, exit_code))
            self._logger.error("[%s]: Instrumentation for Alert Level '%d' stdout: %s"
                               % (self._log_tag, self._alert_level.level, output))
            self._logger.error("[%s]: Instrumentation for Alert Level '%d' stderr: %s"
                               % (self._log_tag, self._alert_level.level, err))

            # Set result.
            self._promise.set_failed()

    def _process_output(self, output: str) -> Optional[SensorAlert]:
        """
        Process output of instrumentation script.
        :param output: output of instrumentation script as string
        :return success or failure
        """

        try:
            self._logger.debug("[%s] Received output from instrumentation for Alert Level '%d': %s"
                               % (self._log_tag, self._alert_level.level, output))

            sensor_alert_dict = json.loads(output)
            new_sensor_alert = SensorAlert.convert_from_dict(sensor_alert_dict)

            # Verify data types of attributes (raises ValueError if type is wrong).
            new_sensor_alert.verify_types()

            # Check that certain sensor alert values have not changed.
            if self._sensor_alert.sensorAlertId != new_sensor_alert.sensorAlertId:
                raise ValueError("sensorAlertId not allowed to change")

            if self._sensor_alert.nodeId != new_sensor_alert.nodeId:
                raise ValueError("nodeId not allowed to change")

            if self._sensor_alert.sensorId != new_sensor_alert.sensorId:
                raise ValueError("sensorId not allowed to change")

            if self._sensor_alert.description != new_sensor_alert.description:
                raise ValueError("description not allowed to change")

            if self._sensor_alert.timeReceived != new_sensor_alert.timeReceived:
                raise ValueError("timeReceived not allowed to change")

            if self._sensor_alert.alertDelay != new_sensor_alert.alertDelay:
                raise ValueError("alertDelay not allowed to change")

            if (any(map(lambda x: x not in self._sensor_alert.alertLevels, new_sensor_alert.alertLevels))
                    or any(map(lambda x: x not in new_sensor_alert.alertLevels, self._sensor_alert.alertLevels))):
                raise ValueError("alertLevels not allowed to change")

            if (any(map(lambda x: x not in self._sensor_alert.triggeredAlertLevels,
                        new_sensor_alert.triggeredAlertLevels))
                    or any(map(lambda x: x not in new_sensor_alert.triggeredAlertLevels,
                               self._sensor_alert.triggeredAlertLevels))):
                raise ValueError("triggeredAlertLevels not allowed to change")

            if self._sensor_alert.dataType != new_sensor_alert.dataType:
                raise ValueError("dataType not allowed to change")

        except Exception:
            self._logger.exception("[%s]: Could not parse received output from from instrumentation "
                                   % self._log_tag
                                   + "for Alert Level '%d'."
                                   % self._alert_level.level)
            return None

        return new_sensor_alert

    def execute(self) -> InstrumentationPromise:
        """
        Execute instrumentation in a non-blocking way.
        :return: promise which contains the results after instrumentation finished execution.
        """
        self._promise = InstrumentationPromise(self._alert_level, self._sensor_alert)

        self._thread = threading.Thread(target=self._execute)
        self._thread.daemon = True
        self._thread.start()

        return self._promise

# TODO test cases