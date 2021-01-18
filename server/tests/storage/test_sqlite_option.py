import logging
from tests.util import config_logging
from tests.storage.sqlite_core import TestStorageCore
from tests.storage.util import compare_options_content
from lib.localObjects import Option


class TestStorageOption(TestStorageCore):

    def test_update_option(self):
        """
        Test Option object updating.
        """
        config_logging(logging.INFO)
        storage = self._create_options()

        # Create changes that should be copied to the stored object.
        new_options = []
        for i in range(len(self.options)):
            temp_option = Option().deepcopy(self.options[i])
            temp_option.value = float(i+5)
            new_options.append(temp_option)

        for i in range(len(new_options)):

            # Update store with new object data.
            temp_option = new_options[i]
            storage.update_option_by_obj(temp_option)

            gt_storage = []
            for j in range(i+1):
                gt_storage.append(new_options[j])
            for j in range(i+1, len(new_options)):
                gt_storage.append(self.options[j])

            stored_options = storage.get_options_list()
            self.assertIsNotNone(stored_options)

            compare_options_content(self, gt_storage, stored_options)

    def test_delete_option(self):
        """
        Test Option object deleting.
        """
        storage = self._create_options()

        for option in storage.get_options_list():

            storage.delete_option_by_type(option.type)

            for stored_option in storage.get_options_list():
                self.assertNotEqual(option.type, stored_option.type)
