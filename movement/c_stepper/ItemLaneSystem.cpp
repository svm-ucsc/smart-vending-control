#include <cstdint>
#include <iostream>
#include <thread>

#include <mcp23017.h>
#include <wiringPi.h>

// Address constants
#define MCP_0_ADDR (0x20)
#define MCP_1_ADDR (0x21)

#define PIN_BASE_0 (100)
#define PIN_BASE_1 (200)

// Pin & multithreading constants
#define PINS_PER_MCP (16)
#define MAX_WORKERS (3)

// Sequence of steps for full steps on a stepper motor (more granular)
static const uint32_t FULL_SEQUENCE[8][4] = { {1, 0, 0, 1},
                                              {1, 0, 0, 0},
                                              {1, 1, 0, 0},
                                              {0, 1, 0, 0},
                                              {0, 1, 1, 0},
                                              {0, 0, 1, 0},
                                              {0, 0, 1, 1},
                                              {0, 0, 0, 1} };

// Sequence of steps for half steps on a stepper motor (less granular)
static const uint32_t HALF_SEQUENCE[4][4] = { {1, 0, 0, 0},
                                              {1, 1, 0, 0},
                                              {0, 1, 1, 0},
                                              {0, 0, 1, 1} };

// ItemLaneStepper class designed to control a any stepper motor in an item lane
class ItemLaneSystem {
public:
    // Constructor that initializes all of the needed details for the item lanes
    ItemLaneSystem() {
        // Prepare the iface for the GPIO pins coming out of the Pi w/ the MCP23017 expander boards
        wiringPiSetup();
        mcp23017Setup(PIN_BASE0, 0

    }

private:
};
