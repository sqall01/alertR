## 1.000-0

* Added sensor error states
* Added persistent/non-persistent client configuration

## 0.901-2

* Added sanity checks during sensor initialization

## 0.901-1

* Updated logging of sensor messages

## 0.901-0

* Added configuration option to disable TLS for testing purposes

## 0.900-0

* Added GPS data processing support
* Refactored sensor data processing

## 0.800-2

* Refactoring sensor processing

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

## 0.503-1

* Update "force" switch now ignores dependency check.

## 0.503-0

* Added new provider (DarkSky) because of problems with wunderground as provider (deactivation of API?).

## 0.502-2

* Added further logging in case of error.

## 0.502-1

* Removed fixed TLS version.

## 0.502-0

* Removed unnecessary triggerState and moved it to individual sensor when necessary.

## 0.501-1

* Added optional data to sensor alert.

## 0.501-0

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.

## 0.500-1

* Changed timeout setting in order to have a more stable connection recovery.

## 0.401-0

* Added thresholds to sensors in order to be able to trigger a sensor alert.

## 0.400-0

* Initial commit of this instance.
* User paths can now be relative paths.
