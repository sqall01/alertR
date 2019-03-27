#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import time
import random
import os
import logging
import icalendar
import datetime
import dateutil
import requests
import threading
import Queue
import pytz
import calendar
from client import AsynchronousSender
from localObjects import SensorDataType, SensorAlert, StateChange


# Internal class that holds the important attributes
# for a sensor to work (this class must be inherited from the
# used sensor class).
class _PollingSensor:

    def __init__(self):

        # Id of this sensor on this client. Will be handled as
        # "remoteSensorId" by the server.
        self.id = None

        # Description of this sensor.
        self.description = None

        # Delay in seconds this sensor has before a sensor alert is
        # issued by the server.
        self.alertDelay = None

        # Local state of the sensor (either 1 or 0). This state is translated
        # (with the help of "triggerState") into 1 = "triggered" / 0 = "normal"
        # when it is send to the server.
        self.state = None

        # State the sensor counts as triggered (either 1 or 0).
        self.triggerState = None

        # A list of alert levels this sensor belongs to.
        self.alertLevels = list()

        # Flag that indicates if this sensor should trigger a sensor alert
        # for the state "triggered" (true or false).
        self.triggerAlert = None

        # Flag that indicates if this sensor should trigger a sensor alert
        # for the state "normal" (true or false).
        self.triggerAlertNormal = None

        # The type of data the sensor holds (i.e., none at all, integer, ...).
        # Type is given by the enum class "SensorDataType".
        self.sensorDataType = None

        # The actual data the sensor holds.
        self.sensorData = None

        # Flag indicates if this sensor alert also holds
        # the data the sensor has. For example, the data send
        # with this alarm message could be the data that triggered
        # the alarm, but not necessarily the data the sensor
        # currently holds. Therefore, this flag indicates
        # if the data contained by this message is also the
        # current data of the sensor and can be used for example
        # to update the data the sensor has.
        self.hasLatestData = None

        # Flag that indicates if a sensor alert that is send to the server
        # should also change the state of the sensor accordingly. This flag
        # can be useful if the sensor watches multiple entities. For example,
        # a timeout sensor could watch multiple hosts and has the state
        # "triggered" when at least one host has timed out. When one host
        # connects back and still at least one host is timed out,
        # the sensor can still issue a sensor alert for the "normal"
        # state of the host that connected back, but the sensor
        # can still has the state "triggered".
        self.changeState = None

        # Optional data that can be transfered when a sensor alert is issued.
        self.hasOptionalData = False
        self.optionalData = None

        # Flag indicates if the sensor changes its state directly
        # by using forceSendAlert() and forceSendState() and the SensorExecuter
        # should ignore state changes and thereby not generate sensor alerts.
        self.handlesStateMsgs = False


    # this function returns the current state of the sensor
    def getState(self):
        raise NotImplementedError("Function not implemented yet.")


    # this function updates the state variable of the sensor
    def updateState(self):
        raise NotImplementedError("Function not implemented yet.")


    # This function initializes the sensor.
    #
    # Returns True or False depending on the success of the initialization.
    def initializeSensor(self):
        raise NotImplementedError("Function not implemented yet.")


    # This function decides if a sensor alert for this sensor should be sent
    # to the server. It is checked regularly and can be used to force
    # a sensor alert despite the state of the sensor has not changed.
    #
    # Returns an object of class SensorAlert if a sensor alert should be sent
    # or None.
    def forceSendAlert(self):
        raise NotImplementedError("Function not implemented yet.")


    # This function decides if an update for this sensor should be sent
    # to the server. It is checked regularly and can be used to force an update
    # of the state and data of this sensor to be sent to the server.
    #
    # Returns an object of class StateChange if a sensor alert should be sent
    # or None.
    def forceSendState(self):
        raise NotImplementedError("Function not implemented yet.")


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
        self.reminderAlertQueue = Queue.Queue()

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

            if not event.has_key("DTSTART") or not event.has_key("SUMMARY"):
                continue

            # Process the vent.
            self._processEvent(event)

        self.icalendarLock.release()


    # Processes an event of a calendar.
    def _processEvent(self, event):

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
        if event.has_key("RRULE"):

            eventRule = event.get("RRULE")

            if eventRule.has_key("UNTIL"):
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

                rrulestr = dateutil.rrule.rrulestr(eventRule.to_ical(),
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
    def _processEventAlarms(self, event, eventDatetime):

        # Create current datetime object.
        currentUTCTime = time.time()
        currentDatetime = datetime.datetime.utcfromtimestamp(currentUTCTime)
        currentDatetime = currentDatetime.replace(tzinfo=pytz.UTC)

        for alarm in event.walk("VALARM"):

            if alarm.has_key("TRIGGER"):

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
                    if event.has_key("DESCRIPTION"):
                        evDescription = event.get("DESCRIPTION")

                    # Get location if event has one.
                    location = ""
                    if event.has_key("LOCATION"):
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
                    msg = "Reminder for event '%s' at %s" \
                        % (title, eventDateStr)

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
            self.htaccessData = requests.auth.HTTPBasicAuth(self.htaccessUser,
                self.htaccessPass)
        elif self.htaccessAuth == "DIGEST":
            self.htaccessData = requests.auth.HTTPDigestAuth(self.htaccessUser,
                self.htaccessPass)
        elif self.htaccessAuth == "NONE":
            self.htaccessData = None
        else:
            return False

        # Get first calendar data.
        self._getCalendar()

        return True


    def getState(self):
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


    def forceSendAlert(self):

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
            msg = "Calendar data for '%s' retrievable again." \
                % self.name
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


    def forceSendState(self):
        return None


# this class polls the sensor states and triggers alerts and state changes
class SensorExecuter:

    def __init__(self, globalData):
        self.fileName = os.path.basename(__file__)
        self.globalData = globalData
        self.connection = self.globalData.serverComm
        self.sensors = self.globalData.sensors

        # Flag indicates if the thread is initialized.
        self._isInitialized = False


    def isInitialized(self):
        return self._isInitialized


    def execute(self):

        # time on which the last full sensor states were sent
        # to the server
        lastFullStateSent = 0

        # Get reference to server communication object.
        while self.connection is None:
            time.sleep(0.5)
            self.connection = self.globalData.serverComm

        self._isInitialized = True

        while True:

            # check if the client is connected to the server
            # => wait and continue loop until client is connected
            if not self.connection.isConnected():
                time.sleep(0.5)
                continue

            # poll all sensors and check their states
            for sensor in self.sensors:

                oldState = sensor.getState()
                sensor.updateState()
                currentState = sensor.getState()

                # Check if a sensor alert is forced to send to the server.
                # => update already known state and continue
                sensorAlert = sensor.forceSendAlert()
                if sensorAlert:
                    oldState = currentState

                    asyncSenderProcess = AsynchronousSender(
                        self.connection, self.globalData)
                    # set thread to daemon
                    # => threads terminates when main thread terminates 
                    asyncSenderProcess.daemon = True
                    asyncSenderProcess.sendSensorAlert = True
                    asyncSenderProcess.sendSensorAlertSensorAlert = sensorAlert
                    asyncSenderProcess.start()

                    continue

                # check if the current state is the same
                # than the already known state => continue
                elif oldState == currentState:
                    continue

                # Check if we should ignore state changes and just let
                # the sensor handle sensor alerts by using forceSendAlert()
                # and forceSendState().
                elif sensor.handlesStateMsgs:
                    continue

                # check if the current state is an alert triggering state
                elif currentState == sensor.triggerState:

                    # check if the sensor triggers a sensor alert
                    # => send sensor alert to server
                    if sensor.triggerAlert:

                        logging.info("[%s]: Sensor alert " % self.fileName
                            + "triggered by '%s'." % sensor.description)

                        # Create sensor alert object to send to the server.
                        sensorAlert = SensorAlert()
                        sensorAlert.clientSensorId = sensor.id
                        sensorAlert.state = 1
                        sensorAlert.hasOptionalData = sensor.hasOptionalData
                        sensorAlert.optionalData = sensor.optionalData
                        sensorAlert.changeState = sensor.changeState
                        sensorAlert.hasLatestData = sensor.hasLatestData
                        sensorAlert.dataType = sensor.sensorDataType
                        sensorAlert.sensorData = sensor.sensorData

                        asyncSenderProcess = AsynchronousSender(
                            self.connection, self.globalData)
                        # set thread to daemon
                        # => threads terminates when main thread terminates 
                        asyncSenderProcess.daemon = True
                        asyncSenderProcess.sendSensorAlert = True
                        asyncSenderProcess.sendSensorAlertSensorAlert = \
                            sensorAlert
                        asyncSenderProcess.start()

                    # if sensor does not trigger sensor alert
                    # => just send changed state to server
                    else:

                        logging.debug("[%s]: State " % self.fileName
                            + "changed by '%s'." % sensor.description)

                        # Create state change object to send to the server.
                        stateChange = StateChange()
                        stateChange.clientSensorId = sensor.id
                        stateChange.state = 1
                        stateChange.dataType = sensor.sensorDataType
                        stateChange.sensorData = sensor.sensorData

                        asyncSenderProcess = AsynchronousSender(
                            self.connection, self.globalData)
                        # set thread to daemon
                        # => threads terminates when main thread terminates 
                        asyncSenderProcess.daemon = True
                        asyncSenderProcess.sendStateChange = True
                        asyncSenderProcess.sendStateChangeStateChange = \
                            stateChange
                        asyncSenderProcess.start()

                # only possible situation left => sensor changed
                # back from triggering state to a normal state
                else:

                    # check if the sensor triggers a sensor alert when
                    # state is back to normal
                    # => send sensor alert to server
                    if sensor.triggerAlertNormal:

                        logging.info("[%s]: Sensor alert " % self.fileName
                            + "for normal state "
                            + "triggered by '%s'." % sensor.description)

                        # Create sensor alert object to send to the server.
                        sensorAlert = SensorAlert()
                        sensorAlert.clientSensorId = sensor.id
                        sensorAlert.state = 0
                        sensorAlert.hasOptionalData = sensor.hasOptionalData
                        sensorAlert.optionalData = sensor.optionalData
                        sensorAlert.changeState = sensor.changeState
                        sensorAlert.hasLatestData = sensor.hasLatestData
                        sensorAlert.dataType = sensor.sensorDataType
                        sensorAlert.sensorData = sensor.sensorData

                        asyncSenderProcess = AsynchronousSender(
                            self.connection, self.globalData)
                        # set thread to daemon
                        # => threads terminates when main thread terminates 
                        asyncSenderProcess.daemon = True
                        asyncSenderProcess.sendSensorAlert = True
                        asyncSenderProcess.sendSensorAlertSensorAlert = \
                            sensorAlert
                        asyncSenderProcess.start()

                    # if sensor does not trigger sensor alert when
                    # state is back to normal
                    # => just send changed state to server
                    else:

                        logging.debug("[%s]: State " % self.fileName
                            + "changed by '%s'." % sensor.description)

                        # Create state change object to send to the server.
                        stateChange = StateChange()
                        stateChange.clientSensorId = sensor.id
                        stateChange.state = 0
                        stateChange.dataType = sensor.sensorDataType
                        stateChange.sensorData = sensor.sensorData

                        asyncSenderProcess = AsynchronousSender(
                            self.connection, self.globalData)
                        # set thread to daemon
                        # => threads terminates when main thread terminates 
                        asyncSenderProcess.daemon = True
                        asyncSenderProcess.sendStateChange = True
                        asyncSenderProcess.sendStateChangeStateChange = \
                            stateChange
                        asyncSenderProcess.start()

            # Poll all sensors if they want to force an update that should
            # be send to the server.
            for sensor in self.sensors:

                stateChange = sensor.forceSendState()
                if stateChange:
                    asyncSenderProcess = AsynchronousSender(
                        self.connection, self.globalData)
                    # set thread to daemon
                    # => threads terminates when main thread terminates 
                    asyncSenderProcess.daemon = True
                    asyncSenderProcess.sendStateChange = True
                    asyncSenderProcess.sendStateChangeStateChange = stateChange
                    asyncSenderProcess.start()

            # check if the last state that was sent to the server
            # is older than 60 seconds => send state update
            utcTimestamp = int(time.time())
            if (utcTimestamp - lastFullStateSent) > 60:

                logging.debug("[%s]: Last state " % self.fileName
                    + "timed out.")

                asyncSenderProcess = AsynchronousSender(
                    self.connection, self.globalData)
                # set thread to daemon
                # => threads terminates when main thread terminates 
                asyncSenderProcess.daemon = True
                asyncSenderProcess.sendSensorsState = True
                asyncSenderProcess.start()

                # update time on which the full state update was sent
                lastFullStateSent = utcTimestamp
                
            time.sleep(0.5)