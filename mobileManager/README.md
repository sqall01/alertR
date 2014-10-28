alertR Mobile Manager
======

This client is written to work as a manager client for mobile devices. At the moment the client software is only written for Android. The client software connects to the "mobile server" and displays all information and options. The "mobile server" connects to the database and displays the current state of the alert system. At the moment, the "mobile server" only works if the server uses MySQL DB as storage backend.


How to use it?
======

Just install the Android client to your mobile device (in case alertR is used more widely, I will add the Android client to the google play store) and configure everything in the settings. You should use HTTPS for the connection to your webserver (note: when your used certificate is not installed to your mobile device, the client refuses to connect to the server). The client is a simple client software that just uses HTTP(S) to connect to the server and logs in via http authentication (actually, it just displays a website written for mobile devices, but handles the log in credentials as configurable options).

The "mobile server" is a bunch of simple PHP scripts that have to be displayed by a webserver. The webserver should be reachable from the internet in order to work correctly. You have to configure htaccess log in credentials for the PHP files so the client can log in to it. The PHP scripts should NEVER be reachable from the internet without any form auf HTTP authentication. The "mobile server" has to be configured in the "config.php" file in the "config" folder. It has to access the "alertr" database on the MySQL server directly (note: the "mobile server" does not communicate with the alertR server, it reads and writes directly to the database).


Known issue
======

The client calculates the time to decide if a sensor has timed out. For this calculation it uses the local time of itself. If the client is in another time zone or has a misconfigured time on its system, it will show sensors as timed out even if they are not timed out. This will be solved when the mobile manager client is rewritten. At the moment the client has a direct access to the database of the alertR server. This was a quick (and dirty) way to have the ability to use a mobile manager.