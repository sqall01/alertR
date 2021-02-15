from unittest import TestCase
from typing import List
from lib.localObjects import Option


def compare_options_content(context: TestCase, gt_options: List[Option], new_options: List[Option]):
    """
    Compares two lists of Option objects.
    :param context:
    :param gt_options:
    :param new_options:
    """
    if len(new_options) != len(gt_options):
        context.fail("Wrong number of objects.")

    already_processed = []
    for stored_option in new_options:
        found = False
        for gt_option in gt_options:
            if stored_option.type == gt_option.type:
                found = True

                # Check which objects we already processed to see if we hold an object with
                # duplicated values.
                if gt_option in already_processed:
                    context.fail("Duplicated object.")
                already_processed.append(gt_option)

                # Only the content of the object should have changed, not the object itself.
                if stored_option == gt_option:
                    context.fail("Changed ground truth object, not content of existing object.")

                if stored_option.value != gt_option.value:
                    context.fail("New object does not have correct content.")

                break

        if not found:
            context.fail("Not able to find modified Option object.")
