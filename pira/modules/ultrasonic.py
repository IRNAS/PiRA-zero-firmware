from __future__ import print_function

from ..messages import MeasurementConfig
from ..hardware import devices, ultrasonic

# Log events.
LOG_ULTRASONIC_DISTANCE = 'ultrasonic.distance'

# Measurement configuration.
MEASUREMENT_ULTRASONIC_DISTANCE = MeasurementConfig(LOG_ULTRASONIC_DISTANCE, int)


class Module(object):
    # Last measured distance that can be accessed by other modules.
    distance = None

    def __init__(self, boot):
        self._boot = boot
        self._driver = ultrasonic.MB7092XL(boot.pigpio, devices.GPIO_ULTRASONIC_RX_PIN)

    def process(self, modules):
        """Measure distance."""
        self.distance = self._driver.read()
        if self.distance is None:
            print("ERROR: Ultrasonic device not connected.")
            return

        # Record measurement in log.
        self._boot.log.insert(LOG_ULTRASONIC_DISTANCE, self.distance)

    def shutdown(self, modules):
        """Shutdown module."""
        self._driver.close()
