# Project 2: Random dice
#
# Press the button to roll a six-sided dice. The seven segment display
# "tumbles" through random digits for a moment, then settles on the result
# (1-6). The result is also printed in the terminal.
#
# NOTE: the segment pins are the ones used in the Experiment 7 test file.
# BUTTON_PIN is an assumption: change it to the GP pin your button uses.

from machine import Pin
from random import randint
from time import sleep_ms

# GP pins for segments a, b, c, d, e, f, g, in that order.
SEGMENT_PINS = [18, 17, 16, 15, 14, 13, 12]

# The button connects this pin to 3.3 V when pressed.
BUTTON_PIN = 20

# Set True if the display's shared pin goes to 3.3 V instead of GND.
COMMON_ANODE = False

# How long the "tumbling" animation lasts, and how fast it changes digit.
ROLL_TIME_MS = 1200
ROLL_STEP_MS = 80

# Which segments are lit for each digit 0-9: (a, b, c, d, e, f, g).
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

segments = [Pin(p, Pin.OUT) for p in SEGMENT_PINS]
# PULL_DOWN keeps the pin at 0 when the button is not pressed.
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)


def clear():
    """Turn off all segments on the display."""
    for pin in segments:
        pin.value(1 if COMMON_ANODE else 0)


def reset_hardware():
    """Cease lingering activities from previous scripts: turn off LED & blank display."""
    # Turn off the onboard LED (handles both Pico W 'LED' and standard Pico GP25)
    for led_id in ("LED", 25):
        try:
            Pin(led_id, Pin.OUT).value(0)
            break
        except Exception:
            pass

    # Turn off all 7-segment display pins
    clear()


def show(digit):
    """Light the segments needed to display 'digit' (0-9)."""
    for pin, on in zip(segments, DIGITS[digit]):
        pin.value((not on) if COMMON_ANODE else on)


def roll():
    """Animate a roll and return the final result (1-6)."""
    elapsed = 0
    while elapsed < ROLL_TIME_MS:
        # Show a random face while the dice is "tumbling".
        show(randint(1, 6))
        sleep_ms(ROLL_STEP_MS)
        elapsed += ROLL_STEP_MS
    result = randint(1, 6)
    show(result)
    return result


# --- Reset at startup ---
# Immediately shut down any active pins/LEDs left behind by previous scripts.
reset_hardware()
sleep_ms(150)

# Start by showing 0 to say "ready, press the button".
show(0)
print("Press the button to roll the dice.")

while True:
    if button.value():
        print("Rolled:", roll())
        # Wait for the button to be released so one press is one roll.
        while button.value():
            sleep_ms(10)
        # Short pause to ignore contact bounce.
        sleep_ms(50)
    sleep_ms(10)
