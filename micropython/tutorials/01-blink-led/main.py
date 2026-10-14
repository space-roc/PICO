
# Tutorial 1: Blink the onboard LED
#
# This program flips the Pico's built-in LED on and off every half second
# and prints a running count so you can see it working in the terminal.

# "machine" is MicroPython's hardware module. "Pin" lets us control the
# Pico's GPIO (general purpose input/output) pins.
from machine import Pin
# "sleep" pauses the program for a number of seconds.
from time import sleep

# Create an output pin connected to the onboard LED.
# "LED" is a name MicroPython knows for the built-in LED on every Pico model.
# On an older MicroPython build with a plain Pico, use Pin(25, Pin.OUT).
# Pin.OUT means the Pico drives the pin (rather than reading it).
led = Pin("LED", Pin.OUT)

# A variable that remembers how many times we have blinked.
count = 0

# "while True" repeats the indented lines below forever.
while True:
    # toggle() switches the LED: off becomes on, on becomes off.
    led.toggle()

    # Add 1 to the counter.
    count += 1

    # print() sends text to the terminal (visible in the REPL).
    print("blink", count)

    # Wait 0.5 seconds. A smaller number makes the LED blink faster.
    sleep(0.5)
    
    if count >= 10:
        led.value(False)
        break
