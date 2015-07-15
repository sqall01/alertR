## 0.300

Features:

-sensor alert messages distinguish now between state "triggered" and "normal"
-authentication message now contains version and revision
-alert system update messages to manager clients now contain version, revision and client instance
-checks (when online update check is activated) the version of all available instances in the online repository with the version of the used instances
-added option to give the amount of days that a sensor alert is kept in the database
-added option to configure the use of the local unix socket server instance
-added option to give the amount of days that a event is kept in the database
-added event log (an event is anything that has happened on the alert system for example a sensor alert, a state change of an sensor, an option change etc.)