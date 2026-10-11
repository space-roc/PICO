# Experiment 8: Exploring wind power
#
# A motor works in reverse too: if you spin its shaft (for example by blowing
# on a fan attached to it) it generates a small voltage. This program
# measures that voltage and shows it as numbers and a simple bar graph.
#
# NOTE: the pin is an assumption. Check it against your kit's guide. Never
# connect more than 3.3 V to a Pico analog pin.

from machine import ADC, Pin
from time import sleep

# Must be an analog-capable pin: GP26, GP27 or GP28.
MOTOR_ADC_PIN = 28

# The voltage that a full-scale reading (65535) represents.
ADC_REF_VOLTS = 3.3

motor = ADC(Pin(MOTOR_ADC_PIN))

# Keep track of the highest voltage seen so far.
peak = 0.0

while True:
    # Convert the raw reading (0-65535) into volts.
    volts = motor.read_u16() * ADC_REF_VOLTS / 65535

    # Update the peak if this reading is higher than any before it.
    peak = max(peak, volts)

    # Build a bar made of "#" characters: 20 characters per volt.
    bar = "#" * int(volts * 20)

    # Show the current voltage, the peak voltage and the bar.
    # "{:.2f}" means show the number with 2 decimal places.
    print("{:.2f} V (peak {:.2f} V) {}".format(volts, peak, bar))

    # Ten readings per second.
    sleep(0.1)
