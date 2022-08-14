import led
import time

# Initialise the module and load the map
led.init()
led.mapFromFile("map")

# The value to set each LED to
value = 1

# The next LED to set (according to mapping)
i = 0

# Total number of LEDs
MAX = 32

# Cycle through each LED, turning them on and off again
while True:
    # Set the next LED
    led.set(i, value)
    i += 1
    # Loop back round and toggle the value
    if i >= MAX:
        i = 0
        value = 1 - value
    # Take your time
    time.sleep(0.5)
