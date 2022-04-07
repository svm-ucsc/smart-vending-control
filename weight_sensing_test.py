from weight_sensor import *

def basic_tests(num_trials:int, sensor):
    """
    Performs basic functionality tests of weight sensors. Prints incremental progress.
    """
    total_error = 0
    print("---------- Now starting basic functionality tests ----------")
    for i in range(num_trials):
        item_weight = float(input("Place an item on the scale. Enter the item's known weight in grams"))
        mes_weight = sensor.get_grams()
        print("Measured weight(grams): {}".format(mes_weight))
        dif = mes_weight - item_weight
        total_error += dif
        print("Difference between actual and measured weights: {}".format(dif))
    print("Basic functionality tests complete. Average measurement error(grams): {}".format(total_error/num_trials))

def main():
    my_sensor = WeightSensor_HX711(dout=17, pd_sck=18, gain=128)
    my_sensor.calibrate()
    basic_tests(3, my_sensor)
    GPIO.cleanup()

if __name__ == "__main__":
    main()