/*
   For use with the 28BYJ-48 5V stepper motors to be used in the item lane components of the machine

   Specs:
     Rated voltage: 5V
     Tested current: 0.3A
     Speed Var. Ratio: 1/64
     Stride Angle: 5.625 deg. -> NOTE: 360 deg = 4096 * (5.625 / 64)
*/

#include <cstdint>
#include <iostream>
#include <string>
#include <thread>

#include <mcp23017.h>
#include <wiringPi.h>

// Address constants
#define MCP0_ADDR       (0x20)
#define MCP1_ADDR       (0x21)

#define PIN_BASE0       (100)
#define PIN_BASE1       (200)

// Pin, step sequence, and multithreading constants
#define PINS_PER_MCP    (16)
#define PINS_PER_MOTOR  (4)

#define FULL_STEP_LEN   (8)

#define MAX_WORKERS     (3)

// Rotation constnants for determining steps needed for a full rotation
#define STEPS_PER_ROT   (4096)
#define MIN_DELAY       (1)
#define MAX_DELAY       (100)

using namespace std;

// Sequence of steps for full steps on a stepper motor (more granular)
static const int FULL_SEQUENCE[FULL_STEP_LEN][PINS_PER_MOTOR] = { {1, 0, 0, 1},
                                                                  {1, 0, 0, 0},
                                                                  {1, 1, 0, 0},
                                                                  {0, 1, 0, 0},
                                                                  {0, 1, 1, 0},
                                                                  {0, 0, 1, 0},
                                                                  {0, 0, 1, 1},
                                                                  {0, 0, 0, 1} };

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
    // - channel: motor to move in the system--maps 0 through 5 to the appropriate base pin for a motor
    // - direction: 'cw' for clockwise or 'ccw' for counterclockwise movement
    // - speed: used to determine how quickly each step takes--bounded between [0, 1.00]
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
                digitalWrite(base_pin + i, FULL_SEQUENCE[cur_step % FULL_STEP_LEN][i]);
            }

            delay(step_sleep);
        }

        // Reset all pins back to digital low
        for(int i = 0; i < PINS_PER_MOTOR; i++) {
            digitalWrite(base_pin + i, 0);
        }
    }

    // Explicitly rotate a pair of stepper motors together
    void rotate_pair(int ch0, string dir0, float spd0, float rot0,
                     int ch1, string dir1, float spd1, float rot1) {
        // To use multithreading within a class function, specify the signature and "this"
        workers[0] = thread(&ItemLaneSystem::rotate, this, ch0, dir0, spd0, rot0);
        workers[1] = thread(&ItemLaneSystem::rotate, this, ch1, dir1, spd1, rot1);

        workers[0].join();
        workers[1].join();
    }

    // Set all of the pins on all expansion boards connecting to the motors to digital low
    void zero_all_pins() {
        for(int i = 0; i < PINS_PER_MCP; i++) {
            digitalWrite(PIN_BASE0 + i, 0);
            digitalWrite(PIN_BASE1 + i, 0);
        }
    }

private:
    thread workers[MAX_WORKERS];                // Private threads for use in running simultaneous motors

    // Maps sequential, positive integer channels to the appropriate base pin address for the motor
    // that is at that place (i.e. 0 to 100, 1 to 104, 2 to 108, 3 to 112, 4 to 200, 5 to 204, etc.)
    int channel_to_base(int channel) {
       return PIN_BASE0 + (PIN_BASE0 * ((int) (channel / PINS_PER_MOTOR))) +
                ((channel % PINS_PER_MOTOR) * PINS_PER_MOTOR);
    }

    // Converts speed into delay amount for the purposes of rotation
    int speed_to_delay(float speed) {
        return int(MIN_DELAY + MAX_DELAY * (1 - speed));
    }
};

int main() {
    ItemLaneSystem sys = ItemLaneSystem();

    for(int i = 0; i < 6; i++) {
        cout << "Running motor " << i << "..." << endl;
        sys.rotate(i, "cw", 1.0, 0.5);
    }

    cout << "Running motors 1 and 2 together..." << endl;
    sys.rotate_pair(1, "cw", 1.0, 1.0, 2, "cw", 1.0, 1.0);
    
    cout << "Running motors 3 and 4 together..." << endl;
    sys.rotate_pair(3, "ccw", 1.0, 1.0, 4, "ccw", 1.0, 1.0);
    
    cout << "Running motors 0 (twice cw) and 5 (once ccw) together..." << endl;
    sys.rotate_pair(0, "cw", 1.0, 2.0, 5, "ccw", 1.0, 1.0);
}
