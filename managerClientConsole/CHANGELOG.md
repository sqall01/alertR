## 1.000-0

* Added sensor error states

## 0.901-0

* Added configuration option to disable TLS for testing purposes

## 0.900-0

* Added GPS data processing support
* Refactored sensor data processing

## 0.800-1

* Improved receiving data

## 0.800-0

* Fixed bug for detailed view if no "Alert Level/Alert/Sensor" existed
* Updater can show changelog
* Removed system status "activated" and "deactivated" to have a more generic system
* Introduced system profiles to replace system status to have a more generic system
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

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.
* Search feature for sensors, alertLevels, alerts, and managers added

## 0.500-1

* Changed timeout setting in order to have a more stable connection recovery.

## 0.400-1

* User paths can now be relative paths.
* Added start up log entries.

## 0.400-0

* Rewritten GUI to be more interactive.
* New detailed view of single elements that show the configuration and connections to other elements.
* Added persistent/non-persistent flag.

## 0.300-0

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Authentication message now contains version and revision.
* Alert system update messages to manager clients now contain version, revision and client instance.
* Shows if sensor alert was received for a "triggered" or "normal" state.
* Sorts displayed sensors, alert clients and manager clients.
