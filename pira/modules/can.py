"""
can.py

It is a module that controls the CAN interface
"""
from __future__ import print_function

from ..messages import MeasurementConfig
from ..hardware import mcp2515


import os
import time

class Module(object):
    def __init__(self, boot):
        """ Inits the Mcp2515 """
        self._boot = boot
        self._driver = mcp2515.MCP2515()

    def process(self, modules):
        """ Sends out the data, receives """
   #     self._driver.send_data(0x01, [0x01], False)
 #       self._recv_message = self._driver.get_data()
        print("process")
    def shutdown(self):
        """ Shutdown """
        self._driver.shutdown()

