# Experiment 3: Dimming an LED with a potentiometer

Turn a potentiometer to change the brightness of an LED.

## What you'll learn

- PWM (pulse-width modulation) with `PWM`
- Mapping an analog input directly to a PWM output

## Run it

Open [main.py](main.py) and use **Tasks: Run Task → Run current file on Pico
(no save)**.

## Check before running

`POT_ADC_PIN` must be an ADC-capable pin (GP26, GP27 or GP28). Both it and
`LED_PIN` are assumptions; verify against your kit's guide.

## Try it yourself

- Make the brightness follow a curve (square the value) so the dimming looks
  more even to the eye.
- Print the pot value as a percentage.
