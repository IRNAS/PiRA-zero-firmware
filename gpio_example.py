#!/usr/bin/python

import RPi.GPIO as GPIO
import time
#import logging

#logging.basicConfig(format='%(levelname)s-%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG,filename='/App/gpio.log')

timer_en_pin = 17
rtc_en_pin = 22
self_en_pin = 18

# Set GPIO mode: GPIO.BCM or GPIO.BOARD
GPIO.setmode(GPIO.BCM)

GPIO.setup(timer_en_pin, GPIO.IN)
GPIO.setup(rtc_en_pin, GPIO.IN)

# Check for power-up scenario
timer_en_state = GPIO.input(timer_en_pin)
rtc_en_state = GPIO.input(rtc_en_pin)

# Self-enable
GPIO.setup(self_en_pin, GPIO.OUT, initial=GPIO.HIGH)

#convert variable into str
print("Timer EN state " + str(timer_en_state))
print("RTC EN state " + str(rtc_en_state))

# GPIO pins list based on GPIO.BOARD
# gpioList1 = [3,5,7,8,10,11,12,13,15]
# gpioList2 = [16,18,19,21,22,23,24,26]

# Set mode for each gpio pin
# GPIO.setup(gpioList1, GPIO.OUT)
# GPIO.setup(gpioList2, GPIO.OUT)

while True:
	# Change gpio pins in list 1 from low to high and list 2 from high to low
    time.sleep(1)
# Reset all gpio pin
GPIO.cleanup()
