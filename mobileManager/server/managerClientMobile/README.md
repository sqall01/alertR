alertR Mobile Manager - Server - Manger Client Mobile
======

This is the part of the mobile manager that connects to the alertR server and receives all information about the alerting system. The information is stored into a MySQL db as a shared medium to the web page.


How to use it?
======

To use this part you have to configure it first. A commented configuration template file is located inside the "config" folder. An init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the server with the start of the host computer. As backend you have to use MySQL (MySQLdb for python).

Nevertheless, a short but more detailed example of how to set up the server is given below.


Configuration example
======

```bash
#################### install packets ####################

root@webserver:/home/sqall# apt-get install python-mysqldb mysql-server


#################### configure autostart ####################

root@webserver:/etc/init.d# chmod 775 alertRManagerClientMobile.sh
root@webserver:/etc/init.d# alertRManagerClientMobile.sh

#!/bin/sh
### BEGIN INIT INFO
# Provides:          alertRManagerClientMobile
# Required-Start:    $all
# Should-Start:      $all
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: h4des.org alertRclient daemon start/stop script
# Description:       Start/Stop script for the h4des.org alertRclient daemon
### END INIT INFO

set -e

# change USER to the user which runs the alertRclient
USER=sqall
# change DAEMON to the path to run the alertRclient
DAEMON=/home/sqall/alertR/managerClientMobile/alertRclient.py

NAME=alertRManagerClientMobile.sh
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

root@webserver:/etc/init.d# update-rc.d alertRManagerClientMobile.sh defaults


#################### preparing mysql database ####################

mysql> create database alertr_mobile_manager;
mysql> CREATE USER 'alertr_mobile'@'localhost' IDENTIFIED BY '<SECRET>';
mysql> GRANT ALL ON alertr_mobile_manager.* TO 'alertr_mobile'@'localhost';


#################### configure alertR ####################

sqall@webserver:~/alertR/managerClientMobile/config$ vim config.conf

[general]
logfile = /home/sqall/alertR/managerClientMobile/logfile.log
loglevel = INFO
server = 10.0.0.2
serverPort = 6666
serverCAFile = /home/sqall/alertR/managerClientMobile/server.crt
username = mobile_manager
password = <SECRET>

certificateRequired = False
certificateFile = /home/sqall/alertR/managerClientMobile/client.crt
keyFile = /home/sqall/alertR/managerClientMobile/client.key

description = mobile manager


[smtp]
smtpActivated = False
server = 127.0.0.1
serverPort = 25
fromAddr = alertR@h4des.org
toAddr = some@address.org


[storage]
method = mysql
server = 127.0.0.1
port = 3306
database = alertr_mobile_manager
username = alertr_mobile
password = <SECRET>
```