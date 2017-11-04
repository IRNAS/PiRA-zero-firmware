#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

import BQ2429x
import MCP3021
import smbus as smbus
import RPi.GPIO as GPIO
import time


def main():

    debug_main()
    #debug_it_all()
    time.sleep(30)


def debug_main():

    print '==============================================='
    print 'BQ2429x  : status - VBUS_STAT : ' \
        + str(sensor_bq.get_status(BQ2429x.VBUS_STAT))
    print 'BQ2429x  : status - CHRG_STAT : ' \
        + str(sensor_bq.get_status(BQ2429x.CHRG_STAT))
	print 'BQ2429x  : status - PG_STAT ---- : ' \
        + str(sensor_bq.get_status(BQ2429x.PG_STAT))
    print 'MCP3021  : status - voltage --: ' \
        + str(sensor_mcp.get_voltage()) + 'V'


def debug_it_all():

    print '==============================================='
    print 'BQ2429x  : status - VSYS ------- : ' \
        + str(sensor_bq.get_status(BQ2429x.VSYS_STAT))
    print 'BQ2429x  : status - THERM_STAT - : ' \
        + str(sensor_bq.get_status(BQ2429x.THERM_STAT))
    print 'BQ2429x  : status - PG_STAT ---- : ' \
        + str(sensor_bq.get_status(BQ2429x.PG_STAT))
    print 'BQ2429x  : status - DPM_STAT --- : ' \
        + str(sensor_bq.get_status(BQ2429x.DPM_STAT))
    print 'BQ2429x  : status - CHRG_STAT -- : ' \
        + str(sensor_bq.get_status(BQ2429x.CHRG_STAT))
    print 'BQ2429x  : status - VBUS_STAT -- : ' \
        + str(sensor_bq.get_status(BQ2429x.VBUS_STAT))
    print 'BQ2429x  : fault - NTC_FAULT --- : ' \
        + str(sensor_bq.get_faults(BQ2429x.NTC_FAULT))
    print 'BQ2429x  : fault - BAT_FAULT --- : ' \
        + str(sensor_bq.get_faults(BQ2429x.BAT_FAULT))
    print 'BQ2429x  : fault - CHRG_FAULT -- : ' \
        + str(sensor_bq.get_faults(BQ2429x.CHRG_FAULT))
    print 'BQ2429x  : fault - BOOST_FAULT - : ' \
        + str(sensor_bq.get_faults(BQ2429x.BOOST_FAULT))
    print 'BQ2429x  : fault - WATCHDOG_FAULT: ' \
        + str(sensor_bq.get_faults(BQ2429x.WATCHDOG_FAULT))
    print 'MCP3021  : status - voltage -----: ' \
        + str(sensor_mcp.get_voltage())


if __name__ == '__main__':

    # referencing the sensors

    sensor_bq = BQ2429x.BQ2429x()
    sensor_mcp = MCP3021.MCP3021()

    # configure GPIOs

    timer_en_pin = 17
    rtc_en_pin = 22
    self_en_pin = 18

    timer_done_pin = 27

    # Set GPIO mode: GPIO.BCM or GPIO.BOARD

    GPIO.setmode(GPIO.BCM)

    GPIO.setup(timer_en_pin, GPIO.IN)
    GPIO.setup(rtc_en_pin, GPIO.IN)

    # Check for power-up scenario

    timer_en_state = GPIO.input(timer_en_pin)
    rtc_en_state = GPIO.input(rtc_en_pin)

    # Self-enable

    GPIO.setup(self_en_pin, GPIO.OUT)
    GPIO.output(self_en_pin, 1)

    # Assert done for timer

    GPIO.setup(timer_done_pin, GPIO.OUT)
    GPIO.output(timer_done_pin, 1)

    # convert variable into str

    print 'Timer EN state ' + str(timer_en_state)
    print 'RTC EN state ' + str(rtc_en_state)

    while 1:
        main()
