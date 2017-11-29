from __future__ import print_function

import contextlib
import datetime
import io
import os
import struct
import time

import dateutil.parser
import RPi.GPIO as gpio

from ..hardware import devices, rockblock
from ..const import MEASUREMENT_DEVICE_VOLTAGE, MEASUREMENT_DEVICE_TEMPERATURE
from ..messages import create_measurements_message

# Persistent state.
STATE_POWERED_ON_TIME = 'rockblock.powered_on_time'
STATE_RETRIES = 'rockblock.retries'


class Module(object):
    def __init__(self, boot):
        self._boot = boot

        # Power on interval (in hours).
        try:
            self._interval = int(os.environ.get('ROCKBLOCK_REPORT_INTERVAL', '24'))
        except ValueError:
            print("ERROR: Malformed Rockblock reporting interval.")
            self._interval = 24

        # Maximum number of retries.
        try:
            self._max_retries = int(os.environ.get('ROCKBLOCK_RETRIES', '2'))
        except ValueError:
            self._max_retries = 2

        self._power = False

    def process(self, modules):
        # Check if we have powered on the modem today.
        current_time = datetime.datetime.now()
        powered_on_time = self._boot.state[STATE_POWERED_ON_TIME]
        if powered_on_time is not None and current_time - powered_on_time < datetime.timedelta(hours=self._interval):
            print("Already transmitted measurements today, not powering up Rockblock.")
            return

        # Power up modem. We leave it powered on until a message is successfully delivered or
        # we go back to sleep (whichever comes first).
        self.power_on_modem()

        # Initialize modem driver.
        modem = None
        try:
            modem = rockblock.rockBlock(devices.ROCKBLOCK_UART, rockblock.rockBlockProtocol())
        except rockblock.rockBlockException:
            print("ERROR: Failed to initialize Rockblock modem.")
            return

        serial_id = modem.getSerialIdentifier()
        signal = modem.requestSignalStrength()
        net_time = modem.networkTime()
        print("Rockblock serial id:", serial_id)
        print("Rockblock signal strength:", signal)
        print("Rockblock network time:", net_time)

        # Transmit message.
        measurements = [
            MEASUREMENT_DEVICE_TEMPERATURE,
            MEASUREMENT_DEVICE_VOLTAGE,
        ]

        if 'pira.modules.ultrasonic' in modules:
            from .ultrasonic import MEASUREMENT_ULTRASONIC_DISTANCE
            measurements.append(MEASUREMENT_ULTRASONIC_DISTANCE)

        message = create_measurements_message(self._boot, powered_on_time, measurements)
        if not message:
            return

        print("Transmitting message ({} bytes) via Rockblock...".format(len(message)))

        if not modem.sendMessage(message):
            print("ERROR: Failed to send message.")
            return

        # Power off modem and reset interval.
        self.power_off_modem()
        self.reset_interval()

    def power_on_modem(self):
        """Power on modem."""
        if self._power:
            return

        print("Powering on Rockblock modem.")
        self._boot.pigpio.write(devices.GPIO_ROCKBLOCK_POWER_PIN, gpio.HIGH)
        self._power = True
        time.sleep(5)

    def power_off_modem(self):
        """Power off modem."""
        print("Powering off Rockblock modem.")
        self._boot.pigpio.write(devices.GPIO_ROCKBLOCK_POWER_PIN, gpio.LOW)
        self._power = False

    def reset_interval(self):
        """Mark transmission as done in the current interval."""
        self._boot.state[STATE_POWERED_ON_TIME] = datetime.datetime.now()
        self._boot.state[STATE_RETRIES] = 0

    def shutdown(self, modules):
        # If we are out of retries, reset retry counter and powered on time.
        retries = self._boot.state[STATE_RETRIES] or 0
        if self._power:
            # Modem is still powered, this means that we failed to send a message.
            self.power_off_modem()

            retries += 1
            self._boot.state[STATE_RETRIES] = retries
            if retries >= self._max_retries:
                print("Maximum number of Rockblock retries reached.")
                self.reset_interval()
