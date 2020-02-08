#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# this class represents a rule that triggeres when the current minute
# lies between the start and end
class RuleMinute:

    def __init__(self):

        # start minute of rule
        # (values: 0 - 59)
        self.start = None

        # end minute of rule
        # (values: 0 - 59)
        self.end = None

        # important: "end >= start"
