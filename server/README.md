alertR Server
======

This is the server that handles the logic of the alert system. It is mandatory in order to use alertR. It is completly written in python and uses (at the moment) either MySQL or SQLite as storage backend. As user backend it uses (at the moment) only a csv file.


How to use it?
======

To use the server you have to configure it first. A commented configuration template file is located inside the "config" folder. Also you have to add username and password for each client that connects to the server in the "users.csv" (also located inside the "config" folder). A username has to be unique for each client that will connect to the server.

As backend you can (at the moment) either choose MySQL (MySQLdb for python) or SQLite (sqlite3 for python).

The server uses SSL for the communication with the clients. This means you have to generate a certificate and a keyfile for your server. Each client needs the certificate file of the server to validate correctness of the server. In turn the clients are validated by the given user credentials.

The clients do not have to be configured at the server side (only on the client side). When the clients have valid credentials, they register themselves at the server. This means also that the content of the database can change (for example IDs of the sensors), if you change the configuration of a client. This results from the fact that the client will newly register itself and the server will delete all information it has about this specific client. If you use the database entries directly (for example to read the state of a sensor and display it on a website) you have to take this behavior into account.

A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the server with the start of the host computer.

Nevertheless, a short but more detailed example of how to set up the server is given below.


Configuration example
======

```bash
#################### install packets ####################

in this example we use the mysql database as storage backend

---

root@raspberrypi:/home/pi# apt-get install python-mysqldb


#################### configure autostart ####################

root@raspberrypi:/etc/init.d# chmod 775 alertRserver.sh
root@raspberrypi:/etc/init.d# alertRserver.sh
#!/bin/sh
### BEGIN INIT INFO
# Provides:          alertRserver.py
# Required-Start:    $all
# Should-Start:      $all
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: h4des.org alertRserver daemon start/stop script
# Description:       Start/Stop script for the h4des.org alertRserver daemon
### END INIT INFO

set -e

# change USER to the user which runs the alertRserver
USER=pi
# change DAEMON to the path to run the alertRserver
DAEMON=/home/pi/server/alertRserver.py

NAME=alertRserver.py
PIDFILE=/var/run/$NAME.pid
DAEMON_OPTS=""

export PATH="${PATH:+$PATH:}/usr/sbin:/sbin"

case "$1" in
        start)
                echo -n "Starting daemon: "$NAME
                start-stop-daemon --start --quiet -b --make-pidfile \
                        --pidfile $PIDFILE --chuid $USER --exec $DAEMON -- $DAEMON_OPTS
                echo "."
        ;;
        stop)
                echo -n "Stopping daemon: "$NAME
                start-stop-daemon --stop --pidfile $PIDFILE --verbose \
                        --retry=TERM/30/KILL/5
                echo "."
        ;;
        *)
                echo "Usage: "$1" {start|stop}"
                exit 1
        ;;
esac

exit 0

---

root@raspberrypi:/etc/init.d# update-rc.d alertRserver.sh defaults


#################### preparing mysql database ####################

mysql> create database alertr;
mysql> CREATE USER 'alertr'@'localhost' IDENTIFIED BY '<SECRET>';
mysql> GRANT ALL ON alertr.* TO 'alertr'@'localhost';


#################### add user credentials ####################

root@raspberrypi:/home/pi/server/config# vim users.csv
sensor_windows, password1
sensor_door, password2
alert_loud, password3
manager_laptop, password4
manager_keypad, password5


#################### generate self signed certificate ####################

root@raspberrypi:/home/pi/server# openssl genrsa -des3 -out server.key 4096
root@raspberrypi:/home/pi/server# openssl req -new -key server.key -out server.csr
root@raspberrypi:/home/pi/server# cp server.key server.key.org
root@raspberrypi:/home/pi/server# openssl rsa -in server.key.org -out server.key
root@raspberrypi:/home/pi/server# openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt


#################### configure alertR ####################

root@raspberrypi:/home/pi/server/config# vim config.conf

[general]
# absolute path
logfile = /home/pi/server/logfile.log
# valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
#loglevel = DEBUG
loglevel = INFO


[server]
certificateFile = /home/pi/server/server.crt
keyFile = /home/pi/server/server.key
port = 6666


[smtp]
smtpActivated = True
# only 127.0.0.1 supported at the moment
server = 127.0.0.1
serverPort = 25
fromAddr = alertR@h4des.org
toAddr = mainProblemAddress@someaddress.org


[userBackend]
# only valid options: csv
method = csv


[storage]
# only valid options: sqlite, mysql
method = mysql
server = 127.0.0.1
port = 3306
database = alertr
username = alertr
password = <SECRET>


# alert level 0 is used global notifications
[alertLevel0]
level = 0
emailAlert = False
toAddr = none
name = global notification
triggerAlways = True


# alert level 1 is used for xbmc pause
[alertLevel1]
level = 1
emailAlert = False
toAddr = none
name = xbmc pause
triggerAlways = True


# alert level 2 is used for eMail notification (only when activated)
[alertLevel2]
level = 2
emailAlert = True
toAddr = EMERGENCY@someaddress.de
name = eMail notification (only activated)
triggerAlways = False


# alert level 3 is used for eMail notification (always)
[alertLevel3]
level = 3
emailAlert = True
toAddr = EMERGENCY@someaddress.de
name = eMail notification (always)
triggerAlways = False


# alert level 4 is used for private eMail notification (always)
[alertLevel4]
level = 4
emailAlert = True
toAddr = private@someaddress.de
name = eMail notification (always/private)
triggerAlways = True


# alert level 5 is used to activate the siren (only when activated)
[alertLevel5]
level = 5
emailAlert = False
toAddr = none
name = sirens (only activated)
triggerAlways = False


# alert level 6 is used to activate the siren (always)
[alertLevel6]
level = 6
emailAlert = False
toAddr = none
name = sirens (always)
triggerAlways = True
```