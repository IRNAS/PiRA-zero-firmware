from __future__ import print_function

import datetime
import io
import os
import struct

from ..hardware import devices, lora
from ..const import LOG_DEVICE_VOLTAGE, LOG_DEVICE_TEMPERATURE

# Persistent state.
STATE_FRAME_COUNTER = 'lora.frame_counter'


class LoRa(lora.LoRa):
    def on_tx_done(self):
        self.set_mode(lora.MODE.STDBY)
        self.clear_irq_flags(TxDone=1)


class Module(object):
    def __init__(self, boot):
        self._boot = boot
        self._lora = None
        self._last_update = datetime.datetime.now()
        self._frame_counter = boot.state[STATE_FRAME_COUNTER] or 1

        # Parse configuration.
        try:
            self._device_addr = self._decode_hex('LORA_DEVICE_ADDR', length=4)
            self._nws_key = self._decode_hex('LORA_NWS_KEY', length=16)
            self._apps_key = self._decode_hex('LORA_APPS_KEY', length=16)
            self._enabled = True
        except:
            self._enabled = False

    def _decode_hex(self, name, length):
        """Decode hex-encoded environment variable."""
        value = [ord(x) for x in os.environ.get(name, '').decode('hex')]
        if len(value) != length:
            raise ValueError

        return value

    def process(self, modules):
        if not self._enabled:
            print("WARNING: LoRa is not correctly configured, skipping.")
            return

        # Initialize LoRa driver if needed.
        if not self._lora:
            lora.board.setup()

            self._lora = LoRa(verbose=False)
            self._lora.set_mode(lora.MODE.SLEEP)
            self._lora.set_dio_mapping([1, 0, 0, 0, 0, 0])
            self._lora.set_freq(868.1)
            self._lora.set_pa_config(pa_select=1)
            self._lora.set_spreading_factor(7)
            self._lora.set_pa_config(max_power=0x0F, output_power=0x0E)
            self._lora.set_sync_word(0x34)
            self._lora.set_rx_crc(True)

        # Check if we need to transmit something.

        # Transmit message.
        measurements = [
            LOG_DEVICE_TEMPERATURE,
            LOG_DEVICE_VOLTAGE,
        ]

        if 'pira.modules.ultrasonic' in modules:
            from .ultrasonic import LOG_ULTRASONIC_DISTANCE
            measurements.append(LOG_ULTRASONIC_DISTANCE)

        # Message format (network byte order):
        # - 4 bytes: unsigned integer, number of measurements
        # - 4 bytes: float, average
        # - 4 bytes: float, min
        # - 4 bytes: float, max
        message = io.BytesIO()
        for event_type in measurements:
            values = self._boot.log.query(self._last_update, event_type, only_numeric=True)

            # Compute statistics.
            if values:
                count = len(values)
                average = sum(values) / count
                min_value = min(values)
                max_value = max(values)
            else:
                count = 0
                average = 0.0
                min_value = 0.0
                max_value = 0.0

            message.write(struct.pack('!Lfff', count, average, min_value, max_value))

        message = message.getvalue()
        print("Transmitting message ({} bytes) via LoRa...".format(len(message)))

        payload = lora.LoRaWANPayload(self._nws_key, self._apps_key)
        payload.create(
            lora.MHDR.UNCONF_DATA_UP,
            {
                'devaddr': self._device_addr,
                'fcnt': self._frame_counter % 2**16,
                'data': list([ord(x) for x in message]),
            }
        )

        self._lora.write_payload(payload.to_raw())
        self._lora.set_mode(lora.MODE.TX)
        self._last_update = datetime.datetime.now()
        self._frame_counter += 1
        self._boot.state[STATE_FRAME_COUNTER] = self._frame_counter % 2**16

    def shutdown(self, modules):
        pass
