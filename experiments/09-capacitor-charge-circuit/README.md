# Experiment 9: Capacitor charge circuit

Charge and discharge a capacitor through a resistor and record its voltage over
time.

## What you'll learn

- How a capacitor charges and discharges (an RC curve)
- Sampling a voltage over time

## Run it

Open [main.py](main.py) and use **Tasks: Run Task → Run current file on Pico
(no save)**. The output is `time_s, volts` rows you can paste into a
spreadsheet to plot.

## Check before running

`CHARGE_PIN` and `SENSE_ADC_PIN` are assumptions; verify them against your
kit's guide. Observe capacitor polarity if it is electrolytic.

## Try it yourself

- Time how long the voltage takes to reach 63% of its final value.
- Swap the capacitor or resistor and compare the curves.
