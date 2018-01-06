from __future__ import print_function

import base64
import collections
import hashlib
import hmac
import json
import os

import requests
import yaml

from ..const import MEASUREMENT_DEVICE_VOLTAGE, MEASUREMENT_DEVICE_TEMPERATURE
from ..messages import create_measurements_message


class Module(object):
    def __init__(self, boot):
        self._boot = boot

    def process(self, modules):

        # Transmit message.
        measurements = [
            MEASUREMENT_DEVICE_TEMPERATURE,
            MEASUREMENT_DEVICE_VOLTAGE,
        ]

        if 'pira.modules.ultrasonic' in modules:
            from .ultrasonic import MEASUREMENT_ULTRASONIC_DISTANCE
            measurements.append(MEASUREMENT_ULTRASONIC_DISTANCE)

        body = {
            'sensors.generic': {
                'device_temperature': {
                    'name': 'Temperature',
                    'unit': 'C',
                    'value': measurements.MEASUREMENT_DEVICE_TEMPERATURE,
                    'group': 'temperature',
                },
                'device_voltage': {
                    'name': 'Voltage',
                    'unit': 'V',
                    'value': measurements.MEASUREMENT_DEVICE_VOLTAGE,
                    'group': 'voltage',
                },
            }
        }

        for sensor_id, value in list(body['sensors.generic'].items()):
            if 'value' not in value:
                continue

            if value['value'] is None:
                del body['sensors.generic'][sensor_id]

        self.nodewatcher_push(body)


    def shutdown(self, modules):
        print("Shutting down nodewatcher module.")

    def nodewatcher_uri_for_node(uuid):
        """Generate nodewatcher push URI for a specific node.

        :param uuid: node uuid
        """
        return 'http://{host}/push/http/{uuid}'.format(
            host=get_config('nodewatcher.host'),
            uuid=uuid,
        )


    def nodewatcher_push(body, ignore_errors=True):
        """Push data to nodewatcher server.

        :param uuid: node uuid
        :param body: correctly formatted request body
        :param ignore_errors: whether errors should be silently ignored
        """
        body = json.dumps(body)

        uuid = os.environ.get('NODEWATCHER_UUID', None),
        host = os.environ.get('NODEWATCHER_HOST', None),
        key = os.environ.get('NODEWATCHER_KEY', None),

        # Check if nodewatcher push is correctly configured
        if uuid == None or host == None or key == None:
            print("Nodewatcher push not configured")
            return

        nodewatcher_uri = 'http://{host}/push/http/{uuid}'.format(
            host=host,
            uuid=uuid,
        )


        signature = base64.b64encode(hmac.new(key, body, hashlib.sha256).digest())

        try:
            requests.post(
                nodewatcher_uri,
                data=body,
                headers={
                    'X-Nodewatcher-Signature-Algorithm': 'hmac-sha256',
                    'X-Nodewatcher-Signature': signature,
                }
            )
        except:
            if not ignore_errors:
                raise
