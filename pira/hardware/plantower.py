import time
import pigpio
import serial
import numpy as np

class PLANTOWER(object):
    """PLANTOWER driver."""

    def __init__(self, portId):

        self.ser = None
        self.portId = portId

        try:

            self.ser = serial.Serial(self.portId, baudrate=9600, stopbits=1, parity="N",  timeout=2)

        except (Exception):
            raise plantowerException


    def read(self, timeout=10):
        """Read distance from ultrasonic sensor.

        :param timeout: Amount of seconds to read data for
        :return: Average distance
        """
        start = time.time()
        pm1_std = []
        pm25_std = []
        pm10_std = []

        pm1_atm = []
        pm25_atm = []
        pm10_atm = []

        part_03 = []
        part_05 = []
        part_1 = []
        part_25 = []
        part_5 = []
        part_10 = []

        # configure sensor in passive mode
        self.ser.write([66, 77, 225, 0, 0, 1, 112])
        while time.time() - start < timeout:
            try:
                self.ser.flushInput()
                self.ser.write([66, 77, 226, 0, 0, 1, 113])   # ask for data
                s3 = self.ser.read(32)
                s2=':'.join(x.encode('hex') for x in s3)
                s1 = s2.split(":")
                s = []
                for index, item in enumerate(s1):
                    s.append(int(item,16))

                if s[0] == 0x42 and s[1] == 0x4d:
                    #print("Header is correct")
                    cs = (s[30] * 256 + s[31])   # check sum
                    # Calculate check sum value
                    check = 0
                    for i in range(30):
                        check += int(s[i])
                    # Check if check sum is correct
                    if check == cs:
                        # PM1, PM2.5 and PM10 values for standard particle in ug/m^3
                        pm1_hb_std = s[4]
                        pm1_lb_std = s[5]
                        pm1_std.append(float(pm1_hb_std * 256 + pm1_lb_std))
                        pm25_hb_std = s[6]
                        pm25_lb_std = s[7]
                        pm25_std.append(float(pm25_hb_std * 256 + pm25_lb_std))
                        pm10_hb_std = s[8]
                        pm10_lb_std = s[9]
                        pm10_std.append(float(pm10_hb_std * 256 + pm10_lb_std))

                        # PM1, PM2.5 and PM10 values for atmospheric conditions in ug/m^3
                        pm1_hb_atm = s[10]
                        pm1_lb_atm = s[11]
                        pm1_atm.append(float(pm1_hb_atm * 256 + pm1_lb_atm))
                        pm25_hb_atm = s[12]
                        pm25_lb_atm = s[13]
                        pm25_atm.append(float(pm25_hb_atm * 256 + pm25_lb_atm))
                        pm10_hb_atm = s[14]
                        pm10_lb_atm = s[15]
                        pm10_atm.append(float(pm10_hb_atm * 256 + pm10_lb_atm))

                        # Number of particles bigger than 0.3 um, 0.5 um, etc. in #/cm^3
                        part_03_hb = s[16]
                        part_03_lb = s[17]
                        part_03.append(int(part_03_hb * 256 + part_03_lb))
                        part_05_hb = s[18]
                        part_05_lb = s[19]
                        part_05.append((part_05_hb * 256 + part_05_lb))
                        part_1_hb = s[20]
                        part_1_lb = s[21]
                        part_1.append(int(part_1_hb * 256 + part_1_lb))
                        part_25_hb = s[22]
                        part_25_lb = s[23]
                        part_25.append(int(part_25_hb * 256 + part_25_lb))
                        part_5_hb = s[24]
                        part_5_lb = s[25]
                        part_5.append(int(part_5_hb * 256 + part_5_lb))
                        part_10_hb = s[26]
                        part_10_lb = s[27]
                        part_10.append(int(part_10_hb * 256 + part_10_lb))
            except ValueError:
                continue

        if not pm1_atm:
            return None

        #print("Standard particle:")
        #print("PM1:", np.mean(pm1_std), "ug/m^3  PM2.5:", np.mean(pm25_std), "ug/m^3  PM10:", np.mean(pm10_std), "ug/m^3")
        #print("Atmospheric conditions:")
        #print("PM1:", np.mean(pm1_atm), "ug/m^3  PM2.5:", np.mean(pm25_atm), "ug/m^3  PM10:", np.mean(pm10_atm), "ug/m^3")
        #print("Number of particles:")
        #print(">0.3:", np.mean(part_03), " >0.5:", np.mean(part_05), " >1.0:", np.mean(part_1), " >2.5:", np.mean(part_25), " >5:", np.mean(part_5), " >10:", np.mean(part_10))
        #sleep(1)

        return np.mean(pm1_atm),np.mean(pm25_atm),np.mean(pm10_atm)

    def close(self):
        """Close device."""
        pass
