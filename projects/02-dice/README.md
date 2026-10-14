# Project 2: Random dice

Press a button to roll a six-sided dice on the seven segment display.

## What you'll learn

- Random numbers with `random.randint`
- Reading a button and waiting for it to be released
- A simple animation before showing a result

## Hardware

- The seven segment display from [Experiment 7](../../experiments/07-seven-segment-display/README.md),
  wired as in your `main_TEST.py`: segments a to g on GP18, GP17, GP16, GP15,
  GP14, GP13, GP12, each through a resistor, with the common pin to GND
- A push button from the kit, connected between 3.3 V and `BUTTON_PIN` (as in
  [Experiment 1](../../experiments/01-digital-inputs-outputs/README.md))

**Check before running:** `BUTTON_PIN` is an assumption (GP20). Change it at the
top of `main.py` to the pin your button uses. If your display's common pin goes
to 3.3 V, set `COMMON_ANODE = True`.

## Run it

1. Open [main.py](main.py) and press `Ctrl+Shift+B`.
2. The display shows `0`, meaning ready.
3. Press the button. The display tumbles through random digits for about a
   second, then settles on a number from 1 to 6, also printed in the terminal.

To keep it on the Pico so it runs at power-up, use **Upload current file to
Pico as main.py**.

## How it works

- `randint(1, 6)` returns a random whole number from 1 to 6, both included.
- `roll()` shows random faces quickly, then picks the final result.
- After a roll the program waits for the button to be released, so holding the
  button down gives one roll rather than many.

## Try it yourself

- Roll two dice by adding a second display, or by showing the total.
- Use the piezo buzzer (Experiment 6) to click while the dice tumbles.
- Keep a count of how many times each number comes up and print it.
- Make a ten-sided dice (digits 0 to 9).

## Troubleshooting

- **Nothing happens on a press:** check `BUTTON_PIN` and the button wiring.
- **Segments wrong or missing:** use the single-pin test in Experiment 7.
- **It rolls by itself:** the button pin is floating; check it is wired to 3.3 V
  through the button only.
