alertR Sensor Client Raspberry Pi
======

This client handles Raspberry Pi GPIO pins as sensors. It polls the state of a GPIO pin and triggers an alert if the state has changed (or a state change if it goes back from a state in which it triggers an alert to a normal state). This means it notifies the server if an alert was triggered by a sensor. A sensor connected to the GPIO pin can be anything you like for example a PIR (Passive InfraRed) sensor, a magnetic switch on a window, a water leak alarm sensor, a smoke detector and so on.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

Nevertheless, a short but more detailed example of how to set up this client is given below.

If you want to test the configuration of the GPIO pins of the Raspberry Pi first, you can use the scripts in the "helperScripts" folder under the main directory.

A schematic about a pull-up circuit that can be used with a Raspberry Pi can be found in the "docs" folder under the main directory.


Configuration example
======

```bash
#################### configure autostart ####################

root@raspberrypi:/etc/init.d# chmod 775 alertRclient.sh 
root@raspberrypi:/etc/init.d# vim alertRclient.sh 
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
USER=root # on a raspberry pi the gpios need root permissions
# change DAEMON to the path to run the alertRclient
DAEMON=/home/someUser/sensorClientRaspberryPi/alertRclient.py

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

root@raspberrypi:/etc/init.d# update-rc.d alertRclient.sh defaults


#################### configure alertR ####################

root@raspberrypi:/home/someUser/sensorClientRaspberryPi/config# vim config.conf

[general]
logfile = /home/someUser/sensorClientRaspberryPi/logfile.log
loglevel = INFO
server = 10.0.0.2
serverPort = 6666
serverCertificate = /home/someUser/sensorClientRaspberryPi/server.crt
username = pi_sensor
password = <SECRET>


[smtp]
smtpActivated = True
server = 127.0.0.1
serverPort = 25
fromAddr = alertR@h4des.org
toAddr = some@address.org


[sensor1]
id = 0
description = front door
gpioPin = 21
alertDelay = 20
alertLevel = 2
triggerAlert = True
triggerAlways = False
triggerState = 1

[sensor2]
id = 1
description = living room window left bottom
gpioPin = 26
alertDelay = 0
alertLevel = 1
triggerAlert = True
triggerAlways = False
triggerState = 1

[sensor3]
id = 2
description = living room window right top
gpioPin = 24
alertDelay = 0
alertLevel = 0
triggerAlert = False
triggerAlways = False
triggerState = 1

[sensor4]
id = 3
description = living room window left top
gpioPin = 23
alertDelay = 0
alertLevel = 0
triggerAlert = False
triggerAlways = False
triggerState = 1
```