alertR Alert Client Dbus
======

This client handles triggered alerts and is written to show a message notification via D-Bus. It works with all window managers that support D-Bus and implement the freedesktop.org specification. For example you can start it on your PC and you get notified as soon as the door bell rings or the front door was opened.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer. The client needs the python interface for dbus ("python-dbus" package under Debian).

Nevertheless, a short but more detailed example of how to set up this client is given below.


Configuration example
======

```bash
#################### install packets ####################

root@pc:/home/sqall# apt-get install python-dbus


#################### configure autostart ####################

root@pc:/etc/init.d# chmod 775 alertRalarm.sh 
root@pc:/etc/init.d# vim alertRalarm.sh 
#!/bin/sh
### BEGIN INIT INFO
# Provides:          alertRclient.py
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
DAEMON=/home/sqall/alertrdbus/alertRclient.py

# this export is important for the dbus client to work correctly
# normally the display of the xserver that is used by the user is ":0.0" and
# this should work in almost all cases
# but if this does not work, check which display is exported by our user
export DISPLAY=":0.0"

NAME=alertRclient.py
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

root@pc:/etc/init.d# update-rc.d alertRalarm.sh defaults


#################### configure alertR ####################

sqall@pc:/home/sqall/alertrdbus/config# vim config.conf

[general]
logfile = /home/sqall/alertrdbus/logfile.log

# valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
loglevel = INFO
server = 10.0.0.2
serverPort = 6666
serverCAFile = /home/sqall/alertrdbus/server.crt
username = dbus_alert
password = <SECRET>

certificateRequired = False
certificateFile = /home/sqall/alertrdbus/client.crt
keyFile = /home/sqall/alertrdbus/client.key


[smtp]
smtpActivated = False
server = 127.0.0.1
serverPort = 25
fromAddr = alertR@h4des.org
toAddr = some@address.org


[alert1]
id = 1
description = pc notification
alertLevels = 3, 4, 5
displayTime = 10000
triggerDelay = 2
```