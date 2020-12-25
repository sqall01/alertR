## 0.700-0

Features:

* Refactored client code to get a more resilient connection.
* Unified client code to make it more maintainable.

## 0.600-2

Features:

* Fixed redirection bug in updater/installer


## 0.600-1

Features:

* Added symlink support to updater/installer to make maintaining repository easier
* Added repository version and repository compatibility list to updater/installer 


## 0.600

Features:

* Migration from Python 2.7 to Python 3.5
* Permissions check for config file


## 0.503-1

Features:

* Update "force" switch now ignores dependency check.


## 0.503

Features:

* Added new provider (DarkSky) because of problems with wunderground as provider (deactivation of API?).


## 0.502-2

Features:

* Added further logging in case of error.


## 0.502-1

Features:

* Removed fixed TLS version.


## 0.502

Features:

* Removed unnecessary triggerState and moved it to individual sensor when necessary.


## 0.501-1

Features:

* Added optional data to sensor alert.


## 0.501

Features:

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.


## 0.500-1

Features:

* Changed timeout setting in order to have a more stable connection recovery.


## 0.401

Features:

* Added thresholds to sensors in order to be able to trigger a sensor alert.


## 0.400

Features:

* Initial commit of this instance.
* User paths can now be relative paths.