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
from ..hardware import bq2429x


class Module(object):
    def __init__(self, boot):
        self._boot = boot

    def process(self, modules):

        body = {
            'sensors.generic': {
                'device_temperature': {
                    'name': 'Temperature',
                    'unit': 'C',
                    'value': str(self._boot.rtc.temperature),
                    'group': 'temperature',
                },
                'device_voltage': {
                    'name': 'Voltage',
                    'unit': 'V',
                    'value': str(self._boot.sensor_mcp.get_voltage()),
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
