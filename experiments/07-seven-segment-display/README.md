# Experiment 7: Using a seven segment display

Count from 0 to 9 on a seven segment display.

## What you'll learn

- Driving several outputs from a list of pins
- Encoding digits as segment patterns

## Run it

Open [main.py](main.py) and use **Tasks: Run Task → Run current file on Pico
(no save)**.

## Check before running

`SEGMENT_PINS` (segments a-g in order) is an assumption; verify against your
kit's guide and the display's wiring. If the digits look inverted, toggle
`COMMON_ANODE`. Use current-limiting resistors as the guide shows.

## Try it yourself

- Count up with a button press.
- Show the value of a potentiometer as a digit 0-9.
