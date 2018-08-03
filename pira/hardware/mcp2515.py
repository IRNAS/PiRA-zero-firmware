"""
mcp2515.py

Is the hardware that connects to the mcp2515

ENV VARS:
    - CAN_SPEED (default 500000)
"""

from __future__ import print_function

import os
import time
import can



class MCP2515():
    def __init__(self):
        """
        Inits MCP2515 at a baudrate and sets up the bus and the link
        """
        self._bitrate = os.environ.get('CAN_SPEED', '500000')
        self._enabled = False
        
        # DEBUG
        #os.system("ifconfig")
        
        # setup the link
        self.os_string = 'ip link set can0 up type can bitrate {}'.format(self._bitrate)
        print("Executing {}".format(self.os_string))
        try:
            # execute the link
            os.system(self.os_string)
            
            try:
                # create can object
                self._bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
                self._enabled = True
            except OSError:
                print("Cannot find CAN board")
                self._enabled = False

        except OSError:
            print("Failed to os execute")

    def get_enabled(self):
        """ check if enabled """
        return self._enabled
    def get_data(self):
        """ waits until nothing received """
        self._message = self._bus.recv()
        if self._message is not None:
            c = '{0:f} {1:x} {2:x} '.format(self._message.timestamp, self._message.arbitration_id, self._message.dlc)
            s = ''
            for i in range(self._message.dlc):
                s += '{0:x} '.format(self._message.data[i])
            
            print(' {}'.format(c+s))
            return self._message
        
        return None

    def send_data(self, ID, DATA, EXTID):
        """ sends data by ID, DATA and if y/n EXTID """
        self._ID = ID
        self._DATA = DATA
        self._EXTID = EXTID
        self._message = can.Message(arbitration_id=self._ID, data=self._DATA, extended_id=self._EXTID)
        self._bus.send(self._message)
        print("Sent to {}, data: {}".format(self._ID, self._DATA))

    def format_data_timestamp(self, msg):
        """ only get timestamp from msg """
        self._format_msg = msg
        return self._format_msg.timestamp

    def format_data_id(self, msg):
        """ only get ID from msg """
        self._format_msg = msg
        return self._format_msg.arbitration_id

    def format_data_dlc(self, msg):
        """ only get DLC from msg """
        self._format_msg = msg
        return self._format_msg.dlc
    
    def shutdown(self):
        """ shutdown the link """
        os.system("ip link set can0 down")
