alertR Sensor Client Ping
======

This client is specialized to just ping a server as sensors and informing the alertR server if a sensor has triggered and/or the state of a sensor has changed. This means it checks if a configured server is reachable via ping. The sensor is triggered if the server is not reachable or a time out occur. 


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

Nevertheless, a short but more detailed basic example configuration of how to set up the client is given in the ([wiki](https://github.com/sqall01/alertR/wiki/Example-configuration)).