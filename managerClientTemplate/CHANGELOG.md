## 0.800-0

* Updater can show changelog
* Removed system status "activated" and "deactivated" to have a more generic system
* Introduced system profiles to replace system status to have a more generic system
* Check permissions of client key file
* Renamed remoteSensorId to clientSensorId to have a more sane naming convention
* Renamed remoteAlertId to clientAlertId to have a more sane naming convention

## 0.700-0

* Refactored client code to get a more resilient connection.
* Unified client code to make it more maintainable.
* Guarantee that requests are send to server in timely order.
* Removed clientTime/serverTime from messages.
* Introduced msgTime into messages to check expiration.

## 0.600-0

* Initial publication
