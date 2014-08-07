alertClientRaspberryPi
======

This client handles triggered alerts and is written to set/unset GPIO pins of a Raspberry Pi. This means it gets notified by the server if an alert was triggered by a sensor and can set/unset configured GPIO pins, for example to activate a siren or something else.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

Nevertheless, a short but more detailed example of how to set up this client is given below.


Configuration example
======

#################### install packets ####################

root@raspberrypi:/home/pi# apt-get install python-pip python-dev python-rpi.gpio

#################### configure autostart ####################

root@raspberrypi:/etc/init.d# chmod 775 alertRalarm.sh 
root@raspberrypi:/etc/init.d# vim alertRalarm.sh 
#!/bin/sh
### BEGIN INIT INFO
# Provides:          alertRalarm.py
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
USER=root # on a raspberry pi the gpios need root permissions
# change DAEMON to the path to run the alertRclient
DAEMON=/home/pi/alertClientRaspberryPi/alertRclient.py

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

root@raspberrypi:/etc/init.d# update-rc.d alertRalarm.sh defaults

#################### 3.3 configure alertR ####################

```bash
root@raspberrypi:/home/pi/alertClientRaspberryPi/config# vim config.conf

[general]
logfile = /home/pi/alertClientRaspberryPi/logfile.log
loglevel = INFO
server = 10.0.0.2
serverPort = 6666
serverCertificate = /home/pi/alertClientRaspberryPi/server.crt
username = pi_alert
password = <SECRET>


[smtp]
smtpActivated = True
server = 127.0.0.1
serverPort = 25
fromAddr = alertR@h4des.org
toAddr = some@address.org


[alert1]
id = 0
description = pi alert

# this alert should be triggered if alert level 1 or 2 is triggered
alertLevels = 1, 2
gpioPin = 26
gpioPinStateNormal = 0
gpioPinStateTriggered = 1
```