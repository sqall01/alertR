# AlertR Sensor Client Template

This client is solely for developers. It is a template which handles the communication with the server, but does not do any logic as a sensor.


## How to use it?

The code for your own Sensor has to be added in the "lib/sensor/template.py" file. The class "TemplateSensor" is used for each configured sensor which monitors something. If you need additional values which should be read from the configuration file, you can add the code in the "alertRclient.py" file.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).