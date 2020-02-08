#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# this class represents a rule that triggeres when the current hour
# lies between the start and end
class RuleHour:

    def __init__(self):

        # the used timezone for the calculation
        # (possible values: local or utc)
        self.time = None

        # start hour of rule
        # (values: 0 - 23)
        self.start = None

        # end hour of rule
        # (values: 0 - 23)
        self.end = None

        # important: "end >= start"
