# Experiment 1: Digital inputs and outputs

Light an LED while a button is held down.

## What you'll learn

- Digital output (`Pin.OUT`) and input (`Pin.IN`)
- Pull-down resistors

## Run it

Open [main.py](main.py) and use **Tasks: Run Task → Run current file on Pico
(no save)**. Use **Upload current file to Pico as main.py** to keep it.

## Check before running

The pins (`LED_PIN`, `BUTTON_PIN`) at the top of `main.py` are assumptions.
Compare them with your kit's guide and edit them to match. If the button is
wired to read 0 when pressed, change `PULL_DOWN` to `PULL_UP` and invert the
value.

## Try it yourself

- Make the button toggle the LED on each press.
- Blink the LED while the button is held.
