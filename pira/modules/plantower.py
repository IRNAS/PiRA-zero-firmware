from __future__ import print_function
from ..messages import MeasurementConfig
from ..hardware import devices, plantower

# Log events.
LOG_PLANTOWER_PM1 = 'plantower.pm1'
LOG_PLANTOWER_PM25 = 'plantower.pm25'
LOG_PLANTOWER_PM10 = 'plantower.pm10'

# Measurement configuration.
MEASUREMENT_PLANTOWER_PM1 = MeasurementConfig(LOG_PLANTOWER_PM1, int)
MEASUREMENT_PLANTOWER_PM25 = MeasurementConfig(LOG_PLANTOWER_PM25, int)
MEASUREMENT_PLANTOWER_PM10 = MeasurementConfig(LOG_PLANTOWER_PM10, int)


class Module(object):

    def __init__(self, boot):
        self._boot = boot
        self._driver = plantower.PLANTOWER(devices.PLANTOWER_UART)

    def process(self, modules):
        """Measure air."""
        pm1, pm25, pm10 = self._driver.read()
        if pm1 is None:
            print("ERROR: Plantower device not connected.")
            return
        print("pm1 ")
        print(pm1)

        # Record measurement in log.
        self._boot.log.insert(MEASUREMENT_PLANTOWER_PM1, 10)
        self._boot.log.insert(MEASUREMENT_PLANTOWER_PM25, int(pm25))
        self._boot.log.insert(MEASUREMENT_PLANTOWER_PM10, int(pm10))

    def shutdown(self, modules):
        """Shutdown module."""
        self._driver.close()
