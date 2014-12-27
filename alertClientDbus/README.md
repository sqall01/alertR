alertR Alert Client Dbus
======

This client handles triggered alerts and is written to show a message notification via D-Bus. It works with all window managers that support D-Bus and implement the freedesktop.org specification. For example you can start it on your PC and you get notified as soon as the door bell rings or the front door was opened.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. A init.d example file for Debian systems is located inside the "init.d_example" folder if you want to start the client with the start of the host computer. The client needs the python interface for dbus ("python-dbus" package under Debian).

Nevertheless, a short but more detailed basic example configuration of how to set up the client is given in the document directory ([/docs/tutorial.md](/docs/tutorial.md)).