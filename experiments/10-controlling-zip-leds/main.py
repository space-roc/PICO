# Experiment 10: Controlling ZIP LEDs
#
# ZIP LEDs are "addressable": many RGB LEDs are chained together and a single
# data pin tells each one what colour to show. MicroPython has a built-in
# "neopixel" module that speaks the protocol these LEDs use.
#
# NOTE: pin and LED count are assumptions. Check them against your kit's guide.

from machine import Pin
from neopixel import NeoPixel
from time import sleep

# The data pin and the number of LEDs in the chain.
ZIP_PIN = 20
NUM_LEDS = 3

# 1.0 is full brightness. ZIP LEDs are very bright, so keep this low.
BRIGHTNESS = 0.2

# Colours as (red, green, blue), each 0-255. If your LEDs show the wrong
# colours (e.g. red and green swapped), they use a different colour order, so
# swap the values here.
COLOURS = [
    (255, 0, 0),      # red
    (0, 255, 0),      # green
    (0, 0, 255),      # blue
    (255, 255, 0),    # yellow
    (0, 255, 255),    # cyan
    (255, 0, 255),    # magenta
]

# Create the LED chain object on the data pin.
leds = NeoPixel(Pin(ZIP_PIN), NUM_LEDS)


def scaled(colour):
    """Return 'colour' with each value reduced by BRIGHTNESS."""
    return tuple(int(c * BRIGHTNESS) for c in colour)


# "step" shifts which colour each LED shows, so the colours appear to move.
step = 0
while True:
    for i in range(NUM_LEDS):
        # Pick a colour for LED number i. The "%" (remainder) makes the index
        # wrap back to the start of the list when it reaches the end.
        leds[i] = scaled(COLOURS[(step + i) % len(COLOURS)])

    # The colours are only sent to the LEDs when write() is called.
    leds.write()

    # Move on to the next colour pattern and wait half a second.
    step += 1
    sleep(0.5)
