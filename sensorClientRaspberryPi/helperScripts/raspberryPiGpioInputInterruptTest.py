#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import RPi.GPIO as GPIO

# NOTE: this is the actual pin number (not the number of the GPIO)
inputPin = 18

pulledUpDown = GPIO.PUD_UP
# pulledUpDown = GPIO.PUD_DOWN

edge = GPIO.FALLING
# edge = GPIO.RISING

GPIO.setmode(GPIO.BOARD)
GPIO.setup(inputPin, GPIO.IN, pull_up_down=pulledUpDown)

counter = 0
while True:
    GPIO.wait_for_edge(inputPin, edge)
    counter += 1
    print("Trigger no.: " + str(counter))
