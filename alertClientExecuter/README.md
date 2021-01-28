# AlertR Alert Client Executer

This client handles triggered sensors and is written to execute a configured script or command with arguments. The arguments are configured and the command is executed on a triggered sensor alert event or when the system profile has changed. This allows you to interact with non-AlertR components or integrate your own code into the AlertR system.


## How to use it?

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).