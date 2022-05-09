from weight_sensor import *
from movement import platform_stepper as ps

def test_round_dif_items(num_trials:int, sensor):
    total_error = 0
    total_error_percent = 0
    for i in range(num_trials):
        item_weight = float(input("Place an item on the scale. Enter the item's known weight in grams\n>"))
        mes_weight = sensor.get_grams(num_samples=16)
        print("Measured weight(grams): {}".format(mes_weight))
        dif = (mes_weight - item_weight) if (mes_weight > item_weight) else (item_weight - mes_weight)
        dif_percent = (dif/item_weight) * 100
        total_error_percent += dif_percent
        total_error += dif
        print("Difference between actual and measured weights: {:.3f}, {:.3f}%".format(dif, dif_percent))
    return (total_error, total_error_percent)

def test_round_same_item(num_trials:int, sensor):
    total_error = 0
    total_error_percent = 0
    print("Now starting a round of tests for one item")
    item_weight = float(input("Please enter the expected weight of the item in grams: \n>"))
    for i in range(num_trials):
        mes_weight = sensor.get_grams(num_samples=16)
        print("Measured weight(grams): {}".format(mes_weight))
        dif = (mes_weight - item_weight) if (mes_weight > item_weight) else (item_weight - mes_weight)
        dif_percent = (dif/item_weight) * 100
        total_error_percent += dif_percent
        total_error += dif
        print("Difference between actual and measured weights: {:.3f}, {:.3f}%".format(dif, dif_percent))

def basic_tests(num_trials:int, sensor):
    """
    Performs basic functionality tests of weight sensors. Prints incremental progress.
    """
    sensor.calibrate()
    print("---------- Now starting basic functionality tests ----------")
    print("The purpose of these tests is to ensure the sensors are working as expected.")
    print("You will weigh a few items. If the sensors are working properly, the measured weights")
    print("Should be relatively close to the known weight")
    total_error, total_error_percent = test_round_dif_items(num_trials, sensor)
    print("Basic functionality tests complete.")
    print("\tAverage measurement error(grams): {:.3f}".format(total_error/num_trials))
    print("\tAverage measurement error(percent): {:.3f}%".format(total_error_percent/num_trials))

def calib_weight_vs_accuracy(sensor, num_items=5, num_to_avg=3):
    print("---------- Now Testing the Effect of Calibrating Weight on Measurement Accuracy ----------")
    
    def trial():
        print("Now starting calibration")
        sensor.calibrate()
        print("For each item, including the calibrating item, you will weigh the item {} times".format(num_to_avg))
        print("and get the average measurement accuracy.")
        for i in range(num_items):
            test_round_same_item(num_to_avg, sensor)

    for i in range(num_items):
        trial()

def item_weight_vs_accuracy(sensor, num_items=5, num_to_avg=5):
    print("---------- Now Testing the Effect of Item Weight on Measurement Accuracy ----------")  
    print("Now starting calibration")
    sensor.calibrate()
    print("For each item, you will weigh the item {} times".format(num_to_avg))
    for i in range(num_items):
        print("Now testing with item number {}".format(i+1))
        test_round_same_item(num_to_avg, sensor)

def test_warmup(sensor, num_trials:int=10):
    print("---------- Now Testing the Effect of a Warmup Period on Accuracy ----------")
    print("---Now testing accuracy without warmup")
    sensor.calibrate()
    test_round_same_item(num_trials, sensor)

    print("--- Now testing with 2 minute warmup period BEFORE calibration")
    sensor.reset()
    sensor.warmup(minutes=2)
    sensor.calibrate()
    test_round_same_item(num_trials, sensor)

    print("--- Now testing with 2 minute warmup period AFTER calibration")
    sensor.reset()
    sensor.calibrate()
    sensor.warmup(minutes=2)
    test_round_same_item(num_trials, sensor)


def drop_height_test(sensor):
    print("---------- Now Testing the Effect of Drop Height on Measurement Accuracy ----------")  

def effect_of_movement(sensor):
    print("---------- Now Testing the Effect of Movement on Measurement Accuracy ----------")
    plat = ps.PlatformStepper(0)
    plat.reset_position()
    sensor.calibrate()

    print("--- Now performing baseline tests(no movement)")
    test_round_same_item(3, sensor)

    print("--- Now performing test after moving up")
    plat.rotate('ccw', 300, 8, False)
    test_round_same_item(3, sensor)

    print("--- Now performing test after moving down")
    plat.rotate('cw', 300, 8, False)
    test_round_same_item(3, sensor)

def calibration_location_tests(num_trials:int, sensor):
    print("---------- Now starting location tests ----------")
    print("Instructions:\n")
    print("\tThe purpose of these tests is to test the effect of item location during calibration.")
    print("\tSensor accuracy will be tested with the calibrating item placed on the left, right, and")
    print("\tcenter of the platform. Use the same calibrating and test items each round.\n")
    
    # Left test
    print("----Now testing calibration on left side----")
    print("Place the item on the left side during calibration!\n")
    sensor.calibrate()
    l_error, l_percent = test_round_dif_items(num_trials, sensor)
    
    # Center test
    print("----Now testing calibration in center----")
    print("Place the item in the center during calibration!\n")
    sensor.calibrate()
    c_error, c_percent = test_round_dif_items(num_trials, sensor)

    # Right test
    print("----Now testing calibration on right side----")
    print("Place the item on the right side during calibration!\n")
    sensor.calibrate()
    r_error, r_percent = test_round_dif_items(num_trials, sensor)

    # Display results
    print("-------Location tests complete!-------")
    print("Left side results:")
    print("\tAverage measurement error(grams): {:.3f}".format(l_error/num_trials))
    print("\tAverage measurement error(percent): {:.3f}%".format(l_percent/num_trials))
    print("Center results: ")
    print("\tAverage measurement error(grams): {:.3f}".format(c_error/num_trials))
    print("\tAverage measurement error(percent): {:.3f}%".format(c_percent/num_trials))
    print("Right side results: ")
    print("\tAverage measurement error(grams): {:.3f}".format(r_error/num_trials))
    print("\tAverage measurement error(percent): {:.3f}%".format(r_percent/num_trials))
    

def main():
    try:
      my_sensor = WeightSensor_HX711(dout=17, pd_sck=18, gain=128)
      basic_tests(3, my_sensor)
      my_sensor.reset()
      calibration_location_tests(3, my_sensor)
      GPIO.cleanup()
    except:
      GPIO.cleanup()

if __name__ == "__main__":
    main()
