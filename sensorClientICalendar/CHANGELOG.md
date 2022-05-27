## 1.000-0

* Added sensor error states
* Added persistent/non-persistent client configuration

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

## 0.501-2

* Update "force" switch now ignores dependency check.

## 0.501-1

* Removed fixed TLS version.

## 0.501-0

* Renamed `interval` to `intervalFetch`.
* Added `intervalProcess` to reduce CPU load.

## 0.500-1

* Fixed issue with whole day events and local time.

## 0.500-0

* Initial release.
