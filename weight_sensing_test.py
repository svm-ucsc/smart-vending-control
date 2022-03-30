from weight_sensor import *

TOL = 0 minimum squared difference for change to be registered

my_sensor = WeightSensor_HX711(dout=17, pd_sck=18, gain=128)
my_sensor.calibrate()

print("---------- Now starting basic functionality tests ----------")
item1_weight = input("Place an item on the scale. Enter the item's weight in grams")
print("Measured weight(grams): {}".format(my_sensor.get_grams()))