import time

import BQ2429x
import smbus as smbus

def main():
	debug_main()
	#debug_it_all()
	time.sleep(6)

def debug_main():

	print "==============================================="
	print "BQ2429x  : status - VSYS ---- : " + str(sensor_bq.get_status(BQ2429x.VSYS_STAT))
	print "BQ2429x  : status - THERM_STAT: " + str(sensor_bq.get_status(BQ2429x.THERM_STAT))
	print "BQ2429x  : status - CHRG_STAT : " + str(sensor_bq.get_status(BQ2429x.CHRG_STAT))
	print "BQ2429x  : fault - BAT_FAULT  : " + str(sensor_bq.get_faults(BQ2429x.BAT_FAULT))
	print "BQ2429x  : fault - CHRG_FAULT : " + str(sensor_bq.get_faults(BQ2429x.CHRG_FAULT))

def debug_it_all():

	print "==============================================="
	print "BQ2429x  : status - VSYS ------- : " + str(sensor_bq.get_status(BQ2429x.VSYS_STAT))
	print "BQ2429x  : status - THERM_STAT - : " + str(sensor_bq.get_status(BQ2429x.THERM_STAT))
	print "BQ2429x  : status - PG_STAT ---- : " + str(sensor_bq.get_status(BQ2429x.PG_STAT))
	print "BQ2429x  : status - DPM_STAT --- : " + str(sensor_bq.get_status(BQ2429x.DPM_STAT))
	print "BQ2429x  : status - CHRG_STAT -- : " + str(sensor_bq.get_status(BQ2429x.CHRG_STAT))
	print "BQ2429x  : status - VBUS_STAT -- : " + str(sensor_bq.get_status(BQ2429x.VBUS_STAT))
	print "BQ2429x  : fault - NTC_FAULT --- : " + str(sensor_bq.get_faults(BQ2429x.NTC_FAULT))
	print "BQ2429x  : fault - BAT_FAULT --- : " + str(sensor_bq.get_faults(BQ2429x.BAT_FAULT))
	print "BQ2429x  : fault - CHRG_FAULT -- : " + str(sensor_bq.get_faults(BQ2429x.CHRG_FAULT))
	print "BQ2429x  : fault - BOOST_FAULT - : " + str(sensor_bq.get_faults(BQ2429x.BOOST_FAULT))
	print "BQ2429x  : fault - WATCHDOG_FAULT: " + str(sensor_bq.get_faults(BQ2429x.WATCHDOG_FAULT))

if __name__ == '__main__':

	# referencing the sensors
	sensor_bq	= BQ2429x.BQ2429x()

	while 1:
		main()
