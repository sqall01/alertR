## 0.700-0

Features:

* Refactored client code to get a more resilient connection.
* Unified client code to make it more maintainable.
* Guarantee that requests are send to server in timely order.

## 0.600-2

Features:

* Fixed redirection bug in updater/installer
* Fixed interrupt counting

## 0.600-1

Features:

* Added symlink support to updater/installer to make maintaining repository easier
* Added repository version and repository compatibility list to updater/installer 


## 0.600

Features:

* Migration from Python 2.7 to Python 3.5
* Permissions check for config file


## 0.503-1

Features:

* Update "force" switch now ignores dependency check.


## 0.503-0

Features:

* Counter for state reads for the PollingSensor in order to compensate insufficiently isolated wiring.


## 0.502-1

Features:

* Removed fixed TLS version.


## 0.502

Features:

* Removed unnecessary triggerState and moved it to individual sensor when necessary.


## 0.501-1

Features:

* Added optional data to sensor alert for DS18b20 sensor.


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

* Added ds18b20 temperature sensor.
* Added persistent/non-persistent flag (sensor clients always persistent).


## 0.300

Features:

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Added option to trigger a sensor alert when sensor goes back from the "triggered" state to the "normal" state.
* Authentication message now contains version and revision.