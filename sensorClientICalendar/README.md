# AlertR Sensor Client iCalendar

This client handles calendar services as a sensor. For this, reminders in this calendar are used to trigger sensor alerts. Every calendar service that gives the option to retrieve the calendar data as .ics file via an URL can be used with this sensor client. For example, you can combine this sensor client with your Google calendar to generate sensor alerts every time a reminder is triggered. These sensor alerts can then be instrumented by AlertR to perform a certain task (e.g., display a message on your Kodi media center setup). Furthermore, this allows you to generate a schedule in your calender which then trigger certain tasks in your AlertR system.


## How to use it?

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).