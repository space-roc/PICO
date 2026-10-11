# Experiment 1: Digital inputs and outputs
#
# An LED lights up while a button is held down, and goes off when it is
# released. This shows the two basic things a pin can do: read (input) and
# drive (output) a simple on/off signal.
#
# NOTE: the pin numbers below are assumptions. Check them against your kit's
# guide and change them to match how you wired the circuit.

from machine import Pin
from time import sleep

# GP numbers for the parts. Change these if your wiring is different.
LED_PIN = 15
BUTTON_PIN = 14

# Output pin: the Pico can set it high (3.3 V, LED on) or low (0 V, LED off).
led = Pin(LED_PIN, Pin.OUT)

# Input pin: the Pico reads whether it is high (1) or low (0).
# PULL_DOWN adds an internal resistor to 0 V so that the pin reads 0 when
# the button is NOT pressed, instead of floating randomly.
# This assumes the button connects the pin to 3.3 V when pressed, so
# button.value() is 1 while pressed. If your button connects to 0 V instead,
# use Pin.PULL_UP and invert the value (1 - button.value()).
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)

while True:
    # Copy the button state to the LED: pressed (1) -> on, released (0) -> off.
    led.value(button.value())

    # A very short pause stops the loop spinning at full speed for no reason.
    sleep(0.01)
