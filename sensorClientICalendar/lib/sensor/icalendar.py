#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import os
import time
import icalendar
import datetime
import dateutil
import requests
import threading
import calendar
from .core import _PollingSensor
from ..globalData.sensorObjects import SensorDataType, SensorDataNone, SensorErrorState


# Class that controls one icalendar.
class ICalendarSensor(_PollingSensor):

    def __init__(self):
        _PollingSensor.__init__(self)

        # Set sensor to not hold any data.
        # NOTE: Can be changed if "parseOutput" is set to true in the
        # configuration file.
        self.sensorDataType = SensorDataType.NONE
        self.data = SensorDataNone()

        # used for logging
        self._log_tag = os.path.basename(__file__)

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
        self._failed_counter = 0
        self._max_failed_attempts = 10

        # Locks calendar data in order to be thread safe.
        self._icalendar_lock = threading.Lock()

        # Time when the data was fetched.
        self._last_fetch = 0

        # Time when the data was processed.
        self._last_process = 0

        # iCalendar data object.
        self._icalendar = None

        # Timeout for HTTP connections.
        self._connection_timeout = 60.0

        # Set of tuples that describe reminders that were already triggered.
        self._already_triggered = set()

        # Time deltas needed for calculations.
        self._time_delta_10min = datetime.timedelta(minutes=10)
        self._time_delta_1day = datetime.timedelta(days=1)
        self._time_delta_2day = datetime.timedelta(days=2)

    def _execute(self):

        while True:

            time.sleep(0.5)

            if self._exit_flag:
                return

            # Check if we have to collect new calendar data.
            utc_timestamp = int(time.time())
            if (utc_timestamp - self._last_fetch) > self.intervalFetch:

                # Update calendar data in a non-blocking way
                # (this means also, that the current state will not be processed
                # on the updated data, but one of the next rounds will have it)
                thread = threading.Thread(target=self._get_calendar)
                thread.start()

                self._log_debug(self._log_tag, "Number of remaining already triggered elements: %d"
                                % len(self._already_triggered))

            # Process calendar data for occurring reminder.
            if (utc_timestamp - self._last_process) > self.intervalProcess:
                self._process_calendar()

            # Clean up already triggered alerts.
            for triggeredTuple in list(self._already_triggered):
                trigger_datetime = triggeredTuple[1]

                timezone = trigger_datetime.tzinfo
                current_datetime = datetime.datetime.fromtimestamp(time.time(), timezone)
                if (current_datetime - self._time_delta_2day) >= trigger_datetime:
                    self._already_triggered.remove(triggeredTuple)

            # If we have too many failed attempts to retrieve new calendar data, set error state.
            if self.error_state.state == SensorErrorState.OK and self._failed_counter > self._max_failed_attempts:
                self._set_error_state(SensorErrorState.ConnectionError,
                                      "Failed more than %d times to retrieve calendar data."
                                      % self._max_failed_attempts)
                self._log_warning(self._log_tag, "Fetching calendar failed for %d attempts." % self._failed_counter)

            # If we have an error state that is not-OK and we could retrieve
            # new calendar data again, clear error state.
            elif self.error_state.state != SensorErrorState.OK and self._failed_counter <= self._max_failed_attempts:
                self._clear_error_state()
                self._log_warning(self._log_tag, "Fetching calendar succeeded after multiple failed attempts.")

    # Collect calendar data from the server.
    def _get_calendar(self):

        # Update time.
        utc_timestamp = int(time.time())
        self._last_fetch = utc_timestamp

        self._log_debug(self._log_tag, "Retrieving calendar data from '%s'." % self.location)

        # Request data from server.
        request = None
        try:
            request = requests.get(self.location, verify=True, auth=self.htaccessData, timeout=self._connection_timeout)

        except Exception:
            self._log_exception(self._log_tag, "Could not get calendar data from server.")
            self._failed_counter += 1
            return

        # Check status code.
        if request.status_code != 200:
            self._log_error(self._log_tag, "Server responded with wrong status code: %d" % request.status_code)
            self._failed_counter += 1
            return

        # Parse calendar data.
        temp_cal = None
        try:
            temp_cal = icalendar.Calendar.from_ical(request.content)

        except Exception:
            self._log_exception(self._log_tag, "Could not parse calendar data.")
            self._failed_counter += 1
            return

        # Move copy icalendar object to final object.
        with self._icalendar_lock:
            self._icalendar = temp_cal

        # Reset fail counter.
        self._failed_counter = 0

    # Process the calendar data if we have a reminder triggered.
    def _process_calendar(self):

        self._last_process = int(time.time())

        with self._icalendar_lock:
            if self._icalendar is None:
                return

            for event in self._icalendar.walk("VEVENT"):

                if event.is_empty():
                    continue

                if "DTSTART" not in event or "SUMMARY" not in event:
                    continue

                # Process the vent.
                self._process_event(event)

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
            self._log_debug(self._log_tag, "Do not know how to handle type '%s' of event start." % dtstart.dt.__class__)
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
                self._log_exception(self._log_tag, "Not able to parse rrule for '%s'." % event.get("SUMMARY"))

            # Process the event alarms for the first event occurring after the current time.
            if event_datetime_after:
                self._process_event_alarms(event, event_datetime_after)

            # Process the event alarms for the first event occurring before the
            # current time (needed because of edge cases with alarms 0 seconds
            # before event). But only check event if it is not older than 10 minutes.
            if event_datetime_before:
                if event_datetime_before >= (current_datetime - self._time_delta_10min):
                    self._process_event_alarms(event, event_datetime_before)

        # Process "normal" events.
        else:
            # Check if the event is in the past (minus 10 minutes).
            if event_datetime <= (current_datetime - self._time_delta_10min):
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
                        trigger_datetime = trigger_datetime.replace(tzinfo=event_datetime.tzinfo)

                # When trigger time is only a date, start at midnight,
                # however, use the same timezone as the event.
                elif type(trigger.dt) == datetime.date:
                    trigger_utc_time = calendar.timegm(trigger.dt.timetuple())
                    trigger_datetime = datetime.datetime.utcfromtimestamp(trigger_utc_time)
                    # Since we just overwrite the timezone here, we do not
                    # care about conversion from UTC since the new datetime
                    # object starts at midnight in the given timezone.
                    trigger_datetime = trigger_datetime.replace(tzinfo=event_datetime.tzinfo)

                else:
                    self._log_error(self._log_tag, "Do not know how to handle trigger type '%s'."
                                    % trigger.dt.__class__)
                    continue

                # Uid of event is needed.
                uid = event.get("UID")

                # Check if we already triggered an alarm for the event
                # with this uid and the given alarm trigger time.
                if (uid, trigger_datetime) in self._already_triggered:
                    break

                # Check if the alarm trigger time lies in the past but not
                # more than 1 day.
                if(current_datetime - self._time_delta_1day) <= trigger_datetime <= current_datetime:

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

                    optional_data = {"message": msg,
                                     "calendar": self.name,
                                     "type": "reminder",
                                     "title": title,
                                     "description": ev_description,
                                     "location": location,
                                     "trigger": utc_trigger,
                                     "start": utc_dtstart}
                    self._add_sensor_alert(self.triggerState,
                                           False,
                                           optional_data)

                    # Store the event uid and the alarm trigger time
                    # as already triggered.
                    self._already_triggered.add((uid, trigger_datetime))

    def initialize(self) -> bool:
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
