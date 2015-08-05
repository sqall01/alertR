alertR Sensor Client Executer
======

This client handles watchdog scripts as sensors and informs the server if a sensor has triggered and/or the state of a sensor has changed. This means it executes configured watchdog scripts in an interval that check a service. The sensor is triggered if the watchdog scripts exit with a return code not equal to 0 or time out. For example you can execute a script that checks if the Internet connection is available and which triggers a sensor alert if no Internet connection is up.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

Nevertheless, a short but more detailed basic example configuration of how to set up the client is given in the ([wiki](https://github.com/sqall01/alertR/wiki/Example-Configuration)).