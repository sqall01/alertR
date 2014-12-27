alertR Mobile Manager - Server - Manger Client Mobile
======

This is the part of the mobile manager that connects to the alertR server and receives all information about the alerting system. The information is stored into a MySQL db as a shared medium to the web page.


How to use it?
======

To use this part you have to configure it first. A commented configuration template file is located inside the "config" folder. An init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the server with the start of the host computer. As backend you have to use MySQL (MySQLdb for python).

Nevertheless, a short but more detailed basic example configuration of how to set up the client is given in the document directory ([/docs/tutorial.md](/docs/tutorial.md)).