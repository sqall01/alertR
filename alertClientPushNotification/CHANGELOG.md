## 0.800-0

* Updater can show changelog
* Only execute Sensor Alert once if it is for multiple Alert Levels that intersect with the Alert Levels of the configured Alert
* Removed sensor alerts off message
* Added system profile change message
* Check permissions of client key file

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

## 0.501-3

* Update "force" switch now ignores dependency check.

## 0.501-2

* Moved push notification component to lightweightpush pip package.

## 0.501-1

* Removed fixed TLS version.

## 0.501-0

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.

## 0.500-1

* Added channel prefixing in order to reduce channel collisions.
* Added message truncation if it is too long.
* Changed timeout setting in order to have a more stable connection recovery.

## 0.500-0

* Initial commit of this instance.
