# Experiment 7 single-pin test
#
# Blinks ONE pin on and off, so you can check one segment at a time.
# Change TEST_PIN to the GP number you wired the segment to.
#
# Needed for the segment to light:
#   - the segment's wire goes to TEST_PIN through a 220-330 ohm resistor
#   - the display's common pin goes to GND (common-cathode display)

from machine import Pin
from time import sleep

# The GP pin to test. 18 is segment "a" in main_TEST.py.
TEST_PIN = 18

pin = Pin(TEST_PIN, Pin.OUT)

while True:
    print("GP" + str(TEST_PIN), "ON")
    pin.value(1)
    sleep(1)

    print("GP" + str(TEST_PIN), "OFF")
    pin.value(0)
    sleep(1)
