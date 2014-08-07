#!/usr/bin/python

# http://raspberrypiguide.de/howtos/raspberry-pi-gpio-how-to/

import RPi.GPIO as GPIO
import time

# NOTE: this is the actual pin number (not the number of the GPIO)
inputPin = 18


GPIO.setmode(GPIO.BOARD)
GPIO.setup(inputPin, GPIO.IN)

while True:
	test = GPIO.input(inputPin)
	print test
	time.sleep(0.2)