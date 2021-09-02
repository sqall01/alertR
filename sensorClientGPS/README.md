# AlertR Sensor Client GPS

This client handles the GPS position of a device as a sensor. It allows you to build a geofence which triggers an alarm as soon as the device leaves it (or enters it). With this you can build home automation (e.g., turn on the thermostats as soon as I am coming home) as well as alarm systems for movable objects (e.g., car leaves the "home zone" in which it normally drives). Currently, only ChasR is supported as GPS provider (https://alertr.de/chasr).


## How to use it?

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).