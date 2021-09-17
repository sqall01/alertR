# AlertR Sensor Client Executer

This client handles scripts as sensors and informs the AlertR system if a sensor has triggered and/or the state of a sensor has changed. This means it executes configured scripts in an interval. Each sensor is basically a cronjob for the AlertR system. The sensor has two options to be triggered: 1) The sensor is triggered if the script exits with an exit code not equal to 0 or a timeout. 2) The script outputs that the sensor should be triggered with the help of a well-defined protocol or a timeout (see the developer tutorials for examples). For instance, you can execute a script that checks if the Internet connection is available and which triggers if no Internet connection is up.


## How to use it?

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).
