#include <iostream>
#include <cstdint>
#include <thread>

#include <mcp23017.h>
#include <wiringPi.h>

// Base pin numbers to correspond to each of the MCPs connected (i.e. the first
// pin for the MCP w/ address 0x20 is 100, for 0x21 is 200, etc.)
#define BASE0 (100)
#define BASE1 (200)

// Number of extra pins brought on by MCP23017
#define PINS_PER_MCP (16)

#define MAX_WORKERS (3)

using namespace std;

static const uint32_t SEQUENCE[8][4] = { {1, 0, 0, 1},
                                         {1, 0, 0, 0},
                                         {1, 1, 0, 0},
                                         {0, 1, 0, 0},
                                         {0, 1, 1, 0},
                                         {0, 0, 1, 0},
                                         {0, 0, 1, 1},
                                         {0, 0, 0, 1} };

void runMotor(int basePin) {
    // Outer loop is a series of steps to take
    for(int j = 0; j < 4096; j++) {
        // Inner loop runs through which pin gets which value in the sequence
        for(int i = 0; i < 4; i++) {
            digitalWrite(basePin + i, SEQUENCE[j % 8][i]);
        }
        
        delay(1);
    }

    for(int i = 0; i < 4; i++) {
        digitalWrite(basePin + i, 0);
    }
}

int main(void) {
    // Initialize the wiringPi library
    wiringPiSetup();

    // Initialize the three MCPs for each of the addresses defined
    mcp23017Setup(BASE0, 0x20);
    mcp23017Setup(BASE1, 0x21);

    for(int i = 0; i < PINS_PER_MCP; i++) {
        pinMode(BASE0 + i, OUTPUT);
        pinMode(BASE1 + i, OUTPUT);
    }

    thread workers[MAX_WORKERS];
    
    // Launch a thread for each one of the motors we want to run together
    workers[0] = thread(runMotor, BASE0);
    workers[1] = thread(runMotor, BASE0 + 4);
    workers[2] = thread(runMotor, BASE0 + 8);

    // Wait for all threads to finish
    for(int i = 0; i < MAX_WORKERS; i++) {
        workers[i].join();
    }
}
