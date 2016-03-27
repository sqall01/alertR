#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

# This enum class gives the different data types of a sensor.
class SensorDataType:
	NONE = 0
	INT = 1
	FLOAT = 2


# This enum class gives the different orderings used to check if the data of a
# sensor exceeds a threshold.
class Ordering:
	LT = 0
	EQ = 1
	GT = 2