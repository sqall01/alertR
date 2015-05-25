#!/bin/sh
### BEGIN INIT INFO
# Provides:          alertRserver
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
USER=someUser
# change DAEMON to the path to run the alertRserver
DAEMON=/absolute/path/to/alertRserver.py

NAME=alertRserver
PIDFILE=/var/run/$NAME.pid
DAEMON_OPTS=""
PATH=/sbin:/usr/sbin:/bin:/usr/bin
# Depend on lsb-base (>= 3.2-14) to ensure that this file is present
# and status_of_proc is working.
. /lib/lsb/init-functions


do_start()
{
	# Return
	#   0 if daemon has been started
	#   2 if daemon could not be started
	start-stop-daemon --start --quiet -b --make-pidfile --pidfile $PIDFILE \
		--chuid $USER --exec $DAEMON -- $DAEMON_OPTS \
		|| return 2
}


do_stop()
{
	# Return
	#   0 if daemon has been stopped
	#   1 if daemon was already stopped
	#   2 if daemon could not be stopped
	#   other if a failure occurred
	start-stop-daemon --stop --pidfile $PIDFILE --verbose \
		--retry=TERM/30/KILL/5
		
	RETVAL="$?"
	[ "$RETVAL" = 2 ] && return 2

	rm -f $PIDFILE
	return "$RETVAL"
}


case "$1" in
	start)
		log_daemon_msg "Starting daemon: "$NAME
		do_start
		case "$?" in
			0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
			2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
		esac
	;;
	stop)
		log_daemon_msg "Stopping daemon: "$NAME
		do_stop
		case "$?" in
			0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
			2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
		esac
	;;
	restart)
		log_daemon_msg "Restarting daemon: "$NAME
		do_stop
		case "$?" in
		  0|1)
			do_start
			case "$?" in
				0) log_end_msg 0 ;;
				1) log_end_msg 1 ;; # Old process is still running
				*) log_end_msg 1 ;; # Failed to start
			esac
			;;
		  *)
			# Failed to stop
			log_end_msg 1
			;;
		esac
	;;
	status)
		status_of_proc -p $PIDFILE "$DAEMON" "$NAME" && exit 0 || exit $?
	;;
	*)
		echo "Usage: "$1" {start|restart|status|stop}"
		exit 1
	;;
esac

exit 0