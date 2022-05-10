# Smart Vending Machine Control

## Project Structure

```
.
├── client.py                        # Client file
├── main.py                          # Entry point to controlling mechanical pieces w/ order
├── main_test.py                     # Test for main file
├── movement         
│   ├── channel0_pos.txt             # Base file for keeping track of position (recreated on boot)
│   ├── __init__.py
│   ├── lane_stepper
│   │   ├── build/
│   │   ├── CMakeLists.txt
│   │   ├── example.py               # Sample script for movement with the lane steppers by themselves
│   │   └── ItemLaneSystem.cpp       # Source for the ItemLaneSystem library for lane steppers
│   ├── platform_stepper.py          # Module for moving the platform stepper motor
│   └── test_movement.py             # Script to test all of the movement modules together
├── README.md
├── status_reporter
│   ├── README.md
│   ├── RGB1602.py                   # Module for outputting to the RGB LCD
│   └── status_reporter.py           # One-shot script to show off the IP address for debug msgs
├── weight_sensing_test.py           # Script to test the weight sensor
└── weight_sensor.py                 # Module for testing the weight sensor on the platform
```
