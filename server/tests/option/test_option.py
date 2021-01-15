import logging
import time
import os
import collections
import threading
from unittest import TestCase
from typing import Tuple, List, Dict, Optional
from tests.util import config_logging
from lib.localObjects import Option
from lib.option.option import OptionExecuter
from lib.globalData import GlobalData
from lib.storage.core import _Storage
from lib.internalSensors import AlertLevelInstrumentationErrorSensor


class MockManagerUpdateExecuter:

    def __init__(self):
        self._force_status_update_calls = 0

    def force_status_update(self):
        self._force_status_update_calls += 1


class MockStorage(_Storage):

    def __init__(self):
        self._options = list()
        self.is_working = True

    @property
    def options(self):
        return list(self._options)

    def changeOption(self,
                     optionType: str,
                     optionValue: float,
                     logger: logging.Logger = None) -> bool:
        if not self.is_working:
            return False

        option = Option()
        option.type = optionType
        option.value = optionValue
        self._options.append(option)
        return True


class TestAlert(TestCase):

    def _create_option_executer(self) -> Tuple[OptionExecuter, GlobalData]:

        config_logging(logging.ERROR)

        global_data = GlobalData()
        global_data.logger = logging.getLogger("Option Test Case")
        global_data.storage = MockStorage()
        global_data.managerUpdateExecuter = MockManagerUpdateExecuter()

        option_executer = OptionExecuter(global_data)
        option_executer.daemon = True
        option_executer.start()

        return option_executer, global_data

    def test_base_option_handling(self):
        """
        Tests basic option handling without delay.
        """
        num = 5

        option_executer, global_data = self._create_option_executer()

        for i in range(num):
            option_executer.add_option("option_" + str(i),
                                       float(i),
                                       0)

        time.sleep(2)

        # Make sure manager update is only forced once.
        self.assertEqual(global_data.managerUpdateExecuter._force_status_update_calls, 1)

        self.assertFalse(option_executer._option_event.is_set())
        self.assertEqual(len(global_data.storage.options), num)

        for i in range(num):
            option = global_data.storage.options[i]
            self.assertEqual(option.type, "option_" + str(i))
            self.assertEqual(option.value, float(i))

    def test_option_handling_delay(self):
        """
        Tests option handling of an option with delay.
        """
        num = 5
        delay = 5

        option_executer, global_data = self._create_option_executer()

        for i in range(num):
            option_executer.add_option("option_" + str(i),
                                       float(i),
                                       delay)

        time.sleep(1)

        # Make sure options were not processed yet.
        self.assertEqual(global_data.managerUpdateExecuter._force_status_update_calls, 0)
        self.assertEqual(len(global_data.storage.options), 0)

        time.sleep(delay)

        # Make sure manager update is only forced once.
        self.assertEqual(global_data.managerUpdateExecuter._force_status_update_calls, 1)
        self.assertFalse(option_executer._option_event.is_set())

        for i in range(num):
            option = global_data.storage.options[i]
            self.assertEqual(option.type, "option_" + str(i))
            self.assertEqual(option.value, float(i))

    def test_option_handling_delay_abort(self):
        """
        Tests option handling of the same type if the second overwrites the first one if the first was delayed.
        """
        delay = 5

        option_executer, global_data = self._create_option_executer()

        option_executer.add_option("option",
                                   float(delay),
                                   delay)

        time.sleep(1)

        # Make sure options were not processed yet.
        self.assertEqual(global_data.managerUpdateExecuter._force_status_update_calls, 0)
        self.assertEqual(len(global_data.storage.options), 0)

        option_executer.add_option("option",
                                   float(0),
                                   0)

        time.sleep(1)

        # Make sure manager update is only forced once.
        self.assertEqual(global_data.managerUpdateExecuter._force_status_update_calls, 1)
        self.assertFalse(option_executer._option_event.is_set())

        self.assertEqual(len(global_data.storage.options), 1)
        option = global_data.storage.options[0]
        self.assertEqual(option.type, "option")
        self.assertEqual(option.value, float(0))

        time.sleep(delay)

        # Make sure only the option without delay was executed.
        self.assertEqual(len(global_data.storage.options), 1)
        option = global_data.storage.options[0]
        self.assertEqual(option.type, "option")
        self.assertEqual(option.value, float(0))

    def test_option_handling_storage_failure(self):
        """
        Tests option handling when the storage fails.
        """
        num = 5

        option_executer, global_data = self._create_option_executer()

        # Set storage to not work.
        global_data.storage.is_working = False

        for i in range(num):
            option_executer.add_option("option_" + str(i),
                                       float(i),
                                       0)

        time.sleep(1)

        # Make sure options were not processed yet.
        self.assertEqual(global_data.managerUpdateExecuter._force_status_update_calls, 0)
        self.assertEqual(len(global_data.storage.options), 0)

    def test_option_handling_profile(self):
        """
        Tests special handling of profile option.
        """
        raise NotImplementedError("TODO")