from __future__ import print_function

from ..hardware import bq2429x


class Module(object):
    def __init__(self, boot):
        self._boot = boot

    def process(self, modules):
        print('===============================================')
        print('BQ2429x  : status - VBUS_STAT : ' + str(self._boot.sensor_bq.get_status(bq2429x.VBUS_STAT)))
        print('BQ2429x  : status - CHRG_STAT : ' + str(self._boot.sensor_bq.get_status(bq2429x.CHRG_STAT)))
        print('BQ2429x  : status - PG_STAT ---- : ' + str(self._boot.sensor_bq.get_status(bq2429x.PG_STAT)))
        print('MCP3021  : status - voltage --: ' + str(self._boot.sensor_mcp.get_voltage()) + 'V')
        print('Charging : {}'.format(self._boot.is_charging))
        print('Debug    : {}'.format(self._boot.is_debug_enabled))
        print('RTC      : {}'.format(self._boot.rtc.current_time))
        print('Temp.    : {}'.format(self._boot.rtc.temperature))

        # Report distance measured by ultrasonic module if enabled.
        if 'pira.modules.ultrasonic' in modules:
            print('Distance : {}'.format(modules['pira.modules.ultrasonic'].distance))

    def shutdown(self, modules):
        """Shutdown module."""
        pass
