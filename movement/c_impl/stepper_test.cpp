#include <iostream>
#include <cstdint>
#include <thread>

#include <mcp23017.h>
#include <wiringPi.h>

// Base pin numbers to correspond to each of the MCPs connected (i.e. the first
// pin for the MCP w/ address 0x20 is 100, for 0x21 is 200, etc.)
#define BASE0 (100)
#define BASE1 (200)
#define BASE2 (300)

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
}

int main(void) {
    // Initialize the wiringPi library
    wiringPiSetup();

    // Initialize the three MCPs for each of the addresses defined
    mcp23017Setup(BASE0, 0x20);
    mcp23017Setup(BASE1, 0x21);
    mcp23017Setup(BASE2, 0x22);

    for(int i = 0; i < 4; i++) {
        pinMode(BASE0 + i, OUTPUT);
        pinMode(BASE1 + i, OUTPUT);
        pinMode(BASE2 + i, OUTPUT);
    }

    thread workers[3];

    for(int i = 0; i < 3; i++) {
        workers[i] = thread(runMotor, (i + 1) * 100);
    }

    for(int i = 0; i < 3; i++) {
        workers[i].join();
    }

}
