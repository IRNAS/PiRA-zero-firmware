#!/usr/bin/env python
# All credit to Antonvh:  https://gist.github.com/antonvh/c81c247fc03029a1ba6a
# View his work here:  https://github.com/antonvh
##
#
# See more about the BrickPi here:  http://www.dexterindustries.com/BrickPi
#
# These files have been made available online through a Creative Commons Attribution-ShareAlike 3.0  license.
# (http://creativecommons.org/licenses/by-sa/3.0/)

#For the code to work - sudo pip install -U future

from __future__ import print_function
from __future__ import division
import smbus, os
from time import sleep

i2c = smbus.SMBus(1)

BQ2429x_I2CADDR 					= 0x4d # default address


class MCP3021(object):
	def __init__(self):
		try:
			dummy = i2c.read_word_data(MCP3021_I2CADDR,0)
		except:
			print "Couldn't connect to MCP3021 | I2C init"									# couldn't connect report back


    def get_voltage():
        try:
                address = 0x4d
                # read data from i2c bus. the 0 command is mandatory for the protocol but not used in this chip.
                data = i2c.read_word_data(MCP3021_I2CADDR, 0)

                # from this data we need the last 4 bits and the first 6.
                last_4 = data & 0b1111 # using a bit mask
                first_6 = data >> 10 # left shift 10 because data is 16 bits

                # together they make the voltage conversion ratio
                # to make it all easier the last_4 bits are most significant :S
                vratio = (last_4 << 6) | first_6

                # Now we can calculate the battery voltage like so:
                ratio = 0.008063   # calibration value based on measurements
                voltage = vratio * ratio

                return "{:.3F}".format(voltage)

        except:
                print "Couldn't connect to MCP3021"
    			return 0
