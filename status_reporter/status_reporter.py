import RGB1602
import socket
import time

# Display constants
COLS = 16
ROWS = 2

# Network constants
DEFAULT_DNS = "8.8.8.8"
DEFAULT_PORT = 80

# Color combination for yellow (#FFFF00)
color_combo = (0xFF, 0xFF, 0x00)

def getIP():
    # Opens a socket for the purposes of getting the IP after a connection
    # can be established
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((DEFAULT_DNS, DEFAULT_PORT))
    ip_addr = s.getsockname()[0]
    
    # If address was empty, wait for a little bit, check again, etc
    if ip_addr is None:
        for i in range(0, 3):
            time.sleep(5)
            ip_addr = s.getsockname()[0]

            # If the next attempt has an IP, return IP
            if ip_addr is not None:
                s.close()
                return ip_addr

        # Reached if none of the connection attempts were successful
        if ip_addr is None:
            s.close()
            return "No n/w conn."

    s.close()

    return ip_addr

def main():
    # Initialize
    lcd = RGB1602.RGB1602(COLS, ROWS)

    # Clear display, reset cursor, set color
    lcd.clear()
    lcd.setCursor(0, 0)
    lcd.setRGB(*color_combo)

    # Show flavor text
    lcd.printout("Booting...")
    time.sleep(3)
    lcd.clear()

    # Print out the IP address of the Pi
    lcd.setCursor(0, 0)
    lcd.printout("IP Address:")
    lcd.setCursor(0, 1)
    lcd.printout(getIP())

if __name__=="__main__":
    main()
