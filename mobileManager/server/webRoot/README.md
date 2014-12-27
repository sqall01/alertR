alertR Mobile Manager - Server - Web
======

This is the part of the mobile manager that shows the information of the alerting system as a web page. It connects to the MySQL db and displays all gathered information. The mobile device clients connect to this web page and show the user all details.


How to use it?
======

To use this part you have to configure it first. A commented configuration template file is located inside the "config" folder. The web page is written in PHP5 and therefore needs a webserver with PHP and MySQL db installed.

You should use HTTPS for the connection to your webserver. Elsewise, other people are able to see your login credentials and therefore can deactivate the alerting system.

Nevertheless, a short but more detailed basic example configuration of how to set up the server is given in the document directory ([/docs/tutorial.md](/docs/tutorial.md)).