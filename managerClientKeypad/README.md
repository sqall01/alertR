# AlertR Manager Client Keypad

This client manages the state of the AlertR system. It can change the used system profile after you entered a correct PIN. If AlertR is, for example, used in an alarm system context, it can change the used system profile from "alarm system activated" to "alarm system deactivated" and vice versa. Furthermore, it allows a delayed system profile change allowing you, for example, in an alarm system context to chose "activate the alarm system in X seconds" and then leave the building. It is written to work as a client with keypad and small display (original for a Raspbery Pi, but is not limited to it). In an alarm system context, the client should be near an entrance to allow the user to activate/deactivate the alarm system while leaving/entering.


## How to use it?

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. The client uses urwid to display all information, so you have to install it first. Whenn configured, just execute the "alertRclient.py".

If you need a more detailed description of how to set up an AlertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).