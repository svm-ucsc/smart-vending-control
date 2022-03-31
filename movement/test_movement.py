#!/usr/bin/python3

import threading
import lane_stepper as ls
import platform_stepper as ps

def main():
	plat_0 = ps.PlatformStepper(0)
	lane_0 = ls.ItemLaneStepper(0, ls.FULL_STEP)
	lane_1 = ls.ItemLaneStepper(1, ls.FULL_STEP)
	lane_2 = ls.ItemLaneStepper(2, ls.FULL_STEP)

	print("SEQUENTIAL TEST STARTING")

	# Example of moving the platform to the location of an item, dispensing, then coming back down
	# in sequential order
	plat_0.rotate('cw', 1000, 5)

	lane_0.rotate('cw', 20000, 1)
	lane_1.rotate('cw', 20000, 1)
	lane_2.rotate('cw', 20000, 1)

	plat_0.rotate('ccw', 1000, 5)

	print("SEQUENTIAL TEST ENDING")


	print("PARALLEL TEST STARTING")

	# Example of moving the platform to the location of an item, dispensing two at a time, then
	# coming back down (with parallelization)
	plat_0.rotate('ccw', 1000, 3)

	# We would need to define the calculations for number of rotations based on how many of
	# a particular item is being dispensed
	thread_0 = threading.Thread(target=lane_0.rotate, args=('cw', 10000, 2))
	thread_1 = threading.Thread(target=lane_1.rotate, args=('cw', 10000, 2))
	thread_2 = threading.Thread(target=lane_2.rotate, args=('cw', 10000, 2))

	try:
		# Launch all threads to rotate the three lanes together
		thread_0.start()
		thread_1.start()
		thread_2.start()
		
		# Wait for all three to finish
		thread_0.join()
		thread_1.join()
		thread_2.join()

	except:
		print("Unable to start a new thread")

	plat_0.rotate('cw', 1000, 3)

	print("PARALLEL TEST ENDING")

	# Cleanup
	lane_0.reset()
	lane_1.reset()
	lane_2.reset()

if __name__ == '__main__':
	main()
