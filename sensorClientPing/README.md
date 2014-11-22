alertR Sensor Client Ping
======

This client is specialized to just ping a server as sensors and informing the alertR server if a sensor has triggered and/or the state of a sensor has changed. This means it checks if a configured server is reachable via ping. The sensor is triggered if the server is not reachable or a time out occur. 


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

Nevertheless, a short but more detailed example of how to set up this client is given below.


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
USER=someUser
# change DAEMON to the path to run the alertRclient
DAEMON=/home/someUser/sensorClientWatchdog/alertRclient.py

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

root@raspberrypi:/home/someUser/sensorClientWatchdog/config# vim config.conf

[general]
logfile = /home/someUser/sensorClientWatchdog/logfile.log
loglevel = INFO
server = 10.0.0.2
serverPort = 6666
serverCAFile = /home/someUser/sensorClientWatchdog/server.crt
username = pi_alert
password = <SECRET>

certificateRequired = False
certificateFile = /someFolder/client.crt
keyFile = /someFolder/client.key


[smtp]
smtpActivated = True
server = 127.0.0.1
serverPort = 25
fromAddr = alertR@h4des.org
toAddr = some@address.org


[sensor0]
id = 0
description = storageserver reachable
alertDelay = 0
alertLevels = 0, 4
triggerAlert = True
triggerAlways = True
triggerState = 1
host = storageserver.h4des.org
execute = /bin/ping
timeout = 30
intervalToCheck = 60

[sensor1]
id = 1
description = firewall reachable
alertDelay = 0
alertLevels = 0, 4
triggerAlert = True
triggerAlways = True
triggerState = 1
host = firewall.h4des.org
execute = /bin/ping
timeout = 30
intervalToCheck = 60

[sensor2]
id = 2
description = sensor raspberry reachable
alertDelay = 0
alertLevels = 0, 4
triggerAlert = True
triggerAlways = True
triggerState = 1
host = sensorrasp.h4des.org
execute = /bin/ping
timeout = 30
intervalToCheck = 60

[sensor3]
id = 3
description = sensor2 raspberry reachable
alertDelay = 0
alertLevels = 0, 4
triggerAlert = True
triggerAlways = True
triggerState = 1
host = sensorrasp2.h4des.org
execute = /bin/ping
timeout = 30
intervalToCheck = 60

[sensor4]
id = 4
description = sensor3 raspberry reachable
alertDelay = 0
alertLevels = 0, 4
triggerAlert = True
triggerAlways = True
triggerState = 1
host = sensorrasp3.h4des.org
execute = /bin/ping
timeout = 30
intervalToCheck = 60

[sensor5]
id = 5
description = printer reachable
alertDelay = 0
alertLevels = 0, 4
triggerAlert = True
triggerAlways = True
triggerState = 1
host = printer.h4des.org
execute = /bin/ping
timeout = 30
intervalToCheck = 60

[sensor6]
id = 6
description = xbmc reachable
alertDelay = 0
alertLevels = 0
triggerAlert = False
triggerAlways = False
triggerState = 1
host = xbmc.h4des.org
execute = /bin/ping
timeout = 30
intervalToCheck = 60
```