from tests.globalData.core import TestSystemDataCore
from tests.globalData.util import compare_options_content
from lib.globalData.managerObjects import ManagerObjOption


class TestSystemDataOption(TestSystemDataCore):

    def test_update_option(self):
        """
        Test Option object updating.
        """
        system_data = self._create_options()

        # Create changes that should be copied to the stored object.
        new_options = []
        for i in range(len(self.options)):
            temp_option = ManagerObjOption().deepcopy_to_obj(self.options[i])
            temp_option.value = i+5
            new_options.append(temp_option)

        for i in range(len(new_options)):

            # Update store with new object data.
            temp_option = new_options[i]
            system_data.update_option(temp_option)

            gt_storage = []
            for j in range(i+1):
                gt_storage.append(new_options[j])
            for j in range(i+1, len(new_options)):
                gt_storage.append(self.options[j])

            stored_options = system_data.get_options_list()
            compare_options_content(self, gt_storage, stored_options)

    def test_delete_option(self):
        """
        Test Option object deleting.
        """
        system_data = self._create_options()

        for option in system_data.get_options_list():

            system_data.delete_option_by_type(option.type)

            if not option.is_deleted():
                self.fail("Option object not marked as deleted.")

            for stored_option in system_data.get_options_list():
                if stored_option.is_deleted():
                    self.fail("Stored Option object marked as deleted.")

                if option.type == stored_option.type:
                    self.fail("Store still contains Option with type that was deleted.")
