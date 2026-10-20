# Project 12: MLX90640 thermal camera (Pico side)
#
# Pimoroni MLX90640 breakout on I2C0: SDA -> GP8, SCL -> GP9, 3-5V -> 3V3 (OUT), GND -> GND
#
# The Pico only reads the sensor's raw data and sends it over USB as text lines.
# viewer.py on the PC turns it into temperatures and shows the picture.
#
#   EE:<hex>                 the sensor's calibration EEPROM (832 words)
#   FR:<subpage>:<ctl>:<hex> one half of a frame (832 words)
#
# Any other line is a status message for the viewer to display.

import sys
from binascii import hexlify
from machine import I2C, Pin
from select import POLLIN, poll
from time import sleep_ms, ticks_diff, ticks_ms

SDA_PIN = 8
SCL_PIN = 9
I2C_FREQ = 400000
ADDRESS = 0x33

# 0 = 0.5 Hz, 1 = 1 Hz, 2 = 2 Hz, 3 = 4 Hz, 4 = 8 Hz. Each frame is two
# subpages, so 4 Hz means 8 messages a second. Higher rates need a faster I2C
# clock and are less reliable.
REFRESH_RATE = 3
SEND_EEPROM_EVERY = 40 # Subpages between repeats, as a backup to asking for it
READY_TIMEOUT_MS = 2000

STATUS_REG = 0x8000
CONTROL_REG = 0x800D
EEPROM_START = 0x2400
RAM_START = 0x0400
DATA_READY = 0x0008

i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)


def read_bytes(register, words):
    return i2c.readfrom_mem(ADDRESS, register, words * 2, addrsize=16)


def read_word(register):
    data = read_bytes(register, 1)
    return data[0] << 8 | data[1]


def write_word(register, value):
    i2c.writeto_mem(ADDRESS, register, bytes((value >> 8, value & 0xFF)), addrsize=16)


def read_subpage():
    # Wait for a subpage, then read it. If a new one arrives while reading,
    # read again so the data isn't a mixture of two.
    start = ticks_ms()
    while not read_word(STATUS_REG) & DATA_READY:
        if ticks_diff(ticks_ms(), start) > READY_TIMEOUT_MS:
            raise RuntimeError("Sensor not ready")
        sleep_ms(2)

    for _ in range(5):
        write_word(STATUS_REG, 0x0030)
        data = read_bytes(RAM_START, 832)
        status = read_word(STATUS_REG)
        if not status & DATA_READY:
            return status & 0x0001, read_word(CONTROL_REG), data
    raise RuntimeError("Too many retries")


if ADDRESS not in i2c.scan():
    raise RuntimeError("MLX90640 not found at 0x33: check SDA (GP8), SCL (GP9), power and GND")

control = read_word(CONTROL_REG)
write_word(CONTROL_REG, (control & 0xFC7F) | (REFRESH_RATE << 7))
eeprom = hexlify(read_bytes(EEPROM_START, 832)).decode()
print("MLX90640 found. Reading frames...")

keyboard = poll()
keyboard.register(sys.stdin, POLLIN)


def eeprom_requested():
    # The viewer sends a byte when it connects, to ask for the EEPROM at once.
    asked = False
    while keyboard.poll(0):
        sys.stdin.read(1)
        asked = True
    return asked


count = 0
while True:
    if count % SEND_EEPROM_EVERY == 0 or eeprom_requested():
        print("EE:" + eeprom)
    try:
        subpage, control, data = read_subpage()
    except (RuntimeError, OSError) as error:
        print("Sensor error:", error)
        sleep_ms(500)
        continue
    print("FR:{}:{:04X}:{}".format(subpage, control, hexlify(data).decode()))
    count += 1
