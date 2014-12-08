alertR Mobile Manager
======

This client is written to work as a manager client for mobile devices. At the moment the client part of the software is only written for Android, but it is only a simple web page that is shown on the mobile device. So it can be easily extended to be used by other mobile operating systems.

The server part of the manager client is divided into two parts. The manager client mobile part and the web part. The manager client mobile connects (like the other manager clients of alertR) itself to the alertR server and gets all information about the alerting system. This information is stored in a MySQL db. The web part is a normal web page that uses php5. The web site connects to the MySQL db and reads the information about the alerting system. The manager client mobile part creates an unix socket in order to communicate with the web part.


How to use it?
======

This is explained in the according subdirectories.