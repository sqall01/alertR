#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.


# this class represents a single alert level that is configured
class AlertLevel:

	def __init__(self):

		# this value indicates the alert level
		self.level = None

		# gives the name of this alert level
		self.name = None

		# this flag indicates if a sensor alert with this alert level
		# should trigger regardless of if the alert system is active or not
		self.triggerAlways = None

		# this flag tells if the alert level should trigger a sensor alert
		# if the sensor goes to state "triggered"
		self.triggerAlertTriggered = None

		# this flag tells if the alert level should also trigger a sensor alert
		# if the sensor goes to state "normal"
		self.triggerAlertNormal = None

		# this flag tells if the alert level has rules activated
		# that has to match before an alert is triggered (flag: True) or
		# if it just triggers when a sensor alert is received (flag: False)
		self.rulesActivated = None

		# a list of rules (rule chain) that have to evaluate before the
		# alert level triggers a sensor alert
		# (the order in which the elements are stored in this list is the
		# order in which the rules have to evaluate)
		self.rules = list()