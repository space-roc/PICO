# Experiment 2: Light sensor and analog inputs

Read a light-dependent resistor (LDR) and switch an LED on when it gets dark.

## What you'll learn

- Reading analog values with `ADC` (0-65535)
- Using a threshold to make a decision

## Run it

Open [main.py](main.py) and use **Tasks: Run Task → Run current file on Pico
(no save)**. Cover the sensor and watch the printed values.

## Check before running

`LDR_ADC_PIN` and `LED_PIN` are assumptions; verify them against your kit's
guide. The reading may rise or fall in the dark depending on the wiring, so
note the values in light and dark, then adjust `DARK_THRESHOLD` and the
comparison direction.

## Try it yourself

- Dim the LED smoothly using PWM as it gets darker.
- Print "Light" or "Dark" instead of raw numbers.
