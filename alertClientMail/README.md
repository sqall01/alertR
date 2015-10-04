alertR Alert Client Mail
======

This client handles triggered sensor alerts and is written to send an eMail to the configured address when it receives a sensor alert. It needs a local SMTP server (like postfix) to send an eMail. For each alert you configure, you can customize the eMail content by using template files. Special keywords will be replaced by information about the received sensor alert.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. Furthermore, an example for an eMail template is also located there. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.


Nevertheless, a short but more detailed basic example configuration of how to set up the client is given in the ([wiki](https://github.com/sqall01/alertR/wiki/Example-Configuration)).