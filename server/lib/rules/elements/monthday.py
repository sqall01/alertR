#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# this class represents a rule that triggeres when the current day of the month
# matches with the configured one
class RuleMonthday:

    def __init__(self):

        # the used timezone for the calculation
        # (possible values: local or utc)
        self.time = None

        # the day of the month
        # (values: 1 - 31)
        self.monthday = None
