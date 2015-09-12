This file only contains major changes with respect to the alertR system. Please refer to the CHANGELOG.md files of the components to see the changes in more detail.


## 0.300

Features:

* sensor alert messages distinguish now between state "triggered" and "normal"
* authentication message now contains version and revision
* alert system update messages to manager clients now contain version, revision and client instance
* renamed "alertR Sensor Client CTF Watchdog" to "alertR Sensor Client Executer" and updated code to allow a variable number of arguments for the scripts
* renamed "alertR Manger Client Mobile" to "alertR Manager Client Database" and updated code to log events, check instance versions against only repository and redefined UNIX socket protocol
* moved "alertR Mobile Manager" (web page and android app) to "alertR Web Mobile Manager" and completely rewrote web page (new design, displays sensor alert information, displays log event information, displays when a new alertR version is available, ...) - needs "alertR Manager Client Database" to work
* alertR server can now participate in a survey