'''
Kitronik Inventor's Kit Exp 1
Turns an LED on and off in response to a press on the button that is connected to GP15.
The Pico has an on-board LED you can control, connected to GP25.
The switch is connected from the 3V3 output header to GP15, which is configured as an input.
'''
import machine
# Setup an input button with a human-readable name and enable the internal pull-down resistor
switch = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_DOWN)
LED = machine.Pin(25, machine.Pin.OUT) # Setup the onboard LED Pin as an output
# The loop will run forever
# Sets the LED output to be equal to the switch input (e.g. switch pressed = LED on)
while True:
    if switch.value():
        LED.value(True)
    else:
        LED.value(False)