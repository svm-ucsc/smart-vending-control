#include <cstdint>
#include <iostream>
#include <thread>

#include <mcp23017.h>
#include <wiringPi.h>

#define PINS_PER_MCP (16)

#define PIN_BASE_0 (100)
#define PIN_BASE_1 (100)

#define MAX_WORKERS (3)

// Sequence of steps for full steps on a stepper motor
static const uint32_t FULL_SEQUENCE[8][4] = { {1, 0, 0, 1},
                                              {1, 0, 0, 0},
                                              {1, 1, 0, 0},
                                              {0, 1, 0, 0},
                                              {0, 1, 1, 0},
                                              {0, 0, 1, 0},
                                              {0, 0, 1, 1},
                                              {0, 0, 0, 1} };
class ItemLaneStepper {

};
