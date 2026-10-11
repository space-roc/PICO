# Experiment 4: Using a transistor to drive a motor

Use a transistor, switched by a Pico pin, to run a motor. The program ramps the
motor speed up and down with PWM.

## What you'll learn

- Why a Pico pin can't power a motor directly
- Switching a load with a transistor and PWM speed control

## Run it

Open [main.py](main.py) and use **Tasks: Run Task → Run current file on Pico
(no save)**. Stop with `Ctrl+C`; the motor may keep its last speed, so
unplug the Pico or re-run to stop it.

## Check before running

`TRANSISTOR_PIN` is an assumption; verify it against your kit's guide. Power
the motor only as the guide shows.

## Try it yourself

- Control the speed with a potentiometer (see Experiment 3).
- Start the motor only while a button is pressed.
