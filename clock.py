import led
import time
import RPi.GPIO as GPIO

# Pin number for the button
BUTTON_PIN = 10

# FSM states
TIME_DAY = 0
TIME_DAY_HOLD = 1
TIME_NIGHT = 2
TIME_NIGHT_HIDE = 3
TIME_NIGHT_HOLD = 4

# Flags to identify parts of the day (day/night)
HOURS_DAY = 0
HOURS_NIGHT = 1

# Location of the DOT LEDs
DOT_NUM = 0

# Set the (two-digit) integer for the given pair of digits
# Parameter whic (0-1) determines which side (hour/minute)
def setInteger(i, which):
    # Scale to be which digit
    which = which * 2
    # Set the 'tens' digit
    tens = int(i / 10)
    setDigit(tens, which)
    # Set the 'units' digit
    units = i % 10
    setDigit(units, which + 1)

# Set the digit to have the given value
# Parameter which (0-3) determines which digit (left to right)
def setDigit(digit, which):
    # Index of first led address of digit
    start = (which * 7) + 1
    # Values (1/0) of each segment of the digit
    digit = splitDigit(digit)
    # Set each segment
    for i in range(7):
        led.set(start + i, digit[i])

# Split the (integer) digit into an array of on/off values
# for the digit's segments.
# Segments start at top bar, move clockwise, finish in middle
def splitDigit(digit):
    values = [
        [1, 1, 1, 1, 1, 1, 0], #0
        [0, 1, 1, 0, 0, 0, 0], #1
        [1, 1, 0, 1, 1, 0, 1], #2
        [1, 1, 1, 1, 0, 0, 1], #3
        [0, 1, 1, 0, 0, 1, 1], #4
        [1, 0, 1, 1, 0, 1, 1], #5
        [1, 0, 1, 1, 1, 1, 1], #6
        [1, 1, 1, 0, 0, 0, 0], #7
        [1, 1, 1, 1, 1, 1, 1], #8
        [1, 1, 1, 1, 0, 1, 1]  #9
    ]
    return values[digit]

# The main loop, takes a state (can be None), acts as appropriate
# and returns the new state
def loop(state, config):
    if state == TIME_DAY or state == TIME_NIGHT_HIDE or state == TIME_NIGHT_HOLD:
        # Get current time
        t = time.localtime()
        hour = t.tm_hour
        min = t.tm_min
        # Set hours
        setInteger(hour, 0)
        # Set minutes
        setInteger(min, 1)
        # If TIME_NIGHT_HIDE, show flashing dots
        if state == TIME_NIGHT_HIDE:
            dots = t.tm_sec % 2
            led.set(DOT_NUM, dots)
    elif state == TIME_NIGHT or state == TIME_DAY_HOLD:
        # Clear display
        led.setAll(0)
    # Determine new state
    return nextState(state, config)
    
# Return the new state based on the current state
def nextState(state, config):
    # Check for timeout of temporary state
    if state == TIME_NIGHT_HIDE:
        if config.checkTimeout():
            state = TIME_NIGHT
            config.clearTimeout()
    # Check for button events
    if GPIO.event_detected(BUTTON_PIN):
        if state == TIME_DAY:
            state = TIME_DAY_HOLD
        elif state == TIME_DAY_HOLD:
            state = TIME_DAY
        elif state == TIME_NIGHT:
            state = TIME_NIGHT_HIDE
            # Start timeout
            config.startTimeout()
        elif state == TIME_NIGHT_HIDE:
            state = TIME_NIGHT_HOLD
            # End timeout
            config.clearTimeout()
        elif state == TIME_NIGHT_HOLD:
            state = TIME_NIGHT
    # Update day hours
    hours = getHours(config)
    # initial undecided state - set first state
    if state == None:
        if hours == HOURS_DAY:
            return TIME_DAY
        else:
            return TIME_NIGHT
    # switch from day to night if needed
    if state == TIME_DAY or state == TIME_DAY_HOLD:
        if hours == HOURS_DAY:
            return state
        else:
            return TIME_NIGHT
    # switch from night to day if needed
    if hours == HOURS_DAY:
        # Before switch, cancel any timeouts
        if state == TIME_NIGHT_HIDE:
            config.clearTimeout()
        return TIME_DAY
    else:
        return state

# Class to hold the configuration of the clock (when morning and evening are,
# duration of timeouts). This will also handle the timeout logic
class Config:
    def __init__(self, timeout=5, day_hour=9, day_min=0, night_hour=22, night_min=30):
        self.timeout = int(timeout)
        self.day_hour = int(day_hour)
        self.day_min = int(day_min)
        self.night_hour = int(night_hour)
        self.night_min = int(night_min)
        self.next_timeout = None

    # Set a new timeout - must be either checked after firing or cleared
    def startTimeout(self):
        t = time.time()
        self.next_timeout = t + self.timeout
    
    # Check the current timeout
    # Returns true if the timeout has fired, false otherwise
    def checkTimeout(self):
        if self.next_timeout == None:
            return False
        t = time.time()
        return self.next_timeout < t
    
    # Clear the current timeout
    def clearTimeout(self):
        self.next_timeout = None

# Get whether it is in day hours or night
def getHours(config):
    t = time.localtime()
    # Which change comes first in the day (after midnight)
    first = HOURS_DAY
    first_hour = config.day_hour
    first_min = config.day_min
    last = HOURS_NIGHT
    last_hour = config.night_hour
    last_min = config.night_min
    if (last_hour < first_hour) or (last_hour == first_hour and last_min < first_min):
        first = last
        first_hour = last_hour
        first_min = last_min
        last = HOURS_DAY
        last_hour = config.day_hour
        last_min = config.day_min
    # Check if before first change
    if t.tm_hour < first_hour:
        return last
    if t.tm_hour == first_hour and t.tm_min < first_min:
        return last
    # Check if between changes
    if t.tm_hour < last_hour:
        return first
    if t.tm_hour == last_hour and t.tm_min < last_min:
        return first
    # (Must be after last change)
    return last

# The main program, calls loop once every second
def main():
    # Initialise state
    state = None
    config = loadConfig()
    # Setup GPIO input for button
    setupGPIO()
    # Initialise and load the map
    led.init()
    led.mapFromFile("map")
    # Start main loop
    while True:
        state = loop(state, config)
        time.sleep(0.2)

def loadConfig():
    with open("config") as file:
        d = dict(x.rstrip().split("=", 1) for x in file)
    return Config(**d)

# Sampled from code example at https://raspberrypihq.com/use-a-push-button-with-raspberry-pi-gpio/ "Using a push button with Raspberry Pi GPIO - Published by Soren on February 8, 2018"
# Accessed 8/8/2022
def setupGPIO():
    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING) # Setup event on pin 10 rising edge

if __name__ == "__main__":
    main()
