from unittest import TestCase
from lib.globalData.sensorObjects import SensorErrorState


class TestSensorErrorState(TestCase):

    # noinspection PyMethodMayBeStatic
    def _eq_attributes(self, obj1: SensorErrorState, obj2: SensorErrorState) -> bool:
        return obj1.state == obj2.state and obj1.msg == obj2.msg

    def test_valid_obj_creation_default(self):
        """
        Tests valid default object creation.
        """
        obj = SensorErrorState()

        self.assertEqual(obj.state, SensorErrorState.OK)
        self.assertEqual(obj.msg, "")

    def test_valid_obj_creation_ok(self):
        """
        Tests valid OK object creation.
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        self.assertEqual(obj.state, SensorErrorState.OK)
        self.assertEqual(obj.msg, "")

    def test_valid_obj_creation_not_ok(self):
        """
        Tests valid GenericError object creation.
        """
        obj = SensorErrorState(SensorErrorState.GenericError, "Generic Error Msg")

        self.assertEqual(obj.state, SensorErrorState.GenericError)
        self.assertEqual(obj.msg, "Generic Error Msg")

    def test_invalid_obj_creation_ok(self):
        """
        Tests invalid OK object creation.
        """
        was_exception = False
        try:
            obj = SensorErrorState(SensorErrorState.OK, "OK Msg")
        except ValueError as e:
            self.assertEqual(str(e), "Message has to be empty.")
            was_exception = True

        self.assertTrue(was_exception)

    def test_invalid_obj_creation_not_ok(self):
        """
        Tests invalid GenericError object creation.
        """
        was_exception = False
        try:
            obj = SensorErrorState(SensorErrorState.GenericError, "")
        except ValueError as e:
            self.assertEqual(str(e), "Message is not allowed to be empty.")
            was_exception = True

        self.assertTrue(was_exception)

    def test_invalid_obj_creation(self):
        """
        Tests invalid unknown object creation.
        """
        was_exception = False
        try:
            obj = SensorErrorState(1337, "")
        except ValueError as e:
            self.assertEqual(str(e), "State 1337 does not exist.")
            was_exception = True

        self.assertTrue(was_exception)

    def test_deepcopy_obj(self):
        """
        Tests deepcopy of an object.
        """
        obj = SensorErrorState(SensorErrorState.GenericError, "Some Msg")

        obj_copy = SensorErrorState().deepcopy_obj(obj)

        self.assertEqual(obj_copy, obj)
        self.assertFalse(obj_copy is obj)
        self.assertTrue(self._eq_attributes(obj, obj_copy))

    def test_to_dict_from_dict(self):
        """
        Tests copying to dict and from dict.
        """
        obj = SensorErrorState(SensorErrorState.GenericError, "Some Msg")

        obj_dict = obj.copy_to_dict()
        obj_copy = SensorErrorState().copy_from_dict(obj_dict)

        self.assertEqual(obj_copy, obj)
        self.assertFalse(obj_copy is obj)
        self.assertTrue(self._eq_attributes(obj, obj_copy))

    def test_valid_verify_dict(self):
        """
        Tests verifying the object as dictionary.
        """
        obj = SensorErrorState(SensorErrorState.GenericError, "Some Msg")

        obj_dict = obj.copy_to_dict()

        self.assertTrue(SensorErrorState.verify_dict(obj_dict))

    def test_invalid_verify_dict_empty_msg(self):
        """
        Tests verifying the object as dictionary (invalid empty msg).
        """
        obj = SensorErrorState(SensorErrorState.GenericError, "Some Msg")

        obj_dict = obj.copy_to_dict()
        obj_dict["msg"] = ""

        self.assertFalse(SensorErrorState.verify_dict(obj_dict))

    def test_invalid_verify_dict_non_empty_msg(self):
        """
        Tests verifying the object as dictionary (invalid non-empty msg).
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        obj_dict = obj.copy_to_dict()
        obj_dict["msg"] = "Some Msg"

        self.assertFalse(SensorErrorState.verify_dict(obj_dict))

    def test_invalid_verify_dict_keys(self):
        """
        Tests verifying the object as dictionary (additional invalid key).
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        obj_dict = obj.copy_to_dict()
        obj_dict["something"] = "Some Msg"

        self.assertFalse(SensorErrorState.verify_dict(obj_dict))

    def test_invalid_verify_dict_key_missing_state(self):
        """
        Tests verifying the object as dictionary (missing state key).
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        obj_dict = obj.copy_to_dict()
        del obj_dict["state"]

        self.assertFalse(SensorErrorState.verify_dict(obj_dict))

    def test_invalid_verify_dict_key_missing_msg(self):
        """
        Tests verifying the object as dictionary (missing msg key).
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        obj_dict = obj.copy_to_dict()
        del obj_dict["msg"]

        self.assertFalse(SensorErrorState.verify_dict(obj_dict))

    def test_invalid_verify_dict_state_unknown(self):
        """
        Tests verifying the object as dictionary (unknown state).
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        obj_dict = obj.copy_to_dict()
        obj_dict["state"] = 1337

        self.assertFalse(SensorErrorState.verify_dict(obj_dict))

    def test_invalid_verify_dict_state_wrong_data_type(self):
        """
        Tests verifying the object as dictionary (state wrong data type).
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        obj_dict = obj.copy_to_dict()
        obj_dict["state"] = 0.0

        self.assertFalse(SensorErrorState.verify_dict(obj_dict))

    def test_invalid_verify_dict_msg_wrong_data_type(self):
        """
        Tests verifying the object as dictionary (msg wrong data type).
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        obj_dict = obj.copy_to_dict()
        obj_dict["msg"] = 1337

        self.assertFalse(SensorErrorState.verify_dict(obj_dict))

    def test_valid_set_error(self):
        """
        Tests valid set error conditions.
        """
        obj = SensorErrorState(SensorErrorState.OK, "")
        obj.set_error(SensorErrorState.GenericError, "Some error")

        self.assertEqual(obj.state, SensorErrorState.GenericError)
        self.assertEqual(obj.msg, "Some error")

    def test_invalid_set_error_state_unknown(self):
        """
        Tests invalid set error conditions (unknown state)
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        was_exception = False
        try:
            obj.set_error(1337, "Some error")
        except ValueError as e:
            self.assertEqual(str(e), "State 1337 does not exist.")
            was_exception = True

        self.assertTrue(was_exception)

    def test_invalid_set_error_state_ok(self):
        """
        Tests invalid set error conditions (OK state)
        """
        obj = SensorErrorState(SensorErrorState.GenericError, "Some msg")

        was_exception = False
        try:
            obj.set_error(SensorErrorState.OK, "")
        except ValueError as e:
            self.assertEqual(str(e), "State 0 is not an error state.")
            was_exception = True

        self.assertTrue(was_exception)

    def test_invalid_set_error_msg_empty(self):
        """
        Tests invalid set error conditions (msg empty)
        """
        obj = SensorErrorState(SensorErrorState.OK, "")

        was_exception = False
        try:
            obj.set_error(SensorErrorState.GenericError, "")
        except ValueError as e:
            self.assertEqual(str(e), "Message is not allowed to be empty.")
            was_exception = True

        self.assertTrue(was_exception)
