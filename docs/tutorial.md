alertR tutorials
======

In this document I give a simple basic configuration example of the alertR server and some components. You can use it to configure alertR at your home (or where ever you want to use it).


basic configuration
======

In this basic configuration example we only use a simple self generated certificate for the server. No self generated CA or signing is needed. The clients are configured to not offer a certificate for there authentication. This is a simple configuration that can be used in a home environment which is not reachable from the Internet.


alertR Server
------

```bash
#################### install packets ####################

In this example we use the mysql database as storage backend.

---

root@raspberrypi:/home/pi# apt-get install python-mysqldb


#################### configure autostart ####################

root@raspberrypi:/etc/init.d# chmod 775 alertRserver.sh
root@raspberrypi:/etc/init.d# alertRserver.sh
#!/bin/sh
### BEGIN INIT INFO
# Provides:          alertRserver.py
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
USER=pi
# change DAEMON to the path to run the alertRserver
DAEMON=/home/pi/server/alertRserver.py

NAME=alertRserver.py
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

root@raspberrypi:/etc/init.d# update-rc.d alertRserver.sh defaults


#################### preparing mysql database ####################

mysql> create database alertr;
mysql> CREATE USER 'alertr'@'localhost' IDENTIFIED BY '<SECRET>';
mysql> GRANT ALL ON alertr.* TO 'alertr'@'localhost';


#################### add user credentials ####################

root@raspberrypi:/home/pi/server/config# vim users.csv
sensor_ping, password1
sensor_pi, password2
alert_dbus, password3
alert_pi, password4
manager_mobile, password5
manager_keypad, password6
alert_xbmc, password7


#################### generate self signed certificate ####################

root@raspberrypi:/home/pi/server# openssl genrsa -des3 -out server.key 4096
root@raspberrypi:/home/pi/server# openssl req -new -key server.key -out server.csr
root@raspberrypi:/home/pi/server# cp server.key server.key.org
root@raspberrypi:/home/pi/server# openssl rsa -in server.key.org -out server.key
root@raspberrypi:/home/pi/server# openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

---

Copy the server.crt to all clients that talk to the alertR server. It is needed to verify the offered certificate of the server.

#################### configure alertR ####################

root@raspberrypi:/home/pi/server/config# vim config.xml

<?xml version="1.0"?>

<config version="0.221">

	<general>

		<log
			file="/home/pi/server/logfile.log"
			level="INFO" />

		<server
			certFile="/home/pi/server/server.crt"
			keyFile="/home/pi/server/server.key"
			port="6666" />

		<client
			useClientCertificates="False"
			clientCAFile="not processed" />

	</general>


	<smtp>

		<general
			activated="True"
			fromAddr="alertR@h4des.org"
			toAddr="mainProblemAddress@someaddress.org" />

		<server
			host="127.0.0.1"
			port="25" />

	</smtp>


	<storage>

		<userBackend
			method="csv" />

		<storageBackend
			method="mysql"
			server="127.0.0.1"
			port="3306"
			database="alertr"
			username="alertr"
			password="<SECRET>" />

	</storage>


	<alertLevels>

		<!--
			alert level 0 is used global notifications
		-->
		<alertLevel>

			<general
				level="0"
				name="global notification"
				triggerAlways="True" />

			<smtp
				emailAlert="False"
				toAddr="none" />

		</alertLevel>

		<!--
			alert level 1 is used for xbmc pause
		-->
		<alertLevel>

			<general
				level="1"
				name="xbmc pause"
				triggerAlways="True" />

			<smtp
				emailAlert="False"
				toAddr="none" />

		</alertLevel>

		<!--
			alert level 2 is used for eMail notification (only when activated)
		-->
		<alertLevel>

			<general
				level="2"
				name="eMail notification (only activated)"
				triggerAlways="False" />

			<smtp
				emailAlert="True"
				toAddr="emergency@someaddress.org" />

		</alertLevel>

		<!--
			alert level 3 is used for eMail notification (always)
		-->
		<alertLevel>

			<general
				level="3"
				name="eMail notification (always)"
				triggerAlways="True" />

			<smtp
				emailAlert="True"
				toAddr="emergency@someaddress.org" />

		</alertLevel>

		<!--
			alert level 4 is used for private eMail notification (always)
		-->
		<alertLevel>

			<general
				level="4"
				name="eMail notification (always/private)"
				triggerAlways="True" />

			<smtp
				emailAlert="True"
				toAddr="myPrivateAddress@someaddress.org" />

		</alertLevel>

		<!--
			alert level 5 is used to activate the siren (only when activated)
		-->
		<alertLevel>

			<general
				level="5"
				name="sirens (only activated)"
				triggerAlways="False" />

			<smtp
				emailAlert="False"
				toAddr="none" />

		</alertLevel>

		<!--
			alert level 6 is used to activate the siren (always)
		-->
		<alertLevel>

			<general
				level="6"
				name="sirens (always)"
				triggerAlways="True" />

			<smtp
				emailAlert="False"
				toAddr="none" />

		</alertLevel>

	</alertLevels>

</config>
```


alertR Sensor Client Ping
------

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

root@raspberrypi:/home/someUser/sensorClientWatchdog/config# vim config.xml

<?xml version="1.0"?>

<config version="0.221">

	<general>

		<log
			file="/home/someUser/sensorClientWatchdog/logfile.log"
			level="INFO" />

		<server
			host="alertR.h4des.org"
			port="6666"
			caFile="/home/someUser/sensorClientWatchdog/server.crt" />

		<client
			certificateRequired="False"
			certFile="none"
			keyFile="none" />

		<credentials
			username="sensor_ping"
			password="password1" />

	</general>


	<smtp>

		<general
			activated="True"
			fromAddr="alertR@h4des.org"
			toAddr="mainProblemAddress@someaddress.org" />

		<server
			host="127.0.0.1"
			port="25" />

	</smtp>


	<sensors>

		<sensor>

			<general
				id="0"
				description="fileserver reachable"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>
			<alertLevel>4</alertLevel>

			<ping
				host="fileserver.h4des.org"
				execute="/bin/ping"
				timeout="30"
				intervalToCheck="60" />

		</sensor>


		<sensor>

			<general
				id="1"
				description="firewall reachable"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>
			<alertLevel>4</alertLevel>

			<ping
				host="firewall.h4des.org"
				execute="/bin/ping"
				timeout="30"
				intervalToCheck="60" />

		</sensor>


		<sensor>

			<general
				id="2"
				description="sensor reachable"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>
			<alertLevel>4</alertLevel>

			<ping
				host="sensor.h4des.org"
				execute="/bin/ping"
				timeout="30"
				intervalToCheck="60" />

		</sensor>


		<sensor>

			<general
				id="3"
				description="sensor2 reachable"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>
			<alertLevel>4</alertLevel>

			<ping
				host="sensor2.h4des.org"
				execute="/bin/ping"
				timeout="30"
				intervalToCheck="60" />

		</sensor>


		<sensor>

			<general
				id="4"
				description="pi reachable"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>
			<alertLevel>4</alertLevel>

			<ping
				host="pi.h4des.org"
				execute="/bin/ping"
				timeout="30"
				intervalToCheck="60" />

		</sensor>


		<sensor>

			<general
				id="5"
				description="printer reachable"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>
			<alertLevel>4</alertLevel>

			<ping
				host="printer.h4des.org"
				execute="/bin/ping"
				timeout="30"
				intervalToCheck="60" />

		</sensor>


		<sensor>

			<general
				id="6"
				description="xbmc reachable"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>

			<ping
				host="xbmc.h4des.org"
				execute="/bin/ping"
				timeout="30"
				intervalToCheck="60" />

		</sensor>

	</sensors>

</config>
```


alertR Sensor Client Raspberry Pi
------

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

root@raspberrypi:/home/someUser/sensorClientRaspberryPi/config# vim config.xml

<?xml version="1.0"?>

<config version="0.221">

	<general>

		<log
			file="/home/someUser/sensorClientRaspberryPi/logfile.log"
			level="INFO" />

		<server
			host="alertR.h4des.org"
			port="6666"
			caFile="/home/sqall/alertR/sensorClientRaspberryPi/server.crt" />

		<client
			certificateRequired="False"
			certFile="none"
			keyFile="none" />

		<credentials
			username="sensor_pi"
			password="password2" />

	</general>


	<smtp>

		<general
			activated="True"
			fromAddr="alertR@h4des.org"
			toAddr="mainProblemAddress@someaddress.org" />

		<server
			host="127.0.0.1"
			port="25" />

	</smtp>


	<sensors>

		<sensor>

			<general
				id="0"
				description="front door (notification)"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>

			<gpio
				type="polling"
				gpioPin="21"
				edge="0"
				pulledUpOrDown="1"
				delayBetweenTriggers="10"
				timeSensorTriggered="5"
				edgeCountBeforeTrigger="4" />

		</sensor>


		<sensor>

			<general
				id="1"
				description="front door (alarm)"
				alertDelay="30"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>2</alertLevel>
			<alertLevel>5</alertLevel>

			<gpio
				type="polling"
				gpioPin="21"
				edge="0"
				pulledUpOrDown="1"
				delayBetweenTriggers="10"
				timeSensorTriggered="5"
				edgeCountBeforeTrigger="4" />

		</sensor>


		<sensor>

			<general
				id="2"
				description="living room window left bottom"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>
			<alertLevel>2</alertLevel>
			<alertLevel>5</alertLevel>

			<gpio
				type="polling"
				gpioPin="26"
				edge="0"
				pulledUpOrDown="1"
				delayBetweenTriggers="10"
				timeSensorTriggered="5"
				edgeCountBeforeTrigger="4" />

		</sensor>


		<sensor>

			<general
				id="3"
				description="living room window right top"
				alertDelay="0"
				triggerAlert="False"
				triggerState="1" />

			<alertLevel>2</alertLevel>
			<alertLevel>5</alertLevel>

			<gpio
				type="polling"
				gpioPin="24"
				edge="0"
				pulledUpOrDown="1"
				delayBetweenTriggers="10"
				timeSensorTriggered="5"
				edgeCountBeforeTrigger="4" />

		</sensor>


		<sensor>

			<general
				id="4"
				description="living room window left top"
				alertDelay="0"
				triggerAlert="False"
				triggerState="1" />

			<alertLevel>2</alertLevel>
			<alertLevel>5</alertLevel>

			<gpio
				type="polling"
				gpioPin="23"
				edge="0"
				pulledUpOrDown="1"
				delayBetweenTriggers="10"
				timeSensorTriggered="5"
				edgeCountBeforeTrigger="4" />

		</sensor>


		<sensor>

			<general
				id="5"
				description="living room window right bottom"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>
			<alertLevel>2</alertLevel>
			<alertLevel>5</alertLevel>

			<gpio
				type="polling"
				gpioPin="22"
				edge="0"
				pulledUpOrDown="1"
				delayBetweenTriggers="10"
				timeSensorTriggered="5"
				edgeCountBeforeTrigger="4" />

		</sensor>


		<sensor>

			<general
				id="6"
				description="door bell"
				alertDelay="0"
				triggerAlert="True"
				triggerState="1" />

			<alertLevel>0</alertLevel>
			<alertLevel>1</alertLevel>

			<gpio
				type="interrupt"
				gpioPin="18"
				edge="0"
				pulledUpOrDown="1"
				delayBetweenTriggers="10"
				timeSensorTriggered="5"
				edgeCountBeforeTrigger="4" />

		</sensor>

	</sensors>

</config>
```


alertR Alert Client Dbus
------

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

sqall@pc:/home/sqall/alertrdbus/config# vim config.xml

<?xml version="1.0"?>

<config version="0.221">

	<general>

		<log
			file="/home/sqall/alertrdbus/logfile.log"
			level="INFO" />

		<server
			host="alertR.h4des.org"
			port="6666"
			caFile="/home/sqall/alertrdbus/server.crt" />

		<client
			certificateRequired="True"
			certFile="none"
			keyFile="none" />

		<credentials
			username="alert_dbus"
			password="password3" />

	</general>


	<smtp>

		<general
			activated="False"
			fromAddr="none"
			toAddr="none" />

		<server
			host="127.0.0.1"
			port="25" />

	</smtp>


	<alerts>

		<alert>

			<general
				id="0"
				description="pc notification" />

			<alertLevel>0</alertLevel>

			<dbus
				displayTime="10000"
				triggerDelay="2" />

		</alert>

	</alerts>

</config>
```


alertR Alert Client Raspberry Pi
------

```bash
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


#################### configure alertR ####################

root@raspberrypi:/home/pi/alertClientRaspberryPi/config# vim config.xml

<?xml version="1.0"?>

<config version="0.221">

	<general>

		<log
			file="/home/pi/alertClientRaspberryPi/logfile.log"
			level="INFO" />

		<server
			host="alertR.h4des.org"
			port="6666"
			caFile="/home/pi/alertClientRaspberryPi/server.crt" />

		<client
			certificateRequired="False"
			certFile="none"
			keyFile="none" />

		<credentials
			username="alert_pi"
			password="password4" />

	</general>


	<smtp>

		<general
			activated="True"
			fromAddr="alertR@h4des.org"
			toAddr="mainProblemAddress@someaddress.org" />

		<server
			host="127.0.0.1"
			port="25" />

	</smtp>


	<alerts>

		<alert>

			<general
				id="0"
				description="siren kitchen" />

			<alertLevel>5</alertLevel>
			<alertLevel>6</alertLevel>

			<gpio
				gpioPin="26"
				gpioPinStateNormal="0"
				gpioPinStateTriggered="1" />

		</alert>

	</alerts>

</config>
```


alertR Mobile Manager - Server - Manger Client Mobile
------

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

sqall@webserver:~/alertR/managerClientMobile/config$ vim config.xml

<?xml version="1.0"?>

<config version="0.221">

	<general>

		<log
			file="/home/sqall/alertR/managerClientMobile/logfile.log"
			level="INFO" />

		<server
			host="alertR.h4des.org"
			port="6666"
			caFile="/home/sqall/alertR/managerClientMobile/server.crt" />

		<client
			certificateRequired="False"
			certFile="none"
			keyFile="none" />

		<credentials
			username="manager_mobile"
			password="password5" />

	</general>


	<smtp>

		<general
			activated="True"
			fromAddr="alertR@h4des.org"
			toAddr="mainProblemAddress@someaddress.org" />

		<server
			host="127.0.0.1"
			port="25" />

	</smtp>


	<manager>

		<general
			description="mobile manager" />

		<storage 
			method="mysql"
			server="127.0.0.1"
			port="3306"
			database="alertr_mobile"
			username="alertr_mobile"
			password="<SECRET>" />

	</manager>

</config>
```


alertR Mobile Manager - Server - Web
------

```bash
#################### install packets ####################

in this example we use apache as a webserver and assume that you already installed/configured the manager client mobile

---

root@webserver:/home/sqall# apt-get install apache2 php5-mysql


#################### configure web page ####################


sqall@webserver:/var/www/alertR/config$ vim config.conf

<?php

$configMysqlDb = "alertr_mobile_manager";
$configMysqlUsername = "alertr_mobile";
$configMysqlPassword = "<SECRET>";
$configMysqlServer = "localhost";
$configMysqlPort = 3306;
$configUnixSocket = "/home/sqall/alertR/managerClientMobile/config/localsocket";

?>


#################### configure htaccess ####################

sqall@webserver:/var/www/alertR$ vim .htaccess

AuthUserFile /var/www/alertR/.htpasswd
AuthName "alertR mobile manager"
AuthType Basic
Require valid-user

sqall@webserver:/var/www/alertR$ htpasswd -c testfile mobile_user
New password: <SECRET>
Re-type new password: <SECRET>
```


alertR Manager Client Keypad
------

```bash
#################### used hardware ####################

TaoTronics TT-CM05 4,3 Zoll PAL/NTSC Digital MIni TFT LCD Monitor

with a resolution of 320x200 and a usb keypad

#################### configure output ####################

root@raspberrypi:/boot# vim config.txt
[...]
sdtv_aspect=1
sdtv_mode=2
framebuffer_width=320
framebuffer_height=240

#################### install packets ####################

root@raspberrypi:/home/pi# pip install urwid

#################### add user for keypad ####################

root@raspberrypi:/home# adduser --disabled-password keypad

#################### configure alertR ####################

root@raspberrypi:/home/keypad/alertR/managerClientKeypad/config# vim config.xml

<?xml version="1.0"?>

<config version="0.221">

	<general>

		<log
			file="/home/keypad/alertR/managerClientKeypad/logfile.log"
			level="INFO" />

		<server
			host="alertR.h4des.org"
			port="6666"
			caFile="/home/keypad/alertR/managerClientKeypad/server.crt" />

		<client
			certificateRequired="False"
			certFile="none"
			keyFile="none" />

		<credentials
			username="manager_keypad"
			password="password6" />

	</general>


	<smtp>

		<general
			activated="True"
			fromAddr="alertR@h4des.org"
			toAddr="mainProblemAddress@someaddress.org" />

		<server
			host="127.0.0.1"
			port="25" />

	</smtp>


	<manager>

		<general
			description="keypad manager" />

		<keypad
			timeDelayedActivation="30">

			<pin>5345</pin>
			<pin>3245</pin>

		</keypad>

	</manager>

</config>

---

configure and compile shell wrapper program:

root@raspberrypi:/home/keypad/alertR/managerClientKeypad/shellWrapper# vim shellWrapper.c
[...]
// change these two lines acording to your configuration
#define PYTHON27 "/usr/bin/python2.7"
#define PATHTOSCRIPT "/home/keypad/alertR/managerClientKeypad/alertRclient.py"
[...]

root@raspberrypi:/home/keypad/alertR/managerClientKeypad/shellWrapper# gcc shellWrapper.c -o shellWrapper

root@raspberrypi:/home/keypad/alertR/managerClientKeypad/shellWrapper# chown keypad:keypad shellWrapper

#################### configure auto login for keypad ####################

change shell for "keypad" user:
root@raspberrypi:/home/keypad# vim /etc/passwd
[...]
keypad:x:1001:1004:,,,:/home/keypad:/home/keypad/alertR/managerClientKeypad/shellWrapper/shellWrapper

configure the system such that "keypad" automatically logs in on tty1:

root@raspberrypi:/etc# vim inittab

change line:
1:2345:respawn:/sbin/getty --noclear 38400 tty1

to:
1:2345:respawn:/sbin/getty --autologin keypad --noclear 38400 tty1

With this configuration the keypad manager will be started automatically on tty1 when the host is started. Because of the shell wrapper, the user "keypad" has no shell to fall back and will log out when someone presses ctrl+c or the keypad manager shuts down unexpectedly. Because the tty1 is configured to log in as the user "keypad", the keypad manager will be instantly started again. Therefore we build a kind of "kiosk-mode" for the keypad manager.
```


alertR Alert Client XBMC
------

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

someUser@xbmc:~/alertClientXBMC/config# vim config.xml

<?xml version="1.0"?>

<config version="0.221">

	<general>

		<log
			file="/home/someUser/alertClientXBMC/logfile.log"
			level="INFO" />

		<server
			host="alertR.h4des.org"
			port="6666"
			caFile="/home/someUser/alertClientXBMC/server.crt" />

		<client
			certificateRequired="False"
			certFile="none"
			keyFile="none" />

		<credentials
			username="alert_xbmc"
			password="password7" />

	</general>


	<smtp>

		<general
			activated="True"
			fromAddr="alertR@h4des.org"
			toAddr="mainProblemAddress@someaddress.org" />

		<server
			host="127.0.0.1"
			port="25" />

	</smtp>


	<alerts>

		<alert>

			<general
				id="0"
				description="xbmc pause" />

			<alertLevel>1</alertLevel>

			<xbmc
				host="localhost"
				port="8080"
				triggerDelay="10"
				pausePlayer="True"
				showMessage="False"
				displayTime="10000" />

		</alert>


		<alert>

			<general
				id="1"
				description="xbmc notification" />

			<alertLevel>0</alertLevel>

			<xbmc
				host="localhost"
				port="8080"
				triggerDelay="2"
				pausePlayer="False"
				showMessage="True"
				displayTime="10000" />

		</alert>

	</alerts>

</config>
```