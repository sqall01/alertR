#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# this class represents a boolean operator for the rule engine
class RuleBoolean:

    def __init__(self):

        # the type of boolean operator this element represents
        # (values: and, or, not)
        self.type = None

        # a list of rule elements this boolean operator contains
        # (important: "not" can only contain one element)
        self.elements = list()
