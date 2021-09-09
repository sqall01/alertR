## 0.900-0

* Added GPS data processing support

## 0.800-1

* Improved receiving data

## 0.800-0

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
* Guarantee that requests are send to server in timely order.
* Removed clientTime/serverTime from messages.
* Introduced msgTime into messages to check expiration.
* Removed storing of events on manager database (long term plan is to move event creation to server)

## 0.600-2

* Fixed redirection bug in updater/installer

## 0.600-1

* Added symlink support to updater/installer to make maintaining repository easier
* Added repository version and repository compatibility list to updater/installer 

## 0.600-0

* Migration from Python 2.7 to Python 3.5
* Permissions check for config file

## 0.501-3

* Update "force" switch now ignores dependency check.

## 0.501-2

* Fixed problem with starting the version fetching process even if updates are deactivated.

## 0.501-1

* Removed fixed TLS version.

## 0.501-0

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.

## 0.500-1

* Changed timeout setting in order to have a more stable connection recovery.

## 0.400-1

* User paths can now be relative paths.
* Added start up log entries.

## 0.400-0

* Streamlined database layout.
* Added persistent/non-persistent flag.

## 0.300-0

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Authentication message now contains version and revision.
* Alert system update messages to manager clients now contain version, revision and client instance.
* Checks (when online update check is activated) the version of all available instances in the online repository with the version of the used instances.
* Added option to give the amount of days that a sensor alert is kept in the database.
* Added option to configure the use of the local unix socket server instance.
* Added option to give the amount of days that a event is kept in the database.
* Added event log (an event is anything that has happened on the alert system for example a sensor alert, a state change of an sensor, an option change etc.).
* Renamed client to alertR Manager Client Database.
