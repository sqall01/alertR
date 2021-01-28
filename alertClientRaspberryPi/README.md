# AlertR Alert Client Raspberry Pi

This client handles triggered alerts and is written to set/unset GPIO pins of a Raspberry Pi. This means it gets notified by the server if a sensor was triggered and can set/unset configured GPIO pins, for example, to activate a siren. However, the sensor can also just be used as a switch and the configured alert can switch on and off the configured GPIO pins.


## How to use it?

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).

If you want to test the configuration of the GPIO pins of the Raspberry Pi first, you can use the scripts in the "helperScripts" folder under the main directory.

A schematic about a relais circuit that can be used with a Raspberry Pi can be found in the "docs" folder under the main directory.