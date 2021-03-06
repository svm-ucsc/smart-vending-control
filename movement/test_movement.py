#!/usr/bin/python3

import lane_stepper.build.ItemLaneSystem as ls
import platform_stepper as ps


def main():
	plat_0 = ps.PlatformStepper(0)
	plat_0.reset_position()
	sys = ls.ItemLaneSystem()


	print("ERROR TEST STARTING (nothing should run at this point!)")
	sys.rotate_n([1, 5], ['cw'], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0])
	print("ERROR TEST ENDING")

	print("SEQUENTIAL TEST STARTING")

	# Example of moving the platform to the location of an item, dispensing, then coming back down
	# in sequential order
	plat_0.rotate('cw', 1000, 5)

	sys.rotate(0, 'cw', 1.0, 1)
	sys.rotate(1, 'cw', 1.0, 1)
	sys.rotate(2, 'cw', 1.0, 1)

	plat_0.rotate('ccw', 1000, 5)

	print("SEQUENTIAL TEST ENDING")


	print("PARALLEL TEST STARTING")

	# Example of moving the platform to the location of an item, dispensing two at a time, then
	# coming back down (with parallelization)
	plat_0.rotate('ccw', 1000, 3)

	try:
		sys.rotate_n([3, 4, 5], ['cw', 'cw', 'cw'], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0])
	except:
		print("Unable to rotate")

	plat_0.rotate('cw', 1000, 3)

	print("PARALLEL TEST ENDING")

	# Cleanup
	sys.zero_all_pins()

def continuous_plat_test():
    plat_0 = ps.PlatformStepper(0)
    try:
    	while(True):
            dir = input("What direction?: ")
            num_rotations = int(input("How many rotations?: "))
            plat_0.rotate(dir, 300, num_rotations)
    except:
        return

if __name__ == '__main__':
	main()
