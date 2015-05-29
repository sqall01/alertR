alertR Sensor Client Raspberry Pi
======

This client handles Raspberry Pi GPIO pins as sensors. It either polls the state of a GPIO pin or uses an interrupt on a falling/rising edge and triggers an alert if the state has changed/interrupt has occurred (or a state change if it goes back from a state in which it triggers an alert to a normal state). This means it notifies the server if an alert was triggered by a sensor. A sensor connected to the GPIO pin can be anything you like for example a PIR (Passive InfraRed) sensor, a magnetic switch on a window, a water leak alarm sensor, a smoke detector and so on.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

Nevertheless, a short but more detailed basic example configuration of how to set up the client is given in the ([wiki](https://github.com/sqall01/alertR/wiki/Example-Configuration)).

If you want to test the configuration of the GPIO pins of the Raspberry Pi first, you can use the scripts in the "helperScripts" folder under the main directory.

A schematic about a pull-up circuit that can be used with a Raspberry Pi can be found in the "docs" folder under the main directory.