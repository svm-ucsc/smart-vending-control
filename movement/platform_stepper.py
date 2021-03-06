#!/usr/bin/python3

import time
import math
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

# Defines maximum speed for gliding motion
MAX_GLIDE_SPEED = 70

# Define constants for the gliding equation for motion
SLP_MAX = 15.5
MIDPT = 0.5
POWER = 4
SLP_MIN = 0.02325

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
    # -glide: forces the rotations to accelerate and decelerate gently--note that enabling
    #         this option uses a different speed scale that is bounded by [0, 70]
    def rotate(self, direction:str, speed:int, rotations:float, glide:bool=False):
        if (glide) and (speed > MAX_GLIDE_SPEED):
            print("Glide caps the speed limit to ", MAX_GLIDE_SPEED)
            exit(1)

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
                
                # Perform motion smoothing if the glide flag is enabled
                if glide:
                    ii = i / step_count
                    step_sleep = (1 / speed) * (SLP_MAX * math.pow(ii - MIDPT, POWER) + SLP_MIN)

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

        time.sleep(4)

        print("Glide motion test underway...")
        my_stepperA.rotate('ccw', 70, 4, True)
        my_stepperA.reset_position()
        print("Position after 4th reset:", my_stepperA.get_position())

    # In-machine test that calibrates the home position of the machine and
    # then uses both modes of the machine to check whether the lanes can be
    # reached.
    #
    # NOTE: CCW is used to move the platform up/CW is used for moving down
    def machine_motor_test():
        s = PlatformStepper(0)

        start_rot = 6.0                         # Number of rotations to go to home on cold boot
        lane_rot = 5.8                          # Number of rotations between item lanes
        
        eas_spd = 35                            # Best speed for eased motion
        lin_spd = 500                           # Best speed for linear motion

        # Startup test (assumed to be run when the machine is cold booted)
        # s.rotate('ccw', 500, start_rot)
        # s.zero_position()
        
        # Reset position
        print("Resetting position to home row...")
        s.reset_position()
        print("Reset complete.")
        time.sleep(1)

        # Ease motion test
        print("Beginning ease motion test...")
        s.rotate('cw', eas_spd, lane_rot, True)
        time.sleep(2)
        s.rotate('ccw', eas_spd, 3 * lane_rot, True)
        time.sleep(2)
        s.rotate('cw', eas_spd, lane_rot, True)
        time.sleep(2)
        
        s.reset_position()
        print("Ease motion test complete.")
        time.sleep(4)

        # Standard motion test
        print("Beginning linear motion test...")
        s.rotate('cw', lin_spd, lane_rot)
        time.sleep(2)
        s.rotate('ccw', lin_spd, 3 * lane_rot)
        time.sleep(2)
        s.rotate('cw', lin_spd, lane_rot)
        time.sleep(2)
        
        s.reset_position()
        print("Linear motion test complete.")


    # Launch the test sequence
    try:
        machine_motor_test()
    except:
        print("Test canceled.")

if __name__ == '__main__':
    main()

