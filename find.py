# Helpful for finding a desired mapping.
# On load, it will read from file 'map'.
# It will light up LED 0/0/0 (device address) and responds to user input
# Input:
#   -  (nothing)
#   -> move to light up the next LED
#   -  "map <num>"
#   -> maps 'num' to the current LED
#   -  "save"
#   -> saves the current mapping to 'map' and exits

import led

# Initialise module
led.init()
led.mapFromFile("map")

# The currently lit pin
device = 0
port = 0
bit = 0

# If a new pin needs to be lit, the old pin is stored as a tuple in this variable
update = None

while True:
    # Perform updates if required
    if update:
        (d, p, b) = update
        update = None
        # Turn off old state
        led.setDPB(d, p, b, 0)
        # Turn on new state
        led.setDPB(device, port, bit, 1)
    # Next command
    line = input()
    if line == "":
        # Remember previous state for update
        update = (device, port, bit)
        # Update state
        bit += 1
        if bit > 7:
            bit = 0
            port += 1
        if port > 1:
            port = 0
            device += 1
        if device > 1:
            device = 0
    elif line == "save":
        # Save and exit
        led.saveMapToFile("map")
        break
    elif line.startswith("map "):
        # Check arguments
        line = line.split(" ")
        if len(line) != 2:
            print("Too many arguments in 'map' command")
            continue
        # Convert to integer
        try:
            num = int(line[1])
        except:
            print("Cannot turn argument into number")
            continue
        # Map num to device/port/bit
        led.mapLED(num, device, port, bit)
    else:
        print("Unrecognised command")
