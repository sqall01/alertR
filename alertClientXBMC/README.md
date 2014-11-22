alertR Alert Client XBMC
======

This client handles triggered alerts and is written to communicate with XBMC/Kodi. It can show a message notification on the display and can pause video/audio playback (for now). For example you can use this client to pause the video/audio playback and show a message notification if someone is rining the bell at your front door.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer.

Nevertheless, a short but more detailed example of how to set up this client is given below.


Configuration example
======

```bash
#################### configure autostart ####################

root@xbmc:/etc/init.d# chmod 775 alertRalarm.sh 
root@xbmc:/etc/init.d# vim alertRalarm.sh 
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
USER=someUser
# change DAEMON to the path to run the alertRclient
DAEMON=/home/someUser/alertClientXBMC/alertRclient.py

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

root@xbmc:/etc/init.d# update-rc.d alertRalarm.sh defaults


#################### configure alertR ####################

someUser@xbmc:~/alertClientXBMC/config# vim config.conf

[general]
logfile = /home/someUser/alertClientXBMC/logfile.log
loglevel = INFO
server = 10.0.0.2
serverPort = 6666
serverCAFile = /home/someUser/alertClientXBMC/server.crt
username = xbmc_alert
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


[alert0]
id = 0
description = xbmc pause
alertLevels = 1
host = localhost
port = 8080
pausePlayer = True
showMessage = False
displayTime = 10000
triggerDelay = 10


[alert1]
id = 1
description = xbmc notification
alertLevels = 0
host = localhost
port = 8080
pausePlayer = False
showMessage = True
displayTime = 10000
triggerDelay = 2
```