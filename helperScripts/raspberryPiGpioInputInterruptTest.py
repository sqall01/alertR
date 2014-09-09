#!/usr/bin/env python2.7
import RPi.GPIO as GPIO
import time

# NOTE: this is the actual pin number (not the number of the GPIO)
inputPin = 26

GPIO.setmode(GPIO.BOARD)
GPIO.setup(inputPin, GPIO.IN)

counter = 0
while True:
	GPIO.wait_for_edge(inputPin, GPIO.FALLING)
	#GPIO.wait_for_edge(inputPin, GPIO.RISING)
	counter += 1
	print "Trigger no.: " + str(counter)