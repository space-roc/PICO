# Experiment 3: Dimming an LED with a potentiometer
#
# Turning the potentiometer (a knob that changes resistance) changes how
# bright the LED is. The brightness is controlled using PWM.
#
# PWM (pulse-width modulation) switches the pin on and off very fast. The
# longer it is "on" in each cycle (the duty cycle), the brighter the LED looks.
#
# NOTE: pins are assumptions. Check them against your kit's guide.

from machine import ADC, PWM, Pin
from time import sleep

# The pot must be on an analog-capable pin: GP26, GP27 or GP28.
POT_ADC_PIN = 27
LED_PIN = 15

# Read the knob position as an analog value.
pot = ADC(Pin(POT_ADC_PIN))

# Set up PWM on the LED pin.
led = PWM(Pin(LED_PIN))
# 1000 cycles per second is too fast for the eye to see as flicker.
led.freq(1000)

while True:
    # read_u16() gives 0-65535 for the knob position, and duty_u16() accepts
    # the same range (0 = always off, 65535 = always on), so we can pass the
    # value straight through with no maths.
    led.duty_u16(pot.read_u16())

    # A short pause between updates is plenty for smooth dimming.
    sleep(0.01)
