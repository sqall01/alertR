#!/bin/sh
### BEGIN INIT INFO
# Provides:          alertRsensorLightning
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
DAEMON=/absolute/path/to/alertRclient.py

NAME=alertRsensorLightning
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

