## 0.800-1

* Improved receiving data

## 0.800-0

* Updater can show changelog
* Check permissions of client key file
* Renamed remoteSensorId to clientSensorId to have a more sane naming convention
* Renamed remoteAlertId to clientAlertId to have a more sane naming convention
* Changed options value from float to int

## 0.700-0

* Refactored client code to get a more resilient connection.
* Unified client code to make it more maintainable.
* Guarantee that requests are send to server in timely order.
* Removed clientTime/serverTime from messages.
* Introduced msgTime into messages to check expiration.

## 0.600-2

* Fixed redirection bug in updater/installer

## 0.600-1

* Added symlink support to updater/installer to make maintaining repository easier
* Added repository version and repository compatibility list to updater/installer 

## 0.600-0

* Migration from Python 2.7 to Python 3.5
* Permissions check for config file

## 0.503-2

* Update "force" switch now ignores dependency check.

## 0.503-1

* Removed fixed TLS version.

## 0.503-0

* Removed unnecessary triggerState and moved it to individual sensor when necessary.

## 0.502-2

* Added optional data to sensor alert.

## 0.502-1

* Logging of command stdout/stderr whenever it fails.

## 0.502-0

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.

### 0.501-0

* IntervalToCheck has to be larger than timeout value.
* Parses output of executed command (if wanted).

## 0.500-1

* Changed timeout setting in order to have a more stable connection recovery.

## 0.400-1

* User paths can now be relative paths.
* Added start up log entries.

## 0.400-0

* Added persistent/non-persistent flag (sensor clients always persistent).

## 0.300-0

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Sends a message ("timeout") added to the sensor alert when executed script times out.
* Added option to trigger a sensor alert when sensor goes back from the "triggered" state to the "normal" state.
* Authentication message now contains version and revision.
* Renamed "alertR Sensor Client CTF Watchdog" to "alertR Sensor Client Executer" and updated code to allow a variable number of arguments for the scripts.
