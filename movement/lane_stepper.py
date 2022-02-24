#!/usr/bin/python3

# For use with the 28BYJ-48 5V stepper motors to be used in the item lane components of the machine
#
# Specs:
# Rated voltage: 5V
# Tested current: 0.3A
# Speed Var. Ratio: 1/64
# Stride Angle: 5.625 deg. -> NOTE: 360 deg = 4096 * (5.625 / 64)

import RPi.GPIO as GPIO
import time

# Define the sequence for the full step (more granular) rotation
FULL_STEP = [[1,0,0,1],
             [1,0,0,0],
             [1,1,0,0],
             [0,1,0,0],
             [0,1,1,0],
             [0,0,1,0],
             [0,0,1,1],
             [0,0,0,1]]

# Define the sequence for the half step (less granular) rotation
HALF_STEP = [[1,0,0,0],
             [1,1,0,0],
             [0,1,1,0],
             [0,0,1,1]]

class ItemLaneStepper:
    def __init__(self, pinA:int, pinB:int, pinC:int, pinD:int, step_mode:list):
        # Helper function to set up the default position/values for the stepper motor
        def pin_setup(pins:list):
            GPIO.setmode(GPIO.BCM)
            for pin in pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)

        self.motor_pins = [pinA, pinB, pinC, pinD]              # Defined in terms of GPIO pin #s
        self.step_mode = step_mode				# FULL_STEP or HALF_STEP
        pin_setup(self.motor_pins)				# Set up GPIO modes for pins
  
    # Return the current step mode of this ItemLaneStepper 
    def get_step_mode(self) -> str:
        return self.step_mode

    # Return the pin configuration for this ItemLaneStepper
    def get_pin_config(self) -> list:
        return self.motor_pins
 
    # Rotate the motor either cw or ccw at a given speed for a specific amount of degrees
    #
    # Parameters:
    # -direction: 'cw' for clockwise or 'ccw' for counterclockwise movement
    # -speed: used to determine how quickly each step takes--bounded between [0, 1500]
    # -rotations: number of rotations to undertake
    def rotate(self, direction:str, speed:int, rotations:float):
        step_sleep = 1 / speed;
        step_count = (int) (rotations * 4096)			# see stride angle note above

        motor_step_counter = 0

        try:
            for i in range(step_count):
                # Set each of the pins, and for each pin, find the */*/*/* layout for the
                # pins that should be on or off for a given step
                for pin in range(0, len(self.motor_pins)):
                    GPIO.output(self.motor_pins[pin], self.step_mode[motor_step_counter][pin])

                if direction == 'cw':
                    motor_step_counter = (motor_step_counter - 1) % len(self.step_mode)
                elif direction == 'ccw':
                    motor_step_counter = (motor_step_counter + 1) % len(self.step_mode)
                else:
                    print("Unexpected direction--should be \'cw\' or \'ccw\'")
                    self.reset()
                    exit(1)

                time.sleep(step_sleep)

        except KeyboardInterrupt:
            self.reset()
            exit(1)

    # Restores all GPIO pins associated with this stepper motor back to low state to turn off the
    # motor--use this whenever you want the 
    def reset(self):
        for pin in self.motor_pins:
            GPIO.output(pin, GPIO.LOW)
        GPIO.cleanup()

# A test script to play with the functionality of the stepper motors for the item lanes
def main():
   my_stepper = ItemLaneStepper(17, 18, 27, 22, FULL_STEP)

   my_stepper.rotate('cw', 1500, 0.5)
   my_stepper.rotate('ccw', 1500, 1)
   my_stepper.rotate('cw', 1500, 1)

   my_stepper.reset()

if __name__ == '__main__':
    main()
