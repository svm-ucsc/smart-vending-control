# Smart Vending Machine Control

## Project Structure

```
.
├── client.py                      # Client file
├── main.py                        # Entry point to controlling mechanical parts with net requests
├── movement                       # Module for all movement in the machine
│   ├── __init__.py
│   ├── lane_stepper.py            # Item lane control
│   ├── platform_stepper.py        # Dispensing platform control
│   └── test_movement.py           # Simulated manual item dispense pipeline
├── README.md
└── weight_sensor.py               # Weight sensor module
```
