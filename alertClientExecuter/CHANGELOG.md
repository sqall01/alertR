## 0.901-1

* Updated logging of alert messages

## 0.901-0

* Added configuration option to disable TLS for testing purposes

## 0.900-0

* Added GPS data processing support
* Refactored sensor data processing

## 0.800-2

* Improved receiving data

## 0.800-1

* Fixed missing optional data in json argument

## 0.800-0

* Updater can show changelog
* Only execute Sensor Alert once if it is for multiple Alert Levels that intersect with the Alert Levels of the configured Alert
* Removed sensor alerts off message
* Added system profile change message
* Removed sensor alerts off handling in configuration
* Added system profile change handling in configuration
* Check permissions of client key file
* Renamed remoteSensorId to clientSensorId to have a more sane naming convention
* Renamed remoteAlertId to clientAlertId to have a more sane naming convention
* Changed options value from float to int

## 0.700-0

* Refactored client code to get a more resilient connection.
* Unified client code to make it more maintainable.
* Guarantee that requests are sent to server in timely order.
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
* Added separated sensor alert message handling (distinguish between "triggered" and "normal" state)

## 0.501-3

* Update "force" switch now ignores dependency check.

## 0.501-2

* Removed fixed TLS version.

## 0.501-1

* Added option to pass the received sensor alert as json string to the argument.

## 0.501-0

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.

## 0.500-1

* Changed timeout setting in order to have a more stable connection recovery.

## 0.400-1

* User paths can now be relative paths.
* Added start up log entries.

## 0.400-0

* Added persistent/non-persistent flag.

## 0.300-0

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Authentication message now contains version and revision.
