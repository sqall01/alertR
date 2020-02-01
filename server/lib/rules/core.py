#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import time
from typing import List, Tuple
from ..globalData import GlobalData
from ..localObjects import SensorAlert, AlertLevel, SensorDataType
from ..server import AsynchronousSender
from .elements import RuleElement

'''
TODO
This is old code of the rule engine which worked when I was using it. It is really really terrible with lots of
old confusing data structures. It needs a complete rewrite. However, I do not use it currently.
Hence, I have no incentive to refactor this code at the moment.
'''


class RuleEngine:

    def __init__(self,
                 globalData: GlobalData):

        # get global configured data
        self.globalData = globalData
        self.logger = self.globalData.logger
        self.serverSessions = self.globalData.serverSessions
        self.storage = self.globalData.storage

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        # Structure: [ list(sensorAlerts), possible triggered alertLevel ]
        self.sensorAlertsToHandleWithRules = list()

    def _updateRuleValuesRecursively(self,
                                     sensorAlertList: List[Tuple[int, int, int, int, int, int, str]],
                                     currentRuleElement: RuleElement) -> bool:
        """
        this internal function recursively updates all values of
        the rule elements it processes received sensor alerts,
        updates the timeWhenTriggered values and sets the rule elements
        to triggered or not triggered respectively

        :param sensorAlertList:
        :param currentRuleElement:
        :return:
        """
        # check if rule element is of type "sensor"
        # => update values of rule
        if currentRuleElement.type == "sensor":

            # get node id of sensor client
            ruleNodeId = self.storage.getNodeId(currentRuleElement.element.username)
            if ruleNodeId is None:
                self.logger.error("[%s]: Not able to get node id for sensor to update rule." % self.fileName)
                return False

            # get sensor id of sensor
            ruleSensorId = self.storage.getSensorId(ruleNodeId, currentRuleElement.element.remoteSensorId)
            if ruleSensorId is None:
                self.logger.error("[%s]: Not able to get sensor id for sensor to update rule." % self.fileName)
                return False

            # update sensor rule element (set as not triggered)
            # if sensor does not count as triggered
            # => unset triggered flag
            utcTimestamp = int(time.time())
            if ((currentRuleElement.timeWhenTriggered + currentRuleElement.timeTriggeredFor) < utcTimestamp
               and currentRuleElement.triggered):
                self.logger.debug("[%s]: Sensor with id '%d' does not count as triggered anymore."
                                  % (self.fileName, ruleSensorId))
                currentRuleElement.triggered = False

            # update sensor rule values with current sensor alerts
            for sensorAlert in sensorAlertList:
                sensorAlertNodeId = sensorAlert[2]
                sensorAlertSensorId = sensorAlert[1]
                sensorAlertTimeReceived = sensorAlert[3]
                sensorAlertAlertDelay = sensorAlert[4]

                # check if received sensor alert is triggered by
                # the sensor of the rule
                if sensorAlertNodeId == ruleNodeId and sensorAlertSensorId == ruleSensorId:
                    self.logger.debug("[%s]: Found match for sensor with id '%d' and sensor in rule."
                                      % (self.fileName, ruleSensorId))

                    # checked if the received sensor alert
                    # is newer than the stored time when triggered
                    # => update time when triggered
                    if (sensorAlertTimeReceived + sensorAlertAlertDelay) > currentRuleElement.timeWhenTriggered:

                        # check if an alert delay has to be considered
                        utcTimestamp = int(time.time())
                        if not (utcTimestamp - sensorAlertTimeReceived) > sensorAlertAlertDelay:
                            self.logger.debug("[%s]: Sensor alert for sensor with id '%d' still delayed for "
                                              % (self.fileName, ruleSensorId)
                                              + "'%d' seconds."
                                              % (sensorAlertAlertDelay - (utcTimestamp - sensorAlertTimeReceived)))
                            continue

                        self.logger.debug("[%s]: New sensor alert for sensor with id '%d' received."
                                          % (self.fileName, ruleSensorId))

                        currentRuleElement.timeWhenTriggered = sensorAlertTimeReceived + sensorAlertAlertDelay

                        # check if sensor still counts as triggered
                        # => set triggered flag
                        if (currentRuleElement.timeWhenTriggered + currentRuleElement.timeTriggeredFor) > utcTimestamp:
                            self.logger.debug("[%s]: Sensor with id '%d' counts as triggered."
                                              % (self.fileName, ruleSensorId))
                            currentRuleElement.triggered = True

                        # if sensor does not count as triggered
                        # => unset triggered flag
                        else:
                            self.logger.debug("[%s]: Sensor with id '%d' does not count as triggered."
                                              % (self.fileName, ruleSensorId))
                            currentRuleElement.triggered = False

        # check if rule element is of type "weekday"
        # => update values of rule according to the date
        elif currentRuleElement.type == "weekday":

            weekdayElement = currentRuleElement.element

            if weekdayElement.time == "local":

                # check if week day matches
                # => set rule element as triggered if it is not yet triggered
                if weekdayElement.weekday == time.localtime().tm_wday:

                    # check if rule element is not triggered
                    # => set as triggered
                    if not currentRuleElement.triggered:
                        self.logger.debug("[%s]: Week day with value '%d' for '%s' counts as triggered."
                                          % (self.fileName, weekdayElement.weekday, weekdayElement.time))
                        utcTimestamp = int(time.time())
                        currentRuleElement.timeWhenTriggered = utcTimestamp
                        currentRuleElement.triggered = True

                # check if rule element is triggered
                # => set rule element as not triggered
                elif currentRuleElement.triggered:
                    self.logger.debug("[%s]: Week day with value '%d' for '%s' no longer counts as triggered."
                                      % (self.fileName, weekdayElement.weekday, weekdayElement.time))
                    currentRuleElement.triggered = False

            elif weekdayElement.time == "utc":

                # check if week day matches
                # => set rule element as triggered if it is not yet triggered
                if weekdayElement.weekday == time.gmtime().tm_wday:

                    # check if rule element is not triggered
                    # => set as triggered
                    if not currentRuleElement.triggered:
                        self.logger.debug("[%s]: Week day with value '%d' for '%s' counts as triggered."
                                          % (self.fileName, weekdayElement.weekday, weekdayElement.time))
                        utcTimestamp = int(time.time())
                        currentRuleElement.timeWhenTriggered = utcTimestamp
                        currentRuleElement.triggered = True

                # check if rule element is triggered
                # => set rule element as not triggered
                elif currentRuleElement.triggered:
                    self.logger.debug("[%s]: Week day with value '%d' for '%s' no longer counts as triggered."
                                      % (self.fileName, weekdayElement.weekday, weekdayElement.time))
                    currentRuleElement.triggered = False

            else:
                self.logger.error("[%s]: No valid value for 'time' attribute in weekday tag." % self.fileName)
                return False

        # check if rule element is of type "monthday"
        # => update values of rule according to the date
        elif currentRuleElement.type == "monthday":

            monthdayElement = currentRuleElement.element

            if monthdayElement.time == "local":

                # check if month day matches
                # => set rule element as triggered if it is not yet triggered
                if monthdayElement.monthday == time.localtime().tm_mday:

                    # check if rule element is not triggered
                    # => set as triggered
                    if not currentRuleElement.triggered:
                        self.logger.debug("[%s]: Month day with value '%d' for '%s' counts as triggered."
                                          % (self.fileName, monthdayElement.monthday, monthdayElement.time))
                        utcTimestamp = int(time.time())
                        currentRuleElement.timeWhenTriggered = utcTimestamp
                        currentRuleElement.triggered = True

                # check if rule element is triggered
                # => set rule element as not triggered
                elif currentRuleElement.triggered:
                    self.logger.debug("[%s]: Month day with value '%d' for '%s' no longer counts as triggered."
                                      % (self.fileName, monthdayElement.monthday, monthdayElement.time))
                    currentRuleElement.triggered = False

            elif monthdayElement.time == "utc":

                # check if month day matches
                # => set rule element as triggered if it is not yet triggered
                if monthdayElement.monthday == time.gmtime().tm_mday:

                    # check if rule element is not triggered
                    # => set as triggered
                    if not currentRuleElement.triggered:
                        self.logger.debug("[%s]: Month day with value '%d' for '%s' counts as triggered."
                                          % (self.fileName, monthdayElement.monthday, monthdayElement.time))
                        utcTimestamp = int(time.time())
                        currentRuleElement.timeWhenTriggered = utcTimestamp
                        currentRuleElement.triggered = True

                # check if rule element is triggered
                # => set rule element as not triggered
                elif currentRuleElement.triggered:
                    self.logger.debug("[%s]: Month day with value '%d' for '%s' no longer counts as triggered."
                                      % (self.fileName, monthdayElement.monthday, monthdayElement.time))
                    currentRuleElement.triggered = False

            else:
                self.logger.error("[%s]: No valid value for 'time' attribute in monthday tag." % self.fileName)
                return False

        # check if rule element is of type "hour"
        # => update values of rule according to the date
        elif currentRuleElement.type == "hour":

            hourElement = currentRuleElement.element

            if hourElement.time == "local":

                # check if the current hour lies between the start/end
                # of the hour rule element
                # => set rule element as triggered if it is not yet triggered
                if hourElement.start <= time.localtime().tm_hour <= hourElement.end:

                    # check if rule element is not triggered
                    # => set as triggered
                    if not currentRuleElement.triggered:
                        self.logger.debug("[%s]: Hour from '%d' to '%d' for '%s' counts as triggered."
                                          % (self.fileName, hourElement.start, hourElement.end, hourElement.time))
                        utcTimestamp = int(time.time())
                        currentRuleElement.timeWhenTriggered = utcTimestamp
                        currentRuleElement.triggered = True

                # check if rule element is triggered
                # => set rule element as not triggered
                elif currentRuleElement.triggered:
                    self.logger.debug("[%s]: Hour from '%d' to '%d' for '%s' no longer counts as triggered."
                                      % (self.fileName, hourElement.start, hourElement.end, hourElement.time))
                    currentRuleElement.triggered = False

            elif hourElement.time == "utc":

                # check if the current hour lies between the start/end
                # of the hour rule element
                # => set rule element as triggered if it is not yet triggered
                if hourElement.start <= time.gmtime().tm_hour <= hourElement.end:

                    # check if rule element is not triggered
                    # => set as triggered
                    if not currentRuleElement.triggered:
                        self.logger.debug("[%s]: Hour from '%d' to '%d' for '%s' counts as triggered."
                                          % (self.fileName, hourElement.start, hourElement.end, hourElement.time))
                        utcTimestamp = int(time.time())
                        currentRuleElement.timeWhenTriggered = utcTimestamp
                        currentRuleElement.triggered = True

                # check if rule element is triggered
                # => set rule element as not triggered
                elif currentRuleElement.triggered:
                    self.logger.debug("[%s]: Hour from '%d' to '%d' for '%s' no longer counts as triggered."
                                      % (self.fileName, hourElement.start, hourElement.end, hourElement.time))
                    currentRuleElement.triggered = False

            else:
                self.logger.error("[%s]: No valid value for 'time' attribute in hour tag." % self.fileName)
                return False

        # check if rule element is of type "minute"
        # => update values of rule according to the date
        elif currentRuleElement.type == "minute":

            minuteElement = currentRuleElement.element

            # check if the current minute lies between the start/end
            # of the minute rule element
            # => set rule element as triggered if it is not yet triggered
            if minuteElement.start <= time.localtime().tm_min <= minuteElement.end:

                # check if rule element is not triggered
                # => set as triggered
                if not currentRuleElement.triggered:
                    self.logger.debug("[%s]: Minute from '%d' to '%d' counts as triggered."
                                      % (self.fileName, minuteElement.start, minuteElement.end))
                    utcTimestamp = int(time.time())
                    currentRuleElement.timeWhenTriggered = utcTimestamp
                    currentRuleElement.triggered = True

            # check if rule element is triggered
            # => set rule element as not triggered
            elif currentRuleElement.triggered:
                self.logger.debug("[%s]: Minute from '%d' to '%d' no longer counts as triggered."
                                  % (self.fileName, minuteElement.start, minuteElement.end))
                currentRuleElement.triggered = False

        # check if rule element is of type "second"
        # => update values of rule according to the date
        elif currentRuleElement.type == "second":

            secondElement = currentRuleElement.element

            # check if the current second lies between the start/end
            # of the second rule element
            # => set rule element as triggered if it is not yet triggered
            if secondElement.start <= time.localtime().tm_sec <= secondElement.end:

                # check if rule element is not triggered
                # => set as triggered
                if not currentRuleElement.triggered:
                    self.logger.debug("[%s]: Second from '%d' to '%d' counts as triggered."
                                      % (self.fileName, secondElement.start, secondElement.end))
                    utcTimestamp = int(time.time())
                    currentRuleElement.timeWhenTriggered = utcTimestamp
                    currentRuleElement.triggered = True

            # check if rule element is triggered
            # => set rule element as not triggered
            elif currentRuleElement.triggered:
                self.logger.debug("[%s]: Second from '%d' to '%d' no longer counts as triggered."
                                  % (self.fileName, secondElement.start, secondElement.end))
                currentRuleElement.triggered = False

        # check if rule element is of type "boolean"
        # => traverse rule recursively
        elif currentRuleElement.type == "boolean":

            # update values of all rule elements in current rule element
            for ruleElement in currentRuleElement.element.elements:
                self._updateRuleValuesRecursively(sensorAlertList, ruleElement)

        else:
            self.logger.error("[%s]: Rule element has an invalid type." % self.fileName)
            return False

        return True

    def _evaluateRuleElementsRecursively(self,
                                         currentRuleElement: RuleElement) -> bool:
        """
        this internal function evaluates rule elements from type
        "boolean" recursively
        (means AND, OR and NOT are evaluated as triggered/not triggered)

        :param currentRuleElement:
        :return:
        """
        # only evaluate rule elements of type "boolean"
        if currentRuleElement.type == "boolean":

            # evaluate "and" rule element
            if currentRuleElement.element.type == "and":

                andElement = currentRuleElement.element

                # check if all elements of the "and" rule element are triggered
                for element in andElement.elements:

                    # check if sensor element is not triggered
                    # => if it is, set current rule element also as
                    # not triggered (if it was triggered) and return
                    if element.type == "sensor":
                        if not element.triggered:

                            if currentRuleElement.triggered:
                                self.logger.debug("[%s]: Sensor rule element with remote id '%d' and username '%s' "
                                                  % (self.fileName, element.element.remoteSensorId,
                                                     element.element.username)
                                                  + "not triggered. Set 'and' rule also to not triggered.")
                                currentRuleElement.triggered = False

                            return True

                    # check if weekday element is not triggered
                    # => if it is, set current rule element also as
                    # not triggered (if it was triggered) and return
                    elif element.type == "weekday":

                        if not element.triggered:

                            if currentRuleElement.triggered:
                                self.logger.debug("[%s]: Week day rule element with value '%d' for '%s' not "
                                                  % (self.fileName, element.element.weekday, element.element.time)
                                                  + "triggered. Set 'and' rule also to not triggered.")
                                currentRuleElement.triggered = False

                            return True

                    # check if monthday element is not triggered
                    # => if it is, set current rule element also as
                    # not triggered (if it was triggered) and return
                    elif element.type == "monthday":

                        if not element.triggered:

                            if currentRuleElement.triggered:
                                self.logger.debug("[%s]: Month day rule element with value '%d' for '%s' not "
                                                  % (self.fileName, element.element.monthday, element.element.time)
                                                  + "triggered. Set 'and' rule also to not triggered.")
                                currentRuleElement.triggered = False

                            return True

                    # check if hour element is not triggered
                    # => if it is, set current rule element also as
                    # not triggered (if it was triggered) and return
                    elif element.type == "hour":

                        if not element.triggered:

                            if currentRuleElement.triggered:
                                self.logger.debug("[%s]: Hour rule element from '%d' to '%d' for '%s' not "
                                                  % (self.fileName, element.element.start, element.element.end,
                                                     element.element.time)
                                                  + "triggered. Set 'and' rule also to not triggered.")
                                currentRuleElement.triggered = False

                            return True

                    # check if minute element is not triggered
                    # => if it is, set current rule element also as
                    # not triggered (if it was triggered) and return
                    elif element.type == "minute":

                        if not element.triggered:

                            if currentRuleElement.triggered:
                                self.logger.debug("[%s]: Minute rule element from '%d' to '%d' not "
                                                  % (self.fileName, element.element.start, element.element.end)
                                                  + "triggered. Set 'and' rule also to not triggered.")
                                currentRuleElement.triggered = False

                            return True

                    # check if second element is not triggered
                    # => if it is, set current rule element also as
                    # not triggered (if it was triggered) and return
                    elif element.type == "second":

                        if not element.triggered:

                            if currentRuleElement.triggered:
                                self.logger.debug("[%s]: Second rule element from '%d' to '%d' not "
                                                  % (self.fileName, element.element.start, element.element.end)
                                                  + "triggered. Set 'and' rule also to not triggered.")
                                currentRuleElement.triggered = False

                            return True

                    elif element.type == "boolean":
                        if not self._evaluateRuleElementsRecursively(element):
                            return False

                        # check if rule element was set to not triggered
                        # => if it was, set current rule element
                        # also as not triggered (when it was triggered)
                        # and return
                        if not element.triggered:

                            if currentRuleElement.triggered:
                                self.logger.debug("[%s]: Rule element evaluates to not triggered. Set 'and' "
                                                  % self.fileName
                                                  + "rule also to not triggered.")

                                currentRuleElement.triggered = False

                            return True

                    else:
                        self.logger.error("[%s]: Type of rule element not valid." % self.fileName)
                        return False

                # when this point is reached, every element of the "and"
                # rule is triggered
                # => set current element as triggered (when not triggered)
                # and return
                if not currentRuleElement.triggered:
                    self.logger.debug("[%s]: Each rule element evaluates to triggered. Set 'and' rule "
                                      % self.fileName
                                      + "also to triggered.")

                    currentRuleElement.triggered = True
                    utcTimestamp = int(time.time())
                    currentRuleElement.timeWhenTriggered = utcTimestamp

                return True

            # evaluate "or" rule element
            elif currentRuleElement.element.type == "or":

                orElement = currentRuleElement.element

                # first check all elements if there exist a "not rule" element
                # that is triggered
                # => if it does, set current rule element
                # also as triggered (if it was not triggered) and return
                # (done for optimization)
                for element in orElement.elements:

                    if element.type == "sensor" and element.triggered is True:

                        if not currentRuleElement.triggered:
                            self.logger.debug("[%s]: Sensor rule element with remote id '%d' and username '%s' "
                                              % (self.fileName, element.element.remoteSensorId,
                                                 element.element.username)
                                              + "triggered. Set 'or' rule also to triggered.")
                            currentRuleElement.triggered = True
                            utcTimestamp = int(time.time())
                            currentRuleElement.timeWhenTriggered = utcTimestamp

                        return True

                    elif element.type == "weekday" and element.triggered is True:

                        if not currentRuleElement.triggered:
                            self.logger.debug("[%s]: Week day rule element with value '%d' for '%s' "
                                              % (self.fileName, element.element.weekday, element.element.time)
                                              + "triggered. Set 'or' rule also to triggered.")
                            currentRuleElement.triggered = True
                            utcTimestamp = int(time.time())
                            currentRuleElement.timeWhenTriggered = utcTimestamp

                        return True

                    elif element.type == "monthday" and element.triggered is True:

                        if not currentRuleElement.triggered:
                            self.logger.debug("[%s]: Month day rule element with value '%d' for '%s' "
                                              % (self.fileName, element.element.monthday, element.element.time)
                                              + "triggered. Set 'or' rule also to triggered.")
                            currentRuleElement.triggered = True
                            utcTimestamp = int(time.time())
                            currentRuleElement.timeWhenTriggered = utcTimestamp

                        return True

                    elif element.type == "hour" and element.triggered is True:

                        if not currentRuleElement.triggered:
                            self.logger.debug("[%s]: Hour rule element from '%d' to '%d' for '%s' "
                                              % (self.fileName, element.element.start, element.element.end,
                                                 element.element.time)
                                              + "triggered. Set 'or' rule also to triggered.")
                            currentRuleElement.triggered = True
                            utcTimestamp = int(time.time())
                            currentRuleElement.timeWhenTriggered = utcTimestamp

                        return True

                    elif element.type == "minute" and element.triggered is True:

                        if not currentRuleElement.triggered:
                            self.logger.debug("[%s]: Minute rule element from '%d' to '%d' "
                                              % (self.fileName, element.element.start, element.element.end)
                                              + "triggered. Set 'or' rule also to triggered.")
                            currentRuleElement.triggered = True
                            utcTimestamp = int(time.time())
                            currentRuleElement.timeWhenTriggered = utcTimestamp

                        return True

                    elif element.type == "second" and element.triggered is True:

                        if not currentRuleElement.triggered:
                            self.logger.debug("[%s]: Second rule element from '%d' to '%d' "
                                              % (self.fileName, element.element.start, element.element.end)
                                              + "triggered. Set 'or' rule also to triggered.")
                            currentRuleElement.triggered = True
                            utcTimestamp = int(time.time())
                            currentRuleElement.timeWhenTriggered = utcTimestamp

                        return True

                # if there exists no element that is already triggered
                # => update rule elements and evaluate them
                for element in orElement.elements:

                    # only update rule elements
                    if element.type == "boolean":
                        if not self._evaluateRuleElementsRecursively(element):
                            return False

                        # check if rule element was set to triggered
                        # => if it was, set current rule element
                        # also as triggered (if it was not triggered)
                        # and return
                        if element.triggered:

                            if not currentRuleElement.triggered:
                                self.logger.debug("[%s]: Rule element evaluates to triggered. Set 'or' rule "
                                                  % self.fileName
                                                  + "also to triggered.")
                                currentRuleElement.triggered = True
                                utcTimestamp = int(time.time())
                                currentRuleElement.timeWhenTriggered = utcTimestamp

                            return True

                # when this point is reached, every element of the "or"
                # rule is not triggered
                # => set current element as not triggered (if it was triggered)
                # and return
                if currentRuleElement.triggered:
                    self.logger.debug("[%s]: Each rule element evaluates to not triggered. Set 'or' rule "
                                      % self.fileName
                                      + "also to not triggered.")
                    currentRuleElement.triggered = False

                return True

            # evaluate "not" rule element
            elif currentRuleElement.element.type == "not":

                notElement = currentRuleElement.element

                element = notElement.elements[0]

                # check if sensor rule element and current not rule element
                # have the same triggered value
                # => toggle current not element triggered value
                if element.type == "sensor":
                    if element.triggered == currentRuleElement.triggered:
                        self.logger.debug("[%s]: Sensor rule element with remote id '%d' and username '%s' has same "
                                          % (self.fileName, element.element.remoteSensorId, element.element.username)
                                          + "triggered value as 'not' rule. Toggle triggered value of 'not' rule.")
                        # toggle current rule element triggered value
                        currentRuleElement.triggered = not element.triggered

                    return True

                # check if week day rule element and current not rule element
                # have the same triggered value
                # => toggle current not element triggered value
                elif element.type == "weekday":
                    if element.triggered == currentRuleElement.triggered:
                        self.logger.debug("[%s]: Week day rule element with value '%d' for '%s' has same "
                                          % (self.fileName, element.element.weekday, element.element.time)
                                          + "triggered value as 'not' rule. Toggle triggered value of 'not' rule.")
                        # toggle current rule element triggered value
                        currentRuleElement.triggered = not element.triggered

                    return True

                # check if month day rule element and current not rule element
                # have the same triggered value
                # => toggle current not element triggered value
                elif element.type == "monthday":
                    if element.triggered == currentRuleElement.triggered:
                        self.logger.debug("[%s]: Month day rule element with value '%d' for '%s' has same "
                                          % (self.fileName, element.element.monthday, element.element.time)
                                          + "triggered value as 'not' rule. Toggle triggered value of 'not' rule.")
                        # toggle current rule element triggered value
                        currentRuleElement.triggered = not element.triggered

                    return True

                # check if hour rule element and current not rule element
                # have the same triggered value
                # => toggle current not element triggered value
                elif element.type == "hour":
                    if element.triggered == currentRuleElement.triggered:
                        self.logger.debug("[%s]: Hour rule element from '%d' to '%d' for '%s' has same "
                                          % (self.fileName, element.element.start, element.element.end,
                                             element.element.time)
                                          + "triggered value as 'not' rule. Toggle triggered value of 'not' rule.")
                        # toggle current rule element triggered value
                        currentRuleElement.triggered = not element.triggered

                    return True

                # check if minute rule element and current not rule element
                # have the same triggered value
                # => toggle current not element triggered value
                elif element.type == "minute":
                    if element.triggered == currentRuleElement.triggered:
                        self.logger.debug("[%s]: Minute rule element from '%d' to '%d' has same "
                                          % (self.fileName, element.element.start, element.element.end)
                                          + "triggered value as 'not' rule. Toggle triggered value of 'not' rule.")
                        # toggle current rule element triggered value
                        currentRuleElement.triggered = not element.triggered

                    return True

                # check if second rule element and current not rule element
                # have the same triggered value
                # => toggle current not element triggered value
                elif element.type == "second":
                    if element.triggered == currentRuleElement.triggered:
                        self.logger.debug("[%s]: Second rule element from '%d' to '%d' has same "
                                          % (self.fileName, element.element.start, element.element.end)
                                          + "triggered value as 'not' rule. Toggle triggered value of 'not' rule.")
                        # toggle current rule element triggered value
                        currentRuleElement.triggered = not element.triggered

                    return True

                # check if rule element evaluates to the same triggered value
                # as the current not rule element
                # => toggle current not element triggered value
                elif element.type == "boolean":
                    if not self._evaluateRuleElementsRecursively(element):
                        return False

                    # check if rule element was evaluated to the same
                    # triggered value as the not rule element
                    # => toggle current not element triggered value
                    if element.triggered == currentRuleElement.triggered:
                        self.logger.debug("[%s]: Rule element evaluates to the same triggered value as 'not' rule. "
                                          % self.fileName
                                          + "Toggle triggered value of 'not' rule.")
                        # toggle current rule element triggered value
                        currentRuleElement.triggered = not element.triggered

                    return True

                else:
                    self.logger.error("[%s]: Type of rule element not valid." % self.fileName)
                    return False

        # if current rule element is not of type "boolean"
        # => just return
        else:
            return True

    def _updateRule(self,
                    sensorAlertList: List[Tuple[int, int, int, int, int, int, str]],
                    alertLevel: AlertLevel) -> bool:
        """
        this internal function updates all rules and their rule elements
        (sets new values for them, evaluates the boolean elements etc)

        :param sensorAlertList:
        :param alertLevel:
        :return:
        """
        self.logger.debug("[%s]: Updating rule values for alert level '%d'."
                          % (self.fileName, alertLevel.level))

        # update and evaluate all rules of the alert level
        for ruleStart in alertLevel.rules:

            # update all rule values (sets also the sensors as triggered
            # or not triggered)
            if not self._updateRuleValuesRecursively(sensorAlertList, ruleStart):
                self.logger.error("[%s]: Not able to update values for rule with order '%d' "
                                  % (self.fileName, ruleStart.order)
                                  + "for alert level '%d'."
                                  % alertLevel.level)
                return False

            # evaluate all and/or/not rule elements
            if not self._evaluateRuleElementsRecursively(ruleStart):
                self.logger.error("[%s]: Not able to evaluate rule with order '%d' for alert level '%d'."
                                  % (self.fileName, ruleStart.order, alertLevel.level))
                return False

        # if more than one rule exists
        # => check if they had triggered in the correct time frame
        if len(alertLevel.rules) > 1:
            for idx in range(len(alertLevel.rules)):

                # skip first rule start
                if idx == 0:
                    continue

                prevRuleStart = alertLevel.rules[idx - 1]
                currRuleStart = alertLevel.rules[idx]

                # check if current rule was triggered
                if currRuleStart.triggered:

                    # check if current rule was triggered right between
                    # min and max time after previous rule
                    # => do not change anything
                    if (((prevRuleStart.timeWhenTriggered + currRuleStart.minTimeAfterPrev) <=
                       currRuleStart.timeWhenTriggered) and
                       ((prevRuleStart.timeWhenTriggered + currRuleStart.maxTimeAfterPrev) >=
                       currRuleStart.timeWhenTriggered)):
                        continue

                    # if rule had not triggered right between min
                    # and max time
                    # => reset it
                    else:
                        self.logger.debug("[%s]: Rule with order '%d' for alert level '%d' did not trigger "
                                          % (self.fileName, currRuleStart.order, alertLevel.level)
                                          + "in time. Reset rule.")
                        currRuleStart.triggered = False
                        currRuleStart.timeWhenTriggered = 0.0

        # check if all received sensor alerts count as triggered
        # and therefore can be removed
        for sensorAlert in list(sensorAlertList):
            sensorAlertTimeReceived = sensorAlert[3]
            sensorAlertAlertDelay = sensorAlert[4]

            # if there does not exist an alert delay
            # => remove sensor alert
            utcTimestamp = int(time.time())
            if sensorAlertAlertDelay == 0:
                sensorAlertList.remove(sensorAlert)

            # if there exist an alert delay
            # => only remove sensor alert from the list when there is no
            # delay to wait (add an artificial delay from 5 seconds
            # to make race condition unlikely)
            elif (utcTimestamp - sensorAlertTimeReceived) > (sensorAlertAlertDelay + 5):
                sensorAlertList.remove(sensorAlert)

        # check if the counter is activated and when it is activated
        # if the counter limit is reached
        for ruleStart in alertLevel.rules:

            # skip counter checking when counter is not activated
            if not ruleStart.counterActivated:
                continue

            # remove all triggered elements from the counter
            # if the time that they have to wait has passed
            utcTimestamp = int(time.time())
            for counterTimeWhenTriggered in list(ruleStart.counterList):
                if (counterTimeWhenTriggered + ruleStart.counterWaitTime) < utcTimestamp:
                    self.logger.debug("[%s]: Counter for rule with order '%d' for alert level '%d' "
                                      % (self.fileName, ruleStart.order, alertLevel.level)
                                      + "has expired. Removing it.")
                    ruleStart.counterList.remove(counterTimeWhenTriggered)

            # only process counter if the rule is triggered
            if ruleStart.triggered:

                # check if timeWhenTriggered is already processed in the
                # counter list
                # => do nothing
                if ruleStart.timeWhenTriggered in ruleStart.counterList:
                    pass

                # when it is not processed yet
                # => add it or reset the trigger
                else:

                    # check if the limit of the counter is not yet reached
                    # => add timeWhenTriggered to the counter list
                    if len(ruleStart.counterList) < ruleStart.counterLimit:
                        ruleStart.counterList.append(ruleStart.timeWhenTriggered)

                    # when the limit is already reached
                    # => reset the trigger
                    else:
                        self.logger.debug("[%s]: Counter for rule with order '%d' for alert level '%d' has reached "
                                          % (self.fileName, ruleStart.order, alertLevel.level)
                                          + "its limit. Resetting rule.")
                        ruleStart.triggered = False
                        ruleStart.timeWhenTriggered = 0.0

    def _evaluateRules(self,
                       alertLevel: AlertLevel) -> bool:
        """
        this internal function evaluates if the rule chain of the given alert level is triggered

        :param alertLevel:
        :return:
        """
        self.logger.debug("[%s]: Evaluate rules for alert level '%d'."
                          % (self.fileName, alertLevel.level))

        # check only the "root" element of the last rule
        # if it has triggered, because only the last rule in the rules chain
        # have to be triggered to trigger the alert level (all other rules
        # in the chain had to be triggered at some point in time to trigger
        # the last rule)
        ruleStart = alertLevel.rules[-1]

        # if the last rule of the chain has triggered
        # => reset all rules in the chain
        if ruleStart.triggered:
            for rule in alertLevel.rules:
                rule.timeWhenTriggered = 0.0
                rule.triggered = False

            return True

        else:
            return False

    def _checkRulesCanTriggerRecursively(self,
                                         currentRuleElement: RuleElement) -> bool:
        """
        this internal function checks recusrively if a rule element is triggered
        and therefore the rule is likely to trigger during the next evaluation

        :param currentRuleElement:
        :return:
        """
        # check if rule element is of type "sensor"
        # => return if it is triggered
        if currentRuleElement.type == "sensor":
            return currentRuleElement.triggered

        # check if rule element is of type "weekday"
        # => return if it is triggered
        elif currentRuleElement.type == "weekday":
            return currentRuleElement.triggered

        # check if rule element is of type "monthday"
        # => return if it is triggered
        elif currentRuleElement.type == "monthday":
            return currentRuleElement.triggered

        # check if rule element is of type "hour"
        # => return if it is triggered
        elif currentRuleElement.type == "hour":
            return currentRuleElement.triggered

        # check if rule element is of type "minute"
        # => return if it is triggered
        elif currentRuleElement.type == "minute":
            return currentRuleElement.triggered

        # check if rule element is of type "second"
        # => return if it is triggered
        elif currentRuleElement.type == "second":
            return currentRuleElement.triggered

        # check if rule element is of type "boolean"
        # => traverse rule recursively
        elif currentRuleElement.type == "boolean":

            # check all rule elements of the current rule element
            # if one rule element is triggered => rule can still trigger
            for ruleElement in currentRuleElement.element.elements:

                if self._checkRulesCanTriggerRecursively(ruleElement):
                    return True

            # when this point is reached, no rule element of the current one
            # is triggered
            return False

        else:
            self.logger.error("[%s]: Rule element has an invalid type while checking."
                              % self.fileName)
            return False

    def _checkRulesCanTrigger(self,
                              sensorAlertList: List[Tuple[int, int, int, int, int, int, str]],
                              alertLevel) -> bool:
        """
        this internal function checks if a rule is likely to trigger
        during the next check (means an element of it counts still as triggered)

        :param sensorAlertList:
        :param alertLevel:
        :return:
        """
        self.logger.debug("[%s]: Check if rules of alert level '%d' can trigger."
                          % (self.fileName, alertLevel.level))

        # check if a sensor alert is still in the list (this happens
        # when a sensor has a delay until it counts as triggered)
        if sensorAlertList:
            return True

        # check all rules if they can still trigger
        # if one of the rules chain can => complete rules chain can trigger
        for ruleElement in alertLevel.rules:
            if self._checkRulesCanTriggerRecursively(ruleElement):
                return True

        # when this point is reached, no rule of the rules chain can trigger
        # at the moment
        return False

    def processSensorAlertsRules(self):
        """
        Function that processes all sensor alerts handled by the rule engine
        (meaning all sensor alerts that are affected by rules).
        """
        # check all sensor alerts to handle with alert levels that have
        # rules if they have to be triggered
        for sensorAlertToHandle in list(self.sensorAlertsToHandleWithRules):

            # Convert sensor alerts back to tuple list because
            # the rule engine works on a tuple list
            # (has to be done until rule engine is re-factored).
            sensorAlertTupleList = list()
            for sensorAlert in sensorAlertToHandle[0]:
                temp = (sensorAlert.sensorAlertId,
                        sensorAlert.sensorId,
                        sensorAlert.nodeId,
                        sensorAlert.timeReceived,
                        sensorAlert.alertDelay,
                        sensorAlert.state,
                        sensorAlert.description)
                sensorAlertTupleList.append(temp)

            alertLevel = sensorAlertToHandle[1]

            # update the rule chain of the alert level with
            # the received sensor alerts
            self._updateRule(sensorAlertTupleList, alertLevel)

            # check if the rule chain evaluates to triggered
            # => trigger sensor alert for the alert level
            if self._evaluateRules(alertLevel):
                self.logger.info("[%s]: Alert level '%d' rules have triggered." % (self.fileName, alertLevel.level))

                # Create a temporary alert level for this triggered rule.
                ruleSensorAlert = SensorAlert()
                ruleSensorAlert.rulesActivated = True
                ruleSensorAlert.sensorId = -1
                ruleSensorAlert.changeState = False
                ruleSensorAlert.alertLevels.append(alertLevel.level)
                ruleSensorAlert.triggeredAlertLevels.append(alertLevel.level)
                ruleSensorAlert.state = 1
                ruleSensorAlert.description = "Rule of Alert Level: '%s'" % alertLevel.name
                ruleSensorAlert.hasOptionalData = False
                ruleSensorAlert.optionalData = None
                ruleSensorAlert.hasLatestData = False
                ruleSensorAlert.dataType = SensorDataType.NONE
                ruleSensorAlert.sensorData = None

                # send sensor alert to all manager and alert clients
                for serverSession in self.serverSessions:
                    # ignore sessions which do not exist yet
                    # and that are not managers
                    if serverSession.clientComm is None:
                        continue
                    if serverSession.clientComm.nodeType != "manager" and serverSession.clientComm.nodeType != "alert":
                        continue
                    if not serverSession.clientComm.clientInitialized:
                        continue

                    # Only send a sensor alert to a client that actually
                    # handles a triggered alert level.
                    clientAlertLevels = serverSession.clientComm.clientAlertLevels
                    atLeastOne = alertLevel.level in clientAlertLevels
                    if not atLeastOne:
                        continue

                    # sending sensor alert to manager/alert node
                    # via a thread to not block the sensor alert executer
                    sensorAlertProcess = AsynchronousSender(self.globalData,
                                                            serverSession.clientComm)
                    # set thread to daemon
                    # => threads terminates when main thread terminates
                    sensorAlertProcess.daemon = True
                    sensorAlertProcess.sendSensorAlert = True
                    sensorAlertProcess.sensorAlert = ruleSensorAlert

                    self.logger.debug("[%s]: Sending sensor alert to manager/alert (%s:%d)."
                                      % (self.fileName, serverSession.clientComm.clientAddress,
                                         serverSession.clientComm.clientPort))
                    sensorAlertProcess.start()

                # remove sensor alert to handle from list
                # after it has triggered
                self.sensorAlertsToHandleWithRules.remove(sensorAlertToHandle)

            # if rule chain did not evaluate to triggered
            # => check if it is likely that it can trigger during the
            # next evaluation if not => remove the sensor alert to handle
            elif not self._checkRulesCanTrigger(sensorAlertTupleList, alertLevel):
                    self.logger.debug("[%s]: Alert level '%d' rules can not trigger at the moment."
                                      % (self.fileName, alertLevel.level))

                    # remove sensor alert to handle from list
                    # when it can not trigger at the current state
                    self.sensorAlertsToHandleWithRules.remove(sensorAlertToHandle)

    def add_sensor_alert(self,
                         sensorAlert: SensorAlert,
                         alertLevel: AlertLevel):
        """
        Function that pre-processes the given sensor alert for a given alert level to decide if the rule
        engine is responsible to handle it.

        :param sensorAlert:
        :param alertLevel:
        """
        if not alertLevel.rulesActivated:
            return

        # check if an alert level with a rule is already triggered
        # => add current sensor alert to it
        found = False
        for alertWithRule in self.sensorAlertsToHandleWithRules:
            if alertLevel.level == alertWithRule[1].level:
                alertWithRule[0].append(sensorAlert)
                found = True
                break

        # if no alert level with a rule was found
        # => create a new sensor alert with rule
        # to handle for it
        if not found:
            self.sensorAlertsToHandleWithRules.append(([sensorAlert], alertLevel))

    def has_sensor_alerts_to_handle(self) -> bool:
        """
        Checks if the rule engine has sensor alerts to handle.

        :return: Are sensor alerts to handle by the rule engine?
        """
        return len(self.sensorAlertsToHandleWithRules) != 0
