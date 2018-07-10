AlertR Sensor Client Executer
======

This client handles watchdog scripts as sensors and informs the server if a sensor has triggered and/or the state of a sensor has changed. This means it executes configured watchdog scripts in an interval that check a service. Each sensor is basically a cronjob for the AlertR system. The sensor has two options to be triggered: 1) The sensor is triggered if the watchdog script exits with an exit code not equal to 0 or a time out. 2) The watchdog script outputs that the sensor should be triggered with the help of a well-defined protocol or a time out (see the developer tutorials for examples). For instance, you can execute a script that checks if the Internet connection is available and which triggers a sensor alert if no Internet connection is up.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).