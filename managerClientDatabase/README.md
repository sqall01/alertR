AlertR Manager Client Database
======

This client stores the state of the alert system in a database for external usage. It uses a MySQL db to store all information about the alert system. External components, such as a website, can use the information in the database for their purposes. In the case of a website, it can process the data and show a visualization to the user. In order to let external components interact with the alert system, the manager client contains a local UNIX socket server which can be contacted.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. An init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the server with the start of the host computer. As backend you have to use MySQL (MySQLdb for python).

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).
