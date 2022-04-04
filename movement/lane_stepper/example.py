import build.ItemLaneSystem as ils

sys = ils.ItemLaneSystem()

# Example call to rotate_n where we specify a list of channels, directions, speeds, and rotations
# for each of the motors described to follow
print("Rotating 2 (ch 0/1) together with rotate_n")
sys.rotate_n([0, 1], ["cw", "ccw"], [1.0, 1.0], [1.0, 1.0])

print("Rotating 3 (ch 3/4/5) together with rotate_n")
sys.rotate_n([3, 4, 5], ["cw", "cw", "cw"], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0])

# Example call to rotate_pair by manually inserting the arguments (which gets long pretty quickly)
# sys.rotate_pair(0, "cw", 1.0, 1.0, 1, "ccw", 1.0, 1.0)

# Example call to rotate_trio using the unpacking feature of python's lists--could be used to 
# perform calls to multiple lanes in the same level
motor0_args = [0, "cw", 1.0, 1.0]
motor1_args = [1, "ccw", 1.0, 1.0]
motor2_args = [2, "cw", 1.0, 1.0]

sys.rotate_trio(*motor0_args, *motor1_args, *motor2_args)

sys.zero_all_pins()

"""
for i in range(0,6):
    sys.rotate(i, "cw", 1.0, 0.5)
"""
