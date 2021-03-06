#!/usr/bin/evn python
# coding:utf-8

import sys
sys.path.append('..')
import time
import math
import threading
from smbus import SMBus
from lib.tools import Singleton
from lib.logger import logger


class Baro(threading.Thread):
    __metaclass__ = Singleton

    def __init__(self, ORB, bus=1, i2c=0x77, elevation=0):
        """Initialize the Driver.
        Default bus is 1.  If you have a Rev 1 RPi then you will need to use bus 0.
        A bus object can also be passed in if you are sharing it among other modules

        Arguments (All optional):
        bus -- 0, 1, or a bus object
        i2c -- I2C address
        elevation -- Elevation in meters"""
        super(Baro, self).__init__(name='Baro')
        self.ORB = ORB

        if(bus == 0 or bus == 1):
            self.bus = SMBus(bus)
        else:
            self.bus = bus
        self.i2c = i2c
        self.elevation = elevation

    def run(self):
        logger.info('Initializing Barometre')

        while True:
            self.read()
            hpa = self.getPressureAdj()
            dic = {'Baro_State': True, 'Pressure': hpa,
                   'Temperature': round(self.tempC, 2)}
            self.update(dic)
            time.sleep(.01)

    def update(self, dictories):
        for (k, v) in dictories.items():
            self.ORB.publish(k, v)

    def average_pressure(self):
        count = 0
        num = 3
        container = []
        while count < num:
            self.read()
            p = self.getPressureAdj()
            if p not in container:
                count += 1
                container.append(p)
        return reduce(lambda x, y: x + y, container) / num

    def setElevation(self, elevation):
        self.elevation = elevation

    def setElevationFt(self, elevation):
        self.elevation = elevation / 3.2808

    def setI2c(self, i2c):
        self.i2c = i2c

    def read(self):
        # Get raw pressure
        self.bus.write_byte(self.i2c, 0x48)
        time.sleep(0.05)

        D1 = self.bus.read_i2c_block_data(self.i2c, 0x00)
        D1 = D1[0] * 65536 + D1[1] * 256.0 + D1[2]
        time.sleep(0.05)

        # Get raw temperature
        self.bus.write_byte(self.i2c, 0x58)
        time.sleep(0.05)
        D2 = self.bus.read_i2c_block_data(self.i2c, 0x00)
        D2 = D2[0] * 65536 + D2[1] * 256.0 + D2[2]
        time.sleep(0.05)

        # Read Constants from Sensor
        if hasattr(self, 'C1'):
            C1 = self.C1
        else:
            C1 = self.bus.read_i2c_block_data(
                self.i2c, 0xA2)  # Pressure Sensitivity
            C1 = C1[0] * 256.0 + C1[1]
            self.C1 = C1
            time.sleep(0.05)

        if hasattr(self, 'C2'):
            C2 = self.C2
        else:
            C2 = self.bus.read_i2c_block_data(
                self.i2c, 0xA4)  # Pressure Offset
            C2 = C2[0] * 256.0 + C2[1]
            self.C2 = C2
            time.sleep(0.05)

        if hasattr(self, 'C3'):
            C3 = self.C3
        else:
            # Temperature coefficient of pressure sensitivity
            C3 = self.bus.read_i2c_block_data(self.i2c, 0xA6)
            C3 = C3[0] * 256.0 + C3[1]
            self.C3 = C3
            time.sleep(0.05)

        if hasattr(self, 'C4'):
            C4 = self.C4
        else:
            # Temperature coefficient of pressure offset
            C4 = self.bus.read_i2c_block_data(self.i2c, 0xA8)
            C4 = C4[0] * 256.0 + C4[1]
            self.C4 = C4
            time.sleep(0.05)

        if hasattr(self, 'C5'):
            C5 = self.C5
        else:
            C5 = self.bus.read_i2c_block_data(
                self.i2c, 0xAA)  # Reference temperature
            C5 = C5[0] * 256.0 + C5[1]
            self.C5 = C5
            time.sleep(0.05)

        if hasattr(self, 'C6'):
            C6 = self.C6
        else:
            # Temperature coefficient of the temperature
            C6 = self.bus.read_i2c_block_data(self.i2c, 0xAC)
            C6 = C6[0] * 256.0 + C6[1]
            self.C6 = C6
            time.sleep(0.05)

        # These are the calculations provided in the datasheet for the sensor.
        dT = D2 - C5 * 2**8
        TEMP = 2000 + dT * C6 / 2**23

        # Set Values to class to be used elsewhere
        self.tempC = TEMP / 100.0
        self.tempF = TEMP / 100.0 * 9.0 / 5 + 32
        self.tempK = TEMP / 100.0 + 273.15

        # These calculations are all used to produce the final pressure value
        OFF = C2 * 2**16 + (C4 * dT) / 2**7
        SENS = C1 * 2**15 + (C3 * dT) / 2**8
        P = (D1 * SENS / 2**21 - OFF) / 2**15
        self.pressure = P / 100.0

        # Calculate an offset for the pressure.  This is required so that the readings are correct.
        # Equation can be found here:
        # http://en.wikipedia.org/wiki/Barometric_formula
        altOffset = math.exp(
            (-9.80665 * 0.0289644 * self.elevation) / (8.31432 * self.tempK))
        self.pressureAdj = (P / altOffset) / 100.0

    def getTempC(self):
        return self.tempC

    def getTempF(self):
        return self.tempF

    def getPressure(self):
        return self.pressure

    def getPressureAdj(self):
        return self.pressureAdj

    def getBus(self):
        return self.bus

    def printResults(self):
        print "Temperature:", round(self.tempC, 2), "C"
        print "            ", round(self.tempF, 2), "F"

        print "Pressure Absolute:", round(self.pressure, 2), "hPa"
        print "         Adjusted:", round(self.pressureAdj, 2), "hPa"
        print "         Adjusted:", round(self.convert2In(self.pressureAdj), 2), "in"

    def convert2In(self, pressure):
        return pressure * 0.0295301


def Baro_start(ORB):
    baro = Baro(ORB)
    baro.start()
    while not ORB.state('Baro'):
        time.sleep(.1)
    logger.info('>>> Barometre is OK')

if __name__ == "__main__":
    from lib.tools import Watcher
    from AF_uORB.uORB import uORB
    from lib.science import pressure2Alt
    ORB = uORB()
    Watcher()

    Baro_start(ORB)

    init_pressure = ORB.subscribe('Pressure')
    ORB.publish('InitAltitude', pressure2Alt(init_pressure))
    while True:
        print ORB.get_altitude(True)
        # print ORB.subscribe('Pressure')
