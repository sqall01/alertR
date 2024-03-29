# AlertR Alert Client Push Notification

This client handles triggered sensor alerts and is written to send an end-to-end encrypted push notification on the configured channel when it receives a sensor alert. It needs an account at https://alertr.de and the receiving devices to have the AlertR App installed. For each alert you configure, you can customize the message content by using template files. Special keywords will be replaced by information about the received sensor alert.


## How to use it?

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. Furthermore, an example for an message template is also located there. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer. You have to set up an account at [alertr.de](https://alertr.de) and the receiving devices have to install the [AlertR App](https://play.google.com/store/apps/details?id=de.alertr.alertralarmnotification).

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).