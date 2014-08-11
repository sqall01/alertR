alertR Manager Client Keypad
======

This client manages the state of the alert system. It can activate or deactivate it. You have to enter a PIN before you can activate the alert system, deactivate it or activate it with a delay of 30 seconds. It is written to work as a client with keypad and small display (original for a Raspbery Pi, but is not limited to it). The client should be near an entrance to allow the user to activate/deactivate the alert system when she leaves/comes. It is written for python and uses urwid to display the information and handling intput.


How to use it?
======

To use this client you have to configure it first. A commented configuration template file is located inside the "config" folder. The client uses urwid to display all information, so you have to install it first. Whenn configured, just execute the "alertRclient.py".

It is designed to run on tty1 after the system has started. To achieve this without manual interaction, the code for a little shell wrapper program is added in the folder "shellWrapper". When compiled, this program should be used as the default shell for a special local user. It starts automatically the keypad manager client and if it is shut down, the user automatically logs out. This prevents a local attacker (that just stops the keypad manager client) from getting access to the computer.

Nevertheless, a short but more detailed example of how to set up this client is given below.


Configuration example
======

```bash
#################### used hardware ####################

TaoTronics® TT-CM05 4,3 Zoll PAL/NTSC Digital MIni TFT LCD Monitor

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

root@raspberrypi:/home/keypad/alertR/managerClientKeypad/config# vim config.conf

[general]
logfile = /home/keypad/alertR/managerClientKeypad/logfile.log
loglevel = INFO
server = 10.0.0.2
serverPort = 6666
serverCertificate = /home/keypad/alertR/managerClientKeypad/server.crt
username = keypad
password = <SECRET>
description = keypad entrance door


[smtp]
smtpActivated = True
server = 127.0.0.1
serverPort = 25
fromAddr = alertR@h4des.org
toAddr = some@address.org

[keypad]
pins = <SOME PIN>, <SOME OTHER PIN>

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