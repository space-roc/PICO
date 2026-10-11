# Experiment 10: Controlling ZIP LEDs

Cycle colours across addressable RGB LEDs (ZIP LEDs).

## What you'll learn

- Addressable LEDs: one data pin controls many LEDs
- Using MicroPython's built-in `neopixel` module with RGB tuples

## Run it

Open [main.py](main.py) and use **Tasks: Run Task → Run current file on Pico
(no save)**.

## Check before running

`ZIP_PIN` and `NUM_LEDS` are assumptions; verify them against your kit's
guide. If the colours look wrong (for example red and green swapped), your LEDs
use a different colour order; swap the values in `COLOURS`. Keep `BRIGHTNESS`
low.

## Try it yourself

- Make a chase where one LED lights at a time.
- Set colour from a potentiometer (Experiment 3).
