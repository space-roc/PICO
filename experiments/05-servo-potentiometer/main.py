# Experiment 5: Controlling a servo with a potentiometer
#
# A hobby servo moves to an angle set by the length of a pulse that is sent
# to it 50 times a second (every 20 ms). A pulse of about 0.5-1 ms gives one
# end of its travel and about 2-2.5 ms gives the other end. Here the knob
# position chooses the pulse length, so turning the knob moves the servo.
#
# NOTE: pins are assumptions. Check them against your kit's guide.

from machine import ADC, PWM, Pin
from time import sleep

POT_ADC_PIN = 27   # must be GP26, GP27 or GP28
SERVO_PIN = 17

# Pulse lengths in microseconds for the two ends of the servo's travel.
# If the servo buzzes or hits its end stops, narrow these (e.g. 1000 and 2000).
MIN_PULSE_US = 500
MAX_PULSE_US = 2500

# Servos expect one pulse every 20,000 microseconds (50 times a second).
PERIOD_US = 20000

pot = ADC(Pin(POT_ADC_PIN))

# Set up PWM at 50 Hz, the signal rate servos expect.
servo = PWM(Pin(SERVO_PIN))
servo.freq(50)

while True:
    # Map the knob reading (0-65535) onto the range MIN_PULSE_US..MAX_PULSE_US.
    # "//" is whole-number division.
    pulse = MIN_PULSE_US + pot.read_u16() * (MAX_PULSE_US - MIN_PULSE_US) // 65535

    # duty_u16() takes the pulse as a fraction of the period, scaled to 65535.
    # For example a 1500 us pulse is 1500/20000 = 7.5% of the cycle.
    servo.duty_u16(pulse * 65535 // PERIOD_US)

    # Update 50 times a second, matching the servo's signal rate.
    sleep(0.02)
