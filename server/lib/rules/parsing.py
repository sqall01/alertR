#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
from .elements import RuleStart, RuleElement, RuleBoolean, RuleSensor, RuleWeekday, RuleMonthday, RuleHour, RuleMinute,\
                      RuleSecond
from ..globalData import GlobalData
from ..localObjects import AlertLevel


# function is used to parse a rule of an alert level recursively
def parseRuleRecursively(currentRoot,
                         currentRule):

    if currentRoot.tag == "not":

        # get possible elements
        orItem = currentRoot.find("or")
        andItem = currentRoot.find("and")
        notItem = currentRoot.find("not")
        sensorItem = currentRoot.find("sensor")
        weekdayItem = currentRoot.find("weekday")
        monthdayItem = currentRoot.find("monthday")
        hourItem = currentRoot.find("hour")
        minuteItem = currentRoot.find("minute")
        secondItem = currentRoot.find("second")

        # check that only one tag is given in not tag
        # (because only one is allowed)
        counter = 0
        if orItem is not None:
            counter += 1
        if andItem is not None:
            counter += 1
        if notItem is not None:
            counter += 1
        if sensorItem is not None:
            counter += 1
        if weekdayItem is not None:
            counter += 1
        if monthdayItem is not None:
            counter += 1
        if hourItem is not None:
            counter += 1
        if minuteItem is not None:
            counter += 1
        if secondItem is not None:
            counter += 1
        if counter != 1:
            raise ValueError("Only one tag is valid inside a 'not' tag.")

        # start parsing the rule
        if orItem is not None:
            # create a new "or" rule
            ruleNew = RuleBoolean()
            ruleNew.type = "or"

            # create a wrapper element around the rule
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "boolean"
            ruleElement.element = ruleNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

            # parse rule starting from the new element
            parseRuleRecursively(orItem, ruleNew)

        elif andItem is not None:
            # create a new "and" rule
            ruleNew = RuleBoolean()
            ruleNew.type = "and"

            # create a wrapper element around the rule
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "boolean"
            ruleElement.element = ruleNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

            # parse rule starting from the new element
            parseRuleRecursively(andItem, ruleNew)

        elif notItem is not None:
            # create a new "not" rule
            ruleNew = RuleBoolean()
            ruleNew.type = "not"

            # create a wrapper element around the rule
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "boolean"
            ruleElement.element = ruleNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

            # parse rule starting from the new element
            parseRuleRecursively(notItem, ruleNew)

        elif sensorItem is not None:
            ruleSensorNew = RuleSensor()
            ruleSensorNew.username = str(sensorItem.attrib["username"])
            ruleSensorNew.remoteSensorId = int(sensorItem.attrib["remoteSensorId"])

            # create a wrapper element around the sensor element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "sensor"
            ruleElement.element = ruleSensorNew
            ruleElement.timeTriggeredFor = float(sensorItem.attrib["timeTriggeredFor"])

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        elif weekdayItem is not None:
            ruleWeekdayNew = RuleWeekday()

            # get time attribute and check if valid
            ruleWeekdayNew.time = str(weekdayItem.attrib["time"])
            if ruleWeekdayNew.time != "local" and ruleWeekdayNew.time != "utc":
                raise ValueError("No valid value for 'time' attribute in weekday tag.")

            # get weekday attribute and check if valid
            ruleWeekdayNew.weekday = int(weekdayItem.attrib["weekday"])
            if ruleWeekdayNew.weekday < 0 or ruleWeekdayNew.weekday > 6:
                raise ValueError("No valid value for 'weekday' attribute in weekday tag.")

            # create a wrapper element around the weekday element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "weekday"
            ruleElement.element = ruleWeekdayNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        elif monthdayItem is not None:
            ruleMonthdayNew = RuleMonthday()

            # get time attribute and check if valid
            ruleMonthdayNew.time = str(monthdayItem.attrib["time"])
            if ruleMonthdayNew.time != "local" and ruleMonthdayNew.time != "utc":
                raise ValueError("No valid value for 'time' attribute in monthday tag.")

            # get monthday attribute and check if valid
            ruleMonthdayNew.monthday = int(monthdayItem.attrib["monthday"])
            if ruleMonthdayNew.monthday < 1 or ruleMonthdayNew.monthday > 31:
                raise ValueError("No valid value for 'monthday' attribute in monthday tag.")

            # create a wrapper element around the monthday element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "monthday"
            ruleElement.element = ruleMonthdayNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        elif hourItem is not None:
            ruleHourNew = RuleHour()

            # get time attribute and check if valid
            ruleHourNew.time = str(hourItem.attrib["time"])
            if ruleHourNew.time != "local" and ruleHourNew.time != "utc":
                raise ValueError("No valid value for 'time' attribute in hour tag.")

            # get start attribute and check if valid
            ruleHourNew.start = int(hourItem.attrib["start"])
            if ruleHourNew.start < 0 or ruleHourNew.start > 23:
                raise ValueError("No valid value for 'start' attribute in hour tag.")

            # get end attribute and check if valid
            ruleHourNew.end = int(hourItem.attrib["end"])
            if ruleHourNew.start < 0 or ruleHourNew.start > 23:
                raise ValueError("No valid value for 'end' attribute in hour tag.")

            if ruleHourNew.start > ruleHourNew.end:
                raise ValueError("'start' attribute not allowed to be greater than 'end' attribute in hour tag.")

            # create a wrapper element around the hour element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "hour"
            ruleElement.element = ruleHourNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        elif minuteItem is not None:
            ruleMinuteNew = RuleMinute()

            # get start attribute and check if valid
            ruleMinuteNew.start = int(minuteItem.attrib["start"])
            if ruleMinuteNew.start < 0 or ruleMinuteNew.start > 59:
                raise ValueError("No valid value for 'start' attribute in minute tag.")

            # get end attribute and check if valid
            ruleMinuteNew.end = int(minuteItem.attrib["end"])
            if ruleMinuteNew.start < 0 or ruleMinuteNew.start > 59:
                raise ValueError("No valid value for 'end' attribute in minute tag.")

            if ruleMinuteNew.start > ruleMinuteNew.end:
                raise ValueError("'start' attribute not allowed to be greater than 'end' attribute in minute tag.")

            # create a wrapper element around the minute element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "minute"
            ruleElement.element = ruleMinuteNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        elif secondItem is not None:
            ruleSecondNew = RuleSecond()

            # get start attribute and check if valid
            ruleSecondNew.start = int(secondItem.attrib["start"])
            if ruleSecondNew.start < 0 or ruleSecondNew.start > 59:
                raise ValueError("No valid value for 'start' attribute in second tag.")

            # get end attribute and check if valid
            ruleSecondNew.end = int(secondItem.attrib["end"])
            if ruleSecondNew.start < 0 or ruleSecondNew.start > 59:
                raise ValueError("No valid value for 'end' attribute in second tag.")

            if ruleSecondNew.start > ruleSecondNew.end:
                raise ValueError("'start' attribute not allowed to be greater than 'end' attribute in second tag.")

            # create a wrapper element around the second element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "second"
            ruleElement.element = ruleSecondNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        else:
            raise ValueError("No valid tag was found.")

        # NOT is always an invalid rule (ignores all elements inside the
        # NOT element)
        return False

    elif currentRoot.tag == "and" or currentRoot.tag == "or":

        # set the current rule element to invald
        ruleValid = False

        # parse all "sensor" tags
        for item in currentRoot.iterfind("sensor"):
            ruleSensorNew = RuleSensor()
            ruleSensorNew.username = str(item.attrib["username"])
            ruleSensorNew.remoteSensorId = int(item.attrib["remoteSensorId"])

            # create a wrapper element around the sensor element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "sensor"
            ruleElement.element = ruleSensorNew
            ruleElement.timeTriggeredFor = float(item.attrib["timeTriggeredFor"])

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

            # a sensor element always sets the rule to a valid rule
            ruleValid = True

        # parse all "weekday" tags
        for item in currentRoot.iterfind("weekday"):
            ruleWeekdayNew = RuleWeekday()

            # get time attribute and check if valid
            ruleWeekdayNew.time = str(item.attrib["time"])
            if ruleWeekdayNew.time != "local" and ruleWeekdayNew.time != "utc":
                raise ValueError("No valid value for 'time' attribute in weekday tag.")

            # get weekday attribute and check if valid
            ruleWeekdayNew.weekday = int(item.attrib["weekday"])
            if ruleWeekdayNew.weekday < 0 or ruleWeekdayNew.weekday > 6:
                raise ValueError("No valid value for 'weekday' attribute in weekday tag.")

            # create a wrapper element around the weekday element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "weekday"
            ruleElement.element = ruleWeekdayNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        # parse all "monthday" tags
        for item in currentRoot.iterfind("monthday"):
            ruleMonthdayNew = RuleMonthday()

            # get time attribute and check if valid
            ruleMonthdayNew.time = str(item.attrib["time"])
            if ruleMonthdayNew.time != "local" and ruleMonthdayNew.time != "utc":
                raise ValueError("No valid value for 'time' attribute in monthday tag.")

            # get monthday attribute and check if valid
            ruleMonthdayNew.monthday = int(item.attrib["monthday"])
            if ruleMonthdayNew.monthday < 1 or ruleMonthdayNew.monthday > 31:
                raise ValueError("No valid value for 'monthday' attribute in monthday tag.")

            # create a wrapper element around the monthday element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "monthday"
            ruleElement.element = ruleMonthdayNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        # parse all "hour" tags
        for item in currentRoot.iterfind("hour"):
            ruleHourNew = RuleHour()

            # get time attribute and check if valid
            ruleHourNew.time = str(item.attrib["time"])
            if ruleHourNew.time != "local" and ruleHourNew.time != "utc":
                raise ValueError("No valid value for 'time' attribute in hour tag.")

            # get start attribute and check if valid
            ruleHourNew.start = int(item.attrib["start"])
            if ruleHourNew.start < 0 or ruleHourNew.start > 23:
                raise ValueError("No valid value for 'start' attribute in hour tag.")

            # get end attribute and check if valid
            ruleHourNew.end = int(item.attrib["end"])
            if ruleHourNew.start < 0 or ruleHourNew.start > 23:
                raise ValueError("No valid value for 'end' attribute in hour tag.")

            if ruleHourNew.start > ruleHourNew.end:
                raise ValueError("'start' attribute not allowed to be greater than 'end' attribute in hour tag.")

            # create a wrapper element around the hour element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "hour"
            ruleElement.element = ruleHourNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        # parse all "minute" tags
        for item in currentRoot.iterfind("minute"):
            ruleMinuteNew = RuleMinute()

            # get start attribute and check if valid
            ruleMinuteNew.start = int(item.attrib["start"])
            if ruleMinuteNew.start < 0 or ruleMinuteNew.start > 59:
                raise ValueError("No valid value for 'start' attribute in minute tag.")

            # get end attribute and check if valid
            ruleMinuteNew.end = int(item.attrib["end"])
            if ruleMinuteNew.start < 0 or ruleMinuteNew.start > 59:
                raise ValueError("No valid value for 'end' attribute in minute tag.")

            if ruleMinuteNew.start > ruleMinuteNew.end:
                raise ValueError("'start' attribute not allowed to be greater than 'end' attribute in minute tag.")

            # create a wrapper element around the minute element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "minute"
            ruleElement.element = ruleMinuteNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        # parse all "second" tags
        for item in currentRoot.iterfind("second"):
            ruleSecondNew = RuleSecond()

            # get start attribute and check if valid
            ruleSecondNew.start = int(item.attrib["start"])
            if ruleSecondNew.start < 0 or ruleSecondNew.start > 59:
                raise ValueError("No valid value for 'start' attribute in second tag.")

            # get end attribute and check if valid
            ruleSecondNew.end = int(item.attrib["end"])
            if ruleSecondNew.start < 0 or ruleSecondNew.start > 59:
                raise ValueError("No valid value for 'end' attribute in second tag.")

            if ruleSecondNew.start > ruleSecondNew.end:
                raise ValueError("'start' attribute not allowed to be greater than 'end' attribute in second tag.")

            # create a wrapper element around the second element
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "second"
            ruleElement.element = ruleSecondNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

        # parse all "and" tags
        for item in currentRoot.iterfind("and"):
            # create a new "and" rule
            ruleNew = RuleBoolean()
            ruleNew.type = "and"

            # create a wrapper element around the rule
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "boolean"
            ruleElement.element = ruleNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

            # parse rule starting from the new element
            tempValid = parseRuleRecursively(item, ruleNew)

            # only set the rule to the result of the recursively parsing
            # if it is not already valid
            if not ruleValid:
                ruleValid = tempValid

        # parse all "or" tags
        for item in currentRoot.iterfind("or"):
            # create a new "or" rule
            ruleNew = RuleBoolean()
            ruleNew.type = "or"

            # create a wrapper element around the rule
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "boolean"
            ruleElement.element = ruleNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

            # parse rule starting from the new element
            tempValid = parseRuleRecursively(item, ruleNew)

            # only set the rule to the result of the recursively parsing
            # if it is not already valid
            if not ruleValid:
                ruleValid = tempValid

        # parse all "not" tags
        for item in currentRoot.iterfind("not"):
            # create a new "not" rule
            ruleNew = RuleBoolean()
            ruleNew.type = "not"

            # create a wrapper element around the rule
            # to have meta information (i.e. triggered,
            # time when triggered, etc.)
            ruleElement = RuleElement()
            ruleElement.type = "boolean"
            ruleElement.element = ruleNew

            # add wrapper element to the current rule
            currentRule.elements.append(ruleElement)

            # parse rule starting from the new element
            parseRuleRecursively(item, ruleNew)

        # return if the current rule is valid
        return ruleValid

    else:
        raise ValueError("No valid tag found in rule.")


# function is used to write the parsed rules to the log file
def logRule(ruleElement,
            spaces,
            fileName):

    if isinstance(ruleElement, RuleStart):
        logString = ("RULE (order=%d, " % ruleElement.order
                     + "minTimeAfterPrev=%.2f, " % ruleElement.minTimeAfterPrev
                     + "maxTimeAfterPrev=%.2f, " % ruleElement.maxTimeAfterPrev
                     + "counterActivated=%s, " % str(ruleElement.counterActivated)
                     + "counterLimit=%d, " % ruleElement.counterLimit
                     + "counterWaitTime=%d)" % ruleElement.counterWaitTime)
        logging.info("[%s]: %s" % (fileName, logString))

    spaceString = ""
    for i in range(spaces):
        spaceString += "   "

    if ruleElement.type == "boolean":
        logString = "%s %s" % (spaceString, ruleElement.element.type)
        logging.info("[%s]: %s" % (fileName, logString))

        spaceString += "   "

        for item in ruleElement.element.elements:

            if item.type == "boolean":
                logRule(item, spaces+1, fileName)

            elif item.type == "sensor":
                logString = ("%s sensor " % spaceString
                             + "(triggeredFor=%.2f, " % item.timeTriggeredFor
                             + "user=%s, " % item.element.username
                             + "remoteId=%d)" % item.element.remoteSensorId)
                logging.info("[%s]: %s" % (fileName, logString))

            elif item.type == "weekday":
                logString = ("%s weekday " % spaceString
                             + "(time=%s, " % item.element.time
                             + "weekday=%d)" % item.element.weekday)
                logging.info("[%s]: %s" % (fileName, logString))

            elif item.type == "monthday":
                logString = ("%s monthday " % spaceString
                             + "(time=%s, " % item.element.time
                             + "monthday=%d)" % item.element.monthday)
                logging.info("[%s]: %s" % (fileName, logString))

            elif item.type == "hour":
                logString = ("%s hour " % spaceString
                             + "(time=%s, " % item.element.time
                             + "start=%d, " % item.element.start
                             + "end=%d)") % item.element.end
                logging.info("[%s]: %s" % (fileName, logString))

            elif item.type == "minute":
                logString = ("%s minute " % spaceString
                             + "(start=%d, " % item.element.start
                             + "end=%d)") % item.element.end
                logging.info("[%s]: %s" % (fileName, logString))

            elif item.type == "second":
                logString = ("%s second " % spaceString
                             + "(start=%d, " % item.element.start
                             + "end=%d)") % item.element.end
                logging.info("[%s]: %s" % (fileName, logString))

            else:
                raise ValueError("Rule has invalid type: '%s'." % ruleElement.type)

    elif ruleElement.type == "sensor":
        logString = ("%s sensor " % spaceString
                     + "(triggeredFor=%.2f, " % ruleElement.timeTriggeredFor
                     + "user=%s, " % ruleElement.element.username
                     + "remoteId=%d)" % ruleElement.element.remoteSensorId)
        logging.info("[%s]: %s" % (fileName, logString))

    elif ruleElement.type == "weekday":
        logString = ("%s weekday " % spaceString
                     + "(time=%s, " % ruleElement.element.time
                     + "weekday=%d)" % ruleElement.element.weekday)
        logging.info("[%s]: %s" % (fileName, logString))

    elif ruleElement.type == "monthday":
        logString = ("%s monthday " % spaceString
                     + "(time=%s, " % ruleElement.element.time
                     + "monthday=%d)" % ruleElement.element.monthday)
        logging.info("[%s]: %s" % (fileName, logString))

    elif ruleElement.type == "hour":
        logString = ("%s hour " % spaceString
                     + "(time=%s, " % ruleElement.element.time
                     + "start=%d, " % ruleElement.element.start
                     + "end=%d)") % ruleElement.element.end
        logging.info("[%s]: %s" % (fileName, logString))

    elif ruleElement.type == "minute":
        logString = ("%s minute " % spaceString
                     + "(start=%d, " % ruleElement.element.start
                     + "end=%d)") % ruleElement.element.end
        logging.info("[%s]: %s" % (fileName, logString))

    elif ruleElement.type == "second":
        logString = ("%s second " % spaceString
                     + "(start=%d, " % ruleElement.element.start
                     + "end=%d)") % ruleElement.element.end
        logging.info("[%s]: %s" % (fileName, logString))

    else:
        raise ValueError("Rule has invalid type: '%s'." % ruleElement.type)


def parse_rule(alertLevel: AlertLevel,
               globalData: GlobalData,
               item,
               fileName: str):

    # a list of flags that indicates if the rule is valid or
    # invalid when it is used alone => one of the rules have to
    # be valid in order for the rule chain to be valid
    # NOTE: the rule engine works event based, this means that
    # at least one sensor has to be in the rule chain that
    # is not negated by a NOT
    rulesValid = list()

    rulesRoot = item.find("rules")

    # parse all rule tags
    for firstRule in rulesRoot.iterfind("rule"):

        # get start of the rule
        orRule = firstRule.find("or")
        andRule = firstRule.find("and")
        notRule = firstRule.find("not")
        sensorRule = firstRule.find("sensor")
        weekdayRule = firstRule.find("weekday")
        monthdayRule = firstRule.find("monthday")
        hourRule = firstRule.find("hour")
        minuteRule = firstRule.find("minute")
        secondRule = firstRule.find("second")

        # check that only one tag is given in rule
        counter = 0
        if orRule is not None:
            counter += 1
        if andRule is not None:
            counter += 1
        if notRule is not None:
            counter += 1
        if sensorRule is not None:
            counter += 1
        if weekdayRule is not None:
            counter += 1
        if monthdayRule is not None:
            counter += 1
        if hourRule is not None:
            counter += 1
        if minuteRule is not None:
            counter += 1
        if secondRule is not None:
            counter += 1
        if counter != 1:
            raise ValueError("Only one tag is valid as starting part of the rule.")

        # create a wrapper element around the rule element
        # to have meta information (i.e. triggered,
        # time when triggered, etc.)
        ruleElement = RuleStart()

        # get order attribute
        ruleElement.order = int(firstRule.attrib["order"])

        # get minTimeAfterPrev attribute
        ruleElement.minTimeAfterPrev = float(firstRule.attrib["minTimeAfterPrev"])

        # get maxTimeAfterPrev attribute
        ruleElement.maxTimeAfterPrev = float(firstRule.attrib["maxTimeAfterPrev"])

        if ruleElement.minTimeAfterPrev > ruleElement.maxTimeAfterPrev:
            raise ValueError("'minTimeAfterPrev' attribute not allowed to be greater than "
                             + "'maxTimeAfterPrev' attribute in rule tag.")

        # get counterActivated attribute
        ruleElement.counterActivated = (str(firstRule.attrib["counterActivated"]).upper() == "TRUE")

        # only parse counter attributes if it is activated
        if ruleElement.counterActivated:

            # get counterLimit attribute
            ruleElement.counterLimit = int(firstRule.attrib["counterLimit"])

            if ruleElement.counterLimit < 0:
                raise ValueError("'counterLimit' attribute not allowed to be smaller than 0.")

            # get counterWaitTime attribute
            ruleElement.counterWaitTime = int(firstRule.attrib["counterWaitTime"])

            if ruleElement.counterWaitTime < 0:
                raise ValueError("'counterWaitTime' attribute not allowed to be smaller than 0.")

        # start parsing the rule
        if orRule is not None:
            ruleStart = RuleBoolean()
            ruleStart.type = "or"

            # fill wrapper element
            ruleElement.type = "boolean"
            ruleElement.element = ruleStart

            ruleValid = parseRuleRecursively(orRule, ruleStart)

            # flag current rule as valid/invalid
            rulesValid.append(ruleValid)

        elif andRule is not None:
            ruleStart = RuleBoolean()
            ruleStart.type = "and"

            # fill wrapper element
            ruleElement.type = "boolean"
            ruleElement.element = ruleStart

            ruleValid = parseRuleRecursively(andRule, ruleStart)

            # flag current rule as valid/invalid
            rulesValid.append(ruleValid)

        elif notRule is not None:
            ruleStart = RuleBoolean()
            ruleStart.type = "not"

            # fill wrapper element
            ruleElement.type = "boolean"
            ruleElement.element = ruleStart

            parseRuleRecursively(notRule, ruleStart)

            # flag current rule as invalid
            rulesValid.append(False)

        elif sensorRule is not None:
            ruleSensorNew = RuleSensor()
            ruleSensorNew.username = str(sensorRule.attrib["username"])
            ruleSensorNew.remoteSensorId = int(sensorRule.attrib["remoteSensorId"])

            # fill wrapper element
            ruleElement.type = "sensor"
            ruleElement.element = ruleSensorNew
            ruleElement.timeTriggeredFor = float(sensorRule.attrib["timeTriggeredFor"])

            # flag current rule as valid
            rulesValid.append(True)

        elif weekdayRule is not None:
            ruleWeekdayNew = RuleWeekday()

            # get time attribute and check if valid
            ruleWeekdayNew.time = str(weekdayRule.attrib["time"])
            if ruleWeekdayNew.time != "local" and ruleWeekdayNew.time != "utc":
                raise ValueError("No valid value for 'time' attribute in weekday tag.")

            # get weekday attribute and check if valid
            ruleWeekdayNew.weekday = int(weekdayRule.attrib["weekday"])
            if ruleWeekdayNew.weekday < 0 or ruleWeekdayNew.weekday > 6:
                raise ValueError("No valid value for 'weekday' attribute in weekday tag.")

            # fill wrapper element
            ruleElement.type = "weekday"
            ruleElement.element = ruleWeekdayNew

            # flag current rule as invalid
            rulesValid.append(False)

        elif monthdayRule is not None:
            ruleMonthdayNew = RuleMonthday()

            # get time attribute and check if valid
            ruleMonthdayNew.time = str(monthdayRule.attrib["time"])
            if ruleMonthdayNew.time != "local" and ruleMonthdayNew.time != "utc":
                raise ValueError("No valid value for 'time' attribute in monthday tag.")

            # get monthday attribute and check if valid
            ruleMonthdayNew.monthday = int(monthdayRule.attrib[
                "monthday"])
            if ruleMonthdayNew.monthday < 1 or ruleMonthdayNew.monthday > 31:
                raise ValueError("No valid value for 'monthday' attribute in monthday tag.")

            # fill wrapper element
            ruleElement.type = "monthday"
            ruleElement.element = ruleMonthdayNew

            # flag current rule as invalid
            rulesValid.append(False)

        elif hourRule is not None:
            ruleHourNew = RuleHour()

            # get time attribute and check if valid
            ruleHourNew.time = str(hourRule.attrib["time"])
            if ruleHourNew.time != "local" and ruleHourNew.time != "utc":
                raise ValueError("No valid value for 'time' attribute in hour tag.")

            # get start attribute and check if valid
            ruleHourNew.start = int(hourRule.attrib["start"])
            if ruleHourNew.start < 0 or ruleHourNew.start > 23:
                raise ValueError("No valid value for 'start' attribute in hour tag.")

            # get end attribute and check if valid
            ruleHourNew.end = int(hourRule.attrib["end"])
            if ruleHourNew.start < 0 or ruleHourNew.start > 23:
                raise ValueError("No valid value for 'end' attribute in hour tag.")

            if ruleHourNew.start > ruleHourNew.end:
                raise ValueError("'start' attribute not allowed to be greater than 'end' attribute in "
                                 + "hour tag.")

            # fill wrapper element
            ruleElement.type = "hour"
            ruleElement.element = ruleHourNew

            # flag current rule as invalid
            rulesValid.append(False)

        elif minuteRule is not None:
            ruleMinuteNew = RuleMinute()

            # get start attribute and check if valid
            ruleMinuteNew.start = int(minuteRule.attrib["start"])
            if ruleMinuteNew.start < 0 or ruleMinuteNew.start > 59:
                raise ValueError("No valid value for 'start' attribute in minute tag.")

            # get end attribute and check if valid
            ruleMinuteNew.end = int(minuteRule.attrib["end"])
            if ruleMinuteNew.start < 0 or ruleMinuteNew.start > 59:
                raise ValueError("No valid value for 'end' attribute in minute tag.")

            if ruleMinuteNew.start > ruleMinuteNew.end:
                raise ValueError("'start' attribute not allowed to be greater than 'end' attribute in "
                                 + "minute tag.")

            # fill wrapper element
            ruleElement.type = "minute"
            ruleElement.element = ruleMinuteNew

            # flag current rule as invalid
            rulesValid.append(False)

        elif secondRule is not None:
            ruleSecondNew = RuleSecond()

            # get start attribute and check if valid
            ruleSecondNew.start = int(secondRule.attrib["start"])
            if ruleSecondNew.start < 0 or ruleSecondNew.start > 59:
                raise ValueError("No valid value for 'start' attribute in second tag.")

            # get end attribute and check if valid
            ruleSecondNew.end = int(secondRule.attrib["end"])
            if ruleSecondNew.start < 0 or ruleSecondNew.start > 59:
                raise ValueError("No valid value for 'end' attribute in second tag.")

            if ruleSecondNew.start > ruleSecondNew.end:
                raise ValueError("'start' attribute not allowed to be greater than 'end' attribute in "
                                 + "second tag.")

            # fill wrapper element
            ruleElement.type = "second"
            ruleElement.element = ruleSecondNew

            # flag current rule as invalid
            rulesValid.append(False)

        else:
            raise ValueError("No valid tag was found.")

        # check if order of all rules only exists once
        for existingRule in alertLevel.rules:
            if existingRule.order == ruleElement.order:
                raise ValueError("Order of rule must be unique.")

        alertLevel.rules.append(ruleElement)

    # check if any of the rules in this rule chain is valid
    # => if not the rule chain is not valid
    if not any(rulesValid):
        raise ValueError("Rule chain for alert level '%d' is not valid." % alertLevel.level)

    # sort rules by order
    alertLevel.rules.sort(key=lambda x: x.order)

    # check if parsed rules should be logged
    if globalData.loglevel == logging.INFO or globalData.loglevel == logging.DEBUG:
        globalData.logger.info("[%s]: Parsed rules for alert level %d."
                               % (fileName, alertLevel.level))

        for ruleElement in alertLevel.rules:
            logRule(ruleElement, 0, fileName)
