
'''
 * Name: bq2429x
 * Author: Silard Gal
 * Version: 1.0
 * Description: A library for interfacing the MAXIM MAX17201/MAX17205
 * 				Li+ fuel gauges.
 * Source: https://github.com/IRNAS/bq2429x
 * License: Copyright (c) 2017 Nick Lamprianidis 
 *          This library is licensed under the GPL license
 *          http://www.opensource.org/licenses/mit-license.php
 * Inspiration: The library is inspired by: https://github.com/IRNAS/bq2429x
 * Filename: bq2429x.py
 * File description: Definitions and methods for the bq2429x library
''' 

import logging
import time
import Adafruit_GPIO.I2C as I2C
i2c = I2C

BQ2429x_I2CADDR 					= 0x0b # default address
BQ2429x_INPUT_CTRL_ADDR 			= 0x00 # Input Source Control Register REG00 [reset = 00110xxx, or 3x]
BQ2429x_POWERON_CTRL_ADDR 			= 0x01 # Power-On Configuration Register REG01 [reset = 00011011, or 0x1B]
BQ2429x_CHARGE_CUR_CTRL_ADDR 		= 0x02 # Charge Current Control Register REG02 [reset = 01100000, or 60]
BQ2429x_PRECHARGE_CTRL_ADDR 		= 0x03 # Pre-Charge/Termination Current Control Register REG03 [reset = 00010001, or 0x11]
BQ2429x_CHARGE_VOL_CTRL_ADDR 		= 0x04 # Charge Voltage Control Register REG04 [reset = 10110010, or 0xB2]
BQ2429x_CHARGE_TERM_CTRL_ADDR 		= 0x05 # Charge Termination/Timer Control Register REG05 [reset = 10011010, or 0x9A]
BQ2429x_BOOST_THERMAL_CTRL_ADDR 	= 0x06 # Boost Voltage/Thermal Regulation Control Register REG06 [reset = 01110011, or 0x73]
BQ2429x_MISC_CTRL_ADDR 				= 0x07 # Misc Operation Control Register REG07 [reset = 01001011, or 4B]
BQ2429x_STATUS_ADDR 				= 0x08 # System Status Register REG08
BQ2429x_FAULT_ADDR 					= 0x09 # New Fault Register REG09
BQ2429x_VENDOR_ADDR 				= 0x0A #/ Vender / Part / Revision Status Register REG0A

# indentifications for the register values
VBUS_STAT							= 5
CHRG_STAT = WATCHDOG_FAULT			= 4
DPM_STAT = BOOST_FAULT				= 3
PG_STAT = CHRG_FAULT				= 2
THERM_STAT = BAT_FAULT				= 1
VSYS_STAT = NTC_FAULT				= 0

# status register values
vsys_data 	= { '0' : "BAT > VSYSMIN", '1' : "BAT < VSYSMIN" }
therm_data 	= { '0' : "Normal status" ,  '1' : "In thermal regulation" }
pg_data 	= { '0' : "Not good power", '1' : "Power good" }
dpm_data 	= { '0' : "Not DPM", '1' : "VINDPM or IINDPM" }
chrg_data 	= { "00" : "Not charging", "01" : "Pre-charger", "10" : "Fast charging", "11" : "Charge termination done" }
vbus_data 	= { "00" : "No input", "01" : "USB host", "10" : "Adapter port", "11" : "OTG" }

# fault register values
ntc_data		= {
	"000" : "Normal",
	"001" : "TS1 Cold",
	"010" : "TS1 Hot",
	"011" : "TS2 Cold",
	"100" : "TS2 Hot",
	"101" : "Both Cold",
	"110" : "Both Hot",
	"111" : "Not defined..."
}
bat_data		= { '0' : "Normal", '1' : "BatOVP" }
chrg_fault_data = { "00" : "Normal", "01" : "Input fault (VBUS OVP or VBAT<VBUS<3.8V)","10" : "Thermal shutdown","11" : "Charge Safety Timer Expiration" }
boost_data 		= { '0' : "Normal", '1' : "VBUS overloaded or VBUS OVP in boost mode" }
watchdog_data	= { '0' : "Normal", '1' : "Watchdog timer expiration" }

CVL_DEFAULT			= 100110
PRECH_0 = THRESH_0 	= 0
PRECH_1	= THRESH_1 	= 1

PRECH_CURRENT_DEFAULT = TERM_CURRENT_DEFAULT = 0001

class BQ2429x(object):
	def __init__(self):
		try:
			self._device = i2c.get_i2c_device(BQ2429x_I2CADDR)								# connect to the device
		except:
			print "Couldn't connect to BQ2429x | I2C init"									# couldn't connect report back 

	# def get_status(self, type_of_status) - gets the type of status you request
	def get_status(self, type_of_status):
		try:
			value = self._device.readU8(BQ2429x_STATUS_ADDR)								# get the value in 0-255

			# convert to byte array and remove the 0b part
			binary_value = bin(value)[2:]
			
			binary_value = self.check8bit(binary_value)

			# it is choosing on the type_of_status and returning the dictionary value
			if type_of_status == VSYS_STAT:
				return vsys_data[binary_value[0]]

			elif type_of_status == THERM_STAT:
				return therm_data[binary_value[1]]

			elif type_of_status == PG_STAT:
				return pg_data[binary_value[2]]

			elif type_of_status == DPM_STAT:
				return dpm_data[binary_value[3]]

			elif type_of_status == CHRG_STAT:
				# combining the two to make life easier
				_stat = str(binary_value[4]) + str(binary_value[5])
				return chrg_data[_stat]

			elif type_of_status == VBUS_STAT:
				# combining the two to make life easier
				_stat = str(binary_value[6]) + str(binary_value[7])
				return vbus_data[_stat]


		except:
			print "Couldn't connect to BQ2429x"
			return 0

	# def get_faults(self, type_of_fault) - gets the type of fault you request
	def get_faults(self, type_of_fault):
		try:

			value = self._device.readU8(BQ2429x_FAULT_ADDR)									# get the 0-255 value							
			
			binary_value = bin(value)[2:]													# convert to byte array and remove the 0b
			
			binary_value = self.check8bit(binary_value)

			# choose on the type_of_fault and return the data from the dictionary
			if type_of_fault == NTC_FAULT:
				_stat = str(binary_value[0]) + str(binary_value[1]) + str(binary_value[2])
				return ntc_data[_stat]

			elif type_of_fault == BAT_FAULT:
				return bat_data[binary_value[3]]

			elif type_of_fault == CHRG_FAULT:
				_stat = str(binary_value[4]) + str(binary_value[5])
 				return chrg_fault_data[_stat]

			elif type_of_fault == BOOST_FAULT:
				return boost_data[binary_value[6]]

			elif type_of_fault == WATCHDOG_FAULT:
				return watchdog_data[binary_value[7]]

		except:
			print "Couldn't connect to BQ2429x"
			return 0


	#def set_ter_prech_current(self,termination,precharge) - set the termination and precharge current limit
	def set_ter_prech_current(self, termination, precharge):

		# termination 		- Termination current limit,
		#					- TERM_CURRENT_DEFAULT (0001)
		# precharge 		- precharge current limit,
		#					- PRECH_CURRENT_DEFAULT (0001)

		try:
			writing_value = int(str(termination) + str(precharge))									# combine the value and convert to int
			self._device.write8(BQ2429x_PRECHARGE_CTRL_ADDR, writing_value)							# write to register
			current_value = self._device.readU8(BQ2429x_PRECHARGE_CTRL_ADDR)						# read the register
	
			current_value = self.check8bit(current_value)

			if int(hex(current_value)[2:]) == writing_value:										# comapre them 
				return str(writing_value) + " - Success"											# success!
			else:
				return str(writing_value) + " - ERROR!"												# not the same!
			
		except:
			print "Couldn't connect to BQ2429x"
			return 0


	# def set_charge_voltage(self, c_v_l, precharge, thresh) - sets the values for register 4
	def set_charge_voltage(self, c_v_l, precharge, thresh):

		# c_v_l 		- charge voltage limit, 
		#				- set to CVL_DEFAULT (4.112V) (default)
		# precharge 	- battery precharge to fast charge threshold
		#				- set to PRECH_0	(2.8V)
		#				- set to PRECH_1	(3.0V) (default)
		# thresh 		- battery recharge threshold (below battery regulation voltage)
		#				- set to THRESH_0 	(100mV) (default)
		#				- set to THRESH_1	(300mV)

		try:
			writing_value = int(str(thresh) + str(precharge) + str(c_v_l))							# combine the values and convert to int
			self._device.write8(BQ2429x_CHARGE_VOL_CTRL_ADDR, writing_value)						# write to register
			current_value = self._device.readU8(BQ2429x_CHARGE_VOL_CTRL_ADDR)						# read the register

			current_value = self.check8bit(current_value)

			if int(bin(current_value)[2:]) == writing_value:										# compare them
				return str(writing_value) + " - Success"											# success
			else:
				return str(writing_value) + " - ERROR!"												# error not the same!

		except:																				
			print "Couldn't connect to BQ2429x"
			return 0

	# def check8bit(self, _input) - checks if every bit is there if not fill it with 0
	def check8bit(self, _input):
		value_length = len(_input)
		if(value_length != 8):														
			new_binary_value = ""
			for i in range(0, 8-value_length):											
				new_binary_value += "0"

			new_binary_value += str(_input)																			
			return new_binary_value
		else:
			return _input