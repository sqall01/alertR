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
from .core import _PollingSensor
from ..globalData import SensorObjSensorAlert, SensorObjStateChange, SensorDataType
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
    def _get_calendar(self):

        # Update time.
        utc_timestamp = int(time.time())
        self.lastFetch = utc_timestamp

        logging.debug("[%s]: Retrieving calendar data from '%s'." % (self.fileName, self.location))

        # Request data from server.
        request = None
        try:
            request = requests.get(self.location, verify=True, auth=self.htaccessData)

        except Exception:
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
        temp_cal = None
        try:
            temp_cal = icalendar.Calendar.from_ical(request.content)

        except Exception:
            logging.exception("[%s]: Could not parse calendar data."
                              % self.fileName)
            self.failedCounter += 1
            return

        # Move copy icalendar object to final object.
        self.icalendarLock.acquire()
        self.icalendar = temp_cal
        self.icalendarLock.release()

        # Reset fail counter.
        self.failedCounter = 0

    # Process the calendar data if we have a reminder triggered.
    def _process_calendar(self):

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
            self._process_event(event)

        self.icalendarLock.release()

    # Processes an event of a calendar.
    def _process_event(self, event: icalendar.cal.Event):

        # Get time when event starts.
        dtstart = event.get("DTSTART")

        # Get current time in timezone of event.
        event_datetime = None

        # Create a datetime starting at midnight
        # if we have an "all day" event. This event is in the local
        # timezone.
        if type(dtstart.dt) == datetime.date:
            event_utc_time = calendar.timegm(dtstart.dt.timetuple())
            # Since we just overwrite the timezone here, we do not
            # care about conversion from UTC since the new datetime
            # object starts at midnight in the given timezone.
            event_datetime = datetime.datetime.fromtimestamp(event_utc_time, dateutil.tz.tzlocal())

        # Copy the date time if we have a "normal" event.
        elif type(dtstart.dt) == datetime.datetime:
            event_datetime = dtstart.dt
            if event_datetime.tzinfo is None:
                event_datetime = event_datetime.replace(tzinfo=datetime.timezone.utc)

        else:
            logging.debug("[%s] Do not know how to handle type '%s' "
                          % (self.fileName, dtstart.dt.__class__)
                          + "of event start.")
            return

        # Create current datetime object.
        current_datetime = datetime.datetime.fromtimestamp(time.time(), datetime.timezone.utc)

        # Process rrule if event has one (rrule means event is repeating).
        if "RRULE" in event:

            event_rule = event.get("RRULE")

            if "UNTIL" in event_rule:
                # Sometimes the rrule will fail to parse the event rule if
                # we have a mix of "date times" with timezone and an
                # "until" without it.
                if type(event_rule.get("until")[0]) == datetime.datetime:
                    timezone = event_rule.get("until")[0].tzinfo

                    # "RRULE values must be specified in UTC when
                    # DTSTART is timezone-aware"
                    if timezone is None:
                        event_rule["UNTIL"][0] = event_rule["UNTIL"][0].replace(tzinfo=datetime.timezone.utc)

                # Since date objects do not have a timezone but rrule needs
                # one, we replace the date object with a datetime object
                # in UTC time.
                elif type(event_rule.get("until")[0]) == datetime.date:
                    temp_until = event_rule.get("until")[0]
                    rule_utc_time = calendar.timegm(temp_until.timetuple())
                    rule_datetime = datetime.datetime.fromtimestamp(rule_utc_time, datetime.timezone.utc)
                    event_rule["UNTIL"][0] = rule_datetime

            # Use python dateutil for parsing the rrule.
            event_datetime_after = None
            event_datetime_before = None

            try:
                rrset = dateutil.rrule.rruleset()

                rule_str = event_rule.to_ical().decode("ascii")
                rrulestr = dateutil.rrule.rrulestr(rule_str,
                                                   dtstart=event_datetime)
                rrset.rrule(rrulestr)

                # Get first event that occurs before
                # and after the current time.
                event_datetime_after = rrset.after(current_datetime)
                event_datetime_before = rrset.before(current_datetime)

            except Exception:
                logging.exception("[%s] Not able to parse rrule for '%s'."
                                  % (self.fileName, event.get("SUMMARY")))

            # Process the event alarms for the first event occurring after the
            # current time.
            if event_datetime_after:

                self._process_event_alarms(event, event_datetime_after)

            # Process the event alarms for the first event occurring before the
            # current time (needed because of edge cases with alarms 0 seconds
            # before event). But only check event if it is not older than
            # 10 minutes.
            if event_datetime_before:
                if (event_datetime_before >=
                   (current_datetime - self.timedelta10min)):
                    self._process_event_alarms(event, event_datetime_before)

        # Process "normal" events.
        else:
            # Check if the event is in the past (minus 10 minutes).
            if event_datetime <= (current_datetime - self.timedelta10min):
                return

            self._process_event_alarms(event, event_datetime)

    # Processes each reminder/alarm of an event.
    def _process_event_alarms(self, event: icalendar.cal.Event, event_datetime: datetime.datetime):

        # Create current datetime object.
        current_datetime = datetime.datetime.fromtimestamp(time.time(), datetime.timezone.utc)

        for alarm in event.walk("VALARM"):

            if "TRIGGER" in alarm:

                # Get time delta when reminder is triggered.
                trigger = alarm.get("TRIGGER")

                # Get time when reminder is triggered.
                # When trigger time is a delta, then calculate the actual time.
                if type(trigger.dt) == datetime.timedelta:
                    trigger_datetime = event_datetime + trigger.dt

                # When trigger time is an actual time, use this.
                elif type(trigger.dt) == datetime.datetime:
                    trigger_datetime = trigger.dt

                    # Use the same timezone as the event when
                    # no is given.
                    if trigger_datetime.tzinfo is None:
                        trigger_datetime = trigger_datetime.replace(
                                                tzinfo=event_datetime.tzinfo)

                # When trigger time is only a date, start at midnight,
                # however, use the same timezone as the event.
                elif type(trigger.dt) == datetime.date:
                    trigger_utc_time = calendar.timegm(trigger.dt.timetuple())
                    trigger_datetime = datetime.datetime.utcfromtimestamp(trigger_utc_time)
                    # Since we just overwrite the timezone here, we do not
                    # care about conversion from UTC since the new datetime
                    # object starts at midnight in the given timezone.
                    trigger_datetime = trigger_datetime.replace(
                                                tzinfo=event_datetime.tzinfo)

                else:
                    logging.error("[%s] Error: Do not know how to handle "
                                  % self.fileName
                                  + "trigger type '%s'."
                                  % trigger.dt.__class__)
                    continue

                # Uid of event is needed.
                uid = event.get("UID")

                # Check if we already triggered an alarm for the event
                # with this uid and the given alarm trigger time.
                if (uid, trigger_datetime) in self.alreadyTriggered:
                    break

                # Check if the alarm trigger time lies in the past but not
                # more than 1 day.
                if(current_datetime - self.timedelta1day) <= trigger_datetime <= current_datetime:

                    title = event.get("SUMMARY")

                    # Get description if event has one.
                    ev_description = ""
                    if "DESCRIPTION" in event:
                        ev_description = event.get("DESCRIPTION")

                    # Get location if event has one.
                    location = ""
                    if "LOCATION" in event:
                        location = event.get("LOCATION")

                    # Create the utc unix timestamp for the start of the event.
                    unix_start = datetime.datetime.fromtimestamp(0, datetime.timezone.utc)

                    utc_dtstart = int((event_datetime - unix_start).total_seconds())

                    # Create the utc unix timestamp for the reminder trigger.
                    utc_trigger = int((trigger_datetime - unix_start).total_seconds())

                    event_date_str = time.strftime("%D %H:%M:%S", time.localtime(utc_dtstart))
                    msg = "Reminder for event '%s' at %s" % (title, event_date_str)

                    # Create sensor alert.
                    sensor_alert = SensorObjSensorAlert()
                    sensor_alert.clientSensorId = self.id
                    sensor_alert.state = 1
                    sensor_alert.hasOptionalData = True
                    sensor_alert.optionalData = {"message": msg,
                                                 "calendar": self.name,
                                                 "type": "reminder",
                                                 "title": title,
                                                 "description": ev_description,
                                                 "location": location,
                                                 "trigger": utc_trigger,
                                                 "start": utc_dtstart}
                    sensor_alert.changeState = False
                    sensor_alert.hasLatestData = False
                    sensor_alert.dataType = SensorDataType.NONE

                    self.reminderAlertQueue.put(sensor_alert)

                    # Store the event uid and the alarm trigger time
                    # as already triggered.
                    self.alreadyTriggered.add((uid, trigger_datetime))

    def initializeSensor(self):
        self.changeState = False
        self.hasLatestData = False
        self.state = 1 - self.triggerState

        # Set htaccess authentication object.
        if self.htaccessAuth == "BASIC":
            # noinspection PyUnresolvedReferences
            self.htaccessData = requests.auth.HTTPBasicAuth(self.htaccessUser, self.htaccessPass)
        elif self.htaccessAuth == "DIGEST":
            # noinspection PyUnresolvedReferences
            self.htaccessData = requests.auth.HTTPDigestAuth(self.htaccessUser, self.htaccessPass)
        elif self.htaccessAuth == "NONE":
            self.htaccessData = None
        else:
            return False

        # Get first calendar data.
        self._get_calendar()

        return True

    def getState(self) -> int:
        return self.state

    def updateState(self):

        # Check if we have to collect new calendar data.
        utc_timestamp = int(time.time())
        if (utc_timestamp - self.lastFetch) > self.intervalFetch:

            # Update calendar data in a non-blocking way
            # (this means also, that the current state will not be processed
            # on the updated data, but one of the next rounds will have it)
            thread = threading.Thread(target=self._get_calendar)
            thread.start()

            logging.debug("[%s] Number of remaining already "
                          % self.fileName
                          + "triggered elements: %d"
                          % len(self.alreadyTriggered))

        # Process calendar data for occurring reminder.
        if (utc_timestamp - self.lastProcess) > self.intervalProcess:
            self._process_calendar()

        # Clean up already triggered alerts.
        for triggeredTuple in list(self.alreadyTriggered):
            trigger_datetime = triggeredTuple[1]

            timezone = trigger_datetime.tzinfo
            current_datetime = datetime.datetime.fromtimestamp(time.time(), timezone)
            if (current_datetime - self.timedelta2day) >= trigger_datetime:
                self.alreadyTriggered.remove(triggeredTuple)

    def forceSendAlert(self) -> Optional[SensorObjSensorAlert]:

        # Check if we have exceeded the threshold of failed calendar
        # retrieval attempts and create a sensor alert if we have.
        sensor_alert = None
        if not self.inFailedState and self.failedCounter > self.maxFailedAttempts:

            logging.warning("[%s] Triggering sensor alert for "
                            % self.fileName
                            + "'%d' failed calendar fetching attempts."
                            % self.failedCounter)

            sensor_alert = SensorObjSensorAlert()
            sensor_alert.clientSensorId = self.id
            sensor_alert.state = 1
            sensor_alert.hasOptionalData = True
            msg = "Failed more than %d times for '%s' " \
                  % (self.maxFailedAttempts, self.name) \
                  + "to retrieve calendar data."
            sensor_alert.optionalData = {"message": msg,
                                         "calendar": self.name,
                                         "type": "timeout"}
            sensor_alert.changeState = True
            sensor_alert.hasLatestData = False
            sensor_alert.dataType = SensorDataType.NONE

            self.state = self.triggerState
            self.inFailedState = True

        # If we are in a failed retrieval state and we could retrieve
        # calendar data again trigger a sensor alert for "normal".
        elif self.inFailedState and self.failedCounter <= self.maxFailedAttempts:

            logging.warning("[%s] Fetching calendar succeeded after "
                            % self.fileName
                            + "multiple failed attempts. Triggering sensor alert.")

            sensor_alert = SensorObjSensorAlert()
            sensor_alert.clientSensorId = self.id
            sensor_alert.state = 0
            sensor_alert.hasOptionalData = True
            msg = "Calendar data for '%s' retrievable again." % self.name
            sensor_alert.optionalData = {"message": msg,
                                         "calendar": self.name,
                                         "type": "timeout"}
            sensor_alert.changeState = True
            sensor_alert.hasLatestData = False
            sensor_alert.dataType = SensorDataType.NONE

            self.state = 1 - self.triggerState
            self.inFailedState = False

        # If we have sensor alerts of reminder waiting
        # return the oldest of them.
        elif not self.reminderAlertQueue.empty():
            try:
                sensor_alert = self.reminderAlertQueue.get(True, 2)

            except Exception:
                pass

        return sensor_alert

    def forceSendState(self) -> Optional[SensorObjStateChange]:
        return None
