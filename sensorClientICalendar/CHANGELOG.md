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

## 0.501-2

Features:

* Update "force" switch now ignores dependency check.

## 0.501-1

Features:

* Removed fixed TLS version.

## 0.501-0

Features:

* Renamed `interval` to `intervalFetch`.
* Added `intervalProcess` to reduce CPU load.

## 0.500-1

Features:

* Fixed issue with whole day events and local time.

## 0.500-0

Features:

* Initial release.
