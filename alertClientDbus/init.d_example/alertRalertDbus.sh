#!/bin/sh
### BEGIN INIT INFO
# Provides:          alertRalertDbus
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

# this export is important for the dbus client to work correctly
# normally the display of the xserver that is used by the user is ":0.0" and
# this should work in almost all cases
# but if this does not work, check which display is exported by our user
export DISPLAY=":0.0"

NAME=alertRalertDbus
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

