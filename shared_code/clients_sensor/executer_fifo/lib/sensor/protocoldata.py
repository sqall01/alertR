#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import json
from .core import _PollingSensor
from ..globalData.sensorObjects import SensorDataType, SensorErrorState


# noinspection PyAbstractClass
class _ProtocolDataSensor(_PollingSensor):
    """
    Class implements processing of sensor data protocol data.
    """

    def __init__(self):
        super().__init__()

        # used for logging
        self._log_tag = os.path.basename(__file__)

    def _check_data_type(self, data_type: int) -> int:
        if not isinstance(data_type, int):
            return False
        if data_type != self.sensorDataType:
            return False
        return True

    # noinspection PyMethodMayBeStatic
    def _check_change_state(self, change_state: bool) -> bool:
        if not isinstance(change_state, bool):
            return False
        return True

    # noinspection PyMethodMayBeStatic
    def _check_has_latest_data(self, has_latest_data: bool) -> bool:
        if not isinstance(has_latest_data, bool):
            return False
        return True

    # noinspection PyMethodMayBeStatic
    def _check_has_optional_data(self, has_optional_data: bool) -> bool:
        if not isinstance(has_optional_data, bool):
            return False
        return True

    # noinspection PyMethodMayBeStatic
    def _check_state(self, state) -> bool:
        if not isinstance(state, int):
            return False
        if state != 0 and state != 1:
            return False
        return True

    def _process_protocol_data(self, data: str) -> bool:
        """
        Internal function that processes data according to the sensor protocol. Function fails directly if data is
        invalid. If function fails it does not modify the sensor error state or creates an event for it.
        This has to be done by the caller if desired.

        :param data:
        :return: success or failure
        """

        # Parse data.
        # noinspection PyBroadException,PyUnusedLocal
        try:

            message = json.loads(data)

            # Parse message depending on type.
            # Type: statechange
            if str(message["message"]).upper() == "STATECHANGE":

                # Check if state is valid.
                temp_input_state = message["payload"]["state"]
                if not self._check_state(temp_input_state):
                    self._log_error(self._log_tag, "Received 'state' invalid. Ignoring message.")
                    return False

                # Check if data type is valid.
                temp_data_type = message["payload"]["dataType"]
                if not self._check_data_type(temp_data_type):
                    self._log_error(self._log_tag,
                                    "Received 'dataType' invalid. Ignoring message.")
                    return False

                # Get new data.
                sensor_data_class = SensorDataType.get_sensor_data_class(temp_data_type)
                if not sensor_data_class.verify_dict(message["payload"]["data"]):
                    self._log_error(self._log_tag, "Received 'data' invalid. Ignoring message.")
                    return False
                temp_input_data = sensor_data_class.copy_from_dict(message["payload"]["data"])

                # Create state change object that is send to the server if the data could be changed
                # or the state has changed.
                if self.data != temp_input_data or self.state != temp_input_state:
                    self._add_state_change(temp_input_state,
                                           temp_input_data)

            # Type: sensoralert
            elif str(message["message"]).upper() == "SENSORALERT":

                # Check if state is valid.
                temp_input_state = message["payload"]["state"]
                if not self._check_state(temp_input_state):
                    self._log_error(self._log_tag, "Received 'state' invalid. Ignoring message.")
                    return False

                # Check if hasOptionalData field is valid.
                temp_has_optional_data = message["payload"]["hasOptionalData"]
                if not self._check_has_optional_data(temp_has_optional_data):
                    self._log_error(self._log_tag,
                                    "Received 'hasOptionalData' field invalid. Ignoring message.")
                    return False

                # Check if data type is valid.
                temp_data_type = message["payload"]["dataType"]
                if not self._check_data_type(temp_data_type):
                    self._log_error(self._log_tag,
                                    "Received 'dataType' invalid. Ignoring message.")
                    return False

                sensor_data_class = SensorDataType.get_sensor_data_class(temp_data_type)
                if not sensor_data_class.verify_dict(message["payload"]["data"]):
                    self._log_error(self._log_tag, "Received 'data' invalid. Ignoring message.")
                    return False
                temp_input_data = sensor_data_class.copy_from_dict(message["payload"]["data"])

                # Check if hasLatestData field is valid.
                temp_has_latest_data = message["payload"]["hasLatestData"]
                if not self._check_has_latest_data(temp_has_latest_data):
                    self._log_error(self._log_tag,
                                    "Received 'hasLatestData' field invalid. Ignoring message.")
                    return False

                # Check if changeState field is valid.
                temp_change_state = message["payload"]["changeState"]
                if not self._check_change_state(temp_change_state):
                    self._log_error(self._log_tag,
                                    "Received 'changeState' field invalid. Ignoring message.")
                    return False

                # Check if data should be transferred with the sensor alert
                # => if it should parse it
                temp_optional_data = None
                if temp_has_optional_data:

                    temp_optional_data = message["payload"]["optionalData"]

                    # check if data is of type dict
                    if not isinstance(temp_optional_data, dict):
                        self._log_error(self._log_tag,
                                        "Received 'optionalData' invalid. Ignoring message.")
                        return False

                self._add_sensor_alert(temp_input_state,
                                       temp_change_state,
                                       temp_optional_data,
                                       temp_has_latest_data,
                                       temp_input_data)

            # Type: errorstatechange
            elif str(message["message"]).upper() == "ERRORSTATECHANGE":

                # Check if error state is valid.
                temp_input_error_state = message["payload"]["error_state"]
                if not SensorErrorState.verify_dict(temp_input_error_state):
                    self._log_error(self._log_tag,
                                    "Received 'error_state' invalid. Ignoring message.")
                    return False

                self._set_error_state(temp_input_error_state["state"], temp_input_error_state["msg"])

            # Type: invalid
            else:
                raise ValueError("Invalid message type.")

        except Exception as e:
            self._log_exception(self._log_tag, "Could not parse received data.")
            return False

        return True
