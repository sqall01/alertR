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
* Added separated sensor alert message handling (distinguish between "triggered" and "normal" state)


## 0.501-3

Features:

* Update "force" switch now ignores dependency check.


## 0.501-2

Features:

* Moved push notification component to lightweightpush pip package.


## 0.501-1

Features:

* Removed fixed TLS version.


## 0.501

Features:

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.


## 0.500-1

Features:

* Added channel prefixing in order to reduce channel collisions.
* Added message truncation if it is too long.
* Changed timeout setting in order to have a more stable connection recovery.


## 0.500

Features:

* Initial commit of this instance.
