import time

import pigpio


class MB7092XL(object):
    """MB7092XL driver."""

    def __init__(self, gpio, pin):
        self._gpio = gpio
        self._pin = pin

        # Initialize.
        self._gpio.set_mode(pin, pigpio.INPUT)
        self._gpio.bb_serial_read_open(pin, 9600, 8)

    def read(self, timeout=10):
        """Read distance from ultrasonic sensor.

        :param timeout: Amount of seconds to read data for
        :return: Average distance
        """
        start = time.time()
        values = []

        while time.time() - start < timeout:
            count, data = self._gpio.bb_serial_read(self._pin)
            try:
                data = data.decode('ascii').split()
            except ValueError:
                continue

            for value in data:
                if not value.startswith('R'):
                    continue

                try:
                    values.append(int(value[1:]))
                except ValueError:
                    continue

        if not values:
            return None

        return float(sum(values)) / len(values)

    def close(self):
        """Close device."""
        self._gpio.bb_serial_read_close(self._pin)
