#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# this class represents a rule that triggeres when the current day of the week
# matches with the configured one
class RuleWeekday:

    def __init__(self):

        # the used timezone for the calculation
        # (possible values: local or utc)
        self.time = None

        # the day of the week
        # (values: 0 - 6 (0: Monday, ..., 6: Sunday))
        self.weekday = None
