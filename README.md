alertR
======

alertR is an unified client/server based alerting system. Originally it was developed as an open source home security system, but soon it became apparent that it can be used in a great variety of scenarios where an alerting system is needed, for example as a simpler nagios to monitor the availability of a server/service.

An introduction to the project can be found [here](http://h4des.org/blog/index.php?/archives/345-Introducing-alertR-Open-Source-alerting-system.html). There are some pictures and short descriptions of how to build a sensor.


Structure
======

alertR uses a client/server based structure. The server contains all the logic and is informed by the clients of the state of the sensors. When a sensor is triggered, the server decides what to do. Depending on your configuration, the server will inform the clients that can trigger an alarm (such as a siren) and send you an eMail notification that a sensor has been triggered.

There are 3 types of clients:
* sensor
* alert
* manager


sensor
------

The "sensor" client is a client that manages one or more sensors. The sensor can be anything from a Raspberry Pi GPIO pin to a script that is executed and its exit code is been checked. Depending on your configuration, the client will inform the server of a triggered alert or a changed sensor state. The state of a sensor is logical and can either be 1 (triggered) or 0 (normal). The sensor can be configured in any way you want. A sensor can trigger always (this means it ignores if the alerting system is active or not), depending on the state of the alerting system (active or not) or never (just monitor the state of the sensor). A sensor that should trigger always for example could be a smoke detector. A sensor that should never trigger could for example be a watchdog script that checks if a PC is up and running (and you only want to see this on a manager client).

Sensors a categorized in so called "alert levels". The alert level is a category in which "alert" clients are registered. When a sensor is triggered and the server is informed about it, the server will look up the alert level and will inform any "alert" client which is registered in this alert level about it. This way you can trigger different alert scenarios for different sensors (for example turn on a siren when a window is opened but only send you an eMail when a server is down).


alert
------

The "alert" client is a client that gets informed by the server if a sensor has triggered and an alarm should be raised. The client can have one or more alerts it can activate. An alert it activates can be anything from a Raspberry Pi GPIO which is set to high and turns on a siren to making a call via an Asterisk server.

Alerts are categorized in so called "alert levels". The server will only inform alert clients about a triggered sensor when they are in the same alert level.


manager
------

The "manager" client is a client that gets informed about the state of the alerting system. It is used to give an overview about the current state of the alerting system and all its sensors. Also the client is used to activate or deactivate the alerting system.