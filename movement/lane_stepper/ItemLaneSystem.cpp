/*
   For use with the 12V NEMA-17 motors to be used in the item lane components of the machine--
   this code can be used with other bipolar stepper motors but requires changes to the number of
   steps per rotation (STEPS_PER_ROT) depending on the stride angle of the motor.
*/

#include <cstdint>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

#include <mcp23017.h>
#include <wiringPi.h>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

// Address constants
#define MCP0_ADDR       (0x20)
#define MCP1_ADDR       (0x21)

#define PIN_BASE0       (100)
#define PIN_BASE1       (200)

// Pin, step sequence, and multithreading constants
#define PINS_PER_MCP    (12)
#define PINS_PER_MOTOR  (4)
#define MOTORS_PER_MCP  (3)

#define HALF_STEP_LEN   (8)

#define MAX_WORKERS     (3)

// Rotation constants for determining steps needed for a full rotation
#define STEPS_PER_ROT   (400)
#define MIN_DELAY       (1)
#define MAX_DELAY       (100)

using namespace std;

static const int HALF_SEQUENCE[HALF_STEP_LEN][PINS_PER_MOTOR] = { {1, 0, 1, 0},
                                                                  {0, 0, 1, 0},
                                                                  {0, 1, 1, 0},
                                                                  {0, 1, 0, 0},
                                                                  {0, 1, 0, 1},
                                                                  {0, 0, 0, 1},
                                                                  {1, 0, 0, 1},
                                                                  {1, 0, 0, 0} };


// ItemLaneStepper class designed to control a any stepper motor in an item lane
class ItemLaneSystem {
public:
    // Constructor that initializes all of the needed details for the item lanes
    ItemLaneSystem() {
        // Prepare the iface for the GPIO pins coming out of the Pi w/ the MCP23017 expander boards
        wiringPiSetup();
        mcp23017Setup(PIN_BASE0, MCP0_ADDR);
        mcp23017Setup(PIN_BASE1, MCP1_ADDR);

        // Set all of the relevant pins to output mode
        for(int i = 0; i < PINS_PER_MCP; i++) {
            pinMode(PIN_BASE0 + i, OUTPUT);
            pinMode(PIN_BASE1 + i, OUTPUT);
        }
    }

    // Rotate one motor either cw or ccw at a given speed for a specific amount of rotations
    //
    // Parameters:
    // - channel:   motor to move in the system--maps 0 through 5 to the appropriate base pin for a motor
    // - direction: 'cw' for clockwise or 'ccw' for counterclockwise movement
    // - speed:     used to determine how quickly each step takes--bounded between [0, 1.00]
    // - rotations: number of rotations to undertake
    void rotate(int channel, string direction, float speed, float rotations) {
        int base_pin = this->channel_to_base(channel);     // Convert digit channel to base pin addr.
        int step_sleep = this->speed_to_delay(speed);      // Convert speed to step sleep amount (ms)
        int step_count = int(rotations * STEPS_PER_ROT);   // Convert rotations to number of steps

        // Set rotation direction
        int dir = -1;

        if (direction == "cw") {
            dir = 0;
        } else if (direction == "ccw") {
            dir = 1;
        } else {
            cout << "Invalid direction chosen, staying idle..." << endl;
            return;
        }

        for(int j = 0; j < step_count; j++) {
            // Change the index of the step we want depending on the direction
            int cur_step = (dir ? step_count - j - 1 : j);

            // Inner loop runs through the pins in order to determine which value is placed per pin
            for(int i = 0; i < PINS_PER_MOTOR; i++) {
                digitalWrite(base_pin + i, HALF_SEQUENCE[cur_step % HALF_STEP_LEN][i]);
            }

            delay(step_sleep);
        }

        // Reset all pins back to digital low
        for(int i = 0; i < PINS_PER_MOTOR; i++) {
            digitalWrite(base_pin + i, 0);
        }
    }

    // Rotate a number of stepper motors using arrays sent in to each of the arguments with
    // corresponding entries belonging to different channels (up to MAX_WORKERS amount)
    //
    // NOTE: the machine prototype uses the following number scheme for the lanes:
    //
    //  [0] [3]
    //  [1] [4]
    //  [2] [5]
    //
    // Channels 0 and 3, 1 and 4, and 2 and 5 are the pairs that are able to run in parallel,
    // so we should pick channels that have the same modulus value out of 3 to run in this manner
    //
    // Parameters:
    // - channels:   Vector of numbered channels of motors to run
    // - directions: Vector of directions the corresponding motors will turn
    // - speeds:     Vector of speeds for the corresponding motor (bounded between 0.0 and 1.0)
    // - rotations:  Vector of the # of rotations the corresponding motors should take
    void rotate_n(vector<int> channels, vector<string> directions, vector<float> speeds, vector<float> rotations) {
        size_t num_chans = channels.size();

        if((num_chans != directions.size()) && (num_chans != speeds.size()) && (num_chans != rotations.size())) {
            cout << "Mismatched lengths of lists for channels, directions, speeds, and rotations, staying idle..." << endl;
            return;
        }

        for(int i = 0; i < num_chans; i++) {
            workers[i] = thread(&ItemLaneSystem::rotate, this, channels[i], directions[i],
                                                              speeds[i], rotations[i]);
        }

        for(int i = 0; i < num_chans; i++) {
            workers[i].join();
        }
    }
 
    // Set all of the pins on all expansion boards connecting to the motors to digital low--this
    // is recommended to run once a rotation is complete to avoid stray power draw
    void zero_all_pins() {
        for(int i = 0; i < PINS_PER_MCP; i++) {
            digitalWrite(PIN_BASE0 + i, 0);
            digitalWrite(PIN_BASE1 + i, 0);
        }
    }

private:
    thread workers[MAX_WORKERS];           // Private threads for use in running simultaneous motors

    // Maps sequential, positive integer channels to the appropriate base pin address for the motor
    // that is at that place (i.e. 0 to 100, 1 to 104, 2 to 108, 3 to 200, 4 to 204, 5 to 208, etc.)
    int channel_to_base(int channel) {
       return PIN_BASE0 + (PIN_BASE0 * ((int) (channel / MOTORS_PER_MCP))) +
                ((channel % MOTORS_PER_MCP) * PINS_PER_MOTOR);
    }

    // Converts speed into delay amount for the purposes of rotation
    int speed_to_delay(float speed) {
        return int(MIN_DELAY + MAX_DELAY * (1 - speed));
    }
};

PYBIND11_MODULE(ItemLaneSystem, m) {
    pybind11::class_<ItemLaneSystem>(m, "ItemLaneSystem")
        .def(pybind11::init<>())
        .def("rotate", &ItemLaneSystem::rotate)
        .def("rotate_n", &ItemLaneSystem::rotate_n)
        .def("zero_all_pins", &ItemLaneSystem::zero_all_pins);
}

// Test execution to see that motors can work independently and together
int main() {
    ItemLaneSystem sys = ItemLaneSystem();

    for(int i = 0; i < 6; i++) {
        cout << "Running motor " << i << "..." << endl;
        sys.rotate(i, "cw", 1.0, 0.5);
    }

    vector<int> channels = {1, 3, 0};
    vector<string> directions = {"cw", "ccw", "cw"};
    vector<float> speeds = {1.0, 1.0, 2.0};
    vector<float> rotations = {1.0, 1.0, 1.0};

    cout << "Running motors 0, 1, and 3 together..." << endl;
    sys.rotate_n(channels, directions, speeds, rotations);

    cout << "Running motors 1 and 2 together..." << endl;
    sys.rotate_n({1, 2}, {"cw", "cw"}, {1.0, 1.0}, {2.0, 1.0});
    
    cout << "Running motors 3 and 4 together..." << endl;
    sys.rotate_n({3, 4}, {"ccw", "ccw"}, {1.0, 1.0}, {1.0, 1.0});
    
    cout << "Running motors 0 (twice cw) and 5 (once ccw) together..." << endl;
    sys.rotate_n({0, 5}, {"cw", "ccw"}, {1.0, 1.0}, {2.0, 1.0});
}
