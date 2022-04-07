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

    def __init__(self, dout, pd_sck, gain=128):
        """
        Set GPIO Mode, and pin for communication with HX711
        :param dout: Serial Data Output pin
        :param pd_sck: Power Down and Serial Clock Input pin
        :param gain: set gain 128, 64, 32
        """
        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1

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
        self.power_up()
        self.set_gain(gain)

    def set_gain(self, gain=128):

        try:
            if gain == 128:
                self.GAIN = 3
            elif gain == 64:
                self.GAIN = 2
            elif gain == 32:
                self.GAIN = 1
        except:
            self.GAIN = 3  # Sets default GAIN at 128

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

    def read(self):
        """
        Read data from the HX711 chip
        :param void
        :return reading from the HX711
        """

        # Original C source code ported to Python as described in datasheet
        # https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf
        # Output from python matched the output of
        # different HX711 Arduino library example
        # Lastly, behaviour matches while applying pressure
        # Please see page 8 of the PDF document

        count = 0

        for i in range(24):
            GPIO.output(self.PD_SCK, True)
            count = count << 1
            GPIO.output(self.PD_SCK, False)
            if(GPIO.input(self.DOUT)):
                count += 1

        GPIO.output(self.PD_SCK, True)
        count = count ^ 0x800000
        GPIO.output(self.PD_SCK, False)

        # set channel and gain factor for next reading
        for i in range(self.GAIN):
            GPIO.output(self.PD_SCK, True)
            GPIO.output(self.PD_SCK, False)

        return count

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

    def get_grams(self, times=16):
        """
        :param times: Set value to calculate average, 
        be aware that high number of times will have a 
        slower runtime speed.        
        :return float weight in grams
        """
        value = (self.read_average(times) - self.OFFSET)
        grams = (value / self.SCALE)
        return grams

    def calibrate(self):
        """
        Tare functionality for calibration
        :param times: set value to calculate average
        """
        print("Initializing.\n Please ensure that the platform is empty.")
        scale_ready = False
        while not scale_ready:
            if (GPIO.input(self.DOUT) == 0):
                scale_ready = False
            if (GPIO.input(self.DOUT) == 1):
                print("Initialization complete!")
                scale_ready = True
        readyCheck = input("Remove any items from platform. Press any key when ready.")
        offset = self.read_average()
        print("Value at zero (offset): {}".format(offset))
        self.set_offset(offset)
        print("Please place an item of known weight on the scale.")
        item_weight = input("Please enter the item's weight in grams.\n>")
        measured_weight = (self.read_average()-self.get_offset())
        scale = int(measured_weight)/int(item_weight)
        self.set_scale(scale)
        print("Scale adjusted for grams: {}".format(scale))


    def power_down(self):
        """
        Power the chip down
        """
        GPIO.output(self.PD_SCK, False)
        GPIO.output(self.PD_SCK, True)

    def power_up(self):
        """
        Power the chip up
        """
        GPIO.output(self.PD_SCK, False)
