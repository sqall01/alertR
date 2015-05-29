alertR Alert Client Raspberry Pi
======

This client handles triggered alerts and is written to set/unset GPIO pins of a Raspberry Pi. This means it gets notified by the server if an alert was triggered by a sensor and can set/unset configured GPIO pins, for example to activate a siren or something else.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

Nevertheless, a short but more detailed basic example configuration of how to set up the client is given in the ([wiki](https://github.com/sqall01/alertR/wiki/Example-Configuration)).

If you want to test the configuration of the GPIO pins of the Raspberry Pi first, you can use the scripts in the "helperScripts" folder under the main directory.

A schematic about a relais circuit that can be used with a Raspberry Pi can be found in the "docs" folder under the main directory.