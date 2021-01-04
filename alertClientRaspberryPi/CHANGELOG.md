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
* Added separated sensor alert message handling (distinguish between "triggered" and "normal" state)

## 0.502-1

* Update "force" switch now ignores dependency check.

## 0.502-0

* Added `gpioResetStateTime` option that can reset the triggered alert to normal state after given time.

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

* Added persistent/non-persistent flag.

## 0.300-0

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Authentication message now contains version and revision.
