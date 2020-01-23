## 0.501-3

Features:

* Update "force" switch now ignores dependency check.


## 0.501-2

Features:

* Fixed problem with starting the version fetching process even if updates are deactivated.


## 0.501-1

Features:

* Removed fixed TLS version.


## 0.501

Features:

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.


## 0.500-1

Features:

* Changed timeout setting in order to have a more stable connection recovery.


## 0.400-1

Features:

* User paths can now be relative paths.
* Added start up log entries.


## 0.400

Features:

* Streamlined database layout.
* Added persistent/non-persistent flag.


## 0.300

Features:

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Authentication message now contains version and revision.
* Alert system update messages to manager clients now contain version, revision and client instance.
* Checks (when online update check is activated) the version of all available instances in the online repository with the version of the used instances.
* Added option to give the amount of days that a sensor alert is kept in the database.
* Added option to configure the use of the local unix socket server instance.
* Added option to give the amount of days that a event is kept in the database.
* Added event log (an event is anything that has happened on the alert system for example a sensor alert, a state change of an sensor, an option change etc.).
* Renamed client to alertR Manager Client Database.