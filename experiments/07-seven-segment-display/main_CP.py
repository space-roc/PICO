# Experiment 7: Using a seven segment display
#
# A seven segment display is made of seven LEDs (segments) labelled a-g.
# Lighting different combinations of them draws the digits 0-9. This program
# counts from 0 to 9, changing digit every second.
#
#      aaa
#     f   b
#      ggg
#     e   c
#      ddd
#
# NOTE: pins are assumptions. Check them against your kit's guide and the
# display's wiring.

from machine import Pin
from time import sleep

# The GP pin for each segment, in the order a, b, c, d, e, f, g.
SEGMENT_PINS = [0, 1, 2, 3, 4, 5, 6]

# False: the display's shared pin goes to 0 V, so a 1 lights a segment.
# True:  the shared pin goes to 3.3 V, so a 0 lights a segment (inverted).
# If your digits look wrong or inverted, flip this setting.
COMMON_ANODE = False

# Which segments are lit for each digit. Each row is (a, b, c, d, e, f, g)
# where 1 = lit and 0 = off. The row position is the digit it shows.
DIGITS = [
    (1, 1, 1, 1, 1, 1, 0),  # 0
    (0, 1, 1, 0, 0, 0, 0),  # 1
    (1, 1, 0, 1, 1, 0, 1),  # 2
    (1, 1, 1, 1, 0, 0, 1),  # 3
    (0, 1, 1, 0, 0, 1, 1),  # 4
    (1, 0, 1, 1, 0, 1, 1),  # 5
    (1, 0, 1, 1, 1, 1, 1),  # 6
    (1, 1, 1, 0, 0, 0, 0),  # 7
    (1, 1, 1, 1, 1, 1, 1),  # 8
    (1, 1, 1, 1, 0, 1, 1),  # 9
]

# Make a list containing one output Pin object per segment.
segments = [Pin(p, Pin.OUT) for p in SEGMENT_PINS]


def show(digit):
    """Light the segments needed to display 'digit' (0-9)."""
    # zip() pairs each pin with its on/off value for this digit.
    for pin, on in zip(segments, DIGITS[digit]):
        # For a common-anode display, flip the value (on becomes 0).
        pin.value((not on) if COMMON_ANODE else on)


while True:
    # Count from 0 up to 9 (range(10) gives 0..9), one digit per second.
    for n in range(10):
        show(n)
        sleep(1)
