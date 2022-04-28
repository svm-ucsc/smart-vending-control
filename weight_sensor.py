#!/usr/bin/python3
#
# For use with the HX711 24-bit ADC to be used for item weight detection
# 
# HX711 datasheet: https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf
# Adapted from https://github.com/j-dohnalek/hx711py/blob/master/hx711.py

import RPi.GPIO as GPIO
import time
from movement.lane_stepper import *

class WeightSensor_HX711:

    def __init__(self, dout, pd_sck, gain=128, MAX_CAP=500, MIN_CAP=-10):
        """
        Set GPIO Mode, and pin for communication with HX711
        :param dout: Serial Data Output pin
        :param pd_sck: Power Down and Serial Clock Input pin
        :param gain: set gain 128, 64, 32
        """
        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1
        self.MAX_CAP = MAX_CAP
        self.MIN_CAP = MIN_CAP
        self.scale_ready = False

        self.prev_read = 0         # Holds a previous read value for comparison

        # Setup the gpio pin numbering system
        GPIO.setmode(GPIO.BCM)

        # Set the pin numbers
        self.PD_SCK = pd_sck
        self.DOUT = dout

        # Setup the GPIO Pin as output
        GPIO.setup(self.PD_SCK, GPIO.OUT)

        # Setup the GPIO Pin as input
        GPIO.setup(self.DOUT, GPIO.IN)

        # Power up the chip
        #self.power_up()
        self.set_gain(gain)
        time.sleep(1)

    def is_ready(self):
        return GPIO.input(self.DOUT) == 0

    def set_gain(self, gain=128):

        try:
            if gain == 128:
                self.GAIN = 1
            elif gain == 64:
                self.GAIN = 3
            elif gain == 32:
                self.GAIN = 2
        except:
            self.GAIN = 1  # Sets default GAIN at 128

        GPIO.output(self.PD_SCK, False)
        self.read()

    def set_scale(self, scale):
        """
        Set scale
        :param scale, scale
        """
        self.SCALE = scale

    def set_offset(self, offset):
        """
        Set the offset
        :param offset: offset
        """
        self.OFFSET = offset
    
    def set_prev_read(self, weight):
        """
        Stores a specified weight for later reference
        :param weight: weight to store
        """
        self.prev_read = weight

    def get_scale(self):
        """
        Returns value of scale
        """
        return self.SCALE

    def get_offset(self):
        """
        Returns value of offset
        """
        return self.OFFSET

    def read_bit(self):
        GPIO.output(self.PD_SCK, True)
        GPIO.output(self.PD_SCK, False)
        return int(GPIO.input(self.DOUT))

    def read(self):
        """
        Read data from the HX711 chip
        :param void
        :return reading from the HX711
        """
        byte_vals = []
        while not self.is_ready():
            pass

        for i in range(3):
            count = 0
            for ii in range(8):
                count <<= 1
                #count >>=1
                count |= self.read_bit() #* 0x80
                #count |= int(GPIO.input(self.DOUT))*0x80
            byte_vals.append(count)

        for i in range(self.GAIN):
            GPIO.output(self.PD_SCK, True)
            GPIO.output(self.PD_SCK, False)

        value = ((byte_vals[0] << 16) | (byte_vals[1] << 8) | byte_vals[2])
        #value = ((byte_vals[2] << 16) | (byte_vals[1]) << 8 | (byte_vals[0]))
        value = -(value & 0x800000) + (value & 0x7fffff)
        return int(value)

    def is_ready(self):
        return GPIO.input(self.DOUT) == 0

    def warmup(self, minutes=3):
        print("time:{}".format(minutes*60))
        # wait until sensors are ready
        while (not self.is_ready()):
            pass
        start = time.time()
        print(start)
        elapsed = 0
        while (elapsed < (start + (minutes*60))):
            while (not self.is_ready()):
                pass
            value = self.read()
            print(value)
            elapsed = time.time()-start
            #print("elapsed time: {}".format(elapsed))

    def read_average(self, times=16):
        """
        Calculate average value from
        :param times: measure x amount of time to get average
        """
        sum = 0
        for i in range(times):
            sum += self.read()
        return sum / times
    
    def detect_change(self, tolerance) -> bool:
        """
        Detects whether a change in weight has occurred.
        If change detected, stores newly recorded weight as previous read
        :param tolerance: minimum squared difference for change to be registered
        """
        new_weight = self.get_grams()
        if (new_weight - self.prev_read) ** 2 > tolerance:
            self.set_prev_read(new_weight)
            return True
        else:
            return False
    
    def difference(self):
        """
        Returns difference between current weight and offset
        """
        current = self.get_grams()
        return current - self.get_offset()

    def get_grams(self, num_samples=16):
        """
        :param times: Set value to calculate average, 
        be aware that high number of times will have a 
        slower runtime speed.        
        :return float weight in grams
        """
        sum = 0
        for i in range(num_samples):
            val = (self.read()-self.OFFSET)/self.SCALE
            # Account for extreme outliers
            val = self.MIN_CAP if val < self.MIN_CAP else val
            val = self.MAX_CAP if val > self.MAX_CAP else val
            sum += val
        grams = sum/num_samples
        return grams

    def calc_offset(self, num_samples=16):
        readings = []
        time.sleep(2)
        for i in range(num_samples):
            readings.append(self.read_average())
            time.sleep(1)

        print("length before removal: {}".format(len(readings)))
        readings.remove(min(readings))
        print("length after remove min: {}".format(len(readings)))
        readings.remove(max(readings))
        print("length after remove mac: {}".format(len(readings)))
        offset = sum(readings)/(num_samples-2)
        return offset

    def calibrate(self):
        """
        Tare functionality for calibration
        :param times: set value to calculate average
        """
        print("Initializing.\n Please ensure that the platform is empty and on a stable surface.")
        while not self.is_ready():
            pass
        readyCheck = input("Remove any items from platform. Press any key when ready.")
        offset = self.read_average()
        print("Value at zero (offset): {}".format(offset))
        self.set_offset(offset)
        print("Please place an item of known weight on the scale.")
        item_weight = input("Please enter the item's weight in grams.\n>")
        measured_weight = (self.read_average()-self.get_offset())
        print("Measured weight: ".format(measured_weight))
        scale = (measured_weight)/float(item_weight)
        self.set_scale(scale)
        print("Scale adjusted for grams: {}".format(scale))


    def power_down(self):
        """
        Power the chip down
        """
        GPIO.output(self.PD_SCK, False)
        GPIO.output(self.PD_SCK, True)
        time.sleep(0.0001)

    def power_up(self):
        """
        Power the chip up
        """
        GPIO.output(self.PD_SCK, False)
        time.sleep(0.0001)