# AlertR Alert Client Template

This client handles triggered alerts and is solely for developers. It is a template which handles the communication with the server, but does not do any logic when a configured alert is triggered.


## How to use it?

The code for your own Alert has to be added in the "lib/alert/template.py" file. The class "TemplateAlert" is used for each configured alert which can be triggered. If you need additional values which should be read from the configuration file, you can add the code in the "alertRclient.py" file.

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).