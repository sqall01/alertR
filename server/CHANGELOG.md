## 0.800-2

* Fixed error in initial state handling of version informer internal sensor

## 0.800-1

* Removed `triggeredAlertLevels` from instrumentation script argument since they do not hold any information value at this point

## 0.800-0

* Updater can show changelog
* Removed system status "activated" and "deactivated" to have a more generic system
* Introduced system profiles to replace system status to have a more generic system
* Removed sensor alerts off message
* Added system profile change message
* Refactored option message handling
* Removed `triggerAlways` flag for Alert Levels (same behavior can now be achieved by being part of all profiles)
* Removed Sensor Alerts from database (use internal in-memory queue for Sensor Alert processing instead)
* Check permissions of server key file
* Renamed remoteSensorId to clientSensorId to have a more sane naming convention
* Renamed remoteAlertId to clientAlertId to have a more sane naming convention
* Changed options value from float to int

## 0.700-0

* Removed rules from Alert Levels and replaced it with instrumentation (more flexible form to achieve the same).
* Removed clientTime/serverTime from messages.
* Introduced msgTime into messages to check expiration.

## 0.600-3

* Fixed redirection bug in updater/installer

## 0.600-2

* Added symlink support to updater/installer to make maintaining repository easier
* Added repository version and repository compatibility list to updater/installer 

## 0.600-1

* Added graphExport.py utility.

## 0.600-0

* Migration from Python 2.7 to Python 3.5
* Permissions check for config file
* Removed MySQL Backend

## 0.504-2

* Update "force" switch now ignores dependency check.

## 0.504-1

* Introducing database layout version in order to make updates easier.

## 0.504-0

* Make TLS/SSL Options configurable.
* Migrated survey to use requests and connect to 443 (instead of 444).

## 0.503-5

* Changed users.csv file format and added manageUsers.py script to manage users.
* Users can now be added and deleted at runtime (modifying requires shutdown beforehand).

## 0.503-4

* Only send sensor alert messages to clients that actually handles the triggered alert level.

## 0.503-3

* Added optional data to sensor alert.

## 0.503-2

* Bugfix: Revision of server node was not updated in database.

## 0.503-0

* Removed smtp functionality.
* Added internal sensor for version checks.
* Update process checks dependency changes and can delete old files.

## 0.502-0

* Making internal sensor description available for configuration.
* Adding optional data to internal sensor alerts.

## 0.501-0

* Added alert system state as an internal sensor in order to generate sensor alerts if alert system changes state (activated/deactivated).

## 0.500-1

* Changed timeout setting in order to have a more stable connection recovery.
* Fixed problem with multiple log entries.

## 0.400-1

* User paths can now be relative paths.

## 0.400-0

* Username, remoteSensorId and remoteAlertId transmitted to manager clients.
* Sensor alert messages transfer information if it should change the state of the sensor.
* Server has internal sensors that can trigger on internal events (at the moment sensor timeout, client timeout).
* Changed logging system to have separated log files for each client connection.
* Removed eMail notification option in alertLevels (is now moved to a separate alert client with eMail templating).

## 0.300-0

* Sensor alert messages distinguish now between state "triggered" and "normal"
* Authentication message now contains version and revision.
* users.csv now also contains type of client and instance of client and checks it during the authentication phase.
* Alert levels have the option to filter out sensor alert messages that were sent for sensors going to the "normal" state.
* Alert levels have the option to filter out sensor alert messages that were sent for sensors going to the "triggered" state.
* Server can now participate in a survey.
