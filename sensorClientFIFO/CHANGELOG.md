## 0.600

Features:

* Migration from Python 2.7 to Python 3.5


## 0.502-3

Features:

* Update "force" switch now ignores dependency check.


## 0.502-1

Features:

* Removed fixed TLS version.


## 0.502

Features:

* Removed unnecessary triggerState and moved it to individual sensor when necessary.


## 0.501

Features:

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.


## 0.500-1

Features:

* Changed timeout setting in order to have a more stable connection recovery.


## 0.400-1

Features:

* User paths can now be relative paths.
* Added start up log entries.


## 0.400

Features:

* Changed FIFO sensor protocol.
* Added sensor data feature.
* Added persistent/non-persistent flag (sensor clients always persistent).


## 0.300

Features:

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Added option to trigger a sensor alert when sensor goes back from the "triggered" state to the "normal" state.
* Authentication message now contains version and revision.