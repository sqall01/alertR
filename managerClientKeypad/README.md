alertR Manager Client Keypad
======

This client manages the state of the alert system. It can activate or deactivate it. You have to enter a PIN before you can activate the alert system, deactivate it or activate it with a configured delay. It is written to work as a client with keypad and small display (original for a Raspbery Pi, but is not limited to it). The client should be near an entrance to allow the user to activate/deactivate the alert system when she leaves/enters.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. The client uses urwid to display all information, so you have to install it first. Whenn configured, just execute the "alertRclient.py".

It is designed to run on tty1 after the system has started. To achieve this without manual interaction, the code for a little shell wrapper program is added in the folder "shellWrapper". When compiled, this program should be used as the default shell for a special local user. It starts automatically the keypad manager client and if it is shut down, the user automatically logs out. This prevents a local attacker (that just stops the keypad manager client) from getting access to the computer.

If you need a more detailed description of how to set up an alertR system, a basic example configuration is given in the [wiki](https://github.com/sqall01/alertR/wiki/Example-Configuration).