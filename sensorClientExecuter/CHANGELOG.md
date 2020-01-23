## 0.600

Features:

* Migration from Python 2.7 to Python 3.5


## 0.503-2

Features:

* Update "force" switch now ignores dependency check.


## 0.503-1

Features:

* Removed fixed TLS version.


## 0.503

Features:

* Removed unnecessary triggerState and moved it to individual sensor when necessary.


## 0.502-2

Features:

* Added optional data to sensor alert.


## 0.502-1

Features:

* Logging of command stdout/stderr whenever it fails.


## 0.502

Features:

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.


### 0.501

Features:

* IntervalToCheck has to be larger than timeout value.
* Parses output of executed command (if wanted).


## 0.500-1

Features:

* Changed timeout setting in order to have a more stable connection recovery.


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