# Experiment 4: Using a transistor to drive a motor
#
# A Pico pin can only supply a tiny current, far too little for a motor.
# Instead the pin switches a transistor, and the transistor switches the
# larger motor current from a separate supply. Using PWM we can also vary the
# motor speed. This program ramps the speed up, holds it, then ramps down.
#
# NOTE: the pin is an assumption. Check it against your kit's guide.

from machine import PWM, Pin
from time import sleep

# The pin connected to the transistor's base (its switch input).
TRANSISTOR_PIN = 16

# Set up PWM on that pin. A higher duty cycle means the transistor is on for
# more of each cycle, so the motor gets more power and spins faster.
motor = PWM(Pin(TRANSISTOR_PIN))
motor.freq(1000)

while True:
    # Speed up: duty goes from 0 to 65535 (full power) in steps of 2048.
    for duty in range(0, 65536, 2048):
        # min() makes sure we never go above the maximum allowed value.
        motor.duty_u16(min(duty, 65535))
        sleep(0.1)

    # Hold at full speed for one second.
    sleep(1)

    # Slow down: duty goes from 65535 back to 0 in steps of 2048.
    for duty in range(65535, -1, -2048):
        # max() makes sure we never go below zero.
        motor.duty_u16(max(duty, 0))
        sleep(0.1)

    # Pause with the motor stopped for one second, then repeat.
    sleep(1)
