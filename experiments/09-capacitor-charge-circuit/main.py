# Experiment 9: Capacitor charge circuit
#
# A capacitor stores electrical charge. When it is connected to a voltage
# through a resistor, its own voltage rises gradually (charging) and when the
# supply is removed it falls gradually (discharging). This program does both
# and prints the capacitor's voltage over time so you can plot the curve.
#
# NOTE: pins are assumptions. Check them against your kit's guide.

from machine import ADC, Pin
# sleep_ms pauses for milliseconds. ticks_ms/ticks_diff measure elapsed time.
from time import sleep_ms, ticks_diff, ticks_ms

# This pin is set high (3.3 V) to charge the capacitor and low (0 V) to
# discharge it, both via a resistor.
CHARGE_PIN = 19

# This analog pin (GP26-GP28) measures the voltage across the capacitor.
SENSE_ADC_PIN = 26

ADC_REF_VOLTS = 3.3

# Start with the charge pin low so the capacitor begins empty.
charge = Pin(CHARGE_PIN, Pin.OUT, value=0)
sense = ADC(Pin(SENSE_ADC_PIN))


def volts():
    """Return the capacitor voltage in volts."""
    return sense.read_u16() * ADC_REF_VOLTS / 65535


def record(label, seconds):
    """Print time and voltage readings for 'seconds' seconds."""
    print(label)
    # Remember when we started so we can print the time since then.
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < seconds * 1000:
        # Print "seconds since start, volts", e.g. "1.20, 2.153".
        print("{:.2f}, {:.3f}".format(ticks_diff(ticks_ms(), start) / 1000, volts()))
        # Take 10 readings per second.
        sleep_ms(100)


while True:
    # Column headings, handy when pasting the output into a spreadsheet.
    print("time_s, volts")

    # Charge: drive the pin high for 5 seconds while recording.
    charge.value(1)
    record("Charging", 5)

    # Discharge: drive the pin low for 5 seconds while recording.
    charge.value(0)
    record("Discharging", 5)
