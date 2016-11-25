This file only contains major changes with respect to the alertR system. Please refer to the CHANGELOG.md files of the instances to see the changes in more detail.

## 0.500

Features:

* Push notification client.


## 0.400

Features:

* Protocol header of RTS message got size field to enable variable message sizes.
* Added persistent/non-persistent flag.
* Sensor can hold data (at the moment none/integer/float).
* Username of nodes and remoteSensorId of sensors visible for manager clients.
* SensorAlert messages do not necessarily change the state of the sensor (can now be independent from the state).


## 0.300

Features:

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Authentication message now contains version and revision.
* Alert system update messages to manager clients now contain version, revision and client instance.
* Renamed "alertR Sensor Client CTF Watchdog" to "alertR Sensor Client Executer" and updated code to allow a variable number of arguments for the scripts.
* Renamed "alertR Manger Client Mobile" to "alertR Manager Client Database" and updated code to log events, check instance versions against only repository and redefined UNIX socket protocol.
* Moved "alertR Mobile Manager" (web page and android app) to "alertR Web Mobile Manager" and completely rewrote web page (new design, displays sensor alert information, displays log event information, displays when a new alertR version is available, ...) - needs "alertR Manager Client Database" to work.
* AlertR server can now participate in a survey.