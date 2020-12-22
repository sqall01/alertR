#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import time
import logging
import icalendar
import datetime
import dateutil
import requests
import threading
import queue
import calendar
import pytz
from .core import _PollingSensor
from ..localObjects import SensorAlert, StateChange, SensorDataType
from typing import Optional


# Class that controls one icalendar.
class ICalendarSensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        # NOTE: Can be changed if "parseOutput" is set to true in the
        # configuration file.
        self.sensorDataType = SensorDataType.NONE

        # used for logging
        self.fileName = os.path.basename(__file__)

        # Name of the calendar.
        self.name = None

        # Location of the icalendar.
        self.location = None

        # Used htaccess authentication.
        self.htaccessAuth = None
        self.htaccessUser = None
        self.htaccessPass = None
        self.htaccessData = None

        # The interval in seconds in which an update is collected
        # from the server.
        self.intervalFetch = None

        # The interval in seconds in which the calendar is processed.
        self.intervalProcess = None

        # Number of failed calendar collection attempts.
        self.failedCounter = 0
        self.maxFailedAttempts = 10
        self.inFailedState = False

        # Locks calendar data in order to be thread safe.
        self.icalendarLock = threading.Semaphore(1)

        # Time when the data was fetched.
        self.lastFetch = 0

        # Time when the data was processed.
        self.lastProcess = 0

        # iCalendar data object.
        self.icalendar = None

        # A queue of reminder sensor alerts.
        self.reminderAlertQueue = queue.Queue()

        # Set of tuples that describe reminders that were already triggered.
        self.alreadyTriggered = set()

        # Time deltas needed for calculations.
        self.timedelta10min = datetime.timedelta(minutes=10)
        self.timedelta1day = datetime.timedelta(days=1)
        self.timedelta2day = datetime.timedelta(days=2)

    # Collect calendar data from the server.
    def _getCalendar(self):

        # Update time.
        utcTimestamp = int(time.time())
        self.lastFetch = utcTimestamp

        logging.debug("[%s]: Retrieving calendar data from '%s'."
                      % (self.fileName, self.location))

        # Request data from server.
        request = None
        try:
            request = requests.get(self.location,
                verify=True,
                auth=self.htaccessData)
        except:
            logging.exception("[%s]: Could not get calendar data from server."
                              % self.fileName)
            self.failedCounter += 1
            return

        # Check status code.
        if request.status_code != 200:
            logging.error("[%s] Server responded with wrong status code (%d)."
                          % (self.fileName, request.status_code))
            self.failedCounter += 1
            return

        # Parse calendar data.
        tempCal = None
        try:
            tempCal = icalendar.Calendar.from_ical(request.content)
        except:
            logging.exception("[%s]: Could not parse calendar data."
                              % self.fileName)
            self.failedCounter += 1
            return

        # Move copy icalendar object to final object.
        self.icalendarLock.acquire()
        self.icalendar = tempCal
        self.icalendarLock.release()

        # Reset fail counter.
        self.failedCounter = 0

    # Process the calendar data if we have a reminder triggered.
    def _processCalendar(self):

        self.lastProcess = int(time.time())

        self.icalendarLock.acquire()

        # Only process calendar data if we have any.
        if self.icalendar is None:
            self.icalendarLock.release()
            return

        for event in self.icalendar.walk("VEVENT"):

            if event.is_empty():
                continue

            if "DTSTART" not in event or "SUMMARY" not in event:
                continue

            # Process the vent.
            self._processEvent(event)

        self.icalendarLock.release()

    # Processes an event of a calendar.
    def _processEvent(self, event: icalendar.cal.Event):

        # Get time when event starts.
        dtstart = event.get("DTSTART")

        # Get current time in timezone of event.
        eventDatetime = None

        # Create a datetime starting at midnight
        # if we have an "all day" event. This event is in the local
        # timezone.
        if type(dtstart.dt) == datetime.date:
            eventUTCTime = calendar.timegm(dtstart.dt.timetuple())
            eventDatetime = datetime.datetime.utcfromtimestamp(eventUTCTime)
            # Since we just overwrite the timezone here, we do not
            # care about conversion from UTC since the new datetime
            # object starts at midnight in the given timezone.
            eventDatetime = eventDatetime.replace(tzinfo=dateutil.tz.tzlocal())

        # Copy the date time if we have a "normal" event.
        elif type(dtstart.dt) == datetime.datetime:
            eventDatetime = dtstart.dt
            if eventDatetime.tzinfo is None:
                eventDatetime = eventDatetime.replace(tzinfo=pytz.UTC)

        else:
            logging.debug("[%s] Do not know how to handle type '%s' "
                          % (self.fileName, dtstart.dt.__class__)
                          + "of event start.")
            return

        # Create current datetime object.
        currentUTCTime = time.time()
        currentDatetime = datetime.datetime.utcfromtimestamp(currentUTCTime)
        currentDatetime = currentDatetime.replace(tzinfo=pytz.UTC)

        # Process rrule if event has one (rrule means event is repeating).
        if "RRULE" in event:

            eventRule = event.get("RRULE")

            if "UNTIL" in eventRule:
                # Sometimes the rrule will fail to parse the event rule if
                # we have a mix of "date times" with timezone and an
                # "until" without it.
                if type(eventRule.get("until")[0]) == datetime.datetime:
                    timezone = eventRule.get("until")[0].tzinfo

                    # "RRULE values must be specified in UTC when
                    # DTSTART is timezone-aware"
                    if timezone is None:
                        eventRule["UNTIL"][0] = eventRule["UNTIL"][0].replace(
                                                            tzinfo=pytz.UTC)

                # Since date objects do not have a timezone but rrule needs
                # one, we replace the date object with a datetime object
                # in UTC time.
                elif type(eventRule.get("until")[0]) == datetime.date:
                    tempUntil = eventRule.get("until")[0]
                    ruleUTCTime = calendar.timegm(tempUntil.timetuple())
                    ruleDatetime = datetime.datetime.utcfromtimestamp(
                                                                ruleUTCTime)
                    ruleDatetime = ruleDatetime.replace(tzinfo=pytz.UTC)
                    eventRule["UNTIL"][0] = ruleDatetime

            # Use python dateutil for parsing the rrule.
            eventDatetimeAfter = None
            eventDatetimeBefore = None

            try:
                rrset = dateutil.rrule.rruleset()

                rule_str = eventRule.to_ical().decode("ascii")
                rrulestr = dateutil.rrule.rrulestr(rule_str,
                                                   dtstart=eventDatetime)
                rrset.rrule(rrulestr)

                # Get first event that occurs before
                # and after the current time.
                eventDatetimeAfter = rrset.after(currentDatetime)
                eventDatetimeBefore = rrset.before(currentDatetime)

            except:
                logging.exception("[%s] Not able to parse rrule for '%s'."
                                  % (self.fileName, event.get("SUMMARY")))

            # Process the event alarms for the first event occurring after the
            # current time.
            if eventDatetimeAfter:

                self._processEventAlarms(event, eventDatetimeAfter)

            # Process the event alarms for the first event occurring before the
            # current time (needed because of edge cases with alarms 0 seconds
            # before event). But only check event if it is not older than
            # 10 minutes.
            if eventDatetimeBefore:
                if (eventDatetimeBefore >=
                   (currentDatetime - self.timedelta10min)):
                    self._processEventAlarms(event, eventDatetimeBefore)

        # Process "normal" events.
        else:
            # Check if the event is in the past (minus 10 minutes).
            if eventDatetime <= (currentDatetime - self.timedelta10min):
                return

            self._processEventAlarms(event, eventDatetime)

    # Processes each reminder/alarm of an event.
    def _processEventAlarms(self, event: icalendar.cal.Event, eventDatetime: datetime.datetime):

        # Create current datetime object.
        currentUTCTime = time.time()
        currentDatetime = datetime.datetime.utcfromtimestamp(currentUTCTime)
        currentDatetime = currentDatetime.replace(tzinfo=pytz.UTC)

        for alarm in event.walk("VALARM"):

            if "TRIGGER" in alarm:

                # Get time delta when reminder is triggered.
                trigger = alarm.get("TRIGGER")

                # Get time when reminder is triggered.
                # When trigger time is a delta, then calculate the actual time.
                if type(trigger.dt) == datetime.timedelta:
                    triggerDatetime = eventDatetime + trigger.dt

                # When trigger time is an actual time, use this.
                elif type(trigger.dt) == datetime.datetime:
                    triggerDatetime = trigger.dt

                    # Use the same timezone as the event when
                    # no is given.
                    if triggerDatetime.tzinfo is None:
                        triggerDatetime = triggerDatetime.replace(
                                                tzinfo=eventDatetime.tzinfo)

                # When trigger time is only a date, start at midnight,
                # however, use the same timezone as the event.
                elif type(trigger.dt) == datetime.date:
                    triggerUTCTime = calendar.timegm(trigger.dt.timetuple())
                    triggerDatetime = datetime.datetime.utcfromtimestamp(
                                                                triggerUTCTime)
                    # Since we just overwrite the timezone here, we do not
                    # care about conversion from UTC since the new datetime
                    # object starts at midnight in the given timezone.
                    triggerDatetime = triggerDatetime.replace(
                                                tzinfo=eventDatetime.tzinfo)

                else:
                    logging.error("[%s] Error: Do not know how to handle "
                                  % self.fileName
                                  + "trigger type '%s'."
                                  % trigger.dt.__class__)
                    continue

                # Uid of event is needed.
                uid = event.get("UID")

                # Get time when event starts.
                dtstart = event.get("DTSTART")

                # Check if we already triggered an alarm for the event
                # with this uid and the given alarm trigger time.
                if (uid, triggerDatetime) in self.alreadyTriggered:
                    break

                # Check if the alarm trigger time lies in the past but not
                # more than 1 day.
                if((currentDatetime - self.timedelta1day)
                    <= triggerDatetime
                    <= currentDatetime):

                    title = event.get("SUMMARY")

                    # Get description if event has one.
                    evDescription = ""
                    if "DESCRIPTION" in event:
                        evDescription = event.get("DESCRIPTION")

                    # Get location if event has one.
                    location = ""
                    if "LOCATION" in event:
                        location = event.get("LOCATION")

                    # Create the utc unix timestamp for the start of the event.
                    unixStart = datetime.datetime.utcfromtimestamp(0)
                    unixStart = unixStart.replace(tzinfo=pytz.UTC)

                    utcDtstart = int(
                                (eventDatetime - unixStart).total_seconds())

                    # Create the utc unix timestamp for the reminder trigger.
                    utcTrigger = int(
                                (triggerDatetime - unixStart).total_seconds())

                    eventDateStr = time.strftime("%D %H:%M:%S",
                                                 time.localtime(utcDtstart))
                    msg = "Reminder for event '%s' at %s" % (title, eventDateStr)

                    # Create sensor alert.
                    sensorAlert = SensorAlert()
                    sensorAlert.clientSensorId = self.id
                    sensorAlert.state = 1
                    sensorAlert.hasOptionalData = True
                    sensorAlert.optionalData = {"message": msg,
                                                "calendar": self.name,
                                                "type": "reminder",
                                                "title": title,
                                                "description": evDescription,
                                                "location": location,
                                                "trigger": utcTrigger,
                                                "start": utcDtstart}
                    sensorAlert.changeState = False
                    sensorAlert.hasLatestData = False
                    sensorAlert.dataType = SensorDataType.NONE

                    self.reminderAlertQueue.put(sensorAlert)

                    # Store the event uid and the alarm trigger time
                    # as already triggered.
                    self.alreadyTriggered.add( (uid, triggerDatetime) )

    def initializeSensor(self):
        self.changeState = False
        self.hasLatestData = False
        self.state = 1 - self.triggerState

        # Set htaccess authentication object.
        if self.htaccessAuth == "BASIC":
            self.htaccessData = requests.auth.HTTPBasicAuth(self.htaccessUser, self.htaccessPass)
        elif self.htaccessAuth == "DIGEST":
            self.htaccessData = requests.auth.HTTPDigestAuth(self.htaccessUser, self.htaccessPass)
        elif self.htaccessAuth == "NONE":
            self.htaccessData = None
        else:
            return False

        # Get first calendar data.
        self._getCalendar()

        return True

    def getState(self) -> int:
        return self.state

    def updateState(self):

        # Check if we have to collect new calendar data.
        utcTimestamp = int(time.time())
        if (utcTimestamp - self.lastFetch) > self.intervalFetch:

            # Update calendar data in a non-blocking way
            # (this means also, that the current state will not be processed
            # on the updated data, but one of the next rounds will have it)
            thread = threading.Thread(target=self._getCalendar)
            thread.start()

            logging.debug("[%s] Number of remaining already "
                          % self.fileName
                          + "triggered elements: %d"
                          % len(self.alreadyTriggered))

        # Process calendar data for occurring reminder.
        if (utcTimestamp - self.lastProcess) > self.intervalProcess:
            self._processCalendar()

        # Clean up already triggered alerts.
        for triggeredTuple in list(self.alreadyTriggered):
            uid = triggeredTuple[0]
            triggerDatetime = triggeredTuple[1]

            timezone = triggerDatetime.tzinfo
            currentDatetime = datetime.datetime.fromtimestamp(time.time(),
                                                              timezone)
            if (currentDatetime - self.timedelta2day) >= triggerDatetime:
                self.alreadyTriggered.remove(triggeredTuple)

    def forceSendAlert(self) -> Optional[SensorAlert]:

        # Check if we have exceeded the threshold of failed calendar
        # retrieval attempts and create a sensor alert if we have.
        sensorAlert = None
        if (not self.inFailedState
            and self.failedCounter > self.maxFailedAttempts):

            logging.warning("[%s] Triggering sensor alert for "
                            % self.fileName
                            + "'%d' failed calendar fetching attempts."
                            % self.failedCounter)

            sensorAlert = SensorAlert()
            sensorAlert.clientSensorId = self.id
            sensorAlert.state = 1
            sensorAlert.hasOptionalData = True
            msg = "Failed more than %d times for '%s' " \
                  % (self.maxFailedAttempts, self.name) \
                  + "to retrieve calendar data."
            sensorAlert.optionalData = {"message": msg,
                                        "calendar": self.name,
                                        "type": "timeout"}
            sensorAlert.changeState = True
            sensorAlert.hasLatestData = False
            sensorAlert.dataType = SensorDataType.NONE

            self.state = self.triggerState
            self.inFailedState = True

        # If we are in a failed retrieval state and we could retrieve
        # calendar data again trigger a sensor alert for "normal".
        elif (self.inFailedState
            and self.failedCounter <= self.maxFailedAttempts):

            logging.warning("[%s] Fetching calendar succeeded after "
                            % self.fileName
                            + "multiple failed attempts. Triggering sensor alert.")

            sensorAlert = SensorAlert()
            sensorAlert.clientSensorId = self.id
            sensorAlert.state = 0
            sensorAlert.hasOptionalData = True
            msg = "Calendar data for '%s' retrievable again." % self.name
            sensorAlert.optionalData = {"message": msg,
                                        "calendar": self.name,
                                        "type": "timeout"}
            sensorAlert.changeState = True
            sensorAlert.hasLatestData = False
            sensorAlert.dataType = SensorDataType.NONE

            self.state = 1 - self.triggerState
            self.inFailedState = False

        # If we have sensor alerts of reminder waiting
        # return the oldest of them.
        elif not self.reminderAlertQueue.empty():
            try:
                sensorAlert = self.reminderAlertQueue.get(True, 2)
            except:
                pass

        return sensorAlert

    def forceSendState(self) -> Optional[StateChange]:
        return None
