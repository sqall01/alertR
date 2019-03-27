#!/usr/bin/python

# http://raspberrypiguide.de/howtos/raspberry-pi-gpio-how-to/

import RPi.GPIO as GPIO
import time
import signal
import sys

# NOTE: this is the actual pin number (not the number of the GPIO)
outputPin = 18

def signalHandler(signum, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signalHandler)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(outputPin, GPIO.OUT)

print "low"
GPIO.output(outputPin, GPIO.LOW)
time.sleep(5)

print "high"
GPIO.output(outputPin, GPIO.HIGH)
time.sleep(5)

print "low"
GPIO.output(outputPin, GPIO.LOW)

GPIO.cleanup()