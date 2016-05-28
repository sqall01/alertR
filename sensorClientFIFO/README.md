alertR Sensor Client FIFO
======

This client is build for the integration of already developed scripts or other software into the alertR infrastructure as a sensor. For each sensor it creates a FIFO file on the file system and monitors it. Other scripts/programs can write into the FIFO file to change the state of the associated sensor. For example you can use a cronjob to write into the FIFO file at specific times to trigger a sensor event or the ISC DHCP server to write into the FIFO file each time a client in a specific subnet requests an IP address.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

If you need a more detailed description of how to set up an alertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).