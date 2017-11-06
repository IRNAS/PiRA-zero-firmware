#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

import BQ2429x
import MCP3021
import smbus as smbus
import RPi.GPIO as GPIO
import time
import os
from resin import Resin
resin = Resin()

# unknown booot reason init
boot_reason = 0

def main():

    debug_main()
    # debug_it_all()
    time.sleep(30)

    ## Go to sleep if charging is not connected
    if sensor_bq.get_status(BQ2429x.CHRG_STAT) == "Not charging" and \
       os.environ['SLEEP_WHEN_CHARGING'] == '1':
        resin.models.supervisor.shutdown(device_uuid=os.environ['RESIN_DEVICE_UUID'], app_id=os.environ['RESIN_APP_ID'])
        print 'Shutting down as scheduled.'

    ## implement monitor pin for timer alarms and clear them in real time

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

# determining what the surce of booting was
boot_reason_data = {
    0 : "unknown",
    1 : "Self enable",
    2 : "Timer enable",
    3 : "Power enable",
    4 : "RTC enable"
}

if __name__ == '__main__':

    try:
        #check system variables
        #charging action if system should stay on when on charge, default on
        charging_action=os.getenv('SLEEP_WHEN_CHARGING', 1)

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
        GPIO.setwarnings(False)

        GPIO.setup(timer_en_pin, GPIO.IN)
        GPIO.setup(rtc_en_pin, GPIO.IN)

        # Self-enable
        GPIO.setup(self_en_pin, GPIO.OUT)
        GPIO.output(self_en_pin, 1)

        # Check for power-up scenario

        timer_en_state = GPIO.input(timer_en_pin)
        rtc_en_state = GPIO.input(rtc_en_pin)

        if timer_en_state == 0 and \
           rtc_en_state == 1:
            # boot from either timer of self
            # figure out method for detection of the two later
            # boot due to Self-enable or timer
            boot_reason = 2
        elif timer_en_state == 1 and \
             rtc_en_state == 0:
            if sensor_bq.get_status(BQ2429x.CHRG_STAT) == "Not charging":
                #boot due to RTC
                boot_reason = 4
            else:
                # boot due to power enable
                boot_reason = 3
        else:
            #unknown boot reason
            boot_reason = 0

        # Assert done for timer

        GPIO.setup(timer_done_pin, GPIO.OUT)
        GPIO.output(timer_done_pin, 1)

        # convert variable into str

        print 'Boot source: ' + boot_reason_data[boot_reason]

        print 'Disable charge timer'
        sensor_bq.set_charge_termination(10010010)
        print 'Configure pre-charge'
        sensor_bq.set_ter_prech_current(1111,0001)

        while 1:
            main()
    except Exception as e:
        print "other error"
        print(e)
    finally:
        #GPIO.cleanup() # must not be used as it disables the self-enable
        print "Exiting..."
        # shut down if there is an error, disabled for debugging
        #resin.models.supervisor.shutdown(device_uuid=os.environ['RESIN_DEVICE_UUID'], app_id=os.environ['RESIN_APP_ID'])
        #print 'Shutting down due to an error.
