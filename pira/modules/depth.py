import ms5837
import time
from __future__ import print_function
from ..messages import MeasurementConfig
from ..hardware import devices, plantower
import os

# Log events.
LOG_DEPTH_DEPTH = 'depth.depth'
LOG_DEPTH_ALTITUDE = 'depth.altitude'
LOG_DEPTH_PRESSURE = 'depth.pressure'
LOG_DEPTH_TEMPERATURE = 'depth.temperature'

# Measurement configuration.
MEASUREMENT_DEPTH_DEPTH = MeasurementConfig(LOG_DEPTH_DEPTH, int)
MEASUREMENT_DEPTH_ALTITUDE = MeasurementConfig(LOG_DEPTH_ALTITUDE, int)
MEASUREMENT_DEPTH_PRESSURE = MeasurementConfig(LOG_DEPTH_PRESSURE, int)
MEASUREMENT_DEPTH_TEMPERATURE = MeasurementConfig(LOG_DEPTH_TEMPERATURE, int)


class Module(object):
    def __init__(self, boot):
        self._boot = boot
        self._driver = ms5837.MS5837(model=ms5837.MS5837_MODEL_30BA, bus=1)

    def process(self, modules):
        # We have to read values from sensor to update pressure and temperature
        if not self._driver.read():
            print("Depth sensor read failed!")

        pressure = self._driver.pressure(ms5837.UNITS_mbar)
        temperature = self._driver.temperature(ms5837.UNITS_Centigrade)
        self._driver.setFluidDensity(ms5837.DENSITY_SALTWATER)
        depth = self._driver.depth()
        altitude = self._driver.altitude() # relative to Mean Sea Level pressure in air

        print("Pressure:", pressure, " mbar  depth:", depth, " m  altitude:", altitude, "m temperature", temperature, " C")

        # Record measurement in log.
        self._boot.log.insert(LOG_DEPTH_DEPTH, int(depth))
        self._boot.log.insert(LOG_DEPTH_DEPTH, int(altitude))
        self._boot.log.insert(LOG_DEPTH_PRESSURE, int(pressure))
        self._boot.log.insert(LOG_DEPTH_TEMPERATURE, int(ptemperaturem10))

    def shutdown(self, modules):
        """Shutdown module."""
        self._driver.close()
