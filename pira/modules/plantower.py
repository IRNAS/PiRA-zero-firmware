from __future__ import print_function
from ..messages import MeasurementConfig
from ..hardware import devices, plantower

# Log events.
LOG_PLANTOWER_PM1 = 'plantower.pm1'
LOG_PLANTOWER_PM25 = 'plantower.pm25'
LOG_PLANTOWER_PM10 = 'plantower.pm10'

# Measurement configuration.
MEASUREMENT_PLANTOWER_PM1 = MeasurementConfig(LOG_PLANTOWER_PM1, float)
MEASUREMENT_PLANTOWER_PM25 = MeasurementConfig(LOG_PLANTOWER_PM25, float)
MEASUREMENT_PLANTOWER_PM10 = MeasurementConfig(LOG_PLANTOWER_PM10, float)


class Module(object):

    def __init__(self, boot):
        self._boot = boot
        self._driver = plantower.PLANTOWER(devices.PLANTOWER_UART)

    def process(self, modules):
        """Measure air."""
        self.measurements = self._driver.read()
        if self.measurements is None:
            print("ERROR: Plantower device not connected.")
            return
        pm1 = self.measurements[0]
        pm25 = self.measurements[1]
        pm10 = self.measurements[2]

        # Record measurement in log.
        self._boot.log.insert(MEASUREMENT_PLANTOWER_PM1, float(pm1))
        self._boot.log.insert(MEASUREMENT_PLANTOWER_PM25, float(pm25))
        self._boot.log.insert(MEASUREMENT_PLANTOWER_PM10, float(pm10))

    def shutdown(self, modules):
        """Shutdown module."""
        self._driver.close()
