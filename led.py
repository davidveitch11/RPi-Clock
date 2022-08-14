
# This module will allow the user to control two MCP23017 devices
# where it is assumed that all pins on the devices are set to output
# to LEDs.
# The module keeps track of whether each of the 32 LEDs is on (1) or
# off (0). LEDs are numbered 0-31
# Since not all LEDs will be attached in order, the module will map
# LED numbers to pin identifiers.
# The map can be loaded from a file with 'mapFromFile' and saved to
# a file with 'saveMapToFile'. A single LED can be mapped with 'mapLED'
# Call 'init' before other methods once the devices are connected.
# Set an LED using 'set'

from math import floor
import smbus

# Identifiers for the two devices
DEVICE_1 = 0x20
DEVICE_2 = 0x21

# Identifiers for the registers
IODIR_A = 0x0
IODIR_B = 0x1
GPIO_A = 0x12
GPIO_B = 0x13

# The mapping between LED numbers (0 - 31) and GPIO pins (device, port and bit position)
# If a number is not present, the mapping is assumed to be default.
# device = num / 16, port = (num % 16) / 8, bit = num % 8
mapping = []

# The bus to be used to communicate with device
bus = None

# The current status of all the pins
status = [0] * 32

# Initialise the module - must be called before any other
def init():
    global bus
    bus = smbus.SMBus(1)
    # Reset directions to be outputs and GPIO to be 'off'
    setAll(0, include_dir = True)

# Set all (GPIO) registers in both devices to use the value given.
# If include_dir is set to True, this will also set the IODIR
# registers to the same value
def setAll(value, include_dir = False):
    # Decide which registers/devices to use
    devices = [DEVICE_1, DEVICE_2]
    if include_dir:
        registers = [IODIR_A, GPIO_A, IODIR_B, GPIO_B]
    else:
        registers = [GPIO_A, GPIO_B]
    # Set all registers in both devices to the value
    for device in devices:
        for register in registers:
            bus.write_byte_data(device, register, value)

# Open the <sep>-separated file and use each line as a map record
# "<device> <port> <bit> <num>\n"
def mapFromFile(filename, sep=" "):
    with open(filename) as file:
        for line in file:
            [device, port, bit, num] = line.removesuffix("\n").split(sep)
            num = int(num)
            device = int(device)
            port = int(port)
            bit = int(bit)
            mapping.append((num, (device, port, bit)))

# Save the current mapping to a <sep>-separated file
def saveMapToFile(filename, sep=" "):
    with open(filename, "w") as file:
        for (num, (device, port, bit)) in mapping:
            file.write("{1}{0}{2}{0}{3}{0}{4}\n".format(sep, device, port, bit, num))

# Specify that LED 'num' corresponds to the device/port/bit specified
def mapLED(num, device, port, bit):
    mapping.append((num, (device, port, bit)))

# Get the device/port/bit corresponding to LED 'num'
def getLED(num):
    # Find predetermined mapping
    for entry in mapping:
        if entry[0] == num:
            return entry[1]
    # Default mapping
    device = floor(num / 16)
    port = floor((num % 16) / 8)
    bit = num % 8
    return (device, port, bit)

# Get the 'status' value - a byte that can be written to the device
def getStatus(device, port):
    # Ouput byte
    s = 0
    # Index of 'status' to start reading from
    main_index = (device * 16) + (port * 8)
    # Byte to be 'or'd onto 's'
    add_bit = 0x1
    # Construct by adding each bit
    for i in range(8):
        if status[main_index + i] == 1:
            s |= add_bit
        add_bit = add_bit << 1
    return s

# Set LED to be on (value == 1) or off (value == 0)
def set(num, value):
    # Get the location of the LED
    (device, port, bit) = getLED(num)
    # Update the status of the LED
    updateStatus(device, port, bit, value)
    update(device, port)

# Set the value of a pin (on = 1, off = 0)
def setDPB(device, port, bit, value):
    # Update the status of the LED
    updateStatus(device, port, bit, value)
    update(device, port)

# Update the status of the required port to match the status list in memory
def update(device, port):
    # Get the binary version of the status for this port
    s = getStatus(device, port)
    # Write the register
    write(device, port, s)

# Update the in-memory status list to hold the new value
def updateStatus(device, port, bit, value):
    i = (device * 16) + (port * 8) + bit
    status[i] = value

# Write the GPIO register to be value for the device/port specified
def write(device, port, value):
    if device == 0:
        d = DEVICE_1
    else:
        d = DEVICE_2
    if port == 0:
        p = GPIO_A
    else:
        p = GPIO_B
    bus.write_byte_data(d, p, value)
