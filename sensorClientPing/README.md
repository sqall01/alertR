# AlertR Sensor Client Ping

This client is specialized to just ping a server as a sensor and informing the AlertR system if a host is reachable or not. The sensor is triggered if the server is not reachable or a timeout occur.


## How to use it?

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).