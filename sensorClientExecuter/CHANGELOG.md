## 0.400-1

Features:

* User paths can now be relative paths.
* Added start up log entries.


## 0.400

Features:

* Added persistent/non-persistent flag (sensor clients always persistent).


## 0.300

Features:

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Sends a message ("timeout") added to the sensor alert when executed script times out.
* Added option to trigger a sensor alert when sensor goes back from the "triggered" state to the "normal" state.
* Authentication message now contains version and revision.
* Renamed "alertR Sensor Client CTF Watchdog" to "alertR Sensor Client Executer" and updated code to allow a variable number of arguments for the scripts.