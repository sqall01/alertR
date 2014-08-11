alertR Client Template
======

This client handles triggered alerts. It is a template which handles the communication with the server, but does not do any logic when a configured alert is triggered. The code for this has to be added in the "lib/alert.py" file. The class "TemplateAlert" is used for each configured alert which can be triggered. If you need additional values which should be read from the configuration file, you can add the code in the "alertRclient.py" file.