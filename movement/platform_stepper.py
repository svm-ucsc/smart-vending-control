#!/usr/bin/python3

import time
import board
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit
from pathlib import Path

# Define base I2C address (see soldered jumpers)
I2C_ADDR = 0x61

# Define filenames/locations for the stored positions of the stepper motors
PLAT0_FILE = "channel0_pos.txt"
PLAT0_LOC = Path(PLAT0_FILE)
PLAT1_FILE = "channel1_pos.txt"
PLAT1_LOC = Path(PLAT1_FILE)

# Define macros for specific turns
QUARTER_TURN = 0.25
HALF_TURN = 0.5
FULL_TURN = 1.0

# Defines the number of steps per entire rotation using the DOUBLE_STEP mode
DOUBLE_STEP = 200

class PlatformStepper:
    # Perform setup and check whether the position we are loading from is correct or not relative
    # to the expected neutral position of the stepper motor
    def __init__(self, channel:int):
        self.kit = MotorKit(i2c=board.I2C(), address=I2C_ADDR)
        self.step_channel = None
        self.position = None
        self.pos_file = None
        self.pos_loc = None

        # Determine stepper we are using on the given HAT?
        if (channel < 0) or (channel > 1):
            print('Platform stepper channel must be 0 or 1')
            exit(1)
        
        self.step_channel = self.kit.stepper1 if channel == 0 else self.kit.stepper2
        self.pos_file = PLAT0_FILE if channel == 0 else PLAT1_FILE
        self.pos_loc = PLAT0_LOC if channel == 0 else PLAT1_LOC

        # Check if the file for storing postition exists and initialize if not so
        if not self.pos_loc.is_file():
            self.pos_loc.touch(exist_ok=True)
              
            # Set stored position to 0
            with open(self.pos_file, "w") as f:
                f.write("0")

        # Load position for stepper 0 from the file
        with open(self.pos_file, "r") as f:
            self.position = int(f.read())

    # Return the current motor channel for this stepper motor on the HAT
    def get_channel(self) -> int:
        return self.step_channel

    # Return the current position of the stepper motor relative to the neutral position
    def get_position(self) -> int:
        return self.position

    # Rotate the motor either cw or ccw at a given speed for a specific amount of rotations
    #
    # Parameters:
    # -direction: 'cw' for clockwise or 'ccw' for counterclockwise movement
    # -speed: used to determine the stride of each step--bounded between [0, 10000]
    # -rotations: number of rotations to undertake
    def rotate(self, direction:str, speed:int, rotations:float):
        step_sleep = 1 / speed
        step_count = (int) (rotations * DOUBLE_STEP)
        dir_mode = None

        if direction == 'cw':
            dir_mode = stepper.FORWARD
        elif direction == 'ccw':
            dir_mode = stepper.BACKWARD
        else:
            print("Unexpected direction--should be \'cw\' or \'ccw\'")
            exit(1)

        try:
            for i in range(step_count):
                self.step_channel.onestep(direction=dir_mode, style=stepper.DOUBLE)
                self.position = self.position + (1 if direction == 'cw' else -1)
                time.sleep(step_sleep)
            
            with open(self.pos_file, "w") as f:
                f.write(str(self.position))

        except (KeyboardInterrupt, SystemExit):
            with open(self.pos_file, "w") as f:
                f.write(str(self.position))

            exit(1)

    # Move the motor in a smooth motion such that platform may go from fast to slow as it
    # approaches its destination
    #
    # Parameters:
    # -direction: 'cw' for clockwise or 'ccw' for counterclockwise movement
    # -init_speed: determines the initial speed at which the motor begins moving
    # -rotations: number of rotations to undertake
    def rotate_ease(self, direction:str, init_speed:int, rotations:float):
        step_sleep = 1 / init_speed
        step_count = (int) (rotations * DOUBLE_STEP)
        dir_mode = None

        if direction == 'cw':
            dir_mode = stepper.FORWARD
        elif direction == 'ccw':
            dir_mode = stepper.BACKWARD
        else:
            print("Unexpected direction--should be \'cw\' or \'ccw\'")
            exit(1)

        try:
            for i in range(step_count):
                self.step_channel.onestep(direction=dir_mode, style=stepper.DOUBLE)
                self.position = self.position + (1 if direction == 'cw' else -1)
                time.sleep(step_sleep)
            
            with open(self.pos_file, "w") as f:
                f.write(str(self.position))

        except (KeyboardInterrupt, SystemExit):
            with open(self.pos_file, "w") as f:
                f.write(str(self.position))

            exit(1)

    # Resets the position of the stepper motor back to the currently-defined zero position
    def reset_position(self):
        if self.position > 0:
            while self.position > 0:
                self.step_channel.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
                self.position = self.position - 1
                time.sleep(0.01)
        elif self.position < 0:
            while self.position < 0:
                self.step_channel.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
                self.position = self.position + 1
                time.sleep(0.01)

        with open(self.pos_file, "w") as f:
            print(self.position)
            f.write(str(self.position))

    # Sets the CURRENT position of the stepper motor as the new zero position--if you want to move
    # the motor's position back to the original position, call reset_position() instead!
    def zero_position(self):
        self.position = 0

        with open(self.pos_file, "w") as f:
            f.write(str(self.position))

def main():
	# Standard test to ensure that movement and reset is tracked appropriately
    # across different actions
    def test_motor_A():
        my_stepperA = PlatformStepper(0)

        # Reset once, return position
        my_stepperA.reset_position()
        print("Position after first reset:", my_stepperA.get_position())
        
        my_stepperA.rotate('cw', 1000, 5)
        my_stepperA.rotate('ccw', 400, 2)
        print("Position after 3 rotations:", my_stepperA.get_position())
       
        time.sleep(4)

        my_stepperA.reset_position()
        print("Position after 2nd reset:", my_stepperA.get_position())
        
        my_stepperA.rotate('cw', 100, 1.5)
        
        # Define new zero position
        my_stepperA.zero_position()

        time.sleep(4)

        my_stepperA.rotate('ccw', 400, 2.5)
        my_stepperA.reset_position()
        print("Position after 3rd reset:", my_stepperA.get_position())
    
    # Test for checking whether the platform stepper can ease to a stop rather than simply
    # stop immediately
    def test_motor_A_ease():
        my_stepper = PlatformStepper(0)
        my_stepper.reset_position()
        my_stepper.rotate_ease('cw', 10000, 3)

    # Launch the threads
    try:
        #test_motor_A()
        test_motor_A_ease()
    except:
        print("Unable to start a new thread.")

if __name__ == '__main__':
    main()

