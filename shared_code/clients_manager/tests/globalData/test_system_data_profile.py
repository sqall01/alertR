from tests.globalData.core import TestSystemDataCore
from tests.globalData.util import compare_profiles_content
from collections import defaultdict
from lib.globalData.managerObjects import ManagerObjProfile


class TestSystemDataProfile(TestSystemDataCore):

    def test_update_profile(self):
        """
        Test Profile object updating.
        """
        system_data = self._create_profiles()

        # Create changes that should be copied to the stored object.
        new_profiles = []
        for i in range(len(self.profiles)):
            temp_profile = ManagerObjProfile.deepcopy(self.profiles[i])
            temp_profile.name += "_new"
            new_profiles.append(temp_profile)

        for i in range(len(new_profiles)):

            # Update store with new object data.
            temp_profile = new_profiles[i]
            system_data.update_profile(temp_profile)

            gt_storage = []
            for j in range(i+1):
                gt_storage.append(new_profiles[j])
            for j in range(i+1, len(new_profiles)):
                gt_storage.append(self.profiles[j])

            stored_profiles = system_data.get_profiles_list()
            compare_profiles_content(self, gt_storage, stored_profiles)

    def test_delete_profile(self):
        """
        Test Profile object deleting.
        """
        system_data = self._create_alert_levels()

        # Create a mapping from profiles to alert levels.
        profile_alert_level_map = defaultdict(set)
        for profile in system_data.get_profiles_list():
            for alert_level in system_data.get_alert_levels_list():
                if profile.profileId in alert_level.profiles:
                    profile_alert_level_map[profile.profileId].add(alert_level.level)
        self.assertNotEqual(len(profile_alert_level_map.keys()), 0)

        for profile in system_data.get_profiles_list():

            system_data.delete_profile_by_id(profile.profileId)

            if not profile.is_deleted():
                self.fail("Profile object not marked as deleted.")

            for stored_profile in system_data.get_profiles_list():
                if stored_profile.is_deleted():
                    self.fail("Stored Option object marked as deleted.")

                if profile.profileId == stored_profile.profileId:
                    self.fail("Store still contains Option with type that was deleted.")

            # Make sure that either the Profile was removed from the Alert Level or the Alert Level was deleted.
            for alert_level in profile_alert_level_map[profile.profileId]:
                alert_level_obj = system_data.get_alert_level_by_level(alert_level)
                if alert_level_obj is not None:
                    self.assertFalse(profile.profileId in alert_level_obj.profiles)
