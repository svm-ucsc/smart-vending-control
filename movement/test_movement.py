#!/usr/bin/python3

import time
import lane_stepper.build.ItemLaneSystem as ls
import platform_stepper as ps


def machine_motor_test():
    s = ps.PlatformStepper(0)
    sys = ls.ItemLaneSystem()

    start_rot = 6.0                         # Number of rotations to go to home on cold boot
    lane_rot = 5.8                          # Number of rotations between item lanes
        
    eas_spd = 35                            # Best speed for eased motion
    lin_spd = 500                           # Best speed for linear motion

    
    # Startup test (assumed to be run when the machine is cold booted)
    s.rotate('ccw', 500, start_rot)
    s.zero_position()
        
    # Reset position
    print("Resetting position to home row...")
    s.reset_position()
    print("Reset complete.")
    time.sleep(1)

    # Ease motion test
    print("Beginning ease motion test...")
    s.rotate('ccw', eas_spd, 2 * lane_rot, True)
    
    # Pretend dispense
    print("Running through all pairs of item lines...")
    sys.rotate_n([0,3], ['cw', 'cw'], [1.0, 1.0], [20.0, 20.0])
    sys.rotate_n([1,4], ['cw', 'cw'], [1.0, 1.0], [20.0, 20.0])
    sys.rotate_n([2,5], ['cw', 'cw'], [1.0, 1.0], [20.0, 20.0])
    print("Pairwise test complete."

    print("Resetting position...")
    s.reset_position()
    print("Dispense motion test complete.")

def continuous_plat_test():
    plat_0 = ps.PlatformStepper(0)
    try:
    	while(True):
            dir = input("What direction?: ")
            num_rotations = int(input("How many rotations?: "))
            plat_0.rotate(dir, 300, num_rotations)
    except:
        return


def main():
    # Run the test
    machine_motor_test()

    # Cleanup
    sys.zero_all_pins()

if __name__ == '__main__':
    main()
