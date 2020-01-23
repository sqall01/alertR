## 0.600

Features:

* Migration from Python 2.7 to Python 3.5


## 0.502-3

Features:

* Update "force" switch now ignores dependency check.


## 0.502-2

Features:

* Replaced sound files.


## 0.502-1

Features:

* Removed fixed TLS version.


## 0.502

Features:

* Removed update checker process (moved to server instance).
* Update process checks dependency changes and can delete old files.


## 0.501-1

Features:

* Changed timeout setting in order to have a more stable connection recovery.


## 0.501

Features:

* Play silent option as a workaround for HDMI sound delay.


## 0.400-1

Features:

* User paths can now be relative paths.
* Added start up log entries.


## 0.400

Features:

* Client is now able to play sounds in certain situations.
* Client can now check if sensors are in a certain state and ask the user for confirmation before sending an alarm system activation message to the server (sensors and state are configurable in the configuration file of this client).
* Added persistent/non-persistent flag.


## 0.300

Features:

* Sensor alert messages distinguish now between state "triggered" and "normal".
* Authentication message now contains version and revision.
* Alert system update messages to manager clients now contain version, revision and client instance.