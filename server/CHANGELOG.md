## 0.503-0

Features:

* Removed smtp functionality.
* Added internal sensor for version checks.

## 0.502-0

Features:

* Making internal sensor description available for configuration.
* Adding optional data to internal sensor alerts.

## 0.501-0

Features:

* Added alert system state as an internal sensor in order to generate sensor alerts if alert system changes state (activated/deactivated).


## 0.500-1

Features:

* Changed timeout setting in order to have a more stable connection recovery.
* Fixed problem with multiple log entries.


## 0.400-1

Features:

* User paths can now be relative paths.


## 0.400

Features:

* Username, remoteSensorId and remoteAlertId transmitted to manager clients.
* Sensor alert messages transfer information if it should change the state of the sensor.
* Server has internal sensors that can trigger on internal events (at the moment sensor timeout, client timeout).
* Changed logging system to have separated log files for each client connection.
* Removed eMail notification option in alertLevels (is now moved to a separate alert client with eMail templating).


## 0.300

Features:

* Sensor alert messages distinguish now between state "triggered" and "normal"
* Authentication message now contains version and revision.
* users.csv now also contains type of client and instance of client and checks it during the authentication phase.
* Alert levels have the option to filter out sensor alert messages that were sent for sensors going to the "normal" state.
* Alert levels have the option to filter out sensor alert messages that were sent for sensors going to the "triggered" state.
* Server can now participate in a survey.