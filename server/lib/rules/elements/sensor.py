#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# this class represents a rule that triggeres when the triggered sensor
# matches with the configured one
class RuleSensor:

    def __init__(self):

        # username of the node that handles the sensor
        self.username = None

        # the id that is configured for the sensor on the client side
        self.remoteSensorId = None
