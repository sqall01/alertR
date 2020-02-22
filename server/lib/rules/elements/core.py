#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.


# this class represents a rule element in the given rules of the alert level
# and has all meta information of the rule
class RuleElement:

    def __init__(self):

        # the type of the rule element
        # (values: sensor, boolean, weekday, monthday, hour, minute, second)
        self.type = None 

        # is the rule element triggered
        self.triggered = False

        # time when rule element triggered
        self.timeWhenTriggered = 0.0 

        # time how long this element counts as triggered
        self.timeTriggeredFor = 0.0 

        # the element of this rule element (for example a sensor rule)
        self.element = None


# this class represents the start of a rule and has all meta information that
# is needed for it
class RuleStart(RuleElement):

    def __init__(self):
        RuleElement.__init__(self)

        # the order of the rule in the chain in which the rules have to trigger
        self.order = None

        # the maximum amount of time that this rule has to trigger after
        # the previous rule has triggered in the chain (not used by the first
        # rule in the chain)
        self.maxTimeAfterPrev = None

        # the minimum amount of time that this rule has to trigger after
        # the previous rule has triggered in the chain (not used by the first
        # rule in the chain)
        self.minTimeAfterPrev = None

        # important: maxTimeAfterPrev >= minTimeAfterPrev

        # this flag is set when the counter of the rule is activated
        self.counterActivated = None

        # the list of timeWhenTriggered values for the counter
        # (only processed if counterActivated is set)
        self.counterList = list()

        # the max value/limit of the counter (when it is reached
        # the trigger is reset)
        # (only processed if counterActivated is set)
        self.counterLimit = 0

        # the time that has to be passed before a timeWhenTriggered is removed
        # from the counter
        # (only processed if counterActivated is set)
        self.counterWaitTime = 0
