alertR Server
======

This is the server that handles the logic of the alert system. It is mandatory in order to use alertR. It uses either MySQL or SQLite as storage backend. As user backend it uses (at the moment) only a csv file.


How to use it?
======

To use the server you have to configure it first. A commented configuration template file is located inside the "config" folder. Also you have to add username and password for each client that connects to the server in the "users.csv" (also located inside the "config" folder). A username has to be unique for each client that will connect to the server.

As backend you can (at the moment) either choose MySQL (MySQLdb for python) or SQLite (sqlite3 for python).

The server uses SSL for the communication with the clients. This means you have to generate a certificate and a keyfile for your server. Each client needs the certificate file of the server to validate correctness of the server. In turn the clients are validated by the given user credentials.

The clients do not have to be configured at the server side (only on the client side). When the clients have valid credentials, they register themselves at the server. This means also that the content of the database can change (for example IDs of the sensors), if you change the configuration of a client. This results from the fact that the client will newly register itself and the server will delete all information it has about this specific client. If you use the database entries directly (for example to read the state of a sensor and display it on a website) you have to take this behavior into account.

A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the server with the start of the host computer.

If you need a more detailed description of how to set up an alertR system, a basic example configuration is given in the [wiki](https://github.com/sqall01/alertR/wiki/Example-Configuration).