#!/usr/bin/python3

# For use with the 28BYJ-48 5V stepper motors to be used in the item lane components of the machine
#
# Specs:
# Rated voltage: 5V
# Tested current: 0.3A
# Speed Var. Ratio: 1/64
# Stride Angle: 5.625 deg. -> NOTE: 360 deg = 4096 * (5.625 / 64)

import board
import busio
import digitalio
import threading
import time
from adafruit_mcp230xx.mcp23017 import MCP23017

MCP_TOTAL = 3											# How many MCP23017 boards are connected
PINS_PER_MCP = 16										# Number of GPIOs per MCP

# Define the sequence for the full step (more granular) rotation
FULL_STEP = [[True ,False,False,True ],
             [True ,False,False,False],
             [True ,True ,False,False],
             [False,True ,False,False],
             [False,True ,True ,False],
             [False,False,True ,False],
             [False,False,True ,True ],
             [False,False,False,True ]]


# Define the sequence for the half step (less granular) rotation
HALF_STEP = [[True ,False,False,False],
             [True ,True ,False,False],
             [False,True ,True ,False],
             [False,False,True ,True ]]
             
class ItemLaneStepper:
    def __init__(self, pinA, pinB, pinC, pinD, step_mode:list):
        self.motor_pins = [pinA, pinB, pinC, pinD]              # Defined in terms of GPIO pin #s
        self.step_mode = step_mode								# FULL_STEP or HALF_STEP
  
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
    # -speed: used to determine how quickly each step takes--bounded between [0, ???]
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
                    self.motor_pins[pin].value = self.step_mode[motor_step_counter][pin]

                if direction == 'cw':
                    motor_step_counter = (motor_step_counter - 1) % len(self.step_mode)
                elif direction == 'ccw':
                    motor_step_counter = (motor_step_counter + 1) % len(self.step_mode)
                else:
                    print("Unexpected direction--should be \'cw\' or \'ccw\'")
                    exit(1)
				
                #print(self.motor_pins)
                time.sleep(step_sleep)

        except KeyboardInterrupt:
            for pin in range(0, len(self.motor_pins)):
                self.motor_pins[pin].value = False
            exit(1)

    def reset(self):
        for pin in range(0, len(self.motor_pins)):
            self.motor_pins[pin].value=False

# A test script to play with the functionality of the stepper motors for the item lanes
def main():
	# Will need to initialize pins first before going in and using them per stepper (perhaps
	# include this as a part of the bigger Vending Machine object?)
	#
	# Returns 2D list that contains all the pins mapped to each MCP board
	def i2c_setup():
		i2c = busio.I2C(board.SCL, board.SDA)
	
		mcp = []											# Address MCPs directly
		pins = [[None] * PINS_PER_MCP] * MCP_TOTAL			# Return a list with [mcp][pin] indexing

		# Set up all of the pins as output pins
		for i in range(0, MCP_TOTAL):
			# For each MCP, we have a list of pins we can address such that the first board at 0x20
			# has a set of 16 pins numbered 0-15, 0x21 has the same, and so on
			mcp.append(MCP23017(i2c, address=(0x20 + i)))
			pins.insert(i, [])

			for j in range(0, PINS_PER_MCP):
				# Note that there are only 16 GPIOs per MCP23017
				pins[i].insert(j, mcp[i].get_pin(j))
		
				# Switch the pins to output mode (default value assumed False)
				pins[i][j].switch_to_output(value=False)
				#pins[i][j].pull = digitalio.Pull.UP

		return pins

	def move():
		p = i2c_setup()
		my_stepper = ItemLaneStepper(p[0][0], p[0][1], p[0][2], p[0][3], FULL_STEP)
		my_stepper.rotate('cw', 1000000, 0.5)
		my_stepper.rotate('ccw', 1000000, 1)
		my_stepper.rotate('cw', 1000000, 1)
		my_stepper.reset()


	def move1():
		p = i2c_setup()
		my_stepper = ItemLaneStepper(p[1][0], p[1][1], p[1][2], p[1][3], FULL_STEP)
		my_stepper.rotate('cw', 1000000, 0.5)
		my_stepper.rotate('ccw', 1000000, 1)
		my_stepper.rotate('cw', 1000000, 1)
		my_stepper.reset()

	def move2():
		p = i2c_setup()
		my_stepper = ItemLaneStepper(p[2][0], p[2][1], p[2][2], p[2][3], FULL_STEP)
		my_stepper.rotate('cw', 1000000, 0.5)
		my_stepper.rotate('ccw', 1000000, 1)
		my_stepper.rotate('cw', 1000000, 1)
		my_stepper.reset()


	#p = i2c_setup()

	#my_stepper_A = ItemLaneStepper(p[0][0], p[0][1], p[0][2], p[0][3], FULL_STEP)
	#my_stepper_B = ItemLaneStepper(p[1][0], p[1][1], p[1][2], p[1][3], FULL_STEP)
	#my_stepper_C = ItemLaneStepper(p[1][4], p[1][5], p[1][6], p[1][7], FULL_STEP)
	

	thread_A = threading.Thread(target=move)
	thread_B = threading.Thread(target=move1)
	thread_C = threading.Thread(target=move2)
	#thread_B = threading.Thread(target=move, args=(my_stepper_B,))
	#thread_C = threading.Thread(target=move, args=(my_stepper_C,))

	try:
		thread_A.start()
		thread_B.start()
		thread_C.start()
	except:
		print("Unable to start a new thread")

if __name__ == '__main__':
    main()
