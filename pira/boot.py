from __future__ import print_function

import collections
import importlib
import os
import subprocess
import time
import traceback

import RPi.GPIO as gpio
import pigpio

# Optional Resin support.
try:
    import resin
    RESIN_ENABLED = True
except ImportError:
    RESIN_ENABLED = False

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
        'pira.modules.lora',
        'pira.modules.rockblock',
        'pira.modules.nodewatcher',
        'pira.modules.debug',
        'pira.modules.webserver',
    ]

    def __init__(self):
        self.reason = Boot.BOOT_REASON_UNKNOWN
        self.shutdown = False
        self.shutdown_hold = None
        self._charging_status = collections.deque(maxlen=4)
        self._wifi = None

    def setup_gpio(self):
        """Initialize GPIO."""
        print("Initializing GPIO...")
        while True:
            try:
                self.pigpio = pigpio.pi()
                self.pigpio.get_pigpio_version()
                break
            except:
                print("Failed to initialize connection to pigpiod. Retrying...")
                time.sleep(1)

        self.pigpio.set_mode(devices.GPIO_TIMER_STATUS_PIN, pigpio.INPUT)
        self.pigpio.set_mode(devices.GPIO_RTC_STATUS_PIN, pigpio.INPUT)

        self.pigpio.set_mode(devices.GPIO_SELF_ENABLE_PIN, pigpio.OUTPUT)
        self.pigpio.write(devices.GPIO_SELF_ENABLE_PIN, gpio.HIGH)

        self.pigpio.set_mode(devices.GPIO_ROCKBLOCK_POWER_PIN, pigpio.OUTPUT)

        self.pigpio.set_mode(devices.GPIO_TIMER_DONE_PIN, pigpio.OUTPUT)

        #Make GPIO always on so ti can be used to supply power to a switch
        self.pigpio.set_mode(devices.GPIO_SOFT_POWER_PIN, pigpio.OUTPUT)
        self.pigpio.write(devices.GPIO_SOFT_POWER_PIN, gpio.LOW)

    def setup_devices(self):
        """Initialize device drivers."""
        print("Initializing device drivers...")
        self.sensor_bq = bq2429x.BQ2429x()
        self.sensor_mcp = mcp3021.MCP3021()
        self.rtc = rtc.RTC()

    def setup_wifi(self):
        """Setup wifi."""
        if not self.is_wifi_enabled:
            print("Not starting wifi as it is disabled.")
            return

        # Enable wifi.
        print("Enabling wifi.")
        try:
            if RESIN_ENABLED:
                self._wifi = subprocess.Popen(["./scripts/wifi-connect-start.sh"])
                pass
            else:
                subprocess.call(["./scripts/start-networking.sh"])
        except:
            print("ERROR: Failed to start wifi-connect.")

    def boot(self):
        """Perform boot sequence."""
        print("Performing boot sequence.")

        if os.environ.get('BOOT_DISABLE', '0') == '1':
            print("Boot has been disabled (BOOT_DISABLE=1). Not booting further.")
            while True:
                time.sleep(1)

        self.setup_gpio()
        self.setup_devices()
        self.setup_wifi()

        self.state = State()
        self.log = Log()
        self.log.insert(LOG_SYSTEM, 'boot')

        self._update_charging()

        # Determine boot reason.
        timer_en_state = self.pigpio.read(devices.GPIO_TIMER_STATUS_PIN)
        rtc_en_state = self.pigpio.read(devices.GPIO_RTC_STATUS_PIN)

        if timer_en_state == gpio.LOW and rtc_en_state == gpio.HIGH:
            # Boot from either timer of self.
            # TODO: Figure out method for detection of the two later.
            self.reason = Boot.BOOT_REASON_TIMER
        elif timer_en_state == gpio.HIGH and rtc_en_state == gpio.LOW:
            if not self.is_charging:
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

        # Disable charge timer, configure pre-charge. THIS IS IMPORTANT
        # Bit 7 EN_TERM 1 Enabled
        # Bit 6 Reserved 0
        #I2C Watchdog Timer Setting - MUST be disabled with 00, otherwise resets
        #Bit 5 WATCHDOG[1] 0
        #Bit 4 WATCHDOG[0] 0
        #Charging Safety Timer Enable - MUST be disabled if device is on permanently
        #Bit 3 EN_TIMER 0
        #Bit 2 CHG_TIMER[1] R/W 1
        #Bit 1 CHG_TIMER[0] R/W 0
        #Bit 0 Reserved R/W 0

        self.sensor_bq.set_charge_termination(10000010)

        # Precharge must be higher then self-consumption, in multi-cell can be 2A
        # Termination must be lower then self-consumption
        self.sensor_bq.set_ter_prech_current(1111, 0001)

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
                print("ImportError  * {} [IMPORT FAILED]".format(module_name))
                continue
            except ValueError:
                print("ValueError  * {} [IMPORT FAILED]".format(module_name))
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
            self._update_charging()
            # Shutdown hold is reset in every loop
            self.shutdown_hold = None

            # Store some general log entries.
            self.log.insert(LOG_DEVICE_VOLTAGE, self.sensor_mcp.get_voltage())
            self.log.insert(LOG_DEVICE_TEMPERATURE, self.rtc.temperature)

            # Process all modules.
            for name, module in self.modules.items():
                try:
                    module.process(self.modules)
                except:
                    print("Error while running processing in module '{}'.".format(name))
                    traceback.print_exc()

            # Check if battery voltage is below threshold and shutdown
            if (self.sensor_mcp.get_voltage() <= os.environ.get('SHUTDOWN_VOLTAGE', '2.6')):
                print("Voltage is under the threshold, need to shutdown.")
                self.shutdown = True

            # Save state.
            try:
                self.state.save()
            except:
                print("Error while saving state.")
                traceback.print_exc()

            if self.shutdown:
                # Perform shutdown when requested. This will either request the Resin
                # supervisor to shut down and block forever or the shutdown request will
                # be ignored and we will continue processing.
                self.shutdown = False
                self._perform_shutdown()

            time.sleep(os.environ.get('LOOP_DELAY', 30))

    def _update_charging(self):
        """Update charging status."""
        not_charging = (
            self.sensor_bq.get_status(bq2429x.VBUS_STAT) == 'No input' and
            self.sensor_bq.get_status(bq2429x.CHRG_STAT) == 'Not charging' and
            self.sensor_bq.get_status(bq2429x.PG_STAT) == 'Not good power'
        )
        self._charging_status.append(not not_charging)

    @property
    def is_charging(self):
        return any(self._charging_status)

    @property
    def is_wifi_enabled(self):
        wifi_mode = os.environ.get('WIFI_ENABLE_MODE', 'charging')

        if wifi_mode == 'charging':
            return self.is_charging == 1
        elif wifi_mode == 'on':
            return True
        elif wifi_mode == 'debug':
            return self.is_debug_enabled == 1
        elif wifi_mode == 'off':
            return False

    @property
    def is_debug_enabled(self):
        debug_mode = os.environ.get('DEBUG_ENABLE_MODE', 'none')

        if debug_mode.startswith('gpio:'):
            # Based on GPIO.
            try:
                _, pin = debug_mode.split(':')
                pin = int(pin)
            except ValueError:
                print("Invalid GPIO pin specified for debug.")
                return True

            # Read from given GPIO pin.
            self.pigpio.set_mode(pin, pigpio.INPUT)
            return self.pigpio.read(pin) == gpio.LOW

    def shutdown(self):
        """Request shutdown."""
        print("Module has requested shutdown.")
        self.shutdown = True

    def _perform_shutdown(self):
        """Perform shutdown."""

        sleep_mode = os.environ.get('SLEEP_ENABLE_MODE', 'sleep')

        if sleep_mode == 'charging' and self.is_charging == 1:
            print("Not shutting down: Charging.")
            return
        elif sleep_mode == 'off':
            print("Not shutting down: Sleep off.")
            return
        elif sleep_mode == 'sleep':
            pass

        if sleep_mode == 'debug' and self.is_debug_enabled == 1:
            print("Shutting down even during debug.")
            pass
        elif self.is_debug_enabled == 1:
            print("Not shutting down: Debug on.")
            return

        if not self.shutdown_hold == None:
            print("Not shutting down: On hold due to: "+self.shutdown_hold)
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
            if self._wifi:
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
        self.log.close()

        # Force filesystem sync.
        try:
            subprocess.call('sync')
        except:
            print("Error while forcing filesystem sync.")
            traceback.print_exc()

        self.clear_alarms()

        self.shutdown_strategy = os.environ.get('SHUTDOWN_STRATEGY', 'reboot')

        # Configurable shutdown strategy, shutdown as an option, reboot as default
        # TODO: handle error curl: (7) Failed to connect to 127.0.0.1 port 48484: Connection refused

        if self.shutdown_strategy == 'shutdown':
            # Shutdown will clear the self-enable pin by default.
            if RESIN_ENABLED:
                subprocess.call(["/usr/src/app/scripts/resin-shutdown.sh"])
            else:
                subprocess.Popen(["/sbin/shutdown", "--poweroff", "now"])
        elif self.shutdown_strategy == 'safe':
            # Shutdown will clear the self-enable pin by default.
            if RESIN_ENABLED:
                subprocess.call(["/usr/src/app/scripts/resin-reboot.sh"])
            else:
                subprocess.Popen(["/sbin/shutdown", "--reboot", "now"])
        else:
            # Turn off the self-enable pin then reboot as safety if enabled by another source
            print('Shutting down as scheduled.')
            self.pigpio.write(devices.GPIO_SELF_ENABLE_PIN, gpio.LOW)

            if RESIN_ENABLED:
                subprocess.call(["/usr/src/app/scripts/resin-reboot.sh"])
            else:
                subprocess.Popen(["/sbin/shutdown", "--reboot", "now"])

        # Block.
        while True:
            time.sleep(1)
