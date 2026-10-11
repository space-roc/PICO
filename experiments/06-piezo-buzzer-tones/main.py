# Experiment 6: Setting the tone with a piezo buzzer
#
# A piezo buzzer makes a sound when it is driven with a signal that switches
# on and off. The pitch (musical note) depends on how many times per second
# it switches, measured in hertz (Hz). This program plays a musical scale.
#
# NOTE: the pin is an assumption. Check it against your kit's guide.

from machine import PWM, Pin
from time import sleep

BUZZER_PIN = 18

# Frequencies in Hz for one octave starting at middle C.
# "C5" is the C one octave higher, which finishes the scale.
NOTES = {"C": 262, "D": 294, "E": 330, "F": 349, "G": 392, "A": 440, "B": 494, "C5": 523}

# The order the notes are played in.
SCALE = ["C", "D", "E", "F", "G", "A", "B", "C5"]

# PWM generates the switching signal on the buzzer pin.
buzzer = PWM(Pin(BUZZER_PIN))


def play(freq, seconds):
    """Play one note at 'freq' Hz for 'seconds' seconds, then a short gap."""
    # Set how fast the pin switches: this sets the pitch.
    buzzer.freq(freq)
    # A duty of 32768 is half of 65535, so the pin is on for half of each
    # cycle. That gives the loudest, cleanest tone. A duty of 0 is silence.
    buzzer.duty_u16(32768)
    # Hold the note for the requested time.
    sleep(seconds)
    # Silence the buzzer, then pause briefly so notes sound separate.
    buzzer.duty_u16(0)
    sleep(0.05)


while True:
    # Play each note of the scale for 0.3 seconds.
    for note in SCALE:
        play(NOTES[note], 0.3)

    # Wait two seconds before playing the scale again.
    sleep(2)
