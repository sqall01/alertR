from tests.globalData.core import TestSystemDataCore
from lib.localObjects import Option


class TestSystemDataOption(TestSystemDataCore):

    def test_update_option(self):
        """
        Test Option object updating.
        """
        system_data = self._create_options()

        # Create changes that should be copied to the stored object.
        new_options = []
        for i in range(len(self.options)):
            temp_option = Option().deepCopy(self.options[i])
            temp_option.value = float(i+5)
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
            if len(stored_options) != len(gt_storage):
                self.fail("Wrong number of objects stored.")

            already_processed = []
            for stored_option in stored_options:
                found = False
                for gt_option in gt_storage:
                    if stored_option.type == gt_option.type:
                        found = True

                        # Check which objects we already processed to see if we hold an object with
                        # duplicated values.
                        if gt_option in already_processed:
                            self.fail()
                        already_processed.append(gt_option)

                        # Only the content of the object should have changed, not the object itself.
                        if stored_option == gt_option:
                            self.fail("Store changed object, not content of existing object.")

                        if stored_option.value != gt_option.value:
                            self.fail("Stored object does not have correct content.")

                        break

                if not found:
                    self.fail("Not able to find modified Option object.")

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
