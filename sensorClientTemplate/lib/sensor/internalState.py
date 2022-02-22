#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


from typing import Any, Dict


class SensorInternalState:
    """
    Class represents the internal state of a sensor.
    """
    OK = 0
    GenericError = 1
    ProcessingError = 2
    TimeoutError = 3

    _str = {0: "OK",
            1: "Generic Error",
            2: "Processing Error",
            3: "Timeout Error"}

    def __init__(self, state: int = 0, msg: str = ""):
        self._state = state
        self._msg = msg

    def __str__(self) -> str:
        if self._state in SensorInternalState._str.keys():
            return "%s (%s)" % (SensorInternalState._str[self._state], self._msg)
        return "Unknown (%s)" % self._msg

    @property
    def state(self) -> int:
        return self._state

    @property
    def msg(self) -> str:
        return self._msg

    @staticmethod
    def copy_from_dict(data: Dict[str, Any]):
        """
        This function creates from the given dictionary an object of this class.
        This function has to succeed if verify_dict() says dictionary is correct.
        :param data:
        :return: object of this class
        """
        return SensorInternalState(data["state"], data["msg"])

    @staticmethod
    def deepcopy(obj):
        """
        This function copies all attributes of the given object to a new data object.
        :param obj:
        :return: object of this class
        """
        return SensorInternalState(obj.msg, obj.msg)

    @staticmethod
    def verify_dict(data: Dict[str, Any]) -> bool:
        """
        This function verifies the given dictionary representing this object for correctness.
        Meaning, if verify_dict() succeeds, copy_from_dict() has to be able to create a valid object.
        :return: correct or not
        """
        if (isinstance(data, dict)
                and all([x in data.keys() for x in ["state", "msg"]])
                and len(data.keys()) == 2
                and isinstance(data["state"], int)
                and isinstance(data["msg"], str)):
            return True
        return False

    def copy_to_dict(self) -> Dict[str, Any]:
        """
        Copies the object's data into a dictionary.
        :return: dictionary representation of a copy of this object
        """
        dict_obj = {"state": self._state,
                    "msg": self._msg,
                    }
        return dict_obj

    def deepcopy_obj(self, obj):
        """
        This function copies all attributes of the given object to this object.
        :param obj:
        :return: this object
        """
        self._state = obj.state
        self._msg = obj.msg
        return self

    def set_error(self, state: int, msg: str):
        if state not in SensorInternalState._str.keys():
            raise ValueError("State %d does not exist." % state)

        if state == SensorInternalState.OK:
            raise ValueError("State %d is not an error state." % state)

        if msg.strip() == "":
            raise ValueError("Message is not allowed to be empty.")

        self._state = state
        self._msg = msg

    def set_ok(self):
        self._state = SensorInternalState.OK
        self._msg = ""
