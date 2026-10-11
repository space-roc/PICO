# Experiment 2: Light sensor and analog inputs
#
# A light-dependent resistor (LDR) changes its resistance with the amount of
# light. We read it as an analog value and switch an LED on when it gets dark.
#
# NOTE: pins and the threshold are assumptions. Check them against your kit's
# guide, and tune the threshold using the values printed below.

from machine import ADC, Pin
from time import sleep

# Only GP26, GP27 and GP28 can be read as analog inputs (ADC0, ADC1, ADC2).
LDR_ADC_PIN = 26
LED_PIN = 15

# Readings run from 0 to 65535. Anything below this number counts as "dark".
# Look at the printed readings in light and dark, then pick a value in
# between. If your readings go UP in the dark, change "<" to ">" below.
DARK_THRESHOLD = 20000

# ADC(Pin(...)) sets up the pin as an analog input.
ldr = ADC(Pin(LDR_ADC_PIN))
# The LED is a normal on/off output.
led = Pin(LED_PIN, Pin.OUT)

while True:
    # Read the sensor: a number from 0 (0 V) to 65535 (3.3 V).
    reading = ldr.read_u16()

    # Print the number so you can see how it changes when you cover the sensor.
    print("Light reading:", reading)

    # Compare the reading to the threshold. The expression gives 1 (on) when
    # it is dark and 0 (off) otherwise. Which direction means "dark" depends
    # on how the LDR is wired in the circuit.
    led.value(1 if reading < DARK_THRESHOLD else 0)

    # Take about 5 readings per second.
    sleep(0.2)
