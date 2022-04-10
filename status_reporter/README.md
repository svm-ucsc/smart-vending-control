## Status Reporter

Small module designed to integrate with the Pi and display the IP address upon boot
to make SSH-ing into the Pi easy

### Raspberry Pi Kiosk Setup

The autostart file in `/etc/xdg/autostart` should point to and run the status_reporter.py
file before the kiosk mode and interface is started.

