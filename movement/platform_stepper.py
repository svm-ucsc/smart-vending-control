#!/usr/bin/python3

import threading
import time
import board
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit

# Define macros for specific turns
QUARTER_TURN = 0.25
HALF_TURN = 0.5
FULL_TURN = 1.0

# Defines the number of steps per entire rotation using the DOUBLE_STEP mode
DOUBLE_STEP = 200

class PlatformStepper:
    def __init__(self, channel:int):
        self.kit = MotorKit(i2c=board.I2C())
        self.step_channel = None

        # Determine stepper we are using on the given HAT?
        if (channel < 0) or (channel > 1):
            print('Platform stepper channel  must be 0 or 1')
            exit(1)
        elif channel == 0:
            self.step_channel = self.kit.stepper1

            # Load position for stepper 1 from the file, check if it is 
        else:
            self.step_channel = self.kit.stepper2

            # Load position for stepper 2

    # Return the current motor channel for this stepper motor on the HAT
    def get_channel(self) -> int:
        return self.step_channel

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
                print(self.step_channel.onestep(direction=dir_mode, style=stepper.DOUBLE))
                time.sleep(step_sleep)

        except KeyboardInterrupt:
            exit(1)

def main():
	# Define two functions to test out the motors simultaneously
	def test_motor_A():
		my_stepperA = PlatformStepper(0)
		my_stepperA.rotate('cw', 1000, 3)
		my_stepperA.rotate('ccw', 100, 3)
		#my_stepperA.rotate('cw', 100, HALF_TURN)

	def test_motor_B():
		my_stepperB = PlatformStepper(1)
		my_stepperB.rotate('cw', 10000, 3)
		my_stepperB.rotate('ccw', 500, 3)
		my_stepperB.rotate('cw', 100, HALF_TURN)

	# Define two threds w/ each function listed above
	thread_A = threading.Thread(target=test_motor_A)
	#thread_B = threading.Thread(target=test_motor_B)

	# Launch the threads
	try:
		thread_A.start()
		#thread_B.start()
	except:
		print("Unable to start a new thread.")

if __name__ == '__main__':
	main()

