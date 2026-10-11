# Experiment 8: Exploring wind power

Use a motor as a generator: blow on or spin it, and measure the voltage it
produces.

## What you'll learn

- Motors generate a voltage when turned
- Reading and visualising a changing voltage

## Run it

Open [main.py](main.py) and use **Tasks: Run Task → Run current file on Pico
(no save)**. Spin the rotor and watch the printed voltage and bar.

## Check before running

`MOTOR_ADC_PIN` is an assumption; verify it against your kit's guide. Never
feed more than 3.3 V into an ADC pin; use the guide's voltage-limiting
circuit if it has one.

## Try it yourself

- Light an LED when the voltage passes a threshold.
- Compare the peak voltage from different blowing distances.
