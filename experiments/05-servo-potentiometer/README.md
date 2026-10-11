# Experiment 5: Controlling a servo with a potentiometer

Turn a potentiometer to set the angle of a hobby servo.

## What you'll learn

- How servos are driven by pulse width at 50 Hz
- Mapping an analog value to a pulse length

## Run it

Open [main.py](main.py) and use **Tasks: Run Task → Run current file on Pico
(no save)**.

## Check before running

`POT_ADC_PIN` and `SERVO_PIN` are assumptions; verify against your kit's
guide. If the servo buzzes or hits its end stops, narrow `MIN_PULSE_US` and
`MAX_PULSE_US` (for example 1000 and 2000).

## Try it yourself

- Sweep the servo back and forth automatically.
- Print the angle in degrees.
