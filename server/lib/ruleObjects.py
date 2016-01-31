#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.


# this class represents a rule that triggeres when the current second
# lies between the start and end
class RuleSecond:

	def __init__(self):

		def __init__(self):

			# start second of rule
			# (values: 0 - 59)
			self.start = None

			# end second of rule
			# (values: 0 - 59)
			self.end = None

			# important: "end >= start"


# this class represents a rule that triggeres when the current minute
# lies between the start and end
class RuleMinute:

	def __init__(self):

		def __init__(self):

			# start minute of rule
			# (values: 0 - 59)
			self.start = None

			# end minute of rule
			# (values: 0 - 59)
			self.end = None

			# important: "end >= start"


# this class represents a rule that triggeres when the current hour
# lies between the start and end
class RuleHour:

	def __init__(self):

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


# this class represents a rule that triggeres when the current day of the month
# matches with the configured one
class RuleMonthday:

	def __init__(self):

		def __init__(self):

			# the used timezone for the calculation
			# (possible values: local or utc)
			self.time = None

			# the day of the month
			# (values: 1 - 31)
			self.monthday = None


# this class represents a rule that triggeres when the current day of the week
# matches with the configured one
class RuleWeekday:

	def __init__(self):

		def __init__(self):

			# the used timezone for the calculation
			# (possible values: local or utc)
			self.time = None

			# the day of the week
			# (values: 0 - 6 (0: Monday, ..., 6: Sunday))
			self.weekday = None


# this class represents a rule that triggeres when the triggered sensor
# matches with the configured one
class RuleSensor:

	def __init__(self):

		def __init__(self):

			# username of the node that handles the sensor
			self.username = None

			# the id that is configured for the sensor on the client side
			self.remoteSensorId = None


# this class represents a boolean operator for the rule engine
class RuleBoolean:

	def __init__(self):

		# the type of boolean operator this element represents
		# (values: and, or, not)
		self.type = None

		# a list of rule elements this boolean operator contains
		# (important: "not" can only contain one element)
		self.elements = list()


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