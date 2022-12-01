# AlertR Manager Client Prometheus

This client exposes all sensors holding float or integer data for a Prometheus collector to collect it. This allows to create a time series of the sensor data which can be used, for example, by Grafana to create graph views. Note that this client is only for internal usage and does not provide any authentication mechanisms or transport encryption such as TLS for the exposed data.

## How to use it?

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. An init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the server with the start of the host computer.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).