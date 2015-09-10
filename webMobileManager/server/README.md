alertR Web Mobile Manager
======

This is the web page of the alertR Web Mobile Manager. It shows the information of the alerting system on a web page optimized for mobile phones. To work, it needs access to the MySQL database of the alertR Manager Client Database. If wanted, the web page can use the local UNIX socket of the alertR Manager Client Database to send commands back to the alertR system. 


How to use it?
======

To use the web page you have to configure it first. A commented configuration template file is located inside the "config" folder. The web page is written in PHP and therefore needs a webserver that can interpret PHP. Also, access to the MySQL db of the alertR Manager Client Database is needed for the web page to work. Therefore, the alertR Manager Client Database has to be installed first.

We strongly recommend to use HTTPS for the connection to the webserver. Otherwise, people are able to see your login credentials and therefore can send commands to your alertR system (if it is activated, otherwise they only can see the information of your alerting system).

A short but more detailed basic example configuration of how to set up the web page is given in the ([wiki](https://github.com/sqall01/alertR/wiki/Example-Configuration)).