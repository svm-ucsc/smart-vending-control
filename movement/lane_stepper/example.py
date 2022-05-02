import build.ItemLaneSystem as ils
import time

sys = ils.ItemLaneSystem()

sys.rotate(4, "cw", 1.0, 10.0)

# Example call to rotate_n where we specify a list of channels, directions, speeds, and rotations
# for each of the motors described to follow
print("Rotating 2 (ch 0/3) together with rotate_n")
sys.rotate_n([0, 3], ["cw", "ccw"], [1.0, 1.0], [1.0, 1.0])

print("Rotating 3 (ch 3/4/5) together with rotate_n")
sys.rotate_n([3, 4, 5], ["cw", "cw", "cw"], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0])

chans = [0, 1, 2]
dirs = ["cw", "ccw", "cw"]
spds = [1.0, 1.0, 1.0]
rots = [1.0, 1.0, 1.0]

print("Rtoating 3 (ch 0/1/2) together with rotate_n")
sys.rotate_n(chans, dirs, spds, rots)

sys.zero_all_pins()

