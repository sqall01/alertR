## 0.700-0

Features:

* Refactored client code to get a more resilient connection.
* Unified client code to make it more maintainable.
* Guarantee that requests are send to server in timely order.
* Removed clientTime/serverTime from messages.
* Introduced msgTime into messages to check expiration.

## 0.600-2

Features:

* Fixed redirection bug in updater/installer

## 0.600-1

Features:

* Added symlink support to updater/installer to make maintaining repository easier
* Added repository version and repository compatibility list to updater/installer 

## 0.600-0

Features:

* Migration from Python 2.7 to Python 3.5
* Permissions check for config file

## 0.502-3

Features:

* Update "force" switch now ignores dependency check.

## 0.502-2

Features:

* Replaced sound files.

## 0.502-1

Features:

* Removed fixed TLS version.

## 0.502-0

Features:

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.

## 0.501-1

Features:

* Changed timeout setting in order to have a more stable connection recovery.

## 0.501-0

Features:

* Play silent option as a workaround for HDMI sound delay.

## 0.400-1

Features:

* User paths can now be relative paths.
* Added start up log entries.

## 0.400-0

Features:

* Client is now able to play sounds in certain situations.
* Client can now check if sensors are in a certain state and ask the user for confirmation before sending an alarm system activation message to the server (sensors and state are configurable in the configuration file of this client).
* Added persistent/non-persistent flag.

## 0.300-0

Features:

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Authentication message now contains version and revision.
* Alert system update messages to manager clients now contain version, revision and client instance.
