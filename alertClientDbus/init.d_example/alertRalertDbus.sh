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

# Change USER to the user which runs the alertRclient.
USER=alertr
# Change DAEMON to the path to run the alertRclient.
DAEMON=/absolute/path/to/alertRclient.py

# This export is important for the dbus client to work correctly.
# Normally the display of the xserver that is used by the user is ":0.0" and
# this should work in almost all cases.
# But if this does not work, check which display is exported by our user.
export DISPLAY=":0.0"

# IMPORTANT: if you start this AlertR client as a different user than the one
# the X session is running on, you need to allow this user to access your X
# session in order to display notifications. For example, if the user the
# AlertR client is running on is `alertr` and the user you use for your daily
# usage is `someUser`, then `someUser` has to execute the following command
# each time she/he logs in:
#
# xhost +SI:localuser:alertr
# 
# This allows the user `alertr` to access the X session of `someUser`. In
# order to automate this, it is best to place this command somewhere that is
# executed each time the user logs in like the `.xsessionrc` file.

NAME=alertRalertDbus
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
        echo "Usage: "$0" {start|restart|status|stop}"
        exit 1
    ;;
esac

exit 0