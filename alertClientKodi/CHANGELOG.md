## 0.600

Features:

* Migration from Python 2.7 to Python 3.5
* Added separated sensor alert message handling (distinguish between "triggered" and "normal" state)


## 0.501-2

Features:

* Update "force" switch now ignores dependency check.


## 0.501-1

Features:

* Removed fixed TLS version.


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

* Added persistent/non-persistent flag.


## 0.300

Features:

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Displays if a sensor alert was raised for state "triggered" or "normal".
* Authentication message now contains version and revision.
