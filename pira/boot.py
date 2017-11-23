from __future__ import print_function

import collections
import importlib
import os
import subprocess
import time
import traceback

import RPi.GPIO as gpio
import pigpio
import resin

from .hardware import devices, bq2429x, mcp3021, rtc
from .state import State
from .log import Log
from .const import LOG_SYSTEM, LOG_DEVICE_VOLTAGE, LOG_DEVICE_TEMPERATURE


class Boot(object):
    """Boot handling."""
    BOOT_REASON_UNKNOWN = 'unknown'
    BOOT_REASON_SELF = 'self'
    BOOT_REASON_TIMER = 'timer'
    BOOT_REASON_CHARGER = 'charger'
    BOOT_REASON_RTC = 'rtc'

    # Modules that should be loaded.
    enabled_modules = [
        'pira.modules.scheduler',
        # Sensor modules.
        'pira.modules.ultrasonic',
        'pira.modules.camera',
        # Reporting modules should come after all sensor modules, so they can get
        # the latest values.
        'pira.modules.rockblock',
        'pira.modules.debug',
        'pira.modules.webserver',
    ]

    def __init__(self):
        self.reason = Boot.BOOT_REASON_UNKNOWN
        self._resin = resin.Resin()
        self._shutdown = False

    def setup_gpio(self):
        """Initialize GPIO."""
        print("Initializing GPIO...")
        self.pigpio = pigpio.pi()

        self.pigpio.set_mode(devices.GPIO_TIMER_STATUS_PIN, pigpio.INPUT)
        self.pigpio.set_mode(devices.GPIO_RTC_STATUS_PIN, pigpio.INPUT)

        self.pigpio.set_mode(devices.GPIO_SELF_ENABLE_PIN, pigpio.OUTPUT)
        self.pigpio.write(devices.GPIO_SELF_ENABLE_PIN, gpio.HIGH)

        self.pigpio.set_mode(devices.GPIO_ROCKBLOCK_POWER_PIN, pigpio.OUTPUT)

        self.pigpio.set_mode(devices.GPIO_TIMER_DONE_PIN, pigpio.OUTPUT)

    def setup_devices(self):
        """Initialize device drivers."""
        print("Initializing device drivers...")
        self.sensor_bq = bq2429x.BQ2429x()
        self.sensor_mcp = mcp3021.MCP3021()
        self.rtc = rtc.RTC()

    def setup_wifi(self):
        """Setup wifi."""
        enable_when_not_charging = os.environ.get('WIFI_WHEN_NOT_CHARGING', '1') == '1'
        if not self.is_charging and not enable_when_not_charging:
            print("Not starting wifi as we are not charging.")
            return

        # Enable wifi.
        print("Enabling wifi.")
        try:
            self._wifi = subprocess.Popen(["./wifi-connect", "--clear=false"])
        except:
            print("ERROR: Failed to start wifi-connect.")

    def boot(self):
        """Perform boot sequence."""
        print("Performing boot sequence.")

        self.setup_gpio()
        self.setup_devices()
        self.setup_wifi()

        self.state = State()
        self.log = Log()
        self.log.insert(LOG_SYSTEM, 'boot')

        # Determine boot reason.
        timer_en_state = self.pigpio.read(devices.GPIO_TIMER_STATUS_PIN)
        rtc_en_state = self.pigpio.read(devices.GPIO_RTC_STATUS_PIN)

        if timer_en_state == gpio.LOW and rtc_en_state == gpio.HIGH:
            # Boot from either timer of self.
            # TODO: Figure out method for detection of the two later.
            self.reason = Boot.BOOT_REASON_TIMER
        elif timer_en_state == gpio.HIGH and rtc_en_state == gpio.LOW:
            if self.sensor_bq.get_status(bq2429x.CHRG_STAT) == "Not charging":
                # Boot due to RTC.
                self.reason = Boot.BOOT_REASON_RTC
            else:
                # Boot due to charging power.
                self.reason = Boot.BOOT_REASON_CHARGER
        else:
            # Boot reason unknown.
            self.reason = Boot.BOOT_REASON_UNKNOWN

        # Clear timer and RTC alarms.
        self.clear_alarms()

        # Disable charge timer, configure pre-charge.
        self.sensor_bq.set_charge_termination(10010010)
        self.sensor_bq.set_ter_prech_current(1111, 0111)

        # Monitor timer pin and clear alarms while we are running.
        self.pigpio.callback(
            devices.GPIO_TIMER_STATUS_PIN,
            pigpio.FALLING_EDGE,
            self.clear_timer
        )

        print("Boot reason: {}".format(self.reason))

        print("RTC Time: {}".format(self.rtc.current_time.isoformat()))
        print("RTC Alarm 1: {}".format(self.rtc.alarm1_time.isoformat()))
        print("RTC Alarm 2: {}".format(self.rtc.alarm2_time.isoformat()))

        self.process()

    def clear_alarms(self):
        """Clear all alarms."""
        self.pigpio.write(devices.GPIO_TIMER_DONE_PIN, gpio.HIGH)
        self.rtc.alarm1_clear()
        self.rtc.alarm2_clear()

    def clear_timer(self, pin, level, tick):
        """Clear timer alarms while we are running."""
        print("Clearing timer alarm.")
        self.pigpio.write(devices.GPIO_TIMER_DONE_PIN, gpio.HIGH)

    def process(self):
        self.log.insert(LOG_SYSTEM, 'module_init')

        # Override module list if configured.
        override_modules = os.environ.get('MODULES', None)
        if override_modules:
            print("Only loading configured modules.")
            self.enabled_modules = override_modules.strip().split(',')

        # Initialize modules.
        print("Initializing modules...")
        self.modules = collections.OrderedDict()
        for module_name in self.enabled_modules:
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                print("  * {} [IMPORT FAILED]".format(module_name))
                continue

            print("  * {}".format(module.__name__))

            try:
                instance = module.Module(self)
                self.modules[module.__name__] = instance
            except:
                print("Error while initializing a module.")
                traceback.print_exc()

        self.log.insert(LOG_SYSTEM, 'main_loop')

        # Enter main loop.
        print("Starting processing loop.")
        while True:
            # Process all modules.
            for name, module in self.modules.items():
                try:
                    module.process(self.modules)
                except:
                    print("Error while running processing in module '{}'.".format(name))
                    traceback.print_exc()

            # Store some general log entries.
            self.log.insert(LOG_DEVICE_VOLTAGE, self.sensor_mcp.get_voltage())
            self.log.insert(LOG_DEVICE_TEMPERATURE, self.rtc.temperature)

            # Save state.
            try:
                self.state.save()
            except:
                print("Error while saving state.")
                traceback.print_exc()

            if self._shutdown:
                # Perform shutdown when requested. This will either request the Resin
                # supervisor to shut down and block forever or the shutdown request will
                # be ignored and we will continue processing.
                self._shutdown = False
                self._perform_shutdown()

            time.sleep(30)

    @property
    def should_sleep_when_charging(self):
        return os.environ.get('SLEEP_WHEN_CHARGING', '0') == '1'

    @property
    def should_never_sleep(self):
        return os.environ.get('SLEEP_NEVER', '0') == '1'

    @property
    def is_charging(self):
        return self.sensor_bq.get_status(bq2429x.CHRG_STAT) != "Not charging"

    def shutdown(self):
        """Request shutdown."""
        print("Module has requested shutdown.")
        self._shutdown = True

    def _perform_shutdown(self):
        """Perform shutdown."""
        if self.is_charging and not self.should_sleep_when_charging:
            print("Not shutting down as we are charging and are configured to not sleep when charging.")
            return

        if self.should_never_sleep:
            print("Not shutting down as we should never sleep.")
            return

        self.log.insert(LOG_SYSTEM, 'shutdown')

        print("Requesting all modules to shut down.")
        for name, module in self.modules.items():
            try:
                module.shutdown(self.modules)
            except:
                print("Error while running shutdown in module '{}'.".format(name))
                traceback.print_exc()

        # Shut down devices.
        try:
            self._wifi.kill()
        except:
            print("Error while shutting down devices.")
            traceback.print_exc()

        # Save state.
        try:
            self.state.save()
        except:
            print("Error while saving state.")
            traceback.print_exc()

        self.log.insert(LOG_SYSTEM, 'halt')

        # Force filesystem sync.
        try:
            subprocess.call('sync')
        except:
            print("Error while forcing filesystem sync.")
            traceback.print_exc()

        self.clear_alarms()

        # Go to sleep if charging is not connected.
        print('Shutting down as scheduled.')
        self.pigpio.write(devices.GPIO_SELF_ENABLE_PIN, gpio.LOW)
        self._resin.models.supervisor.restart(
            device_uuid=os.environ['RESIN_DEVICE_UUID'],
            app_id=os.environ['RESIN_APP_ID']
        )

        # Block.
        while True:
            time.sleep(1)
