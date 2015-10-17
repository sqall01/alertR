alertR Alert Client Executer
======

This client handles triggered alerts and is written to execute a configured script or command with arguments. The arguments are configured and the command is executed on a triggered sensor alert event or when all alerts are stopped. For example you can start a init script on a Linux system when a sensor alert was triggered and when all alerts are stopped the init script is stopped.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

If you need a more detailed description of how to set up an alertR system, a basic example configuration is given in the [wiki](https://github.com/sqall01/alertR/wiki/Example-Configuration).