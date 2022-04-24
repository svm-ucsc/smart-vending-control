from weight_sensor import *

def test_round(num_trials:int, sensor):
    total_error = 0
    total_error_percent = 0
    for i in range(num_trials):
        item_weight = float(input("Place an item on the scale. Enter the item's known weight in grams\n>"))
        mes_weight = sensor.get_grams()
        print("Measured weight(grams): {}".format(mes_weight))
        dif = (mes_weight - item_weight) if (mes_weight > item_weight) else (item_weight - mes_weight)
        dif_percent = (dif/item_weight) * 100
        total_error_percent += dif_percent
        total_error += dif
        print("Difference between actual and measured weights: {:.3f}, {:.3f}%".format(dif, dif_percent))
    return (total_error, total_error_percent)

def basic_tests(num_trials:int, sensor):
    """
    Performs basic functionality tests of weight sensors. Prints incremental progress.
    """
    sensor.calibrate()
    print("---------- Now starting basic functionality tests ----------")
    total_error, total_error_percent = test_round(num_trials, sensor)
    print("Basic functionality tests complete.")
    print("\tAverage measurement error(grams): {:.3f}".format(total_error/num_trials))
    print("\tAverage measurement error(percent): {:.3f}%".format(total_error_percent/num_trials))

def location_tests(num_trials:int, sensor):
    print("---------- Now starting location tests ----------")
    print("Instructions:\n")
    print("\tThe purpose of these tests is to test the effect of item location during calibration.")
    print("\tSensor accuracy will be tested with the calibrating item placed on the left, right, and")
    print("\tcenter of the platform. Use the same calibrating and test items each round.\n")
    
    # Left test
    print("----Now testing calibration on left side----")
    print("Place the item on the left side during calibration!\n")
    sensor.calibrate()
    l_error, l_percent = test_round(num_trials, sensor)
    
    # Center test
    print("----Now testing calibration in center----")
    print("Place the item in the center during calibration!\n")
    sensor.calibrate()
    c_error, c_percent = test_round(num_trials, sensor)

    # Right test
    print("----Now testing calibration on right side----")
    print("Place the item on the right side during calibration!\n")
    sensor.calibrate()
    r_error, r_percent = test_round(num_trials, sensor)

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
    my_sensor = WeightSensor_HX711(dout=17, pd_sck=18, gain=128)
    basic_tests(5, my_sensor)
    location_tests(3, my_sensor)
    GPIO.cleanup()

if __name__ == "__main__":
    main()